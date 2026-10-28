"""Vergleich eines Ausleseergebnisses mit dem Goldstandard (CLAUDE.md: Qualitätsmessung ab Tag 1)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from rapidfuzz import fuzz

from app.kontierung.betraege import parse_amount

TOLERANZ = Decimal("0.01")
LIEFERANT_MIN_SCORE = 90.0

PFLICHTFELDER = (
    "supplier_name", "invoice_number", "invoice_date", "net_total", "tax_total", "gross_total",
    "tax_rates", "document_type", "reverse_charge",
)


def _norm_text(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip().lower()


def _norm_id(v: Any) -> str:
    return re.sub(r"[\s]", "", str(v or "")).upper()


def _rate(v: Any) -> Decimal | None:
    try:
        r = parse_amount(v)
    except TypeError:
        return None
    return None if r is None else r.normalize()


def _amount(v: Any) -> Decimal | None:
    try:
        return parse_amount(v)
    except TypeError:
        return None


def _same_amount(a: Any, b: Any) -> bool:
    x, y = _amount(a), _amount(b)
    if x is None or y is None:
        return x is None and y is None
    return abs(x - y) <= TOLERANZ


def supplier_matches(expected: Any, actual: Any) -> bool:
    if not expected or not actual:
        return not expected and not actual
    return fuzz.token_sort_ratio(_norm_text(expected), _norm_text(actual)) >= LIEFERANT_MIN_SCORE


def compare(expected: dict[str, Any], actual: dict[str, Any] | None) -> dict[str, Any]:
    """Gibt je Feld True/False zurück und je Positionsmerkmal (richtig, gesamt)."""
    exp_lines = expected.get("lines") or []
    if actual is None:
        felder = {f: False for f in PFLICHTFELDER}
        n_acc = sum(1 for ln in exp_lines if ln.get("account_skr03"))
        return {
            "felder": felder,
            "positionen": {"anzahl": False, "betrag": [0, len(exp_lines)], "steuersatz": [0, len(exp_lines)],
                           "konto": [0, n_acc]},
        }

    act_lines = [ln for ln in (actual.get("lines") or []) if isinstance(ln, dict)]
    exp_rates = {_rate(ln.get("tax_rate")) for ln in exp_lines}
    act_rates = {_rate(ln.get("tax_rate")) for ln in act_lines}

    felder = {
        "supplier_name": supplier_matches(expected.get("supplier_name"), actual.get("supplier_name")),
        "invoice_number": _norm_id(expected.get("invoice_number")) == _norm_id(actual.get("invoice_number")),
        "invoice_date": str(expected.get("invoice_date")) == str(actual.get("invoice_date")),
        "net_total": _same_amount(expected.get("net_total"), actual.get("net_total")),
        "tax_total": _same_amount(expected.get("tax_total"), actual.get("tax_total")),
        "gross_total": _same_amount(expected.get("gross_total"), actual.get("gross_total")),
        "tax_rates": exp_rates == act_rates,
        "document_type": expected.get("document_type") == actual.get("document_type"),
        "reverse_charge": bool(expected.get("reverse_charge")) == bool(actual.get("reverse_charge")),
    }

    # Positionen über den Nettobetrag zuordnen (Reihenfolge egal).
    unused = list(range(len(act_lines)))
    betrag = satz = konto = konto_total = 0
    for exp in exp_lines:
        match = next((i for i in unused if _same_amount(exp.get("net_amount"), act_lines[i].get("net_amount"))), None)
        if exp.get("account_skr03"):
            konto_total += 1
        if match is None:
            continue
        unused.remove(match)
        act = act_lines[match]
        betrag += 1
        satz += _rate(exp.get("tax_rate")) == _rate(act.get("tax_rate"))
        if exp.get("account_skr03"):
            konto += str(exp["account_skr03"]) == str(act.get("account_skr03"))

    return {
        "felder": felder,
        "positionen": {
            "anzahl": len(exp_lines) == len(act_lines),
            "betrag": [betrag, len(exp_lines)],
            "steuersatz": [int(satz), len(exp_lines)],
            "konto": [int(konto), konto_total],
        },
    }


def leaks(payload_text: str, sensitive: list[str]) -> list[int]:
    """Indizes der sensiblen Werte, die (auch leicht verändert) im KI-Text stehen.

    Gibt nur Indizes zurück, nie die Werte selbst (Logs ohne Belegdaten).
    """
    hay = re.sub(r"[^a-z0-9]", "", payload_text.lower())
    found = []
    for i, value in enumerate(sensitive):
        needle = re.sub(r"[^a-z0-9]", "", value.lower())
        if len(needle) < 6:
            continue
        # Kennungen (IBAN, USt-IdNr., Telefon) nur exakt, sonst Fehlalarme bei ähnlichen Nummern;
        # Namen und Anschriften auch unscharf (OCR-Lesefehler).
        mostly_digits = sum(c.isdigit() for c in needle) * 2 > len(needle)
        if needle in hay or (not mostly_digits and fuzz.partial_ratio(needle, hay) >= 90):
            found.append(i)
    return found
