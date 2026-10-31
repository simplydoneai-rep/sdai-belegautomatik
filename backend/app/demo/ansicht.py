"""Rechnungseingang der Demo: Liste der zu verbuchenden Belege, Detailansicht mit Kontovorschlägen,
Ampel je Position, Kreditorenzuordnung und Freigabe.

Ampel je Position (Wunsch Paul Graß, 31.10.2026):
  grün = sicheres Konto: von Ihnen bestätigt, oder mindestens 3 von 5 Modellen einig, oder für diesen
         Kreditor schon gebucht – und das Konto passt zum Steuersatz
  gelb = unsicheres Konto: Vorschlag vorhanden, aber nicht abgesichert oder Widerspruch zum Steuersatz
  rot  = frei: noch kein Konto
"""

from __future__ import annotations

import hashlib
import json
import threading
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.demo import zustand
from app.demo.verarbeitung import MODELLE, TESTDATEN, TABELLEN, aufzeichnungen, mandanten, testbelege, verarbeite
from app.kontierung.betraege import parse_amount
from app.kontierung.konten import umschluesseln
from app.kontierung.kontensuche import konto, oeffentlich

STANDARD_MODELL = "ionos_qwen"
MIN_STIMMEN = 3
SACHKONTENLAENGE = 4  # je Mandant konfigurierbar, Demo: alle Mandanten 4-stellig
STANDARD_JE_SATZ = {"19": "3400", "7": "3300"}

_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def _testeingang() -> list[dict[str, Any]]:
    out = []
    for nr, b in enumerate(testbelege()):
        if b["datei"].startswith("kosit_sicht/"):
            continue
        out.append({**b, "nr": nr})
    return out


def eingang() -> list[dict[str, Any]]:
    """Belege im Rechnungseingang: synthetische Rechnungen, KoSIT-E-Rechnungen (ohne Sicht-PDF-Dubletten)
    und hochgeladene Dateien."""
    uploads = [{"key": k, "id": "Upload", "datei": u["datei"], "art": u["art"], "client_id": u["mandant"],
                "merkmale": [u["dateiname"]], "erwartet": None, "nr": -1}
               for k, u in zustand.laden().get("uploads", {}).items()]
    return _testeingang() + uploads


UPLOAD_ORDNER = TESTDATEN / "demo" / "uploads"
ERLAUBT = {".pdf": "pdf", ".xml": "xml", ".jpg": "foto", ".jpeg": "foto", ".png": "foto", ".tif": "scan", ".tiff": "scan"}


def hochladen(inhalt: bytes, dateiname: str, mandant: str) -> str:
    """Datei in den Eingang übernehmen (Prüfsumme als Name, Dubletten werden erkannt)."""
    endung = Path(dateiname).suffix.lower()
    if endung not in ERLAUBT:
        raise ValueError("Dateityp nicht unterstützt (PDF, XML, JPG, PNG, TIFF)")
    sha = hashlib.sha256(inhalt).hexdigest()
    for b in _testeingang():
        if _sha(b["datei"]) == sha:
            return str(b["key"])  # bekannter Testbeleg
    UPLOAD_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel = UPLOAD_ORDNER / f"{sha[:16]}{endung}"
    if not ziel.exists():
        ziel.write_bytes(inhalt)
    key = f"Upload|demo/uploads/{ziel.name}"
    zustand.upload_merken(key, {"datei": f"demo/uploads/{ziel.name}", "art": ERLAUBT[endung],
                                "mandant": mandant, "dateiname": Path(dateiname).name})
    return key


def _beleg(key: str) -> dict[str, Any]:
    for b in eingang():
        if b["key"] == key:
            return b
    raise KeyError(key)


@lru_cache(maxsize=None)
def _sha(datei: str) -> str:
    return hashlib.sha256((TESTDATEN / datei).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _steuersatz_konten() -> dict[str, set[int]]:
    rates = json.loads((TABELLEN / "skr03_konto_steuersatz.json").read_text(encoding="utf-8"))["konten"]
    return {k: set(v) for k, v in rates.items()}


def ergebnis(key: str, modell: str) -> dict[str, Any]:
    """Verarbeitung je Beleg und Modell, im Speicher zwischengespeichert (Texterkennung nur einmal)."""
    with _LOCK:
        if (key, modell) in _CACHE:
            return _CACHE[(key, modell)]
    b = _beleg(key)
    r = verarbeite(TESTDATEN / b["datei"], b["client_id"], modell, b["erwartet"])
    with _LOCK:
        _CACHE[(key, modell)] = r
    return r


_IN_ARBEIT: set[tuple[str, str]] = set()


def vorberechnen(modell: str = STANDARD_MODELL, keys: list[str] | None = None) -> None:
    for key in keys or [b["key"] for b in eingang()]:
        try:
            ergebnis(key, modell)
        finally:
            with _LOCK:
                _IN_ARBEIT.discard((key, modell))


def _im_hintergrund(keys: list[str], modell: str) -> None:
    """Fehlende Ergebnisse in einem Hintergrund-Thread berechnen (jeder Beleg nur einmal gleichzeitig)."""
    with _LOCK:
        neu = [k for k in keys if (k, modell) not in _CACHE and (k, modell) not in _IN_ARBEIT]
        _IN_ARBEIT.update((k, modell) for k in neu)
    if neu:
        threading.Thread(target=vorberechnen, args=(modell, neu), daemon=True).start()


def _aufgezeichnete_positionen(b: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Positionen je Modell aus den Messläufen. E-Rechnungen: Antworten zum Sichtbeleg derselben Rechnung."""
    datei = b["datei"]
    if datei.endswith(".xml"):
        sicht = next((x["datei"] for x in testbelege() if x["id"] == b["id"] and x["datei"].startswith("kosit_sicht/")), None)
        if not sicht:
            return {}
        datei = sicht
    antworten = aufzeichnungen().get(_sha(datei), {}).get("antworten", {})
    return {m: (a.get("ausgabe") or {}).get("lines") or [] for m, a in antworten.items()}


def _passend(lines: list[dict[str, Any]], betrag: Decimal | None, index: int) -> dict[str, Any] | None:
    if betrag is not None:
        for line in lines:
            a = parse_amount(line.get("net_amount"))
            if a is not None and abs(a - betrag) <= Decimal("0.01"):
                return line
    return lines[index] if index < len(lines) else None


def _konto_ok(nr: str | None) -> str | None:
    if not nr:
        return None
    nr = umschluesseln(str(nr).split()[0])
    return nr if konto(nr) else None


def _position(i: int, pos: dict[str, Any], modell: str, je_modell: dict[str, list[dict[str, Any]]],
              gewaehlt: dict[str, Any], kreditor: dict[str, Any] | None, rc: bool) -> dict[str, Any]:
    betrag = parse_amount(pos.get("net_amount"))
    satz = parse_amount(pos.get("tax_rate"))
    stimmen: dict[str, list[str]] = {}
    for m, lines in je_modell.items():
        line = _passend(lines, betrag, i)
        nr = _konto_ok(line.get("account_skr03")) if line else None
        if nr:
            stimmen.setdefault(nr, []).append(m)
    ki_konto = _konto_ok(pos.get("account_skr03"))
    if not ki_konto:  # E-Rechnung: KI-Vorschlag des gewählten Modells zum Sichtbeleg
        line = _passend(je_modell.get(modell, []), betrag, i)
        ki_konto = _konto_ok(line.get("account_skr03")) if line else None

    historie: dict[str, int] = dict((kreditor or {}).get("konten", {}))
    bestaetigt = str(i) in gewaehlt
    nr = gewaehlt.get(str(i)) if bestaetigt else (ki_konto or next(iter(sorted(historie, key=historie.get, reverse=True)), None))  # type: ignore[arg-type]

    vorschlaege: list[dict[str, Any]] = []

    def add(kto: str, quelle: str) -> None:
        if kto and konto(kto) and kto not in {v["nr"] for v in vorschlaege}:
            vorschlaege.append({**oeffentlich(konto(kto)), "quelle": quelle})  # type: ignore[arg-type]

    if ki_konto:
        add(ki_konto, f'KI · {MODELLE[modell]["kurz"]}')
    for kto, ms in sorted(stimmen.items(), key=lambda kv: -len(kv[1])):
        add(kto, f"KI · {len(ms)} von {len(je_modell)} Modellen")
    for kto, n in sorted(historie.items(), key=lambda kv: -kv[1]):
        add(kto, f"Bisher für diesen Kreditor ({n}×)")
    if satz is not None and str(satz.normalize()) in STANDARD_JE_SATZ:
        add(STANDARD_JE_SATZ[str(satz.normalize())], f"Standard bei {satz.normalize()} %")

    passt = True
    if nr and satz is not None and nr in _steuersatz_konten() and int(satz) not in _steuersatz_konten()[nr]:
        passt = False
    n_stimmen = len(stimmen.get(nr or "", []))
    if not nr:
        ampel, grund = "rot", "Frei – bitte Konto wählen"
    elif not passt:  # Steuerlogik prüft immer, auch bei manueller Wahl (CLAUDE.md Regel 15)
        ampel, grund = "gelb", f"Konto {nr} passt nicht zu {satz.normalize() if satz is not None else '?'} % Steuer"
    elif bestaetigt:
        ampel, grund = "gruen", "Von Ihnen bestätigt"
    elif historie.get(nr):
        ampel, grund = "gruen", f"Für diesen Kreditor schon {historie[nr]}× gebucht"
    elif n_stimmen >= MIN_STIMMEN:
        ampel, grund = "gruen", f"{n_stimmen} von {len(je_modell)} Modellen einig"
    else:
        ampel, grund = "gelb", (f"Nur {n_stimmen} von {len(je_modell)} Modellen schlagen dieses Konto vor" if je_modell
                                else "Vorschlag ohne Bestätigung")
    if rc and satz == 0 and nr in ("3300", "3400"):
        ampel, grund = "gelb", "Reverse Charge: Konto für § 13b oder i. g. Erwerb prüfen"

    k = konto(nr) if nr else None
    return {"pos": i, "bezeichnung": pos.get("description"), "menge": pos.get("quantity"), "einheit": pos.get("unit"),
            "netto": pos.get("net_amount"), "steuersatz": pos.get("tax_rate"),
            "konto": oeffentlich(k) if k else None, "bestaetigt": bestaetigt, "ampel": ampel, "grund": grund,
            "vorschlaege": vorschlaege[:6]}


def _gesamt(positionen: list[dict[str, Any]], summen_ok: bool, kreditor_ok: bool) -> str:
    if not summen_ok or any(p["ampel"] == "rot" for p in positionen) or not positionen:
        return "rot"
    if not kreditor_ok or any(p["ampel"] == "gelb" for p in positionen):
        return "gelb"
    return "gruen"


def ansicht(key: str, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    b = _beleg(key)
    r = ergebnis(key, modell)
    kopf = dict(r["kopf"])
    if str(kopf.get("supplier_name") or "").startswith("[") and b.get("anzeige_lieferant"):
        kopf["supplier_name"] = b["anzeige_lieferant"]
    st = zustand.beleg_zustand(key)
    mandant = b["client_id"]
    lieferant = kopf.get("supplier_name")
    kreditor = zustand.kreditor_finden(mandant, lieferant)
    je_modell = _aufgezeichnete_positionen(b)
    rc = bool(r["kopf"].get("reverse_charge"))
    positionen = [_position(i, p, modell, je_modell, st.get("konten", {}), kreditor, rc)
                  for i, p in enumerate(r["positionen"])]
    offen = []
    if not kreditor:
        offen.append("Kreditor anlegen")
    frei = sum(1 for p in positionen if p["ampel"] == "rot")
    if frei:
        offen.append(f"{frei} Position{'en' if frei > 1 else ''} ohne Konto")
    if not r["steuerlogik"]["ok"]:
        offen.append("Summen widersprüchlich")
    lo, hi = zustand.kreditor_bereich(SACHKONTENLAENGE)
    return {
        "key": key, "id": b["id"], "nr": b["nr"], "art": b["art"], "datei": b["datei"], "merkmale": b["merkmale"],
        "mandant": {"id": mandant, "name": mandanten()[mandant]["name"], "branche": mandanten()[mandant]["branche"]},
        "status": st.get("status", "offen"), "freigegeben_am": st.get("freigegeben_am"),
        "kopf": kopf, "steuerlogik": r["steuerlogik"], "schritte": r["schritte"], "ki": r["ki"],
        "quelle": r["quelle"], "pseudonymisiert": r["pseudonymisiert"], "platzhalter": r["platzhalter"], "soll": r["soll"],
        "kreditor": kreditor and {"nr": kreditor["nr"], "name": kreditor["name"]},
        "kreditor_vorschlag": None if kreditor else {"nr": zustand.naechste_kreditornummer(mandant, SACHKONTENLAENGE),
                                                   "name": lieferant, "von": lo, "bis": hi},
        "positionen": positionen, "ampel": _gesamt(positionen, r["steuerlogik"]["ok"], bool(kreditor)),
        "offen": offen, "freigabe_moeglich": not offen and st.get("status") != "freigegeben",
        "protokoll": zustand.protokoll(key)[-20:],
    }


def liste(mandant: str | None = None, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    eintraege, nach_konto = [], {}
    z = zustand.laden()
    for b in eingang():
        if mandant and b["client_id"] != mandant:
            continue
        with _LOCK:
            fertig = (b["key"], modell) in _CACHE
        status = z["belege"].get(b["key"], {}).get("status", "offen")
        e: dict[str, Any] = {"key": b["key"], "id": b["id"], "art": b["art"], "status": status,
                             "mandant": mandanten()[b["client_id"]]["name"], "mandant_id": b["client_id"], "bereit": fertig}
        if fertig:
            a = ansicht(b["key"], modell)
            e.update({"lieferant": a["kopf"].get("supplier_name"), "datum": a["kopf"].get("invoice_date"),
                      "brutto": a["kopf"].get("gross_total"), "ampel": a["ampel"],
                      "kreditor": a["kreditor"] and a["kreditor"]["nr"], "positionen": len(a["positionen"]),
                      "frei": sum(1 for p in a["positionen"] if p["ampel"] == "rot")})
            if status == "offen":
                for p in a["positionen"]:
                    k = p["konto"] or {"nr": "—", "name": "Noch kein Konto"}
                    g = nach_konto.setdefault(k["nr"], {"nr": k["nr"], "name": k["name"], "anzahl": 0, "summe": Decimal(0)})
                    g["anzahl"] += 1
                    g["summe"] += parse_amount(p["netto"]) or Decimal(0)
        eintraege.append(e)
    _im_hintergrund([e["key"] for e in eintraege if not e["bereit"]], modell)
    eintraege.sort(key=lambda e: e.get("datum") or "", reverse=True)
    offen = [e for e in eintraege if e["status"] == "offen"]
    konten = sorted(nach_konto.values(), key=lambda g: (g["nr"] == "—", -g["anzahl"]))
    return {
        "eintraege": eintraege,
        "anzahl_offen": len(offen), "anzahl_erledigt": len(eintraege) - len(offen),
        "summe_offen": str(sum((parse_amount(e.get("brutto")) or Decimal(0) for e in offen if e.get("brutto")), Decimal(0))),
        "nach_konto": [{**g, "summe": str(g["summe"])} for g in konten],
        "bereit": all(e["bereit"] for e in eintraege),
    }


def freigeben(key: str, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    a = ansicht(key, modell)
    if not a["freigabe_moeglich"]:
        raise ValueError("Freigabe nicht möglich: " + ", ".join(a["offen"] or ["schon freigegeben"]))
    buchungen = [{"pos": p["pos"], "konto": p["konto"]["nr"], "netto": p["netto"], "steuersatz": p["steuersatz"]}
                 for p in a["positionen"]]
    zustand.freigeben(key, a["mandant"]["id"], a["kreditor"]["nr"], buchungen)
    return ansicht(key, modell)


def konto_waehlen(key: str, pos: int, nr: str, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    if not konto(nr):
        raise ValueError(f"Konto {nr} gibt es im SKR03 nicht")
    a = ansicht(key, modell)
    if not 0 <= pos < len(a["positionen"]):
        raise ValueError("Position nicht gefunden")
    vorher = (a["positionen"][pos]["konto"] or {}).get("nr")
    zustand.konto_setzen(key, pos, nr, vorher)
    return ansicht(key, modell)


def kreditor_anlegen(key: str, nr: int, name: str, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    b = _beleg(key)
    lieferant = ansicht(key, modell)["kopf"].get("supplier_name")
    zustand.kreditor_anlegen(b["client_id"], nr, name, key, SACHKONTENLAENGE, alias=lieferant)
    return ansicht(key, modell)


def pfad(key: str) -> Path:
    return TESTDATEN / _beleg(key)["datei"]
