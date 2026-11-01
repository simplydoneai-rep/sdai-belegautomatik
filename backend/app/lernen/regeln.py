"""Lernregeln je Mandant und Kreditor (CLAUDE.md Abschnitt 5, Regel 8: nie mandantenübergreifend).

Eine Regel ist ein „Fingerabdruck“ einer Rechnungsposition: Kernbegriffe der Bezeichnung + Steuersatz → Sachkonto.
Beispiel: Getränke Hanse · {mineralwasser, medium} · 19 % → 3400.

Sicherheit (CLAUDE.md: „Ab 3 gleichen Korrekturen gilt die Regel als sicher“):
- Wurde der Vorschlag nie korrigiert, ist die Regel nach der ersten Bestätigung sicher.
- Hat ein Sachbearbeiter das Konto korrigiert, braucht die Regel 3 gleiche Bestätigungen.
Jede Regel ist einsehbar und einzeln abschaltbar.
"""

from __future__ import annotations

import copy
import re
import uuid
from decimal import Decimal
from typing import Any

MIN_AEHNLICHKEIT = 0.5
BESTAETIGUNGEN_NACH_KORREKTUR = 3
_UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_FUELLWOERTER = {
    "und", "oder", "mit", "fuer", "von", "der", "die", "das", "inkl", "zzgl", "pro", "stueck", "stk", "kiste",
    "karton", "packung", "paket", "lt", "laut", "nach", "auf", "aus", "bis", "ohne",
    # Zeitangaben ändern sich jeden Monat und dürfen den Fingerabdruck nicht verschieben
    "januar", "februar", "maerz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november",
    "dezember", "monat", "monate", "quartal", "jahr",
}


def begriffe(bezeichnung: str | None) -> frozenset[str]:
    """Kernbegriffe einer Positionsbezeichnung: klein, ohne Umlaute, ohne Zahlen, Einheiten und Füllwörter."""
    text = (bezeichnung or "").lower().translate(_UMLAUT)
    woerter = re.findall(r"[a-z][a-z-]{2,}", text)
    return frozenset(w.strip("-") for w in woerter if w.strip("-") not in _FUELLWOERTER and len(w.strip("-")) >= 3)


def aehnlichkeit(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _satz(value: Any) -> str:
    try:
        return str(Decimal(str(value)).normalize())
    except Exception:
        return str(value)


def regel_finden(regeln: list[dict[str, Any]], bezeichnung: str | None, steuersatz: Any,
                 nur_aktive: bool = True) -> dict[str, Any] | None:
    """Beste Regel mit gleichem Steuersatz und ausreichend ähnlicher Bezeichnung."""
    ziel = begriffe(bezeichnung)
    satz = _satz(steuersatz)
    beste, wert = None, 0.0
    for r in regeln:
        if (nur_aktive and not r.get("aktiv", True)) or r["satz"] != satz:
            continue
        w = aehnlichkeit(ziel, frozenset(r["begriffe"]))
        if w > wert:
            beste, wert = r, w
    return beste if wert >= MIN_AEHNLICHKEIT else None


def ist_sicher(regel: dict[str, Any]) -> bool:
    if not regel.get("aktiv", True):
        return False
    if regel["korrekturen"] == 0:
        return bool(regel["bestaetigungen"] >= 1)
    return bool(regel["bestaetigungen"] >= BESTAETIGUNGEN_NACH_KORREKTUR)


def sicherheit(regel: dict[str, Any]) -> float:
    """Sicherheit 0–1 einer Regel für die Ampel und die Belegsicherheit."""
    if not regel.get("aktiv", True):
        return 0.0
    n = regel["bestaetigungen"]
    if ist_sicher(regel):
        return min(0.99, 0.93 + 0.02 * n)
    return 0.5 + 0.1 * n


def lernen(regeln: list[dict[str, Any]], bezeichnung: str | None, steuersatz: Any, konto: str,
           korrektur: bool, zeit: str) -> dict[str, Any]:
    """Regel anlegen oder anpassen. Gibt eine Änderung zurück, mit der sich das Lernen rückgängig machen lässt
    (Beleg wieder öffnen)."""
    vorhanden = regel_finden(regeln, bezeichnung, steuersatz, nur_aktive=False)
    if vorhanden is None:
        neu = {"id": uuid.uuid4().hex[:10], "begriffe": sorted(begriffe(bezeichnung)), "beispiel": bezeichnung,
               "satz": _satz(steuersatz), "konto": konto, "bestaetigungen": 1, "korrekturen": 1 if korrektur else 0,
               "aktiv": True, "angelegt": zeit, "zuletzt": zeit}
        regeln.append(neu)
        return {"regel": neu["id"], "vorher": None}
    vorher = copy.deepcopy(vorhanden)
    if vorhanden["konto"] == konto:
        vorhanden["bestaetigungen"] += 1
    else:  # Korrektur: neues Konto, Zählung beginnt von vorn, ab jetzt 3 Bestätigungen nötig
        vorhanden.update({"konto": konto, "bestaetigungen": 1, "korrekturen": vorhanden["korrekturen"] + 1})
    vorhanden["zuletzt"] = zeit
    vorhanden["beispiel"] = bezeichnung
    return {"regel": vorhanden["id"], "vorher": vorher}


def rueckgaengig(regeln: list[dict[str, Any]], aenderung: dict[str, Any]) -> None:
    for i, r in enumerate(regeln):
        if r["id"] == aenderung["regel"]:
            if aenderung["vorher"] is None:
                del regeln[i]
            else:
                regeln[i] = aenderung["vorher"]
            return
