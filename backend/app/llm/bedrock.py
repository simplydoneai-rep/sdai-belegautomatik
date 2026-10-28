"""Claude über Amazon Bedrock, nur EU (eu-central-1, Inferenzprofil ``eu.``)."""

from __future__ import annotations

import os

from app.llm.base import LLMProvider


def validate_bedrock_config(model_id: str, region: str) -> None:
    if not model_id.startswith("eu."):
        raise ValueError("Bedrock-Modell-ID muss ein EU-Inferenzprofil sein (Präfix 'eu.')")
    if "fable" in model_id.lower():
        raise ValueError("Claude Fable ist ausgeschlossen (30 Tage Speicherung bei AWS)")
    if region != "eu-central-1":
        raise ValueError("Bedrock-Client nur in eu-central-1 (Frankfurt)")


class BedrockProvider(LLMProvider):
    name = "bedrock"

    def __init__(self, model_id: str | None = None, region: str | None = None) -> None:
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
            inferenceConfig={"maxTokens": 4096, "temperature": 0.0},
        )
        parts = resp["output"]["message"]["content"]
        text = "".join(p.get("text", "") for p in parts)
        usage = resp.get("usage", {})
        return text, int(usage.get("inputTokens", 0)), int(usage.get("outputTokens", 0))
