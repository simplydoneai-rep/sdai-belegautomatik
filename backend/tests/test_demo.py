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


@pytest.fixture()
def leerer_zustand(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    from app.demo import zustand

    monkeypatch.setattr(zustand, "ZUSTAND", tmp_path / "zustand.json")
    return zustand


@pytest.mark.skipif(not (TESTDATEN / "demo" / "aufzeichnungen.json").exists(), reason="Aufzeichnungen fehlen")
def test_rechnungseingang_ablauf(leerer_zustand) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht

    key = next(b["key"] for b in ansicht.eingang() if b["id"] == "S02")
    a = ansicht.ansicht(key)
    assert a["kreditor"] is None and a["kreditor_vorschlag"]["nr"] == 70000
    assert not a["freigabe_moeglich"] and "Kreditor anlegen" in a["offen"]
    assert all(p["ampel"] == "gruen" for p in a["positionen"])  # 5 von 5 Modellen einig

    with pytest.raises(ValueError):
        ansicht.kreditor_anlegen(key, 69999, "Getränke Hanse")  # außerhalb 70000–99999
    a = ansicht.kreditor_anlegen(key, 70000, "Getränke Hanse")
    assert a["kreditor"]["nr"] == "70000" and a["freigabe_moeglich"]
    with pytest.raises(ValueError):
        ansicht.kreditor_anlegen(key, 70000, "Anderer Lieferant")  # Nummer doppelt

    a = ansicht.konto_waehlen(key, 2, "3400")  # 19-%-Konto für 7-%-Position
    assert a["positionen"][2]["ampel"] == "gelb" and "passt nicht" in a["positionen"][2]["grund"]
    a = ansicht.konto_waehlen(key, 2, "3300")
    assert a["positionen"][2]["ampel"] == "gruen" and a["positionen"][2]["grund"] == "Von Ihnen bestätigt"
    with pytest.raises(ValueError):
        ansicht.konto_waehlen(key, 0, "1234")  # gibt es im SKR03 nicht

    a = ansicht.freigeben(key)
    assert a["status"] == "freigegeben"
    felder = [e["feld"] for e in leerer_zustand.protokoll(key)]
    assert "Status" in felder and any("Sachkonto" in f for f in felder)

    # Nächster Beleg: nächste freie Kreditorennummer
    key2 = next(b["key"] for b in ansicht.eingang() if b["id"] == "S01")
    assert ansicht.ansicht(key2)["kreditor_vorschlag"]["nr"] == 70001


def test_kontensuche() -> None:
    from app.kontierung.kontensuche import suchen

    assert [k["nr"] for k in suchen("War")][:2] == ["3200", "3300"]
    assert "3400" in [k["nr"] for k in suchen("War")]
    assert suchen("34")[0]["nr"] == "3400"
    assert suchen("kfz rep")[0]["nr"] == "4540"
    assert suchen("") == []


def test_skr03_2026_ohne_4610() -> None:
    from app.kontierung.konten import umschluesseln
    from app.kontierung.kontensuche import konto

    assert konto("4610") is None and konto("4600")["name"] == "Werbekosten"
    assert umschluesseln("4610") == "4600"


@pytest.mark.skipif(not (TESTDATEN / "folgemonat" / "gold").exists(), reason="Belege November fehlen")
def test_folgemonat_ist_vorkontiert_und_bleibt_kontrollierbar(leerer_zustand) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht

    ansicht.demo_oktober()
    ansicht.demo_november()
    eingang = {b["id"]: b["key"] for b in ansicht.eingang()}

    sicher = ansicht.ansicht(eingang["F10"])  # Reinigung: im Oktober gebucht
    assert sicher["bereich"] == "sicher" and all(p["quelle"] == "regel" for p in sicher["positionen"])
    for fall in ("F04", "F14", "F15", "F16", "F17"):  # neue Position, Gutschrift, § 13b, neuer Lieferant, hoher Betrag
        assert ansicht.ansicht(eingang[fall])["bereich"] == "pruefen", fall

    # Regel abschalten: Beleg geht zur Prüfung, Grund wird genannt
    regel = sicher["positionen"][0]["regel"]["id"]
    a = ansicht.regel_aktiv(eingang["F10"], regel, False)
    assert a["bereich"] == "pruefen" and "abgeschaltet" in a["positionen"][0]["grund"]
    assert ansicht.regel_aktiv(eingang["F10"], regel, True)["bereich"] == "sicher"

    # Sammelfreigabe nur für sichere Belege; Wieder öffnen nimmt das Gelernte zurück
    r = ansicht.sammelfreigabe([eingang["F10"], eingang["F16"]])
    assert r["freigegeben"] == [eingang["F10"]] and [u["key"] for u in r["uebersprungen"]] == [eingang["F16"]]
    assert ansicht.ansicht(eingang["F10"])["positionen"][0]["regel"]["bestaetigungen"] == 2
    a = ansicht.wiedereroeffnen(eingang["F10"])
    assert a["bereich"] == "sicher" and a["positionen"][0]["regel"]["bestaetigungen"] == 1
