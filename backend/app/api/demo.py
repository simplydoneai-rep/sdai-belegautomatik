"""Demo-Webserver: Rechnungseingang mit Kontierung, Kreditoren und Freigabe. Nur lokal (127.0.0.1), nur Testbelege.

Start (aus ``backend/``): ``.venv/Scripts/python -m uvicorn app.api.demo:app --host 127.0.0.1 --port 8077``
oder Doppelklick auf ``demo_starten.bat`` im Projektordner.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from lxml import etree
from pydantic import BaseModel

from app.demo import ansicht, kanzlei, zustand
from app.demo.verarbeitung import MODELLE, aufzeichnungen, feldrahmen, positionsrahmen, seitenbilder
from app.erechnung.belegbild import belegbild
from app.erechnung.parser import ERechnungFehler
from app.kontierung.kontensuche import alle_konten, suchen

STATIC = Path(__file__).resolve().parents[1] / "demo" / "static"
MAX_UPLOAD = 15 * 1024 * 1024
log = logging.getLogger("demo")  # nur IDs, Status, Laufzeiten (CLAUDE.md Regel 7)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Texterkennung und Kontenliste vorladen, Eingang im Hintergrund lesen (Liste füllt sich nach und nach).
    from app.ocr.text import _predictor

    _predictor()
    aufzeichnungen()
    alle_konten()
    ansicht.liste()  # stößt das Lesen aller Belege im Hintergrund an
    yield


async def _nutzer_setzen(x_nutzer: str | None = Header(None), nutzer: str | None = None) -> str:
    """Demo ohne Anmeldung: Die Oberfläche schickt das Kürzel der gewählten Person mit (Phase 5: Anmeldung mit
    Zwei-Faktor). Asynchron, damit die Angabe in den Protokolleinträgen der Anfrage ankommt."""
    wer = x_nutzer or nutzer or "AK"  # Bilder (img src) schicken das Kürzel als Parameter
    zustand.NUTZER.set(wer)
    return wer


app = FastAPI(title="Simply Done AI – Belegautomatik (Demo)", lifespan=lifespan,
              dependencies=[Depends(_nutzer_setzen)])


@app.middleware("http")
async def kein_zwischenspeicher(request: Request, call_next: Any) -> Any:
    """Oberfläche nie aus dem Browser-Zwischenspeicher: nach einem Update sieht jeder sofort den neuen Stand."""
    antwort = await call_next(request)
    antwort.headers["Cache-Control"] = "no-store"
    return antwort


def _fehler(exc: Exception) -> HTTPException:
    return HTTPException(400, str(exc))


def _modell(modell: str) -> str:
    if modell not in MODELLE:
        raise HTTPException(400, "Unbekanntes Modell")
    return modell


def _key(key: str) -> str:
    beleg = next((b for b in ansicht.eingang() if b["key"] == key), None)
    if beleg is None:
        raise HTTPException(404, "Beleg nicht gefunden")
    _mandant(beleg["client_id"])
    return key


def _mandant(mid: str) -> str:
    """Sachbearbeiter sehen nur zugeordnete Mandanten (CLAUDE.md Abschnitt 3)."""
    if not kanzlei.darf(zustand.NUTZER.get(), mid):
        raise HTTPException(403, "Kein Zugriff auf diesen Mandanten")
    return mid


@app.get("/api/stammdaten")
def stammdaten() -> dict[str, Any]:
    return {
        **kanzlei.stammdaten(zustand.NUTZER.get()),
        "modelle": [{"id": k, **v} for k, v in MODELLE.items()],
        "standard_modell": ansicht.STANDARD_MODELL,
        "sachkontenlaenge": list(kanzlei.SACHKONTENLAENGE),
    }


@app.get("/api/eingang")
def eingang(mandant: str, modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.liste(_mandant(mandant), _modell(modell))


@app.get("/api/uebersicht")
def uebersicht(modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.uebersicht(zustand.NUTZER.get(), _modell(modell))


class MandantDaten(BaseModel):
    id: str | None = None
    name: str
    beraternummer: int | str | None = None
    nummer: int | str
    kontenrahmen: str
    sachkontenlaenge: int | str | None = None
    wj_beginn: int | str | None = None
    ansprechpartner: str = ""
    ustid: str | None = None
    zustaendig: str | None = None
    vertretung: str | None = None


class SachbearbeiterDaten(BaseModel):
    kuerzel: str
    name: str
    rolle: str = "sachbearbeitung"


class BeraterDaten(BaseModel):
    nr: int | str
    bezeichnung: str = ""
    standard: bool = False


class Zugriff(BaseModel):
    kuerzel: str
    mandant: str
    wert: str
    zustaendigkeit_anpassen: bool = False


def _kanzlei(aufruf: Any) -> dict[str, Any]:
    try:
        aufruf()
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise _fehler(exc) from exc
    return kanzlei.stammdaten(zustand.NUTZER.get())


@app.post("/api/kanzlei/mandant")
def mandant_speichern(m: MandantDaten) -> dict[str, Any]:
    return _kanzlei(lambda: kanzlei.mandant_speichern(zustand.NUTZER.get(), m.model_dump()))


@app.post("/api/kanzlei/sachbearbeiter")
def sachbearbeiter_speichern(s: SachbearbeiterDaten) -> dict[str, Any]:
    return _kanzlei(lambda: kanzlei.sachbearbeiter_speichern(zustand.NUTZER.get(), s.kuerzel, s.name, s.rolle))


@app.post("/api/kanzlei/beraternummer")
def beraternummer_speichern(b: BeraterDaten) -> dict[str, Any]:
    return _kanzlei(lambda: kanzlei.beraternummer_speichern(zustand.NUTZER.get(), b.nr, b.bezeichnung, b.standard))


@app.post("/api/kanzlei/beraternummer/entfernen")
def beraternummer_entfernen(b: BeraterDaten) -> dict[str, Any]:
    return _kanzlei(lambda: kanzlei.beraternummer_entfernen(zustand.NUTZER.get(), b.nr))


@app.post("/api/kanzlei/zugriff")
def zugriff_setzen(z: Zugriff) -> dict[str, Any]:
    return _kanzlei(lambda: kanzlei.zugriff_setzen(zustand.NUTZER.get(), z.kuerzel, z.mandant, z.wert,
                                                   z.zustaendigkeit_anpassen))


@app.get("/api/beleg")
def beleg(key: str, modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.ansicht(_key(key), _modell(modell))


@app.get("/api/beleg/seiten")
def beleg_seiten(key: str) -> dict[str, int]:
    return {"anzahl": len(seitenbilder(ansicht.pfad(_key(key))))}


@app.get("/api/beleg/seite")
def beleg_seite(key: str, i: int, dpi: int = 110) -> Response:
    seiten = seitenbilder(ansicht.pfad(_key(key)), 200 if dpi > 110 else 110)
    if not 0 <= i < len(seiten):
        raise HTTPException(404, "Seite nicht gefunden")
    return Response(seiten[i], media_type="image/png")


@app.get("/api/beleg/markierungen")
def beleg_markierungen(key: str, modell: str = ansicht.STANDARD_MODELL) -> list[list[dict[str, float]]]:
    """Fundstellen der Positionen im Beleg für die Hervorhebung beim Überfahren."""
    a = ansicht.ansicht(_key(key), _modell(modell))
    return positionsrahmen(ansicht.pfad(key), tuple(p["bezeichnung"] or "" for p in a["positionen"]))


@app.get("/api/beleg/feldrahmen")
def beleg_feldrahmen(key: str, modell: str = ansicht.STANDARD_MODELL) -> dict[str, dict[str, Any]]:
    """Fundstellen der Kopfangaben im Beleg (Lieferant, Mandant, Datum, Beträge, Zahlung …) für die Hervorhebung."""
    a = ansicht.ansicht(_key(key), _modell(modell))
    return feldrahmen(ansicht.pfad(key), ansicht.feldsuche(a))


@app.get("/api/beleg/belegbild")
def beleg_belegbild(key: str) -> dict[str, Any]:
    """Lesbares Belegbild einer E-Rechnung; das Original-XML bleibt unter /api/beleg/datei."""
    path = ansicht.pfad(_key(key))
    if path.suffix != ".xml":
        raise HTTPException(404, "Keine E-Rechnung (XML)")
    try:
        return belegbild(path)
    except (ERechnungFehler, etree.XMLSyntaxError) as exc:
        raise HTTPException(422, "E-Rechnung nicht lesbar") from exc


@app.get("/api/beleg/datei", response_model=None)
def beleg_datei(key: str) -> FileResponse | PlainTextResponse:
    path = ansicht.pfad(_key(key))
    if path.suffix == ".xml":
        return PlainTextResponse(path.read_text(encoding="utf-8"))
    return FileResponse(path)


@app.get("/api/konten")
def konten(q: str = "") -> list[dict[str, Any]]:
    return suchen(q)


class KontoWahl(BaseModel):
    key: str
    pos: int
    nr: str
    modell: str = ansicht.STANDARD_MODELL


class KreditorNeu(BaseModel):
    key: str
    nr: int
    name: str
    modell: str = ansicht.STANDARD_MODELL


class BelegAktion(BaseModel):
    key: str
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/beleg/konto")
def konto_waehlen(w: KontoWahl) -> dict[str, Any]:
    try:
        return ansicht.konto_waehlen(_key(w.key), w.pos, w.nr, _modell(w.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


class KreditorDaten(BaseModel):
    key: str
    ustid: str | None = None
    land: str | None = None
    modell: str = ansicht.STANDARD_MODELL


class PositionWert(BaseModel):
    key: str
    pos: int
    wert: str | None = None  # None = zurück zum Vorschlag
    modell: str = ansicht.STANDARD_MODELL


class Aufteilung(BaseModel):
    key: str
    pos: int
    teile: list[dict[str, str]] | None = None  # [] = keine Aufteilung, None = Vorschlag
    modell: str = ansicht.STANDARD_MODELL


@app.get("/api/steuerschluessel")
def steuerschluessel_liste() -> list[dict[str, Any]]:
    from app.kontierung.steuerschluessel import auswahl

    return auswahl()


@app.post("/api/beleg/steuerschluessel")
def steuerschluessel_waehlen(w: PositionWert) -> dict[str, Any]:
    try:
        return ansicht.steuerschluessel_waehlen(_key(w.key), w.pos, w.wert, _modell(w.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/steuersatz")
def steuersatz_waehlen(w: PositionWert) -> dict[str, Any]:
    try:
        return ansicht.steuersatz_waehlen(_key(w.key), w.pos, w.wert, _modell(w.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/aufteilung")
def aufteilen(a: Aufteilung) -> dict[str, Any]:
    try:
        return ansicht.aufteilen(_key(a.key), a.pos, a.teile, _modell(a.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/kreditor/daten")
def kreditor_daten(k: KreditorDaten) -> dict[str, Any]:
    try:
        return ansicht.kreditor_daten(_key(k.key), k.ustid, k.land, _modell(k.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/kreditor")
def kreditor_anlegen(k: KreditorNeu) -> dict[str, Any]:
    try:
        return ansicht.kreditor_anlegen(_key(k.key), k.nr, k.name, _modell(k.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/freigeben")
def freigeben(a: BelegAktion) -> dict[str, Any]:
    try:
        result = ansicht.freigeben(_key(a.key), _modell(a.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc
    log.info("freigegeben beleg=%s", result["id"])
    return result


@app.post("/api/beleg/wiedereroeffnen")
def wiedereroeffnen(a: BelegAktion) -> dict[str, Any]:
    try:
        return ansicht.wiedereroeffnen(_key(a.key), _modell(a.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


class Entfernen(BaseModel):
    key: str
    grund: str
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/beleg/entfernen")
def entfernen(e: Entfernen) -> dict[str, Any]:
    """Beleg aus der Bearbeitung nehmen (Original bleibt gespeichert, wiederherstellbar)."""
    try:
        return ansicht.entfernen(_key(e.key), e.grund, _modell(e.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/beleg/wiederherstellen")
def wiederherstellen(a: BelegAktion) -> dict[str, Any]:
    try:
        return ansicht.wiederherstellen(_key(a.key), _modell(a.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.get("/api/beleg/entfernen/gruende")
def entfern_gruende() -> list[str]:
    return list(zustand.ENTFERN_GRUENDE)


class Kurs(BaseModel):
    key: str
    wert: str | None = None
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/beleg/kurs")
def kurs_setzen(k: Kurs) -> dict[str, Any]:
    """Umrechnungskurs von Hand (1 Euro = Kurs Fremdwährung); leer = BMF-Monatskurs."""
    try:
        return ansicht.kurs_setzen(_key(k.key), k.wert, _modell(k.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


class ExportAuftrag(BaseModel):
    mandant: str
    monat: str
    modell: str = ansicht.STANDARD_MODELL


@app.get("/api/export/vorschau")
def export_vorschau(mandant: str, monat: str | None = None, modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.export_vorschau(_mandant(mandant), monat, _modell(modell))


@app.post("/api/export")
def exportieren(x: ExportAuftrag) -> Response:
    """DATEV-Buchungsstapel als CSV (Windows-1252). Die Datei bleibt als Exportstapel mit Hash gespeichert."""
    try:
        r = ansicht.exportieren(_mandant(x.mandant), x.monat, _modell(x.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc
    log.info("export mandant=%s monat=%s belege=%s", x.mandant, x.monat, r["export"]["anzahl"])
    return Response(r["daten"], media_type="text/csv; charset=windows-1252",
                    headers={"Content-Disposition": f'attachment; filename="{r["datei"]}"'})


@app.get("/api/export/datei")
def export_datei(mandant: str, id: str) -> Response:
    """Frühere Exportdatei erneut herunterladen (unverändert, Hash wird geprüft)."""
    import hashlib

    e = next((e for e in zustand.exporte(_mandant(mandant)) if e["id"] == id), None)
    if not e:
        raise HTTPException(404, "Export nicht gefunden")
    daten = (zustand.EXPORTE / e["datei"]).read_bytes()
    if hashlib.sha256(daten).hexdigest() != e["sha256"]:
        raise HTTPException(409, "Exportdatei wurde verändert")
    return Response(daten, media_type="text/csv; charset=windows-1252",
                    headers={"Content-Disposition": f'attachment; filename="{e["datei"]}"'})


class Sammel(BaseModel):
    keys: list[str]
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/sammelfreigabe")
def sammelfreigabe(s: Sammel) -> dict[str, Any]:  # jeder Schlüssel einzeln auf Zugriff geprüft (_key)
    result = ansicht.sammelfreigabe([_key(k) for k in s.keys], _modell(s.modell))
    log.info("sammelfreigabe freigegeben=%d uebersprungen=%d", len(result["freigegeben"]), len(result["uebersprungen"]))
    return result


class RegelSchalter(BaseModel):
    key: str
    regel: str
    aktiv: bool
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/regel/aktiv")
def regel_aktiv(r: RegelSchalter) -> dict[str, Any]:
    try:
        return ansicht.regel_aktiv(_key(r.key), r.regel, r.aktiv, _modell(r.modell))
    except ValueError as exc:
        raise _fehler(exc) from exc


@app.post("/api/demo/oktober")
def demo_oktober() -> dict[str, int]:
    return ansicht.demo_oktober()


@app.post("/api/demo/november")
def demo_november() -> dict[str, int]:
    return {"eingespielt": ansicht.demo_november()}


@app.post("/api/upload")
async def upload(datei: UploadFile = File(...), mandant: str = Form("M1")) -> dict[str, str]:
    _mandant(mandant)
    inhalt = await datei.read()
    if len(inhalt) > MAX_UPLOAD:
        raise HTTPException(413, "Datei zu groß (höchstens 15 MB)")
    try:
        key = ansicht.hochladen(inhalt, datei.filename or "beleg.pdf", mandant)
    except ValueError as exc:
        raise _fehler(exc) from exc
    return {"key": key}


@app.post("/api/demo/zuruecksetzen")
def zuruecksetzen() -> dict[str, str]:
    zustand.zuruecksetzen()
    kanzlei.zuruecksetzen()
    return {"status": "zurückgesetzt"}


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
