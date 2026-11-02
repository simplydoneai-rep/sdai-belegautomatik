"""Kanzlei-Stammdaten der Demo: Mandanten, Sachbearbeiter und Berechtigungen.

- Ein Mandant hat Firmenname, Mandantennummer (DATEV 1–99999), Kontenrahmen (SKR03/SKR04), Ansprechpartner
  beim Unternehmen und bis zu zwei Sachbearbeiter: zuständig und Vertretung.
- Ein Sachbearbeiter hat Kürzel, Namen und Rolle. Die Kanzleileitung sieht alle Mandanten und pflegt die Rechte.
- Zugriff je Sachbearbeiter und Mandant: „an“ (darf bearbeiten), „aus“ (kein Zugriff) oder „gesperrt“
  (darf diesem Mandanten nie zugeordnet werden, z. B. bei Interessenkonflikt). Zuständige und Vertretungen haben
  immer Zugriff (CLAUDE.md: Sachbearbeiter sehen nur zugeordnete Mandanten).

Gespeichert in ``testdaten/demo/kanzlei.json`` (nicht im Repository). Jede Änderung steht im Protokoll.
In Phase 5 ersetzen Tabellen in PostgreSQL und die Anmeldung mit Zwei-Faktor diese Datei.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from typing import Any

from app.demo import zustand
from app.demo.verarbeitung import mandanten as testmandanten

DATEI = zustand.ZUSTAND.parent / "kanzlei.json"
KONTENRAHMEN = ("SKR03", "SKR04")
ROLLEN = {"leitung": "Kanzleileitung", "sachbearbeitung": "Sachbearbeitung"}
ZUGRIFF = ("an", "aus", "gesperrt")
_LOCK = threading.Lock()

# Erfundene Startbelegung für die Demo (keine echten Personen)
_START_SB = [("AK", "Anna Keller", "leitung"), ("MB", "Markus Bauer", "sachbearbeitung"),
             ("SL", "Sophie Lang", "sachbearbeitung"), ("TW", "Tim Wagner", "sachbearbeitung")]
_START_ZUSTAENDIG = {"M1": ["MB", "SL"], "M2": ["SL", "TW"], "M3": ["TW", "MB"], "M4": ["MB", "TW"],
                     "M5": ["SL", "MB"], "M6": ["TW", None]}


def _start() -> dict[str, Any]:
    jetzt = datetime.now().isoformat(timespec="seconds")
    sb = {k: {"kuerzel": k, "name": n, "rolle": r, "zugriff": {}, "angelegt": jetzt} for k, n, r in _START_SB}
    mandanten = {}
    for i, (mid, m) in enumerate(testmandanten().items()):
        haupt, vertretung = _START_ZUSTAENDIG.get(mid, [None, None])
        mandanten[mid] = {"id": mid, "name": m["name"], "nummer": 10001 + i, "kontenrahmen": "SKR03",
                          "ansprechpartner": m.get("person", ""), "branche": m.get("branche", ""),
                          "ustid": m.get("vat_id"),
                          "zustaendig": haupt, "vertretung": vertretung, "angelegt": jetzt}
        for k in (haupt, vertretung):
            if k:
                sb[k]["zugriff"][mid] = "an"
    sb["SL"]["zugriff"]["M4"] = "gesperrt"  # Beispiel: Sophie Lang darf Pixelwerk Design nicht betreuen
    return {"mandanten": mandanten, "sachbearbeiter": sb}


def laden() -> dict[str, Any]:
    if not DATEI.exists():
        return _start()
    data: dict[str, Any] = json.loads(DATEI.read_text(encoding="utf-8"))
    return data


def _speichern(k: dict[str, Any]) -> None:
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATEI.with_suffix(".tmp")
    tmp.write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(DATEI)


def zuruecksetzen() -> None:
    with _LOCK:
        if DATEI.exists():
            DATEI.unlink()


def _protokoll(feld: str, alt: Any, neu: Any, nutzer: str) -> None:
    zustand.protokoll_ergaenzen(None, feld, alt, neu, f"Kanzlei · {nutzer}")


# --------------------------------------------------------------------------- Lesen


def mandant(mid: str) -> dict[str, Any]:
    m = laden()["mandanten"].get(mid)
    if not m:
        raise KeyError(f"Mandant {mid} nicht gefunden")
    if "ustid" not in m:  # ältere Stammdaten: USt-IdNr. aus den Testmandanten
        m = {**m, "ustid": testmandanten().get(mid, {}).get("vat_id")}
    return dict(m)


def sachbearbeiter(kuerzel: str) -> dict[str, Any]:
    s = laden()["sachbearbeiter"].get(kuerzel)
    if not s:
        raise KeyError(f"Sachbearbeiter {kuerzel} nicht gefunden")
    return dict(s)


def ist_leitung(nutzer: str) -> bool:
    return bool(laden()["sachbearbeiter"].get(nutzer, {}).get("rolle") == "leitung")


def darf(nutzer: str, mid: str) -> bool:
    k = laden()
    sb = k["sachbearbeiter"].get(nutzer)
    if not sb or mid not in k["mandanten"]:
        return False
    return sb["rolle"] == "leitung" or sb["zugriff"].get(mid) == "an"


def sichtbare_mandanten(nutzer: str) -> list[dict[str, Any]]:
    k = laden()
    return [m for mid, m in sorted(k["mandanten"].items(), key=lambda kv: kv[1]["name"]) if darf(nutzer, mid)]


def _person(k: dict[str, Any], kuerzel: str | None, rolle: str) -> dict[str, Any] | None:
    s = k["sachbearbeiter"].get(kuerzel or "")
    return {"kuerzel": s["kuerzel"], "name": s["name"], "rolle": rolle} if s else None


def mandant_oeffentlich(m: dict[str, Any], k: dict[str, Any] | None = None) -> dict[str, Any]:
    k = k or laden()
    team = [p for p in (_person(k, m.get("zustaendig"), "zuständig"), _person(k, m.get("vertretung"), "Vertretung")) if p]
    return {**m, "team": team}


def stammdaten(nutzer: str) -> dict[str, Any]:
    k = laden()
    return {
        "nutzer": sachbearbeiter(nutzer) if nutzer in k["sachbearbeiter"] else None,
        "leitung": ist_leitung(nutzer),
        "sachbearbeiter": sorted(k["sachbearbeiter"].values(), key=lambda s: (s["rolle"] != "leitung", s["name"])),
        "mandanten": [mandant_oeffentlich(m, k) for m in sichtbare_mandanten(nutzer)],
        "alle_mandanten": [mandant_oeffentlich(m, k) for m in sorted(k["mandanten"].values(), key=lambda m: m["name"])]
        if ist_leitung(nutzer) else [],
        "kontenrahmen": list(KONTENRAHMEN), "rollen": ROLLEN,
    }


# --------------------------------------------------------------------------- Ändern (nur Kanzleileitung)


def _nur_leitung(nutzer: str) -> None:
    if not ist_leitung(nutzer):
        raise PermissionError("Nur die Kanzleileitung darf Mandanten, Sachbearbeiter und Rechte ändern")


def mandant_speichern(nutzer: str, daten: dict[str, Any]) -> dict[str, Any]:
    _nur_leitung(nutzer)
    name = str(daten.get("name") or "").strip()
    if not name:
        raise ValueError("Firmenname fehlt")
    try:
        nummer = int(daten.get("nummer") or 0)
    except (TypeError, ValueError):
        raise ValueError("Mandantennummer muss eine Zahl sein") from None
    if not 1 <= nummer <= 99999:
        raise ValueError("Mandantennummer muss zwischen 1 und 99999 liegen (DATEV)")
    ustid = re.sub(r"\s", "", str(daten.get("ustid") or "")).upper()
    if ustid and not re.fullmatch(r"[A-Z]{2}[0-9A-Z]{2,12}", ustid):
        raise ValueError("USt-IdNr. des Mandanten: Ländercode und Nummer, z. B. DE123456789")
    rahmen = daten.get("kontenrahmen")
    if rahmen not in KONTENRAHMEN:
        raise ValueError("Kontenrahmen SKR03 oder SKR04 wählen")
    haupt, vertretung = daten.get("zustaendig") or None, daten.get("vertretung") or None
    if not haupt:
        raise ValueError("Zuständigen Sachbearbeiter wählen")
    if haupt == vertretung:
        raise ValueError("Vertretung muss eine andere Person sein")
    with _LOCK:
        k = laden()
        mid = daten.get("id") or _neue_id(k)
        for anderer in k["mandanten"].values():
            if anderer["id"] != mid and int(anderer["nummer"]) == nummer:
                raise ValueError(f"Mandantennummer {nummer} ist schon an {anderer['name']} vergeben")
        for kuerzel in (haupt, vertretung):
            if kuerzel and kuerzel not in k["sachbearbeiter"]:
                raise ValueError(f"Sachbearbeiter {kuerzel} gibt es nicht")
            if kuerzel and k["sachbearbeiter"][kuerzel]["zugriff"].get(mid) == "gesperrt":
                raise ValueError(f'{k["sachbearbeiter"][kuerzel]["name"]} ist für diesen Mandanten gesperrt')
        alt = k["mandanten"].get(mid)
        neu = {**(alt or {"angelegt": datetime.now().isoformat(timespec="seconds"), "branche": ""}),
               "id": mid, "name": name, "nummer": nummer, "kontenrahmen": rahmen,
               "ansprechpartner": str(daten.get("ansprechpartner") or "").strip(),
               "ustid": (re.sub(r"\s", "", str(daten.get("ustid") or "")).upper() or None),
               "zustaendig": haupt, "vertretung": vertretung}
        k["mandanten"][mid] = neu
        for kuerzel in (haupt, vertretung):
            if kuerzel:
                k["sachbearbeiter"][kuerzel]["zugriff"][mid] = "an"
        _speichern(k)
    _protokoll(f"Mandant {nummer}", alt and _kurz(alt), _kurz(neu), nutzer)
    return mandant_oeffentlich(neu)


def _kurz(m: dict[str, Any]) -> str:
    return (f'{m["name"]} · {m["kontenrahmen"]} · zuständig {m.get("zustaendig") or "–"}'
            f' · Vertretung {m.get("vertretung") or "–"}')


def _neue_id(k: dict[str, Any]) -> str:
    n = 1
    while f"M{n}" in k["mandanten"]:
        n += 1
    return f"M{n}"


def sachbearbeiter_speichern(nutzer: str, kuerzel: str, name: str, rolle: str) -> dict[str, Any]:
    _nur_leitung(nutzer)
    kuerzel = kuerzel.strip().upper()
    name = name.strip()
    if not re.fullmatch(r"[A-ZÄÖÜ]{2,4}", kuerzel):
        raise ValueError("Kürzel: 2 bis 4 Buchstaben, z. B. MB")
    if not name:
        raise ValueError("Name fehlt")
    if rolle not in ROLLEN:
        raise ValueError("Rolle wählen")
    with _LOCK:
        k = laden()
        alt = k["sachbearbeiter"].get(kuerzel)
        if alt and alt["rolle"] == "leitung" and rolle != "leitung" and \
                sum(1 for s in k["sachbearbeiter"].values() if s["rolle"] == "leitung") == 1:
            raise ValueError("Mindestens eine Person muss Kanzleileitung bleiben")
        neu = {**(alt or {"zugriff": {}, "angelegt": datetime.now().isoformat(timespec="seconds")}),
               "kuerzel": kuerzel, "name": name, "rolle": rolle}
        k["sachbearbeiter"][kuerzel] = neu
        _speichern(k)
    _protokoll(f"Sachbearbeiter {kuerzel}", alt and f'{alt["name"]} · {ROLLEN[alt["rolle"]]}',
               f"{name} · {ROLLEN[rolle]}", nutzer)
    return neu


def zugriff_setzen(nutzer: str, kuerzel: str, mid: str, wert: str) -> dict[str, Any]:
    _nur_leitung(nutzer)
    if wert not in ZUGRIFF:
        raise ValueError("Zugriff: an, aus oder gesperrt")
    with _LOCK:
        k = laden()
        sb, m = k["sachbearbeiter"].get(kuerzel), k["mandanten"].get(mid)
        if not sb or not m:
            raise ValueError("Sachbearbeiter oder Mandant nicht gefunden")
        if wert != "an" and kuerzel in (m.get("zustaendig"), m.get("vertretung")):
            rolle = "zuständig" if kuerzel == m.get("zustaendig") else "Vertretung"
            raise ValueError(f'{sb["name"]} ist für {m["name"]} {rolle}. Zuerst beim Mandanten die Zuständigkeit ändern.')
        alt = sb["zugriff"].get(mid, "aus")
        sb["zugriff"][mid] = wert
        _speichern(k)
    _protokoll(f'Zugriff {kuerzel} auf {m["name"]}', alt, wert, nutzer)
    return sb
