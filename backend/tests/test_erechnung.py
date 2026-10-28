from pathlib import Path

import pytest

from app.erechnung.parser import ERechnungFehler, parse_file, sum_check, without_parties

KOSIT = Path(__file__).resolve().parents[2] / "testdaten" / "kosit"
UBL_FILES = sorted(KOSIT.glob("*_ubl.xml"))


@pytest.mark.parametrize("ubl", UBL_FILES, ids=lambda p: p.name[:6])
def test_ubl_und_cii_liefern_dasselbe(ubl: Path) -> None:
    """KoSIT liefert jeden Fall als UBL und CII; beide Parser müssen dasselbe Ergebnis liefern."""
    cii = ubl.with_name(ubl.name.replace("_ubl", "_uncefact"))
    a, b = without_parties(parse_file(ubl)), without_parties(parse_file(cii))
    for key in ("document_type", "invoice_number", "invoice_date", "currency", "reverse_charge"):
        assert a[key] == b[key], key
    for key in ("net_total", "tax_total", "gross_total"):
        assert float(a[key]) == float(b[key]), key  # nur Vergleich, keine Rechnung
    assert len(a["lines"]) == len(b["lines"])
    assert [ln["tax_rate"] for ln in a["lines"]] == [ln["tax_rate"] for ln in b["lines"]]
    assert sum_check(a)


def test_beispiel_01_01() -> None:
    d = parse_file(KOSIT / "01.01a-INVOICE_ubl.xml")
    assert d["invoice_number"] == "123456XX"
    assert d["invoice_date"] == "2016-04-04"
    assert (d["net_total"], d["tax_total"], d["gross_total"]) == ("314.86", "22.04", "336.9")
    assert {ln["tax_rate"] for ln in d["lines"]} == {"7"}


def test_reverse_charge_ae() -> None:
    d = parse_file(KOSIT / "01.21a-INVOICE_ubl.xml")
    assert d["reverse_charge"] is True and d["tax_total"] in ("0", "0.00")


def test_unbekanntes_format(tmp_path: Path) -> None:
    f = tmp_path / "x.xml"
    f.write_text("<Foo/>", encoding="utf-8")
    with pytest.raises(ERechnungFehler):
        parse_file(f)


def test_keine_externen_entitaeten(tmp_path: Path) -> None:
    f = tmp_path / "xxe.xml"
    secret = tmp_path / "geheim.txt"
    secret.write_text("GEHEIM", encoding="utf-8")
    f.write_text(
        f'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///{secret.as_posix()}">]>'
        '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
        'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "<cbc:ID>&x;</cbc:ID></Invoice>",
        encoding="utf-8",
    )
    d = parse_file(f)
    assert "GEHEIM" not in str(d["invoice_number"])
