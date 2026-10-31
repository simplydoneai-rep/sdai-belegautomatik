"""Liest den DATEV-Kontenrahmen SKR03 (Formular 11174, BilRUG, gültig 2026) aus der PDF.

Ergebnis: ``app/kontierung/tabellen/skr03_vollstaendig.json`` mit Kontonummer, Bezeichnung,
DATEV-Kennzeichen (z. B. AV = automatische Vorsteuer, AM = automatische Umsatzsteuer) und Bereich.
Reservierte Konten (Kennzeichen R) werden ausgelassen.

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/skr03_einlesen.py "<Pfad zur PDF>"``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

ZIEL = Path(__file__).resolve().parents[1] / "app" / "kontierung" / "tabellen" / "skr03_vollstaendig.json"
# Spalten je Seitenhälfte: Kontonummer ab x_min, Seitenhälfte bis x_max (aus dem Formular ausgemessen)
HAELFTEN = ((140.0, 295.0), (380.0, 612.0))
KOPF_Y, FUSS_Y = 112.0, 760.0
# Vor der Nummer kann die Spalte „Programmverbindung“ stehen (U, G, K), danach das Kennzeichen (AV, AM, S, F …)
START = re.compile(r"^(?:(?:U|G|K|KU)\s+)*(?:(?P<flag>(?:[A-Z]{1,2}/)?[A-Z]{1,2})\s+)?(?P<nr>\d{4})(?:\s+(?P<name>\S.*))?$")
BEREICH = re.compile(r"^-(?P<bis>\d{2,4})(?:\s+(?P<rest>\S.*))?$")
FUSSNOTE = re.compile(r"(\S)\d{1,2}\)")


KUERZEL = {"HB", "StB", "EÜR", "EB", "KU", "HB StB", "StB HB"}  # Spalte „Abschlusszweck“, kein Namensbestandteil


def zeilen(page: pymupdf.Page, x_min: float, x_max: float) -> list[tuple[float, str, bool]]:
    """Zeilen einer Seitenhälfte als (y, Text, fett), Teile gleicher Höhe zusammengeführt."""
    roh: list[tuple[float, float, str, bool]] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            x0, y0 = line["bbox"][0], line["bbox"][1]
            text = "".join(s["text"] for s in line["spans"]).strip()
            if not text or text in KUERZEL or not (x_min <= x0 < x_max and KOPF_Y < y0 < FUSS_Y):
                continue
            fett = all("Bold" in s["font"] for s in line["spans"] if s["text"].strip())
            roh.append((round(y0, 0), x0, text, fett))
    roh.sort()
    out: list[tuple[float, str, bool]] = []
    for y, _, text, fett in roh:
        if out and abs(out[-1][0] - y) <= 1:
            out[-1] = (out[-1][0], out[-1][1] + " " + text, out[-1][2] and fett)
        else:
            out.append((y, text, fett))
    return out


def anhaengen(name: str, teil: str) -> str:
    if not name:
        return teil
    # „Betriebs-“ + „und …“ ist ein Ergänzungsstrich, keine Silbentrennung
    if name.endswith("-") and teil[:1].islower() and not re.match(r"(und|oder|bzw\.?|sowie)\b", teil):
        return name[:-1] + teil
    return name + " " + teil


def einlesen(pdf: Path) -> list[dict[str, object]]:
    konten: dict[str, dict[str, object]] = {}
    with pymupdf.open(pdf) as doc:
        for page in doc:
            for x_min, x_max in HAELFTEN:
                aktuell: dict[str, object] | None = None
                aktuell_fett = False
                for _, text, fett in zeilen(page, x_min, x_max):
                    m = START.match(text)
                    if not m and fett and not aktuell_fett:
                        aktuell = None  # fette Zwischenüberschrift beendet die laufende Bezeichnung
                        continue
                    if m:
                        flag = m.group("flag") or ""
                        aktuell_fett = fett
                        aktuell = {"nr": m.group("nr"), "name": m.group("name") or "", "kennzeichen": flag}
                        if "R" in flag.split("/"):
                            aktuell = None  # reserviert
                        elif m.group("nr") not in konten:
                            konten[m.group("nr")] = aktuell
                        continue
                    b = BEREICH.match(text)
                    if b and aktuell is not None:
                        aktuell["bis"] = b.group("bis")
                        if b.group("rest"):
                            aktuell["name"] = anhaengen(str(aktuell["name"]), b.group("rest"))
                        continue
                    if aktuell is not None:
                        aktuell["name"] = anhaengen(str(aktuell["name"]), text)
    for k in konten.values():
        k["name"] = re.sub(r"\s+", " ", FUSSNOTE.sub(r"\1", str(k["name"]))).strip()
    return sorted((k for k in konten.values() if k["name"]), key=lambda k: str(k["nr"]))


def main() -> None:
    pdf = Path(sys.argv[1])
    konten = einlesen(pdf)
    ZIEL.write_text(json.dumps({
        "_meta": {"kontenrahmen": "SKR03",
                  "quelle": "DATEV-Kontenrahmen nach BilRUG, Standardkontenrahmen SKR 03, Art.-Nr. 11174, gültig für 2026",
                  "erzeugt_mit": "backend/scripts/skr03_einlesen.py",
                  "kennzeichen": {"AV": "Automatikkonto Vorsteuer", "AM": "Automatikkonto Umsatzsteuer",
                                  "S": "Sammelkonto", "F": "Konto mit allgemeiner Funktion"}},
        "konten": konten}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(konten)} Konten → {ZIEL}")


if __name__ == "__main__":
    main()
