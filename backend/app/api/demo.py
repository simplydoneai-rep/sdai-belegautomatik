"""Demo-Webserver: Beleg rein → Buchungsvorschlag raus. Nur lokal (127.0.0.1), nur Testbelege.

Start (aus ``backend/``): ``.venv/Scripts/python -m uvicorn app.api.demo:app --host 127.0.0.1 --port 8077``
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from app.demo.verarbeitung import (MODELLE, TESTDATEN, aufzeichnungen, mandanten, seitenbilder, testbelege,
                                  verarbeite, verarbeite_upload)

STATIC = Path(__file__).resolve().parents[1] / "demo" / "static"
MAX_UPLOAD = 15 * 1024 * 1024
log = logging.getLogger("demo")  # nur IDs, Status, Laufzeiten (CLAUDE.md Regel 7)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Texterkennung vorladen, damit der erste Scan in der Vorführung nicht 15 s braucht.
    from app.ocr.text import _predictor

    _predictor()
    aufzeichnungen()
    yield


app = FastAPI(title="Simply Done AI – Belegautomatik (Demo)", lifespan=lifespan)


@app.get("/api/stammdaten")
def stammdaten() -> dict[str, Any]:
    return {
        "mandanten": [{"id": k, "name": v["name"], "branche": v["branche"]} for k, v in mandanten().items()],
        "modelle": [{"id": k, **v} for k, v in MODELLE.items()],
        "testbelege": [{"nr": i, "id": b["id"], "datei": b["datei"], "art": b["art"], "client_id": b["client_id"],
                        "merkmale": b["merkmale"]} for i, b in enumerate(testbelege())],
    }


def _beleg(nr: int) -> dict[str, Any]:
    belege = testbelege()
    if not 0 <= nr < len(belege):
        raise HTTPException(404, "Testbeleg nicht gefunden")
    return belege[nr]


@app.get("/api/testbelege/{nr}/datei", response_model=None)
def testbeleg_datei(nr: int) -> FileResponse | PlainTextResponse:
    path = TESTDATEN / _beleg(nr)["datei"]
    if path.suffix == ".xml":
        return PlainTextResponse(path.read_text(encoding="utf-8"))
    return FileResponse(path)


@app.get("/api/testbelege/{nr}/seiten")
def testbeleg_seiten(nr: int) -> dict[str, int]:
    return {"anzahl": len(seitenbilder(TESTDATEN / _beleg(nr)["datei"]))}


@app.get("/api/testbelege/{nr}/seite/{i}")
def testbeleg_seite(nr: int, i: int) -> Response:
    seiten = seitenbilder(TESTDATEN / _beleg(nr)["datei"])
    if not 0 <= i < len(seiten):
        raise HTTPException(404, "Seite nicht gefunden")
    return Response(seiten[i], media_type="image/png")


@app.post("/api/testbelege/{nr}/verarbeiten")
def testbeleg_verarbeiten(nr: int, modell: str = Form("ionos_qwen")) -> dict[str, Any]:
    b = _beleg(nr)
    if modell not in MODELLE:
        raise HTTPException(400, "Unbekanntes Modell")
    result = verarbeite(TESTDATEN / b["datei"], b["client_id"], modell, b["erwartet"])
    log.info("beleg=%s modell=%s ampel=%s", b["id"], modell, result["ampel"])
    return result


@app.post("/api/upload")
async def upload(datei: UploadFile = File(...), mandant: str = Form("M1"),
                 modell: str = Form("ionos_qwen")) -> dict[str, Any]:
    if mandant not in mandanten() or modell not in MODELLE:
        raise HTTPException(400, "Unbekannter Mandant oder unbekanntes Modell")
    content = await datei.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "Datei zu groß (höchstens 15 MB)")
    try:
        result = verarbeite_upload(content, datei.filename or "beleg.pdf", mandant, modell)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    log.info("upload modell=%s ampel=%s", modell, result["ampel"])
    return result


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
