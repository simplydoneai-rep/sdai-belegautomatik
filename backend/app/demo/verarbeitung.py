"""Demo-Verarbeitung: Beleg rein → Auslesen → Pseudonymisierung → KI (Aufzeichnung) → Steuerlogik → Vorschlag.

Alle Schritte laufen live und lokal. Nur die KI-Antwort wird aus den Messläufen abgespielt
(``app.llm.replay``), damit bei AWS oder IONOS keine Kosten entstehen. Unbekannte Belege
gehen an den regelbasierten Platzhalter. Nur für synthetische Testbelege (CLAUDE.md Regel 1).
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.erechnung.parser import parse_file, without_parties
from app.kontierung.betraege import parse_amount
from app.kontierung.konten import load_accounts, normalize_lines
from app.kontierung.steuerlogik import pruefe_summen
from app.llm.base import LLMProvider
from app.llm.placeholder import PlaceholderProvider
from app.llm.replay import ReplayProvider
from app.ocr.text import read_document
from app.pseudo.hilfen import client_profile, restore
from app.pseudo.pseudonymizer import pseudonymize
from app.qualitaet.vergleich import compare

PROJECT = Path(__file__).resolve().parents[3]
TESTDATEN = PROJECT / "testdaten"
TABELLEN = Path(__file__).resolve().parents[1] / "kontierung" / "tabellen"

MODELLE: dict[str, dict[str, str]] = {
    "ionos_qwen": {"label": "Qwen3.5 397B · IONOS (Deutschland)", "kurz": "Qwen3.5 (IONOS)"},
    "ionos_gptoss": {"label": "GPT-OSS 120B · IONOS (Deutschland)", "kurz": "GPT-OSS (IONOS)"},
    "bedrock": {"label": "Claude Sonnet 4.6 · AWS Bedrock (Frankfurt)", "kurz": "Claude (AWS)"},
    "bedrock_gptoss": {"label": "GPT-OSS 120B · AWS Bedrock (Frankfurt)", "kurz": "GPT-OSS (AWS)"},
    "bedrock_qwen": {"label": "Qwen3 235B · AWS Bedrock (Frankfurt)", "kurz": "Qwen3 (AWS)"},
}
PLACEHOLDER_KIND = re.compile(r"\[([A-Z_]+)_\d+\]")


@lru_cache(maxsize=1)
def mandanten() -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = json.loads((TESTDATEN / "mandanten.json").read_text(encoding="utf-8"))["mandanten"]
    return data


@lru_cache(maxsize=1)
def aufzeichnungen() -> dict[str, dict[str, Any]]:
    path = TESTDATEN / "demo" / "aufzeichnungen.json"
    if not path.exists():
        return {}
    data: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["belege"]
    return data


@lru_cache(maxsize=1)
def testbelege() -> list[dict[str, Any]]:
    """Alle Testbelege aus dem Goldstandard, je Datei ein Eintrag."""
    out = []
    for gpath in sorted((TESTDATEN / "goldstandard").glob("*.json")):
        gold = json.loads(gpath.read_text(encoding="utf-8"))
        for doc in gold["dokumente"]:
            if doc["pfad"].endswith("_uncefact.xml"):
                continue  # CII-Variante: gleicher Inhalt wie UBL
            out.append({"key": f'{gold["id"]}|{doc["pfad"]}', "id": gold["id"], "datei": doc["pfad"],
                        "art": doc["art"], "client_id": gold["client_id"], "merkmale": gold.get("merkmale", []),
                        "erwartet": {**gold["erwartet"], **doc.get("abweichend", {})}})
    return out


@lru_cache(maxsize=1)
def _konten() -> tuple[dict[str, str], dict[str, set[int]]]:
    names = dict(load_accounts("SKR03"))
    rates = json.loads((TABELLEN / "skr03_konto_steuersatz.json").read_text(encoding="utf-8"))["konten"]
    return names, {k: set(v) for k, v in rates.items()}


def _ampel_position(line: dict[str, Any], quelle: str, reverse_charge: bool) -> tuple[str, list[str]]:
    """Demo-Regel: rot = Angabe fehlt; gelb = Widerspruch oder ohne KI; grün = schlüssig.
    Die Sicherheit 0–1 aus CLAUDE.md Abschnitt 5 folgt in Phase 2."""
    names, rates = _konten()
    hinweise = []
    konto = line.get("account_skr03")
    rate = parse_amount(line.get("tax_rate")) if line.get("tax_rate") is not None else None
    if not konto or parse_amount(line.get("net_amount")) is None or rate is None:
        return "rot", ["Konto, Betrag oder Steuersatz fehlt"]
    if konto in rates and int(rate) not in rates[konto]:
        hinweise.append(f"Konto {konto} passt nicht zu {rate.normalize()} %")
    if rate == 0 and not reverse_charge and konto in ("3300", "3400"):
        hinweise.append("0 % ohne Reverse Charge")
    if quelle == "regelbasiert":
        hinweise.append("Vorschlag ohne KI")
    return ("gelb" if hinweise else "gruen"), hinweise


def gesamtampel(summen_ok: bool, positionen: list[dict[str, Any]], quelle: str) -> str:
    """Rot bei Widerspruch in den Summen; Grün nur mit Positionen, alle grün und mit KI oder E-Rechnung."""
    if not summen_ok:
        return "rot"
    if not positionen or quelle == "regelbasiert" or any(p["ampel"] != "gruen" for p in positionen):
        return "gelb"
    return "gruen"


def verarbeite(path: Path, client_id: str, modell: str, erwartet: dict[str, Any] | None = None) -> dict[str, Any]:
    schritte: list[dict[str, Any]] = []

    def schritt(name: str, t0: float, detail: str) -> None:
        schritte.append({"name": name, "dauer_s": round(time.perf_counter() - t0, 2), "detail": detail})

    t0 = time.perf_counter()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    schritt("Eingang", t0, f"SHA-256 {digest[:16]}…, {len(raw) / 1024:.0f} KB")

    client = mandanten()[client_id]
    accounts = load_accounts("SKR03")
    names, _ = _konten()
    ki: dict[str, Any] = {}
    pseudo_text = ""
    platzhalter: dict[str, int] = {}

    if path.suffix.lower() == ".xml":
        t0 = time.perf_counter()
        data: dict[str, Any] | None = without_parties(parse_file(path))
        schritt("Auslesen", t0, "E-Rechnung (XML) direkt gelesen, keine KI nötig")
        quelle = "e-rechnung"
        ki = {"art": "keine", "text": "E-Rechnung: strukturierte Daten, kein KI-Aufruf"}
    else:
        t0 = time.perf_counter()
        read = read_document(path)
        schritt("Auslesen", t0, "PDF-Textlayer" if read.method == "textlayer" else "Texterkennung (docTR, lokal)")

        t0 = time.perf_counter()
        pseudo = pseudonymize(read.text, client_profile(client), accounts, own_vat_ids=(client["vat_id"],))
        pseudo_text = pseudo.payload.text
        for kind in PLACEHOLDER_KIND.findall(pseudo_text):
            platzhalter[kind] = platzhalter.get(kind, 0) + 1
        schritt("Pseudonymisierung", t0, f"{sum(platzhalter.values())} Angaben durch Platzhalter ersetzt")

        t0 = time.perf_counter()
        recording = aufzeichnungen().get(digest, {}).get("antworten", {}).get(modell)
        provider: LLMProvider
        if recording:
            provider = ReplayProvider(modell, recording)
            quelle = "ki"
            ki = {"art": "aufzeichnung", "modell": MODELLE[modell]["label"], "lauf": recording.get("lauf"),
                  "laufzeit_s": recording.get("laufzeit_s"), "kosten_eur": recording.get("kosten_eur"),
                  "token_ein": recording.get("token_ein"), "token_aus": recording.get("token_aus")}
        else:
            provider = PlaceholderProvider()
            quelle = "regelbasiert"
            ki = {"art": "regelbasiert", "text": "Kein aufgezeichnetes KI-Ergebnis für diese Datei; regelbasierte Auslese ohne KI"}
        res = provider.extract(pseudo.payload)
        data = restore(res.data, pseudo.mapping) if res.data is not None else None
        detail = (f'Aufzeichnung {MODELLE[modell]["kurz"]} abgespielt (damals {recording["laufzeit_s"]:.1f} s)'
                  if recording else "regelbasiert ohne KI")
        schritt("KI-Vorschlag", t0, detail)

    t0 = time.perf_counter()
    if data:
        normalize_lines(data, {nr for nr, _ in accounts})
    check = pruefe_summen(data) if data else None
    schritt("Steuerlogik", t0, "Summen schlüssig" if check and check.ok else "Widerspruch gefunden")

    positionen = []
    for line in (data or {}).get("lines") or []:
        ampel, hinweise = _ampel_position(line, quelle, bool((data or {}).get("reverse_charge")))
        positionen.append({**line, "konto_name": names.get(str(line.get("account_skr03")), ""),
                           "ampel": ampel, "hinweise": hinweise})
    if quelle == "e-rechnung":
        for p in positionen:
            if not p.get("account_skr03"):
                p["ampel"], p["hinweise"] = "gelb", ["E-Rechnung: Kontierung folgt über Regeln (Phase 3)"]

    gesamt = gesamtampel(check.ok if check else False, positionen, quelle)
    soll = None
    if erwartet:
        v = compare(erwartet, data)
        soll = {"pflichtfelder": [sum(v["felder"].values()), len(v["felder"])],
                "positionen": v["positionen"]["betrag"], "konten": v["positionen"]["konto"],
                "abweichend": [k for k, ok in v["felder"].items() if not ok]}

    return {
        "sha256": digest, "quelle": quelle, "ki": ki, "schritte": schritte,
        "kopf": {k: (data or {}).get(k) for k in ("supplier_name", "invoice_number", "invoice_date", "document_type",
                                                    "net_total", "tax_total", "gross_total", "reverse_charge")},
        "positionen": positionen, "steuerlogik": {"ok": bool(check and check.ok), "hinweise": check.hinweise if check else []},
        "ampel": gesamt, "pseudonymisiert": pseudo_text, "platzhalter": platzhalter, "soll": soll,
    }


def seitenbilder(path: Path, dpi: int = 110) -> list[bytes]:
    """Belegseiten als PNG für die Vorschau (unabhängig vom PDF-Betrachter des Browsers)."""
    import pymupdf

    if path.suffix.lower() == ".xml":
        return []
    with pymupdf.open(path) as doc:
        if doc.is_pdf:
            return [page.get_pixmap(dpi=dpi).tobytes("png") for page in doc]
        return [doc[0].get_pixmap().tobytes("png")]  # Bilddatei


def verarbeite_upload(content: bytes, filename: str, client_id: str, modell: str) -> dict[str, Any]:
    suffix = Path(filename).suffix.lower() or ".pdf"
    if suffix not in (".pdf", ".xml", ".jpg", ".jpeg", ".png", ".tif", ".tiff"):
        raise ValueError("Dateityp nicht unterstützt")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"beleg{suffix}"
        path.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        bekannt = next((b for b in testbelege()
                        if hashlib.sha256((TESTDATEN / b["datei"]).read_bytes()).hexdigest() == digest), None)
        result = verarbeite(path, bekannt["client_id"] if bekannt else client_id, modell,
                            bekannt["erwartet"] if bekannt else None)
        result["seiten"] = ["data:image/png;base64," + base64.b64encode(png).decode() for png in seitenbilder(path)]
        return result
