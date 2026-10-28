# Plan – Machbarkeitstest

Stand: 28.10.2026 · Grundlage: `CLAUDE.md` Abschnitt 9 (Phase „Test“), `docs/naechste-schritte.md` Schritt 2

## Ausgangslage
Vorhanden: LLMProvider-Schnittstelle (`backend/app/llm/`), Bedrock- und OpenAI-kompatibler Client, Pseudonymisierung (`backend/app/pseudo/`), SKR03-Kontenliste, KoSIT-Testsuite (XRechnung 3.0, UBL und CII) unter `testdaten/kosit/`, Python-Umgebung mit PyMuPDF, docTR, reportlab.
Es fehlen: Platzhalter-Anbieter, E-Rechnungs-Parser, Texterkennung, synthetische Belege, Goldstandard, Messskript, Bericht.

## Schritte
1. **Git:** `.gitignore`, erster Commit, Remote `sdai-belegautomatik` eintragen.
2. **Testbelege (30):**
   - 20 synthetische PDF-Rechnungen (`testdaten/synthetisch/`), davon 3 als schlechte Scans.
   - 10 KoSIT-XRechnungen (UBL). Sie laufen zweimal: direkt als XML (ohne KI) und als daraus erzeugte Sicht-PDF durch die KI.
   - Erwartete Ergebnisse als JSON in `testdaten/goldstandard/`.
3. **Pipeline** (`backend/scripts/machbarkeitstest.py`):
   Einlesen (XML → Parser, PDF mit Text → PyMuPDF, Scan → docTR) → Pseudonymisierung → LLMProvider → JSON nach festem Schema → Steuerlogik-Plausibilität (Netto + Steuer = Brutto).
4. **Anbieter:** `placeholder` (immer, ohne KI, regelbasiert), `bedrock`, `stackit_qwen`, `stackit_gptoss`, sobald Zugangsdaten in `.env` stehen.
5. **Auswertung** (`backend/scripts/auswertung.py`): Trefferquote je Feld und Anbieter, getrennt nach sauberen PDFs, Scans und XML; Kosten pro Beleg; Laufzeit. Ergebnis: `docs/machbarkeitstest-bericht.md`.
6. **Tests** (`backend/tests/`): Pseudonymisierung, Parser, Auswertung, Platzhalter-Anbieter.
7. **Doku:** Entscheidungen in `docs/entscheidungen/`, Eintrag in `docs/protokoll.md`.

## Messgrößen
Pflichtfelder: Lieferant, Rechnungsnummer, Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Belegart, Reverse Charge.
Positionen: Anzahl, Nettobetrag und Steuersatz je Position, Sachkonto SKR03 je Position.
Zielwert: mindestens 90 % korrekte Pflichtfelder bei sauberen PDFs (Abbruchkriterium Phase A).
