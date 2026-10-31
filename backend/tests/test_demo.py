"""Demo: Ampel und Ablauf ohne KI-Kosten (Aufzeichnungen bzw. regelbasiert)."""

import pytest

from app.demo import verarbeitung as demo
from app.demo.verarbeitung import TESTDATEN, _ampel_position, gesamtampel, verarbeite


def test_gesamtampel() -> None:
    gruen = [{"ampel": "gruen"}]
    assert gesamtampel(True, gruen, "ki") == "gruen"
    assert gesamtampel(False, gruen, "ki") == "rot"
    assert gesamtampel(True, [], "ki") == "gelb"
    assert gesamtampel(True, gruen, "regelbasiert") == "gelb"
    assert gesamtampel(True, [{"ampel": "gelb"}], "ki") == "gelb"


def test_position_konto_passt_nicht_zum_satz() -> None:
    ampel, hinweise = _ampel_position({"account_skr03": "3300", "net_amount": "10.00", "tax_rate": "19"}, "ki", False)
    assert ampel == "gelb" and "3300" in hinweise[0]
    assert _ampel_position({"account_skr03": "3400", "net_amount": "10.00", "tax_rate": "19"}, "ki", False)[0] == "gruen"
    assert _ampel_position({"account_skr03": None, "net_amount": "10.00", "tax_rate": "19"}, "ki", False)[0] == "rot"


@pytest.mark.skipif(not (TESTDATEN / "demo" / "aufzeichnungen.json").exists(), reason="Aufzeichnungen fehlen")
def test_demo_spielt_aufzeichnung_ab_und_pseudonymisiert() -> None:
    beleg = next(b for b in demo.testbelege() if b["id"] == "S02")
    result = verarbeite(TESTDATEN / beleg["datei"], beleg["client_id"], "ionos_qwen", beleg["erwartet"])
    assert result["quelle"] == "ki" and result["ki"]["art"] == "aufzeichnung"
    assert result["soll"]["pflichtfelder"] == [9, 9]
    assert "Sonnenblick" not in result["pseudonymisiert"] and "[MANDANT_1]" in result["pseudonymisiert"]


def test_e_rechnung_ohne_ki() -> None:
    beleg = next(b for b in demo.testbelege() if b["datei"].endswith("01.01a-INVOICE_ubl.xml"))
    result = verarbeite(TESTDATEN / beleg["datei"], beleg["client_id"], "ionos_qwen", beleg["erwartet"])
    assert result["quelle"] == "e-rechnung" and result["pseudonymisiert"] == ""
