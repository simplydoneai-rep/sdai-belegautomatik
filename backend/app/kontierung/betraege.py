"""Beträge als Decimal (CLAUDE.md Regel 17). Nie Float."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    """Kaufmännisch auf 2 Stellen runden."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


_CLEAN = re.compile(r"[^\d,.\-]")


def parse_amount(value: object) -> Decimal | None:
    """Liest Beträge in deutscher ("1.234,56") oder technischer ("1234.56") Schreibweise.

    Gibt None zurück, wenn kein Betrag erkennbar ist. Floats werden abgelehnt.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        raise TypeError("Beträge nie als float übergeben")
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("-") or text.endswith("-") or (text.startswith("(") and text.endswith(")"))
    text = _CLEAN.sub("", text).replace("-", "")
    if not text or not any(c.isdigit() for c in text):
        return None
    if "," in text and "." in text:
        # Das zuletzt stehende Zeichen ist das Dezimaltrennzeichen.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        # Auf deutschen Rechnungen ist "," der Dezimaltrenner.
        head, _, tail = text.rpartition(",")
        text = head.replace(",", "") + "." + tail
    elif text.count(".") > 1:
        head, _, tail = text.rpartition(".")
        text = head.replace(".", "") + ("" if len(tail) == 3 else ".") + tail
    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None
    return -amount if negative else amount
