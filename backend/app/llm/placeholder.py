"""Platzhalter-Anbieter ohne KI: regelbasiertes Auslesen des pseudonymisierten Belegtexts.

Dient dazu, die Pipeline ohne Zugangsdaten durchgängig zu testen, und als Vergleichswert
„ohne KI“. Er ist auf die Vorlage der synthetischen Testbelege abgestimmt und daher kein
Maßstab für die Qualität bei fremden Rechnungslayouts.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

from app.kontierung.betraege import parse_amount, q2
from app.llm.base import LLMProvider

_AMOUNT = r"-?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}"
_NUMBER = re.compile(r"(?i)(?:Rechnungs-?(?:nummer|nr\.?)|Gutschrift-?Nr\.?|Beleg-?Nr\.?|Invoice No\.?)\s*:?\s+([A-Z0-9][\w\-/.]*)")
_DATE = re.compile(r"(?i)(?:Rechnungsdatum|Belegdatum|Datum)\s*:?\s+(\d{1,2})\.(\d{1,2})\.(\d{4})")
_MONEY = re.compile(rf"({_AMOUNT})\s*(?:€|EUR|E\b)")
_RATE = re.compile(r"(\d{1,2})[.,]?\s*%")
_ROW = re.compile(r"^\s*(\d{1,3})\s{2,}(.+)$")

KEYWORDS: list[tuple[str, str]] = [
    (r"strom|kwh|grundpreis|gas|wasser", "4240"),
    (r"reinigung", "4250"),
    (r"flyer|visitenkarte|roll-?up|werb|plakat", "4610"),
    (r"lizenz", "4964"),
    (r"wartung|support", "4806"),
    (r"kurier|porto|versand|express", "4910"),
    (r"mobilfunk|telefon|datenvolumen|internet", "4920"),
    (r"papier a4|kopierpapier|toner|kugelschreiber|ordner", "4930"),
    (r"fachbuch|zeitschrift|datenbank|abo", "4940"),
    (r"sp[üu]lmittel|backpapier|karton|reinigungsmittel", "4980"),
    (r"miete", "4210"),
    (r"versicherung", "4360"),
]


def _account(desc: str, rate: Decimal, text: str) -> str:
    low = desc.lower()
    for pattern, account in KEYWORDS:
        if re.search(pattern, low):
            return account
    if rate == 0 and re.search(r"(?i)innergemeinschaftlich", text):
        return "3425"
    if rate == 0 and re.search(r"(?i)13b|Steuerschuldnerschaft", text):
        return "3120"
    return "3300" if rate == 7 else "3400"


def _last_money(line: str) -> Decimal | None:
    found = _MONEY.findall(line)
    return parse_amount(found[-1]) if found else None


def extract_rule_based(text: str) -> dict[str, Any]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    supplier = re.split(r"\s{3,}", lines[0].strip())[0] if lines else None
    credit = bool(re.search(r"(?i)\bGutschrift\b", text))
    gross_prices = bool(re.search(r"(?i)preis brutto|darin enthalten", text))
    rc = bool(re.search(r"(?i)§\s*13b|Steuerschuldnerschaft|innergemeinschaftlich|reverse charge", text))

    m_nr = _NUMBER.search(text)
    m_date = _DATE.search(text)
    date = f"{m_date.group(3)}-{int(m_date.group(2)):02d}-{int(m_date.group(1)):02d}" if m_date else None

    net = tax = gross = None
    tax_sum = Decimal("0")
    tax_found = False
    in_table = False
    positions: list[dict[str, Any]] = []
    for ln in lines:
        low = ln.lower()
        if re.search(r"(?i)^\s*pos\.?\s", ln):
            in_table = True
            continue
        m_row = _ROW.match(ln)
        if in_table and m_row and _MONEY.search(ln) and _RATE.search(ln):
            body = m_row.group(2)
            amount = _last_money(body)
            rates = _RATE.findall(body)
            rate = Decimal(rates[-1])
            desc = re.split(r"\s{2,}", body)[0]
            if amount is not None and gross_prices:
                amount = q2(amount * 100 / (100 + rate))
            if amount is not None and credit and amount > 0:
                amount = -amount
            positions.append(
                {"description": desc, "quantity": None, "unit": None, "unit_price": None,
                 "net_amount": None if amount is None else str(amount), "tax_rate": str(rate),
                 "account_skr03": _account(desc, rate, text)}
            )
            continue
        if positions and not m_row:
            in_table = False
        value = _last_money(ln)
        if value is None:
            continue
        if re.search(r"netto(betrag)?\b|summe netto", low) and "auf" not in low:
            net = value
        elif re.search(r"umsatzsteuer|mwst|ust\b", low) and "id" not in low:
            tax_sum += value
            tax_found = True
        elif re.search(r"rechnungsbetrag|gutschriftsbetrag|gesamtbetrag|^\s*summe\b|zu zahlen", low):
            gross = value

    if tax_found:
        tax = tax_sum
    if gross is not None and tax is not None and net is None:
        net = gross - tax
    if net is not None and tax is None and gross is not None:
        tax = gross - net

    def s(v: Decimal | None) -> str | None:
        return None if v is None else str(v)

    return {
        "document_type": "credit_note" if credit else "invoice",
        "supplier_name": supplier,
        "invoice_number": m_nr.group(1) if m_nr else None,
        "invoice_date": date,
        "currency": "EUR",
        "net_total": s(net),
        "tax_total": s(tax),
        "gross_total": s(gross),
        "reverse_charge": rc,
        "lines": positions,
    }


class PlaceholderProvider(LLMProvider):
    name = "placeholder"

    def _complete(self, system: str, user: str) -> tuple[str, int, int]:
        start, end = user.rfind("<<<\n"), user.rfind("\n>>>")
        text = user[start + 4 : end] if start >= 0 and end > start else user
        return json.dumps(extract_rule_based(text), ensure_ascii=False), 0, 0
