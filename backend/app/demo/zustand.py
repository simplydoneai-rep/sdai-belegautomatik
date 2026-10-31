"""Zustand der Demo: Kreditorenstamm je Mandant, gewählte Konten, Freigaben, Änderungsprotokoll.

Gespeichert in ``testdaten/demo/zustand.json`` (nicht im Repository). Das Protokoll wird nur
ergänzt, nie geändert (Vorbild CLAUDE.md Regel 10). In Phase 0 ersetzt PostgreSQL diese Datei.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

ZUSTAND = Path(__file__).resolve().parents[3] / "testdaten" / "demo" / "zustand.json"
_LOCK = threading.Lock()


def kreditor_bereich(sachkontenlaenge: int = 4) -> tuple[int, int]:
    """DATEV: Kreditoren haben eine Stelle mehr als Sachkonten. Bei 4 Stellen 70000–99999."""
    return 7 * 10 ** sachkontenlaenge, 10 ** (sachkontenlaenge + 1) - 1


def _leer() -> dict[str, Any]:
    return {"kreditoren": {}, "belege": {}, "uploads": {}, "protokoll": []}


def laden() -> dict[str, Any]:
    if not ZUSTAND.exists():
        return _leer()
    data: dict[str, Any] = json.loads(ZUSTAND.read_text(encoding="utf-8"))
    return data


def _speichern(z: dict[str, Any]) -> None:
    ZUSTAND.parent.mkdir(parents=True, exist_ok=True)
    tmp = ZUSTAND.with_suffix(".tmp")
    tmp.write_text(json.dumps(z, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ZUSTAND)


def zuruecksetzen() -> None:
    with _LOCK:
        _speichern(_leer())


def _protokoll(z: dict[str, Any], beleg: str | None, feld: str, alt: Any, neu: Any, quelle: str) -> None:
    z["protokoll"].append({"zeit": datetime.now().isoformat(timespec="seconds"), "nutzer": "Demo",
                           "beleg": beleg, "feld": feld, "alt": alt, "neu": neu, "quelle": quelle})


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9äöüß]", "", name.lower())


def kreditor_finden(mandant: str, lieferant: str | None) -> dict[str, Any] | None:
    if not lieferant:
        return None
    best, score = None, 0.0
    for k in laden()["kreditoren"].get(mandant, []):
        for n in [k["name"], *k.get("aliase", [])]:
            s = fuzz.ratio(_norm(n), _norm(lieferant))
            if s > score:
                best, score = k, s
    return best if score >= 90 else None


def naechste_kreditornummer(mandant: str, sachkontenlaenge: int = 4) -> int:
    lo, hi = kreditor_bereich(sachkontenlaenge)
    vergeben = {int(k["nr"]) for k in laden()["kreditoren"].get(mandant, [])}
    nr = lo
    while nr in vergeben and nr <= hi:
        nr += 1
    if nr > hi:
        raise ValueError("Kein freier Kreditor mehr im Nummernkreis")
    return nr


def kreditor_anlegen(mandant: str, nr: int, name: str, beleg: str | None, sachkontenlaenge: int = 4,
                     alias: str | None = None) -> dict[str, Any]:
    lo, hi = kreditor_bereich(sachkontenlaenge)
    name = name.strip()
    if not lo <= nr <= hi:
        raise ValueError(f"Kreditorennummer muss zwischen {lo} und {hi} liegen")
    if not name:
        raise ValueError("Name des Lieferanten fehlt")
    with _LOCK:
        z = laden()
        liste = z["kreditoren"].setdefault(mandant, [])
        if any(int(k["nr"]) == nr for k in liste):
            raise ValueError(f"Kreditor {nr} ist bei diesem Mandanten schon vergeben")
        if any(_norm(k["name"]) == _norm(name) for k in liste):
            raise ValueError("Dieser Lieferant hat bereits eine Kreditorennummer")
        k = {"nr": str(nr), "name": name, "aliase": [alias] if alias and alias != name else [],
             "angelegt": datetime.now().isoformat(timespec="seconds"), "konten": {}}
        liste.append(k)
        _protokoll(z, beleg, f"Kreditor {mandant}", None, f"{nr} {name}", "Sachbearbeiter")
        _speichern(z)
        return k


def upload_merken(key: str, info: dict[str, Any]) -> None:
    with _LOCK:
        z = laden()
        if key not in z.setdefault("uploads", {}):
            z["uploads"][key] = info
            _protokoll(z, key, "Eingang", None, info["dateiname"], "Upload")
            _speichern(z)


def beleg_zustand(key: str) -> dict[str, Any]:
    b: dict[str, Any] = laden()["belege"].get(key, {})
    return b


def konto_setzen(key: str, pos: int, konto: str | None, vorher: str | None) -> None:
    with _LOCK:
        z = laden()
        b = z["belege"].setdefault(key, {"status": "offen", "konten": {}})
        if b.get("status") == "freigegeben":
            raise ValueError("Beleg ist schon freigegeben")
        b["konten"][str(pos)] = konto
        _protokoll(z, key, f"Position {pos + 1} Sachkonto", vorher, konto, "Sachbearbeiter")
        _speichern(z)


def freigeben(key: str, mandant: str, kreditor: str, buchungen: list[dict[str, Any]]) -> None:
    """Freigabe: Status setzen und je Kreditor merken, welche Konten bestätigt wurden (einfache Lernregel)."""
    with _LOCK:
        z = laden()
        b = z["belege"].setdefault(key, {"status": "offen", "konten": {}})
        if b.get("status") == "freigegeben":
            raise ValueError("Beleg ist schon freigegeben")
        b.update({"status": "freigegeben", "kreditor": kreditor, "freigegeben_am": datetime.now().isoformat(timespec="seconds"),
                  "buchungen": buchungen})
        for k in z["kreditoren"].get(mandant, []):
            if k["nr"] == kreditor:
                for bu in buchungen:
                    zaehler = k.setdefault("konten", {})
                    zaehler[bu["konto"]] = zaehler.get(bu["konto"], 0) + 1
        _protokoll(z, key, "Status", "offen", "freigegeben", "Sachbearbeiter")
        _speichern(z)


def wiedereroeffnen(key: str) -> None:
    with _LOCK:
        z = laden()
        b = z["belege"].get(key)
        if not b or b.get("status") != "freigegeben":
            raise ValueError("Beleg ist nicht freigegeben")
        b["status"] = "offen"
        _protokoll(z, key, "Status", "freigegeben", "offen", "Sachbearbeiter")
        _speichern(z)


def protokoll(key: str | None = None) -> list[dict[str, Any]]:
    eintraege: list[dict[str, Any]] = laden()["protokoll"]
    return [e for e in eintraege if key is None or e["beleg"] == key]
