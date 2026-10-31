"""Suche im vollständigen SKR03 (tabellen/skr03_vollstaendig.json): nach Nummer oder Begriff.

„War“ findet Wareneingang 7 %, Wareneingang 19 % usw.; „34“ findet 3400 ff. Konten, die für
Eingangsrechnungen typisch sind (Klassen 0, 3, 4), stehen bei gleicher Trefferart vorn.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DIR = Path(__file__).parent / "tabellen"
BEVORZUGT = ("3", "4", "0")  # Wareneingang, Aufwand, Anlagen
_UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _norm(s: str) -> str:
    return s.lower().translate(_UMLAUT)


@lru_cache(maxsize=1)
def alle_konten() -> list[dict[str, Any]]:
    data = json.loads((_DIR / "skr03_vollstaendig.json").read_text(encoding="utf-8"))
    konten: list[dict[str, Any]] = data["konten"]
    for k in konten:
        k["_such"] = _norm(f'{k["name"]}')
        k["_woerter"] = re.findall(r"[a-z0-9]+", k["_such"])
    return konten


@lru_cache(maxsize=1)
def _suchbegriffe() -> dict[str, str]:
    data = json.loads((_DIR / "skr03_suchbegriffe.json").read_text(encoding="utf-8"))
    return {_norm(k): _norm(v) for k, v in data["begriffe"].items()}


@lru_cache(maxsize=1)
def konten_nach_nummer() -> dict[str, dict[str, Any]]:
    return {k["nr"]: k for k in alle_konten()}


def konto(nr: str | None) -> dict[str, Any] | None:
    return konten_nach_nummer().get(str(nr)) if nr else None


def oeffentlich(k: dict[str, Any]) -> dict[str, Any]:
    return {"nr": k["nr"], "name": k["name"], "kennzeichen": k.get("kennzeichen", "")}


def suchen(q: str, limit: int = 12) -> list[dict[str, Any]]:
    q = q.strip()
    if not q:
        return []
    treffer: list[tuple[tuple[int, int, str], dict[str, Any]]] = []
    if q.isdigit():
        for k in alle_konten():
            if k["nr"].startswith(q):
                treffer.append(((0, 0 if k["nr"][0] in BEVORZUGT else 1, k["nr"]), k))
    else:
        teile = re.findall(r"[a-z0-9]+", _norm(q))
        begriffe = _suchbegriffe()
        teile = [w for t in teile for w in (begriffe.get(t, t).split())]
        for k in alle_konten():
            if not all(any(w.startswith(t) for w in k["_woerter"]) or t in k["_such"] for t in teile):
                continue
            beginnt = k["_such"].startswith(teile[0]) if teile else False
            rang = 0 if beginnt else (1 if all(any(w.startswith(t) for w in k["_woerter"]) for t in teile) else 2)
            treffer.append(((rang, 0 if k["nr"][0] in BEVORZUGT else 1, k["nr"]), k))
    treffer.sort(key=lambda t: t[0])
    return [oeffentlich(k) for _, k in treffer[:limit]]
