# Entscheidung: Belege entfernen und DATEV-Export

Stand: 04.11.2026 · Anlass: Paul Graß – Löschfunktion für Belege, die nicht hineingehören; Export, wenn alle Belege erledigt sind

## Entfernen statt Löschen
Die Bitte war eine Löschfunktion. CLAUDE.md Regel 9 (GoBD) verbietet, Originalbelege zu löschen. Deshalb **entfernen**: Der Beleg verlässt die Bearbeitung (zählt nicht mehr als offen, wird nicht exportiert), das Original bleibt gespeichert, Grund und Person stehen im Protokoll, Wiederherstellen ist möglich. Gründe: anderer Mandant, kein Beleg (Werbung, Mahnung), doppelt, privat, sonstiges. Nur offene Belege; freigegebene zuerst wieder öffnen.

Später sinnvoll: „Anderem Mandanten zuordnen“ statt nur entfernen.

## DATEV-Export
- Knopf „DATEV-Export“ unten in der Belegliste, sobald es freigegebene, nicht exportierte Belege gibt; hervorgehoben, wenn nichts mehr offen ist.
- Fenster mit Mandant, Berater-/Mandantennummer, Kontenrahmen, Sachkontenlänge, Sachbearbeitern, Monat (Auswahl bei mehreren), Anzahl, Summe brutto und den Rechnungen zum Aufklappen (Buchungszeilen wie im Stapel). Abbrechen oder Exportieren.
- **Je Monat (Belegdatum), erst wenn dort alle Belege erledigt sind.** Ein Monat mit offenen Belegen zeigt den Grund und sperrt „Exportieren“.
- Datei: DATEV-Buchungsstapel EXTF 700/21, Windows-1252. Kopfsatz und Spalten 1–14 nach übereinstimmenden Sekundärquellen (`docs/datev/buchungsstapel.md`); Prüfskript vor jeder Ausgabe (CLAUDE.md Abschnitt 7).
- Exportstapel mit SHA-256, gespeicherte Datei (nie überschrieben), erneut herunterladbar mit Hashprüfung. Exportierte Belege sind gesperrt.
- Fremdwährung: im Stapel mit Währungskennzeichen, nicht in der Euro-Summe; Umrechnung offen (Hinweis im Fenster).
- Festschreibung 0: Die Kanzlei behält die Kontrolle in DATEV (CLAUDE.md Regel 12).

## Offen (Gate Phase 4)
Offizielle Formatbeschreibung, weitere Spalten (Leistungsdatum, EU-USt-IdNr., Beleglink), Fremdwährungskurs, Wirtschaftsjahresbeginn je Mandant, Testimport in DATEV Kanzlei-Rechnungswesen.

## Kleinere Änderungen
- Eingabefeld „Beraternummer“ breiter (175 px), der Platzhalter passt vollständig.
- Zeile „Zahlung“ in den Rechnungsdaten entfernt; auch die Suche nach Zahlungsangaben im Beleg entfällt. Im Belegbild der E-Rechnung bleibt der Zahlungsblock, weil er zur Rechnung gehört.
