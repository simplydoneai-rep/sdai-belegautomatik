"""Deterministische Plausibilitätsprüfung der Steuerbeträge (CLAUDE.md Regeln 15, 17).

Im Machbarkeitstest nur die Rechenprüfung. Steuerschlüssel und Sonderfälle folgen in Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.kontierung.betraege import parse_amount, q2

TOLERANZ = Decimal("0.01")
ZULAESSIGE_SAETZE = {Decimal("0"), Decimal("7"), Decimal("19")}


@dataclass
class Pruefergebnis:
    ok: bool
    hinweise: list[str] = field(default_factory=list)


def pruefe_summen(data: dict[str, Any]) -> Pruefergebnis:
    """Prüft: Netto + Steuer = Brutto, Steuer je Satz = Netto je Satz × Satz, Satz zulässig.

    Toleranz 0,01 € je Steuersatz. Gibt Hinweise ohne Belegdaten zurück (logbar).
    """
    hinweise: list[str] = []
    net = parse_amount(data.get("net_total"))
    tax = parse_amount(data.get("tax_total"))
    gross = parse_amount(data.get("gross_total"))
    if net is None or tax is None or gross is None:
        return Pruefergebnis(False, ["summen_unvollstaendig"])

    if abs(net + tax - gross) > TOLERANZ:
        hinweise.append("netto_plus_steuer_ungleich_brutto")

    lines = data.get("lines") or []
    net_by_rate: dict[Decimal, Decimal] = {}
    for line in lines:
        rate = parse_amount(line.get("tax_rate"))
        amount = parse_amount(line.get("net_amount"))
        if rate is None or amount is None:
            hinweise.append("position_unvollstaendig")
            continue
        if rate not in ZULAESSIGE_SAETZE:
            hinweise.append("steuersatz_unzulaessig")
        net_by_rate[rate] = net_by_rate.get(rate, Decimal("0")) + amount

    if net_by_rate:
        expected_tax = sum((q2(n * r / 100) for r, n in net_by_rate.items()), Decimal("0"))
        if abs(expected_tax - tax) > TOLERANZ * len(net_by_rate):
            hinweise.append("steuer_passt_nicht_zu_positionen")
        if abs(sum(net_by_rate.values(), Decimal("0")) - net) > TOLERANZ * len(net_by_rate):
            # Bei Zu- und Abschlägen auf Belegebene zulässig, daher nur Hinweis.
            hinweise.append("positionen_ungleich_netto")

    if data.get("reverse_charge") and tax != 0:
        hinweise.append("reverse_charge_mit_steuer")

    harte = {"netto_plus_steuer_ungleich_brutto", "steuersatz_unzulaessig", "reverse_charge_mit_steuer"}
    return Pruefergebnis(not (harte & set(hinweise)), hinweise)
