"""XRechnung-Validierung mit den offiziellen KoSIT-Prüfregeln (Schema, EN 16931, XRechnung 3.0)."""

from pathlib import Path

import pytest

from app.erechnung.validierung import validiere, verfuegbar

TESTDATEN = Path(__file__).resolve().parents[2] / "testdaten"
pytestmark = pytest.mark.skipif(not verfuegbar(), reason="KoSIT-Prüfregeln nicht eingerichtet (scripts/kosit_einrichten.py)")


def test_gueltige_xrechnung_ubl_und_cii() -> None:
    for name in ("01.02a-INVOICE_ubl.xml", "01.02a-INVOICE_uncefact.xml"):
        r = validiere(TESTDATEN / "kosit" / name)
        assert r["gueltig"] is True and r["fehler"] == [], name
        assert "XRechnung" in r["szenario"] and "3.0.2" in r["regelwerk"]


def test_fehlerhafte_xrechnung() -> None:
    r = validiere(TESTDATEN / "folgemonat" / "F21_bueroversand.xml")
    assert r["gueltig"] is False
    assert {e["regel"] for e in r["fehler"]} == {"BR-CO-15", "BR-DE-15"}  # Brutto falsch, Käuferreferenz fehlt


def test_keine_xrechnung_3(tmp_path: Path) -> None:
    xml = (TESTDATEN / "kosit" / "01.02a-INVOICE_ubl.xml").read_text(encoding="utf-8")
    alt = xml.replace("urn:xeinkauf.de:kosit:xrechnung_3.0", "urn:xoev-de:kosit:standard:xrechnung_2.3")
    (tmp_path / "alt.xml").write_text(alt, encoding="utf-8")
    r = validiere(tmp_path / "alt.xml")
    assert r["gueltig"] is False and r["szenario"] is None and "xrechnung_2.3" in r["fehler"][0]["text"]


def test_klartext_fuer_sachbearbeiter() -> None:
    from app.erechnung.validierung import klartext

    assert klartext("BR-CO-15", "") == "Rechenfehler: Der Bruttobetrag ist nicht Netto + Umsatzsteuer."
    assert klartext("BR-DE-15", "") == "Die Käuferreferenz (Leitweg-ID) fehlt."
    assert klartext("BR-DEC-14", "[BR-DEC-14]-… Invoice total amount with VAT (BT-112) is 2.") == \
        "Zu viele Nachkommastellen: Gesamtbetrag brutto."
    assert klartext("UBL-CR-001", "irgendwas") == "Technischer Formfehler im Aufbau der E-Rechnung."
    assert klartext("BR-62", "The Seller electronic address (BT-34) shall have a Scheme identifier.") == \
        "Angabe fehlt oder ist unvollständig: Elektronische Adresse des Lieferanten."
    r = validiere(TESTDATEN / "folgemonat" / "F21_bueroversand.xml")
    assert all(e["klartext"] and "BR-" not in e["klartext"] for e in r["fehler"] + r["warnungen"])


def test_dtd_wird_abgelehnt(tmp_path: Path) -> None:
    boese = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///c:/windows/win.ini">]><x>&e;</x>'
    (tmp_path / "boese.xml").write_text(boese, encoding="utf-8")
    r = validiere(tmp_path / "boese.xml")
    assert r["gueltig"] is False and "nicht zulässig" in r["fehler"][0]["text"]
