import json

import httpx
import pytest

from app.llm.base import parse_json_answer
from app.llm.bedrock import validate_bedrock_config
from app.llm.openai_compat import OpenAICompatProvider
from app.llm.placeholder import extract_rule_based
from app.ocr.text import rows_from_words
from app.pseudo.pseudonymizer import ClientProfile, pseudonymize
from app.qualitaet.vergleich import compare, leaks, supplier_matches


def test_bedrock_nur_eu_ohne_fable() -> None:
    validate_bedrock_config("eu.anthropic.claude-sonnet-5-5", "eu-central-1")
    with pytest.raises(ValueError):
        validate_bedrock_config("anthropic.claude-sonnet-5-5", "eu-central-1")
    with pytest.raises(ValueError):
        validate_bedrock_config("eu.anthropic.claude-fable-5-1", "eu-central-1")
    with pytest.raises(ValueError):
        validate_bedrock_config("eu.anthropic.claude-sonnet-5-5", "us-east-1")


@pytest.mark.parametrize("model_id", ["openai.gpt-oss-120b-1:0", "qwen.qwen3-235b-a22b-2507-v1:0", "eu.anthropic.claude-sonnet-4-6"])
def test_bedrock_regionale_modelle_in_frankfurt_erlaubt(model_id: str) -> None:
    validate_bedrock_config(model_id, "eu-central-1")


@pytest.mark.parametrize(
    "model_id",
    ["us.anthropic.claude-sonnet-5-5", "global.anthropic.claude-sonnet-5-5", "apac.qwen.qwen3-32b-v1:0",
     "us.openai.gpt-oss-120b-1:0", "", "gpt-oss-120b"],
)
def test_bedrock_profile_ausserhalb_eu_abgelehnt(model_id: str) -> None:
    with pytest.raises(ValueError):
        validate_bedrock_config(model_id, "eu-central-1")


def test_openai_compat_lehnt_us_endpunkte_ab() -> None:
    for url in ("https://api.anthropic.com/v1", "https://api.openai.com/v1", "http://unsicher.example/v1"):
        with pytest.raises(ValueError):
            OpenAICompatProvider("x", url, "k", "m")


def test_openai_compat_mit_attrappe() -> None:
    answer = {"supplier_name": "A GmbH", "lines": []}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["temperature"] == 0.0
        assert "[MANDANT_1]" in body["messages"][1]["content"]
        assert "Geheim GmbH" not in body["messages"][1]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "<think>x</think>```json\n"
                                                                    + json.dumps(answer) + "\n```"}}],
                                         "usage": {"prompt_tokens": 100, "completion_tokens": 20}})

    p = OpenAICompatProvider("stackit_test", "https://beispiel.invalid/v1", "k", "m", transport=httpx.MockTransport(handler))
    payload = pseudonymize("Rechnung an Geheim GmbH", ClientProfile(("Geheim GmbH",)), (("3400", "WE"),)).payload
    res = p.extract(payload)
    assert res.error is None and res.data == answer and (res.input_tokens, res.output_tokens) == (100, 20)


def test_parse_json_answer_fehler() -> None:
    with pytest.raises(ValueError):
        parse_json_answer("keine Antwort")


def test_rows_from_words() -> None:
    words = [(10, 100, 40, 110, "Pos."), (44, 101, 104, 111, "Bezeichnung"), (10, 120, 20, 130, "1"),
             (60, 120, 100, 130, "Mehl"), (300, 121, 330, 131, "7 %")]
    assert rows_from_words(words) == ["Pos. Bezeichnung", "1   Mehl   7 %"]


def test_vergleich_gemischte_reihenfolge() -> None:
    exp = {"supplier_name": "Getränke Hanse Vertrieb GmbH", "invoice_number": "GH-88213", "invoice_date": "2026-10-07",
           "net_total": "243.12", "tax_total": "39.34", "gross_total": "282.46", "document_type": "invoice",
           "reverse_charge": False,
           "lines": [{"net_amount": "186.00", "tax_rate": "19", "account_skr03": "3400"},
                     {"net_amount": "57.12", "tax_rate": "7", "account_skr03": "3300"}]}
    act = {**exp, "supplier_name": "Getranke Hanse Vertrieb GmbH", "invoice_number": "GH-88213 ",
           "lines": [{"net_amount": "57.12", "tax_rate": "7.0", "account_skr03": "3400"},
                     {"net_amount": "186", "tax_rate": "19", "account_skr03": "3400"}]}
    v = compare(exp, act)
    assert all(v["felder"].values())
    assert v["positionen"]["betrag"] == [2, 2] and v["positionen"]["konto"] == [1, 2]
    assert not compare(exp, None)["felder"]["net_total"]


def test_lieferant_unscharf() -> None:
    assert supplier_matches("Frischgut Großhandel GmbH", "Frischgut GroBhandel GmbH")
    assert not supplier_matches("Frischgut Großhandel GmbH", "Lackwerk Südpark GmbH")


def test_leckpruefung_kennungen_exakt() -> None:
    assert leaks("USt-IdNr.: DE999200001", ["DE999100001"]) == []
    assert leaks("USt-IdNr.: DE999100001", ["DE999100001"]) == [0]
    assert leaks("Backerei Kornteld KG", ["Bäckerei Kornfeld KG"]) == [0]


def test_platzhalter_kleinbetrag_brutto() -> None:
    text = ("Bürowelt Kranich e.K.\nDatum: 17.10.2026\nPos. Artikel   Menge   Preis brutto   MwSt   Betrag\n"
            "1   Toner   1   47,60 €   19 %   47,60 €\nSumme   47,60 €\ndarin enthalten 19 % MwSt. 7,60 €")
    d = extract_rule_based(text)
    assert d["lines"][0]["net_amount"] == "40.00" and d["net_total"] == "40.00" and d["invoice_number"] is None


def test_factory_ionos_anbieter(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.llm.factory import build_providers

    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_BEARER_TOKEN_BEDROCK", "STACKIT_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("IONOS_API_KEY", "test-token")
    monkeypatch.setenv("IONOS_BASE_URL", "https://openai.inference.de-txl.ionos.com/v1")
    monkeypatch.setenv("IONOS_MODEL_GPTOSS", "openai/gpt-oss-120b")
    monkeypatch.delenv("IONOS_MODEL_QWEN", raising=False)
    ok, skipped = build_providers()
    assert "ionos_gptoss" in ok and ok["ionos_gptoss"].name == "ionos_gptoss"
    assert skipped["ionos_qwen"] == "IONOS_MODEL_QWEN fehlt"
