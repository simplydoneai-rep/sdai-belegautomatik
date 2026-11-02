"""Prüfung der Pflichtangaben einer Eingangsrechnung, deterministisch (CLAUDE.md Abschnitt 6, Regel 15).

Rechtsgrundlagen (gesetze-im-internet.de, Stand 02.11.2026):
- § 14 Abs. 4 Satz 1 UStG: Pflichtangaben jeder Rechnung (Nr. 1–8; Nr. 9 und 10 betreffen Sonderfälle).
- § 14a UStG: zusätzliche Angaben, u. a. Hinweis „Steuerschuldnerschaft des Leistungsempfängers“ (§ 13b) und
  USt-IdNr. beider Seiten bei innergemeinschaftlichen Lieferungen.
- § 31 UStDV: Name und Anschrift genügen, wenn eindeutig feststellbar; Abkürzungen zulässig; als Leistungszeitpunkt
  genügt der Kalendermonat.
- § 33 UStDV: Kleinbetragsrechnung bis 250 € brutto: nur Name und Anschrift des Leistenden, Ausstellungsdatum,
  Menge und Art, Entgelt und Steuerbetrag in einer Summe und Steuersatz (bzw. Hinweis auf Befreiung).
- § 15 Abs. 1 Satz 1 Nr. 4 UStG: Bei § 13b hängt der Vorsteuerabzug nicht an einer ordnungsgemäßen Rechnung;
  fehlende Angaben sind dann nur ein Hinweis.

Gelesen wird lokal aus dem Belegtext bzw. der E-Rechnung, nie über die KI.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from rapidfuzz import fuzz

from app.kontierung.betraege import parse_amount

KLEINBETRAG = Decimal("250")
_ANSCHRIFT = re.compile(r"\b\d{4,5}\s+[A-ZÄÖÜ][\wäöüß.-]+|\b[A-Z]{2}\s\d{5}\b|\b[A-Z]{1,2}\d[\dA-Z]?\s\d[A-Z]{2}\b")
_STEUERNUMMER = re.compile(r"\b\d{2,3}/\d{3,4}/\d{4,5}\b")
_BEFREIUNG = re.compile(r"(?i)steuerfrei|steuerbefrei|§\s*4\s*nr|§\s*19\s*ustg|kleinunternehmer|reverse\s+charge|"
                        r"steuerschuldnerschaft|art\.?\s*138|innergemeinschaftlich|nicht\s+steuerbar")
_RC_HINWEIS = re.compile(r"(?i)steuerschuldnerschaft\s+des\s+leistungsempf|reverse\s+charge")
_SKONTO = re.compile(r"(?i)skonto")

PUNKTE = [
    ("leistender", "Name und Anschrift des Lieferanten", "§ 14 Abs. 4 Nr. 1 UStG"),
    ("empfaenger", "Name und Anschrift des Mandanten", "§ 14 Abs. 4 Nr. 1 UStG"),
    ("steuernummer", "Steuernummer / USt-IdNr. des Lieferanten", "§ 14 Abs. 4 Nr. 2 UStG"),
    ("datum", "Rechnungsdatum", "§ 14 Abs. 4 Nr. 3 UStG"),
    ("nummer", "Fortlaufende Rechnungsnummer", "§ 14 Abs. 4 Nr. 4 UStG"),
    ("menge_art", "Menge und Art der Leistung", "§ 14 Abs. 4 Nr. 5 UStG"),
    ("leistungszeit", "Zeitpunkt der Leistung", "§ 14 Abs. 4 Nr. 6 UStG, § 31 Abs. 4 UStDV"),
    ("entgelt", "Entgelt je Steuersatz", "§ 14 Abs. 4 Nr. 7 UStG"),
    ("steuer", "Steuersatz und Steuerbetrag", "§ 14 Abs. 4 Nr. 8 UStG"),
]
KLEIN_PFLICHT = {"leistender", "datum", "menge_art", "steuer"}  # § 33 UStDV


def _im_text(name: str | None, text: str) -> bool:
    return bool(name) and fuzz.partial_ratio(str(name).lower(), text.lower()) >= 90


def pruefe(kopf: dict[str, Any], positionen: list[dict[str, Any]], text: str, mandant: dict[str, Any],
           verkaeufer: dict[str, Any] | None, kaeufer: dict[str, Any] | None, summen_ok: bool) -> dict[str, Any]:
    """Ergebnis je Pflichtangabe: ok, fehlt, hinweis (fehlt, aber ohne Folgen) oder entfaellt."""
    brutto = parse_amount(kopf.get("gross_total"))
    fall = kopf.get("steuerfall") or "inland"
    klein = brutto is not None and abs(brutto) <= KLEINBETRAG and fall not in ("13b", "ige")
    saetze = [parse_amount(p.get("tax_rate")) for p in positionen]
    kopfteil = "\n".join(text.splitlines()[:8])
    e_rechnung = verkaeufer is not None

    def adresse(partei: dict[str, Any] | None) -> bool:
        return bool(partei and (partei.get("city") or partei.get("postcode") or partei.get("street")))

    erfuellt: dict[str, tuple[bool, str]] = {
        "leistender": (bool(kopf.get("supplier_name")) and (adresse(verkaeufer) if e_rechnung else bool(_ANSCHRIFT.search(kopfteil))),
                       kopf.get("supplier_name") or ""),
        "empfaenger": ((bool(kaeufer and kaeufer.get("name")) and adresse(kaeufer)) if e_rechnung
                       else _im_text(mandant.get("name"), text)
                       and (not mandant.get("postcode") or mandant["postcode"] in text), mandant.get("name") or ""),
        "steuernummer": (bool(kopf.get("lieferant_ustid") or _STEUERNUMMER.search(text)),
                         kopf.get("lieferant_ustid") or (m.group(0) if (m := _STEUERNUMMER.search(text)) else "")),
        "datum": (bool(kopf.get("invoice_date")), kopf.get("invoice_date") or ""),
        "nummer": (bool(kopf.get("invoice_number")), kopf.get("invoice_number") or ""),
        "menge_art": (bool(positionen) and all(p.get("description") and (p.get("quantity") or p.get("unit"))
                                                 for p in positionen), f"{len(positionen)} Positionen"),
        "leistungszeit": (bool(kopf.get("leistung")), ""),
        "entgelt": (kopf.get("net_total") is not None and all(s is not None for s in saetze),
                    "Skonto angegeben" if _SKONTO.search(text) else ""),
        "steuer": ((kopf.get("tax_total") is not None and parse_amount(kopf.get("tax_total")) != 0)
                   if any(s for s in saetze) else bool(_BEFREIUNG.search(text)),
                   ", ".join(sorted({f"{s.normalize()} %" for s in saetze if s is not None}))),
    }
    punkte = []
    for key, text_punkt, grundlage in PUNKTE:
        ok, detail = erfuellt[key]
        if klein and key not in KLEIN_PFLICHT:
            status = "entfaellt"
        elif ok:
            status = "ok"
        else:
            status = "hinweis" if fall == "13b" else "fehlt"
        punkte.append({"key": key, "text": text_punkt, "grundlage": grundlage, "status": status, "detail": detail})

    if fall == "13b":
        ok = bool(_RC_HINWEIS.search(text))
        punkte.append({"key": "hinweis_13b", "text": "Hinweis auf Reverse Charge",
                       "grundlage": "§ 14a Abs. 5 UStG", "status": "ok" if ok else "hinweis",
                       "detail": "" if ok else "fehlt; Steuer schuldet der Mandant trotzdem"})
    if fall == "ige":
        ok = bool(kopf.get("lieferant_ustid")) and bool(mandant.get("vat_id")) and mandant["vat_id"] in text.replace(" ", "")
        punkte.append({"key": "ustid_beide", "text": "USt-IdNr. von Lieferant und Mandant",
                       "grundlage": "§ 14a Abs. 3 UStG", "status": "ok" if ok else "fehlt", "detail": ""})
    punkte.append({"key": "rechnerisch", "text": "Rechnerisch richtig",
                   "grundlage": "Prüfung", "status": "ok" if summen_ok else "fehlt", "detail": ""})

    fehlt = [p["text"] for p in punkte if p["status"] == "fehlt"]
    art = "kleinbetrag" if klein else "voll"
    return {"art": art, "punkte": punkte, "fehlt": fehlt,
            "grundlage": "§ 33 UStDV (Kleinbetragsrechnung)" if klein else "§ 14 Abs. 4 UStG, § 31 UStDV",
            "e_rechnung": e_rechnung}
