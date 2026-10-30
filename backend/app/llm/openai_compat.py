"""OpenAI-kompatible Schnittstelle (STACKIT AI Model Serving, IONOS AI Model Hub)."""

from __future__ import annotations

import httpx

from app.llm.base import LLMProvider


class OpenAICompatProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
        timeout_s: float = 180.0,
    ) -> None:
        if not base_url.startswith("https://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
            raise ValueError("Nur HTTPS-Endpunkte erlaubt")
        if "api.anthropic.com" in base_url or "api.openai.com" in base_url:
            raise ValueError("Endpunkt nicht zugelassen (kein EU-Anbieter)")
        self.name = name
        self.model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_s,
            transport=transport,
        )

    def _complete(self, system: str, user: str) -> tuple[str, int, int]:
        resp = self._client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.0,
                "max_tokens": 8192,  # Platz für Denk-Token (GPT-OSS)
            },
        )
        resp.raise_for_status()
        body = resp.json()
        text = body["choices"][0]["message"]["content"] or ""
        usage = body.get("usage", {})
        return text, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
