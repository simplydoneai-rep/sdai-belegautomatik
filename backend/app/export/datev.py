"""DATEV-Format: Buchungsstapel (Kennzeichen EXTF, Version 700, Formatkategorie 21, Formatversion 13).

Aufbau (CLAUDE.md Abschnitt 7): Zeile 1 Kopfsatz, Zeile 2 Spaltenüberschriften, ab Zeile 3 Buchungen.
Semikolon als Trenner, Textfelder in Anführungszeichen (Anführungszeichen im Text verdoppelt), Zeilenende CR LF,
Kodierung Windows-1252. Umsatz ohne Vorzeichen mit Dezimalkomma, Richtung über das Soll/Haben-Kennzeichen;
Belegdatum TTMM (Jahr aus dem Zeitraum des Kopfsatzes).

Stand und Quellen: siehe docs/datev/buchungsstapel.md. Die offizielle Formatbeschreibung aus dem DATEV Developer
Portal liegt noch nicht vor; geschrieben werden nur der Kopfsatz und die Spalten 1–14, die in den Quellen
übereinstimmend beschrieben sind. Vor dem Pilot: Abgleich mit der Formatbeschreibung und Testimport in
DATEV Kanzlei-Rechnungswesen (Gate Phase 4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

KODIERUNG = "cp1252"
SPALTEN = [
    "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs", "Basis-Umsatz", "WKZ Basis-Umsatz",
    "Konto", "Gegenkonto (ohne BU-Schlüssel)", "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
    "Buchungstext",
]
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
    """Eine Zeile aus dem Buchungsstapel der Ansicht (Konto = Kreditor, Gegenkonto = Sachkonto)."""
    umsatz = Decimal(str(z["umsatz"]))
    belegdatum = date.fromisoformat(z["belegdatum"])
    wkz = z.get("waehrung") or "EUR"
    return [
        _betrag(umsatz), _text(z["soll_haben"]), _text("" if wkz == "EUR" else wkz), "", "", "",
        str(z["konto"]), str(z["gegenkonto"]), _text(z.get("bu") or ""), belegdatum.strftime("%d%m"),
        _text(z.get("belegfeld1"), 36), "", "", _text(z.get("buchungstext"), 60),
    ]


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
        for nr in (5, 12, 14, 15):
            if not re.fullmatch(r"\d{8}(\d{9})?", kopf[nr]):
                fehler.append(f"Kopfsatz: Feld {nr + 1} muss ein Datum JJJJMMTT sein")
    if _felder(zeilen[1]) != SPALTEN:
        fehler.append("Spaltenüberschriften stimmen nicht")
    laenge = int(kopf[13]) if len(kopf) > 13 and kopf[13].isdigit() else 4
    for n, zeile in enumerate(zeilen[2:], start=3):
        f = _felder(zeile)
        if len(f) != len(SPALTEN):
            fehler.append(f"Zeile {n}: {len(SPALTEN)} Felder erwartet, {len(f)} gefunden")
            continue
        if not re.fullmatch(r"\d+,\d{2}", f[0]) or f[0] == "0,00":
            fehler.append(f"Zeile {n}: Umsatz positiv mit Dezimalkomma, ohne Tausenderpunkt")
        if f[1] not in ("S", "H"):
            fehler.append(f"Zeile {n}: Soll/Haben-Kennzeichen S oder H")
        if not f[6].isdigit() or len(f[6]) != laenge + 1:
            fehler.append(f"Zeile {n}: Konto (Kreditor) muss {laenge + 1}-stellig sein")
        if not f[7].isdigit() or len(f[7]) != laenge:
            fehler.append(f"Zeile {n}: Gegenkonto (Sachkonto) muss {laenge}-stellig sein")
        if not re.fullmatch(r"\d{4}", f[9]) or not (1 <= int(f[9][:2]) <= 31 and 1 <= int(f[9][2:]) <= 12):
            fehler.append(f"Zeile {n}: Belegdatum TTMM")
        if len(f[10]) > 36 or len(f[13]) > 60:
            fehler.append(f"Zeile {n}: Belegfeld 1 höchstens 36, Buchungstext höchstens 60 Zeichen")
    return fehler
