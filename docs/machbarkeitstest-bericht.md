# Machbarkeitstest – Bericht

Stand: 28.10.2026, 23:50 Uhr · Phase „Test“ aus `CLAUDE.md` · Plan: `docs/plan-machbarkeitstest.md`

---

## 1. Kurzfassung

| Frage | Ergebnis |
|---|---|
| Läuft die Strecke „Beleg rein → strukturierte Daten → Sachkonto-Vorschlag“? | **Ja.** XML, PDF, Scan und Handyfoto laufen durch Auslesen, Pseudonymisierung, KI, Steuerlogik-Prüfung und Vergleich mit dem Goldstandard. |
| **Erste KI gemessen: Claude Sonnet 4.6 über Amazon Bedrock (Frankfurt)** | **99,2 % richtige Pflichtfelder** über alle 42 Belege. Saubere PDFs 99,6 %, Scans und Foto 100 %. Bei den fremden Layouts (modern, englisch, Kassenbon, Brief) überall 100 %. **Zielwert 90 % klar erreicht.** |
| Positionen und Kontierung (Claude) | Nettobetrag je Position 98,3 %, Steuersatz 97,7 %, **Sachkonto SKR03 88,5 %** ohne jede Lernregel. Die Abweichungen sind überwiegend Ermessensfragen (Abschnitt 4). |
| E-Rechnungen (XRechnung, UBL und CII) | **100 %** ohne KI. UBL und CII liefern bei allen 33 KoSIT-Fällen identische Werte. |
| Texterkennung (docTR, lokal) | Alle Scans und das Handyfoto werden gelesen, auch eine verkehrt herum eingezogene Seite. Ca. 4 s je Seite ohne Grafikkarte. |
| Pseudonymisierung | **0 von 364** geprüften sensiblen Werten erreichen die KI (nach Behebung von sechs Fehlern, Abschnitt 4). |
| Kosten je Beleg (KI) | **Gemessen: 1,2 Cent** mit Claude Sonnet 4.6. Geschätzt für STACKIT: 0,1 Cent (GPT-OSS 120B) bis 0,3 Cent (Qwen3-VL). Planannahme waren 2 Cent. |
| Noch offen | STACKIT (Konto in Prüfung) und Claude Sonnet 5.5 (für neue AWS-Konten noch nicht freigegeben). |

**Empfehlung, Stand heute:** Der Machbarkeitstest ist **bestanden**, die KI-Strecke erreicht den Zielwert deutlich. Die Anbieterwahl fällt nach der STACKIT-Messung nach der Regel in Abschnitt 5. Erreicht STACKIT ein vergleichbares Ergebnis, ist es wegen Standort Deutschland und Preis die erste Wahl.

---

## 2. Aufbau des Tests

### Testbelege (42)
| Gruppe | Anzahl | Inhalt |
|---|---|---|
| Synthetische PDFs, Grundvorlage | 17 | Erfundene Lieferanten und Mandanten aus 5 Branchen (Café, Kfz-Werkstatt, Zimmerei, Werbeagentur, Bäckerei). 7 %, 19 %, gemischt 7/19 % (4×), Gutschrift, Reverse Charge § 13b, innergemeinschaftlicher Erwerb, Kleinbetragsrechnung ohne Rechnungsnummer |
| Synthetische Scans, Grundvorlage | 3 | Bild in 150 dpi mit JPEG-Artefakten; 2,5° schief; verrauscht mit Flecken und geringem Kontrast |
| Zusatzbelege mit fremden Layouts | 12 | Modern ohne Tabellenlinien, englisch (EU-Reverse-Charge), drei Kassenbons (Tankstelle, Bewirtung, Baumarkt als Handyfoto), Mietrechnung als Brief, mehrseitig mit 28 Positionen, Bruttopreise, Positionsrabatt, Schlussrechnung mit Abschlag, Beleg mit vielen Nummern, eine Seite auf dem Kopf gescannt (`docs/entscheidungen/2026-10-28_zusatzbelege.md`) |
| KoSIT-XRechnungen | 10 | Aus der offiziellen Testsuite (XRechnung 3.0): 0 %, 7 %, 19 %, gemischt, Reverse Charge (AE), über 20 Positionen, Zu- und Abschläge, negative Mengen. Jeder Fall läuft dreimal: als UBL, als CII (beide ohne KI) und als Sicht-PDF durch die KI-Strecke |

Erwartete Ergebnisse je Beleg: `testdaten/goldstandard/*.json`. Erzeugung reproduzierbar mit `backend/scripts/erzeuge_testbelege.py` und `backend/scripts/zusatzbelege.py`.

### Ablauf je Beleg
```
XML ──────────────▶ E-Rechnungs-Parser (UBL/CII) ────────────────────────────────┐
PDF mit Text ─────▶ PyMuPDF-Textlayer ─┐                                         ├─▶ Steuerlogik prüft Summen ─▶ Vergleich Goldstandard
Scan, Foto ───────▶ docTR (lokal) ─────┴─▶ Pseudonymisierung ─▶ LLMProvider ─────┘
```

### Gemessene Felder
- **Pflichtfelder (9):** Lieferant, Rechnungsnummer, Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Belegart, Reverse Charge.
- **Positionen:** Nettobetrag, Steuersatz, Sachkonto SKR03 (aus der erlaubten Kontenliste, 25 Konten).
- **Steuerlogik:** Netto + Steuer = Brutto, Steuer passt zu den Positionen, nur 0/7/19 %, Reverse Charge ohne Steuer (Toleranz 0,01 € je Steuersatz).
- **Pseudonymisierung:** Je Beleg werden 5–10 sensible Werte im Text gesucht, der an die KI ginge (exakt und unscharf).

---

## 3. Messwerte

<!-- MESSWERTE:START -->
**Lauf:** `2026-10-28_234816` · Belege: 42 · gemessene Anbieter: erechnung, bedrock, placeholder

**Modelle:** `bedrock` = `eu.anthropic.claude-sonnet-4-6`

**Nicht gemessen:** `stackit_qwen` (kein STACKIT_API_KEY in .env); `stackit_gptoss` (kein STACKIT_API_KEY in .env)

### Pflichtfelder je Anbieter und Belegart

| Anbieter | E-Rechnung XML (KoSIT) | PDF mit Text (synthetisch) | PDF mit Text (KoSIT-Sichtbeleg) | Scan / Foto | Gesamt |
|---|---|---|---|---|---|
| `erechnung` | 100.0 % (20) | – | – | – | **100.0 %** |
| `bedrock` | – | 99.6 % (27) | 97.8 % (10) | 100.0 % (5) | **99.2 %** |
| `placeholder` | – | 84.8 % (27) | 100.0 % (10) | 77.8 % (5) | **87.6 %** |

In Klammern: Zahl der Belege. Zielwert Phase A: mindestens 90 % bei sauberen PDFs.

### Pflichtfelder je Layout (PDF, Scan, Foto)

| Layout | Belege | `bedrock` | `placeholder` |
|---|---|---|---|
| bon | 3 | 100.0 % | 44.4 % |
| brief | 1 | 100.0 % | 55.6 % |
| englisch | 1 | 100.0 % | 44.4 % |
| klassisch | 23 | 99.5 % | 97.1 % |
| kosit | 10 | 97.8 % | 100.0 % |
| modern | 4 | 100.0 % | 52.8 % |

Layout „klassisch“ ist die Vorlage, auf die der Platzhalter abgestimmt ist. Die übrigen Layouts zeigen, wie gut ein Anbieter mit fremden Rechnungsbildern umgeht.

### Trefferquote je Feld (ohne XML)

| Feld | `bedrock` | `placeholder` |
|---|---|---|
| Lieferant | 100.0 % | 100.0 % |
| Rechnungsnummer | 95.2 % | 81.0 % |
| Rechnungsdatum | 100.0 % | 78.6 % |
| Netto | 100.0 % | 90.5 % |
| Steuer | 100.0 % | 85.7 % |
| Brutto | 100.0 % | 76.2 % |
| Steuersätze | 97.6 % | 76.2 % |
| Belegart (Rechnung/Gutschrift) | 100.0 % | 100.0 % |
| Reverse Charge / i. g. Erwerb | 100.0 % | 100.0 % |
| Positionen: Nettobetrag | 98.3 % (169/172) | 70.9 % (122/172) |
| Positionen: Steuersatz | 97.7 % (168/172) | 70.9 % (122/172) |
| Positionen: Sachkonto SKR03 | 88.5 % (92/104) | 46.2 % (48/104) |
| Steuerlogik: Summen plausibel | 100.0 % | 76.2 % |

Sachkonten werden nur bei den synthetischen Belegen bewertet (KoSIT-Belege haben keine Sollkontierung).

### Pseudonymisierung

Geprüft: 364 sensible Werte in 42 Belegtexten (Mandantenname, Ansprechpartner, Anschrift, USt-IdNr. des Mandanten, IBAN, E-Mail, Telefon, Steuernummer, Namen natürlicher Personen beim Lieferanten).

**Im KI-Text verblieben: 0 von 364 (0.0 %)**

### Laufzeit je Beleg

| Schritt | Mittelwert | Maximum |
|---|---|---|
| XML parsen | 0.00 s | 0.00 s |
| PDF-Textlayer lesen | 0.00 s | 0.01 s |
| Texterkennung docTR (CPU), Scan und Foto | 4.24 s | 8.51 s |
| Anbieter `bedrock` | 4.11 s | 14.93 s |
| Anbieter `placeholder` | 0.00 s | 0.00 s |

### Kosten je Beleg (KI-Aufruf)

| Anbieter | Preis Eingabe / Ausgabe je Mio. Token | Token je Beleg (Ø ein / aus) | Kosten je Beleg | Grundlage |
|---|---|---|---|---|
| `bedrock` | 3.00 € / 15.00 € | 1,575 / 510 | 0.0124 € | gemessen (42 Aufrufe) |
| `stackit_qwen` | 1.50 € / 1.75 € | 1,575 / 510 | 0.0033 € | Schätzung, noch nicht gemessen |
| `stackit_gptoss` | 0.45 € / 0.65 € | 1,575 / 510 | 0.0010 € | Schätzung, noch nicht gemessen |

Hinzu kommen Serverkosten für Texterkennung und Anwendung (siehe `docs/kosten.md`).

### Ergebnisse je Beleg

| Beleg | Merkmale | Art | Anbieter | Pflichtfelder | Positionen Betrag | Konto | Abweichungen |
|---|---|---|---|---|---|---|---|
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `placeholder` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock` | 8/9 | 3/3 | – | Rechnungsnummer |
| K01.11 | Drei Positionen, 19 % | pdf | `placeholder` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock` | 8/9 | 11/11 | – | Rechnungsnummer |
| K01.13 | Elf Positionen, 19 % | pdf | `placeholder` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock` | 9/9 | 1/1 | – | Positionsanzahl |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `placeholder` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (UBL) | `erechnung` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (CII) | `erechnung` | 9/9 | 23/23 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `placeholder` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (UBL) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (CII) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `placeholder` | 9/9 | 3/4 | – | Positionsanzahl |
| K03.06 | Austauschteile, negative Menge | xml (UBL) | `erechnung` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | xml (CII) | `erechnung` | 9/9 | 4/4 | – | – |
| S01 | 7 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S02 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S03 | 19 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S04 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S04 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S06 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S06 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S07 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S07 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S09 | 7 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S12 | 19 %, Energie | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock` | 8/9 | 1/1 | 1/1 | Steuersätze |
| S17 | innergemeinschaftlicher Erwerb | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `placeholder` | 8/9 | 2/3 | 2/3 | Steuersätze, Positionsanzahl |
| S21 | Layout modern, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S21 | Layout modern, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `placeholder` | 6/9 | 2/2 | 0/2 | Rechnungsnummer, Steuer, Brutto |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 1/2 | 1/2 | – |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 28/28 | 28/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `placeholder` | 5/9 | 0/28 | 0/28 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `placeholder` | 8/9 | 1/3 | 0/3 | Rechnungsnummer, Positionsanzahl |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock` | 9/9 | 0/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `placeholder` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
<!-- MESSWERTE:ENDE -->

---

## 4. Befunde

1. **Claude erreicht den Zielwert deutlich, auch bei fremden Layouts.** 99,2 % der Pflichtfelder sind richtig. Die Abweichungen:
   - **K01.11, K01.13:** In den KoSIT-Testdateien steht als Rechnungsnummer wörtlich „Rechnungsnummer“ (Platzhalter der Testsuite). Claude gibt keine Nummer zurück, was fachlich richtig ist. Fehler im Testdatensatz, nicht bei der KI.
   - **S17, innergemeinschaftlicher Erwerb:** Claude trägt 19 % ein (den Satz, den der Käufer selbst versteuert) statt 0 % laut Rechnung. Fachlich vertretbar; die Steuerlogik muss für i. g. Erwerb und Reverse Charge eindeutig vorgeben, welcher Satz gemeint ist (Phase 2).
2. **Positionen bei Bruttopreisen:** Bei S27 (Bruttopreise über 250 €) übernimmt Claude die Bruttobeträge als Netto je Position; die Summen stimmen trotzdem. Die Steuerlogik erkennt die Abweichung zwischen Positionen und Nettosumme. In Phase 2 rechnet die Steuerlogik selbst um, statt sich auf die KI zu verlassen (`CLAUDE.md` Regel 15).
3. **Sachkonten: 88,5 % ohne Lernen.** Von 12 Abweichungen sind die meisten Ermessensfragen, die Kanzleien unterschiedlich buchen: Schleifpapier und Schrauben als Ware oder Kleinmaterial (3400 oder 4985), Online-Datenbank als Lizenz oder Fachliteratur (4964 oder 4940), Backpapier in der Bäckerei als Wareneingang oder Betriebsbedarf. Ein echter Fehler: Kurierfahrten auf 4980 statt 4910 (Porto). Genau diese Fälle lösen später das Branchen-Regelwerk und die Lernregeln je Mandant.
4. **E-Rechnungen brauchen keine KI.** Der eigene Parser liest XRechnung in UBL und CII vollständig. Mit der E-Rechnungspflicht im B2B-Bereich (Empfang seit 2025, Versand schrittweise bis 2028) sinkt der KI-Anteil und damit die Kosten weiter.
5. **Texterkennung:** docTR liest Scans, Kassenbons und das Handyfoto. Eine verkehrt herum gescannte Seite lieferte zunächst nur Zeichensalat; behoben durch automatische Lageerkennung (bei geringer Erkennungssicherheit wird die Seite gedreht). Große Fotos werden vorher verkleinert (30 s → 2 s).
6. **Pseudonymisierung: sechs Fehler gefunden und behoben**
   - Die Telefon-Regel enthielt ein unsichtbares Steuerzeichen und erkannte Nummern ohne „+49“ nicht.
   - Die Personen-Regel nahm Text nach dem Namen über mehrere Leerzeichen hinweg mit.
   - Mandantenname mit OCR-Lesefehler („Backerei Kornteld KG“) wurde nicht ersetzt; jetzt unscharfer Abgleich.
   - „Geschäftsführer“ fehlte als Hinweiswort, auch in verlesener Form.
   - Englische Hinweiswörter („Managing director“, „Attn“) und Namenszusätze („van“, „von“) fehlten.
   - Ein Name unter einer Grußformel ohne Hinweiswort blieb stehen. Jetzt erkannt; außerdem wird jeder einmal erkannte Personenname im ganzen Beleg ersetzt.
7. **Restrisiko Pseudonymisierung:** Namen natürlicher Personen ohne Hinweiswort und ohne Grußformel erkennt die Regel weiterhin nicht. Die Leckprüfung findet verlesene Kennungen (z. B. „449 4289 117“ statt „+49 911 4289 117“) nicht, weil sie Kennungen nur exakt sucht. In Phase 1 kommt Presidio mit deutschem NER-Modell dazu (`CLAUDE.md`, Technik).
8. **Die regelbasierte Vergleichsstufe (`placeholder`) zeigt, warum KI nötig ist:** Auf der eigenen Vorlage 97 %, bei fremden Layouts nur 44–56 %.
9. **Kleiner Prompt:** Gemessen ca. 1.600 Eingabe- und 500 Ausgabe-Token je Beleg (Planannahme 5.000 / 800). Mit vollständiger Kontenliste des Mandanten (mehrere hundert Konten) steigt die Eingabe auf ca. 4.000–6.000 Token; die Kosten bleiben auch mit Claude unter 3 Cent je Beleg.

---

## 5. Empfehlung und Entscheidungsregel

**Abbruchkriterium Phase A: nicht erreicht.** Mindestens ein Anbieter liegt deutlich über 90 %. Das Projekt kann in Phase B (Entwicklung) übergehen.

Die Anbieterwahl fällt nach der STACKIT-Messung nach dieser Regel:

| Ergebnis bei sauberen PDFs (Pflichtfelder) | Entscheidung |
|---|---|
| STACKIT-Modell ≥ 90 % und höchstens 3 Prozentpunkte unter Claude | **STACKIT produktiv.** Kein AWS nötig, kein § 203-Addendum über AWS-Partner. |
| STACKIT ≥ 90 %, aber mehr als 3 Punkte unter Claude | STACKIT für den Pilot, Claude als Rückfall für Belege mit geringer Sicherheit; nach 3 Monaten Pilot neu bewerten |
| Nur Claude ≥ 90 % (aktueller Stand) | Bedrock EU, § 203-Addendum über AWS-Partner sofort anstoßen |
| Kein Anbieter ≥ 90 % | entfällt, Claude liegt bei 99,6 % |

Bei gleicher Qualität entscheidet der Preis: GPT-OSS 120B kostet nach Schätzung etwa ein Zwölftel von Claude.

---

## 6. So wird die Messung vervollständigt

1. **STACKIT:** Nach Freischaltung des Kundenkontos `STACKIT_API_KEY`, `STACKIT_MODEL_QWEN` und `STACKIT_MODEL_GPTOSS` direkt in `.env` eintragen (nicht in einen Chat).
2. **Claude Sonnet 5.5:** AWS meldet für das neue Konto „not available for this account“. Freischaltung über eine Support-Anfrage bei AWS (Verwaltungskonto, Region eu-central-1). Bis dahin ist Sonnet 4.6 die Referenz.
3. Im Ordner `backend`:
   ```
   .venv\Scripts\python scripts\machbarkeitstest.py
   .venv\Scripts\python scripts\auswertung.py
   ```
   Für ein anderes Bedrock-Modell vorher `BEDROCK_MODEL_ID` in `.env` ändern. Die Tabellen in Abschnitt 3 werden automatisch ersetzt; Modell und Preise stehen im Lauf.

---

## 7. Grenzen des Tests

- Alle Belege sind synthetisch. Sechs Layouts und 42 Belege sind deutlich vielfältiger als zuvor, aber weniger als die Hunderte Layouts echter Lieferanten. Für Phase B ist ein Goldstandard mit mindestens 200 Belegen geplant (`CLAUDE.md`, Code-Konventionen).
- Die KoSIT-Sichtbelege nutzen die Grundvorlage; die Lieferantennamen der KoSIT-Dateien sind Platzhalter („[Seller name]“) und wurden durch erfundene Namen ersetzt.
- Die Sollkontierung ist eine von mehreren vertretbaren. Für eine belastbare Kontierungsquote sollte ein Sachbearbeiter der Kanzlei den Goldstandard einmal prüfen.
- An die KI geht nur Text, kein Bild (`docs/entscheidungen/2026-10-28_ki-eingabe-nur-text.md`). Die Bildfähigkeit von Qwen3-VL wird nicht genutzt.
- Gemessen wurde Claude Sonnet 4.6, nicht das in `CLAUDE.md` vorgesehene Sonnet 5.5 (siehe Abschnitt 6).
- Preis Claude Sonnet 4.6 (3 $ / 15 $ je Million Token, 1:1 in Euro gerechnet) und Sonnet 5.5 (2 $ / 10 $ laut Projektplan): vor dem Pilot im AWS-Preisrechner für `eu-central-1` prüfen. STACKIT-Preise: [STACKIT-Preisliste](https://stackit.com/en/asset/download/37788/file/STACKIT_price_list.pdf?version=18) (GPT-OSS 120B 0,45 € / 0,65 €; Qwen3-VL 1,75 € Ausgabe), Eingabepreis Qwen3-VL 1,50 € laut [european.cloud](https://european.cloud/2025/10/stackit-ai-model-serving/) und [wz-it.com](https://wz-it.com/en/blog/european-llm-api-comparison/), verbindlich bei STACKIT erfragen.
- Laufzeiten gemessen auf dem Entwicklungs-PC ohne Grafikkarte; Claude antwortet im Mittel in 4 s je Beleg.
