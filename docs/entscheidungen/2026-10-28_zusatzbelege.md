# Entscheidung: 12 Zusatzbelege mit anderen Layouts (S21–S32)

Datum: 28.10.2026 · Status: entschieden

## Kontext
Die ersten 20 synthetischen Belege nutzen eine einzige Vorlage. Eine Trefferquote auf dieser Grundlage wäre zu optimistisch; der regelbasierte Platzhalter erreicht darauf 100 %, weil er auf genau diese Vorlage abgestimmt ist.

## Entscheidung
Zwölf zusätzliche Belege mit eigenem Generator (`backend/scripts/zusatzbelege.py`), Goldstandard wie bisher in `testdaten/goldstandard/`, Feld `layout` je Beleg:

| Layout | Belege | Prüft |
|---|---|---|
| modern (ohne Tabellenlinien, Serifenschrift, Datum ausgeschrieben, „EUR“) | S21, S25, S27, S31 | anderes Schriftbild, mehrseitig mit Übertrag (S25, 28 Positionen), Bruttopreise über 250 € (S27) |
| englisch | S24 | englische Begriffe, Zahlenformat 1,234.56, Reverse Charge für EU-Leistung |
| Kassenbon (80 mm, Schreibmaschinenschrift) | S23, S29, S30 | Tankbeleg, Bewirtungsbeleg, Baumarkt; nur Bruttopreise, Steuerkennzeichen A/B |
| Brief ohne Tabelle | S28 | Beträge nur im Fließtext (Gewerbemiete mit Option nach § 9 UStG) |
| klassisch mit Besonderheiten | S22, S26, S32 | Schlussrechnung mit Abschlag (Rechnungsbetrag ≠ Zahlbetrag), Positionsrabatt und Versandkosten, viele Nummern auf dem Beleg (Kunden-, Auftrags-, Lieferscheinnummer) |
| Verschlechterungen | S30 Handyfoto (JPG, Perspektive, Schatten), S31 auf dem Kopf gescannt | Texterkennung unter realistischen Bedingungen |

Neue Konten in `skr03_konten.json`: 0480 (geringwertige Wirtschaftsgüter), 4985 (Werkzeuge und Kleingeräte).

Bei der Schlussrechnung (S22) ist der erwartete Bruttobetrag der **Rechnungsbetrag** der gesamten Leistung, nicht der Zahlbetrag nach Abzug der Abschlagszahlung (`CLAUDE.md` Abschnitt 6: Schlussrechnungen markieren, Prüfung durch Menschen).

## Befunde beim Erstellen
- **Texterkennung:** Eine auf dem Kopf gescannte Seite lieferte nur Zeichensalat. Behoben: Bei geringer Erkennungssicherheit (unter 0,8) werden 180°, 90° und 270° versucht (`app/ocr/text.py`). Große Fotos werden vor der Erkennung verkleinert (30 s → 2 s).
- **Pseudonymisierung:** Zwei Lücken gefunden und behoben: englische Hinweiswörter („Managing director“, „Attn“) und Namenszusätze („van“, „von“); Name unter einer Grußformel ohne Hinweiswort. Jeder einmal erkannte Personenname wird jetzt im ganzen Beleg ersetzt.

## Begründung
Ehrlichere Messwerte für die Anbieterwahl und für das Gespräch mit der Kanzlei. Die Frage „Funktioniert das auch bei echten, unterschiedlichen Rechnungen?“ lässt sich ohne echte Mandantendaten nur mit vielfältigen synthetischen Belegen annähern.
