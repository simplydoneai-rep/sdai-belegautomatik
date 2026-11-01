"""Demo-Webserver: Rechnungseingang mit Kontierung, Kreditoren und Freigabe. Nur lokal (127.0.0.1), nur Testbelege.

Start (aus ``backend/``): ``.venv/Scripts/python -m uvicorn app.api.demo:app --host 127.0.0.1 --port 8077``
oder Doppelklick auf ``demo_starten.bat`` im Projektordner.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.demo import ansicht, zustand
from app.demo.verarbeitung import MODELLE, aufzeichnungen, mandanten, seitenbilder
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


app = FastAPI(title="Simply Done AI – Belegautomatik (Demo)", lifespan=lifespan)


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
    if key not in {b["key"] for b in ansicht.eingang()}:
        raise HTTPException(404, "Beleg nicht gefunden")
    return key


@app.get("/api/stammdaten")
def stammdaten() -> dict[str, Any]:
    lo, hi = zustand.kreditor_bereich(ansicht.SACHKONTENLAENGE)
    return {
        "mandanten": [{"id": k, "name": v["name"], "branche": v["branche"]} for k, v in mandanten().items()],
        "modelle": [{"id": k, **v} for k, v in MODELLE.items()],
        "standard_modell": ansicht.STANDARD_MODELL,
        "kreditoren_bereich": [lo, hi],
    }


@app.get("/api/eingang")
def eingang(mandant: str | None = None, modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.liste(mandant or None, _modell(modell))


@app.get("/api/beleg")
def beleg(key: str, modell: str = ansicht.STANDARD_MODELL) -> dict[str, Any]:
    return ansicht.ansicht(_key(key), _modell(modell))


@app.get("/api/beleg/seiten")
def beleg_seiten(key: str) -> dict[str, int]:
    return {"anzahl": len(seitenbilder(ansicht.pfad(_key(key))))}


@app.get("/api/beleg/seite")
def beleg_seite(key: str, i: int) -> Response:
    seiten = seitenbilder(ansicht.pfad(_key(key)))
    if not 0 <= i < len(seiten):
        raise HTTPException(404, "Seite nicht gefunden")
    return Response(seiten[i], media_type="image/png")


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


class Sammel(BaseModel):
    keys: list[str]
    modell: str = ansicht.STANDARD_MODELL


@app.post("/api/sammelfreigabe")
def sammelfreigabe(s: Sammel) -> dict[str, Any]:
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
    if mandant not in mandanten():
        raise HTTPException(400, "Unbekannter Mandant")
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
    return {"status": "zurückgesetzt"}


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
