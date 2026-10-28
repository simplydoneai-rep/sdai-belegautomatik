import json
from pathlib import Path

import pytest

from app.llm.placeholder import PlaceholderProvider
from app.pseudo.pseudonymizer import ClientProfile, PseudonymizedPayload, pseudonymize

ACCOUNTS = (("3400", "Wareneingang 19 % Vorsteuer"),)
CLIENT = ClientProfile(
    name_variants=("Bäckerei Kornfeld KG",),
    address_fragments=("Marktplatz 7", "91126 Schwabach"),
    person_names=("Jonas Kornfeld",),
    industry_code="10.71",
)


def run(text: str, vat: tuple[str, ...] = ()) -> tuple[str, dict[str, str]]:
    res = pseudonymize(text, CLIENT, ACCOUNTS, own_vat_ids=vat)
    return res.payload.text, res.mapping


def test_payload_nur_ueber_pseudonymize() -> None:
    with pytest.raises(TypeError):
        PseudonymizedPayload("roh", "10.71", "SKR03", ACCOUNTS)


def test_provider_lehnt_rohtext_ab() -> None:
    with pytest.raises(TypeError):
        PlaceholderProvider().extract("Rohtext mit IBAN")  # type: ignore[arg-type]


def test_mandant_anschrift_person_werden_ersetzt() -> None:
    text, mapping = run("Bäckerei Kornfeld KG\nz. Hd. Herrn Jonas Kornfeld\nMarktplatz 7\n91126 Schwabach")
    for value in ("Kornfeld", "Marktplatz", "Schwabach"):
        assert value not in text
    assert "[MANDANT_1]" in text and mapping["[MANDANT_1]"] == "Bäckerei Kornfeld KG"


def test_mandant_mit_ocr_fehler_wird_ersetzt() -> None:
    text, _ = run("Backerei Kornteld KG\nZ. Hd. Herm Jonas Kornfeld")
    assert "Kornteld" not in text and "[MANDANT_1]" in text


def test_iban_bic_email_steuernummer() -> None:
    text, mapping = run(
        "IBAN DE45 9999 9999 0005 0185 05 BIC TESTDEFFXXX\nE-Mail: info@beispiel-firma.de\n"
        "Steuernummer: 241/105/50065"
    )
    assert "9999" not in text and "TESTDEFF" not in text and "@" not in text and "241/105" not in text
    assert {"[IBAN_1]", "[BIC_1]", "[EMAIL_1]", "[STEUERNR_1]"} <= set(mapping)


@pytest.mark.parametrize("line", ["Tel. +49 911 4034 102", "Tel 0911 12345", "Tel.449   4289 117", "Fax: 0911/123456"])
def test_telefon_auch_ohne_plus(line: str) -> None:
    text, _ = run(line)
    assert "[TELEFON_1]" in text


def test_personen_beim_lieferanten() -> None:
    text, _ = run("Ansprechpartner: Rita Schuster   Backstubenweg 8 90763 Fürth\nGeschäftsführer: Bernd Ofer · HRB 1")
    assert "Schuster" not in text and "Ofer" not in text
    # Anschrift des Lieferanten (Firma) bleibt erhalten
    assert "Backstubenweg 8" in text


@pytest.mark.parametrize(
    ("line", "name"),
    [("Managing director: Pieter van Dam · IBAN", "Dam"), ("Attn: Sanne de Vries", "Vries"),
     ("Geschäftsführer: Anna von Berg", "Berg"), ("CEO: John Smith", "Smith")],
)
def test_personen_englisch_und_namenszusaetze(line: str, name: str) -> None:
    text, _ = run(line)
    assert "[PERSON_" in text and name not in text


def test_unterschrift_nach_grussformel_und_wiederholung() -> None:
    text, _ = run("Mit freundlichen Grüßen\n\nDoris Engel\nHausverwaltung Rosenhof GmbH\nGeschäftsführerin: Doris Engel")
    assert "Engel" not in text
    assert "Hausverwaltung Rosenhof GmbH" in text


def test_ocr_verlesener_geschaeftsfuehrer() -> None:
    text, _ = run("Olehmeister GmbH Geschansfohrer: Berod Oter Amtsgericht")
    assert "Berod" not in text


def test_eigene_ustid_ersetzt_fremde_bleibt() -> None:
    text, _ = run("USt-IdNr.: DE999200017\nEmpfänger: DE999100005", vat=("DE999100005",))
    assert "DE999200017" in text and "DE999100005" not in text


def test_lieferant_betraege_positionen_bleiben() -> None:
    src = "Frischgut Großhandel GmbH\n1   Weizenmehl Type 405   25   kg   0,85 €   7 %   21,25 €\nRechnungsbetrag 22,74 €"
    text, _ = run(src)
    assert text == src


GOLD = Path(__file__).resolve().parents[2] / "testdaten" / "goldstandard"


@pytest.mark.skipif(not GOLD.exists(), reason="Testbelege nicht erzeugt")
def test_keine_lecks_in_textbelegen() -> None:
    """Alle PDF-Testbelege mit Textlayer: kein sensibler Wert erreicht den KI-Text."""
    from app.kontierung.konten import load_accounts
    from app.ocr.text import read_document
    from app.qualitaet.vergleich import leaks

    root = GOLD.parent
    mandanten = json.loads((root / "mandanten.json").read_text(encoding="utf-8"))["mandanten"]
    for gpath in sorted(GOLD.glob("*.json")):
        gold = json.loads(gpath.read_text(encoding="utf-8"))
        c = mandanten[gold["client_id"]]
        profile = ClientProfile((c["name"],), (c["street"], f'{c["postcode"]} {c["city"]}'), (c["person"],), c["industry_code"])
        for doc in gold["dokumente"]:
            if doc["art"] != "pdf":
                continue
            read = read_document(root / doc["pfad"])
            res = pseudonymize(read.text, profile, load_accounts(), own_vat_ids=(c["vat_id"],))
            assert leaks(res.payload.text, gold["sensible_werte"]) == [], gold["id"]
