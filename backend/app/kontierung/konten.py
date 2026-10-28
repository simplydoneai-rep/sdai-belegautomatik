"""Lädt die Kontenliste aus ``tabellen/`` (CLAUDE.md Regel 16)."""

from __future__ import annotations

import json
from pathlib import Path

_DIR = Path(__file__).parent / "tabellen"


def load_accounts(chart: str = "SKR03") -> tuple[tuple[str, str], ...]:
    path = _DIR / f"{chart.lower()}_konten.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple((nr, name) for nr, name in data["konten"])
