"""Lädt die Kontenliste aus ``tabellen/`` (CLAUDE.md Regel 16)."""

from __future__ import annotations

import json
from pathlib import Path

_DIR = Path(__file__).parent / "tabellen"


def load_accounts(chart: str = "SKR03") -> tuple[tuple[str, str], ...]:
    path = _DIR / f"{chart.lower()}_konten.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple((nr, name) for nr, name in data["konten"])


def normalize_account(value: object, allowed: set[str]) -> str | None:
    """Kontonummer aus der KI-Antwort herauslösen ("4910 Porto" → "4910").

    Konten außerhalb der erlaubten Liste werden verworfen (CLAUDE.md Abschnitt 5).
    """
    import re

    match = re.match(r"\s*(\d{4,8})\b", str(value or ""))
    if not match:
        return None
    number = umschluesseln(match.group(1))
    return number if number in allowed else None


def umschluesseln(number: str) -> str:
    """Im SKR03 2026 entfallene Konten auf das heutige Konto abbilden (tabellen/skr03_umschluessel.json)."""
    return _aliases().get(number, number)


def _aliases() -> dict[str, str]:
    global _ALIAS_CACHE
    if _ALIAS_CACHE is None:
        data = json.loads((_DIR / "skr03_umschluessel.json").read_text(encoding="utf-8"))
        _ALIAS_CACHE = dict(data["konten"])
    return _ALIAS_CACHE


_ALIAS_CACHE: dict[str, str] | None = None


def normalize_lines(data: dict[str, object], allowed: set[str]) -> int:
    """Bereinigt account_skr03 aller Positionen; gibt die Zahl verworfener Konten zurück."""
    dropped = 0
    lines = data.get("lines")
    if not isinstance(lines, list):
        return 0
    for line in lines:
        if isinstance(line, dict) and "account_skr03" in line:
            raw = line["account_skr03"]
            line["account_skr03"] = normalize_account(raw, allowed)
            dropped += raw not in (None, "") and line["account_skr03"] is None
    return dropped
