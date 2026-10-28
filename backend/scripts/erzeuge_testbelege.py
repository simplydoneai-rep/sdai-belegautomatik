"""Erzeugt die Testbelege für den Machbarkeitstest.

- 20 synthetische PDF-Rechnungen erfundener Firmen nach ``testdaten/synthetisch/``
  (S18–S20 als schlechte Scans: Bild, schief, verrauscht)
- Sicht-PDFs zu 10 KoSIT-XRechnungen nach ``testdaten/kosit_sicht/``
- erwartete Ergebnisse je Beleg nach ``testdaten/goldstandard/``
- Mandanten-Stammdaten (erfunden) nach ``testdaten/mandanten.json``

Alle Namen, Anschriften, IBANs und Steuernummern sind erfunden. USt-IdNr. beginnen mit
DE999 bzw. ATU999, IBANs nutzen die Bankleitzahl 99999999 (nicht vergeben).

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/erzeuge_testbelege.py``
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pymupdf
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.erechnung.parser import parse_file  # noqa: E402
from app.kontierung.betraege import q2  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "testdaten"
D = Decimal

# --------------------------------------------------------------------------- Stammdaten (erfunden)

MANDANTEN: dict[str, dict[str, Any]] = {
    "M1": {"name": "Café Sonnenblick GmbH", "attn": "Frau Sabine Kowalczyk", "person": "Sabine Kowalczyk",
           "street": "Lindenallee 12", "postcode": "90402", "city": "Nürnberg", "vat_id": "DE999100001",
           "industry_code": "56.10", "branche": "Gastronomie (Café)"},
    "M2": {"name": "Kfz-Technik Albrecht GmbH", "attn": "Herrn Tobias Albrecht", "person": "Tobias Albrecht",
           "street": "Gewerbering 4", "postcode": "91052", "city": "Erlangen", "vat_id": "DE999100002",
           "industry_code": "45.20", "branche": "Kfz-Werkstatt"},
    "M3": {"name": "Holzbau Brenner GmbH", "attn": "Frau Martina Brenner", "person": "Martina Brenner",
           "street": "Sägewerkstraße 9", "postcode": "95444", "city": "Bayreuth", "vat_id": "DE999100003",
           "industry_code": "43.91", "branche": "Zimmerei, Dachdeckerei"},
    "M4": {"name": "Pixelwerk Design GmbH", "attn": "Frau Lea Brandt", "person": "Lea Brandt",
           "street": "Kreativhof 3", "postcode": "90763", "city": "Fürth", "vat_id": "DE999100004",
           "industry_code": "73.11", "branche": "Werbeagentur"},
    "M5": {"name": "Bäckerei Kornfeld KG", "attn": "Herrn Jonas Kornfeld", "person": "Jonas Kornfeld",
           "street": "Marktplatz 7", "postcode": "91126", "city": "Schwabach", "vat_id": "DE999100005",
           "industry_code": "10.71", "branche": "Bäckerei"},
    "M6": {"name": "Musterverwaltung Lohberg GmbH", "attn": "Herrn Felix Raabe", "person": "Felix Raabe",
           "street": "Am Rathausplatz 1", "postcode": "96047", "city": "Bamberg", "vat_id": "DE999100006",
           "industry_code": "70.10", "branche": "Verwaltung (Käufer der KoSIT-Belege)"},
}


def _iban(n: int) -> str:
    # Formal wie eine deutsche IBAN, BLZ 99999999 ist nicht vergeben.
    return f"DE{(n * 7) % 90 + 10:02d} 9999 9999 {n:04d} {n * 37 % 10000:04d} {n % 100:02d}"


def _supplier(i: int, name: str, street: str, city: str, person: str, gf: str, country: str = "DE",
              vat: str | None = None) -> dict[str, Any]:
    slug = name.split()[0].lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("&", "")
    return {
        "name": name, "street": street, "postcode_city": city, "country": country,
        "vat_id": vat or f"DE999200{i:03d}", "steuernr": f"241/{100 + i}/{50000 + i * 13}",
        "contact": person, "phone": f"+49 911 {4000 + i * 17} {100 + i}", "email": f"buchhaltung@{slug}-beispiel.de",
        "gf": gf, "hrb": f"HRB {30000 + i * 11}", "iban": _iban(i), "bic": "TESTDEFFXXX",
    }


SUPPLIERS = {
    "frischgut": _supplier(1, "Frischgut Großhandel GmbH", "Hafenstraße 21", "90451 Nürnberg", "Jonas Feldmann", "Petra Lindqvist"),
    "hanse": _supplier(2, "Getränke Hanse Vertrieb GmbH", "Brunnenweg 5", "90411 Nürnberg", "Mehmet Arslan", "Klaus Wendel"),
    "nordring": _supplier(3, "Teilezentrum Nordring GmbH", "Nordring 88", "90765 Fürth", "Svenja Haase", "Dirk Bremer"),
    "lackwerk": _supplier(4, "Lackwerk Südpark GmbH", "Südparkallee 14", "91058 Erlangen", "Olga Petrenko", "Rainer Voss"),
    "kessler": _supplier(5, "Gerüst & Ausbau Kessler GmbH", "Industriestraße 40", "95448 Bayreuth", "Marco Kessler", "Marco Kessler"),
    "waldmark": _supplier(6, "Holzhandel Waldmark GmbH", "Forstweg 2", "95463 Bindlach", "Heike Sommer", "Uwe Tanner"),
    "feinschnitt": _supplier(7, "Druckerei Feinschnitt GmbH", "Papiermühle 6", "90429 Nürnberg", "Timo Reuter", "Anja Pohl"),
    "cloudkontor": _supplier(8, "CloudKontor Software GmbH", "Datenpark 1", "91052 Erlangen", "Nina Okafor", "Sebastian Ruhl"),
    "hollerbach": _supplier(9, "Mühle Hollerbach GmbH & Co. KG", "Mühlweg 3", "91154 Roth", "Georg Hollerbach", "Georg Hollerbach"),
    "kranich": _supplier(10, "Bürowelt Kranich e.K.", "Königstraße 50", "90402 Nürnberg", "Ingrid Kranich", "Ingrid Kranich"),
    "talgrund": _supplier(11, "Energieversorgung Talgrund GmbH", "Kraftwerkstraße 1", "90449 Nürnberg", "Service-Team", "Dr. Helmut Grau"),
    "glanzpunkt": _supplier(12, "Reinigungsservice Glanzpunkt GmbH", "Gartenstraße 19", "90482 Nürnberg", "Aylin Demir", "Frank Becker"),
    "paragraph": _supplier(13, "Fachverlag Paragraphenreiter GmbH", "Verlagsplatz 2", "90403 Nürnberg", "Lukas Brenneis", "Carola Stein"),
    "funknetz": _supplier(14, "Funknetz Mitte GmbH", "Antennenweg 7", "91056 Erlangen", "Kundenservice", "Patrick Aumann"),
    "blitzkurier": _supplier(15, "Blitzkurier Mainfranken GmbH", "Zollhof 4", "97080 Würzburg", "Denis Wolf", "Denis Wolf"),
    "alpenholz": _supplier(16, "Alpenholz Handels GmbH", "Sägeweg 12", "6020 Innsbruck", "Florian Hofer", "Florian Hofer",
                           country="AT", vat="ATU99916016"),
    "ofenmeister": _supplier(17, "Bäckereibedarf Ofenmeister GmbH", "Backstubenweg 8", "90763 Fürth", "Rita Schuster", "Bernd Ofer"),
}

PAY_TERMS = "Zahlbar innerhalb von 14 Tagen ohne Abzug. Bei Zahlung innerhalb von 7 Tagen 2 % Skonto."

# Positionen: (Bezeichnung, Menge, Einheit, Einzelpreis netto, Steuersatz, Sachkonto SKR03)
INVOICES: list[dict[str, Any]] = [
    {"id": "S01", "sup": "frischgut", "client": "M1", "nr": "FG-2026-10412", "date": "2026-10-05", "tags": ["7 %"],
     "lines": [("Kaffeebohnen Espresso Röstung", "10", "kg", "18.90", 7, "3300"),
               ("Vollmilch 3,5 %", "60", "l", "1.09", 7, "3300"),
               ("Weizenmehl Type 405", "25", "kg", "0.85", 7, "3300"),
               ("Süßrahmbutter", "10", "kg", "7.40", 7, "3300")]},
    {"id": "S02", "sup": "hanse", "client": "M1", "nr": "GH-88213", "date": "2026-10-07", "tags": ["7 % und 19 %"],
     "lines": [("Mineralwasser medium 12 x 0,75 l", "12", "Kiste", "8.40", 19, "3400"),
               ("Apfelsaft naturtrüb 6 x 1,0 l", "6", "Kiste", "14.20", 19, "3400"),
               ("Vollmilch 3,8 % Barista", "48", "l", "1.19", 7, "3300")]},
    {"id": "S03", "sup": "nordring", "client": "M2", "nr": "TZN-261004-07", "date": "2026-10-04", "tags": ["19 %"],
     "lines": [("Bremsscheibe vorne belüftet", "2", "Stück", "64.50", 19, "3400"),
               ("Bremsbeläge Satz Vorderachse", "1", "Satz", "48.90", 19, "3400"),
               ("Motoröl 5W-30 Longlife", "20", "l", "6.80", 19, "3400"),
               ("Ölfilter", "4", "Stück", "7.25", 19, "3400")]},
    {"id": "S04", "sup": "lackwerk", "client": "M2", "nr": "LS/2026/3381", "date": "2026-10-09", "tags": ["19 %"],
     "lines": [("Basislack Farbton nach Muster", "4", "l", "58.00", 19, "3400"),
               ("Klarlack 2K HS", "5", "l", "39.50", 19, "3400"),
               ("Schleifpapier P800, Packung 50 Blatt", "2", "Pck", "18.90", 19, "3400")]},
    {"id": "S05", "sup": "kessler", "client": "M3", "nr": "K-2026-118", "date": "2026-10-12", "tags": ["Reverse Charge § 13b"],
     "reverse_charge": True,
     "notes": ["Steuerschuldnerschaft des Leistungsempfängers gemäß § 13b Abs. 2 Nr. 4 UStG.",
               "Die Umsatzsteuer schuldet der Leistungsempfänger."],
     "lines": [("Gerüststellung Bauvorhaben Ahornweg, Standzeit 4 Wochen", "1", "pauschal", "2450.00", 0, "3120"),
               ("Montage Dachrinne inkl. Fallrohr", "18", "m", "21.50", 0, "3120")]},
    {"id": "S06", "sup": "waldmark", "client": "M3", "nr": "WM-55120", "date": "2026-10-13", "tags": ["19 %"],
     "lines": [("Konstruktionsvollholz Fichte 80 x 160 mm", "8", "m³", "465.00", 19, "3400"),
               ("Dachlatten 30 x 50 mm imprägniert", "120", "m", "1.35", 19, "3400"),
               ("Holzbauschrauben 8 x 240, Karton", "6", "Karton", "12.40", 19, "3400")]},
    {"id": "S07", "sup": "feinschnitt", "client": "M4", "nr": "DF-2026-0931", "date": "2026-10-14", "tags": ["19 %"],
     "lines": [("Flyer DIN A5, 4/4-farbig, 135 g", "5000", "Stück", "0.042", 19, "4610"),
               ("Visitenkarten 85 x 55 mm", "500", "Stück", "0.09", 19, "4610"),
               ("Roll-up Display 85 x 200 cm", "1", "Stück", "89.00", 19, "4610")]},
    {"id": "S08", "sup": "cloudkontor", "client": "M4", "nr": "CK-INV-77031", "date": "2026-10-01", "tags": ["19 %", "Lizenz"],
     "lines": [("Designsoftware Pro, Jahreslizenz 11/2026–10/2027", "3", "Lizenz", "540.00", 19, "4964"),
               ("Support- und Wartungspaket, 12 Monate", "1", "Jahr", "240.00", 19, "4806")]},
    {"id": "S09", "sup": "hollerbach", "client": "M5", "nr": "MH-26-1187", "date": "2026-10-02", "tags": ["7 %"],
     "lines": [("Weizenmehl Type 550, 25-kg-Sack", "1000", "kg", "0.62", 7, "3300"),
               ("Roggenmehl Type 1150", "400", "kg", "0.71", 7, "3300"),
               ("Dinkelmehl Type 630", "200", "kg", "1.05", 7, "3300")]},
    {"id": "S10", "sup": "hollerbach", "client": "M5", "nr": "GS-26-0042", "date": "2026-10-16", "tags": ["Gutschrift", "7 %"],
     "doc_type": "credit_note", "notes": ["Gutschrift zu Rechnung MH-26-1187 vom 02.10.2026 (beschädigte Säcke)."],
     "lines": [("Rücknahme Weizenmehl Type 550, beschädigte Säcke", "75", "kg", "0.62", 7, "3300")]},
    {"id": "S11", "sup": "kranich", "client": "M4", "nr": None, "date": "2026-10-17", "tags": ["Kleinbetragsrechnung"],
     "kleinbetrag": True,
     # Kleinbetrag: Einzelpreise brutto, durch 1,19 glatt teilbar
     "lines": [("Kopierpapier A4, 500 Blatt", "2", "Pck", "11.90", 19, "4930"),
               ("Tonerkassette schwarz", "1", "Stück", "47.60", 19, "4930"),
               ("Kugelschreiber blau, 10er", "1", "Pck", "11.90", 19, "4930")]},
    {"id": "S12", "sup": "talgrund", "client": "M1", "nr": "ET-2026-500731", "date": "2026-10-03", "tags": ["19 %", "Energie"],
     "lines": [("Strom Arbeitspreis 01.07.–30.09.2026", "4820", "kWh", "0.289", 19, "4240"),
               ("Grundpreis", "3", "Monat", "14.50", 19, "4240")]},
    {"id": "S13", "sup": "glanzpunkt", "client": "M1", "nr": "RG-10-2026-14", "date": "2026-10-31", "tags": ["19 %"],
     "lines": [("Unterhaltsreinigung Gastraum Oktober 2026", "1", "Monat", "680.00", 19, "4250"),
               ("Grundreinigung Küche", "6", "Std", "38.00", 19, "4250")]},
    {"id": "S14", "sup": "paragraph", "client": "M4", "nr": "FP-104455", "date": "2026-10-08", "tags": ["7 % und 19 %"],
     "lines": [("Fachbuch Gestaltungs- und Urheberrecht, 4. Auflage", "2", "Stück", "49.00", 7, "4940"),
               ("Online-Datenbank Medienrecht, Jahresabo", "1", "Jahr", "180.00", 19, "4940")]},
    {"id": "S15", "sup": "funknetz", "client": "M2", "nr": "FM-9930-1026", "date": "2026-10-06", "tags": ["19 %"],
     "lines": [("Mobilfunk Business Tarif, Grundgebühr Oktober", "3", "Vertrag", "29.99", 19, "4920"),
               ("Zusatz-Datenvolumen 10 GB", "1", "Stück", "9.99", 19, "4920")]},
    {"id": "S16", "sup": "blitzkurier", "client": "M4", "nr": "BK-26-3310", "date": "2026-10-20", "tags": ["19 %"],
     "lines": [("Kurierfahrt Stadtgebiet", "7", "Fahrt", "12.50", 19, "4910"),
               ("Expresszuschlag", "2", "Stück", "8.00", 19, "4910")]},
    {"id": "S17", "sup": "alpenholz", "client": "M3", "nr": "AH-2026-0815", "date": "2026-10-15",
     "tags": ["innergemeinschaftlicher Erwerb"], "reverse_charge": True,
     "notes": ["Steuerfreie innergemeinschaftliche Lieferung gemäß Art. 138 MwStSystRL.",
               "USt-IdNr. des Empfängers: DE999100003"],
     "lines": [("Lärchenholz Fassadenprofil 21 x 121 mm", "240", "m", "9.80", 0, "3425")]},
    {"id": "S18", "sup": "frischgut", "client": "M1", "nr": "FG-2026-10688", "date": "2026-10-19",
     "tags": ["Scan: Bild", "7 % und 19 %"], "scan": "bild",
     "lines": [("Schlagsahne 30 %", "20", "l", "3.10", 7, "3300"),
               ("Eier Bodenhaltung Gr. M", "360", "Stück", "0.24", 7, "3300"),
               ("Spülmittel Profi, 10-l-Kanister", "4", "Kanister", "16.90", 19, "4980")]},
    {"id": "S19", "sup": "nordring", "client": "M2", "nr": "TZN-261021-02", "date": "2026-10-21",
     "tags": ["Scan: schief", "19 %"], "scan": "schief",
     "lines": [("Zündkerzen Iridium", "8", "Stück", "9.40", 19, "3400"),
               ("Luftfilter", "3", "Stück", "14.80", 19, "3400"),
               ("Scheibenwischer Satz", "2", "Paar", "22.50", 19, "3400")]},
    {"id": "S20", "sup": "ofenmeister", "client": "M5", "nr": "OM-7710", "date": "2026-10-22",
     "tags": ["Scan: verrauscht", "7 % und 19 %"], "scan": "verrauscht",
     "lines": [("Backhefe frisch", "25", "kg", "2.40", 7, "3300"),
               ("Backpapier 40 x 60 cm, Rolle", "10", "Rolle", "6.90", 19, "4980"),
               ("Tortenkarton 32 x 32 cm", "200", "Stück", "0.38", 19, "4980")]},
]

KOSIT_SELECTION = {
    "01.01": "Zwei Positionen, 7 %",
    "01.03": "Zwei Positionen, 7 %",
    "01.04": "Steuerbefreit, 0 %",
    "01.06": "Sieben Positionen, 19 %",
    "01.11": "Drei Positionen, 19 %",
    "01.13": "Elf Positionen, 19 %",
    "01.21": "Reverse Charge (Kategorie AE)",
    "02.05": "Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge",
    "03.01": "14 Positionen, 7 % und 19 %",
    "03.06": "Austauschteile, negative Menge",
}
KOSIT_SELLERS = [
    ("Lesezirkel Bergland GmbH", "Zeitungsweg 3", "96050 Bamberg"),
    ("Fachbuchversand Kellerhof GmbH", "Buchgasse 11", "97070 Würzburg"),
    ("Dolmetschbüro Weitblick GmbH", "Sprachenplatz 2", "90403 Nürnberg"),
    ("Bürotechnik Ostwind GmbH", "Druckerstraße 17", "91052 Erlangen"),
    ("Möbelwerk Ahornstein GmbH", "Tischlerweg 6", "95444 Bayreuth"),
    ("IT-Service Lichtblick GmbH", "Serverring 9", "90763 Fürth"),
    ("Montagebau Rehberg GmbH", "Hallenstraße 30", "91126 Schwabach"),
    ("Laborbedarf Quellental GmbH", "Pipettenweg 4", "96047 Bamberg"),
    ("Hausmeisterservice Eckstein GmbH", "Werkhof 8", "90402 Nürnberg"),
    ("Autoteile Kreuzberg GmbH", "Motorstraße 22", "91058 Erlangen"),
]


# --------------------------------------------------------------------------- Formatierung


def money(value: Decimal) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def num(value: Decimal) -> str:
    v = value.normalize()
    s = f"{v:,f}" if v == v.to_integral() else f"{value:,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def de_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


# --------------------------------------------------------------------------- Rendern


class Renderer:
    def __init__(self, path: Path) -> None:
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.w, self.h = A4
        self.page = 1

    def text(self, x: float, y: float, s: str, size: float = 9, bold: bool = False, right: bool = False) -> None:
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        (self.c.drawRightString if right else self.c.drawString)(x, y, s)

    def new_page(self) -> float:
        self.c.showPage()
        self.page += 1
        self.text(self.w - 40, self.h - 40, f"Seite {self.page}", 8, right=True)
        return self.h - 70

    def save(self) -> None:
        self.c.save()


def render(path: Path, r: dict[str, Any]) -> None:
    """Gemeinsame Rechnungsvorlage für synthetische Belege und KoSIT-Sichtbelege."""
    pdf = Renderer(path)
    s, b = r["seller"], r.get("buyer")
    w, h = pdf.w, pdf.h

    pdf.text(40, h - 50, s["name"], 15, bold=True)
    pdf.text(40, h - 64, f'{s["street"]} · {s["postcode_city"]}' + (f' · {s["country"]}' if s.get("country") not in (None, "DE") else ""), 8)
    y = h - 50
    for line in r.get("contact_lines", []):
        pdf.text(w - 40, y, line, 8, right=True)
        y -= 11

    if b:
        pdf.text(40, h - 120, f'{s["name"]} · {s["street"]} · {s["postcode_city"]}', 6.5)
        by = h - 136
        for line in [b["name"], b.get("attn") and f'z. Hd. {b["attn"]}', b["street"], f'{b["postcode"]} {b["city"]}']:
            if line:
                pdf.text(40, by, line, 10)
                by -= 13

    pdf.text(40, h - 225, r["title"], 16, bold=True)
    my = h - 205
    for label, value in r["meta"]:
        pdf.text(w - 190, my, f"{label}:", 9)
        pdf.text(w - 40, my, value, 9, right=True)
        my -= 13

    cols = r.get("columns", ["Pos.", "Bezeichnung", "Menge", "Einheit", "Einzelpreis", "USt", "Betrag"])
    xs = [40, 68, 330, 370, 470, 505, w - 40]
    y = h - 265

    def header(yy: float) -> float:
        for x, label, right in zip(xs, cols, [False, False, True, False, True, True, True]):
            pdf.text(x if not right else x, yy, label, 8.5, bold=True, right=right)
        pdf.c.line(40, yy - 4, w - 40, yy - 4)
        return yy - 17

    y = header(y)
    for ln in r["lines"]:
        desc = simpleSplit(ln["desc"], "Helvetica", 9, 255)
        if y - 12 * len(desc) < 150:
            y = header(pdf.new_page())
        pdf.text(xs[0], y, str(ln["pos"]))
        for i, part in enumerate(desc):
            pdf.text(xs[1], y - 11 * i, part)
        pdf.text(xs[2], y, ln["qty"], right=True)
        pdf.text(xs[3], y, ln["unit"])
        pdf.text(xs[4], y, ln["price"], right=True)
        pdf.text(xs[5], y, ln["rate"], right=True)
        pdf.text(xs[6], y, ln["amount"], right=True)
        y -= 11 * len(desc) + 5

    if y < 220:
        y = pdf.new_page()
    pdf.c.line(w - 270, y + 4, w - 40, y + 4)
    y -= 10
    for label, value, bold in r["totals"]:
        pdf.text(w - 270, y, label, 9.5 if bold else 9, bold=bold)
        pdf.text(w - 40, y, value, 9.5 if bold else 9, bold=bold, right=True)
        y -= 14

    y -= 10
    for note in r.get("notes", []):
        for part in simpleSplit(note, "Helvetica", 9, w - 80):
            pdf.text(40, y, part)
            y -= 12

    fy = 70
    for line in r.get("footer", []):
        pdf.c.setFont("Helvetica", 7)
        pdf.c.drawCentredString(w / 2, fy, line)
        fy -= 10
    pdf.save()


# --------------------------------------------------------------------------- synthetische Belege


def build_synthetic(inv: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Gibt (Render-Daten, erwartetes Ergebnis) zurück."""
    sup = SUPPLIERS[inv["sup"]]
    cli = MANDANTEN[inv["client"]]
    credit = inv.get("doc_type") == "credit_note"
    small = inv.get("kleinbetrag", False)
    sign = D(-1) if credit else D(1)

    render_lines, gold_lines = [], []
    net_by_rate: dict[int, Decimal] = {}
    gross_small = D(0)
    for pos, (desc, qty, unit, price, rate, account) in enumerate(inv["lines"], start=1):
        q, p = D(qty), D(price)
        amount = q2(q * p)
        if small:
            gross_small += amount
            net_line = q2(amount * 100 / (100 + rate))
        else:
            net_line = amount
        net_line *= sign
        net_by_rate[rate] = net_by_rate.get(rate, D(0)) + net_line
        render_lines.append({"pos": pos, "desc": desc, "qty": num(q), "unit": unit, "price": money(p),
                             "rate": f"{rate} %", "amount": money(amount * sign)})
        gold_lines.append({"description": desc, "quantity": str(q), "unit": unit,
                           "unit_price": str(q2(p * 100 / (100 + rate))) if small else str(p),
                           "net_amount": str(net_line), "tax_rate": str(rate), "account_skr03": account})

    if small:
        tax = q2(gross_small * 19 / 119)
        gross, net = gross_small, gross_small - tax
        totals = [("Summe", money(gross), True), ("darin enthalten 19 % MwSt.", money(tax), False)]
        assert sum((D(g["net_amount"]) for g in gold_lines), D(0)) == net, "Kleinbetrag nicht glatt"
    else:
        net = sum(net_by_rate.values(), D(0))
        taxes = {r: q2(n * r / 100) for r, n in sorted(net_by_rate.items())}
        tax = sum(taxes.values(), D(0))
        gross = net + tax
        totals = [("Nettobetrag", money(net), False)]
        for r, t in taxes.items():
            if r == 0:
                totals.append(("Umsatzsteuer 0 %", money(t), False))
            else:
                totals.append((f"Umsatzsteuer {r} % auf {money(net_by_rate[r])}", money(t), False))
        totals.append(("Gutschriftsbetrag" if credit else "Rechnungsbetrag", money(gross), True))

    meta = []
    if inv["nr"]:
        meta.append(("Gutschrift-Nr." if credit else "Rechnungsnummer", inv["nr"]))
    meta.append(("Datum", de_date(inv["date"])))
    if not small:
        meta.append(("Leistungsdatum", de_date(inv["date"])))
        meta.append(("Kundennummer", f"K-{inv['client']}-{inv['sup'][:3].upper()}"))

    contact = [f'Ansprechpartner: {sup["contact"]}', f'Tel. {sup["phone"]}', f'E-Mail: {sup["email"]}',
               f'USt-IdNr.: {sup["vat_id"]}', f'Steuernummer: {sup["steuernr"]}']
    footer = [f'{sup["name"]} · Geschäftsführer: {sup["gf"]} · Amtsgericht · {sup["hrb"]}',
              f'Bank: Testbank · IBAN {sup["iban"]} · BIC {sup["bic"]}']
    notes = list(inv.get("notes", []))
    if not small and not credit:
        notes.append(PAY_TERMS)
    if credit:
        notes.append("Der Betrag wird mit der nächsten Rechnung verrechnet.")

    r = {
        "seller": {**sup, "postcode_city": sup["postcode_city"]},
        "buyer": None if small else {"name": cli["name"], "attn": cli["attn"], "street": cli["street"],
                                     "postcode": cli["postcode"], "city": cli["city"]},
        "title": "Gutschrift" if credit else ("Quittung / Rechnung" if small else "Rechnung"),
        "meta": meta, "lines": render_lines, "totals": totals, "notes": notes,
        "contact_lines": contact[:3] if small else contact, "footer": footer,
        "columns": ["Pos.", "Artikel", "Menge", "Einheit", "Preis brutto", "MwSt", "Betrag"] if small else None,
    }
    if r["columns"] is None:
        del r["columns"]

    expected = {
        "document_type": "credit_note" if credit else "invoice",
        "supplier_name": sup["name"],
        "invoice_number": inv["nr"],
        "invoice_date": inv["date"],
        "currency": "EUR",
        "net_total": str(net),
        "tax_total": str(tax),
        "gross_total": str(gross),
        "reverse_charge": bool(inv.get("reverse_charge")),
        "lines": gold_lines,
    }
    return r, expected


# --------------------------------------------------------------------------- Scans


def degrade(src: Path, dst: Path, mode: str) -> None:
    """Rendert die PDF als Bild und verschlechtert es wie einen schlechten Scan."""
    rng = np.random.default_rng({"bild": 1, "schief": 2, "verrauscht": 3}[mode])
    dpi = {"bild": 150, "schief": 200, "verrauscht": 150}[mode]
    with pymupdf.open(src) as doc:
        pix = doc[0].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()

    if mode == "bild":
        img = cv2.GaussianBlur(img, (3, 3), 0)
        quality = 45
    elif mode == "schief":
        h, w = img.shape
        m = cv2.getRotationMatrix2D((w / 2, h / 2), 2.5, 1.0)
        img = cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderValue=235)
        img = cv2.GaussianBlur(img, (3, 3), 0)
        quality = 60
    else:
        img = cv2.GaussianBlur(img, (3, 3), 0.8)
        noise = rng.normal(0, 28, img.shape)
        speckle = rng.random(img.shape) < 0.004
        out = img.astype(np.float32) * 0.82 + 30 + noise
        out[speckle] = 20
        img = np.clip(out, 0, 255).astype(np.uint8)
        quality = 35

    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok
    out_doc = pymupdf.open()
    page = out_doc.new_page(width=A4[0], height=A4[1])
    page.insert_image(page.rect, stream=jpg.tobytes())
    out_doc.save(dst, deflate=True)
    out_doc.close()


# --------------------------------------------------------------------------- KoSIT


def build_kosit(case: str, idx: int) -> tuple[dict[str, Any], dict[str, Any], str]:
    xml = ROOT / "kosit" / f"{case}a-INVOICE_ubl.xml"
    data = parse_file(xml)
    parties = data.pop("parties")
    seller_name, street, pc = KOSIT_SELLERS[idx]
    cli = MANDANTEN["M6"]
    currency = data["currency"]

    def m(v: str | None) -> str:
        return "" if v is None else money(D(v)).replace("€", currency if currency != "EUR" else "€")

    lines = []
    for pos, ln in enumerate(data["lines"], start=1):
        lines.append({"pos": pos, "desc": ln["description"] or "", "qty": num(D(ln["quantity"] or "0")),
                      "unit": ln["unit"] or "", "price": m(ln["unit_price"]), "rate": f'{ln["tax_rate"]} %',
                      "amount": m(ln["net_amount"])})
    net_by_rate: dict[str, Decimal] = {}
    for ln in data["lines"]:
        net_by_rate[ln["tax_rate"]] = net_by_rate.get(ln["tax_rate"], D(0)) + D(ln["net_amount"] or "0")
    totals = [("Summe Positionen", m(str(sum(net_by_rate.values(), D(0)))), False)]
    if D(data["net_total"]) != sum(net_by_rate.values(), D(0)):
        totals.append(("Zu- und Abschläge", m(str(D(data["net_total"]) - sum(net_by_rate.values(), D(0)))), False))
    totals.append(("Nettobetrag", m(data["net_total"]), False))
    totals.append(("Umsatzsteuer gesamt", m(data["tax_total"]), False))
    totals.append(("Rechnungsbetrag", m(data["gross_total"]), True))

    notes = []
    if data["reverse_charge"]:
        notes.append("Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge).")
    if "E" in parties["tax_categories"]:
        notes.append("Teilweise steuerbefreite Leistungen.")

    r = {
        "seller": {"name": seller_name, "street": street, "postcode_city": pc, "country": "DE"},
        "buyer": {"name": cli["name"], "attn": cli["attn"], "street": cli["street"], "postcode": cli["postcode"], "city": cli["city"]},
        "title": "Rechnung",
        "meta": [("Rechnungsnummer", data["invoice_number"]), ("Rechnungsdatum", de_date(data["invoice_date"]))],
        "lines": lines, "totals": totals, "notes": notes,
        "contact_lines": [f"USt-IdNr.: DE999300{idx:03d}", f"Tel. +49 951 {7000 + idx} 55"],
        "footer": [f"{seller_name} · IBAN {_iban(100 + idx)}"],
    }
    expected = {**data, "supplier_name": seller_name}
    return r, expected, parties["seller"]["name"] or ""


# --------------------------------------------------------------------------- Hauptprogramm


def main() -> None:
    syn_dir, gold_dir, sicht_dir = ROOT / "synthetisch", ROOT / "goldstandard", ROOT / "kosit_sicht"
    for d in (syn_dir, gold_dir, sicht_dir):
        d.mkdir(parents=True, exist_ok=True)

    (ROOT / "mandanten.json").write_text(
        json.dumps({"_meta": {"hinweis": "Erfundene Mandanten für Testbelege. Keine echten Daten."},
                    "mandanten": MANDANTEN}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for inv in INVOICES:
        r, expected = build_synthetic(inv)
        slug = SUPPLIERS[inv["sup"]]["name"].split()[0].lower()
        slug = slug.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss").strip("-&")
        name = f'{inv["id"]}_{slug}.pdf'
        target = syn_dir / name
        if inv.get("scan"):
            vector = syn_dir / f"_{name}"
            render(vector, r)
            degrade(vector, target, inv["scan"])
            vector.unlink()
            art = "scan"
        else:
            render(target, r)
            art = "pdf"
        sup, cli = SUPPLIERS[inv["sup"]], MANDANTEN[inv["client"]]
        sensitive = [cli["name"], cli["person"], cli["street"], cli["vat_id"], sup["iban"], sup["email"],
                     sup["phone"], sup["steuernr"], sup["contact"], sup["gf"]]
        gold = {"id": inv["id"], "quelle": "synthetisch", "client_id": inv["client"], "merkmale": inv["tags"],
                "dokumente": [{"pfad": f"synthetisch/{name}", "art": art}], "erwartet": expected,
                # Werte, die nie beim KI-Anbieter ankommen dürfen (Prüfung der Pseudonymisierung)
                "sensible_werte": [v for v in sensitive if v not in ("Service-Team", "Kundenservice")]}
        (gold_dir / f'{inv["id"]}.json').write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")

    for idx, (case, desc) in enumerate(KOSIT_SELECTION.items()):
        r, expected, xml_seller = build_kosit(case, idx)
        pdf_name = f"{case}a-sicht.pdf"
        render(sicht_dir / pdf_name, r)
        gold = {
            "id": f"K{case}", "quelle": "kosit", "client_id": "M6", "merkmale": [desc],
            "dokumente": [
                {"pfad": f"kosit/{case}a-INVOICE_ubl.xml", "art": "xml",
                 "abweichend": {"supplier_name": xml_seller}},
                {"pfad": f"kosit/{case}a-INVOICE_uncefact.xml", "art": "xml",
                 "abweichend": {"supplier_name": xml_seller}},
                {"pfad": f"kosit_sicht/{pdf_name}", "art": "pdf"},
            ],
            "erwartet": expected,
            "sensible_werte": [MANDANTEN["M6"]["name"], MANDANTEN["M6"]["person"], MANDANTEN["M6"]["street"],
                               _iban(100 + idx), f"+49 951 {7000 + idx} 55"],
        }
        (gold_dir / f"K{case}.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(INVOICES)} synthetische Belege, {len(KOSIT_SELECTION)} KoSIT-Belege erzeugt.")


if __name__ == "__main__":
    main()
