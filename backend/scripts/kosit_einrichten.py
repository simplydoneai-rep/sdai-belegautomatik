"""Richtet die offiziellen XRechnung-Prüfregeln der KoSIT ein (für ``app/erechnung/validierung.py``).

Lädt die Validator-Konfiguration für XRechnung 3.0.2 von GitHub (itplr-kosit, Apache-2.0), prüft die SHA-256-Prüfsumme
und entpackt sie nach ``tools/kosit/xrechnung-3.0.2``. Ausführen nach dem Klonen und bei jeder neuen Version
(URL und Prüfsumme hier anpassen, Entscheidung in docs/entscheidungen/ festhalten).

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/kosit_einrichten.py``
Python-Paket für die Ausführung der Regeln: ``saxonche`` (requirements.txt).
"""

from __future__ import annotations

import hashlib
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = ("https://github.com/itplr-kosit/validator-configuration-xrechnung/releases/download/v2026-08-31/"
       "xrechnung-3.0.2-validator-configuration-2026-08-31.zip")
SHA256 = "2530cd107c414511c5d0462ec10f886910395abfca820db82e83d70bf01221a8"
ZIEL = Path(__file__).resolve().parents[2] / "tools" / "kosit" / "xrechnung-3.0.2"


def main() -> None:
    with urllib.request.urlopen(URL, timeout=60) as antwort:  # noqa: S310 (feste HTTPS-Adresse)
        daten = antwort.read()
    pruefsumme = hashlib.sha256(daten).hexdigest()
    if pruefsumme != SHA256:
        sys.exit(f"Prüfsumme stimmt nicht ({pruefsumme}) – Datei nicht verwendet.")
    if ZIEL.exists():
        shutil.rmtree(ZIEL)
    ZIEL.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(daten)) as z:
        for eintrag in z.namelist():  # nur innerhalb des Zielordners entpacken
            if not (ZIEL / eintrag).resolve().is_relative_to(ZIEL.resolve()):
                sys.exit(f"Unzulässiger Pfad im Archiv: {eintrag}")
        z.extractall(ZIEL)
    print(f"KoSIT-Prüfregeln eingerichtet: {ZIEL}")


if __name__ == "__main__":
    main()
