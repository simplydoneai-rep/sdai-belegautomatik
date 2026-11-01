"""Rechnungen für den Folgemonat (November 2026): dieselben Lieferanten wie im Oktober, neue Nummern und Mengen.

Zeigt in der Demo das Lernen: Was im Oktober gebucht wurde, ist im November schon vorkontiert.
Einige Fälle gehen bewusst zur Prüfung: neuer Lieferant, neue Positionsart, ungewöhnlich hoher Betrag,
Gutschrift, Reverse Charge. Alle Belege nutzen die Grundvorlage; in der Demo werden sie ohne KI
(regelbasiert) gelesen, weil es für sie keine aufgezeichneten KI-Antworten gibt.

Ergebnis: ``testdaten/folgemonat/F*.pdf`` und ``testdaten/folgemonat/gold/F*.json``.
Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/folgemonat.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import erzeuge_testbelege as basis  # noqa: E402

ORDNER = basis.ROOT / "folgemonat"

basis.SUPPLIERS["bohnenglueck"] = basis._supplier(40, "Kaffeerösterei Bohnenglück GmbH", "Röstweg 3", "90443 Nürnberg",
                                                  "Mila Vogt", "Mila Vogt")
# Drittland (USA, Rechnung in US-Dollar) und EU-Lieferant (Niederlande, innergemeinschaftliche Lieferung)
basis.SUPPLIERS["pixelcloud"] = {**basis._supplier(41, "PixelCloud Software Inc.", "500 Market Street", "San Francisco, CA 94105",
                                                   "Billing Team", "Dana Whitfield", country="USA", vat="99-9990041"),
                                 "id_label": "Tax ID (EIN)", "steuernr": None, "email": "billing@pixelcloud-example.com"}
basis.SUPPLIERS["gereedschap"] = {**basis._supplier(42, "Gereedschap Groothandel B.V.", "Havenweg 12", "3011 Rotterdam",
                                                    "Sanne de Vries", "Pieter Bakker", country="NL", vat="NL999999042B01"),
                                  "steuernr": None}

# Gleiche Schreibweise der Positionen wie im Oktober, damit die Lernregeln greifen.
RECHNUNGEN: list[dict[str, Any]] = [
    {"id": "F01", "sup": "frischgut", "client": "M1", "nr": "FG-2026-11203", "date": "2026-11-04", "tags": ["wiederkehrend", "7 %"],
     "lines": [("Kaffeebohnen Espresso Röstung", "12", "kg", "18.90", 7, "3300"),
               ("Vollmilch 3,5 %", "50", "l", "1.09", 7, "3300"),
               ("Weizenmehl Type 405", "20", "kg", "0.85", 7, "3300"),
               ("Süßrahmbutter", "8", "kg", "7.40", 7, "3300")]},
    {"id": "F02", "sup": "hanse", "client": "M1", "nr": "GH-88977", "date": "2026-11-06", "tags": ["wiederkehrend", "7 % und 19 %"],
     "lines": [("Mineralwasser medium 12 x 0,75 l", "10", "Kiste", "8.40", 19, "3400"),
               ("Apfelsaft naturtrüb 6 x 1,0 l", "8", "Kiste", "14.20", 19, "3400"),
               ("Vollmilch 3,8 % Barista", "40", "l", "1.19", 7, "3300")]},
    {"id": "F03", "sup": "nordring", "client": "M2", "nr": "TZN-261105-03", "date": "2026-11-05", "tags": ["wiederkehrend", "19 %"],
     "lines": [("Bremsscheibe vorne belüftet", "4", "Stück", "64.50", 19, "3400"),
               ("Motoröl 5W-30 Longlife", "25", "l", "6.80", 19, "3400"),
               ("Ölfilter", "6", "Stück", "7.25", 19, "3400")]},
    {"id": "F04", "sup": "lackwerk", "client": "M2", "nr": "LS/2026/3512", "date": "2026-11-10", "tags": ["neue Positionsart", "19 %"],
     "lines": [("Basislack Farbton nach Muster", "3", "l", "58.00", 19, "3400"),
               ("Klarlack 2K HS", "4", "l", "39.50", 19, "3400"),
               ("Akku-Poliermaschine 18 V", "1", "Stück", "289.00", 19, "4985")]},
    {"id": "F05", "sup": "waldmark", "client": "M3", "nr": "WM-55488", "date": "2026-11-12", "tags": ["wiederkehrend", "19 %"],
     "lines": [("Konstruktionsvollholz Fichte 80 x 160 mm", "6", "m³", "465.00", 19, "3400"),
               ("Dachlatten 30 x 50 mm imprägniert", "200", "m", "1.35", 19, "3400")]},
    {"id": "F06", "sup": "feinschnitt", "client": "M4", "nr": "DF-2026-1044", "date": "2026-11-13", "tags": ["wiederkehrend", "19 %"],
     "lines": [("Flyer DIN A5, 4/4-farbig, 135 g", "2500", "Stück", "0.042", 19, "4600"),
               ("Visitenkarten 85 x 55 mm", "250", "Stück", "0.09", 19, "4600")]},
    {"id": "F07", "sup": "cloudkontor", "client": "M4", "nr": "CK-INV-78110", "date": "2026-11-01", "tags": ["wiederkehrend", "19 %"],
     "leistung": ("Leistungszeitraum", "01.11.26–31.10.27"),
     "lines": [("Support- und Wartungspaket, 12 Monate", "1", "Jahr", "240.00", 19, "4806")]},
    {"id": "F08", "sup": "hollerbach", "client": "M5", "nr": "MH-26-1302", "date": "2026-11-03", "tags": ["wiederkehrend", "7 %"],
     "lines": [("Weizenmehl Type 550, 25-kg-Sack", "1200", "kg", "0.62", 7, "3300"),
               ("Roggenmehl Type 1150", "300", "kg", "0.71", 7, "3300")]},
    {"id": "F09", "sup": "talgrund", "client": "M1", "nr": "ET-2026-501288", "date": "2026-11-03", "tags": ["Dauerbeleg", "Energie"],
     "leistung": ("Leistungszeitraum", "01.10.–31.10.2026"),
     "lines": [("Strom Arbeitspreis 01.10.–31.10.2026", "1650", "kWh", "0.289", 19, "4240"),
               ("Grundpreis", "1", "Monat", "14.50", 19, "4240")]},
    {"id": "F10", "sup": "glanzpunkt", "client": "M1", "nr": "RG-11-2026-15", "date": "2026-11-30", "tags": ["Dauerbeleg", "19 %"],
     "leistung": ("Leistungszeitraum", "01.11.–30.11.2026"),
     "lines": [("Unterhaltsreinigung Gastraum November 2026", "1", "Monat", "680.00", 19, "4250")]},
    {"id": "F11", "sup": "paragraph", "client": "M4", "nr": "FP-104902", "date": "2026-11-09", "tags": ["wiederkehrend", "7 %"],
     "lines": [("Fachbuch Gestaltungs- und Urheberrecht, 4. Auflage", "1", "Stück", "49.00", 7, "4940")]},
    {"id": "F12", "sup": "funknetz", "client": "M2", "nr": "FM-9930-1126", "date": "2026-11-06", "tags": ["Dauerbeleg", "19 %"],
     "lines": [("Mobilfunk Business Tarif, Grundgebühr November", "3", "Vertrag", "29.99", 19, "4920")]},
    {"id": "F13", "sup": "blitzkurier", "client": "M4", "nr": "BK-26-3561", "date": "2026-11-18", "tags": ["wiederkehrend", "19 %"],
     "lines": [("Kurierfahrt Stadtgebiet", "5", "Fahrt", "12.50", 19, "4910")]},
    {"id": "F14", "sup": "hollerbach", "client": "M5", "nr": "GS-26-0057", "date": "2026-11-14", "tags": ["Gutschrift"],
     "doc_type": "credit_note", "notes": ["Gutschrift zu Rechnung MH-26-1302 vom 03.11.2026 (Fehlmenge)."],
     "lines": [("Rücknahme Roggenmehl Type 1150, Fehlmenge", "50", "kg", "0.71", 7, "3300")]},
    {"id": "F15", "sup": "kessler", "client": "M3", "nr": "K-2026-131", "date": "2026-11-16", "tags": ["Reverse Charge § 13b"],
     "reverse_charge": True,
     "notes": ["Steuerschuldnerschaft des Leistungsempfängers gemäß § 13b Abs. 2 Nr. 4 UStG.",
               "Die Umsatzsteuer schuldet der Leistungsempfänger."],
     "lines": [("Gerüststellung Bauvorhaben Ahornweg, Standzeit 4 Wochen", "1", "pauschal", "2450.00", 0, "3120")]},
    {"id": "F16", "sup": "bohnenglueck", "client": "M1", "nr": "BG-2026-0071", "date": "2026-11-11", "tags": ["neuer Lieferant", "7 %"],
     "lines": [("Kaffeebohnen Hausmischung", "15", "kg", "21.40", 7, "3300")]},
    {"id": "F17", "sup": "frischgut", "client": "M1", "nr": "FG-2026-11455", "date": "2026-11-20", "tags": ["Betrag ungewöhnlich hoch"],
     "lines": [("Kaffeebohnen Espresso Röstung", "10", "kg", "18.90", 7, "3300"),
               ("Vollmilch 3,5 %", "60", "l", "1.09", 7, "3300"),
               ("Weizenmehl Type 405", "400", "kg", "0.85", 7, "3300"),
               ("Süßrahmbutter", "120", "kg", "7.40", 7, "3300")]},
    {"id": "F18", "sup": "pixelcloud", "client": "M4", "nr": "PC-2026-118842", "date": "2026-11-02",
     "tags": ["Drittland", "US-Dollar", "Reverse Charge § 13b"], "currency": "USD", "reverse_charge": True,
     "leistung": ("Leistungszeitraum", "01.11.–30.11.2026"),
     "notes": ["Reverse Charge: Steuerschuldnerschaft des Leistungsempfängers (§ 13b UStG).",
               "Amounts in US-Dollar (USD)."],
     "lines": [("Design-Software Lizenz Team, Monatsabo", "4", "Nutzer", "54.00", 0, "4964")]},
    {"id": "F19", "sup": "gereedschap", "client": "M2", "nr": "GG-26-04417", "date": "2026-11-17",
     "tags": ["EU-Lieferant", "innergemeinschaftlicher Erwerb"], "reverse_charge": True,
     "leistung": ("Lieferdatum", "13.11.2026"),
     "notes": ["Steuerfreie innergemeinschaftliche Lieferung gemäß Art. 138 MwStSystRL.",
               "USt-IdNr. des Leistungsempfängers: DE999100002"],
     "lines": [("Drehmomentschlüssel 1/2 Zoll, 40–200 Nm", "2", "Stück", "129.00", 0, "4985"),
               ("Steckschlüsselsatz 94-teilig", "1", "Satz", "189.00", 0, "4985")]},
]


def main() -> None:
    gold_dir = ORDNER / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    for inv in RECHNUNGEN:
        r, expected = basis.build_synthetic(inv)
        slug = basis.SUPPLIERS[inv["sup"]]["name"].split()[0].lower()
        slug = slug.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss").strip("-&")
        name = f'{inv["id"]}_{slug}.pdf'
        basis.render(ORDNER / name, r)
        gold = {"id": inv["id"], "quelle": "folgemonat", "client_id": inv["client"], "merkmale": inv["tags"],
                "dokumente": [{"pfad": f"folgemonat/{name}", "art": "pdf"}], "erwartet": expected}
        (gold_dir / f'{inv["id"]}.json').write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(RECHNUNGEN)} Rechnungen für November erzeugt → {ORDNER}")


if __name__ == "__main__":
    main()
