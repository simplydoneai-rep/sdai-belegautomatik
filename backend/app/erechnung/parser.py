"""Parser für E-Rechnungen: XRechnung/EN 16931 in UBL (Invoice, CreditNote) und UN/CEFACT CII.

Strukturierte Daten brauchen keine KI. Ausgabe im selben Schema wie die KI-Antwort
(``app.llm.base.OUTPUT_SCHEMA``), Beträge als Dezimal-Strings. Zusätzlich ``parties`` mit
Verkäufer- und Käuferangaben; diese verlassen das System nie in Richtung KI.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from lxml import etree

from app.kontierung.betraege import parse_amount

# Sicher parsen: keine externen Entitäten, kein Netzwerk (XXE-Schutz).
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)

UNIT_CODES = {
    "C62": "Stück", "H87": "Stück", "XPP": "Stück", "EA": "Stück", "LS": "pauschal",
    "HUR": "Std", "DAY": "Tag", "MON": "Monat", "KGM": "kg", "GRM": "g", "LTR": "l",
    "MTR": "m", "MTK": "m²", "MTQ": "m³", "KMT": "km", "TNE": "t", "SET": "Set", "XBX": "Karton",
}
CREDIT_TYPE_CODES = {"381", "396", "81", "83", "532"}
REVERSE_CHARGE_CATEGORIES = {"AE", "K"}  # AE: § 13b, K: innergemeinschaftlich


class ERechnungFehler(ValueError):
    pass


def _local(el: etree._Element) -> str:
    return etree.QName(el).localname


def _child(el: etree._Element | None, *path: str) -> etree._Element | None:
    for name in path:
        if el is None:
            return None
        el = next((c for c in el if isinstance(c.tag, str) and _local(c) == name), None)
    return el


def _children(el: etree._Element | None, name: str) -> list[etree._Element]:
    if el is None:
        return []
    return [c for c in el if isinstance(c.tag, str) and _local(c) == name]


def _text(el: etree._Element | None, *path: str) -> str | None:
    node = _child(el, *path) if path else el
    if node is None or node.text is None:
        return None
    return node.text.strip() or None


def _dec(value: str | None) -> str | None:
    amount = parse_amount(value) if value is not None else None
    return None if amount is None else str(amount)


def _rate(value: str | None) -> str:
    amount = parse_amount(value) if value else None
    if amount is None:
        return "0"
    return str(amount.normalize()) if amount == amount.to_integral() else str(amount)


def parse_file(path: Path) -> dict[str, Any]:
    root = etree.parse(str(path), _PARSER).getroot()
    kind = _local(root)
    if kind in ("Invoice", "CreditNote"):
        return _parse_ubl(root, credit=kind == "CreditNote")
    if kind == "CrossIndustryInvoice":
        return _parse_cii(root)
    raise ERechnungFehler(f"Unbekanntes E-Rechnungsformat: {kind}")


# --------------------------------------------------------------------------- UBL


def _ubl_party(party: etree._Element | None) -> dict[str, Any]:
    p = _child(party, "Party")
    addr = _child(p, "PostalAddress")
    return {
        "name": _text(p, "PartyLegalEntity", "RegistrationName") or _text(p, "PartyName", "Name"),
        "street": _text(addr, "StreetName"),
        "postcode": _text(addr, "PostalZone"),
        "city": _text(addr, "CityName"),
        "country": _text(addr, "Country", "IdentificationCode"),
        "vat_id": next(
            (_text(s, "CompanyID") for s in _children(p, "PartyTaxScheme") if _text(s, "TaxScheme", "ID") == "VAT"),
            None,
        ),
        "contact": _text(p, "Contact", "Name"),
        "phone": _text(p, "Contact", "Telephone"),
        "email": _text(p, "Contact", "ElectronicMail"),
    }


def _parse_ubl(root: etree._Element, credit: bool) -> dict[str, Any]:
    currency = _text(root, "DocumentCurrencyCode") or "EUR"
    type_code = _text(root, "CreditNoteTypeCode" if credit else "InvoiceTypeCode") or ""
    totals = _child(root, "LegalMonetaryTotal")

    tax_total: str | None = None
    categories: set[str] = set()
    for tt in _children(root, "TaxTotal"):
        amount_el = _child(tt, "TaxAmount")
        if amount_el is not None and amount_el.get("currencyID", currency) == currency and tax_total is None:
            tax_total = _dec(amount_el.text)
        for sub in _children(tt, "TaxSubtotal"):
            cat = _text(sub, "TaxCategory", "ID")
            if cat:
                categories.add(cat)

    lines = []
    for line in _children(root, "CreditNoteLine" if credit else "InvoiceLine"):
        qty_el = _child(line, "CreditedQuantity" if credit else "InvoicedQuantity")
        unit_code = qty_el.get("unitCode") if qty_el is not None else None
        tax_cat = _child(line, "Item", "ClassifiedTaxCategory")
        lines.append(
            {
                "description": _text(line, "Item", "Name"),
                "quantity": _dec(qty_el.text if qty_el is not None else None),
                "unit": UNIT_CODES.get(unit_code or "", unit_code),
                "unit_price": _dec(_text(line, "Price", "PriceAmount")),
                "net_amount": _dec(_text(line, "LineExtensionAmount")),
                "tax_rate": _rate(_text(tax_cat, "Percent")),
                "account_skr03": None,
            }
        )

    payment = _child(root, "PaymentMeans", "PayeeFinancialAccount")
    return {
        "document_type": "credit_note" if credit or type_code in CREDIT_TYPE_CODES else "invoice",
        "supplier_name": _ubl_party(_child(root, "AccountingSupplierParty"))["name"],
        "invoice_number": _text(root, "ID"),
        "invoice_date": _text(root, "IssueDate"),
        "currency": currency,
        "net_total": _dec(_text(totals, "TaxExclusiveAmount")),
        "tax_total": tax_total or "0",
        "gross_total": _dec(_text(totals, "TaxInclusiveAmount")),
        "reverse_charge": bool(categories & REVERSE_CHARGE_CATEGORIES),
        "lines": lines,
        "parties": {
            "seller": _ubl_party(_child(root, "AccountingSupplierParty")),
            "buyer": _ubl_party(_child(root, "AccountingCustomerParty")),
            "iban": _text(payment, "ID"),
            "type_code": type_code,
            "tax_categories": sorted(categories),
            "notes": [n.text.strip() for n in _children(root, "Note") if n.text and n.text.strip()],
        },
    }


# --------------------------------------------------------------------------- CII


def _cii_party(p: etree._Element | None) -> dict[str, Any]:
    addr = _child(p, "PostalTradeAddress")
    vat = next(
        (r.text.strip() for r in _children(p, "SpecifiedTaxRegistration") for r in _children(r, "ID")
         if r.get("schemeID") == "VA" and r.text),
        None,
    )
    contact = _child(p, "DefinedTradeContact")
    return {
        "name": _text(p, "Name"),
        "street": _text(addr, "LineOne"),
        "postcode": _text(addr, "PostcodeCode"),
        "city": _text(addr, "CityName"),
        "country": _text(addr, "CountryID"),
        "vat_id": vat,
        "contact": _text(contact, "PersonName"),
        "phone": _text(contact, "TelephoneUniversalCommunication", "CompleteNumber"),
        "email": _text(contact, "EmailURIUniversalCommunication", "URIID"),
    }


def _cii_date(value: str | None) -> str | None:
    if value and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value


def _parse_cii(root: etree._Element) -> dict[str, Any]:
    doc = _child(root, "ExchangedDocument")
    tx = _child(root, "SupplyChainTradeTransaction")
    agreement = _child(tx, "ApplicableHeaderTradeAgreement")
    settlement = _child(tx, "ApplicableHeaderTradeSettlement")
    currency = _text(settlement, "InvoiceCurrencyCode") or "EUR"
    summary = _child(settlement, "SpecifiedTradeSettlementHeaderMonetarySummation")
    type_code = _text(doc, "TypeCode") or ""

    tax_total: str | None = None
    for el in _children(summary, "TaxTotalAmount"):
        if el.get("currencyID", currency) == currency:
            tax_total = _dec(el.text)
            break
    categories = {c for t in _children(settlement, "ApplicableTradeTax") if (c := _text(t, "CategoryCode"))}

    lines = []
    for item in _children(tx, "IncludedSupplyChainTradeLineItem"):
        qty_el = _child(item, "SpecifiedLineTradeDelivery", "BilledQuantity")
        unit_code = qty_el.get("unitCode") if qty_el is not None else None
        lsett = _child(item, "SpecifiedLineTradeSettlement")
        lines.append(
            {
                "description": _text(item, "SpecifiedTradeProduct", "Name"),
                "quantity": _dec(qty_el.text if qty_el is not None else None),
                "unit": UNIT_CODES.get(unit_code or "", unit_code),
                "unit_price": _dec(
                    _text(item, "SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount")
                ),
                "net_amount": _dec(_text(lsett, "SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount")),
                "tax_rate": _rate(_text(lsett, "ApplicableTradeTax", "RateApplicablePercent")),
                "account_skr03": None,
            }
        )

    seller = _cii_party(_child(agreement, "SellerTradeParty"))
    return {
        "document_type": "credit_note" if type_code in CREDIT_TYPE_CODES else "invoice",
        "supplier_name": seller["name"],
        "invoice_number": _text(doc, "ID"),
        "invoice_date": _cii_date(_text(doc, "IssueDateTime", "DateTimeString")),
        "currency": currency,
        "net_total": _dec(_text(summary, "TaxBasisTotalAmount")),
        "tax_total": tax_total or "0",
        "gross_total": _dec(_text(summary, "GrandTotalAmount")),
        "reverse_charge": bool(categories & REVERSE_CHARGE_CATEGORIES),
        "lines": lines,
        "parties": {
            "seller": seller,
            "buyer": _cii_party(_child(agreement, "BuyerTradeParty")),
            "iban": _text(settlement, "SpecifiedTradeSettlementPaymentMeans", "PayeePartyCreditorFinancialAccount", "IBANID"),
            "type_code": type_code,
            "tax_categories": sorted(categories),
            "notes": [t for n in _children(doc, "IncludedNote") if (t := _text(n, "Content"))],
        },
    }


def without_parties(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k != "parties"}


def sum_check(data: dict[str, Any]) -> bool:
    net, tax, gross = (parse_amount(data.get(k)) for k in ("net_total", "tax_total", "gross_total"))
    return None not in (net, tax, gross) and abs(net + tax - gross) <= Decimal("0.01")  # type: ignore[operator]
