"""DATEV-Format: Buchungsstapel (Kennzeichen EXTF, Version 700, Formatkategorie 21, Formatversion 13).

Aufbau (CLAUDE.md Abschnitt 7): Zeile 1 Kopfsatz, Zeile 2 Spaltenüberschriften, ab Zeile 3 Buchungen.
Semikolon als Trenner, Textfelder in Anführungszeichen (Anführungszeichen im Text verdoppelt), Zeilenende CR LF,
Kodierung Windows-1252. Umsatz ohne Vorzeichen mit Dezimalkomma in Belegwährung, Richtung über das
Soll/Haben-Kennzeichen; bei Fremdwährung Währung (Feld 3) und Kurs in Mengennotierung (Feld 4), DATEV rechnet beim
Import in Euro um. Belegdatum TTMM (Jahr aus dem Zeitraum des Kopfsatzes), Leistungsdatum TTMMJJJJ.

Stand und Quellen: docs/datev/buchungsstapel.md. Die offizielle Formatbeschreibung aus dem DATEV Developer Portal
liegt noch nicht vor; Spaltenliste und Feldbedeutungen stammen aus übereinstimmenden Sekundärquellen. Vor dem Pilot:
Abgleich mit der Formatbeschreibung und Testimport in DATEV Kanzlei-Rechnungswesen (Gate Phase 4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

KODIERUNG = "cp1252"

# Spalten 1–124 des Buchungsstapels (Quelle: Feldliste OBS-Wiki, siehe docs/datev/buchungsstapel.md)
SPALTEN = [
    "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs", "Basisumsatz", "WKZ Basisumsatz",
    "Konto", "Gegenkonto (ohne BU-Schlüssel)", "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
    "Buchungstext", "Postensperre", "Diverse Adressnummer", "Geschäftspartnerbank", "Sachverhalt", "Zinssperre",
    "Beleglink",
    *[f"Beleginfo - {art} {n}" for n in range(1, 9) for art in ("Art", "Inhalt")],
    "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost Menge", "EU-Land u. USt-IdNr. (Bestimmung)",
    "EU-Steuersatz (Bestimmung)", "Abw. Versteuerungsart", "Sachverhalt L+L", "Funktionsergänzung L+L",
    "BU 49 Hauptfunktionstyp", "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
    *[f"Zusatzinformation - {art} {n}" for n in range(1, 21) for art in ("Art", "Inhalt")],
    "Stück", "Gewicht", "Zahlweise", "Forderungsart", "Veranlagungsjahr", "Zugeordnete Fälligkeit", "Skontotyp",
    "Auftragsnummer", "Buchungstyp", "USt-Schlüssel (Anzahlungen)", "EU-Mitgliedstaat (Anzahlungen)",
    "Sachverhalt L+L (Anzahlungen)", "EU-Steuersatz (Anzahlungen)", "Erlöskonto (Anzahlungen)", "Herkunft-Kz",
    "Leerfeld", "KOST-Datum", "SEPA-Mandatsreferenz", "Skontosperre", "Gesellschaftername", "Beteiligtennummer",
    "Identifikationsnummer", "Zeichnernummer", "Postensperre bis", "Bezeichnung SoBil-Sachverhalt",
    "Kennzeichen SoBil-Buchung", "Festschreibung", "Leistungsdatum", "Datum Zuord. Steuerperiode", "Fälligkeit",
    "Generalumkehr", "Steuersatz", "Land", "Abrechnungsreferenz", "BVV-Position", "EU-Land u. USt-IdNr. (Ursprung)",
    "EU-Steuersatz (Ursprung)",
]
assert len(SPALTEN) == 124
# Spaltennummer (1-basiert) → Position in der Liste
UMSATZ, SH, WKZ, KURS, KONTO, GEGENKONTO, BU, BELEGDATUM, BELEGFELD1, BUCHUNGSTEXT = 0, 1, 2, 3, 6, 7, 8, 9, 10, 13
BELEGLINK, BELEGINFO_ART1, BELEGINFO_INHALT1, LEISTUNGSDATUM, EU_USTID_URSPRUNG = 19, 20, 21, 114, 122
_STEUERZEICHEN = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class Kopf:
    beraternummer: int
    mandantennummer: int
    wj_beginn: date
    sachkontenlaenge: int
    datum_von: date
    datum_bis: date
    bezeichnung: str
    kontenrahmen: str  # "SKR03" oder "SKR04"
    erzeugt: datetime


def _text(wert: Any, laenge: int | None = None) -> str:
    s = _STEUERZEICHEN.sub(" ", str(wert or "")).strip()
    if laenge:
        s = s[:laenge]
    return '"' + s.replace('"', '""') + '"'


def _betrag(wert: Decimal) -> str:
    return f"{abs(wert):.2f}".replace(".", ",")


def _kurs(wert: Any) -> str:
    return f"{Decimal(str(wert)):.6f}".replace(".", ",")


def kopfsatz(k: Kopf) -> list[str]:
    """31 Felder; leer bleibt, was die Quellen nicht eindeutig belegen."""
    felder = [""] * 31
    felder[0] = _text("EXTF")
    felder[1] = "700"
    felder[2] = "21"
    felder[3] = _text("Buchungsstapel")
    felder[4] = "13"
    felder[5] = k.erzeugt.strftime("%Y%m%d%H%M%S") + f"{k.erzeugt.microsecond // 1000:03d}"
    felder[10] = str(k.beraternummer)
    felder[11] = str(k.mandantennummer)
    felder[12] = k.wj_beginn.strftime("%Y%m%d")
    felder[13] = str(k.sachkontenlaenge)
    felder[14] = k.datum_von.strftime("%Y%m%d")
    felder[15] = k.datum_bis.strftime("%Y%m%d")
    felder[16] = _text(k.bezeichnung, 30)
    felder[18] = "1"   # Buchungstyp: Finanzbuchführung
    felder[19] = "0"   # Rechnungslegungszweck: unabhängig
    felder[20] = "0"   # keine Festschreibung: die Kanzlei kann in DATEV noch korrigieren (CLAUDE.md Regel 12)
    felder[21] = _text("EUR")
    felder[26] = _text(k.kontenrahmen[-2:])
    return felder


def buchungszeile(z: dict[str, Any]) -> list[str]:
    """Eine Zeile aus dem Buchungsstapel der Ansicht (Konto = Kreditor, Gegenkonto = Sachkonto).

    Zusätzlich: ``kurs`` bei Fremdwährung, ``leistungsdatum`` (ISO), ``eu_ustid`` (USt-IdNr. des Lieferanten bei
    i. g. Erwerb und § 13b aus dem EU-Ausland → „EU-Land u. USt-IdNr. (Ursprung)“), ``beleglink`` (DATEV-Kennung
    mit GUID aus dem Belegtransfer, z. B. ``BEDI "…"``) und ``beleginfo`` (Art, Inhalt) als Verweis auf das Original.
    """
    f = [""] * len(SPALTEN)
    wkz = (z.get("waehrung") or "EUR").upper()
    f[UMSATZ] = _betrag(Decimal(str(z["umsatz"])))
    f[SH] = _text(z["soll_haben"])
    f[WKZ] = _text("" if wkz == "EUR" else wkz)
    if wkz != "EUR":
        f[KURS] = _kurs(z["kurs"])
    f[KONTO] = str(z["konto"])
    f[GEGENKONTO] = str(z["gegenkonto"])
    f[BU] = _text(z.get("bu") or "")
    f[BELEGDATUM] = date.fromisoformat(z["belegdatum"]).strftime("%d%m")
    f[BELEGFELD1] = _text(z.get("belegfeld1"), 36)
    f[BUCHUNGSTEXT] = _text(z.get("buchungstext"), 60)
    f[BELEGLINK] = _text(z.get("beleglink"), 210)
    art, inhalt = z.get("beleginfo") or ("", "")
    f[BELEGINFO_ART1], f[BELEGINFO_INHALT1] = _text(art, 20), _text(inhalt, 210)
    if z.get("leistungsdatum"):
        f[LEISTUNGSDATUM] = date.fromisoformat(z["leistungsdatum"]).strftime("%d%m%Y")
    f[EU_USTID_URSPRUNG] = _text(re.sub(r"\s", "", z.get("eu_ustid") or "").upper(), 15)
    return f


def buchungsstapel(kopf: Kopf, zeilen: list[dict[str, Any]]) -> bytes:
    text = [";".join(kopfsatz(kopf)), ";".join(_text(s) for s in SPALTEN)]
    text += [";".join(buchungszeile(z)) for z in zeilen]
    return ("\r\n".join(text) + "\r\n").encode(KODIERUNG, errors="replace")


# --------------------------------------------------------------------------- Prüfskript


def _felder(zeile: str) -> list[str]:
    """Semikolon-getrennt, Anführungszeichen beachten."""
    out, aktuell, in_text, i = [], "", False, 0
    while i < len(zeile):
        c = zeile[i]
        if c == '"':
            if in_text and i + 1 < len(zeile) and zeile[i + 1] == '"':
                aktuell += '"'
                i += 1
            else:
                in_text = not in_text
        elif c == ";" and not in_text:
            out.append(aktuell)
            aktuell = ""
        else:
            aktuell += c
        i += 1
    out.append(aktuell)
    return out


def _datum_ok(text: str, form: str) -> bool:
    try:
        datetime.strptime(text, form)
        return True
    except ValueError:
        return False


def pruefe(daten: bytes) -> list[str]:
    """Prüft eine Exportdatei vor der Ausgabe (CLAUDE.md Abschnitt 7). Leere Liste = in Ordnung."""
    fehler: list[str] = []
    try:
        text = daten.decode(KODIERUNG)
    except UnicodeDecodeError:
        return ["Datei ist nicht in Windows-1252 kodiert"]
    if not text.endswith("\r\n") or "\n" in text.replace("\r\n", ""):
        fehler.append("Zeilenende muss CR LF sein")
    zeilen = text.rstrip("\r\n").split("\r\n")
    if len(zeilen) < 3:
        return fehler + ["Kopfsatz, Spaltenüberschriften und mindestens eine Buchung erwartet"]
    kopf = _felder(zeilen[0])
    if len(kopf) != 31 or kopf[:5] != ["EXTF", "700", "21", "Buchungsstapel", "13"]:
        fehler.append("Kopfsatz: EXTF, 700, 21, Buchungsstapel, 13 und 31 Felder erwartet")
    else:
        if not (kopf[10].isdigit() and 1001 <= int(kopf[10]) <= 9999999):
            fehler.append("Kopfsatz: Beraternummer 1001–9999999")
        if not (kopf[11].isdigit() and 1 <= int(kopf[11]) <= 99999):
            fehler.append("Kopfsatz: Mandantennummer 1–99999")
        if not (kopf[13].isdigit() and 4 <= int(kopf[13]) <= 8):
            fehler.append("Kopfsatz: Sachkontenlänge 4–8")
        for nr in (12, 14, 15):
            if not _datum_ok(kopf[nr], "%Y%m%d"):
                fehler.append(f"Kopfsatz: Feld {nr + 1} muss ein Datum JJJJMMTT sein")
        if not re.fullmatch(r"\d{17}", kopf[5]):
            fehler.append("Kopfsatz: Erzeugt am JJJJMMTTHHMMSSFFF")
        if all(_datum_ok(kopf[nr], "%Y%m%d") for nr in (12, 14, 15)) and not kopf[12] <= kopf[14] <= kopf[15]:
            fehler.append("Kopfsatz: Wirtschaftsjahresbeginn ≤ Datum von ≤ Datum bis")
    if _felder(zeilen[1]) != SPALTEN:
        fehler.append("Spaltenüberschriften stimmen nicht")
    laenge = int(kopf[13]) if len(kopf) > 13 and kopf[13].isdigit() else 4
    for n, zeile in enumerate(zeilen[2:], start=3):
        f = _felder(zeile)
        if len(f) != len(SPALTEN):
            fehler.append(f"Zeile {n}: {len(SPALTEN)} Felder erwartet, {len(f)} gefunden")
            continue
        if not re.fullmatch(r"\d+,\d{2}", f[UMSATZ]) or f[UMSATZ] == "0,00":
            fehler.append(f"Zeile {n}: Umsatz positiv mit Dezimalkomma, ohne Tausenderpunkt")
        if f[SH] not in ("S", "H"):
            fehler.append(f"Zeile {n}: Soll/Haben-Kennzeichen S oder H")
        if f[WKZ] and not (re.fullmatch(r"[A-Z]{3}", f[WKZ]) and re.fullmatch(r"\d{1,4},\d{6}", f[KURS])):
            fehler.append(f"Zeile {n}: Fremdwährung braucht Währungscode und Kurs (1 EUR = Kurs, 6 Nachkommastellen)")
        if not f[KONTO].isdigit() or len(f[KONTO]) != laenge + 1:
            fehler.append(f"Zeile {n}: Konto (Kreditor) muss {laenge + 1}-stellig sein")
        if not f[GEGENKONTO].isdigit() or len(f[GEGENKONTO]) != laenge:
            fehler.append(f"Zeile {n}: Gegenkonto (Sachkonto) muss {laenge}-stellig sein")
        if not re.fullmatch(r"\d{4}", f[BELEGDATUM]) or not (1 <= int(f[BELEGDATUM][:2]) <= 31 and 1 <= int(f[BELEGDATUM][2:]) <= 12):
            fehler.append(f"Zeile {n}: Belegdatum TTMM")
        if f[LEISTUNGSDATUM] and not _datum_ok(f[LEISTUNGSDATUM], "%d%m%Y"):
            fehler.append(f"Zeile {n}: Leistungsdatum TTMMJJJJ")
        if f[EU_USTID_URSPRUNG] and not re.fullmatch(r"[A-Z]{2}[0-9A-Z+*]{2,13}", f[EU_USTID_URSPRUNG]):
            fehler.append(f"Zeile {n}: EU-Land u. USt-IdNr.: Ländercode und Nummer")
        if len(f[BELEGFELD1]) > 36 or len(f[BUCHUNGSTEXT]) > 60:
            fehler.append(f"Zeile {n}: Belegfeld 1 höchstens 36, Buchungstext höchstens 60 Zeichen")
    return fehler
