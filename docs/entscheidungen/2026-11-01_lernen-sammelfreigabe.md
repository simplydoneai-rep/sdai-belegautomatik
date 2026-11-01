# Entscheidung: Lernen aus Freigaben, Bereich „Sicher“ und Sammelfreigabe (Demo)

Datum: 01.11.2026 · Status: entschieden (Wunsch Paul Graß)

## Ausgangslage
Wunsch: Rechnungen bekannter Lieferanten sollen im Folgemonat schon fertig vorkontiert sein, sodass man sie „nur noch angucken“ muss. Bedingung: Die volle Kontrolle über die Belegverarbeitung bleibt; man kann jederzeit nachsehen und ändern.

## Entscheidung
1. **Lernen je Position, je Mandant und Kreditor** (`backend/app/lernen/regeln.py`). Eine Regel ist ein Fingerabdruck der Position: Kernbegriffe der Bezeichnung (ohne Zahlen, Einheiten, Füllwörter und Zeitangaben wie Monatsnamen) + Steuersatz → Sachkonto. Ähnlichkeit nach Jaccard, Schwelle 0,5. Nie mandantenübergreifend (`CLAUDE.md` Regel 8).
2. **Wann eine Regel sicher ist** (`CLAUDE.md` Abschnitt 5): Wurde der Vorschlag nie korrigiert, reicht eine Freigabe. Nach einer Korrektur braucht die Regel 3 gleiche Bestätigungen. Jede Korrektur setzt die Zählung zurück.
3. **Reihenfolge der Vorschläge:** Lernregel vor KI. Die Steuerlogik prüft immer, auch gelernte Konten (Regel 15).
4. **Drei Bereiche in der Eingangsliste:**
   - **Sicher:** Kreditor bekannt, jede Position grün, Belegsicherheit ≥ 0,80, keine Ausnahme.
   - **Prüfen:** alles andere, mit genanntem Grund.
   - **Erledigt:** freigegeben.
5. **Feste Ausnahmen**, die immer zur Prüfung gehen, egal wie sicher die Konten sind: neuer Lieferant, Gutschrift, Reverse Charge, Anzahlung/Schlussrechnung, fehlende Rechnungsnummer über 250 €, Summen widersprüchlich, Betrag mehr als doppelt so hoch wie das bisherige Maximum dieses Kreditors.
6. **Sammelfreigabe** nur für den Bereich „Sicher“. Ein Blatt zeigt jede Rechnung mit Betrag; einzelne lassen sich abwählen oder ansehen. Der Server prüft jeden Beleg beim Freigeben erneut und überspringt alles, was nicht mehr sicher ist.
7. **Kein automatisches Buchen:** Auch sichere Rechnungen brauchen einen Klick (`CLAUDE.md` Regel 12).

## Kontrolle bleibt beim Menschen
- **Regeln einsehen und abschalten:** In der Kreditor-Karte stehen alle gelernten Regeln mit Konto, Zahl der Bestätigungen und letztem Datum. Ein Schalter je Regel; eine abgeschaltete Regel schickt den Beleg sofort zur Prüfung mit dem Grund „Gelernte Regel ist abgeschaltet“.
- **Wieder öffnen:** Eine Freigabe lässt sich zurücknehmen. Was diese Freigabe gelernt hat, wird ebenfalls zurückgenommen (Zustand der Regel vor der Freigabe wird am Beleg gespeichert).
- **Protokoll:** Jede Freigabe, jede gelernte oder korrigierte Regel und jedes Ab- und Einschalten steht im append-only Protokoll mit Quelle (Sachbearbeiter, Sammelfreigabe, Demo-Szenario).

## Demo-Szenario
Menü „Demo“ unten links:
1. **Oktober als gebucht übernehmen:** legt die Kreditoren an und gibt die 32 synthetischen Oktoberbelege mit den Konten aus dem Goldstandard frei (wie eine Buchung durch Sachbearbeiter).
2. **Belege November einspielen:** 17 neue Rechnungen derselben Lieferanten (`backend/scripts/folgemonat.py`, `testdaten/folgemonat/`). Ergebnis: 12 sicher vorkontiert, 5 zur Prüfung (neue Positionsart, Gutschrift, Reverse Charge, neuer Lieferant, ungewöhnlich hoher Betrag).
3. **Zurücksetzen.**

## Geprüft
- `tests/test_lernen.py` (Fingerabdruck, Sicherheit, Korrektur, Abschalten, Rückgängig, Monatswechsel) und `tests/test_demo.py::test_folgemonat_ist_vorkontiert_und_bleibt_kontrollierbar`.
- Im Browser: Sicher 12 / Prüfen 15 / Erledigt 32 nach dem Einspielen; Regel ab- und einschalten; Sammelfreigabe mit einer abgewählten Rechnung (11 freigegeben); Wieder öffnen setzt die Regel von 2× auf 1× bestätigt zurück.

## Später (Phase 3)
Regeln in PostgreSQL (`rule`), Import der DATEV-Buchungshistorie als Startwissen, Branchen-Regelwerk für neue Mandanten, automatische Freigabe nur pro Mandant einschaltbar (Phase 6).
