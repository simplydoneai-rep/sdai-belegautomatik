"""Mandanten, Sachbearbeiter und Rechte der Demo (Sachbearbeiter sehen nur zugeordnete Mandanten)."""

import json

import pytest

from app.demo import kanzlei, zustand


@pytest.fixture()
def leer(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(zustand, "ZUSTAND", tmp_path / "zustand.json")
    monkeypatch.setattr(kanzlei, "DATEI", tmp_path / "kanzlei.json")
    return kanzlei


def test_startbelegung_und_sichtbarkeit(leer) -> None:  # type: ignore[no-untyped-def]
    assert kanzlei.ist_leitung("AK") and len(kanzlei.sichtbare_mandanten("AK")) == 6
    sl = {m["id"] for m in kanzlei.sichtbare_mandanten("SL")}
    assert sl == {"M1", "M2", "M5"}  # zuständig oder Vertretung
    assert not kanzlei.darf("SL", "M4") and not kanzlei.darf("XX", "M1")


def test_mandant_erfassen_und_pruefen(leer) -> None:  # type: ignore[no-untyped-def]
    neu = kanzlei.mandant_speichern("AK", {"name": "Physio Wellenreiter GmbH", "nummer": "10007", "kontenrahmen": "SKR04",
                                           "ansprechpartner": "Jana Ufer", "zustaendig": "TW", "vertretung": "MB"})
    assert neu["id"] == "M7" and [p["kuerzel"] for p in neu["team"]] == ["TW", "MB"]
    assert kanzlei.darf("TW", "M7") and kanzlei.darf("MB", "M7")
    with pytest.raises(ValueError, match="schon an"):
        kanzlei.mandant_speichern("AK", {"name": "X", "nummer": 10001, "kontenrahmen": "SKR03", "zustaendig": "TW"})
    with pytest.raises(ValueError, match="SKR03 oder SKR04"):
        kanzlei.mandant_speichern("AK", {"name": "X", "nummer": 20000, "kontenrahmen": "SKR99", "zustaendig": "TW"})
    with pytest.raises(ValueError, match="gesperrt"):  # Sophie Lang ist für Pixelwerk Design gesperrt
        kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M4"), "zustaendig": "SL"})
    with pytest.raises(PermissionError):
        kanzlei.mandant_speichern("MB", {"name": "X", "nummer": 20001, "kontenrahmen": "SKR03", "zustaendig": "MB"})
    felder = [e["feld"] for e in zustand.protokoll()]
    assert "Mandant 10007" in felder


def test_zugriff_und_sperre(leer) -> None:  # type: ignore[no-untyped-def]
    kanzlei.sachbearbeiter_speichern("AK", "jn", "Jonas Neu", "sachbearbeitung")
    assert not kanzlei.darf("JN", "M3")
    kanzlei.zugriff_setzen("AK", "JN", "M3", "an")
    assert kanzlei.darf("JN", "M3")
    kanzlei.zugriff_setzen("AK", "JN", "M3", "gesperrt")
    assert not kanzlei.darf("JN", "M3")
    with pytest.raises(ValueError, match="zuständig"):  # ohne Zustimmung keine Änderung der Zuständigkeit
        kanzlei.zugriff_setzen("AK", "MB", "M1", "aus")
    with pytest.raises(ValueError, match="Kanzleileitung"):
        kanzlei.sachbearbeiter_speichern("AK", "AK", "Anna Keller", "sachbearbeitung")


def test_beraternummern(leer) -> None:  # type: ignore[no-untyped-def]
    """Eine Kanzlei kann mehrere Beraternummern haben; Mandantennummern sind je Beraternummer eindeutig."""
    assert kanzlei.beraternummer("M1") == 29098 and kanzlei.stammdaten("AK")["kanzlei"]["standard"] == 29098
    k = kanzlei.beraternummer_speichern("AK", "45110", "Zweigstelle Erlangen")
    assert [b["nr"] for b in k["beraternummern"]] == [29098, 45110] and k["standard"] == 29098
    # dieselbe Mandantennummer unter anderer Beraternummer ist erlaubt, unter derselben nicht
    neu = kanzlei.mandant_speichern("AK", {"name": "Zahnarzt Dr. Weiß", "beraternummer": 45110, "nummer": 10001,
                                           "kontenrahmen": "SKR03", "zustaendig": "MB"})
    assert kanzlei.beraternummer(neu["id"]) == 45110
    with pytest.raises(ValueError, match="unter Beraternummer 29098 schon an"):
        kanzlei.mandant_speichern("AK", {"name": "X", "nummer": 10001, "kontenrahmen": "SKR03", "zustaendig": "MB"})
    with pytest.raises(ValueError, match="nicht angelegt"):
        kanzlei.mandant_speichern("AK", {"name": "X", "beraternummer": 77777, "nummer": 30000, "kontenrahmen": "SKR03",
                                         "zustaendig": "MB"})
    # ohne Angabe gilt der Standard; ein neuer Standard gilt nur für neue Mandanten
    ohne = kanzlei.mandant_speichern("AK", {"name": "Y", "nummer": 30001, "kontenrahmen": "SKR03", "zustaendig": "MB"})
    assert kanzlei.beraternummer(ohne["id"]) == 29098
    kanzlei.beraternummer_speichern("AK", 45110, "Zweigstelle Erlangen", standard=True)
    nach = kanzlei.mandant_speichern("AK", {"name": "Z", "nummer": 30002, "kontenrahmen": "SKR03", "zustaendig": "MB"})
    assert kanzlei.beraternummer(nach["id"]) == 45110 and kanzlei.beraternummer("M1") == 29098
    with pytest.raises(ValueError, match="zwischen 1001 und 9999999"):
        kanzlei.beraternummer_speichern("AK", 999, "zu kurz")
    with pytest.raises(ValueError, match="noch .* Mandanten"):
        kanzlei.beraternummer_entfernen("AK", 29098)
    with pytest.raises(ValueError, match="Standard"):
        kanzlei.beraternummer_entfernen("AK", 45110)
    with pytest.raises(PermissionError):
        kanzlei.beraternummer_speichern("MB", 50000, "nicht erlaubt")
    kanzlei.beraternummer_speichern("AK", 60000, "Alt")
    assert 60000 not in [b["nr"] for b in kanzlei.beraternummer_entfernen("AK", 60000)["beraternummern"]]
    felder = [e["feld"] for e in zustand.protokoll()]
    assert "Beraternummer 45110" in felder and "Standard-Beraternummer" in felder


def test_alte_stammdaten_bekommen_beraternummer(leer) -> None:  # type: ignore[no-untyped-def]
    alt = kanzlei._start()
    del alt["kanzlei"]
    for m in alt["mandanten"].values():
        del m["beraternummer"]
    kanzlei.DATEI.write_text(json.dumps(alt), encoding="utf-8")
    assert kanzlei.beraternummer("M3") == 29098
    assert kanzlei.stammdaten("AK")["kanzlei"]["beraternummern"][0]["mandanten"] == 6


def test_zugriff_entziehen_passt_zustaendigkeit_an(leer) -> None:  # type: ignore[no-untyped-def]
    """Sophie Lang ist bei Bäckerei Kornfeld (M5) zuständig, Markus Bauer Vertretung."""
    kanzlei.zugriff_setzen("AK", "SL", "M5", "aus", zustaendigkeit_anpassen=True)
    m = kanzlei.mandant("M5")
    assert (m["zustaendig"], m["vertretung"]) == ("MB", None) and not kanzlei.darf("SL", "M5")
    # Vertretung: entfällt, Zuständigkeit bleibt
    kanzlei.zugriff_setzen("AK", "TW", "M2", "gesperrt", zustaendigkeit_anpassen=True)
    assert (kanzlei.mandant("M2")["zustaendig"], kanzlei.mandant("M2")["vertretung"]) == ("SL", None)
    assert kanzlei.sachbearbeiter("TW")["zugriff"]["M2"] == "gesperrt"
    # einzige zuständige Person (M6: nur Tim Wagner): erst andere Person eintragen
    with pytest.raises(ValueError, match="einzige zuständige Person"):
        kanzlei.zugriff_setzen("AK", "TW", "M6", "aus", zustaendigkeit_anpassen=True)
    assert "Mandant 10005" in [e["feld"] for e in zustand.protokoll()]


def test_sachkontenlaenge(leer) -> None:  # type: ignore[no-untyped-def]
    assert kanzlei.sachkontenlaenge("M1") == 4
    m = kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M3"), "sachkontenlaenge": 5})
    assert kanzlei.sachkontenlaenge(m["id"]) == 5 and zustand.kreditor_bereich(5) == (700000, 999999)
    with pytest.raises(ValueError, match="4 bis 8"):
        kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M3"), "sachkontenlaenge": 9})
    zustand.kreditor_anlegen("M3", 700000, "Holzhandel Waldmark GmbH", None, 5)
    with pytest.raises(ValueError, match="nicht mehr ändern"):  # Kreditoren haben schon die bisherige Länge
        kanzlei.mandant_speichern("AK", {**kanzlei.mandant("M3"), "sachkontenlaenge": 4})
