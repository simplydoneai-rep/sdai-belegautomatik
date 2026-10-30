# Machbarkeitstest – Bericht

Stand: 31.10.2026 · Phase „Test“ aus `CLAUDE.md` · Plan: `docs/plan-machbarkeitstest.md`

---

## 1. Kurzfassung

Fünf KI-Zugänge, gleicher Prompt, 42 Belege:

| | Claude Sonnet 4.6 (AWS) | GPT-OSS 120B (AWS) | Qwen3 235B (AWS) | **GPT-OSS 120B (IONOS)** | **Qwen3.5 397B (IONOS)** |
|---|---|---|---|---|---|
| Pflichtfelder (Kopfdaten) | 99,2 % | 99,2 % | 99,5 % | 98,9 % | 98,7 % |
| Positionen (Betrag, Steuersatz) | 99,4 % | 100 % | 93,6 % | 100 % | 100 % |
| **Sachkonto SKR03** (ohne Lernregeln) | **88,5 %** | 62,5 % | 68,3 % | 61,5 % | **87,5 %** |
| Kosten je Beleg | 1,27 Cent | 0,08 Cent | 0,07 Cent | **0,09 Cent** | 1,90 Cent |
| Antwortzeit je Beleg | 3 s | 5 s | 6 s | 6 s | 61 s |
| Anbieter, Verarbeitung | US-Konzern, EU-Regionen | US-Konzern, Frankfurt | US-Konzern, Frankfurt | **deutsch, Deutschland** | **deutsch, Deutschland** |
| § 203 StGB | nur über AWS-Partner | nur über AWS-Partner | nur über AWS-Partner | **in Standard-AVV** | **in Standard-AVV** |

| Frage | Ergebnis |
|---|---|
| Zielwert Phase A (90 % Pflichtfelder bei sauberen PDFs) | **Von allen fünf klar erreicht.** Der Machbarkeitstest ist bestanden. |
| Geht es ohne AWS? | **Ja.** Bei IONOS liest GPT-OSS so gut aus wie Claude, und Qwen3.5 397B kontiert fast so gut wie Claude (87,5 % gegenüber 88,5 %). |
| Haken der deutschen Lösung | Qwen3.5 „denkt“ lange: ca. 1 Minute und knapp 2 Cent je Beleg. Lange Rechnungen brauchen ein hohes Token-Limit (24.000). |
| E-Rechnungen (XRechnung, UBL und CII) | **100 %** ohne KI. |
| Texterkennung (docTR, lokal) | Scans, Kassenbons, Handyfoto und verkehrt herum eingezogene Seite werden gelesen; ca. 4,5 s je Seite ohne Grafikkarte. |
| Pseudonymisierung | **0 von 364** geprüften sensiblen Werten erreichen die KI. |
| Nicht gemessen | STACKIT (Kundenkonto abgelehnt), Claude Sonnet 5.5 (für das AWS-Konto gesperrt). |

**Empfehlung:** Komplett bei IONOS in Deutschland. GPT-OSS 120B liest aus (0,09 Cent je Beleg), Lernregeln und Branchen-Regelwerk kontieren, und nur für Positionen ohne Regel schlägt Qwen3.5 397B ein Sachkonto vor. AWS bleibt als Rückfallebene. Einzelheiten in Abschnitt 5.

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
**Belege:** 42 · **gemessene Anbieter:** erechnung, bedrock, bedrock_gptoss, bedrock_qwen, ionos_gptoss, ionos_qwen, placeholder

**Läufe:** `bedrock` aus `2026-10-30_222139`; `bedrock_gptoss` aus `2026-10-30_222139`; `bedrock_qwen` aus `2026-10-30_222139`; `erechnung` aus `2026-10-30_231801, 2026-10-31_000550`; `ionos_gptoss` aus `2026-10-30_231801`; `ionos_qwen` aus `2026-10-30_231801, 2026-10-31_000550`; `placeholder` aus `2026-10-30_222139`

**Modelle:** `bedrock` = `eu.anthropic.claude-sonnet-4-6`; `bedrock_gptoss` = `openai.gpt-oss-120b-1:0`; `bedrock_qwen` = `qwen.qwen3-235b-a22b-2507-v1:0`; `ionos_gptoss` = `openai/gpt-oss-120b`; `ionos_qwen` = `Qwen/Qwen3.5-397B-A17B`

**Nicht gemessen:** `stackit_qwen` (kein STACKIT_API_KEY in .env); `stackit_gptoss` (kein STACKIT_API_KEY in .env)

### Pflichtfelder je Anbieter und Belegart

| Anbieter | E-Rechnung XML (KoSIT) | PDF mit Text (synthetisch) | PDF mit Text (KoSIT-Sichtbeleg) | Scan / Foto | Gesamt |
|---|---|---|---|---|---|
| `erechnung` | 100.0 % (20) | – | – | – | **100.0 %** |
| `bedrock` | – | 99.6 % (27) | 97.8 % (10) | 100.0 % (5) | **99.2 %** |
| `bedrock_gptoss` | – | 99.2 % (27) | 100.0 % (10) | 97.8 % (5) | **99.2 %** |
| `bedrock_qwen` | – | 99.2 % (27) | 100.0 % (10) | 100.0 % (5) | **99.5 %** |
| `ionos_gptoss` | – | 99.2 % (27) | 98.9 % (10) | 97.8 % (5) | **98.9 %** |
| `ionos_qwen` | – | 99.2 % (27) | 97.8 % (10) | 97.8 % (5) | **98.7 %** |
| `placeholder` | – | 84.8 % (27) | 100.0 % (10) | 77.8 % (5) | **87.6 %** |

In Klammern: Zahl der Belege. Zielwert Phase A: mindestens 90 % bei sauberen PDFs.

### Pflichtfelder je Layout (PDF, Scan, Foto)

| Layout | Belege | `bedrock` | `bedrock_gptoss` | `bedrock_qwen` | `ionos_gptoss` | `ionos_qwen` | `placeholder` |
|---|---|---|---|---|---|---|---|
| bon | 3 | 96.3 % | 88.9 % | 96.3 % | 88.9 % | 88.9 % | 44.4 % |
| brief | 1 | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 55.6 % |
| englisch | 1 | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 44.4 % |
| klassisch | 23 | 100.0 % | 100.0 % | 99.5 % | 100.0 % | 100.0 % | 97.1 % |
| kosit | 10 | 97.8 % | 100.0 % | 100.0 % | 98.9 % | 97.8 % | 100.0 % |
| modern | 4 | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 52.8 % |

Layout „klassisch“ ist die Vorlage, auf die der Platzhalter abgestimmt ist. Die übrigen Layouts zeigen, wie gut ein Anbieter mit fremden Rechnungsbildern umgeht.

### Trefferquote je Feld (ohne XML)

| Feld | `bedrock` | `bedrock_gptoss` | `bedrock_qwen` | `ionos_gptoss` | `ionos_qwen` | `placeholder` |
|---|---|---|---|---|---|---|
| Lieferant | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % |
| Rechnungsnummer | 92.9 % | 92.9 % | 97.6 % | 90.5 % | 88.1 % | 81.0 % |
| Rechnungsdatum | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 78.6 % |
| Netto | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 90.5 % |
| Steuer | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 85.7 % |
| Brutto | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 76.2 % |
| Steuersätze | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 76.2 % |
| Belegart (Rechnung/Gutschrift) | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % |
| Reverse Charge / i. g. Erwerb | 100.0 % | 100.0 % | 97.6 % | 100.0 % | 100.0 % | 100.0 % |
| Positionen: Nettobetrag | 99.4 % (171/172) | 100.0 % (172/172) | 93.6 % (161/172) | 100.0 % (172/172) | 100.0 % (172/172) | 70.9 % (122/172) |
| Positionen: Steuersatz | 99.4 % (171/172) | 100.0 % (172/172) | 93.6 % (161/172) | 100.0 % (172/172) | 100.0 % (172/172) | 70.9 % (122/172) |
| Positionen: Sachkonto SKR03 | 88.5 % (92/104) | 62.5 % (65/104) | 68.3 % (71/104) | 61.5 % (64/104) | 87.5 % (91/104) | 46.2 % (48/104) |
| Steuerlogik: Summen plausibel | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 76.2 % |

Sachkonten werden nur bei den synthetischen Belegen bewertet (KoSIT-Belege haben keine Sollkontierung).

### Pseudonymisierung

Geprüft: 364 sensible Werte in 42 Belegtexten (Mandantenname, Ansprechpartner, Anschrift, USt-IdNr. des Mandanten, IBAN, E-Mail, Telefon, Steuernummer, Namen natürlicher Personen beim Lieferanten).

**Im KI-Text verblieben: 0 von 364 (0.0 %)**

### Laufzeit je Beleg

| Schritt | Mittelwert | Maximum |
|---|---|---|
| XML parsen | 0.00 s | 0.00 s |
| PDF-Textlayer lesen | 0.00 s | 0.01 s |
| Texterkennung docTR (CPU), Scan und Foto | 4.51 s | 8.93 s |
| Anbieter `bedrock` | 2.66 s | 10.79 s |
| Anbieter `bedrock_gptoss` | 5.18 s | 12.31 s |
| Anbieter `bedrock_qwen` | 6.28 s | 26.87 s |
| Anbieter `ionos_gptoss` | 6.21 s | 22.07 s |
| Anbieter `ionos_qwen` | 60.81 s | 143.95 s |
| Anbieter `placeholder` | 0.00 s | 0.00 s |

### Kosten je Beleg (KI-Aufruf)

| Anbieter | Preis Eingabe / Ausgabe je Mio. Token | Token je Beleg (Ø ein / aus) | Kosten je Beleg | Grundlage |
|---|---|---|---|---|
| `bedrock` | 3.00 € / 15.00 € | 1,727 / 501 | 0.0127 € | gemessen (42 Aufrufe) |
| `bedrock_gptoss` | 0.15 € / 0.60 € | 1,327 / 1,014 | 0.0008 € | gemessen (42 Aufrufe) |
| `bedrock_qwen` | 0.22 € / 0.88 € | 1,559 / 445 | 0.0007 € | gemessen (42 Aufrufe) |
| `ionos_gptoss` | 0.15 € / 0.65 € | 1,330 / 1,071 | 0.0009 € | gemessen (42 Aufrufe) |
| `ionos_qwen` | 0.60 € / 3.60 € | 1,456 / 5,046 | 0.0190 € | gemessen (42 Aufrufe) |

Hinzu kommen Serverkosten für Texterkennung und Anwendung (siehe `docs/kosten.md`).

### Ergebnisse je Beleg

| Beleg | Merkmale | Art | Anbieter | Pflichtfelder | Positionen Betrag | Konto | Abweichungen |
|---|---|---|---|---|---|---|---|
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `ionos_qwen` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `ionos_qwen` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock_gptoss` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock_qwen` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `ionos_gptoss` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `ionos_qwen` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `ionos_gptoss` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `ionos_qwen` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `placeholder` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock` | 8/9 | 3/3 | – | Rechnungsnummer |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `ionos_qwen` | 8/9 | 3/3 | – | Rechnungsnummer |
| K01.11 | Drei Positionen, 19 % | pdf | `placeholder` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock` | 8/9 | 11/11 | – | Rechnungsnummer |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `ionos_gptoss` | 8/9 | 11/11 | – | Rechnungsnummer |
| K01.13 | Elf Positionen, 19 % | pdf | `ionos_qwen` | 8/9 | 11/11 | – | Rechnungsnummer |
| K01.13 | Elf Positionen, 19 % | pdf | `placeholder` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock` | 9/9 | 1/1 | – | Positionsanzahl |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock_gptoss` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock_qwen` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `ionos_gptoss` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `ionos_qwen` | 9/9 | 1/1 | – | Positionsanzahl |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock` | 9/9 | 23/23 | – | Positionsanzahl |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock_gptoss` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock_qwen` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `ionos_gptoss` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `ionos_qwen` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `placeholder` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (UBL) | `erechnung` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (CII) | `erechnung` | 9/9 | 23/23 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `ionos_gptoss` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `ionos_qwen` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `placeholder` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (UBL) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (CII) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock_gptoss` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock_qwen` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `ionos_gptoss` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `ionos_qwen` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `placeholder` | 9/9 | 3/4 | – | Positionsanzahl |
| K03.06 | Austauschteile, negative Menge | xml (UBL) | `erechnung` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | xml (CII) | `erechnung` | 9/9 | 4/4 | – | – |
| S01 | 7 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `bedrock_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `bedrock_qwen` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `ionos_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `ionos_qwen` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S02 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S03 | 19 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `bedrock_qwen` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `ionos_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `ionos_qwen` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S04 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S04 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `ionos_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S06 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S07 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S07 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 0/3 | – |
| S07 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/3 | 0/3 | – |
| S07 | 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 0/3 | – |
| S07 | 19 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S07 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S08 | 19 %, Lizenz | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S09 | 7 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock_gptoss` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock_qwen` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `ionos_gptoss` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `ionos_qwen` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock_qwen` | 9/9 | 2/3 | 2/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S12 | 19 %, Energie | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `ionos_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S14 | 7 % und 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S15 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S15 | 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock` | 9/9 | 1/1 | 1/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock_gptoss` | 9/9 | 1/1 | 1/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock_qwen` | 8/9 | 1/1 | 1/1 | Reverse Charge / i. g. Erwerb |
| S17 | innergemeinschaftlicher Erwerb | pdf | `ionos_gptoss` | 9/9 | 1/1 | 0/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `ionos_qwen` | 9/9 | 1/1 | 1/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 2/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `ionos_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `ionos_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `ionos_qwen` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `ionos_gptoss` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `ionos_qwen` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `placeholder` | 8/9 | 2/3 | 2/3 | Steuersätze, Positionsanzahl |
| S21 | Layout modern, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S21 | Layout modern, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `placeholder` | 6/9 | 2/2 | 0/2 | Rechnungsnummer, Steuer, Brutto |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 1/2 | 1/2 | – |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock_qwen` | 9/9 | 1/2 | 1/2 | – |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `ionos_gptoss` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `ionos_qwen` | 8/9 | 2/2 | 2/2 | Rechnungsnummer |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 28/28 | 28/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 28/28 | 20/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 28/28 | 20/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `ionos_gptoss` | 9/9 | 28/28 | 20/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `ionos_qwen` | 9/9 | 28/28 | 28/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `placeholder` | 5/9 | 0/28 | 0/28 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `ionos_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `ionos_qwen` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `placeholder` | 8/9 | 1/3 | 0/3 | Rechnungsnummer, Positionsanzahl |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock_qwen` | 9/9 | 0/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock_qwen` | 8/9 | 0/3 | 0/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `ionos_gptoss` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `ionos_qwen` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock` | 9/9 | 3/3 | 1/3 | – |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock_gptoss` | 8/9 | 3/3 | 0/3 | Rechnungsnummer |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock_qwen` | 9/9 | 0/3 | 0/3 | – |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `ionos_gptoss` | 8/9 | 3/3 | 0/3 | Rechnungsnummer |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `ionos_qwen` | 8/9 | 3/3 | 0/3 | Rechnungsnummer |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `ionos_qwen` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 1/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `ionos_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `ionos_qwen` | 9/9 | 2/2 | 2/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `placeholder` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
<!-- MESSWERTE:ENDE -->

---

## 4. Befunde

1. **Auslesen: Alle fünf Zugänge erreichen den Zielwert deutlich.** Kopfdaten 98,7–99,5 %. Die verbleibenden Abweichungen:
   - **K01.11, K01.13:** In den KoSIT-Testdateien steht als Rechnungsnummer wörtlich „Rechnungsnummer“ (Platzhalter der Testsuite). Die Modelle geben keine Nummer zurück, was fachlich richtig ist. Fehler im Testdatensatz.
   - Kassenbons ohne Rechnungsnummer und mit Bruttopreisen sind für alle Modelle die schwierigste Belegart (89–96 % der Pflichtfelder).
2. **Kontierung: Zwei Modelle auf Augenhöhe.** Claude 88,5 %, Qwen3.5 397B bei IONOS 87,5 %. Die kleineren offenen Modelle (GPT-OSS, Qwen3 235B) liegen bei 62–68 % und machen systematische Fehler: Betriebsbedarf (Spülmittel, Backpapier, Kartons) auf 3400 Wareneingang statt 4980, Dienstleistungen (Werbung, Lizenzen, Wartung, Telefon) auf 3100 Fremdleistungen. Claudes und Qwens Abweichungen sind dagegen überwiegend Ermessensfragen (Schleifpapier als Ware oder Kleinmaterial).
3. **Qwen3.5 397B denkt lange.** Im Mittel ca. 5.000 Ausgabe-Token und 61 Sekunden je Beleg (höchstens 144 s). Bei IONOS lässt sich das Nachdenken nicht abschalten (getestet: `enable_thinking`, `reasoning_effort`, `/no_think`, alle ohne Wirkung). Bei den beiden längsten Rechnungen (23 und 28 Positionen) reichte das Limit von 8.192 Token nicht, die Antwort brach ab. Mit 24.000 Token: beide vollständig richtig, bei S25 alle 28 Sachkonten. Für die Verarbeitung im Hintergrund (Warteschlange) ist eine Minute je Beleg vertretbar, für eine Live-Demo nicht.
4. **Der Prompt entscheidet mit.** In einer ersten Messung erreichte GPT-OSS bei den Positionen nur 58 %: Es hatte die Anweisung „Bruttopreise auf netto umrechnen“ auf alle Rechnungen angewendet. Qwen3 schrieb Kontonummer und Kontoname zusammen („4910 Porto“). Nach einer eindeutigeren Anweisung und dem Herauslösen der Kontonummer: GPT-OSS 100 % bei den Positionen. Jede Prompt-Änderung muss gegen den Goldstandard gemessen werden.
5. **Gleiches Modell, gleiches Ergebnis:** GPT-OSS 120B liefert bei AWS und bei IONOS praktisch identische Werte. Die Wahl des Anbieters ist damit eine Frage von Recht, Preis und Verfügbarkeit, nicht der Qualität.
6. **Kosten** je Beleg: GPT-OSS 0,08–0,09 Cent, Qwen3 235B 0,07 Cent, Claude 1,27 Cent, Qwen3.5 397B 1,90 Cent. Bei 50.000 Belegen im Monat, wenn jeder Beleg zur KI geht: GPT-OSS ca. 45 €, Claude ca. 635 €, Qwen3.5 ca. 950 €. Wird Qwen3.5 nur für Positionen ohne Lernregel genutzt, sinkt dieser Anteil mit jedem Monat.
7. **E-Rechnungen brauchen keine KI.** Mit der E-Rechnungspflicht im B2B-Bereich (Empfang seit 2025, Versand schrittweise bis 2028) sinkt der KI-Anteil weiter.
8. **Texterkennung:** docTR liest Scans, Kassenbons und das Handyfoto; eine verkehrt herum gescannte Seite wird durch automatische Lageerkennung richtig gelesen.
9. **Pseudonymisierung: sechs Fehler gefunden und behoben** (Telefon-Regel mit unsichtbarem Steuerzeichen, zu gierige Personen-Regel, OCR-Lesefehler im Mandantennamen, fehlendes Hinweiswort „Geschäftsführer“, englische Hinweiswörter und Namenszusätze, Name unter Grußformel). Restrisiko: Namen natürlicher Personen ohne Hinweiswort; dafür kommt in Phase 1 Presidio mit deutschem NER-Modell dazu.
10. **Die regelbasierte Vergleichsstufe (`placeholder`) zeigt, warum KI nötig ist:** auf der eigenen Vorlage 97 %, bei fremden Layouts nur 44–56 %.

---

## 5. Empfehlung und Entscheidungsregel

**Abbruchkriterium Phase A: nicht erreicht.** Alle Zugänge liegen deutlich über 90 %. Das Projekt kann in Phase B (Entwicklung) übergehen.

**Empfohlene Aufteilung (komplett in Deutschland):**

| Schritt | Womit | Warum |
|---|---|---|
| Auslesen (Kopfdaten, Positionen, Steuersätze) | **GPT-OSS 120B bei IONOS** | So gut wie Claude, 0,09 Cent je Beleg, 6 s, deutscher Anbieter mit § 203 in der AVV |
| Kontierung, Stufe 1–3 | Lernregeln je Mandant, Buchungshistorie, Branchen-Regelwerk | Ohne KI, nachvollziehbar, deckt mit der Zeit die meisten Belege ab |
| Kontierung, Stufe 4 (keine Regel greift) | **Qwen3.5 397B bei IONOS**, nur für die betroffenen Positionen | Kontiert fast so gut wie Claude; durch kurzen Prompt nur mit den offenen Positionen weniger Token und schneller als im Test |
| Rückfallebene | Claude über AWS Bedrock EU | Falls IONOS ausfällt oder Qwen3.5 bei echten Belegen schwächer ist |
| Steuerlogik | deterministischer Code | Prüft immer, unabhängig vom Modell (`CLAUDE.md` Regel 15) |

**Entscheidungsregel (ergänzt um die Kontierung):**

| Ergebnis | Entscheidung |
|---|---|
| Deutsches Modell bei Pflichtfeldern und Positionen höchstens 3 Prozentpunkte unter Claude | Deutsches Modell fürs Auslesen (**erfüllt**: GPT-OSS bei IONOS) |
| Deutsches Modell bei der Kontierung höchstens 5 Prozentpunkte unter Claude | Deutsches Modell auch für die Kontierung (**erfüllt**: Qwen3.5 397B, 1 Punkt Abstand) |
| sonst | Claude für die Kontierung |

**Vor der endgültigen Festlegung offen:** anwaltliche Bestätigung, dass die Standard-AVV von IONOS mit § 203-Klausel für eine Steuerkanzlei reicht (Projektplan R3/R3a); Messung mit mindestens 200 vielfältigen Belegen in Phase B; Umbau auf zwei Aufrufe (Auslesen, dann Kontierung nur offener Positionen) und Messung der Kosten dieser Aufteilung.

---

## 6. So wird die Messung wiederholt

1. Zugangsdaten und Modelle in `.env` (nie in einen Chat): `AWS_BEARER_TOKEN_BEDROCK`, `BEDROCK_MODEL_ID`, `BEDROCK_MODEL_GPTOSS`, `BEDROCK_MODEL_QWEN`, `IONOS_API_KEY`, `IONOS_MODEL_GPTOSS`, `IONOS_MODEL_QWEN`. Die IONOS-Modellnamen liefert `scripts/ionos_modelle.py`.
2. Im Ordner `backend`:
   ```
   .venv\Scripts\python scripts\machbarkeitstest.py
   .venv\Scripts\python scripts\auswertung.py
   ```
   Die Auswertung nimmt je Anbieter und Beleg das jüngste Ergebnis aller Läufe; mit Ordnern als Argument nur diese Läufe. Modell und Preise stehen im Lauf.
3. Token-Gültigkeit: AWS-Schlüssel und IONOS-Token laufen nach 30 Tagen ab und müssen dann erneuert werden.

---

## 7. Grenzen des Tests

- Alle Belege sind synthetisch: sechs Layouts, 42 Belege. Echte Lieferanten haben Hunderte Layouts. Für Phase B ist ein Goldstandard mit mindestens 200 Belegen geplant (`CLAUDE.md`, Code-Konventionen).
- Die Sollkontierung ist eine von mehreren vertretbaren. Für eine belastbare Kontierungsquote sollte ein Sachbearbeiter der Kanzlei den Goldstandard einmal prüfen.
- Die erlaubte Kontenliste enthält nur Kontonummer und Namen (25 Konten). Eine vollständige Kontenliste des Mandanten mit mehreren hundert Konten macht die Kontierung schwerer und den Prompt länger.
- An die KI geht nur Text, kein Bild (`docs/entscheidungen/2026-10-28_ki-eingabe-nur-text.md`).
- Gemessen wurde Claude Sonnet 4.6, nicht das in `CLAUDE.md` vorgesehene Sonnet 5.5 (für das AWS-Konto gesperrt).
- Preise (1 $ = 1 € gerechnet): IONOS laut [Preisliste v2026-10-29](https://docs.ionos.com/cloud/support/general-information/price-list/ionos-cloud-gmbh-de) (netto); Claude Sonnet 4.6 3 $ / 15 $ je Million Token; GPT-OSS und Qwen3 bei AWS laut Preisvergleichsseiten ([futureagi.com](https://futureagi.com/llm-cost-calculator/bedrock), [typingmind.com](https://custom.typingmind.com/tools/estimate-llm-usage-costs/amazon-bedrock/qwen-qwen3-235b-a22b-2507-v1-0)), vor dem Pilot auf der offiziellen AWS-Preisseite prüfen.
- Laufzeiten gemessen vom Entwicklungs-PC aus; bei IONOS können sie je nach Auslastung schwanken.
