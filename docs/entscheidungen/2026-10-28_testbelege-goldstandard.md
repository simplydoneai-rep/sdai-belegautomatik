# Entscheidung: Zusammensetzung der 30 Testbelege und des Goldstandards

Datum: 28.10.2026 · Status: entschieden

## Entscheidung
- **20 synthetische Rechnungen** (17 PDF mit Text, 3 Scans) von erfundenen Firmen, erzeugt per Skript (`backend/scripts/erzeuge_testbelege.py`), damit sie jederzeit reproduzierbar sind.
- **10 KoSIT-XRechnungen** aus der offiziellen Testsuite (`testdaten/kosit/`, XRechnung 3.0), ausgewählt nach Vielfalt: 0/7/19 %, gemischt, Reverse Charge (AE), viele Positionen, Zu- und Abschläge, negative Mengen. Jeder Fall läuft als UBL, als CII und als daraus erzeugte Sicht-PDF.
- Erfundene Kennungen sind erkennbar unecht: USt-IdNr. `DE999…`/`ATU999…`, IBAN mit Bankleitzahl `99999999`, BIC `TESTDEFFXXX`.
- **Sollkontierung SKR03** nur bei den synthetischen Belegen. Die KoSIT-Positionen („Produkt 1“ usw.) lassen keine fachlich sinnvolle Kontierung zu.
- Die Platzhalter-Lieferantennamen der KoSIT-Dateien („[Seller name]“) werden in den Sicht-PDFs durch erfundene Firmennamen ersetzt, sonst würde die KI sie für unsere eigenen Platzhalter halten.
- Kontierung der synthetischen Positionen: Lebensmittel 7 % → 3300, Waren/Material 19 % → 3400, Bauleistung § 13b → 3120, innergemeinschaftlicher Erwerb → 3425 (neu in `skr03_konten.json`), sonst die passenden Aufwandskonten (4240, 4250, 4610, 4806, 4910, 4920, 4930, 4940, 4964, 4980).
- Je Beleg eine Liste **sensibler Werte**, mit der die Pseudonymisierung bei jedem Lauf geprüft wird.

## Begründung
`CLAUDE.md` Regel 1 (nur synthetische Daten) und Phasenplan „Test“ (30 Belege, KoSIT plus eigene PDFs und Scans).

## Offene Punkte
- Kontierung 3425/3120 im Abgleich mit der offiziellen DATEV-SKR03-Liste bestätigen (`skr03_konten.json`, Feld `quelle`).
- Für Phase B mindestens 200 Belege aus vielen verschiedenen Vorlagen.
