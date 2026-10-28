"""Zusatzbelege S21–S32 mit anderen Layouts als die Grundvorlage (Entscheidung 2026-10-28_zusatzbelege).

Layouts:
  modern   – ohne Tabellenlinien, Serifenschrift, Datum ausgeschrieben, Beträge mit "EUR"
  englisch – wie modern, englische Begriffe und Zahlenformat (1,234.56)
  bon      – Kassenbon, 80 mm breit, Schreibmaschinenschrift, Bruttopreise
  brief    – Fließtext ohne Tabelle (Mietrechnung)
  klassisch – Grundvorlage aus erzeuge_testbelege.py, mit Rabatt, Abschlag oder vielen Positionen
Verschlechterungen: Handyfoto (Perspektive, Licht, JPG), auf dem Kopf gescannte Seite.

Alle Firmen, Personen und Kennungen sind erfunden (siehe erzeuge_testbelege.py).
Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/zusatzbelege.py``
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from erzeuge_testbelege import MANDANTEN, ROOT, _supplier, de_date, money, num, render  # noqa: E402

from app.kontierung.betraege import q2  # noqa: E402

D = Decimal
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]

SUP = {
    "lichtwerk": _supplier(21, "Lichtwerk Fotostudio GmbH", "Atelierweg 4", "90419 Nürnberg", "Clara Weiß", "Clara Weiß"),
    "funkenflug": _supplier(22, "Elektro Funkenflug GmbH", "Schaltweg 12", "90441 Nürnberg", "Stefan Brandl", "Stefan Brandl"),
    "tankhof": _supplier(23, "Tankhof Regnitzgrund GmbH", "Bundesstraße 4", "91056 Erlangen", "Filialleitung", "Ralf Kuhn"),
    "northwind": {**_supplier(24, "Northwind Analytics B.V.", "Keizersgracht 1000", "1015 AA Amsterdam", "Sanne de Vries",
                              "Pieter van Dam", country="NL", vat="NL999999999B01"),
                  "phone": "+31 20 999 0024", "email": "billing@northwind-beispiel.nl"},
    "gastroring": _supplier(25, "Gastro-Ring Großmarkt GmbH", "Marktallee 1", "90451 Nürnberg", "Tanja Lehner", "Holger Fink"),
    "werkzeugprofi": _supplier(26, "Werkzeugprofi Kranz GmbH", "Schraubenstraße 9", "91074 Herzogenaurach", "Jan Kranz", "Jan Kranz"),
    "backstube24": _supplier(27, "Backstube24 Versand GmbH", "Lagerstraße 77", "97076 Würzburg", "Kundenservice", "Mira Sander"),
    "rosenhof": _supplier(28, "Hausverwaltung Rosenhof GmbH", "Rosengasse 5", "90762 Fürth", "Doris Engel", "Doris Engel"),
    "zumkrug": _supplier(29, "Gasthaus Zum Krug GmbH", "Am Anger 3", "91054 Erlangen", "Service", "Tom Wirth"),
    "baumarkt": _supplier(30, "Baumarkt Holzweg GmbH", "Gewerbepark 20", "95448 Bayreuth", "Kasse 3", "Ulf Hager"),
    "pixelnord": _supplier(31, "Satz & Druck Pixelnord GmbH", "Druckhaus 2", "90763 Fürth", "Leon Faber", "Greta Faber"),
    "systemhaus": _supplier(32, "IT-Systemhaus Bitbrücke GmbH", "Netzweg 8", "91126 Schwabach", "Emre Kaya", "Nora Busch"),
}

# Positionen: (Bezeichnung, Menge, Einheit, Einzelpreis, Steuersatz, Sachkonto[, Rabatt %])
# Bei "brutto": Einzelpreis inkl. USt; Beträge so gewählt, dass sie sich glatt auf netto umrechnen.
GASTRO_LINES = [
    ("Rapsöl 10 l Kanister", "2", "Kanister", "21.90", 7, "3300"), ("Weizenmehl Type 405, 10 kg", "3", "Sack", "6.40", 7, "3300"),
    ("Zucker fein, 10 kg", "1", "Sack", "11.20", 7, "3300"), ("Vollmilch 3,5 %, 12 x 1 l", "4", "Karton", "13.08", 7, "3300"),
    ("Sahne 30 %, 10 x 1 l", "2", "Karton", "29.50", 7, "3300"), ("Butter, 10 x 250 g", "3", "Karton", "18.90", 7, "3300"),
    ("Eier Freiland Gr. L, 180 Stück", "1", "Lage", "52.20", 7, "3300"), ("Kaffeebohnen Crema, 6 kg", "1", "Karton", "98.40", 7, "3300"),
    ("Tee Auswahl, 6 x 100 Beutel", "1", "Karton", "32.40", 7, "3300"), ("Kakao Pulver, 1 kg", "2", "Dose", "9.80", 7, "3300"),
    ("Orangensaft 6 x 1 l", "5", "Kiste", "10.80", 19, "3400"), ("Mineralwasser still 12 x 0,75 l", "6", "Kiste", "7.90", 19, "3400"),
    ("Cola 24 x 0,33 l", "3", "Kiste", "16.80", 19, "3400"), ("Apfelschorle 24 x 0,33 l", "3", "Kiste", "13.20", 19, "3400"),
    ("Croissants TK, 60 Stück", "2", "Karton", "24.60", 7, "3300"), ("Brezeln TK, 80 Stück", "2", "Karton", "19.20", 7, "3300"),
    ("Tomaten, 6 kg", "2", "Kiste", "14.40", 7, "3300"), ("Gurken, 12 Stück", "2", "Kiste", "8.40", 7, "3300"),
    ("Käse Gouda in Scheiben, 1 kg", "4", "Packung", "11.60", 7, "3300"), ("Schinken gekocht, 1 kg", "3", "Packung", "13.90", 7, "3300"),
    ("Servietten 3-lagig, 1000 Stück", "2", "Karton", "17.50", 19, "4980"), ("Coffee-to-go-Becher 0,3 l, 1000 Stück", "1", "Karton", "64.00", 19, "4980"),
    ("Deckel für Becher, 1000 Stück", "1", "Karton", "29.00", 19, "4980"), ("Spülmaschinentabs, 200 Stück", "1", "Eimer", "38.90", 19, "4980"),
    ("Handseife 5 l", "2", "Kanister", "12.50", 19, "4980"), ("Müllbeutel 120 l, 250 Stück", "1", "Karton", "22.80", 19, "4980"),
    ("Frischhaltefolie 300 m", "2", "Rolle", "9.60", 19, "4980"), ("Alufolie 150 m", "2", "Rolle", "11.40", 19, "4980"),
]

INVOICES: list[dict[str, Any]] = [
    {"id": "S21", "sup": "lichtwerk", "client": "M4", "layout": "modern", "nr": "LW-26-0147", "date": "2026-10-23",
     "tags": ["Layout modern", "19 %"],
     "lines": [("Fotoproduktion Imagekampagne, Studiotag", "1", "Tag", "950.00", 19, "4610"),
               ("Bildbearbeitung und Retusche", "6", "Std", "65.00", 19, "4610")]},
    {"id": "S22", "sup": "funkenflug", "client": "M1", "layout": "klassisch", "nr": "EF-2026-0388", "date": "2026-10-24",
     "tags": ["Schlussrechnung mit Abschlag", "19 %"],
     "notes": ["Schlussrechnung zum Auftrag vom 01.10.2026 (Elektroinstallation Gastraum).",
               "Abzüglich Abschlagszahlung vom 05.10.2026: 595,00 € (darin 95,00 € USt)."],
     "abschlag": "595.00",
     "lines": [("Elektroarbeiten Gastraum, Gesellenstunden", "14", "Std", "68.00", 19, "4260"),
               ("Installationsmaterial lt. Aufmaß", "1", "pauschal", "386.50", 19, "4260")]},
    {"id": "S23", "sup": "tankhof", "client": "M2", "layout": "bon", "nr": None, "date": "2026-10-25",
     "tags": ["Kassenbon", "Kleinbetragsrechnung"], "brutto": True,
     "lines": [("Super E10 39,91 l x 1,789", "1", "", "71.40", 19, "4530"),
               ("Scheibenreiniger 1 l", "1", "", "5.95", 19, "4530")]},
    {"id": "S24", "sup": "northwind", "client": "M4", "layout": "englisch", "nr": "INV-2026-11-0042", "date": "2026-11-02",
     "tags": ["Englisch", "Reverse Charge EU-Leistung"], "reverse_charge": True,
     "notes": ["VAT reverse charge: the recipient is liable for VAT (Article 196 Council Directive 2006/112/EC)."],
     "lines": [("Analytics platform subscription, November 2026", "1", "month", "420.00", 0, "4964"),
               ("Additional user seats", "5", "seat", "18.00", 0, "4964")]},
    {"id": "S25", "sup": "gastroring", "client": "M1", "layout": "modern", "nr": "GR-778120", "date": "2026-10-26",
     "tags": ["Mehrseitig", "28 Positionen", "7 % und 19 %"], "lines": GASTRO_LINES},
    {"id": "S26", "sup": "werkzeugprofi", "client": "M2", "layout": "klassisch", "nr": "WK-26-5521", "date": "2026-10-27",
     "tags": ["Positionsrabatt", "Versandkosten", "19 %"],
     "lines": [("Drehmomentschlüssel 40–200 Nm", "1", "Stück", "189.00", 19, "4985", 10),
               ("Steckschlüsselsatz 1/2 Zoll, 32-teilig", "1", "Satz", "249.00", 19, "4985", 10),
               ("Versandkosten", "1", "pauschal", "6.90", 19, "4985")]},
    {"id": "S27", "sup": "backstube24", "client": "M5", "layout": "modern", "nr": "B24-1029-3381", "date": "2026-10-29",
     "tags": ["Bruttopreise über 250 €", "19 %"], "brutto": True,
     "lines": [("Gärkörbe Peddigrohr rund, 1 kg", "20", "Stück", "11.90", 19, "4985"),
               ("Lochbleche 60 x 40 cm", "6", "Stück", "29.75", 19, "4985")]},
    {"id": "S28", "sup": "rosenhof", "client": "M4", "layout": "brief", "nr": "MI-2026-11-04", "date": "2026-10-28",
     "tags": ["Brief ohne Tabelle", "Miete", "19 %"],
     "lines": [("Gewerbemiete Büroeinheit 2. OG, November 2026", "1", "Monat", "1450.00", 19, "4210"),
               ("Tiefgaragenstellplatz Nr. 14, November 2026", "1", "Monat", "60.00", 19, "4210")]},
    {"id": "S29", "sup": "zumkrug", "client": "M2", "layout": "bon", "nr": None, "date": "2026-10-28",
     "tags": ["Bewirtungsbeleg", "Kleinbetragsrechnung"], "brutto": True,
     "lines": [("Rinderroulade mit Klößen", "2", "", "23.80", 19, "4650"),
               ("Apfelschorle 0,4 l", "2", "", "4.76", 19, "4650"),
               ("Espresso", "2", "", "2.38", 19, "4650")]},
    {"id": "S30", "sup": "baumarkt", "client": "M3", "layout": "bon", "nr": None, "date": "2026-10-29",
     "tags": ["Handyfoto", "Kassenbon", "Kleinbetragsrechnung"], "brutto": True, "foto": True,
     "lines": [("Schleifscheiben K120, 10 St.", "3", "", "5.95", 19, "4980"),
               ("Arbeitshandschuhe Gr. 10", "2", "", "11.90", 19, "4980"),
               ("Silikon transparent 310 ml", "3", "", "8.33", 19, "4980")]},
    {"id": "S31", "sup": "pixelnord", "client": "M4", "layout": "modern", "nr": "PN-4412", "date": "2026-10-30",
     "tags": ["Scan auf dem Kopf", "7 % und 19 %"], "kopf": True,
     "lines": [("Broschüre Firmenchronik, 48 Seiten, Auflage 200", "200", "Stück", "4.10", 7, "4610"),
               ("Gestaltung und Satz", "8", "Std", "72.00", 19, "4610")]},
    {"id": "S32", "sup": "systemhaus", "client": "M5", "layout": "klassisch", "nr": "8812", "date": "2026-10-31",
     "tags": ["Viele Nummern auf dem Beleg", "GWG", "19 %"],
     "meta_extra": [("Kunden-Nr.", "2026-1102"), ("Auftrags-Nr.", "A-77812"), ("Lieferschein", "LS-30551")],
     "lines": [("Notebook 14 Zoll, 16 GB RAM, 512 GB SSD", "1", "Stück", "749.00", 19, "0480"),
               ("Wartungsvertrag Kassensystem, 4. Quartal 2026", "1", "Quartal", "180.00", 19, "4806")]},
]


# --------------------------------------------------------------------------- Beträge und Goldstandard


def compute(inv: dict[str, Any]) -> dict[str, Any]:
    brutto = inv.get("brutto", False)
    rows, gold_lines = [], []
    net_by_rate: dict[int, Decimal] = {}
    gross_by_rate: dict[int, Decimal] = {}
    for line in inv["lines"]:
        desc, qty, unit, price, rate, account = line[:6]
        discount = D(line[6]) if len(line) > 6 else D(0)
        q, p = D(qty), D(price)
        base = q2(q * p)
        amount = q2(base * (100 - discount) / 100)
        if brutto:
            gross_by_rate[rate] = gross_by_rate.get(rate, D(0)) + amount
            net = q2(amount * 100 / (100 + rate))
            unit_net = q2(p * 100 / (100 + rate))
        else:
            net, unit_net = amount, p
        net_by_rate[rate] = net_by_rate.get(rate, D(0)) + net
        rows.append({"desc": desc, "q": q, "unit": unit, "price": p, "rate": rate, "discount": discount,
                     "base": base, "amount": amount})
        gold_lines.append({"description": desc, "quantity": str(q), "unit": unit or None, "unit_price": str(unit_net),
                           "net_amount": str(net), "tax_rate": str(rate), "account_skr03": account})
    if brutto:
        taxes = {r: q2(g * r / (100 + r)) for r, g in gross_by_rate.items()}
        gross = sum(gross_by_rate.values(), D(0))
        net_total = gross - sum(taxes.values(), D(0))
        assert net_total == sum(net_by_rate.values(), D(0)), f'{inv["id"]}: Brutto nicht glatt'
    else:
        taxes = {r: q2(n * r / 100) for r, n in net_by_rate.items()}
        net_total = sum(net_by_rate.values(), D(0))
        gross = net_total + sum(taxes.values(), D(0))
    return {"rows": rows, "gold_lines": gold_lines, "net_by_rate": dict(sorted(net_by_rate.items())),
            "taxes": dict(sorted(taxes.items())), "net": net_total, "tax": sum(taxes.values(), D(0)), "gross": gross}


def long_date(iso: str, en: bool = False) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{MONTHS[m - 1]} {d}, {y}" if en else f"{d}. {MONATE[m - 1]} {y}"


def b2(v: Decimal) -> str:
    """Betrag ohne Währung mit zwei Nachkommastellen (Kassenbon)."""
    return money(v).replace(" €", "")


def eur(v: Decimal, en: bool = False) -> str:
    if en:
        return f"€{v:,.2f}" if v >= 0 else f"-€{-v:,.2f}"
    return money(v).replace(" €", " EUR")


# --------------------------------------------------------------------------- Layout modern / englisch


def render_modern(path: Path, inv: dict[str, Any], c: dict[str, Any], en: bool = False) -> None:
    s, cli = SUP[inv["sup"]], MANDANTEN[inv["client"]]
    pdf = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    L = {"inv": "INVOICE" if en else "RECHNUNG", "nr": "Invoice no." if en else "Rg.-Nr.",
         "date": "Invoice date" if en else "Datum der Rechnung", "service": "Service period" if en else "Leistungszeitraum",
         "desc": "Description" if en else "Leistung", "qty": "Qty" if en else "Anz.", "price": "Unit price" if en else "Preis",
         "vat": "VAT" if en else "USt", "total": "Amount" if en else "Gesamt", "sub": "Subtotal (net)" if en else "Zwischensumme netto",
         "due": "Total due" if en else "Endbetrag", "carry": "Carried forward" if en else "Übertrag",
         "page": "Page" if en else "Seite"}

    def head(page: int) -> float:
        pdf.setFont("Times-Bold", 20)
        pdf.drawString(50, h - 60, s["name"])
        pdf.setFont("Times-Roman", 9)
        pdf.drawString(50, h - 74, f'{s["street"]}, {s["postcode_city"]}' + (", Netherlands" if s["country"] == "NL" else ""))
        pdf.drawRightString(w - 50, h - 60, f'{L["page"]} {page}')
        return h - 110

    y = head(1)
    pdf.setFont("Times-Roman", 10)
    for line in [cli["name"], (f'Attn: {cli["person"]}' if en else f'Ansprechpartner: {cli["person"]}'), cli["street"],
                 f'{cli["postcode"]} {cli["city"]}' + (", Germany" if en else ""),
                 (f'VAT ID: {cli["vat_id"]}' if en else "")]:
        if line:
            pdf.drawString(50, y, line)
            y -= 13
    pdf.setFont("Times-Bold", 26)
    pdf.drawString(50, y - 30, L["inv"])
    pdf.setFont("Times-Roman", 10)
    meta = [(L["nr"], inv["nr"]), (L["date"], long_date(inv["date"], en)), (L["service"], long_date(inv["date"], en))]
    my = h - 110
    for k, v in meta:
        pdf.drawString(w - 230, my, k)
        pdf.drawRightString(w - 50, my, v)
        my -= 14
    for k, v in [("Phone" if en else "Telefon", s["phone"]), ("E-mail" if en else "E-Mail", s["email"]),
                 ("VAT ID" if en else "USt-IdNr.", s["vat_id"])]:
        pdf.drawString(w - 230, my, k)
        pdf.drawRightString(w - 50, my, v)
        my -= 14

    xs = (50, 320, 360, 450, 490, w - 50)
    y -= 70

    def header(yy: float) -> float:
        pdf.setFont("Times-Bold", 10)
        for x, lab, right in zip(xs, (L["desc"], L["qty"], "", L["price"], L["vat"], L["total"]),
                                 (False, True, False, True, True, True)):
            (pdf.drawRightString if right else pdf.drawString)(x, yy, lab)
        return yy - 18

    y = header(y)
    running = D(0)
    page = 1
    for row in c["rows"]:
        if y < 120:
            pdf.setFont("Times-Italic", 10)
            pdf.drawString(50, y - 5, L["carry"])
            pdf.drawRightString(w - 50, y - 5, eur(running, en))
            pdf.showPage()
            page += 1
            y = head(page)
            pdf.setFont("Times-Italic", 10)
            pdf.drawString(50, y, L["carry"])
            pdf.drawRightString(w - 50, y, eur(running, en))
            y = header(y - 24)
        pdf.setFont("Times-Roman", 10)
        parts = simpleSplit(row["desc"], "Times-Roman", 10, 260)
        for i, part in enumerate(parts):
            pdf.drawString(xs[0], y - 12 * i, part)
        qty = f'{row["q"].normalize():f}' if en else num(row["q"])
        pdf.drawRightString(xs[1], y, qty)
        pdf.drawString(xs[2] + 4, y, row["unit"])
        pdf.drawRightString(xs[3], y, eur(row["price"], en))
        pdf.drawRightString(xs[4], y, f'{row["rate"]}%')
        pdf.drawRightString(xs[5], y, eur(row["amount"], en))
        running += row["amount"]
        y -= 12 * len(parts) + 6

    if y < 200:
        pdf.showPage()
        page += 1
        y = head(page)
    y -= 14
    brutto = inv.get("brutto", False)
    totals: list[tuple[str, str, bool]] = []
    if brutto:
        totals.append(("Gesamtbetrag (inkl. USt)", eur(c["gross"]), True))
        totals.append(("darin Nettobetrag", eur(c["net"]), False))
        for r, t in c["taxes"].items():
            totals.append((f"darin enthaltene USt {r} %", eur(t), False))
    else:
        totals.append((L["sub"], eur(c["net"], en), False))
        for r, t in c["taxes"].items():
            label = (f"VAT {r}%" if en else f"USt {r} % auf {eur(c['net_by_rate'][r])}")
            totals.append((label, eur(t, en), False))
        totals.append((L["due"], eur(c["gross"], en), True))
    for label, value, bold in totals:
        pdf.setFont("Times-Bold" if bold else "Times-Roman", 11 if bold else 10)
        pdf.drawString(w - 300, y, label)
        pdf.drawRightString(w - 50, y, value)
        y -= 16
    y -= 10
    pdf.setFont("Times-Roman", 9.5)
    notes = list(inv.get("notes", []))
    if brutto:
        notes.append("Alle Preise inkl. gesetzlicher Umsatzsteuer.")
    notes.append("Payment within 30 days, no deduction." if en else "Zahlungsziel: 30 Tage netto.")
    for note in notes:
        for part in simpleSplit(note, "Times-Roman", 9.5, w - 100):
            pdf.drawString(50, y, part)
            y -= 12
    pdf.setFont("Times-Roman", 7.5)
    pdf.drawCentredString(w / 2, 60, f'{s["name"]} · Managing director: {s["gf"]} · IBAN {s["iban"]}' if en else
                          f'{s["name"]} · Geschäftsführung: {s["gf"]} · {s["hrb"]} · Steuer-Nr. {s["steuernr"]}')
    pdf.drawCentredString(w / 2, 50, "" if en else f'Bankverbindung: IBAN {s["iban"]} · BIC {s["bic"]}')
    pdf.save()


# --------------------------------------------------------------------------- Kassenbon


def render_receipt(path: Path, inv: dict[str, Any], c: dict[str, Any]) -> None:
    s = SUP[inv["sup"]]
    width = 80 * 2.8346
    lines: list[tuple[str, str]] = []  # (links, rechts)
    lines += [(s["name"].upper(), ""), (s["street"], ""), (s["postcode_city"], ""), (f'Tel. {s["phone"]}', ""),
              (f'USt-IdNr. {s["vat_id"]}', ""), ("-" * 32, "")]
    for row in c["rows"]:
        code = "A" if row["rate"] == 19 else "B"
        if row["q"] != 1:
            lines.append((row["desc"][:30], ""))
            lines.append((f'  {num(row["q"])} x {b2(row["price"])}', f'{b2(row["amount"])} {code}'))
        elif len(row["desc"]) > 22:
            lines.append((row["desc"][:30], ""))
            lines.append(("", f'{b2(row["amount"])} {code}'))
        else:
            lines.append((row["desc"], f'{b2(row["amount"])} {code}'))
    lines += [("-" * 32, ""), ("SUMME EUR", b2(c["gross"])), ("", ""), ("Gegeben EC-Karte", b2(c["gross"])), ("", "")]
    lines.append(("MwSt   Netto    MwSt   Brutto", ""))
    for r, t in c["taxes"].items():
        code = "A" if r == 19 else "B"
        gross_r = sum((row["amount"] for row in c["rows"] if row["rate"] == r), D(0))
        lines.append((f"{code} {r}% {b2(gross_r - t):>8} {b2(t):>6} {b2(gross_r):>7}", ""))
    y, m, d = inv["date"].split("-")
    lines += [("", ""), (f"{d}.{m}.{y}  18:42  Bon 4711", ""), ("Vielen Dank für Ihren Einkauf!", "")]
    if inv["id"] == "S29":
        lines += [("", ""), ("Angaben zum Nachweis der", ""), ("Höhe und der betrieblichen", ""),
                  ("Veranlassung von Bewirtungs-", ""), ("aufwendungen (§ 4 Abs. 5 EStG)", ""),
                  ("Anlass: Kundengespräch", ""), ("Bewirtete Personen: siehe Anlage", "")]
    height = 30 + 12 * len(lines)
    pdf = canvas.Canvas(str(path), pagesize=(width, height))
    yy = height - 20
    for left, right in lines:
        pdf.setFont("Courier-Bold" if left.startswith(("SUMME", s["name"].upper())) else "Courier", 8)
        pdf.drawString(8, yy, left)
        if right:
            pdf.drawRightString(width - 8, yy, right)
        yy -= 12
    pdf.save()


# --------------------------------------------------------------------------- Brief


def render_letter(path: Path, inv: dict[str, Any], c: dict[str, Any]) -> None:
    s, cli = SUP[inv["sup"]], MANDANTEN[inv["client"]]
    pdf = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, h - 60, s["name"])
    pdf.setFont("Helvetica", 9)
    pdf.drawString(60, h - 74, f'{s["street"]} · {s["postcode_city"]} · Tel. {s["phone"]}')
    y = h - 130
    pdf.setFont("Helvetica", 10.5)
    for line in [cli["name"], cli["street"], f'{cli["postcode"]} {cli["city"]}']:
        pdf.drawString(60, y, line)
        y -= 14
    pdf.drawRightString(w - 60, h - 130, f'Fürth, {long_date(inv["date"])}')
    y -= 30
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(60, y, f'Rechnung Nr. {inv["nr"]} – Miete November 2026')
    y -= 30
    r = c["rows"]
    tax = c["taxes"][19]
    text = (
        f'Sehr geehrte Damen und Herren, sehr geehrte Frau {cli["person"].split()[-1]},\n\n'
        f'gemäß Mietvertrag vom 01.03.2024 berechnen wir Ihnen für den Monat November 2026 die Miete für die '
        f'Büroeinheit im 2. Obergeschoss in Höhe von {eur(r[0]["amount"])} sowie für den Tiefgaragenstellplatz '
        f'Nr. 14 {eur(r[1]["amount"])}, zusammen {eur(c["net"])} netto. Da wir zur Umsatzsteuer optiert haben '
        f'(§ 9 UStG), kommen 19 % Umsatzsteuer in Höhe von {eur(tax)} hinzu. Der Gesamtbetrag beläuft sich somit '
        f'auf {eur(c["gross"])}.\n\n'
        f'Bitte überweisen Sie den Betrag bis zum 03.11.2026 auf unser Konto IBAN {s["iban"]}. '
        f'Leistungszeitraum: 01.11.2026 bis 30.11.2026.\n\n'
        f'Mit freundlichen Grüßen\n\n{s["contact"]}\n{s["name"]}\nUSt-IdNr. {s["vat_id"]} · Geschäftsführerin: {s["gf"]}'
    )
    pdf.setFont("Helvetica", 10.5)
    for para in text.split("\n"):
        for part in simpleSplit(para, "Helvetica", 10.5, w - 120) or [""]:
            pdf.drawString(60, y, part)
            y -= 15
    pdf.save()


# --------------------------------------------------------------------------- klassische Vorlage


def render_classic(path: Path, inv: dict[str, Any], c: dict[str, Any]) -> None:
    s, cli = SUP[inv["sup"]], MANDANTEN[inv["client"]]
    lines = []
    for pos, row in enumerate(c["rows"], start=1):
        desc = row["desc"]
        if row["discount"]:
            desc += f' (Listenpreis {money(row["base"])}, abzgl. {num(row["discount"])} % Rabatt)'
        lines.append({"pos": pos, "desc": desc, "qty": num(row["q"]), "unit": row["unit"], "price": money(row["price"]),
                      "rate": f'{row["rate"]} %', "amount": money(row["amount"])})
    totals = [("Nettobetrag", money(c["net"]), False)]
    for r, t in c["taxes"].items():
        totals.append((f"Umsatzsteuer {r} % auf {money(c['net_by_rate'][r])}", money(t), False))
    totals.append(("Rechnungsbetrag", money(c["gross"]), True))
    meta = [("Rechnung", inv["nr"])] + list(inv.get("meta_extra", [])) + [("Datum", de_date(inv["date"]))]
    render(path, {
        "seller": s,
        "buyer": {"name": cli["name"], "attn": cli["attn"], "street": cli["street"], "postcode": cli["postcode"], "city": cli["city"]},
        "title": "Schlussrechnung" if "Schlussrechnung" in " ".join(inv["tags"]) else "Rechnung",
        "meta": meta, "lines": lines, "totals": totals,
        "notes": list(inv.get("notes", []))
        + ([f'Noch zu zahlen: {money(c["gross"] - D(inv["abschlag"]))}'] if inv.get("abschlag") else [])
        + ["Zahlbar innerhalb von 14 Tagen ohne Abzug."],
        "contact_lines": [f'Ansprechpartner: {s["contact"]}', f'Tel. {s["phone"]}', f'E-Mail: {s["email"]}',
                          f'USt-IdNr.: {s["vat_id"]}', f'Steuernummer: {s["steuernr"]}'],
        "footer": [f'{s["name"]} · Geschäftsführer: {s["gf"]} · {s["hrb"]}', f'IBAN {s["iban"]} · BIC {s["bic"]}'],
    })


# --------------------------------------------------------------------------- Verschlechterungen


def to_image(pdf_path: Path, dpi: int) -> np.ndarray:
    with pymupdf.open(pdf_path) as doc:
        pix = doc[0].get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).copy()


def phone_photo(src: Path, dst: Path) -> None:
    """Kassenbon als Handyfoto: Tisch als Hintergrund, Perspektive, ungleichmäßiges Licht, JPG."""
    rng = np.random.default_rng(30)
    bon = to_image(src, 220)
    bh, bw = bon.shape[:2]
    H, W = int(bh * 1.35), int(bw * 2.2)
    table = np.full((H, W, 3), (92, 110, 128), np.uint8)  # Holztisch, BGR-artig
    table = (table + rng.normal(0, 8, table.shape)).clip(0, 255).astype(np.uint8)
    ox, oy = (W - bw) // 2, (H - bh) // 2
    src_pts = np.float32([[0, 0], [bw, 0], [bw, bh], [0, bh]])
    dst_pts = np.float32([[ox + 40, oy + 10], [ox + bw - 10, oy + 45], [ox + bw + 25, oy + bh - 20], [ox - 15, oy + bh - 5]])
    m = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(bon, m, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mask = cv2.warpPerspective(np.full((bh, bw), 255, np.uint8), m, (W, H))
    img = np.where(mask[..., None] > 0, warped, table)
    yy, xx = np.mgrid[0:H, 0:W]
    light = 1.05 - 0.35 * ((xx / W) * 0.6 + (yy / H) * 0.4)  # Schatten zur rechten unteren Ecke
    img = (img.astype(np.float32) * light[..., None]).clip(0, 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0.7)
    ok, jpg = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 70])
    assert ok
    dst.write_bytes(jpg.tobytes())


def upside_down_scan(src: Path, dst: Path) -> None:
    rng = np.random.default_rng(31)
    img = cv2.cvtColor(to_image(src, 200), cv2.COLOR_RGB2GRAY)
    img = np.rot90(img, 2).copy()
    img = (img.astype(np.float32) * 0.92 + 12 + rng.normal(0, 10, img.shape)).clip(0, 255).astype(np.uint8)
    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])
    assert ok
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_image(page.rect, stream=jpg.tobytes())
    doc.save(dst, deflate=True)
    doc.close()


# --------------------------------------------------------------------------- Hauptprogramm


def main() -> None:
    syn_dir, gold_dir = ROOT / "synthetisch", ROOT / "goldstandard"
    for inv in INVOICES:
        c = compute(inv)
        s, cli = SUP[inv["sup"]], MANDANTEN[inv["client"]]
        slug = s["name"].split()[0].lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("&", "").strip("-")
        degraded = inv.get("foto") or inv.get("kopf")
        name = f'{inv["id"]}_{slug}' + (".jpg" if inv.get("foto") else ".pdf")
        target = syn_dir / name
        vector = syn_dir / f'_{inv["id"]}.pdf' if degraded else target

        layout = inv["layout"]
        if layout in ("modern", "englisch"):
            render_modern(vector, inv, c, en=layout == "englisch")
        elif layout == "bon":
            render_receipt(vector, inv, c)
        elif layout == "brief":
            render_letter(vector, inv, c)
        else:
            render_classic(vector, inv, c)

        art = "pdf"
        if inv.get("foto"):
            phone_photo(vector, target)
            art = "foto"
        elif inv.get("kopf"):
            upside_down_scan(vector, target)
            art = "scan"
        if degraded:
            vector.unlink()

        expected = {
            "document_type": "invoice", "supplier_name": s["name"], "invoice_number": inv["nr"],
            "invoice_date": inv["date"], "currency": "EUR", "net_total": str(c["net"]), "tax_total": str(c["tax"]),
            "gross_total": str(c["gross"]), "reverse_charge": bool(inv.get("reverse_charge")), "lines": c["gold_lines"],
        }
        sensitive = [cli["name"], cli["person"], cli["street"], cli["vat_id"], s["iban"], s["email"], s["phone"],
                     s["steuernr"], s["contact"], s["gf"]]
        skip = {"Service-Team", "Kundenservice", "Filialleitung", "Service", "Kasse 3"}
        gold = {"id": inv["id"], "quelle": "synthetisch", "client_id": inv["client"], "merkmale": inv["tags"],
                "layout": layout, "dokumente": [{"pfad": f"synthetisch/{name}", "art": art}], "erwartet": expected,
                "sensible_werte": [v for v in sensitive if v not in skip]}
        (gold_dir / f'{inv["id"]}.json').write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(INVOICES)} Zusatzbelege erzeugt.")


if __name__ == "__main__":
    main()
