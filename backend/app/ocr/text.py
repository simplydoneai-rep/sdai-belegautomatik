"""Belegtext gewinnen: PDF-Textlayer (PyMuPDF), sonst lokale Texterkennung (docTR).

Belegbilder verlassen den Rechner nie (CLAUDE.md, Technik: OCR lokal).
Wörter werden zu Zeilen nach ihrer Lage auf der Seite zusammengesetzt, damit Tabellen
(Positionen) zeilenweise lesbar bleiben.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pymupdf

MIN_TEXT_CHARS = 40  # weniger Text im Textlayer → als Scan behandeln
OCR_DPI = 300
DESKEW_SIGN = 1.0  # Vorzeichen des docTR-Winkels relativ zu OpenCV, per Test geprüft
MAX_SIDE = 2600  # Pixel; größere Fotos werden vorher verkleinert
MIN_CONFIDENCE = 0.8  # darunter wird eine andere Seitenlage versucht

Word = tuple[float, float, float, float, str]  # x0, y0, x1, y1, Text (y nach unten)


@dataclass
class ReadResult:
    text: str
    method: str  # "textlayer" | "ocr"
    pages: int
    seconds: float


def rows_from_words(words: list[Word], line_tol: float = 0.5) -> list[str]:
    """Gruppiert Wörter zu Zeilen. ``line_tol`` relativ zur Worthöhe."""
    if not words:
        return []
    ordered = sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    rows: list[list[Word]] = []
    centers: list[float] = []
    for w in ordered:
        cy, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1e-6)
        if rows and abs(cy - centers[-1]) <= h * line_tol:
            rows[-1].append(w)
            centers[-1] = sum((x[1] + x[3]) / 2 for x in rows[-1]) / len(rows[-1])
        else:
            rows.append([w])
            centers.append(cy)
    out = []
    for row in rows:
        row.sort(key=lambda w: w[0])
        avg_char = sum((w[2] - w[0]) / max(len(w[4]), 1) for w in row) / len(row)
        parts = [row[0][4]]
        for prev, cur in zip(row, row[1:]):
            gap = cur[0] - prev[2]
            parts.append(("   " if gap > 2.5 * avg_char else " ") + cur[4])
        out.append("".join(parts))
    return out


def _pdf_textlayer(doc: pymupdf.Document) -> str:
    pages = []
    for page in doc:
        words: list[Word] = [(w[0], w[1], w[2], w[3], w[4]) for w in page.get_text("words")]
        pages.append("\n".join(rows_from_words(words)))
    return "\n\f\n".join(pages)


@lru_cache(maxsize=1)
def _predictor() -> Any:
    from doctr.models import ocr_predictor

    return ocr_predictor(det_arch="db_resnet50", reco_arch="crnn_vgg16_bn", pretrained=True)


def deskew(image: np.ndarray) -> np.ndarray:
    """Richtet schief gescannte Seiten gerade aus (Winkel über die Textzeilen geschätzt)."""
    import cv2

    try:
        from doctr.models._utils import estimate_orientation

        angle = float(estimate_orientation(image))
    except Exception:
        return image
    if abs(angle) < 0.3 or abs(angle) > 45:
        return image
    h, w = image.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), DESKEW_SIGN * angle, 1.0)
    return cv2.warpAffine(image, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))


def limit_size(image: np.ndarray, max_side: int = MAX_SIDE) -> np.ndarray:
    """Verkleinert große Fotos (Handykamera), damit die Texterkennung nicht unnötig lange rechnet."""
    import cv2

    h, w = image.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return image
    return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def _ocr_page(image: np.ndarray) -> tuple[list[Word], float]:
    """Liest eine Seite; gibt Wörter und die mittlere Erkennungssicherheit (0–1) zurück."""
    page = _predictor()([image]).pages[0]
    words: list[Word] = []
    confs: list[float] = []
    for block in page.blocks:
        for line in block.lines:
            for word in line.words:
                (x0, y0), (x1, y1) = word.geometry
                words.append((x0 * 1000, y0 * 1000, x1 * 1000, y1 * 1000, word.value))
                confs.append(float(word.confidence))
    return words, (sum(confs) / len(confs) if confs else 0.0)


def ocr_images(images: list[np.ndarray]) -> str:
    """Texterkennung je Seite. Ist die Sicherheit gering (z. B. Blatt verkehrt herum eingezogen),
    werden 180°, 90° und 270° versucht und die Lage mit der höchsten Sicherheit genommen."""
    pages = []
    for img in images:
        img = deskew(limit_size(img))
        words, conf = _ocr_page(img)
        if conf < MIN_CONFIDENCE:
            for k in (2, 1, 3):
                cand_words, cand_conf = _ocr_page(np.ascontiguousarray(np.rot90(img, k)))
                if cand_conf > conf:
                    words, conf = cand_words, cand_conf
                if conf >= MIN_CONFIDENCE:
                    break
        pages.append("\n".join(rows_from_words(words)))
    return "\n\f\n".join(pages)


def _render(doc: pymupdf.Document) -> list[np.ndarray]:
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csRGB, alpha=False)
        images.append(np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).copy())
    return images


def read_document(path: Path, force_ocr: bool = False) -> ReadResult:
    t0 = time.perf_counter()
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        import cv2

        img = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)
        return ReadResult(ocr_images([img]), "ocr", 1, time.perf_counter() - t0)
    with pymupdf.open(path) as doc:
        if not force_ocr:
            text = _pdf_textlayer(doc)
            if len(text.strip()) >= MIN_TEXT_CHARS:
                return ReadResult(text, "textlayer", doc.page_count, time.perf_counter() - t0)
        return ReadResult(ocr_images(_render(doc)), "ocr", doc.page_count, time.perf_counter() - t0)
