"""Kopfangaben, die lokal aus dem Belegtext gelesen werden (ohne KI): Leistungsdatum, Währung, Herkunft des Lieferanten.

- Leistungsdatum bzw. Leistungszeitraum (§ 14 Abs. 4 Nr. 6 UStG): wichtig für die Steuerentstehung bei
  Soll- und Istversteuerung. Fehlt es, steht oft „Leistungsdatum entspricht Rechnungsdatum“ auf dem Beleg.
- Währung: ISO-Code (EUR, USD, CHF, GBP …). Fremdwährung braucht eine Umrechnung in Euro.
- Herkunft (Inland, EU, Drittland) aus der USt-IdNr. des Lieferanten; entscheidet über den Steuerfall.
"""

from __future__ import annotations

import re
from typing import Any

from app.kontierung.steuerschluessel import herkunft_aus_ustid

_D = r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})"
_SCHLUESSEL = r"(?:Liefer-?\s*(?:und|/)\s*Leistungs(?:datum|zeitraum)|Leistungsdatum|Leistungszeitraum|Lieferdatum|" \
              r"Abrechnungszeitraum|Leistungsmonat|Liefertag|Service\s+period|Delivery\s+date|Date\s+of\s+supply)"
_ZEITRAUM = re.compile(rf"(?i){_SCHLUESSEL}\s*:?\s*(?:vom\s+)?(\d{{1,2}})\.(\d{{1,2}})\.(\d{{2,4}})?\s*(?:[-–]|bis)\s*{_D}")
_DATUM = re.compile(rf"(?i){_SCHLUESSEL}\s*:?\s*{_D}")
_MONAT = re.compile(rf"(?i){_SCHLUESSEL}\s*:?\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|"
                    r"November|Dezember)\s+(\d{4})")
_LANG = re.compile(rf"(?i){_SCHLUESSEL}\s*:?\s*(\d{{1,2}})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|"
                   r"September|Oktober|November|Dezember)\s+(\d{4})")
_ENGLISCH = re.compile(rf"(?i){_SCHLUESSEL}\s*:?\s*(January|February|March|April|May|June|July|August|September|"
                       r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})")
_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
           "november", "december"]
_WIE_RECHNUNG = re.compile(r"(?i)(?:leistungs|liefer)\w*\s+(?:datum\s+)?(?:entspricht|=|gleich)\s+(?:dem\s+)?rechnungsdatum")
_MONATE = ["januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november",
           "dezember"]
_LETZTER = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_WAEHRUNG = [("USD", r"\bUSD\b|US\$|\$\s?\d|\d\s?\$"), ("CHF", r"\bCHF\b|\bSFr\b"), ("GBP", r"\bGBP\b|£"),
             ("PLN", r"\bPLN\b|\bzł\b"), ("CZK", r"\bCZK\b|\bKč\b")]
_USTID = re.compile(r"(?i:USt-?Id(?:Nr|ent)?\.?(?:-?Nr\.?)?|VAT(?:\s+(?:ID|No\.?|number|reg\.?\s*no\.?))?|UID)\s*:?\s*"
                    r"([A-Z]{2}(?:\s?[0-9A-Z]){8,12})(?![0-9A-Za-z])")
_DRITTLAND = re.compile(r"(?i)\b(USA|United States|Vereinigte Staaten|Schweiz|Switzerland|United Kingdom|"
                        r"Großbritannien|Norwegen|Norway|Kanada|Canada|Japan|China|Indien|Türkei)\b")


def _iso(t: str, m: str, j: str) -> str:
    jahr = int(j) + (2000 if len(j) == 2 else 0)
    return f"{jahr:04d}-{int(m):02d}-{int(t):02d}"


def leistungsdatum(text: str, rechnungsdatum: str | None) -> dict[str, Any] | None:
    """{"von", "bis", "art"}: art = „beleg“ (auf dem Beleg angegeben) oder „wie_rechnung“ (laut Hinweis)."""
    if m := _ZEITRAUM.search(text):
        t1, m1, j1, t2, m2, j2 = m.groups()
        return {"von": _iso(t1, m1, j1 or j2), "bis": _iso(t2, m2, j2), "art": "beleg"}
    if m := _MONAT.search(text):
        nr = _MONATE.index(m.group(1).lower()) + 1
        jahr = int(m.group(2))
        tage = 29 if nr == 2 and jahr % 4 == 0 else (28 if nr == 2 else _LETZTER[nr - 1])
        return {"von": f"{jahr}-{nr:02d}-01", "bis": f"{jahr}-{nr:02d}-{tage}", "art": "beleg"}
    if m := _DATUM.search(text):
        return {"von": _iso(*m.groups()), "bis": None, "art": "beleg"}
    if m := _LANG.search(text):  # „26. Oktober 2026“
        return {"von": _iso(m.group(1), str(_MONATE.index(m.group(2).lower()) + 1), m.group(3)), "bis": None, "art": "beleg"}
    if m := _ENGLISCH.search(text):  # „November 2, 2026“
        return {"von": _iso(m.group(2), str(_MONTHS.index(m.group(1).lower()) + 1), m.group(3)), "bis": None, "art": "beleg"}
    if rechnungsdatum and _WIE_RECHNUNG.search(text):
        return {"von": rechnungsdatum, "bis": None, "art": "wie_rechnung"}
    return None


def waehrung(text: str, angabe: str | None) -> str:
    """Währung laut KI bzw. E-Rechnung; ein Fremdwährungszeichen im Text hat Vorrang vor „EUR“ als Vorgabe."""
    if angabe and angabe.upper() != "EUR":
        return angabe.upper()
    if re.search(r"€|\bEUR\b", text):
        return "EUR"
    for code, muster in _WAEHRUNG:
        if re.search(muster, text):
            return code
    return (angabe or "EUR").upper()


def lieferanten_ustid(text: str, eigene: tuple[str, ...] = ()) -> str | None:
    """Erste USt-IdNr. im Text, die nicht dem Mandanten gehört."""
    eigen = {re.sub(r"\s", "", e.upper()) for e in eigene}
    for m in _USTID.finditer(text):
        nr = re.sub(r"\s", "", m.group(1).upper())
        if nr not in eigen:
            return nr
    return None


def herkunft(text: str, ustid: str | None, land: str | None = None) -> str:
    if h := herkunft_aus_ustid(ustid):
        return h
    if land:
        return herkunft_aus_ustid(land + "0") or "inland"
    return "drittland" if _DRITTLAND.search(text) else "inland"
