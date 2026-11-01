"""Validierung von E-Rechnungen mit den offiziellen Prüfregeln der KoSIT (XRechnung 3.0, EN 16931).

Ablauf wie im KoSIT-Validator (https://github.com/itplr-kosit/validator), gesteuert über dessen Konfiguration
``scenarios.xml``:
1. Szenario wählen (XPath ``match``, z. B. CustomizationID = XRechnung 3.0 in UBL oder CII).
2. XML-Schema prüfen (UBL 2.1 bzw. CII D16B) mit lxml.
3. Schematron-Regeln ausführen (EN 16931 und XRechnung, als XSLT kompiliert) mit Saxon (saxonche, ohne Java).

Ergebnis: gültig, wenn das Schema passt und keine Regel mit ``flag="fatal"``/``"error"`` verletzt ist.
Warnungen werden angezeigt, machen die Rechnung aber nicht ungültig.

Die Konfiguration liegt in ``tools/kosit/`` (eingerichtet mit ``backend/scripts/kosit_einrichten.py``),
der Ordner ist über ``KOSIT_KONFIG`` änderbar. Läuft vollständig lokal; keine Rechnungsdaten verlassen den Rechner.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from lxml import etree

PROJEKT = Path(__file__).resolve().parents[3]
STANDARD_KONFIG = PROJEKT / "tools" / "kosit" / "xrechnung-3.0.2"
_SZ = "{http://www.xoev.de/de/validator/framework/1/scenarios}"
_SVRL = "{http://purl.oclc.org/dsdl/svrl}"
_FEHLER_FLAGS = {"fatal", "error"}
_LOCK = threading.Lock()  # Saxon-Prozessor wird von mehreren Threads genutzt
_KLARTEXT = Path(__file__).parent / "tabellen" / "xrechnung_klartext.json"
# Rechnungen von außen: keine externen Entitäten, kein Netzzugriff (Schutz vor XXE, DSGVO Art. 32)
_SICHER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)


@dataclass
class Szenario:
    name: str
    namespaces: dict[str, str]
    match: str
    schema: Path | None
    schematron: list[Path] = field(default_factory=list)


def konfig() -> Path:
    return Path(os.environ.get("KOSIT_KONFIG") or STANDARD_KONFIG).resolve()


def verfuegbar() -> bool:
    return (konfig() / "scenarios.xml").exists()


@lru_cache(maxsize=1)
def _szenarien() -> tuple[str, list[Szenario]]:
    wurzel = konfig()
    doc = etree.parse(str(wurzel / "scenarios.xml"))
    titel = f'{doc.findtext(f"{_SZ}name")} · KoSIT-Konfiguration vom {doc.findtext(f"{_SZ}date")}'
    out = []
    for s in doc.getroot().iter(f"{_SZ}scenario"):
        schema = s.find(f"{_SZ}validateWithXmlSchema/{_SZ}resource/{_SZ}location")
        out.append(Szenario(
            name=s.findtext(f"{_SZ}name") or "",
            namespaces={n.get("prefix"): (n.text or "").strip() for n in s.findall(f"{_SZ}namespace")},
            match=(s.findtext(f"{_SZ}match") or "").strip(),
            schema=wurzel / schema.text.strip() if schema is not None and schema.text else None,
            schematron=[wurzel / (r.text or "").strip()
                        for r in s.findall(f"{_SZ}validateWithSchematron/{_SZ}resource/{_SZ}location")]))
    return titel, out


@lru_cache(maxsize=1)
def _saxon() -> Any:
    from saxonche import PySaxonProcessor

    return PySaxonProcessor(license=False)


@lru_cache(maxsize=None)
def _xslt(pfad: Path) -> Any:
    return _saxon().new_xslt30_processor().compile_stylesheet(stylesheet_file=str(pfad))


@lru_cache(maxsize=None)
def _xsd(pfad: Path) -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(pfad)))


def _ort(xpath: str | None) -> str:
    """XPath aus dem Prüfbericht lesbar kürzen: /*:Invoice[namespace-uri()='…'][1]/*:AccountingSupplierParty[1] → …"""
    if not xpath:
        return ""
    kurz = re.sub(r"\[namespace-uri\(\)='[^']*'\]|Q\{[^}]*\}", "", xpath).replace("*:", "")
    return re.sub(r"\[1\]", "", kurz)


@lru_cache(maxsize=1)
def _tabelle() -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = json.loads(_KLARTEXT.read_text(encoding="utf-8"))
    return data


def klartext(regel: str, text: str) -> str:
    """Verständliche deutsche Meldung für Sachbearbeiter. Reihenfolge: feste Übersetzung der Regel,
    Regelfamilie (z. B. Nachkommastellen, Steuerkategorie), sonst aus den genannten Feldern (BT/BG) abgeleitet."""
    t = _tabelle()
    if regel in t["regeln"]:
        return t["regeln"][regel]
    kennungen = re.findall(r"\b(B[TG]-\d+)\b", text)
    felder = [k for k in kennungen if k.startswith("BT")] or kennungen  # Felder vor Gruppen nennen
    begriffe = list(dict.fromkeys(t["begriffe"][k] for k in felder if k in t["begriffe"]))[:3]
    liste = ", ".join(begriffe) or "mehrere Angaben"
    for familie in sorted(t["familien"], key=len, reverse=True):
        if regel == familie or regel.startswith(familie + "-"):
            return t["familien"][familie].format(begriffe=liste)
    if not begriffe:
        return "Formfehler in der E-Rechnung."
    if "=" in text or re.search(r"(?i)\bsum\b|summe", text):
        return f"Rechenfehler bei: {liste}."
    if re.search(r"(?i)shall (have|contain|be provided|specify)|must be|muss .*übermittelt|muss .*enthalten", text):
        return f"Angabe fehlt oder ist unvollständig: {liste}."
    return f"Angabe fehlerhaft: {liste}."


def _szenario_fuer(pfad: Path) -> Szenario | None:
    sx = _saxon()
    knoten = sx.parse_xml(xml_file_name=str(pfad))
    for sz in _szenarien()[1]:
        xp = sx.new_xpath_processor()
        for prefix, uri in sz.namespaces.items():
            xp.declare_namespace(prefix, uri)
        xp.set_context(xdm_item=knoten)
        if xp.effective_boolean_value(sz.match):
            return sz
    return None


def validiere(pfad: Path) -> dict[str, Any]:
    """Prüft eine E-Rechnung (XML) gegen Schema und Schematron-Regeln. Gibt nie Belegtexte in Logs aus."""
    if not verfuegbar():
        return {"verfuegbar": False, "gueltig": None, "regelwerk": None, "szenario": None,
                "fehler": [], "warnungen": [], "hinweis": "Prüfregeln der KoSIT nicht eingerichtet (scripts/kosit_einrichten.py)"}
    pfad = pfad.resolve()
    titel = _szenarien()[0]
    if re.search(rb"<!DOCTYPE|<!ENTITY", pfad.read_bytes()[:4096]):  # E-Rechnungen haben nie eine DTD
        return {"verfuegbar": True, "gueltig": False, "regelwerk": titel, "szenario": None, "warnungen": [],
                "fehler": [{"regel": "XML-Schema", "text": "DTD bzw. Entitäten sind in E-Rechnungen nicht zulässig.",
                            "ort": "", "klartext": "Die Datei enthält unzulässige Steueranweisungen und wird nicht geöffnet."}]}
    with _LOCK:
        sz = _szenario_fuer(pfad)
        if sz is None:
            kennung = re.search(rb"CustomizationID[^>]*>([^<]{0,160})<|GuidelineSpecifiedDocumentContextParameter>\s*<[^>]*ID>([^<]{0,160})<",
                                pfad.read_bytes())
            text = (kennung.group(1) or kennung.group(2)).decode("utf-8", "replace") if kennung else "nicht angegeben"
            return {"verfuegbar": True, "gueltig": False, "regelwerk": titel, "szenario": None, "warnungen": [],
                    "fehler": [{"regel": "Szenario", "text": f"Keine XRechnung 3.0 (Kennung: {text}). Es gibt kein passendes "
                                "Prüfszenario; die Rechnung ist keine gültige XRechnung im Sinne der aktuellen Version.",
                                "ort": "CustomizationID", "klartext": klartext("Szenario", "")}]}
        fehler: list[dict[str, str]] = []
        warnungen: list[dict[str, str]] = []
        if sz.schema:
            schema = _xsd(sz.schema)
            if not schema.validate(etree.parse(str(pfad), _SICHER)):
                fehler += [{"regel": "XML-Schema", "text": e.message, "ort": f"Zeile {e.line}"}
                           for e in list(schema.error_log)[:20]]
        for xsl in sz.schematron:
            svrl = etree.fromstring(_xslt(xsl).transform_to_string(source_file=str(pfad)).encode("utf-8"))
            for fa in list(svrl.iter(f"{_SVRL}failed-assert")) + list(svrl.iter(f"{_SVRL}successful-report")):
                eintrag = {"regel": fa.get("id") or "", "text": " ".join((fa.findtext(f"{_SVRL}text") or "").split()),
                           "ort": _ort(fa.get("location"))}
                (fehler if (fa.get("flag") or "fatal").lower() in _FEHLER_FLAGS else warnungen).append(eintrag)
    for e in fehler + warnungen:
        e["klartext"] = klartext(e["regel"], e["text"])
    return {"verfuegbar": True, "gueltig": not fehler, "regelwerk": titel, "szenario": sz.name,
            "fehler": fehler, "warnungen": warnungen}
