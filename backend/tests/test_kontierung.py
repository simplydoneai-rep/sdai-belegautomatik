from decimal import Decimal

import pytest

from app.kontierung.betraege import parse_amount, q2
from app.kontierung.konten import load_accounts
from app.kontierung.steuerlogik import pruefe_summen


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.234,56 €", "1234.56"), ("1234.56", "1234.56"), ("1,234.56", "1234.56"), ("-46,50 €", "-46.50"),
        ("0,042", "0.042"), ("12.829.687,50", "12829687.50"), ("1.234.567", "1234567"), ("(5,00)", "-5.00"),
        ("49,00-", "-49.00"), (12, "12"), (Decimal("3.1"), "3.1"),
    ],
)
def test_parse_amount(raw: object, expected: str) -> None:
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", [None, "", "abc", True])
def test_parse_amount_leer(raw: object) -> None:
    assert parse_amount(raw) is None


def test_float_verboten() -> None:
    with pytest.raises(TypeError):
        parse_amount(1.5)


def test_q2_kaufmaennisch() -> None:
    assert q2(Decimal("3.255")) == Decimal("3.26")
    assert q2(Decimal("-3.255")) == Decimal("-3.26")
    assert q2(Decimal("0.004")) == Decimal("0.00")


def _beleg(**kw: object) -> dict[str, object]:
    base: dict[str, object] = {
        "net_total": "243.12", "tax_total": "39.34", "gross_total": "282.46", "reverse_charge": False,
        "lines": [{"net_amount": "186.00", "tax_rate": "19"}, {"net_amount": "57.12", "tax_rate": "7"}],
    }
    base.update(kw)
    return base


def test_summen_gemischte_steuersaetze_ok() -> None:
    res = pruefe_summen(_beleg())
    assert res.ok and res.hinweise == []


def test_summe_falsch() -> None:
    res = pruefe_summen(_beleg(gross_total="290.00"))
    assert not res.ok and "netto_plus_steuer_ungleich_brutto" in res.hinweise


def test_toleranz_ein_cent() -> None:
    assert pruefe_summen(_beleg(gross_total="282.47")).ok


def test_unzulaessiger_steuersatz() -> None:
    res = pruefe_summen(_beleg(lines=[{"net_amount": "243.12", "tax_rate": "16"}]))
    assert not res.ok and "steuersatz_unzulaessig" in res.hinweise


def test_reverse_charge_ohne_steuer() -> None:
    ok = pruefe_summen({"net_total": "2837", "tax_total": "0", "gross_total": "2837", "reverse_charge": True,
                        "lines": [{"net_amount": "2837", "tax_rate": "0"}]})
    assert ok.ok
    bad = pruefe_summen({"net_total": "100", "tax_total": "19", "gross_total": "119", "reverse_charge": True,
                         "lines": [{"net_amount": "100", "tax_rate": "19"}]})
    assert not bad.ok


def test_gutschrift_negativ() -> None:
    res = pruefe_summen({"net_total": "-46.50", "tax_total": "-3.26", "gross_total": "-49.76",
                         "lines": [{"net_amount": "-46.50", "tax_rate": "7"}]})
    assert res.ok


def test_unvollstaendig() -> None:
    assert not pruefe_summen({"net_total": None}).ok


def test_kontenliste() -> None:
    konten = dict(load_accounts("SKR03"))
    for nr in ("3120", "3300", "3400", "3425", "4240", "4930"):
        assert nr in konten


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("4910", "4910"), ("4910 Porto", "4910"), (" 3400 - Wareneingang", "3400"), (4910, "4910"),
     ("9999", None), ("Porto", None), (None, None), ("", None)],
)
def test_kontonummer_bereinigen(raw: object, expected: str | None) -> None:
    from app.kontierung.konten import normalize_account

    assert normalize_account(raw, {"3400", "4910"}) == expected


def test_positionen_bereinigen_zaehlt_verworfene() -> None:
    from app.kontierung.konten import normalize_lines

    data: dict[str, object] = {"lines": [{"account_skr03": "4910 Porto"}, {"account_skr03": "1234"}, {"account_skr03": None}]}
    assert normalize_lines(data, {"4910"}) == 1
    assert [ln["account_skr03"] for ln in data["lines"]] == ["4910", None, None]  # type: ignore[union-attr]
