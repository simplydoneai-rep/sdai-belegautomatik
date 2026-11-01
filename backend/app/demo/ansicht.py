"""Rechnungseingang der Demo: Bereiche „Sicher“, „Prüfen“, „Erledigt“, Detailansicht mit Kontovorschlägen,
Ampel je Position, Kreditoren, Lernregeln, Freigabe und Sammelfreigabe.

Vorschlag je Position, in dieser Reihenfolge (CLAUDE.md Abschnitt 5):
  1. Lernregel des Mandanten für diesen Kreditor und diese Positionsart
  2. KI-Vorschlag (in der Demo aus den Messläufen abgespielt)
Die Steuerlogik prüft jeden Vorschlag, auch eine manuelle Wahl (Regel 15).

Ampel je Position (Vorgabe Paul Graß, 31.10.2026): grün = sicher, gelb = unsicher, rot = frei.
Ein Beleg ist „sicher“ (nur ansehen, Sammelfreigabe), wenn der Kreditor bekannt ist, alle Positionen grün sind,
die Summen stimmen und keine feste Ausnahme greift. Nichts wird ohne Klick freigegeben (Regel 12);
jeder Beleg bleibt jederzeit zu öffnen und zu ändern.
"""

from __future__ import annotations

import hashlib
import json
import re
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
from app.lernen import regeln as lernregeln

STANDARD_MODELL = "ionos_qwen"
MIN_STIMMEN = 3
SACHKONTENLAENGE = 4  # je Mandant konfigurierbar, Demo: alle Mandanten 4-stellig
STANDARD_JE_SATZ = {"19": "3400", "7": "3300"}
MIN_SICHERHEIT = Decimal("0.80")
KLEINBETRAG = Decimal("250")
BETRAG_FAKTOR = Decimal("2")  # mehr als doppelt so hoch wie bisher → prüfen

_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LOCK = threading.Lock()
_IN_ARBEIT: set[tuple[str, str]] = set()


# --------------------------------------------------------------------------- Eingang


@lru_cache(maxsize=1)
def _testeingang() -> list[dict[str, Any]]:
    out = []
    for nr, b in enumerate(testbelege()):
        if b["datei"].startswith("kosit_sicht/"):
            continue
        out.append({**b, "nr": nr, "monat": "2026-10"})
    return out


@lru_cache(maxsize=1)
def _folgemonat() -> list[dict[str, Any]]:
    out = []
    for g in sorted((TESTDATEN / "folgemonat" / "gold").glob("*.json")):
        gold = json.loads(g.read_text(encoding="utf-8"))
        doc = gold["dokumente"][0]
        out.append({"key": f'{gold["id"]}|{doc["pfad"]}', "id": gold["id"], "datei": doc["pfad"], "art": doc["art"],
                    "client_id": gold["client_id"], "merkmale": gold["merkmale"], "erwartet": gold["erwartet"],
                    "nr": -1, "monat": "2026-11"})
    return out


def eingang() -> list[dict[str, Any]]:
    """Oktober (synthetische Rechnungen, KoSIT-E-Rechnungen ohne Sicht-PDF-Dubletten), November nach dem
    Einspielen, und hochgeladene Dateien."""
    z = zustand.laden()
    uploads = [{"key": k, "id": "Upload", "datei": u["datei"], "art": u["art"], "client_id": u["mandant"],
                "merkmale": [u["dateiname"]], "erwartet": None, "nr": -1, "monat": None}
               for k, u in z.get("uploads", {}).items()]
    return _testeingang() + (_folgemonat() if z.get("folgemonat") else []) + uploads


UPLOAD_ORDNER = TESTDATEN / "demo" / "uploads"
ERLAUBT = {".pdf": "pdf", ".xml": "xml", ".jpg": "foto", ".jpeg": "foto", ".png": "foto", ".tif": "scan", ".tiff": "scan"}


def hochladen(inhalt: bytes, dateiname: str, mandant: str) -> str:
    """Datei in den Eingang übernehmen (Prüfsumme als Name, Dubletten werden erkannt)."""
    endung = Path(dateiname).suffix.lower()
    if endung not in ERLAUBT:
        raise ValueError("Dateityp nicht unterstützt (PDF, XML, JPG, PNG, TIFF)")
    sha = hashlib.sha256(inhalt).hexdigest()
    for b in _testeingang() + _folgemonat():
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


# --------------------------------------------------------------------------- Verarbeitung (zwischengespeichert)


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


# --------------------------------------------------------------------------- Vorschläge je Position


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


def _datum(iso: str) -> str:
    j, m, t = iso[:10].split("-")
    return f"{t}.{m}.{j}"


def _position(i: int, pos: dict[str, Any], modell: str, je_modell: dict[str, list[dict[str, Any]]],
              gewaehlt: dict[str, Any], regeln: list[dict[str, Any]], rc: bool) -> dict[str, Any]:
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

    regel = lernregeln.regel_finden(regeln, pos.get("description"), pos.get("tax_rate"))
    abgeschaltet = regel is None and lernregeln.regel_finden(regeln, pos.get("description"), pos.get("tax_rate"),
                                                             nur_aktive=False) is not None
    vorschlag_nr = regel["konto"] if regel else ki_konto  # automatischer Vorschlag ohne Eingriff
    bestaetigt = str(i) in gewaehlt
    nr = gewaehlt.get(str(i)) if bestaetigt else vorschlag_nr

    vorschlaege: list[dict[str, Any]] = []

    def add(kto: str | None, quelle: str) -> None:
        k = konto(kto) if kto else None
        if k and kto not in {v["nr"] for v in vorschlaege}:
            vorschlaege.append({**oeffentlich(k), "quelle": quelle})

    if regel:
        add(regel["konto"], f'Gelernt · {regel["bestaetigungen"]}× bestätigt')
    add(ki_konto, f'KI · {MODELLE[modell]["kurz"]}')
    for kto, ms in sorted(stimmen.items(), key=lambda kv: -len(kv[1])):
        add(kto, f"KI · {len(ms)} von {len(je_modell)} Modellen")
    for r in regeln:
        if r.get("aktiv", True):
            add(r["konto"], "Bisher für diesen Kreditor")
    if satz is not None and str(satz.normalize()) in STANDARD_JE_SATZ:
        add(STANDARD_JE_SATZ[str(satz.normalize())], f"Standard bei {satz.normalize()} %")

    passt = not (nr and satz is not None and nr in _steuersatz_konten() and int(satz) not in _steuersatz_konten()[nr])
    n_stimmen = len(stimmen.get(nr or "", []))
    quelle = "manuell" if bestaetigt else ("regel" if regel else ("ki" if ki_konto else None))
    if not nr:
        ampel, grund, sicher = "rot", "Frei – bitte Konto wählen", 0.0
    elif not passt:  # Steuerlogik prüft immer, auch bei manueller Wahl (CLAUDE.md Regel 15)
        ampel, grund, sicher = "gelb", f"Konto {nr} passt nicht zu {satz.normalize() if satz is not None else '?'} % Steuer", 0.3
    elif bestaetigt:
        ampel, grund, sicher = "gruen", "Von Ihnen bestätigt", 1.0
    elif regel and lernregeln.ist_sicher(regel):
        ampel, grund, sicher = "gruen", f'Gelernt: {regel["bestaetigungen"]}× bestätigt, zuletzt {_datum(regel["zuletzt"])}', lernregeln.sicherheit(regel)
    elif regel:
        ampel = "gelb"
        grund = (f'Gelernt nach Korrektur: {regel["bestaetigungen"]} von {lernregeln.BESTAETIGUNGEN_NACH_KORREKTUR} '
                 "Bestätigungen")
        sicher = lernregeln.sicherheit(regel)
    elif n_stimmen >= MIN_STIMMEN:
        ampel, grund, sicher = "gruen", f"{n_stimmen} von {len(je_modell)} Modellen einig", 0.8 + 0.03 * (n_stimmen - MIN_STIMMEN)
    elif abgeschaltet:
        ampel, grund, sicher = "gelb", "Gelernte Regel ist abgeschaltet – Vorschlag bitte prüfen", 0.4
    elif regeln and not je_modell:
        ampel, grund, sicher = "gelb", "Neue Positionsart für diesen Lieferanten – noch nicht gelernt", 0.4
    else:
        ampel = "gelb"
        grund = (f"Nur {n_stimmen} von {len(je_modell)} Modellen schlagen dieses Konto vor" if je_modell
                 else "Vorschlag ohne Bestätigung")
        sicher = 0.5
    if rc and satz == 0 and nr in ("3300", "3400"):
        ampel, grund, sicher = "gelb", "Reverse Charge: Konto für § 13b oder i. g. Erwerb prüfen", 0.3

    k = konto(nr) if nr else None
    return {"pos": i, "bezeichnung": pos.get("description"), "menge": pos.get("quantity"), "einheit": pos.get("unit"),
            "netto": pos.get("net_amount"), "steuersatz": pos.get("tax_rate"),
            "konto": oeffentlich(k) if k else None, "vorschlag_nr": vorschlag_nr, "bestaetigt": bestaetigt,
            "quelle": quelle, "regel": regel and {"id": regel["id"], "bestaetigungen": regel["bestaetigungen"]},
            "ampel": ampel, "grund": grund, "sicherheit": round(sicher, 2), "vorschlaege": vorschlaege[:6]}


# --------------------------------------------------------------------------- Beleg


def _ausnahmen(kopf: dict[str, Any], r: dict[str, Any], kreditor: dict[str, Any] | None, historie: list[str]) -> list[str]:
    """Feste Ausnahmen: solche Belege gehen immer zur Prüfung, egal wie sicher die Konten sind."""
    aus = []
    brutto = parse_amount(kopf.get("gross_total"))
    if not kreditor:
        aus.append("Neuer Lieferant")
    if kopf.get("document_type") == "credit_note":
        aus.append("Gutschrift")
    if kopf.get("reverse_charge"):
        aus.append("Reverse Charge")
    if re.search(r"(?i)\b(abschlag|anzahlung|schlussrechnung)", r.get("pseudonymisiert") or ""):
        aus.append("Anzahlung oder Schlussrechnung")
    if not kopf.get("invoice_number") and (brutto is None or abs(brutto) > KLEINBETRAG):
        aus.append("Rechnungsnummer fehlt")
    if not r["steuerlogik"]["ok"]:
        aus.append("Summen widersprüchlich")
    bisher = [b for b in (parse_amount(h) for h in historie) if b]
    if brutto and bisher and brutto > max(bisher) * BETRAG_FAKTOR:
        aus.append(f"Betrag ungewöhnlich hoch (bisher höchstens {max(bisher):.2f} €)")
    return aus


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
    knr = kreditor["nr"] if kreditor else None
    regeln = zustand.regeln(mandant, knr)
    je_modell = _aufgezeichnete_positionen(b)
    rc = bool(kopf.get("reverse_charge"))
    positionen = [_position(i, p, modell, je_modell, st.get("konten", {}), regeln, rc)
                  for i, p in enumerate(r["positionen"])]

    offen = []
    if not kreditor:
        offen.append("Kreditor anlegen")
    frei = sum(1 for p in positionen if p["ampel"] == "rot")
    if frei:
        offen.append(f"{frei} Position{'en' if frei > 1 else ''} ohne Konto")
    if not r["steuerlogik"]["ok"]:
        offen.append("Summen widersprüchlich")

    ausnahmen = _ausnahmen(kopf, r, kreditor, zustand.bruttohistorie(mandant, knr, ohne=key))
    sicherheit = min((p["sicherheit"] for p in positionen), default=0.0)
    if ausnahmen:
        sicherheit = min(sicherheit, 0.6)
    status = st.get("status", "offen")
    ampel = _gesamt(positionen, r["steuerlogik"]["ok"], bool(kreditor))
    if status == "freigegeben":
        bereich = "erledigt"
    elif ampel == "gruen" and not ausnahmen and Decimal(str(sicherheit)) >= MIN_SICHERHEIT:
        bereich = "sicher"
    else:
        bereich = "pruefen"
    lo, hi = zustand.kreditor_bereich(SACHKONTENLAENGE)
    gelernt = sum(1 for p in positionen if p["quelle"] == "regel")
    return {
        "key": key, "id": b["id"], "nr": b["nr"], "art": b["art"], "datei": b["datei"], "merkmale": b["merkmale"],
        "monat": b.get("monat"),
        "mandant": {"id": mandant, "name": mandanten()[mandant]["name"], "branche": mandanten()[mandant]["branche"]},
        "status": status, "bereich": bereich, "freigegeben_am": st.get("freigegeben_am"),
        "kopf": kopf, "steuerlogik": r["steuerlogik"], "schritte": r["schritte"], "ki": r["ki"],
        "quelle": r["quelle"], "pseudonymisiert": r["pseudonymisiert"], "platzhalter": r["platzhalter"], "soll": r["soll"],
        "kreditor": kreditor and {"nr": kreditor["nr"], "name": kreditor["name"]},
        "kreditor_vorschlag": None if kreditor else {"nr": zustand.naechste_kreditornummer(mandant, SACHKONTENLAENGE),
                                                   "name": lieferant, "von": lo, "bis": hi},
        "regeln": [{**rg, "sicher": lernregeln.ist_sicher(rg),
                    "konto_name": (konto(rg["konto"]) or {}).get("name", "")} for rg in regeln],
        "positionen": positionen, "ampel": ampel, "ausnahmen": ausnahmen,
        "sicherheit": round(sicherheit, 2), "gelernt": gelernt,
        "offen": offen, "freigabe_moeglich": not offen and status != "freigegeben",
        "protokoll": zustand.protokoll(key)[-30:],
    }


# --------------------------------------------------------------------------- Liste


def liste(mandant: str | None = None, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    eintraege, nach_konto = [], {}
    for b in eingang():
        if mandant and b["client_id"] != mandant:
            continue
        with _LOCK:
            fertig = (b["key"], modell) in _CACHE
        e: dict[str, Any] = {"key": b["key"], "id": b["id"], "art": b["art"], "monat": b.get("monat"),
                             "mandant": mandanten()[b["client_id"]]["name"], "mandant_id": b["client_id"],
                             "bereit": fertig, "bereich": "pruefen", "status": "offen"}
        if fertig:
            a = ansicht(b["key"], modell)
            e.update({"lieferant": a["kopf"].get("supplier_name"), "datum": a["kopf"].get("invoice_date"),
                      "brutto": a["kopf"].get("gross_total"), "ampel": a["ampel"], "status": a["status"],
                      "bereich": a["bereich"], "sicherheit": a["sicherheit"], "ausnahmen": a["ausnahmen"],
                      "kreditor": a["kreditor"] and a["kreditor"]["nr"], "positionen": len(a["positionen"]),
                      "gelernt": a["gelernt"], "frei": sum(1 for p in a["positionen"] if p["ampel"] == "rot")})
            if a["status"] == "offen":
                for p in a["positionen"]:
                    k = p["konto"] or {"nr": "—", "name": "Noch kein Konto"}
                    g = nach_konto.setdefault(k["nr"], {"nr": k["nr"], "name": k["name"], "anzahl": 0, "summe": Decimal(0)})
                    g["anzahl"] += 1
                    g["summe"] += parse_amount(p["netto"]) or Decimal(0)
        eintraege.append(e)
    _im_hintergrund([e["key"] for e in eintraege if not e["bereit"]], modell)
    eintraege.sort(key=lambda e: e.get("datum") or "", reverse=True)

    def summe(bereich: str) -> str:
        return str(sum((parse_amount(e.get("brutto")) or Decimal(0) for e in eintraege if e["bereich"] == bereich),
                       Decimal(0)))

    anzahl = {k: sum(1 for e in eintraege if e["bereich"] == k) for k in ("sicher", "pruefen", "erledigt")}
    konten = sorted(nach_konto.values(), key=lambda g: (g["nr"] == "—", -g["anzahl"]))
    return {
        "eintraege": eintraege, "anzahl": anzahl,
        "summe": {k: summe(k) for k in anzahl},
        "anzahl_offen": anzahl["sicher"] + anzahl["pruefen"], "anzahl_erledigt": anzahl["erledigt"],
        "nach_konto": [{**g, "summe": str(g["summe"])} for g in konten],
        "bereit": all(e["bereit"] for e in eintraege),
        "folgemonat": bool(zustand.laden().get("folgemonat")),
    }


# --------------------------------------------------------------------------- Aktionen


def freigeben(key: str, modell: str = STANDARD_MODELL, quelle: str = "Sachbearbeiter") -> dict[str, Any]:
    a = ansicht(key, modell)
    if not a["freigabe_moeglich"]:
        raise ValueError("Freigabe nicht möglich: " + ", ".join(a["offen"] or ["schon freigegeben"]))
    buchungen = [{"pos": p["pos"], "bezeichnung": p["bezeichnung"], "konto": p["konto"]["nr"], "netto": p["netto"],
                  "steuersatz": p["steuersatz"],
                  "korrektur": bool(p["bestaetigt"] and p["vorschlag_nr"] and p["konto"]["nr"] != p["vorschlag_nr"])}
                 for p in a["positionen"]]
    zustand.freigeben(key, a["mandant"]["id"], a["kreditor"]["nr"], buchungen, a["kopf"].get("gross_total"), quelle)
    return ansicht(key, modell)


def sammelfreigabe(keys: list[str], modell: str = STANDARD_MODELL) -> dict[str, Any]:
    """Nur Belege aus dem Bereich „Sicher“; jeder einzeln geprüft. Gibt freigegebene und übersprungene zurück."""
    ok, uebersprungen = [], []
    for key in keys:
        try:
            a = ansicht(key, modell)
            if a["bereich"] != "sicher":
                uebersprungen.append({"key": key, "grund": "nicht mehr im Bereich Sicher"})
                continue
            freigeben(key, modell, quelle="Sammelfreigabe")
            ok.append(key)
        except (ValueError, KeyError) as exc:
            uebersprungen.append({"key": key, "grund": str(exc)})
    return {"freigegeben": ok, "uebersprungen": uebersprungen}


def wiedereroeffnen(key: str, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    zustand.wiedereroeffnen(key, _beleg(key)["client_id"])
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


def regel_aktiv(key: str, regel_id: str, aktiv: bool, modell: str = STANDARD_MODELL) -> dict[str, Any]:
    a = ansicht(key, modell)
    if not a["kreditor"]:
        raise ValueError("Kein Kreditor")
    zustand.regel_aktiv_setzen(a["mandant"]["id"], a["kreditor"]["nr"], regel_id, aktiv)
    return ansicht(key, modell)


def pfad(key: str) -> Path:
    return TESTDATEN / _beleg(key)["datei"]


# --------------------------------------------------------------------------- Demo-Szenario


def demo_oktober(modell: str = STANDARD_MODELL) -> dict[str, int]:
    """Simuliert, dass die Kanzlei den Oktober schon gebucht hat: Kreditoren anlegen, Konten so setzen,
    wie ein Sachbearbeiter sie gebucht hätte (Sollkontierung des Goldstandards), freigeben.
    Nur die synthetischen Oktober-Rechnungen; jeder Schritt steht im Verlauf (Quelle „Demo-Szenario“)."""
    anzahl = {"freigegeben": 0, "kreditoren": 0}
    for b in _testeingang():
        if not b["datei"].startswith("synthetisch/") or zustand.beleg_zustand(b["key"]).get("status") == "freigegeben":
            continue
        a = ansicht(b["key"], modell)
        if not a["kreditor"]:
            zustand.kreditor_anlegen(b["client_id"], zustand.naechste_kreditornummer(b["client_id"], SACHKONTENLAENGE),
                                     a["kopf"]["supplier_name"], b["key"], SACHKONTENLAENGE)
            anzahl["kreditoren"] += 1
            a = ansicht(b["key"], modell)
        soll = [ln.get("account_skr03") for ln in (b["erwartet"] or {}).get("lines", [])]
        for p in a["positionen"]:
            ziel = soll[p["pos"]] if p["pos"] < len(soll) else None
            if ziel and (not p["konto"] or p["konto"]["nr"] != ziel):
                zustand.konto_setzen(b["key"], p["pos"], ziel, (p["konto"] or {}).get("nr"))
        a = ansicht(b["key"], modell)
        if a["freigabe_moeglich"]:
            freigeben(b["key"], modell, quelle="Demo-Szenario Oktober")
            anzahl["freigegeben"] += 1
    return anzahl


def demo_november(modell: str = STANDARD_MODELL) -> int:
    zustand.folgemonat_einspielen()
    keys = [b["key"] for b in _folgemonat()]
    _im_hintergrund(keys, modell)
    return len(keys)
