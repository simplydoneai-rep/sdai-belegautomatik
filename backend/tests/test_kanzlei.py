"""Mandanten, Sachbearbeiter und Rechte der Demo (Sachbearbeiter sehen nur zugeordnete Mandanten)."""

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
    with pytest.raises(ValueError, match="Zuständigkeit"):  # Zuständige können nicht ausgesperrt werden
        kanzlei.zugriff_setzen("AK", "MB", "M1", "aus")
    with pytest.raises(ValueError, match="Kanzleileitung"):
        kanzlei.sachbearbeiter_speichern("AK", "AK", "Anna Keller", "sachbearbeitung")
