"""DATEV-Steuerschlüssel, Steuerfall und Kopfangaben aus dem Belegtext (CLAUDE.md Regeln 15 und 16)."""

from decimal import Decimal

from app.kontierung.kontensuche import konto
from app.kontierung.steuerschluessel import automatik, bestimmen, herkunft_aus_ustid, steuerfall, steuerkonten
from app.ocr.kopfangaben import herkunft, leistungsdatum, lieferanten_ustid, waehrung

D = Decimal


def test_konten_ohne_automatik_bekommen_den_steuerschluessel() -> None:
    assert bestimmen(konto("4980"), D(19), "inland").bu == "9"  # Sonstiger Betriebsbedarf
    assert bestimmen(konto("4940"), D(7), "inland").bu == "8"  # Fachliteratur 7 %, nicht 7 (= 16 %)
    assert bestimmen(konto("4985"), D(0), "ige").bu == "19"  # i. g. Erwerb, Regelsatz
    assert bestimmen(konto("4964"), D(0), "13b").bu == "94"  # Leistung aus dem Ausland
    st = bestimmen(konto("4240"), D(0), "inland")
    assert st.bu == "" and st.text == "ohne Vorsteuer" and st.hinweis is None


def test_automatikkonten_ohne_schluessel_aber_mit_pruefung() -> None:
    st = bestimmen(konto("3400"), D(19), "inland")
    assert st.automatik and st.bu == "" and st.hinweis is None
    assert "passt nicht" in (bestimmen(konto("3400"), D(7), "inland").hinweis or "")
    assert "Automatikkonto für Inland" in (bestimmen(konto("3400"), D(0), "13b").hinweis or "")
    assert bestimmen(konto("3120"), D(0), "13b").hinweis is None  # Bauleistung § 13b
    assert bestimmen(konto("3425"), D(0), "ige").hinweis is None
    assert bestimmen(konto("3425"), D(0), "13b").hinweis  # i. g. Erwerb ist kein § 13b


def test_automatik_aus_der_kontenbezeichnung() -> None:
    assert automatik(konto("3070")).satz == D("5.5")  # type: ignore[arg-type,union-attr]
    assert automatik(konto("3725")).fall == "ige"  # type: ignore[arg-type,union-attr]
    assert automatik(konto("3553")).fall == "sonder"  # type: ignore[arg-type,union-attr]
    assert automatik(konto("4980")) is None  # type: ignore[arg-type]


def test_steuerfall() -> None:
    assert steuerfall(False, "inland", "", [D(19)]) == "inland"
    assert steuerfall(True, "inland", "§ 13b", [D(0)]) == "13b"
    assert steuerfall(True, "eu", "Steuerfreie innergemeinschaftliche Lieferung", [D(0)]) == "ige"
    assert steuerfall(False, "drittland", "", [D(0)]) == "13b"  # Hinweis fehlt, Ausland ohne Steuer
    assert herkunft_aus_ustid("ATU99916016") == "eu" and herkunft_aus_ustid("DE999200001") == "inland"
    assert steuerfall(False, "eu", "", [D(20)]) == "ausland"  # österreichische USt, kein Reverse Charge


def test_auslaendische_steuer_und_steuerkonten() -> None:
    st = bestimmen(konto("4945"), D(20), "ausland")
    assert st.bu == "" and st.hinweis is None
    assert bestimmen(konto("3400"), D(20), "ausland").hinweis  # Automatikkonto Inland passt nicht
    assert steuerkonten("inland", D(19)) == ("1576", None) and steuerkonten("inland", D(7)) == ("1571", None)
    assert steuerkonten("13b", D(19)) == ("1577", "1787") and steuerkonten("ige", D(19)) == ("1574", "1774")
    assert steuerkonten("inland", D(0)) == (None, None)


def test_leistungsdatum_in_allen_schreibweisen() -> None:
    assert leistungsdatum("Leistungsdatum: 03.11.2026", None) == {"von": "2026-11-03", "bis": None, "art": "beleg"}
    assert leistungsdatum("Leistungszeitraum 01.10.–31.10.2026", None)["bis"] == "2026-10-31"  # type: ignore[index]
    assert leistungsdatum("Leistungszeitraum: Oktober 2026", None)["von"] == "2026-10-01"  # type: ignore[index]
    assert leistungsdatum("Leistungszeitraum   26. Oktober 2026", None)["von"] == "2026-10-26"  # type: ignore[index]
    assert leistungsdatum("Service period   November 2, 2026", None)["von"] == "2026-11-02"  # type: ignore[index]
    wie = leistungsdatum("Liefer- und Leistungsdatum entspricht dem Rechnungsdatum", "2026-11-05")
    assert wie == {"von": "2026-11-05", "bis": None, "art": "wie_rechnung"}
    assert leistungsdatum("Rechnung vom 03.11.2026", "2026-11-03") is None


def test_waehrung_und_herkunft() -> None:
    assert waehrung("Summe 216,00 USD", "EUR") == "USD"
    assert waehrung("Summe 216,00 €", None) == "EUR"
    assert waehrung("", "chf") == "CHF"
    text = "USt-IdNr.: DE999100001 Kunde\nUSt-IdNr.: NL999999042B01"
    assert lieferanten_ustid(text, ("DE999100001",)) == "NL999999042B01"
    assert herkunft("500 Market Street · USA", None) == "drittland"
    assert herkunft("Hafenstraße 21", None) == "inland"
