# Entscheidung: Dashboard, Rechte, Steuerschlüssel, Leistungsdatum, Währung und Belegansicht (Demo)

Datum: 01.11.2026 · Status: entschieden (Vorgaben Paul Graß)

## 1. Steuerschlüssel nach DATEV-Logik
- Jede Position bekommt neben dem Konto ihren Steuerschlüssel, deterministisch aus Konto, Steuersatz und Steuerfall (`backend/app/kontierung/steuerschluessel.py`, Tabelle `tabellen/datev_steuerschluessel.json`, Recherche `docs/recherche/2026-11-01_datev-steuerschluessel.md`).
- **Automatikkonten** (AV, z. B. 3400) bekommen keinen Schlüssel; das Programm prüft, ob Satz und Fall des Kontos zur Rechnung passen. **Konten ohne Automatik** (z. B. 4980, 4250) bekommen 9 (19 %) oder 8 (7 %), bei i. g. Erwerb 19/18, bei § 13b 94/91.
- Korrektur zur Vorgabe: „7 für 7 %“ wäre falsch, DATEV-Schlüssel 7 ist Vorsteuer 16 %. „19“ gilt für den innergemeinschaftlichen **Erwerb** (Einkauf), nicht für Lieferungen.
- Steuerfall (Inland, i. g. Erwerb, § 13b) aus Reverse-Charge-Hinweis und Herkunft des Lieferanten (USt-IdNr.). Rechnungen aus dem Ausland ohne deutsche Steuer gelten als § 13b, auch ohne Hinweis.
- Neuer Abschnitt **Buchungssätze** je Beleg wie im DATEV-Buchungsstapel: Umsatz, Soll/Haben, Konto, Gegenkonto (Kreditor), BU, Belegdatum, Leistungsdatum, Belegfeld 1. Eine Zeile je Konto und Schlüssel. Umsatz brutto im Inland, netto bei § 13b und i. g. Erwerb, Gutschrift im Haben.

## 2. Leistungsdatum und Währung
- **Leistungsdatum oder -zeitraum** (§ 14 Abs. 4 Nr. 6 UStG, wichtig für Soll- und Istversteuerung) wird lokal aus dem Belegtext gelesen, ohne KI (`backend/app/ocr/kopfangaben.py`): „Leistungsdatum 03.11.2026“, „Leistungszeitraum 01.10.–31.10.2026“, „Oktober 2026“, „26. Oktober 2026“, „Service period November 2, 2026“, „Leistungsdatum entspricht Rechnungsdatum“. Bei E-Rechnungen aus BT-72/73/74. Fehlt es (über 250 €), geht der Beleg zur Prüfung.
- **Währung** aus KI bzw. E-Rechnung, abgesichert durch Währungszeichen im Text. Fremdwährung geht zur Prüfung („Umrechnung in Euro nötig“); Beträge werden in der Belegwährung angezeigt.
- Angezeigt in Liste, Kopf, Rechnungsdaten, Buchungssätzen und Sammelfreigabe.
- Zwei neue Testrechnungen: F18 USA in US-Dollar (§ 13b, BU 94), F19 Niederlande (i. g. Erwerb).

## 3. Belegverarbeitung: Gestaltung
- Drei Spalten mit eigenem Hintergrund (Eingang grau, Rechnung hellgrau mit weißen Karten, Beleg dunkler).
- Jeder Abschnitt ist eine eigene Karte mit farbigem Symbol im iOS-Stil: Rechnung (Kopf mit Fakten: Rechnungsdatum, Leistungsdatum, Währung, Steuerfall), Kreditor, Positionen und Konten, Buchungssätze, Rechnungsdaten. Auffällige Fakten (Fremdwährung, § 13b, fehlendes Leistungsdatum) hellorange.
- **Entfernt** aus der Sachbearbeiter-Ansicht: „Verarbeitung und KI“, „Was ging an die KI?“ und die Zeile „Steuerlogik“. Diese Angaben dienten der Nachvollziehbarkeit in der Demo, helfen beim Buchen aber nicht. Die Summenprüfung steht als kurzer Haken unter dem Betrag („✓ Summen stimmen“).
- **Verlauf** bleibt erreichbar (GoBD, Nachvollziehbarkeit), aber als Knopf „Verlauf“ im Kopf, der ein Blatt öffnet; jetzt mit Person.
- **Kontofeld:** Ein Klick leert das Feld und öffnet sofort die Suche mit Vorschlägen. Ohne Auswahl (Esc, Klick daneben) bleibt das bisherige Konto.

## 4. Belegansicht
- Kopf zeigt „Seite 1 von 2“. Schwebende, leicht transparente Werkzeugleiste am rechten Rand (wie im Adobe Reader): Seitenzahl zum Eintippen, Seite hoch/runter, an Breite anpassen, Vergrößern/Verkleinern (50–300 %), Strg + Mausrad, Verschieben mit gedrückter Maustaste. Ab 125 % wird die Seite in höherer Auflösung geladen.

## 5. Dashboard, Mandanten, Sachbearbeiter, Rechte
- Neue Startseite **Übersicht**: Kacheln (offene Belege, sicher vorkontiert, zur Prüfung, Mandanten) und Mandantenliste mit Firmenname, Ansprechpartner, Mandantennummer, Kontenrahmen, Sachbearbeiter als Kürzel (voller Name beim Überfahren, Vertretung umrandet), offene Belege (davon sicher/prüfen) und betroffenem Monat (Belegdatum der offenen Belege).
- **Mandant erfassen/bearbeiten** (nur Kanzleileitung): Unternehmensname, Mandantennummer (1–99999, eindeutig), Kontenrahmen SKR03/SKR04, Ansprechpartner, Sachbearbeiter zuständig und Vertretung. SKR04 wird gespeichert; die Kontenliste der Demo ist noch SKR03 (Hinweis in der Belegverarbeitung).
- **Sachbearbeiter und Rechte** (nur Kanzleileitung): Sachbearbeiter mit Kürzel, Name, Rolle erfassen; je Mandant „Zugriff“, „Kein Zugriff“ oder „Gesperrt“ (darf nie zugeordnet werden). Zuständige und Vertretungen haben immer Zugriff. Mindestens eine Kanzleileitung bleibt.
- Der Server prüft den Zugriff bei jeder Anfrage (403), nicht nur die Oberfläche. Jede Änderung steht im Protokoll.
- Demo ohne Anmeldung: Person oben rechts wählen. Anmeldung mit Zwei-Faktor folgt in Phase 5.

## 6. Frage: Ein Mandant oder alle in der Belegverarbeitung?
**Entscheidung: Die Belegverarbeitung arbeitet immer in genau einem Mandanten.** Klick im Dashboard öffnet diesen Mandanten; oben in der linken Spalte lässt sich schnell auf einen anderen eigenen Mandanten wechseln. Eine gemischte Liste aller Mandanten gibt es dort nicht mehr; der Überblick über alle ist das Dashboard.

Gründe:
- Kreditoren, Kontenrahmen (SKR03/SKR04), Lernregeln, Sachkontenlänge, Wirtschaftsjahr und der DATEV-Export gehören je zu einem Mandanten. Gemischte Listen führen zu Buchungen im falschen Mandanten.
- So arbeitet auch DATEV Kanzlei-Rechnungswesen (Mandant öffnen, buchen, Stapel exportieren); Sachbearbeiter kennen das.
- Upload landet automatisch im geöffneten Mandanten.
- Der Wechsler zeigt nur Mandanten, auf die die Person Zugriff hat.

## Später
Kanzlei-Stammdaten in PostgreSQL (`tenant`, `client`, Benutzer mit Rollen), Anmeldung mit Zwei-Faktor, SKR04-Kontenliste, Umrechnung von Fremdwährungen (Kurs zum Leistungsdatum), Steuerschlüssel gegen DATEV-Dokumentation prüfen (Phase 4).
