"""Umrechnung von Rechnungen in Fremdwährung (deterministisch, CLAUDE.md Regel 15).

Maßgeblich für Umsatzsteuer und Vorsteuer ist der monatliche Durchschnittskurs des BMF für den Monat der Leistung
(§ 16 Abs. 6 UStG); die Kurse stehen in ``tabellen/umsatzsteuer_umrechnungskurse.json``. Fehlt der Monat, wird der
Kurs am Beleg von Hand eingetragen (z. B. Tageskurs mit Genehmigung des Finanzamts). Kurs in Mengennotierung:
1 Euro = Kurs Fremdwährung, wie im DATEV-Buchungsstapel (Feld 4).
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.kontierung.betraege import parse_amount, q2

TABELLE = Path(__file__).parent / "tabellen" / "umsatzsteuer_umrechnungskurse.json"
STELLEN = Decimal("0.000001")  # DATEV: bis zu 6 Nachkommastellen


@lru_cache(maxsize=1)
def _kurse() -> dict[str, dict[str, str]]:
    daten: dict[str, dict[str, str]] = json.loads(TABELLE.read_text(encoding="utf-8"))["kurse"]
    return daten


def bmf_kurs(waehrung: str, monat: str) -> Decimal | None:
    wert = _kurse().get(monat, {}).get(waehrung.upper())
    return Decimal(wert) if wert else None


def leistungsmonat(kopf: dict[str, Any]) -> str | None:
    """Monat der Leistung (Ende des Leistungszeitraums), sonst Rechnungsdatum."""
    leistung = kopf.get("leistung") or {}
    datum = leistung.get("bis") or leistung.get("von") or kopf.get("invoice_date")
    return str(datum)[:7] if datum else None


def kurs_pruefen(wert: Any) -> Decimal:
    k = parse_amount(wert)
    if k is None or k <= 0 or k >= 10000:
        raise ValueError("Kurs: positive Zahl, 1 Euro = Kurs Fremdwährung, z. B. 1,0812")
    return k.quantize(STELLEN, rounding=ROUND_HALF_UP)


def kurs_fuer(kopf: dict[str, Any], manuell: str | None) -> dict[str, Any] | None:
    """Kurs eines Belegs: None bei Euro; sonst Wert (oder None, wenn er fehlt), Quelle und Leistungsmonat."""
    waehrung = (kopf.get("currency") or "EUR").upper()
    if waehrung == "EUR":
        return None
    monat = leistungsmonat(kopf)
    bmf = bmf_kurs(waehrung, monat) if monat else None
    if manuell:
        wert, quelle = Decimal(manuell), "von Hand"
    elif bmf:
        wert, quelle = bmf, "BMF-Monatskurs"
    else:
        wert, quelle = None, None
    brutto = parse_amount(kopf.get("gross_total"))
    return {"waehrung": waehrung, "monat": monat, "wert": str(wert) if wert else None, "quelle": quelle,
            "bmf": str(bmf) if bmf else None,
            "brutto_eur": str(in_euro(brutto, wert)) if wert and brutto is not None else None}


def in_euro(betrag: Decimal, kurs: Decimal) -> Decimal:
    return q2(betrag / kurs)
