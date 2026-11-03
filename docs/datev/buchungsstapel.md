# DATEV-Format: Buchungsstapel (Arbeitsstand, noch ohne offizielle Formatbeschreibung)

Stand: 03.11.2026 · Umsetzung: `backend/app/export/datev.py` · **Vorläufig**

CLAUDE.md Abschnitt 7 verlangt die Formatbeschreibung aus dem DATEV Developer Portal. Die Seiten dort sind ohne Anmeldung nicht abrufbar. Bis sie vorliegt, gilt dieser Arbeitsstand aus übereinstimmenden Sekundärquellen. Geschrieben wird nur, was mehrere Quellen gleich beschreiben.

## Datei
- Kodierung Windows-1252, Trenner Semikolon, Zeilenende CR LF.
- Textfelder in Anführungszeichen, Anführungszeichen im Text verdoppelt, keine Steuerzeichen.
- Zeile 1 Kopfsatz, Zeile 2 Spaltenüberschriften, ab Zeile 3 Buchungen.

## Kopfsatz (31 Felder)
| Feld | Inhalt | Wert bei uns |
|---|---|---|
| 1 | Kennzeichen | `"EXTF"` (Fremdprogramm) |
| 2 | Versionsnummer | 700 |
| 3 | Formatkategorie | 21 (Buchungsstapel) |
| 4 | Formatname | `"Buchungsstapel"` |
| 5 | Formatversion | 13 |
| 6 | Erzeugt am | JJJJMMTTHHMMSSFFF |
| 11 | Beraternummer | 1001–9999999, je Mandant (`kanzlei.beraternummer`) |
| 12 | Mandantennummer | 1–99999 |
| 13 | Wirtschaftsjahresbeginn | JJJJMMTT; Demo: 1. Januar (Feld im Mandanten fehlt noch) |
| 14 | Sachkontenlänge | 4–8, je Mandant |
| 15, 16 | Datum von / bis | JJJJMMTT, erster und letzter Tag des Monats |
| 17 | Bezeichnung | bis 30 Zeichen, z. B. „Eingangsrechnungen 11/2026“ |
| 19 | Buchungstyp | 1 (Finanzbuchführung) |
| 20 | Rechnungslegungszweck | 0 |
| 21 | Festschreibung | 0 (keine), damit die Kanzlei in DATEV noch korrigieren kann |
| 22 | Währungskennzeichen | `"EUR"` |
| 27 | Sachkontenrahmen | `"03"` oder `"04"` |
Alle übrigen Felder bleiben leer.

## Buchungszeilen (Spalten 1–14)
| Spalte | Inhalt | Wert bei uns |
|---|---|---|
| 1 | Umsatz (ohne Soll/Haben-Kz) | positiv, Dezimalkomma, ohne Tausenderpunkt |
| 2 | Soll/Haben-Kennzeichen | bezogen auf das Konto: Rechnung `H`, Gutschrift `S` |
| 3 | WKZ Umsatz | leer bei EUR, sonst Währung (Umrechnung noch offen) |
| 4–6 | Kurs, Basis-Umsatz, WKZ Basis-Umsatz | leer |
| 7 | Konto | Kreditor (Sachkontenlänge + 1 Stellen) |
| 8 | Gegenkonto (ohne BU-Schlüssel) | Sachkonto in Sachkontenlänge |
| 9 | BU-Schlüssel | Steuerschlüssel oder leer (Automatikkonto) |
| 10 | Belegdatum | TTMM |
| 11 | Belegfeld 1 | Rechnungsnummer, höchstens 36 Zeichen |
| 12, 13 | Belegfeld 2, Skonto | leer (Skonto nur Information, CLAUDE.md Abschnitt 6) |
| 14 | Buchungstext | Lieferant, höchstens 60 Zeichen |

## Offen (vor dem Pilot, Gate Phase 4)
1. Offizielle Formatbeschreibung beschaffen und hier ablegen; Spaltenüberschriften und Feldtypen abgleichen.
2. Weitere Spalten: Leistungsdatum, EU-Land und USt-IdNr. (i. g. Erwerb, § 13b), Beleglink (Belegtransfer), KOST1/KOST2.
3. Fremdwährung: Kurs und Euro-Betrag.
4. Wirtschaftsjahresbeginn je Mandant.
5. Testimport in DATEV Kanzlei-Rechnungswesen mit synthetischen Daten.

## Quellen
- [usemeridian.de – DATEV Buchungsstapel EXTF: Aufbau, Kopfzeile und Import](https://usemeridian.de/guides/datev-extf-buchungsstapel)
- [dokuwandel.de – DATEV Buchungsstapel: Format, Aufbau und Import](https://dokuwandel.de/ratgeber/datev-buchungsstapel-erklaerung)
- [billboy.de – DATEV-Buchungsstapel-Import: Format und Fehler](https://billboy.de/ratgeber/datev-buchungsstapel-import-fehler)
- [investmentgarage.de – DATEV Buchungsstapel erzeugen mit R](https://investmentgarage.de/datev-buchungsstapel-erzeugen-mit-r/)
- [DATEV Developer Portal (offizielle Beschreibung, nicht frei abrufbar)](https://developer.datev.de/datev/platform/en/dtvf)
