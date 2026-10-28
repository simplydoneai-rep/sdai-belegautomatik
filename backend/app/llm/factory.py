"""Anbieter aus Konfiguration (.env) erzeugen. Der Anbieter ist Konfiguration, nicht Code."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.llm.base import LLMProvider
from app.llm.placeholder import PlaceholderProvider

_PRICES = json.loads((Path(__file__).parent / "preise.json").read_text(encoding="utf-8"))


def price_per_million(key: str) -> tuple[float, float]:
    env = key.upper()
    vin, vout = os.environ.get(f"PRICE_{env}_IN"), os.environ.get(f"PRICE_{env}_OUT")
    base = _PRICES.get(key, [0.0, 0.0])
    return (float(vin) if vin else base[0], float(vout) if vout else base[1])


def build_providers() -> tuple[dict[str, LLMProvider], dict[str, str]]:
    """Gibt (verfügbare Anbieter, übersprungene mit Grund) zurück."""
    ok: dict[str, LLMProvider] = {"placeholder": PlaceholderProvider()}
    skipped: dict[str, str] = {}
    e = os.environ

    if (e.get("AWS_ACCESS_KEY_ID") and e.get("AWS_SECRET_ACCESS_KEY")) or e.get("AWS_BEARER_TOKEN_BEDROCK"):
        from app.llm.bedrock import BedrockProvider

        ok["bedrock"] = BedrockProvider()
    else:
        skipped["bedrock"] = "keine AWS-Zugangsdaten in .env"

    from app.llm.openai_compat import OpenAICompatProvider

    if e.get("STACKIT_API_KEY"):
        base = e.get("STACKIT_BASE_URL", "")
        for key, var in (("stackit_qwen", "STACKIT_MODEL_QWEN"), ("stackit_gptoss", "STACKIT_MODEL_GPTOSS")):
            if e.get(var):
                ok[key] = OpenAICompatProvider(key, base, e["STACKIT_API_KEY"], e[var])
            else:
                skipped[key] = f"{var} fehlt"
    else:
        skipped["stackit_qwen"] = skipped["stackit_gptoss"] = "kein STACKIT_API_KEY in .env"

    if e.get("IONOS_API_KEY") and e.get("IONOS_MODEL"):
        ok["ionos"] = OpenAICompatProvider("ionos", e["IONOS_BASE_URL"], e["IONOS_API_KEY"], e["IONOS_MODEL"])
    return ok, skipped
