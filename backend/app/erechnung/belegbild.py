"""Lesbares Belegbild einer E-Rechnung (XRechnung/EN 16931, UBL und CII).

Die E-Rechnung hat kein Bild; maßgeblich ist das XML. Für die Sichtprüfung durch den Sachbearbeiter
wird es hier wie eine Papierrechnung aufbereitet: Parteien, Referenzen, Positionen, Zu- und Abschläge,
Steueraufschlüsselung, Summen und Zahlungsangaben. Beträge bleiben Dezimal-Strings, formatiert wird in
der Oberfläche. Das Original-XML bleibt unverändert (GoBD).

Codelisten (Stand XRechnung 3.0): Rechnungsart UNTDID 1001, Zahlungsart UNTDID 4461,
Steuerkategorie UNTDID 5305 – jeweils nur die in der XRechnung zulässigen bzw. üblichen Codes.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from lxml import etree

from app.erechnung.parser import (
    _PARSER,
    UNIT_CODES,
    _cii_date,
    _child,
    _children,
    _dec,
    _local,
    _rate,
    _text,
    parse_file,
)

RECHNUNGSART = {
    "380": "Rechnung", "381": "Gutschrift", "384": "Rechnungskorrektur", "389": "Gutschrift (Gutschriftsverfahren)",
    "326": "Teilrechnung", "386": "Vorauszahlungsrechnung", "875": "Teilrechnung (Bau)", "876": "Teilschlussrechnung",
    "877": "Schlussrechnung",
}
ZAHLUNGSART = {
    "1": "nicht festgelegt", "10": "Bar", "20": "Scheck", "30": "Überweisung", "31": "Überweisung", "42": "Zahlung auf Bankkonto",
    "48": "Kartenzahlung", "49": "Lastschrift", "54": "Kreditkarte", "55": "Debitkarte", "57": "Dauerauftrag",
    "58": "SEPA-Überweisung", "59": "SEPA-Lastschrift", "97": "Verrechnung", "ZZZ": "sonstige",
}
STEUERKATEGORIE = {
    "S": "Normalsatz", "Z": "Nullsatz", "E": "steuerbefreit", "AE": "Reverse Charge (§ 13b UStG)",
    "K": "innergemeinschaftliche Lieferung", "G": "Ausfuhr", "O": "nicht steuerbar", "L": "Kanarische Inseln",
    "M": "Ceuta und Melilla",
}


# Betreff-Code am Anfang eines Hinweises (UNTDID 4451, z. B. „#ADU#“) gehört nicht in die Anzeige
_BETREFF = re.compile(r"^#[A-Z]{3}#\s*")

# Optionale Summen (Abschläge, Zuschläge, Vorauszahlung, Rundung) nur zeigen, wenn sie nicht 0 sind
_OPTIONAL = {"Summe Abschläge", "Summe Zuschläge", "Bereits gezahlt", "Rundung"}


def _summe(label: str, wert: str | None, fett: bool = False) -> dict[str, Any] | None:
    if wert is None or (label in _OPTIONAL and Decimal(wert) == 0):
        return None
    return {"label": label, "betrag": wert, "fett": fett}


def _referenzen(paare: list[tuple[str, str | None]]) -> list[dict[str, str]]:
    return [{"label": label, "wert": wert} for label, wert in paare if wert]


def belegbild(path: Path) -> dict[str, Any]:
    root = etree.parse(str(path), _PARSER).getroot()
    daten = parse_file(path)
    if _local(root) == "CrossIndustryInvoice":
        extra = _cii(root)
        format_ = "XRechnung · UN/CEFACT CII"
    else:
        extra = _ubl(root, credit=_local(root) == "CreditNote")
        format_ = "XRechnung · UBL"
    parteien = daten["parties"]
    code = parteien.get("type_code") or ""
    return {
        "format": format_,
        "art": RECHNUNGSART.get(code, "Rechnung") + (f" ({code})" if code and code not in RECHNUNGSART else ""),
        "nummer": daten["invoice_number"],
        "datum": daten["invoice_date"],
        "leistung": daten["service_period"],
        "waehrung": daten["currency"],
        "verkaeufer": {**parteien["seller"], **extra.pop("verkaeufer_extra")},
        "kaeufer": parteien["buyer"],
        "hinweise": [_BETREFF.sub("", n) for n in parteien.get("notes", [])],
        **extra,
    }


# --------------------------------------------------------------------------- UBL


def _ubl(root: etree._Element, credit: bool) -> dict[str, Any]:
    seller = _child(root, "AccountingSupplierParty", "Party")
    totals = _child(root, "LegalMonetaryTotal")
    currency = _text(root, "DocumentCurrencyCode") or "EUR"

    positionen = []
    for line in _children(root, "CreditNoteLine" if credit else "InvoiceLine"):
        qty = _child(line, "CreditedQuantity" if credit else "InvoicedQuantity")
        positionen.append({
            "nr": _text(line, "ID"),
            "bezeichnung": _text(line, "Item", "Name"),
            "beschreibung": _text(line, "Item", "Description") or _text(line, "Note"),
            "menge": _dec(qty.text if qty is not None else None),
            "einheit": UNIT_CODES.get(qty.get("unitCode") or "", qty.get("unitCode")) if qty is not None else None,
            "einzelpreis": _dec(_text(line, "Price", "PriceAmount")),
            "netto": _dec(_text(line, "LineExtensionAmount")),
            "satz": _rate(_text(line, "Item", "ClassifiedTaxCategory", "Percent")),
        })

    steuern = []
    steuer_gesamt: str | None = None
    for tt in _children(root, "TaxTotal"):
        betrag_el = _child(tt, "TaxAmount")
        if betrag_el is not None and betrag_el.get("currencyID", currency) != currency:
            continue  # Steuer in Buchungswährung (BT-111) nicht doppelt zeigen
        if steuer_gesamt is None and betrag_el is not None:
            steuer_gesamt = _dec(betrag_el.text)
        for sub in _children(tt, "TaxSubtotal"):
            kat = _child(sub, "TaxCategory")
            steuern.append({
                "kategorie": STEUERKATEGORIE.get(_text(kat, "ID") or "", _text(kat, "ID")),
                "satz": _rate(_text(kat, "Percent")),
                "basis": _dec(_text(sub, "TaxableAmount")),
                "betrag": _dec(_text(sub, "TaxAmount")),
                "grund": _text(kat, "TaxExemptionReason"),
            })

    zuschlaege = [{
        "art": "Zuschlag" if _text(ac, "ChargeIndicator") == "true" else "Abschlag",
        "grund": _text(ac, "AllowanceChargeReason") or _text(ac, "AllowanceChargeReasonCode"),
        "betrag": _dec(_text(ac, "Amount")),
        "satz": _rate(_text(ac, "TaxCategory", "Percent")),
    } for ac in _children(root, "AllowanceCharge")]

    mittel = _child(root, "PaymentMeans")
    konto = _child(mittel, "PayeeFinancialAccount")
    return {
        "verkaeufer_extra": {
            "steuernummer": next((_text(s, "CompanyID") for s in _children(seller, "PartyTaxScheme")
                                  if _text(s, "TaxScheme", "ID") != "VAT"), None),
            "register": _text(seller, "PartyLegalEntity", "CompanyID"),
        },
        "faellig": _text(root, "DueDate") or _text(root, "PaymentMeans", "PaymentDueDate"),
        "referenzen": _referenzen([
            ("Leitweg-ID / Käuferreferenz", _text(root, "BuyerReference")),
            ("Bestellnummer", _text(root, "OrderReference", "ID")),
            ("Vertrag", _text(root, "ContractDocumentReference", "ID")),
            ("Projekt", _text(root, "ProjectReference", "ID")),
            ("Vorherige Rechnung", _text(root, "BillingReference", "InvoiceDocumentReference", "ID")),
        ]),
        "positionen": positionen,
        "zuschlaege": zuschlaege,
        "steuern": steuern,
        "summen": [s for s in (
            _summe("Summe Positionen netto", _dec(_text(totals, "LineExtensionAmount"))),
            _summe("Summe Abschläge", _dec(_text(totals, "AllowanceTotalAmount"))),
            _summe("Summe Zuschläge", _dec(_text(totals, "ChargeTotalAmount"))),
            _summe("Gesamt netto", _dec(_text(totals, "TaxExclusiveAmount"))),
            _summe("Umsatzsteuer", steuer_gesamt),
            _summe("Gesamt brutto", _dec(_text(totals, "TaxInclusiveAmount")), fett=True),
            _summe("Bereits gezahlt", _dec(_text(totals, "PrepaidAmount"))),
            _summe("Rundung", _dec(_text(totals, "PayableRoundingAmount"))),
            _summe("Zahlbetrag", _dec(_text(totals, "PayableAmount")), fett=True),
        ) if s],
        "zahlung": {
            "art": ZAHLUNGSART.get(_text(mittel, "PaymentMeansCode") or "", _text(mittel, "PaymentMeansCode")),
            "iban": _text(konto, "ID"),
            "bic": _text(konto, "FinancialInstitutionBranch", "ID"),
            "inhaber": _text(konto, "Name"),
            "verwendungszweck": _text(mittel, "PaymentID"),
            "bedingungen": _text(root, "PaymentTerms", "Note"),
        },
    }


# --------------------------------------------------------------------------- CII


def _cii(root: etree._Element) -> dict[str, Any]:
    tx = _child(root, "SupplyChainTradeTransaction")
    agreement = _child(tx, "ApplicableHeaderTradeAgreement")
    settlement = _child(tx, "ApplicableHeaderTradeSettlement")
    summary = _child(settlement, "SpecifiedTradeSettlementHeaderMonetarySummation")
    seller = _child(agreement, "SellerTradeParty")
    currency = _text(settlement, "InvoiceCurrencyCode") or "EUR"

    positionen = []
    for item in _children(tx, "IncludedSupplyChainTradeLineItem"):
        qty = _child(item, "SpecifiedLineTradeDelivery", "BilledQuantity")
        lsett = _child(item, "SpecifiedLineTradeSettlement")
        positionen.append({
            "nr": _text(item, "AssociatedDocumentLineDocument", "LineID"),
            "bezeichnung": _text(item, "SpecifiedTradeProduct", "Name"),
            "beschreibung": _text(item, "SpecifiedTradeProduct", "Description")
            or _text(item, "AssociatedDocumentLineDocument", "IncludedNote", "Content"),
            "menge": _dec(qty.text if qty is not None else None),
            "einheit": UNIT_CODES.get(qty.get("unitCode") or "", qty.get("unitCode")) if qty is not None else None,
            "einzelpreis": _dec(_text(item, "SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount")),
            "netto": _dec(_text(lsett, "SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount")),
            "satz": _rate(_text(lsett, "ApplicableTradeTax", "RateApplicablePercent")),
        })

    steuern = [{
        "kategorie": STEUERKATEGORIE.get(_text(t, "CategoryCode") or "", _text(t, "CategoryCode")),
        "satz": _rate(_text(t, "RateApplicablePercent")),
        "basis": _dec(_text(t, "BasisAmount")),
        "betrag": _dec(_text(t, "CalculatedAmount")),
        "grund": _text(t, "ExemptionReason"),
    } for t in _children(settlement, "ApplicableTradeTax")]

    zuschlaege = [{
        "art": "Zuschlag" if _text(ac, "ChargeIndicator", "Indicator") == "true" else "Abschlag",
        "grund": _text(ac, "Reason") or _text(ac, "ReasonCode"),
        "betrag": _dec(_text(ac, "ActualAmount")),
        "satz": _rate(_text(ac, "CategoryTradeTax", "RateApplicablePercent")),
    } for ac in _children(settlement, "SpecifiedTradeAllowanceCharge")]

    steuer_gesamt = next((_dec(el.text) for el in _children(summary, "TaxTotalAmount")
                          if el.get("currencyID", currency) == currency), None)
    mittel = _child(settlement, "SpecifiedTradeSettlementPaymentMeans")
    konto = _child(mittel, "PayeePartyCreditorFinancialAccount")
    bedingungen = _child(settlement, "SpecifiedTradePaymentTerms")
    return {
        "verkaeufer_extra": {
            "steuernummer": next((r.text.strip() for reg in _children(seller, "SpecifiedTaxRegistration")
                                  for r in _children(reg, "ID") if r.get("schemeID") == "FC" and r.text), None),
            "register": _text(seller, "SpecifiedLegalOrganization", "ID"),
        },
        "faellig": _cii_date(_text(bedingungen, "DueDateDateTime", "DateTimeString")),
        "referenzen": _referenzen([
            ("Leitweg-ID / Käuferreferenz", _text(agreement, "BuyerReference")),
            ("Bestellnummer", _text(agreement, "BuyerOrderReferencedDocument", "IssuerAssignedID")),
            ("Vertrag", _text(agreement, "ContractReferencedDocument", "IssuerAssignedID")),
            ("Projekt", _text(agreement, "SpecifiedProcuringProject", "ID")),
            ("Vorherige Rechnung", _text(settlement, "InvoiceReferencedDocument", "IssuerAssignedID")),
        ]),
        "positionen": positionen,
        "zuschlaege": zuschlaege,
        "steuern": steuern,
        "summen": [s for s in (
            _summe("Summe Positionen netto", _dec(_text(summary, "LineTotalAmount"))),
            _summe("Summe Abschläge", _dec(_text(summary, "AllowanceTotalAmount"))),
            _summe("Summe Zuschläge", _dec(_text(summary, "ChargeTotalAmount"))),
            _summe("Gesamt netto", _dec(_text(summary, "TaxBasisTotalAmount"))),
            _summe("Umsatzsteuer", steuer_gesamt),
            _summe("Gesamt brutto", _dec(_text(summary, "GrandTotalAmount")), fett=True),
            _summe("Bereits gezahlt", _dec(_text(summary, "TotalPrepaidAmount"))),
            _summe("Rundung", _dec(_text(summary, "RoundingAmount"))),
            _summe("Zahlbetrag", _dec(_text(summary, "DuePayableAmount")), fett=True),
        ) if s],
        "zahlung": {
            "art": ZAHLUNGSART.get(_text(mittel, "TypeCode") or "", _text(mittel, "TypeCode")),
            "iban": _text(konto, "IBANID"),
            "bic": _text(mittel, "PayeeSpecifiedCreditorFinancialInstitution", "BICID"),
            "inhaber": _text(konto, "AccountName"),
            "verwendungszweck": _text(settlement, "PaymentReference"),
            "bedingungen": _text(bedingungen, "Description"),
        },
    }
