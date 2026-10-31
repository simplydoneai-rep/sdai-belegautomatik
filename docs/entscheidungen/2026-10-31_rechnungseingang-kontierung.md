# Entscheidung: Rechnungseingang mit Kreditoren, Kontoauswahl und Ampel (Demo)

Datum: 31.10.2026 · Status: entschieden (Vorgaben Paul Graß)

## Vorgaben
1. Jeder Lieferant bekommt je Mandant eine feste Kreditorennummer im Bereich **70000–99999**, die vor der Freigabe angelegt werden muss.
2. Je Rechnungsposition eine Kontoauswahl mit **Vorschlägen** und **Suchfeld** nach Nummer oder Begriff („War“ → Wareneingang 7 %, 19 % …).
3. Hinter jeder Position eine **Ampel**: grün = sicher erkanntes Konto, gelb = unsicher, rot = frei.
4. Übersicht der **noch zu verbuchenden** Rechnungen mit Anzahl.
5. Gestaltung im Stil von iOS, so einfach, dass jeder es bedienen kann. Nur Rechnungsverarbeitung; Dashboard folgt später.

## Umsetzung
- **Kontenrahmen:** vollständiger DATEV-SKR03 2026 (Art.-Nr. 11174, BilRUG) aus der PDF eingelesen: 1.524 Konten mit Kennzeichen (AV, AM, S, F), `backend/app/kontierung/tabellen/skr03_vollstaendig.json`, Skript `backend/scripts/skr03_einlesen.py`. Reservierte Konten (R) ausgelassen.
- **Abgleich der Testkontenliste:** Konto **4610 gibt es im SKR03 2026 nicht mehr**, Werbekosten stehen auf **4600**. Testliste und Goldstandard angepasst; ältere KI-Antworten werden über `skr03_umschluessel.json` (4610 → 4600) abgebildet, damit die Messwerte vergleichbar bleiben.
- **Kreditoren:** je Mandant eigener Stamm, Vorschlag der nächsten freien Nummer, Prüfung von Bereich und Doppelvergabe, Nummer nach dem Anlegen fest. Bereich aus der Sachkontenlänge: bei 4-stelligen Sachkonten 5-stellige Kreditoren 70000–99999 (DATEV-Standard). Hinweis: Sechsstellige Kreditoren (700000–999999) gelten bei 5-stelligen Sachkonten; die Sachkontenlänge ist je Mandant hinterlegt und umstellbar.
- **Kontoauswahl:** Vorschläge aus KI (gewähltes Modell), Übereinstimmung der aufgezeichneten Modelle, Buchungen für denselben Kreditor, Standardkonto je Steuersatz. Suche über alle 1.524 Konten nach Nummer, Begriff und Alltagsbegriffen (`skr03_suchbegriffe.json`, z. B. „Kfz“ → Fahrzeug). Konten für Eingangsrechnungen (Klassen 3, 4, 0) zuerst.
- **Ampel je Position:**
  - grün: von Ihnen bestätigt, oder für diesen Kreditor schon gebucht, oder mindestens 3 von 5 Modellen einig, und jeweils das Konto passt zum Steuersatz
  - gelb: Vorschlag vorhanden, aber nicht abgesichert, oder Konto passt nicht zum Steuersatz (auch bei manueller Wahl, `CLAUDE.md` Regel 15)
  - rot: frei, noch kein Konto
  Die Übereinstimmung mehrerer Modelle nutzt in der Demo die vorhandenen Aufzeichnungen. Im Betrieb ersetzen Lernregeln und Buchungshistorie dieses Signal; ein zweiter KI-Aufruf nur zur Absicherung wäre möglich, kostet aber.
- **Freigabe:** nur mit Kreditor, mit Konto für jede Position und schlüssigen Summen. Nach der Freigabe merkt sich der Kreditor die gebuchten Konten (einfache Lernregel). Jede Änderung steht im Verlauf (nur ergänzt, nie geändert).
- **Eingang:** 32 synthetische Rechnungen und 10 KoSIT-E-Rechnungen (XML; die Sicht-PDFs sind dieselben Rechnungen und erscheinen nicht doppelt) plus eigene Uploads, sortiert nach Rechnungsdatum. Übersicht „Offene Positionen nach Sachkonto“ mit Anzahl und Summe.
- **Zustand:** `testdaten/demo/zustand.json` (nicht im Repository), zurücksetzbar. In Phase 0 ersetzt PostgreSQL mit Audit-Log diese Datei.

## Folgen
- Die Demo zeigt jetzt den ganzen Ablauf aus `CLAUDE.md`: Beleg rein → Vorschlag → Prüfung und Korrektur → Freigabe → (Lernen angedeutet). Es fehlt noch der DATEV-Export (Phase 4).
- Die Kreditorennummern sind Demo-Daten. Im Betrieb kommen sie aus dem DATEV-Kreditorenstamm des Mandanten (Stammdaten-Import, Phase 4).
