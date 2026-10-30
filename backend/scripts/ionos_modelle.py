"""Listet die Modellnamen, die der IONOS AI Model Hub für dieses Konto anbietet.

Braucht nur IONOS_API_KEY und IONOS_BASE_URL aus ``.env``. Es werden keine Belege gesendet.
Die passenden Namen danach als IONOS_MODEL_GPTOSS und IONOS_MODEL_QWEN in ``.env`` eintragen.

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/ionos_modelle.py``
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[2]


def main() -> None:
    load_dotenv(PROJECT / ".env")
    key, base = os.environ.get("IONOS_API_KEY"), os.environ.get("IONOS_BASE_URL", "")
    if not key or not base.startswith("https://"):
        sys.exit("IONOS_API_KEY oder IONOS_BASE_URL fehlt in .env")
    resp = httpx.get(f"{base.rstrip('/')}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if resp.status_code != 200:
        sys.exit(f"Fehler {resp.status_code} beim Abruf der Modellliste")
    for model in sorted(m.get("id", "") for m in resp.json().get("data", [])):
        hint = ""
        low = model.lower()
        if "gpt-oss-120b" in low:
            hint = "  <- IONOS_MODEL_GPTOSS"
        elif "qwen3.5-397b" in low:
            hint = "  <- IONOS_MODEL_QWEN"
        print(model + hint)


if __name__ == "__main__":
    main()
