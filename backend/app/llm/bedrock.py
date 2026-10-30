"""Modelle über Amazon Bedrock, nur EU (Client in eu-central-1).

Zulässig (CLAUDE.md Regel 5, Entscheidung 2026-10-30_bedrock-regionale-modelle):
- EU-Inferenzprofile mit Präfix ``eu.`` (z. B. Claude), Verarbeitung nur in EU-Regionen
- Modelle ohne Geografie-Präfix, die direkt in eu-central-1 laufen (z. B. GPT-OSS, Qwen);
  Verarbeitung nur in Frankfurt
Unzulässig: geografieübergreifende Profile außerhalb der EU (``us.``, ``apac.``, ``global.`` …) und Claude Fable.
"""

from __future__ import annotations

import os

from app.llm.base import LLMProvider

FOREIGN_PREFIXES = ("us.", "us-gov.", "apac.", "global.", "ca.", "jp.", "au.")
MAX_TOKENS = 8192  # Reasoning-Modelle (GPT-OSS) brauchen Platz für Denk-Token


def validate_bedrock_config(model_id: str, region: str) -> None:
    if not model_id:
        raise ValueError("Bedrock-Modell-ID fehlt")
    if model_id.startswith(FOREIGN_PREFIXES):
        raise ValueError("Bedrock-Modell-ID mit Profil außerhalb der EU ist unzulässig")
    if "." not in model_id.split(":")[0]:
        raise ValueError("Bedrock-Modell-ID unbekannten Formats")
    if "fable" in model_id.lower():
        raise ValueError("Claude Fable ist ausgeschlossen (30 Tage Speicherung bei AWS)")
    if model_id.startswith("anthropic."):
        raise ValueError("Claude nur über das EU-Inferenzprofil (Präfix 'eu.')")
    if region != "eu-central-1":
        raise ValueError("Bedrock-Client nur in eu-central-1 (Frankfurt)")


class BedrockProvider(LLMProvider):
    def __init__(self, model_id: str | None = None, region: str | None = None, name: str = "bedrock") -> None:
        self.name = name
        self.model_id = model_id or os.environ.get("BEDROCK_MODEL_ID", "")
        self.region = region or os.environ.get("AWS_REGION", "eu-central-1")
        validate_bedrock_config(self.model_id, self.region)
        import boto3  # lokal importiert, damit Tests ohne AWS laufen

        self._client = boto3.client("bedrock-runtime", region_name=self.region)

    def _complete(self, system: str, user: str) -> tuple[str, int, int]:
        resp = self._client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.0},
        )
        parts = resp["output"]["message"]["content"]
        # Nur Antworttext; Denk-Blöcke (reasoningContent) werden nicht ausgewertet, aber als Token berechnet.
        text = "".join(p.get("text", "") for p in parts)
        usage = resp.get("usage", {})
        return text, int(usage.get("inputTokens", 0)), int(usage.get("outputTokens", 0))
