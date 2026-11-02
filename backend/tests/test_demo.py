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
    from app.demo import kanzlei, zustand

    monkeypatch.setattr(zustand, "ZUSTAND", tmp_path / "zustand.json")
    monkeypatch.setattr(kanzlei, "DATEI", tmp_path / "kanzlei.json")
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
    # Steuerschlüssel: Reinigung ohne Automatik → BU 9; US-Software (Dollar) → § 13b, BU 94, netto
    assert sicher["positionen"][0]["steuer"]["bu"] == "9"
    # DATEV-Stapel: Konto = Kreditor im Haben, Gegenkonto = Sachkonto mit BU; Buchungssatz mit Vorsteuer 1576
    zeile = sicher["buchungen"]["stapel"][0]
    assert (zeile["konto"], zeile["soll_haben"], zeile["gegenkonto"], zeile["bu"], zeile["umsatz"]) == \
        (sicher["kreditor"]["nr"], "H", "4250", "9", "809.20")
    satz = {(z["seite"], z["konto"]): z["betrag"] for z in sicher["buchungen"]["satz"]}
    assert satz == {("Soll", "4250"): "680.00", ("Soll", "1576"): "129.20", ("Haben", sicher["kreditor"]["nr"]): "809.20"}
    assert sicher["buchungen"]["ausgeglichen"] and not sicher["pflichtangaben"]["fehlt"]
    usa = ansicht.ansicht(eingang["F18"])
    assert usa["kopf"]["currency"] == "USD" and usa["steuerfall"]["id"] == "13b"
    assert usa["positionen"][0]["steuer"]["bu"] == "94" and usa["buchungen"]["stapel"][0]["umsatz"] == "216.00"
    satz = {(z["seite"], z["konto"]): z["betrag"] for z in usa["buchungen"]["satz"]}
    assert satz[("Soll", "1577")] == satz[("Haben", "1787")] == "41.04"  # § 13b: Vorsteuer und Umsatzsteuer
    wien = ansicht.ansicht(eingang["F20"])  # ausländische USt (AT 20 %): brutto in den Aufwand, keine Vorsteuer
    assert wien["steuerfall"]["id"] == "ausland" and wien["buchungen"]["stapel"][0]["umsatz"] == "936.00"
    assert all(z["art"] != "vorsteuer" for z in wien["buchungen"]["satz"])
    assert any("Ausländische Umsatzsteuer" in a for a in wien["ausnahmen"])
    assert any("Fremdwährung" in a for a in usa["ausnahmen"])
    assert usa["kopf"]["leistung"] == {"von": "2026-11-01", "bis": "2026-11-30", "art": "beleg"}
    assert ansicht.ansicht(eingang["F19"])["steuerfall"]["id"] == "ige"

    r = ansicht.sammelfreigabe([eingang["F10"], eingang["F16"]])
    assert r["freigegeben"] == [eingang["F10"]] and [u["key"] for u in r["uebersprungen"]] == [eingang["F16"]]
    assert ansicht.ansicht(eingang["F10"])["positionen"][0]["regel"]["bestaetigungen"] == 2
    a = ansicht.wiedereroeffnen(eingang["F10"])
    assert a["bereich"] == "sicher" and a["positionen"][0]["regel"]["bestaetigungen"] == 1


@pytest.mark.skipif(not (TESTDATEN / "folgemonat" / "gold").exists(), reason="Belege November fehlen")
def test_bewirtung_aufteilung_und_manuelle_korrektur(leerer_zustand) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht

    ansicht.demo_november()
    key = {b["id"]: b["key"] for b in ansicht.eingang()}["F22"]
    a = ansicht.ansicht(key)
    # Bewirtung erkannt: 4650 mit 70/30-Aufteilung auf 4654, Speisen 7 %, Getränke 19 %, Vorsteuer voll
    assert all([t["konto"]["nr"] for t in p["teile"]] == ["4650", "4654"] for p in a["positionen"])
    satz = {(z["seite"], z["konto"]): z["betrag"] for z in a["buchungen"]["satz"]}
    assert satz[("Soll", "1571")] == "16.38" and satz[("Soll", "1576")] == "27.51" and a["buchungen"]["ausgeglichen"]
    assert any(x.startswith("Bewirtung") for x in a["ausnahmen"])
    # Korrekturen von Hand: Aufteilung, Steuersatz, Steuerschlüssel – die Steuerlogik prüft weiter
    a = ansicht.aufteilen(key, 0, [{"konto": "4650", "prozent": "80"}, {"konto": "4654", "prozent": "20"}])
    assert [t["netto"] for t in a["positionen"][0]["teile"]] == ["187.20", "46.80"]
    with pytest.raises(ValueError, match="nicht 100"):
        ansicht.aufteilen(key, 0, [{"konto": "4650", "prozent": "80"}, {"konto": "4654", "prozent": "30"}])
    a = ansicht.steuerschluessel_waehlen(key, 2, "8")
    assert a["positionen"][2]["ampel"] == "gelb" and "7 %" in a["positionen"][2]["grund"]
    a = ansicht.steuersatz_waehlen(key, 1, "7")
    assert a["positionen"][1]["teile"][0]["steuer"]["bu"] == "8" and a["positionen"][1]["satz_manuell"]
    a = ansicht.steuersatz_waehlen(key, 1, None)
    assert a["positionen"][1]["steuersatz"] == "19"


@pytest.mark.skipif(not (TESTDATEN / "folgemonat" / "gold").exists(), reason="Belege November fehlen")
def test_kreditor_mit_ustid_aus_der_rechnung(leerer_zustand) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht

    ansicht.demo_november()
    key = {b["id"]: b["key"] for b in ansicht.eingang()}["F19"]
    a = ansicht.kreditor_anlegen(key, 70000, "Gereedschap Groothandel B.V.")
    assert (a["kreditor"]["ustid"], a["kreditor"]["land"]) == ("NL999999042B01", "NL")
    assert a["buchungen"]["stapel"][0]["eu_ustid"] == "NL999999042B01"
    a = ansicht.kreditor_daten(key, "NL123456789B01", "NL")
    assert any("weicht vom Kreditor ab" in x for x in a["ausnahmen"])
    with pytest.raises(ValueError, match="passt nicht"):
        ansicht.kreditor_daten(key, "NL123456789B01", "BE")
