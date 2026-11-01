"""DATEV-Steuerschlüssel (BU-Schlüssel) je Buchungszeile, deterministisch (CLAUDE.md Regeln 15 und 16).

Zwei Arten von Aufwandskonten im SKR03:
- **Automatikkonten** (Kennzeichen AV, z. B. 3400 „Wareneingang 19 % Vorsteuer“): DATEV rechnet die Steuer aus dem
  Konto. Kein Steuerschlüssel; das Konto muss zu Steuersatz und Steuerfall der Rechnung passen.
- **Konten ohne Automatik** (z. B. 4980 „Sonstiger Betriebsbedarf“): Der Steuerschlüssel steuert den Vorsteuerabzug,
  z. B. 9 = Vorsteuer 19 %, 8 = Vorsteuer 7 %, 19 = i. g. Erwerb 19 %, 94 = § 13b 19 %.

Die Schlüssel stehen in ``tabellen/datev_steuerschluessel.json`` (Quelle und Stand dort).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATEI = Path(__file__).parent / "tabellen" / "datev_steuerschluessel.json"
_KONTEN = Path(__file__).parent / "tabellen" / "skr03_steuerkonten.json"
FAELLE = ("inland", "ige", "13b", "ausland")
FALL_TEXT = {"inland": "Inland", "ige": "innergemeinschaftlicher Erwerb", "13b": "Reverse Charge (§ 13b UStG)",
             "ausland": "ausländische Umsatzsteuer (keine deutsche Vorsteuer)",
             "sonder": "Sonderfall (Dreiecksgeschäft, Umsatzsteuerlager)"}
EU_LAENDER = {"AT", "BE", "BG", "CY", "CZ", "DK", "EE", "EL", "GR", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT",
              "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "XI"}
_IGE_HINWEIS = re.compile(r"(?i)innergemeinschaftliche\s+lieferung|art\.?\s*138|§\s*4\s*nr\.?\s*1\s*b|intra-community\s+supply")


@dataclass(frozen=True)
class Automatik:
    fall: str
    satz: Decimal | None
    text: str


@dataclass(frozen=True)
class Steuer:
    bu: str  # leer: kein Schlüssel (Automatikkonto oder ohne Vorsteuer)
    text: str
    satz: Decimal | None  # deutscher Steuersatz der Buchung
    automatik: bool
    hinweis: str | None  # Widerspruch: senkt die Sicherheit, wird in der Oberfläche markiert

    def oeffentlich(self) -> dict[str, Any]:
        return {"bu": self.bu, "text": self.text, "satz": None if self.satz is None else str(self.satz),
                "automatik": self.automatik, "hinweis": self.hinweis}


@lru_cache(maxsize=1)
def _tabelle() -> dict[str, dict[str, dict[str, str]]]:
    data: dict[str, dict[str, dict[str, str]]] = json.loads(_DATEI.read_text(encoding="utf-8"))["schluessel"]
    return data


def _satz_text(satz: Decimal) -> str:
    return str(satz.quantize(Decimal(1))) if satz == satz.to_integral_value() else str(satz.normalize())


def automatik(konto: dict[str, Any]) -> Automatik | None:
    """Steuerfall und Satz eines Automatikkontos aus der DATEV-Kontenbezeichnung."""
    if konto.get("kennzeichen") != "AV":
        return None
    name = konto.get("name", "")
    m = re.search(r"(\d{1,2}(?:,\d)?)\s*%\s*(?:Vorsteuer|VSt)", name)
    satz = Decimal(m.group(1).replace(",", ".")) if m else None
    if re.search(r"(?i)dreiecksgesch|umsatzsteuerlager|ust-lager|§\s*13a", name):
        fall = "sonder"
    elif re.search(r"(?i)innergemeinschaftliche[mnr]?\s+erwerb", name):
        fall = "ige"
    elif re.search(r"Vorsteuer\s+und\s+\d{1,2}\s*%\s*Umsatzsteuer", name) or re.search(r"(?i)§\s*13b", name):
        fall = "13b"
    else:
        fall = "inland"
    text = (f"{_satz_text(satz).replace('.', ',')} % Vorsteuer" if satz is not None else "Vorsteuer") + ("" if fall == "inland" else f", {FALL_TEXT[fall]}")
    return Automatik(fall, satz, text)


def steuerfall(reverse_charge: bool, herkunft: str | None, text: str, saetze: list[Decimal | None]) -> str:
    """Inland, i. g. Erwerb, § 13b oder ausländische Umsatzsteuer.

    - Rechnung aus dem Ausland ohne Steuer: § 13b, auch wenn der Hinweis fehlt (B2B-Leistung, Ort im Inland).
    - Rechnung aus dem Ausland mit Steuer (z. B. österreichische 20 %): ausländische Umsatzsteuer, in Deutschland
      nicht als Vorsteuer abziehbar; Erstattung nur über das Vorsteuer-Vergütungsverfahren."""
    ohne_steuer = bool(saetze) and all(s == 0 for s in saetze)
    auslaendisch = herkunft in ("eu", "drittland")
    if auslaendisch and not reverse_charge and not ohne_steuer:
        return "ausland"
    if not reverse_charge and not (auslaendisch and ohne_steuer):
        return "inland"
    if herkunft == "eu" and _IGE_HINWEIS.search(text or ""):
        return "ige"
    return "13b"


def herkunft_aus_ustid(ustid: str | None) -> str | None:
    if not ustid:
        return None
    land = re.sub(r"[^A-Z]", "", ustid.upper())[:2]
    if land == "DE":
        return "inland"
    return "eu" if land in EU_LAENDER else "drittland"


def bestimmen(konto: dict[str, Any] | None, satz_beleg: Decimal | None, fall: str) -> Steuer:
    if not konto:
        return Steuer("", "", None, False, None)
    nr = konto["nr"]
    auto = automatik(konto)
    if auto:
        hinweis = None
        if auto.fall != fall:
            hinweis = f"Konto {nr} ist ein Automatikkonto für {FALL_TEXT[auto.fall]}, die Rechnung ist {FALL_TEXT[fall]}"
        elif fall == "inland" and satz_beleg is not None and auto.satz is not None and satz_beleg != auto.satz:
            hinweis = f"Konto {nr} passt nicht zu {_satz_text(satz_beleg)} % Steuer (Automatik {auto.satz} %)"
        elif fall != "inland" and satz_beleg not in (None, Decimal(0)):
            hinweis = f"Rechnung weist {_satz_text(satz_beleg)} % Steuer aus, Konto {nr} erwartet Reverse Charge"
        return Steuer("", f"Automatik · {auto.text}", auto.satz, True, hinweis)

    if fall == "ausland":
        return Steuer("", "ausländische USt, keine deutsche Vorsteuer", None, False, None)
    if fall == "inland":
        if satz_beleg is None:
            return Steuer("", "", None, False, "Steuersatz fehlt")
        if satz_beleg == 0:
            return Steuer("", "ohne Vorsteuer", Decimal(0), False, None)
        eintrag = _tabelle()["inland"].get(_satz_text(satz_beleg))
        if not eintrag:
            return Steuer("", "", satz_beleg, False, f"Für {_satz_text(satz_beleg)} % gibt es keinen Steuerschlüssel")
        return Steuer(eintrag["bu"], eintrag["text"], satz_beleg, False, None)

    # i. g. Erwerb und § 13b: Die Rechnung weist 0 % aus; gebucht wird mit dem deutschen Satz (Regelsatz 19 %).
    satz = satz_beleg if satz_beleg in (Decimal(7), Decimal(19)) else Decimal(19)
    eintrag = _tabelle()[fall][_satz_text(satz)]
    zusatz = "" if satz_beleg == satz else " (Regelsatz angenommen)"
    return Steuer(eintrag["bu"], eintrag["text"] + zusatz, satz, False, None)


@lru_cache(maxsize=1)
def _steuerkonten() -> dict[str, dict[str, dict[str, str]]]:
    data: dict[str, dict[str, dict[str, str]]] = json.loads(_KONTEN.read_text(encoding="utf-8"))
    return data


def steuerkonten(fall: str, satz: Decimal | None) -> tuple[str | None, str | None]:
    """(Vorsteuerkonto, Umsatzsteuerkonto) im SKR03, die DATEV zu diesem Fall bebucht. Ohne Vorsteuer: (None, None)."""
    if satz is None or satz == 0:
        return None, None
    t = _steuerkonten()
    s = _satz_text(satz)
    return t["vorsteuer"].get(fall, {}).get(s), t["umsatzsteuer"].get(fall, {}).get(s)
