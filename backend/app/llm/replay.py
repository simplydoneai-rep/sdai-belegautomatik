"""Abspiel-Anbieter für die Demo: liefert eine aufgezeichnete KI-Antwort statt eines neuen Aufrufs.

Nimmt wie jeder Anbieter nur ``PseudonymizedPayload`` an (CLAUDE.md Regel 2), es entstehen
keine Kosten bei AWS oder IONOS. Die Aufzeichnungen stammen aus den Messläufen
(``scripts/demo_aufzeichnungen.py``) und gehören zu synthetischen Testbelegen.
"""

from __future__ import annotations

import json
from typing import Any

from app.llm.base import LLMProvider


class ReplayProvider(LLMProvider):
    def __init__(self, name: str, recording: dict[str, Any]) -> None:
        self.name = name
        self._recording = recording

    def _complete(self, system: str, user: str) -> tuple[str, int, int]:
        rec = self._recording
        return (json.dumps(rec["ausgabe"], ensure_ascii=False), int(rec.get("token_ein", 0)),
                int(rec.get("token_aus", 0)))
