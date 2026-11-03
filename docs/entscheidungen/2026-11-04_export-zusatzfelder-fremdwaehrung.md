# Entscheidung: Export-Zusatzfelder und Fremdwährung

Stand: 04.11.2026 · Anlass: Paul Graß – fehlende Teile des Exports umsetzen (Leistungsdatum, USt-IdNr. bei Auslandsfällen, Beleglink, Wirtschaftsjahresbeginn je Mandant, Umrechnung von Fremdwährung)

## Spalten
Der Buchungsstapel hat jetzt alle 124 Spalten (Feldliste siehe `docs/datev/buchungsstapel.md`). Belegt werden zusätzlich:
- **Leistungsdatum (115)**, bei Zeiträumen das Ende.
- **EU-Land u. USt-IdNr. (Ursprung) (123)** bei i. g. Erwerb und § 13b aus dem EU-Ausland. DATEV ordnet dem Erwerb das Ursprungsland zu; „Bestimmung“ (Spalte 40) gilt für Lieferungen an Kunden.
- **Beleglink (20):** braucht eine DATEV-GUID aus dem Belegtransfer (z. B. `BEDI "…"`). Die gibt es erst mit der DATEV-Online-Schnittstelle (Developer Portal, CLAUDE.md Abschnitt 10). Vorbereitet über das Feld `datev_beleglink` am Beleg; bis dahin leer.
- **Stattdessen jetzt schon: Beleginfo (21/22)** mit Beleg-ID und SHA-256 des Originals – die Buchung bleibt so eindeutig dem unveränderten Original zugeordnet (GoBD).

## Wirtschaftsjahr
Monat des Wirtschaftsjahresbeginns in den Mandanten-Stammdaten (Standard Januar). Feld 13 des Kopfsatzes: 1. des Monats; liegt der Exportmonat davor, im Vorjahr (abweichendes Wirtschaftsjahr).

## Fremdwährung
- **Rechtsgrundlage:** § 16 Abs. 6 UStG – Umrechnung mit dem vom BMF bekannt gegebenen Monatsdurchschnittskurs des Leistungsmonats; Tageskurs nur mit Genehmigung des Finanzamts. Der EZB-Tageskurs ist daher nicht der Standard und wird nicht automatisch geholt.
- **Quelle der Kurse:** Konfigurationstabelle `umsatzsteuer_umrechnungskurse.json` (CLAUDE.md Regel 16, mit Quelle). Sie ist noch leer, weil die Kurse für Oktober/November 2026 nicht verlässlich abrufbar waren; Werte werden nie geschätzt.
- **Fehlt der Kurs:** Eingabe am Beleg (1 EUR = Kurs, Mengennotierung wie in DATEV), Quelle „von Hand“, im Protokoll. Ohne Kurs keine Freigabe und kein Export.
- **Im Stapel:** Umsatz in Belegwährung, Währung (Spalte 3) und Kurs (Spalte 4); DATEV rechnet beim Import um. Basisumsatz bleibt leer, um Rundungsabweichungen zu vermeiden.
- **Im Export-Fenster:** Kurs, Quelle und Euro-Betrag je Rechnung; die Summe enthält die umgerechneten Beträge.

## Offen
Kurse laufend eintragen oder aus dem BMF-Datenportal importieren (Dateiformat prüfen, wenn erreichbar); Testimport in DATEV mit Fremdwährung, abweichendem Wirtschaftsjahr und i. g. Erwerb; Belegtransfer für den Beleglink.
