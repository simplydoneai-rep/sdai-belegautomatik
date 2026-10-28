# Entscheidung: Python 3.14 für den Machbarkeitstest, Ziel bleibt 3.12

Datum: 28.10.2026 · Status: entschieden

## Kontext
`CLAUDE.md` legt Python 3.12 fest. Auf dem Entwicklungs-PC ist nur Python 3.14.7 installiert, und die virtuelle Umgebung `backend/.venv` mit allen Paketen (PyMuPDF, docTR, PyTorch) läuft bereits darauf.

## Entscheidung
Der Machbarkeitstest läuft mit Python 3.14. Der Code nutzt keine Sprachmerkmale nach 3.12 (`requires-python = ">=3.12"` in `backend/pyproject.toml`). Ab Phase 0 laufen Docker-Image und CI auf Python 3.12; dort wird die Kompatibilität geprüft.

## Begründung
Eine zweite Python-Version nur für den Test kostet Einrichtungszeit ohne Nutzen für die Messwerte.

## Offen
`mypy --strict` ist noch nicht installiert; wird mit Phase 0 (CI) eingerichtet.
