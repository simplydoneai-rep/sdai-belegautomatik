"""Zustand der Demo: Kreditorenstamm je Mandant, gewählte Konten, Freigaben, Änderungsprotokoll.

Gespeichert in ``testdaten/demo/zustand.json`` (nicht im Repository). Das Protokoll wird nur
ergänzt, nie geändert (Vorbild CLAUDE.md Regel 10). In Phase 0 ersetzt PostgreSQL diese Datei.
"""

from __future__ import annotations

import json
import re
from contextvars import ContextVar
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from app.lernen import regeln as lernregeln

ZUSTAND = Path(__file__).resolve().parents[3] / "testdaten" / "demo" / "zustand.json"
_LOCK = threading.Lock()
NUTZER: ContextVar[str] = ContextVar("nutzer", default="Demo")  # angemeldete Person, je Anfrage gesetzt


def kreditor_bereich(sachkontenlaenge: int = 4) -> tuple[int, int]:
    """DATEV: Kreditoren haben eine Stelle mehr als Sachkonten. Bei 4 Stellen 70000–99999."""
    return 7 * 10 ** sachkontenlaenge, 10 ** (sachkontenlaenge + 1) - 1


def _leer() -> dict[str, Any]:
    return {"kreditoren": {}, "belege": {}, "uploads": {}, "regeln": {}, "folgemonat": False, "protokoll": []}


def laden() -> dict[str, Any]:
    if not ZUSTAND.exists():
        return _leer()
    data: dict[str, Any] = json.loads(ZUSTAND.read_text(encoding="utf-8"))
    return data


def _speichern(z: dict[str, Any]) -> None:
    ZUSTAND.parent.mkdir(parents=True, exist_ok=True)
    tmp = ZUSTAND.with_suffix(".tmp")
    tmp.write_text(json.dumps(z, ensure_ascii=False, indent=1), encoding="utf-8")
    for versuch in range(20):  # Windows sperrt die Datei kurz, z. B. während der Virenscanner sie liest
        try:
            tmp.replace(ZUSTAND)
            return
        except PermissionError:
            if versuch == 19:
                raise
            time.sleep(0.05)


def zuruecksetzen() -> None:
    with _LOCK:
        _speichern(_leer())


def _protokoll(z: dict[str, Any], beleg: str | None, feld: str, alt: Any, neu: Any, quelle: str) -> None:
    z["protokoll"].append({"zeit": datetime.now().isoformat(timespec="seconds"), "nutzer": NUTZER.get(),
                           "beleg": beleg, "feld": feld, "alt": alt, "neu": neu, "quelle": quelle})


def protokoll_ergaenzen(beleg: str | None, feld: str, alt: Any, neu: Any, quelle: str) -> None:
    with _LOCK:
        z = laden()
        _protokoll(z, beleg, feld, alt, neu, quelle)
        _speichern(z)


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


def _ustid_pruefen(ustid: str | None, land: str | None) -> tuple[str | None, str | None]:
    ustid = re.sub(r"\s", "", ustid or "").upper() or None
    land = (land or "").strip().upper() or None
    if ustid and not re.fullmatch(r"[A-Z]{2}[0-9A-Z+*]{2,12}", ustid):
        raise ValueError("USt-IdNr.: Ländercode und Nummer, z. B. NL999999042B01")
    if land and not re.fullmatch(r"[A-Z]{2}", land):
        raise ValueError("Land als zweistelliger Code, z. B. NL")
    if ustid and land and not ustid.startswith(land) and not (land == "GR" and ustid.startswith("EL")):
        raise ValueError(f"USt-IdNr. {ustid} passt nicht zum Land {land}")
    return ustid, land or (ustid[:2] if ustid else None)


def kreditor_daten_setzen(mandant: str, nr: str, ustid: str | None, land: str | None, beleg: str | None) -> None:
    """USt-IdNr. und Land des Kreditors (für i. g. Erwerb und § 13b; DATEV fragt beides beim Buchen ab)."""
    ustid, land = _ustid_pruefen(ustid, land)
    with _LOCK:
        z = laden()
        k = next((k for k in z["kreditoren"].get(mandant, []) if k["nr"] == nr), None)
        if not k:
            raise ValueError("Kreditor nicht gefunden")
        vorher = f'{k.get("ustid") or "–"} · {k.get("land") or "–"}'
        k["ustid"], k["land"] = ustid, land
        _protokoll(z, beleg, f"Kreditor {nr} USt-IdNr./Land", vorher, f'{ustid or "–"} · {land or "–"}', "Sachbearbeiter")
        _speichern(z)


def kreditor_anlegen(mandant: str, nr: int, name: str, beleg: str | None, sachkontenlaenge: int = 4,
                     alias: str | None = None, ustid: str | None = None, land: str | None = None) -> dict[str, Any]:
    lo, hi = kreditor_bereich(sachkontenlaenge)
    name = name.strip()
    if not lo <= nr <= hi:
        raise ValueError(f"Kreditorennummer muss zwischen {lo} und {hi} liegen")
    if not name:
        raise ValueError("Name des Lieferanten fehlt")
    ustid, land = _ustid_pruefen(ustid, land)
    with _LOCK:
        z = laden()
        liste = z["kreditoren"].setdefault(mandant, [])
        if any(int(k["nr"]) == nr for k in liste):
            raise ValueError(f"Kreditor {nr} ist bei diesem Mandanten schon vergeben")
        if any(_norm(k["name"]) == _norm(name) for k in liste):
            raise ValueError("Dieser Lieferant hat bereits eine Kreditorennummer")
        k = {"nr": str(nr), "name": name, "aliase": [alias] if alias and alias != name else [],
             "angelegt": datetime.now().isoformat(timespec="seconds"), "konten": {}, "ustid": ustid, "land": land}
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


def position_setzen(key: str, pos: int, feld: str, wert: Any, vorher: Any, bezeichnung: str) -> None:
    """Manuelle Angabe je Position: ``bu`` (Steuerschlüssel), ``satz`` (Steuersatz) oder ``aufteilung``.
    ``wert`` None entfernt die Angabe (zurück zum Vorschlag)."""
    with _LOCK:
        z = laden()
        b = z["belege"].setdefault(key, {"status": "offen", "konten": {}})
        if b.get("status") == "freigegeben":
            raise ValueError("Beleg ist schon freigegeben")
        werte = b.setdefault(feld, {})
        if wert is None:
            werte.pop(str(pos), None)
        else:
            werte[str(pos)] = wert
        _protokoll(z, key, f"Position {pos + 1} {bezeichnung}", vorher, wert if wert is not None else "Vorschlag", "Sachbearbeiter")
        _speichern(z)


def freigeben(key: str, mandant: str, kreditor: str, buchungen: list[dict[str, Any]], brutto: str | None,
              quelle: str = "Sachbearbeiter") -> None:
    """Freigabe: Status setzen und je Position lernen (Lernregel je Mandant und Kreditor).
    Die Änderungen an den Regeln werden am Beleg gemerkt, damit „Wieder öffnen“ sie zurücknehmen kann."""
    jetzt = datetime.now().isoformat(timespec="seconds")
    with _LOCK:
        z = laden()
        b = z["belege"].setdefault(key, {"status": "offen", "konten": {}})
        if b.get("status") == "freigegeben":
            raise ValueError("Beleg ist schon freigegeben")
        regeln = z.setdefault("regeln", {}).setdefault(mandant, {}).setdefault(kreditor, [])
        gelernt = [lernregeln.lernen(regeln, bu["bezeichnung"], bu["steuersatz"], bu["konto"], bu["korrektur"], jetzt)
                   for bu in buchungen]
        b.update({"status": "freigegeben", "mandant": mandant, "kreditor": kreditor, "freigegeben_am": jetzt,
                  "buchungen": buchungen, "gelernt": gelernt, "brutto": brutto})
        _protokoll(z, key, "Status", "offen", "freigegeben", quelle)
        for bu, g in zip(buchungen, gelernt):
            art = "neu gelernt" if g["vorher"] is None else ("korrigiert" if bu["korrektur"] else "bestätigt")
            _protokoll(z, key, f"Lernregel {kreditor}", None, f'{bu["bezeichnung"]} → {bu["konto"]} ({art})', quelle)
        _speichern(z)


def wiedereroeffnen(key: str, mandant: str) -> None:
    """Freigabe zurücknehmen; was diese Freigabe gelernt hat, wird ebenfalls zurückgenommen."""
    with _LOCK:
        z = laden()
        b = z["belege"].get(key)
        if not b or b.get("status") != "freigegeben":
            raise ValueError("Beleg ist nicht freigegeben")
        regeln = z.get("regeln", {}).get(mandant, {}).get(b.get("kreditor", ""), [])
        for g in reversed(b.get("gelernt", [])):
            lernregeln.rueckgaengig(regeln, g)
        b.update({"status": "offen", "gelernt": []})
        _protokoll(z, key, "Status", "freigegeben", "offen (Gelerntes zurückgenommen)", "Sachbearbeiter")
        _speichern(z)


def regeln(mandant: str, kreditor: str | None) -> list[dict[str, Any]]:
    if not kreditor:
        return []
    r: list[dict[str, Any]] = laden().get("regeln", {}).get(mandant, {}).get(kreditor, [])
    return r


def regel_aktiv_setzen(mandant: str, kreditor: str, regel_id: str, aktiv: bool) -> None:
    with _LOCK:
        z = laden()
        for r in z.get("regeln", {}).get(mandant, {}).get(kreditor, []):
            if r["id"] == regel_id:
                vorher = r.get("aktiv", True)
                r["aktiv"] = aktiv
                _protokoll(z, None, f"Lernregel {kreditor} „{r['beispiel']}“", "aktiv" if vorher else "aus",
                           "aktiv" if aktiv else "aus", "Sachbearbeiter")
                _speichern(z)
                return
    raise ValueError("Regel nicht gefunden")


def bruttohistorie(mandant: str, kreditor: str | None, ohne: str | None = None) -> list[str]:
    """Bruttobeträge freigegebener Belege dieses Kreditors (für die Prüfung ungewöhnlicher Beträge)."""
    if not kreditor:
        return []
    z = laden()
    return [str(b["brutto"]) for k, b in z["belege"].items()
            if k != ohne and b.get("status") == "freigegeben" and b.get("kreditor") == kreditor and b.get("brutto")
            and k in _belege_des_mandanten(z, mandant)]


def _belege_des_mandanten(z: dict[str, Any], mandant: str) -> set[str]:
    return {k for k, b in z["belege"].items() if b.get("mandant") == mandant}


def folgemonat_einspielen() -> bool:
    with _LOCK:
        z = laden()
        if z.get("folgemonat"):
            return False
        z["folgemonat"] = True
        _protokoll(z, None, "Eingang", None, "Belege November 2026 eingespielt", "Demo")
        _speichern(z)
        return True


def protokoll(key: str | None = None) -> list[dict[str, Any]]:
    eintraege: list[dict[str, Any]] = laden()["protokoll"]
    return [e for e in eintraege if key is None or e["beleg"] == key]
