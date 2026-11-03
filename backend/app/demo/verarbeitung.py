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
from app.erechnung.validierung import validiere
from app.kontierung.betraege import parse_amount
from app.kontierung.konten import load_accounts, normalize_lines
from app.kontierung import pflichtangaben
from app.kontierung.steuerlogik import pruefe_summen
from app.kontierung.steuerschluessel import steuerfall
from app.llm.base import LLMProvider
from app.llm.placeholder import PlaceholderProvider
from app.llm.replay import ReplayProvider
from app.ocr import kopfangaben
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


def mandant_profil(client_id: str) -> dict[str, Any]:
    """Angaben des Mandanten für die Pseudonymisierung. Neu erfasste Mandanten (Kanzlei-Stammdaten) haben
    nur Name und Ansprechpartner."""
    from app.demo import kanzlei

    m = kanzlei.mandant(client_id)
    if client_id in mandanten():
        return {**mandanten()[client_id], "vat_id": m.get("ustid") or mandanten()[client_id]["vat_id"]}
    return {"name": m["name"], "person": m.get("ansprechpartner") or m["name"], "street": "", "postcode": "",
            "city": "", "vat_id": m.get("ustid") or "", "industry_code": "", "branche": m.get("branche", "")}


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
                        "erwartet": {**gold["erwartet"], **doc.get("abweichend", {})},
                        # KoSIT-Dateien enthalten Platzhalter wie „[Seller name]“; für die Anzeige der erfundene Name
                        "anzeige_lieferant": gold["erwartet"].get("supplier_name")})
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

    client = mandant_profil(client_id)
    accounts = load_accounts("SKR03")
    names, _ = _konten()
    ki: dict[str, Any] = {}
    pseudo_text = ""
    platzhalter: dict[str, int] = {}

    if path.suffix.lower() == ".xml":
        t0 = time.perf_counter()
        voll = parse_file(path)
        data: dict[str, Any] | None = without_parties(voll)
        verkaeufer = (voll.get("parties") or {}).get("seller") or {}
        kaeufer: dict[str, Any] | None = (voll.get("parties") or {}).get("buyer") or {}
        roh = raw.decode("utf-8", errors="replace")
        if re.search(r">K</(?:cbc:ID|ram:CategoryCode)>", roh):  # Steuerkategorie K: innergemeinschaftliche Lieferung
            roh += " innergemeinschaftliche Lieferung"
        lieferant_ustid, land, leistung = verkaeufer.get("vat_id"), verkaeufer.get("country"), voll.get("service_period")
        schritt("Auslesen", t0, "E-Rechnung (XML) direkt gelesen, keine KI nötig")
        t0 = time.perf_counter()
        validierung = validiere(path)
        schritt("Validierung", t0, "XRechnung-Prüfregeln der KoSIT" + (" bestanden" if validierung["gueltig"] else " nicht bestanden"))
        quelle = "e-rechnung"
        ki = {"art": "keine", "text": "E-Rechnung: strukturierte Daten, kein KI-Aufruf"}
    else:
        t0 = time.perf_counter()
        read = read_document(path)
        schritt("Auslesen", t0, "PDF-Textlayer" if read.method == "textlayer" else "Texterkennung (docTR, lokal)")
        roh, land, leistung = read.text, None, None
        verkaeufer, kaeufer = None, None
        validierung = None
        lieferant_ustid = kopfangaben.lieferanten_ustid(read.text, (client["vat_id"],))

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
    herkunft = kopfangaben.herkunft(roh, lieferant_ustid, land)
    check = pruefe_summen(data, auslaendisch=herkunft in ("eu", "drittland")) if data else None
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

    # Kopfangaben lokal aus dem Belegtext (ohne KI): Leistungsdatum, Währung, Herkunft, Steuerfall
    d = data or {}
    if leistung is None:
        leistung = kopfangaben.leistungsdatum(roh, d.get("invoice_date"))
    saetze = [parse_amount(ln.get("tax_rate")) for ln in d.get("lines") or []]
    kopf_lokal = {"currency": kopfangaben.waehrung(roh, d.get("currency")), "leistung": leistung,
                  "herkunft": herkunft, "lieferant_ustid": lieferant_ustid,
                  "steuerfall": steuerfall(bool(d.get("reverse_charge")), herkunft, roh, saetze)}

    kopf = {k: d.get(k) for k in ("supplier_name", "invoice_number", "invoice_date", "document_type",
                                  "net_total", "tax_total", "gross_total", "reverse_charge")} | kopf_lokal
    # Pflichtangaben nach § 14 UStG, §§ 31, 33 UStDV: lokal aus Belegtext bzw. E-Rechnung, nie über die KI
    pflicht = pflichtangaben.pruefe(kopf, d.get("lines") or [], roh, client,
                                    verkaeufer if quelle == "e-rechnung" else None, kaeufer, bool(check and check.ok))

    gesamt = gesamtampel(check.ok if check else False, positionen, quelle)
    soll = None
    if erwartet:
        v = compare(erwartet, data)
        soll = {"pflichtfelder": [sum(v["felder"].values()), len(v["felder"])],
                "positionen": v["positionen"]["betrag"], "konten": v["positionen"]["konto"],
                "abweichend": [k for k, ok in v["felder"].items() if not ok]}

    return {
        "sha256": digest, "quelle": quelle, "ki": ki, "schritte": schritte,
        "kopf": kopf, "pflichtangaben": pflicht, "validierung": validierung,
        "positionen": positionen, "steuerlogik": {"ok": bool(check and check.ok), "hinweise": check.hinweise if check else []},
        "ampel": gesamt, "pseudonymisiert": pseudo_text, "platzhalter": platzhalter, "soll": soll,
    }


@lru_cache(maxsize=128)
def positionsrahmen(path: Path, beschreibungen: tuple[str, ...]) -> list[list[dict[str, float]]]:
    """Wo steht welche Position auf dem Beleg? Sucht die ersten Wörter jeder Bezeichnung im PDF-Textlayer und gibt
    die Zeile als Rechteck relativ zur Seite zurück (0–1). Scans, Fotos und E-Rechnungen: keine Markierung."""
    import pymupdf

    leer: list[list[dict[str, float]]] = [[] for _ in beschreibungen]
    if path.suffix.lower() != ".pdf":
        return leer
    out: list[list[dict[str, float]]] = []
    belegt: set[tuple[int, int]] = set()
    with pymupdf.open(path) as doc:
        if not any(page.get_text().strip() for page in doc):
            return leer
        for text in beschreibungen:
            suche = " ".join((text or "").split()[:4])[:40]
            treffer: list[dict[str, float]] = []
            for nr, page in enumerate(doc):
                if not suche or treffer:
                    break
                for r in page.search_for(suche):
                    if (nr, round(r.y0)) in belegt:  # gleiche Bezeichnung zweimal: nächste Fundstelle
                        continue
                    belegt.add((nr, round(r.y0)))
                    h = page.rect.height
                    treffer.append({"seite": nr, "x0": 0.04, "x1": 0.96, "y0": max(0.0, (r.y0 - 2) / h),
                                    "y1": min(1.0, (r.y1 + 2) / h)})
                    break
            out.append(treffer)
    return out


def _rahmen(nr: int, box: tuple[float, float, float, float], w: float, h: float) -> dict[str, float]:
    x0, y0, x1, y1 = box
    return {"seite": nr, "x0": max(0.0, (x0 - 3) / w), "x1": min(1.0, (x1 + 3) / w),
            "y0": max(0.0, (y0 - 2) / h), "y1": min(1.0, (y1 + 2) / h)}


def _vereinen(boxen: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return min(b[0] for b in boxen), min(b[1] for b in boxen), max(b[2] for b in boxen), max(b[3] for b in boxen)


def feldrahmen(path: Path, suche: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Wo stehen die Kopfangaben auf dem Beleg? Für die Hervorhebung beim Überfahren der Rechnungsprüfung.

    Liest die Zeilen des PDF-Textlayers; eine Zeile zählt mit allen Zeilen auf gleicher Höhe (Tabellen: Bezeichnung
    links, Wert rechts). Ergebnis je Schlüssel: Rechtecke relativ zur Seite (0–1) und der gefundene Text.
    Scans, Fotos und E-Rechnungen: leer (E-Rechnungen markiert das Belegbild selbst)."""
    import pymupdf

    if path.suffix.lower() != ".pdf":
        return {}
    zeilen: list[tuple[int, tuple[float, float, float, float], str, float, float]] = []
    bloecke: list[tuple[int, tuple[float, float, float, float], str, float, float]] = []
    with pymupdf.open(path) as doc:
        for nr, page in enumerate(doc):
            w, h = page.rect.width, page.rect.height
            for b in page.get_text("dict")["blocks"]:
                if b.get("type") != 0:
                    continue
                texte = []
                for ln in b["lines"]:
                    t = "".join(s["text"] for s in ln["spans"]).strip()
                    if t:
                        zeilen.append((nr, tuple(ln["bbox"]), t, w, h))
                        texte.append(t)
                if texte:
                    bloecke.append((nr, tuple(b["bbox"]), "\n".join(texte), w, h))
    if not zeilen:
        return {}
    zeilen.sort(key=lambda z: (z[0], round(z[1][1]), z[1][0]))
    bloecke.sort(key=lambda z: (z[0], z[1][1], z[1][0]))
    kompakt = lambda t: re.sub(r"\s+", "", t).lower()  # noqa: E731

    def reihe(z: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        """Alle Zeilen auf gleicher Höhe (Mitte innerhalb der Zeile)."""
        y0, y1 = z[1][1], z[1][3]
        return [o for o in zeilen if o[0] == z[0] and y0 - 1 <= (o[1][1] + o[1][3]) / 2 <= y1 + 1]

    out: dict[str, dict[str, Any]] = {}
    for key, s in suche.items():
        werte = [kompakt(v) for v in s.get("werte", []) if v]
        muster = re.compile(s["muster"]) if s.get("muster") else None
        if not werte and not muster:
            continue
        if s.get("art") == "block":
            treffer_b = next((b for b in bloecke if any(v in kompakt(b[2]) for v in werte)), None)
            if not treffer_b:
                continue
            boxen = [treffer_b[1]]
            for b in bloecke:  # Anschrift: direkt folgende Absätze darunter gehören dazu
                if b[0] == treffer_b[0] and b[1][1] > boxen[-1][1] and 0 <= b[1][1] - boxen[-1][3] < 6 \
                        and b[1][0] < treffer_b[1][2] and b[1][2] > treffer_b[1][0]:
                    boxen.append(b[1])
            out[key] = {"rahmen": [_rahmen(treffer_b[0], _vereinen(boxen), treffer_b[3], treffer_b[4])],
                        "text": treffer_b[2]}
            continue
        kandidaten = [z for z in zeilen if any(v in kompakt(z[2]) for v in werte) or (muster and muster.search(z[2]))]
        if not kandidaten:
            continue
        if s.get("art") == "alle":
            out[key] = {"rahmen": [_rahmen(z[0], _vereinen([o[1] for o in reihe(z)]), z[3], z[4]) for z in kandidaten],
                        "text": "\n".join(z[2] for z in kandidaten[:4])}
            continue

        def punkte(z: tuple[Any, ...]) -> int:
            text = " ".join(o[2] for o in reihe(z)).lower()
            return sum(w in text for w in s.get("worte", [])) - 2 * sum(w in text for w in s.get("nicht", []))

        beste = max(punkte(z) for z in kandidaten)
        gewaehlt = [z for z in kandidaten if punkte(z) == beste]
        z = gewaehlt[-1] if s.get("letzte") else gewaehlt[0]
        r = reihe(z)
        out[key] = {"rahmen": [_rahmen(z[0], _vereinen([o[1] for o in r]), z[3], z[4])],
                    "text": " ".join(o[2] for o in r)}
    return out


@lru_cache(maxsize=64)
def seitenbilder(path: Path, dpi: int = 110) -> list[bytes]:
    """Belegseiten als PNG für die Vorschau (unabhängig vom PDF-Betrachter des Browsers). 200 dpi beim Vergrößern."""
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
