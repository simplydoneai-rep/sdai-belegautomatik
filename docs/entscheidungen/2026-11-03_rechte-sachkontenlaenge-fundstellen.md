# Entscheidung: Zuständigkeit beim Entzug des Zugriffs, Sachkontenlänge je Mandant, Fundstellen im Beleg

Stand: 03.11.2026 · Anlass: Rückmeldungen Paul Graß zur Übersicht, Rechteverwaltung und Belegverarbeitung

## 1. Zugriff entziehen bei Zuständigen und Vertretungen
Bisher waren „Kein Zugriff“ und „Gesperrt“ für zuständige Personen und Vertretungen ohne Erklärung gesperrt (z. B. Sophie Lang bei Bäckerei Kornfeld KG, wo sie zuständig ist).
- Jetzt fragt die Oberfläche in der Zeile nach und passt die Zuständigkeit mit an: **Vertretung** → Vertretung entfällt. **Zuständig** → die Vertretung wird zuständig.
- Ein Mandant braucht immer eine zuständige Person (CLAUDE.md: Sachbearbeiter sehen nur zugeordnete Mandanten). Ist die Person die einzige zuständige, muss erst im Mandanten eine andere eingetragen werden; die Rückfrage bietet „Mandant bearbeiten“ an.
- Ohne ausdrückliche Zustimmung (`zustaendigkeit_anpassen`) ändert der Server nichts. Beide Änderungen stehen im Protokoll.

## 2. Sachkontenlänge je Mandant
- Feld im Mandanten-Formular, 4 bis 8 Stellen, Standard 4. Kreditoren haben eine Stelle mehr (4 → 70000–99999, 5 → 700000–999999).
- Im Buchungssatz und in der DATEV-Zeile werden Sachkonten hinten mit Nullen aufgefüllt (4650 → 46500 bei 5 Stellen). Die Kontenwahl bei den Positionen bleibt 4-stellig wie im SKR.
- Gibt es für den Mandanten schon Kreditoren, lässt sich die Länge nicht mehr ändern (die Kreditorennummern hätten sonst die falsche Länge).
- **Quelle bisher DATEV-Community, nicht die offizielle Formatbeschreibung.** Vor Phase 4 prüfen (CLAUDE.md: Felder nie raten); Wertebereich an einer Stelle: `kanzlei.SACHKONTENLAENGE`.
  - [DATEV-Community: M-Soft und DATEV Daten einspielen](https://www.datev-community.de/t5/Betriebliches-Rechnungswesen/M-Soft-und-Datev-Daten-einspielen/td-p/340810) – Sachkonten werden mit Nullen aufgefüllt; Personenkonten eine Stelle länger
  - [xentral Hilfe: DATEV-Export](https://help.xentral.com/hc/en-us/articles/10692093278492) – Sachkonten 4-stellig, Kreditoren ab 70000

## 3. Fundstellen der Kopfangaben im Beleg
- Überfahren einer Zeile in Rechnungsprüfung, Rechnungsdaten oder der Kopfkarte markiert die Stelle im Beleg: Lieferant mit Anschrift, Mandant, Steuernummer/USt-IdNr., Rechnungsdatum, Rechnungsnummer, Leistungsdatum, Netto, Steuerzeilen, Rechnungsbetrag, Zahlungsangaben; „Rechnerisch richtig“ zeigt alle Summen, „Menge und Art“ alle Positionen.
- PDF mit Textlayer: `verarbeitung.feldrahmen` liest die Zeilen des Textlayers; eine Zeile zählt mit allen Zeilen auf gleicher Höhe (Bezeichnung links, Wert rechts). Stichwörter entscheiden zwischen gleichen Werten (Rechnungsdatum statt Leistungsdatum). Was gesucht wird, steht in `ansicht.feldsuche`.
- E-Rechnung: Das Belegbild kennzeichnet seine Bereiche selbst (`data-feld`).
- Scans und Fotos: keine Markierung (kein Textlayer; OCR-Positionen folgen mit docTR).
- Neue Zeile „Zahlung“ in den Rechnungsdaten (aus dem Beleg gelesen, nur Information, nicht gebucht – CLAUDE.md Abschnitt 6: Skonto nur speichern).

## 4. Oberfläche
- Übersicht: Spalten sortierbar (Klick, nochmal Klick dreht die Richtung), Filter nach offenen Belegen und Sachbearbeiter; Auswahl gemerkt.
- Trennlinie zwischen Bearbeitung und Beleg verschiebbar (gemerkt, Doppelklick setzt zurück) – z. B. Bearbeitung auf dem linken, Beleg auf dem rechten Bildschirm.
- Alle Auswahlfelder mit eigenem Pfeil; beim Fokus ändert sich nur die Hintergrundfarbe (vorher verschwanden Pfeil und Lupe bzw. wurden grau).
