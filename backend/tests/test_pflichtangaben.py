"""Pflichtangaben nach § 14 UStG, §§ 31, 33 UStDV, § 14a UStG."""

from app.kontierung.pflichtangaben import pruefe

MANDANT = {"name": "Café Sonnenblick GmbH", "postcode": "90402", "vat_id": "DE999100001"}
TEXT = """Frischgut Großhandel GmbH
Hafenstraße 21 · 90451 Nürnberg
Café Sonnenblick GmbH
Lindenallee 12
90402 Nürnberg
USt-IdNr.: DE999200001
Rechnungsnummer: FG-1  Datum: 04.11.2026  Leistungsdatum: 04.11.2026
Umsatzsteuer 7 % auf 100,00 €   7,00 €
Bei Zahlung innerhalb von 7 Tagen 2 % Skonto."""
KOPF = {"supplier_name": "Frischgut Großhandel GmbH", "invoice_number": "FG-1", "invoice_date": "2026-11-04",
        "net_total": "100.00", "tax_total": "7.00", "gross_total": "307.00", "lieferant_ustid": "DE999200001",
        "leistung": {"von": "2026-11-04", "bis": None}, "steuerfall": "inland"}
POS = [{"description": "Vollmilch", "quantity": "10", "unit": "l", "tax_rate": "7"}]


def status(ergebnis: dict, key: str) -> str:  # type: ignore[type-arg]
    return next(p["status"] for p in ergebnis["punkte"] if p["key"] == key)


def test_vollstaendige_rechnung() -> None:
    e = pruefe(KOPF, POS, TEXT, MANDANT, None, None, True)
    assert e["art"] == "voll" and e["fehlt"] == []
    assert next(p["detail"] for p in e["punkte"] if p["key"] == "entgelt") == "Skonto angegeben"


def test_fehlende_angaben() -> None:
    kopf = {**KOPF, "invoice_number": None, "leistung": None}
    e = pruefe(kopf, POS, TEXT.replace("Café Sonnenblick GmbH", "Café XY"), MANDANT, None, None, True)
    assert status(e, "nummer") == status(e, "leistungszeit") == status(e, "empfaenger") == "fehlt"


def test_kleinbetrag_braucht_weniger() -> None:
    kopf = {**KOPF, "gross_total": "107.00", "invoice_number": None, "leistung": None, "lieferant_ustid": None}
    e = pruefe(kopf, POS, "Bäckerei Ofen\n90763 Fürth\nSumme 107,00 €", MANDANT, None, None, True)
    assert e["art"] == "kleinbetrag" and e["fehlt"] == []
    assert status(e, "nummer") == status(e, "empfaenger") == "entfaellt"


def test_reverse_charge_nur_hinweise() -> None:
    kopf = {**KOPF, "steuerfall": "13b", "tax_total": "0", "lieferant_ustid": None}
    pos = [{**POS[0], "tax_rate": "0"}]
    e = pruefe(kopf, pos, "PixelCloud Inc.\n500 Market Street\nSan Francisco, CA 94105\nCafé Sonnenblick GmbH 90402",
               MANDANT, None, None, True)
    assert status(e, "steuernummer") == "hinweis" and status(e, "hinweis_13b") == "hinweis" and e["fehlt"] == []


def test_e_rechnung_aus_strukturierten_daten() -> None:
    verkaeufer = {"name": "Lieferant AG", "city": "Berlin", "postcode": "10115"}
    kaeufer = {"name": "Musterverwaltung", "city": "Bamberg"}
    e = pruefe(KOPF, POS, "<xml/>", MANDANT, verkaeufer, kaeufer, True)
    assert e["e_rechnung"] and status(e, "leistender") == status(e, "empfaenger") == "ok"
