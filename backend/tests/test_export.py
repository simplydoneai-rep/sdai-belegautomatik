"""DATEV-Buchungsstapel, Prüfskript, Entfernen von Belegen und Exportstapel."""

from datetime import date, datetime

import pytest

from app.demo.verarbeitung import TESTDATEN
from app.export import datev

KOPF = datev.Kopf(beraternummer=29098, mandantennummer=10004, wj_beginn=date(2026, 1, 1), sachkontenlaenge=4,
                  datum_von=date(2026, 11, 1), datum_bis=date(2026, 11, 30), bezeichnung="Eingangsrechnungen 11/2026",
                  kontenrahmen="SKR03", erzeugt=datetime(2026, 11, 3, 15, 30, 12, 345000))
ZEILE = {"umsatz": "1234.5", "soll_haben": "H", "waehrung": "EUR", "konto": "70001", "gegenkonto": "3400", "bu": "",
         "belegdatum": "2026-11-21", "belegfeld1": "R-2026-11-0418", "buchungstext": 'Gasthaus "Zur Linde"'}


def test_buchungsstapel_aufbau() -> None:
    daten = datev.buchungsstapel(KOPF, [ZEILE, {**ZEILE, "bu": "9", "gegenkonto": "4650", "umsatz": "16.38"}])
    assert datev.pruefe(daten) == []
    zeilen = daten.decode("cp1252").split("\r\n")
    kopf = zeilen[0].split(";")
    assert kopf[:6] == ['"EXTF"', "700", "21", '"Buchungsstapel"', "13", "20261103153012345"]
    assert (kopf[10], kopf[11], kopf[12], kopf[13], kopf[14], kopf[15]) == ("29098", "10004", "20260101", "4", "20261101", "20261130")
    assert len(kopf) == 31 and kopf[26] == '"03"' and kopf[20] == "0"
    assert zeilen[2] == '1234,50;"H";"";;;;70001;3400;"";2111;"R-2026-11-0418";;;"Gasthaus ""Zur Linde"""'
    assert zeilen[3].split(";")[8] == '"9"' and zeilen[-1] == ""
    assert "Gegenkonto (ohne BU-Schlüssel)".encode("cp1252") in daten


def test_pruefskript_findet_fehler() -> None:
    falsch = datev.buchungsstapel(KOPF, [{**ZEILE, "umsatz": "0", "soll_haben": "X", "gegenkonto": "34000"}])
    fehler = " ".join(datev.pruefe(falsch))
    assert "Umsatz" in fehler and "Soll/Haben" in fehler and "Gegenkonto" in fehler
    assert datev.pruefe(b"EXTF;700\n") and datev.pruefe(falsch.replace(b"\r\n", b"\n"))


@pytest.fixture()
def leer(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    from app.demo import kanzlei, zustand

    monkeypatch.setattr(zustand, "ZUSTAND", tmp_path / "zustand.json")
    monkeypatch.setattr(zustand, "EXPORTE", tmp_path / "exporte")
    monkeypatch.setattr(kanzlei, "DATEI", tmp_path / "kanzlei.json")
    return zustand


@pytest.mark.skipif(not (TESTDATEN / "folgemonat" / "gold").exists(), reason="Belege November fehlen")
def test_entfernen_und_export(leer) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht

    ansicht.demo_oktober()
    ansicht.demo_november()
    mandant = "M4"
    v = ansicht.export_vorschau(mandant)
    assert v["monat"] == "2026-10" and v["moeglich"] and v["anzahl"] > 0  # Oktober ist komplett gebucht
    nov = ansicht.export_vorschau(mandant, "2026-11")
    assert not nov["moeglich"] and "noch offen" in nov["grund"] or not nov["belege"]

    # Entfernen: nur offene Belege, Grund Pflicht, wiederherstellbar; zählt nicht mehr als offen
    offen = [e for e in ansicht.liste(mandant)["eintraege"] if e["bereich"] in ("sicher", "pruefen")]
    key = offen[0]["key"]
    with pytest.raises(ValueError, match="Grund"):
        ansicht.entfernen(key, "weil")
    a = ansicht.entfernen(key, "Doppelt eingegangen")
    assert a["bereich"] == "entfernt" and not a["freigabe_moeglich"] and a["entfernt"]["grund"] == "Doppelt eingegangen"
    assert all(e["key"] != key for e in ansicht.liste(mandant)["eintraege"] if e["bereich"] in ("sicher", "pruefen"))
    assert ansicht.wiederherstellen(key)["bereich"] in ("sicher", "pruefen")

    # Export Oktober: Datei geprüft, gespeichert mit Hash, Belege exportiert und nicht mehr zu öffnen
    r = ansicht.exportieren(mandant, "2026-10")
    assert datev.pruefe(r["daten"]) == [] and r["datei"].startswith("EXTF_Buchungsstapel_29098_10004_202610_")
    assert (leer.EXPORTE / r["datei"]).read_bytes() == r["daten"] and len(r["export"]["sha256"]) == 64
    assert len(r["daten"].decode("cp1252").split("\r\n")) - 3 >= r["export"]["anzahl"]
    with pytest.raises(ValueError, match="exportiert"):
        ansicht.wiedereroeffnen(r["export"]["belege"][0])
    nachher = ansicht.export_vorschau(mandant, "2026-10")
    assert not nachher["moeglich"] and nachher["exporte"][0]["id"] == r["export"]["id"]
    with pytest.raises(ValueError, match="nicht möglich"):
        ansicht.exportieren(mandant, "2026-10")
