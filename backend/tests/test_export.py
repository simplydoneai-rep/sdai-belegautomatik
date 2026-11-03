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
    f = datev._felder(zeilen[2])
    assert len(f) == 124 and f[:14] == ["1234,50", "H", "", "", "", "", "70001", "3400", "", "2111", "R-2026-11-0418", "",
                                        "", 'Gasthaus "Zur Linde"']
    assert datev._felder(zeilen[3])[8] == "9" and zeilen[-1] == ""
    assert "Gegenkonto (ohne BU-Schlüssel)".encode("cp1252") in daten


def test_zusatzfelder_fremdwaehrung_leistungsdatum_ustid() -> None:
    zeile = {**ZEILE, "waehrung": "USD", "kurs": "1.0812", "leistungsdatum": "2026-11-30", "eu_ustid": "NL 999999042B01",
             "beleginfo": ("Beleg-ID", "F19 · SHA-256 abc"), "beleglink": 'BEDI "0a1b2c"'}
    daten = datev.buchungsstapel(KOPF, [zeile])
    assert datev.pruefe(daten) == []
    f = datev._felder(daten.decode("cp1252").split("\r\n")[2])
    assert (f[2], f[3]) == ("USD", "1,081200")                     # Spalte 3 und 4: Währung, Kurs (Mengennotierung)
    assert f[19] == 'BEDI "0a1b2c"' and (f[20], f[21]) == ("Beleg-ID", "F19 · SHA-256 abc")  # Spalte 20–22
    assert f[114] == "30112026" and f[122] == "NL999999042B01"     # Spalte 115 Leistungsdatum, 123 USt-IdNr. Ursprung
    ohne_kurs = datev.buchungsstapel(KOPF, [{**zeile, "kurs": "0"}]).replace(b"0,000000", b"")
    assert any("Kurs" in x for x in datev.pruefe(ohne_kurs))


def test_waehrung() -> None:
    from decimal import Decimal

    from app.kontierung import waehrung

    kopf = {"currency": "USD", "gross_total": "216.00", "invoice_date": "2026-11-02",
            "leistung": {"von": "2026-11-01", "bis": "2026-11-30"}}
    k = waehrung.kurs_fuer(kopf, None)
    assert k is not None and k["monat"] == "2026-11" and k["wert"] is None  # Tabelle ohne Novemberkurs: offen
    k = waehrung.kurs_fuer(kopf, "1.080000")
    assert k is not None and (k["wert"], k["quelle"], k["brutto_eur"]) == ("1.080000", "von Hand", "200.00")
    assert waehrung.kurs_fuer({**kopf, "currency": "EUR"}, None) is None
    assert waehrung.kurs_pruefen("1,0812") == Decimal("1.081200")
    with pytest.raises(ValueError):
        waehrung.kurs_pruefen("0")


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
    zeilen = r["daten"].decode("cp1252").split("\r\n")
    assert len(zeilen) - 3 >= r["export"]["anzahl"] and zeilen[0].split(";")[12] == "20260101"
    assert all(datev._felder(z)[20] == "Beleg-ID" and "SHA-256" in datev._felder(z)[21] for z in zeilen[2:-1])
    with pytest.raises(ValueError, match="exportiert"):
        ansicht.wiedereroeffnen(r["export"]["belege"][0])
    nachher = ansicht.export_vorschau(mandant, "2026-10")
    assert not nachher["moeglich"] and nachher["exporte"][0]["id"] == r["export"]["id"]
    with pytest.raises(ValueError, match="nicht möglich"):
        ansicht.exportieren(mandant, "2026-10")


@pytest.mark.skipif(not (TESTDATEN / "folgemonat" / "gold").exists(), reason="Belege November fehlen")
def test_kurs_am_beleg_und_wirtschaftsjahr(leer) -> None:  # type: ignore[no-untyped-def]
    from app.demo import ansicht, kanzlei

    ansicht.demo_november()
    fremd = next(e for e in ansicht.liste("M4")["eintraege"] if e.get("waehrung") == "USD")
    a = ansicht.ansicht(fremd["key"])
    assert a["kurs"]["wert"] is None and "Umrechnungskurs fehlt" in a["offen"] and not a["freigabe_moeglich"]
    a = ansicht.kurs_setzen(fremd["key"], "1,08")
    assert a["kurs"]["wert"] == "1.080000" and "Umrechnungskurs fehlt" not in a["offen"]
    assert all(z["kurs"] == "1.080000" for z in a["buchungen"]["stapel"])
    assert ansicht.kurs_setzen(fremd["key"], None)["kurs"]["wert"] is None
    with pytest.raises(ValueError, match="Euro"):
        euro = next(e for e in ansicht.liste("M4")["eintraege"] if e.get("waehrung") == "EUR" and e["bereich"] != "erledigt")
        ansicht.kurs_setzen(euro["key"], "1,1")
    # abweichendes Wirtschaftsjahr ab Juli: Oktober 2026 gehört zum Wirtschaftsjahr ab 01.07.2026
    m = kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M4"), "wj_beginn": 7})
    assert kanzlei.mandant(m["id"])["wj_beginn"] == 7
    with pytest.raises(ValueError, match="Monat 1–12"):
        kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M4"), "wj_beginn": 13})
