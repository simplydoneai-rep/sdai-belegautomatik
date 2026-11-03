# DATEV-Format: Buchungsstapel (Arbeitsstand, noch ohne offizielle Formatbeschreibung)

Stand: 04.11.2026 · Umsetzung: `backend/app/export/datev.py` · **Vorläufig**

CLAUDE.md Abschnitt 7 verlangt die Formatbeschreibung aus dem DATEV Developer Portal. Die Seiten dort sind ohne Anmeldung nicht abrufbar. Bis sie vorliegt, gilt dieser Arbeitsstand aus übereinstimmenden Sekundärquellen.

## Datei
- Kodierung Windows-1252, Trenner Semikolon, Zeilenende CR LF.
- Textfelder in Anführungszeichen, Anführungszeichen im Text verdoppelt, keine Steuerzeichen.
- Zeile 1 Kopfsatz (31 Felder), Zeile 2 Spaltenüberschriften (124 Spalten), ab Zeile 3 Buchungen.

## Kopfsatz (31 Felder)
| Feld | Inhalt | Wert bei uns |
|---|---|---|
| 1 | Kennzeichen | `"EXTF"` (Fremdprogramm) |
| 2 | Versionsnummer | 700 |
| 3 | Formatkategorie | 21 (Buchungsstapel) |
| 4 | Formatname | `"Buchungsstapel"` |
| 5 | Formatversion | 13 |
| 6 | Erzeugt am | JJJJMMTTHHMMSSFFF |
| 11 | Beraternummer | 1001–9999999, je Mandant |
| 12 | Mandantennummer | 1–99999 |
| 13 | Wirtschaftsjahresbeginn | JJJJMMTT, aus dem Monat in den Mandanten-Stammdaten; liegt der Exportmonat davor, Beginn im Vorjahr |
| 14 | Sachkontenlänge | 4–8, je Mandant |
| 15, 16 | Datum von / bis | erster und letzter Tag des Monats |
| 17 | Bezeichnung | „Eingangsrechnungen MM/JJJJ“ |
| 19 | Buchungstyp | 1 (Finanzbuchführung) |
| 20 | Rechnungslegungszweck | 0 |
| 21 | Festschreibung | 0 (keine), die Kanzlei schreibt in DATEV fest |
| 22 | Währungskennzeichen | `"EUR"` |
| 27 | Sachkontenrahmen | `"03"` oder `"04"` |
Alle übrigen Felder bleiben leer.

## Buchungszeilen: belegte Spalten
| Spalte | Inhalt | Wert bei uns |
|---|---|---|
| 1 | Umsatz (ohne Soll/Haben-Kz) | positiv, Dezimalkomma, in Belegwährung |
| 2 | Soll/Haben-Kennzeichen | bezogen auf das Konto: Rechnung `H`, Gutschrift `S` |
| 3 | WKZ Umsatz | leer bei EUR, sonst Währung (z. B. `USD`) |
| 4 | Kurs | nur bei Fremdwährung: Mengennotierung (1 EUR = Kurs), 6 Nachkommastellen, z. B. `1,081200`. DATEV rechnet beim Import in Euro um |
| 5, 6 | Basisumsatz, WKZ Basisumsatz | leer (können bei Fremdwährung fehlen) |
| 7 | Konto | Kreditor (Sachkontenlänge + 1 Stellen) |
| 8 | Gegenkonto (ohne BU-Schlüssel) | Sachkonto in Sachkontenlänge |
| 9 | BU-Schlüssel | Steuerschlüssel oder leer (Automatikkonto) |
| 10 | Belegdatum | TTMM |
| 11 | Belegfeld 1 | Rechnungsnummer, höchstens 36 Zeichen |
| 14 | Buchungstext | Lieferant, höchstens 60 Zeichen |
| 20 | Beleglink | DATEV-Kennung (4 Zeichen) + GUID in Anführungszeichen, z. B. `BEDI "…"`. Erst belegt, wenn der Beleg per Belegtransfer in DATEV liegt (Feld `datev_beleglink` am Beleg); bis dahin leer |
| 21, 22 | Beleginfo – Art 1 / Inhalt 1 | `Beleg-ID` / ID und SHA-256 des Originals (Verknüpfung Buchung ↔ Original, GoBD) |
| 115 | Leistungsdatum | TTMMJJJJ; bei einem Zeitraum das Ende |
| 123 | EU-Land u. USt-IdNr. (Ursprung) | USt-IdNr. des Lieferanten bei i. g. Erwerb und § 13b aus dem EU-Ausland (DATEV: Erwerb → „Ursprungsland + USt-IdNr.“) |
Spalte 116 „Datum Zuord. Steuerperiode“ bleibt leer (DATEV ordnet nach Belegdatum zu).

## Fremdwährung
Umrechnung nach § 16 Abs. 6 UStG mit dem BMF-Monatskurs des Leistungsmonats (Tabelle `backend/app/kontierung/tabellen/umsatzsteuer_umrechnungskurse.json`, nur aus BMF-Schreiben befüllen). Fehlt der Monat, trägt der Sachbearbeiter den Kurs am Beleg ein; ohne Kurs keine Freigabe und kein Export.

## Offen (vor dem Pilot, Gate Phase 4)
1. Offizielle Formatbeschreibung beschaffen und hier ablegen; Spaltenüberschriften (Schreibweise, z. B. Bindestrich in „Beleginfo - Art 1“) und Feldtypen abgleichen.
2. Spalte 125: eine Quelle nennt 125 Spalten, die Feldliste endet bei 124.
3. Belegtransfer an DATEV (Beleglink) – setzt Registrierung im DATEV Developer Portal voraus (CLAUDE.md Abschnitt 10).
4. BMF-Umrechnungskurse laufend eintragen (oder Import aus dem BMF-Datenportal, sobald das Dateiformat geprüft ist).
5. Testimport in DATEV Kanzlei-Rechnungswesen mit synthetischen Daten, auch mit Fremdwährung, abweichendem Wirtschaftsjahr und i. g. Erwerb.

## Quellen
- [OBS-Wiki: DATEV CSV-Info (vollständige Spaltenliste 1–124)](https://wiki.bergau.de/OBS/Auswertungen/Datev-CSVInfo)
- [usemeridian.de – DATEV Buchungsstapel EXTF: Aufbau, Kopfzeile](https://usemeridian.de/guides/datev-extf-buchungsstapel)
- [billdock.io – Pflichtfelder, Gegenkonto und Beleglink (Spalte 20)](https://billdock.io/de/blog/datev-buchungsstapel-pflichtfelder)
- [DATEV Hilfe-Center – ASCII-Import: Feldbeschreibungen (Beleglink-Format)](https://apps.datev.de/help-center/documents/1001008)
- [DATEV Hilfe-Center – EU-Informationen beim Buchen erfassen (Bestimmungs- vs. Ursprungsland)](https://apps.datev.de/help-center/documents/9211462)
- [gevitas-Wiki – REXIM mit DATEV-Format (Leistungsdatum Feld 115/116)](https://www.gevitas.de/wiki/index.php?title=REXIM_mit_DATEV_ANSI-Format_Beschreibung_der_Schnittstelle)
- [oxaion Docs – Technische Einzelheiten von DATEV (Kurs in Mengennotierung)](https://docs.oxaion.de/display/open51/Technische+Einzelheiten+von+DATEV)
- [rechnungskit.de – Fremdwährung umrechnen](https://rechnungskit.de/wissen/fremdwaehrung-umrechnung)
- [§ 16 UStG (buzer.de)](https://www.buzer.de/gesetz/5509/a75532.htm) · [Abschn. 16.4 UStAE (Haufe)](https://www.haufe.de/id/norm/umsatzsteuer-anwendungserlass-164-umrechnung-von-werten-in-fremder-waehrung-HI7554985_p16.4.html)
- [BMF-Datenportal: Umsatzsteuer-Umrechnungskurse](https://www.bundesfinanzministerium.de/Datenportal/Daten/offene-daten/steuern-zoelle/umsatzsteuer-umrechnungskurse/umsatzsteuer-umrechnungskurse.html)
- [dokuwandel.de](https://dokuwandel.de/ratgeber/datev-buchungsstapel-erklaerung) · [billboy.de](https://billboy.de/ratgeber/datev-buchungsstapel-import-fehler) · [investmentgarage.de](https://investmentgarage.de/datev-buchungsstapel-erzeugen-mit-r/)
