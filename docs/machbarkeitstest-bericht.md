# Machbarkeitstest – Bericht

Stand: 30.10.2026 · Phase „Test“ aus `CLAUDE.md` · Plan: `docs/plan-machbarkeitstest.md`

---

## 1. Kurzfassung

Drei KI-Modelle über Amazon Bedrock in Frankfurt, gleicher Prompt, 42 Belege:

| | Claude Sonnet 4.6 | GPT-OSS 120B | Qwen3 235B |
|---|---|---|---|
| Pflichtfelder (Kopfdaten) | **99,2 %** | **99,2 %** | **99,5 %** |
| Positionen: Nettobetrag und Steuersatz | 99,4 % | **100 %** | 93,6 % |
| **Sachkonto SKR03** (ohne Lernregeln) | **88,5 %** | 62,5 % | 68,3 % |
| Kosten je Beleg | 1,27 Cent | **0,08 Cent** | **0,07 Cent** |
| Antwortzeit je Beleg | 4 s | 9 s | 6 s |
| Verarbeitung | EU-Regionen (Profil `eu.`) | nur Frankfurt | nur Frankfurt |

| Frage | Ergebnis |
|---|---|
| Zielwert Phase A (90 % Pflichtfelder bei sauberen PDFs) | **Von allen drei Modellen klar erreicht.** Der Machbarkeitstest ist bestanden. |
| Auslesen (Kopfdaten, Positionen) | Die offenen Modelle sind so gut wie Claude, bei rund einem Sechzehntel der Kosten. |
| Kontierung | Claude ist deutlich besser. Die offenen Modelle machen systematische Fehler (Betriebsbedarf auf Wareneingang, Dienstleistungen auf Fremdleistungen), die ein Branchen-Regelwerk abfangen kann. |
| E-Rechnungen (XRechnung, UBL und CII) | **100 %** ohne KI. |
| Texterkennung (docTR, lokal) | Scans, Kassenbons, Handyfoto und verkehrt herum eingezogene Seite werden gelesen; ca. 4 s je Seite ohne Grafikkarte. |
| Pseudonymisierung | **0 von 364** geprüften sensiblen Werten erreichen die KI. |
| Nicht gemessen | STACKIT (Kundenkonto am 30.10.2026 abgelehnt), Claude Sonnet 5.5 (für das AWS-Konto noch gesperrt). |

**Empfehlung:** Auslesen mit einem offenen Modell (GPT-OSS 120B oder Qwen3), Kontierung über Lernregeln und Branchen-Regelwerk, Claude nur dort, wo keine Regel greift. Einzelheiten in Abschnitt 5.

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
**Belege:** 42 · **gemessene Anbieter:** erechnung, bedrock, bedrock_gptoss, bedrock_qwen, placeholder

**Läufe:** `bedrock` aus `2026-10-30_222139`; `bedrock_gptoss` aus `2026-10-30_222139`; `bedrock_qwen` aus `2026-10-30_222139`; `erechnung` aus `2026-10-30_222139`; `placeholder` aus `2026-10-30_222139`

**Modelle:** `bedrock_gptoss` = `openai.gpt-oss-120b-1:0`; `bedrock` = `eu.anthropic.claude-sonnet-4-6`; `bedrock_qwen` = `qwen.qwen3-235b-a22b-2507-v1:0`

**Nicht gemessen:** `stackit_qwen` (kein STACKIT_API_KEY in .env); `stackit_gptoss` (kein STACKIT_API_KEY in .env)

### Pflichtfelder je Anbieter und Belegart

| Anbieter | E-Rechnung XML (KoSIT) | PDF mit Text (synthetisch) | PDF mit Text (KoSIT-Sichtbeleg) | Scan / Foto | Gesamt |
|---|---|---|---|---|---|
| `erechnung` | 100.0 % (20) | – | – | – | **100.0 %** |
| `bedrock` | – | 99.6 % (27) | 97.8 % (10) | 100.0 % (5) | **99.2 %** |
| `bedrock_gptoss` | – | 99.2 % (27) | 100.0 % (10) | 97.8 % (5) | **99.2 %** |
| `bedrock_qwen` | – | 99.2 % (27) | 100.0 % (10) | 100.0 % (5) | **99.5 %** |
| `placeholder` | – | 84.8 % (27) | 100.0 % (10) | 77.8 % (5) | **87.6 %** |

In Klammern: Zahl der Belege. Zielwert Phase A: mindestens 90 % bei sauberen PDFs.

### Pflichtfelder je Layout (PDF, Scan, Foto)

| Layout | Belege | `bedrock` | `bedrock_gptoss` | `bedrock_qwen` | `placeholder` |
|---|---|---|---|---|---|
| bon | 3 | 96.3 % | 88.9 % | 96.3 % | 44.4 % |
| brief | 1 | 100.0 % | 100.0 % | 100.0 % | 55.6 % |
| englisch | 1 | 100.0 % | 100.0 % | 100.0 % | 44.4 % |
| klassisch | 23 | 100.0 % | 100.0 % | 99.5 % | 97.1 % |
| kosit | 10 | 97.8 % | 100.0 % | 100.0 % | 100.0 % |
| modern | 4 | 100.0 % | 100.0 % | 100.0 % | 52.8 % |

Layout „klassisch“ ist die Vorlage, auf die der Platzhalter abgestimmt ist. Die übrigen Layouts zeigen, wie gut ein Anbieter mit fremden Rechnungsbildern umgeht.

### Trefferquote je Feld (ohne XML)

| Feld | `bedrock` | `bedrock_gptoss` | `bedrock_qwen` | `placeholder` |
|---|---|---|---|---|
| Lieferant | 100.0 % | 100.0 % | 100.0 % | 100.0 % |
| Rechnungsnummer | 92.9 % | 92.9 % | 97.6 % | 81.0 % |
| Rechnungsdatum | 100.0 % | 100.0 % | 100.0 % | 78.6 % |
| Netto | 100.0 % | 100.0 % | 100.0 % | 90.5 % |
| Steuer | 100.0 % | 100.0 % | 100.0 % | 85.7 % |
| Brutto | 100.0 % | 100.0 % | 100.0 % | 76.2 % |
| Steuersätze | 100.0 % | 100.0 % | 100.0 % | 76.2 % |
| Belegart (Rechnung/Gutschrift) | 100.0 % | 100.0 % | 100.0 % | 100.0 % |
| Reverse Charge / i. g. Erwerb | 100.0 % | 100.0 % | 97.6 % | 100.0 % |
| Positionen: Nettobetrag | 99.4 % (171/172) | 100.0 % (172/172) | 93.6 % (161/172) | 70.9 % (122/172) |
| Positionen: Steuersatz | 99.4 % (171/172) | 100.0 % (172/172) | 93.6 % (161/172) | 70.9 % (122/172) |
| Positionen: Sachkonto SKR03 | 88.5 % (92/104) | 62.5 % (65/104) | 68.3 % (71/104) | 46.2 % (48/104) |
| Steuerlogik: Summen plausibel | 100.0 % | 100.0 % | 100.0 % | 76.2 % |

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
| Anbieter `placeholder` | 0.00 s | 0.00 s |

### Kosten je Beleg (KI-Aufruf)

| Anbieter | Preis Eingabe / Ausgabe je Mio. Token | Token je Beleg (Ø ein / aus) | Kosten je Beleg | Grundlage |
|---|---|---|---|---|
| `bedrock` | 3.00 € / 15.00 € | 1,727 / 501 | 0.0127 € | gemessen (42 Aufrufe) |
| `bedrock_gptoss` | 0.15 € / 0.60 € | 1,327 / 1,014 | 0.0008 € | gemessen (42 Aufrufe) |
| `bedrock_qwen` | 0.22 € / 0.88 € | 1,559 / 445 | 0.0007 € | gemessen (42 Aufrufe) |
| `stackit_qwen` | 1.50 € / 1.75 € | 1,538 / 653 | 0.0035 € | Schätzung, noch nicht gemessen |
| `stackit_gptoss` | 0.45 € / 0.65 € | 1,538 / 653 | 0.0011 € | Schätzung, noch nicht gemessen |

Hinzu kommen Serverkosten für Texterkennung und Anwendung (siehe `docs/kosten.md`).

### Ergebnisse je Beleg

| Beleg | Merkmale | Art | Anbieter | Pflichtfelder | Positionen Betrag | Konto | Abweichungen |
|---|---|---|---|---|---|---|---|
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock_gptoss` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `bedrock_qwen` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `placeholder` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock` | 8/9 | 3/3 | – | Rechnungsnummer |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `placeholder` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock` | 8/9 | 11/11 | – | Rechnungsnummer |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock_gptoss` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `bedrock_qwen` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `placeholder` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock` | 9/9 | 1/1 | – | Positionsanzahl |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock_gptoss` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `bedrock_qwen` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock` | 9/9 | 23/23 | – | Positionsanzahl |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock_gptoss` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `bedrock_qwen` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `placeholder` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (UBL) | `erechnung` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (CII) | `erechnung` | 9/9 | 23/23 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `placeholder` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (UBL) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (CII) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock_gptoss` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `bedrock_qwen` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `placeholder` | 9/9 | 3/4 | – | Positionsanzahl |
| K03.06 | Austauschteile, negative Menge | xml (UBL) | `erechnung` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | xml (CII) | `erechnung` | 9/9 | 4/4 | – | – |
| S01 | 7 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `bedrock_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `bedrock_qwen` | 9/9 | 4/4 | 4/4 | – |
| S01 | 7 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S02 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S02 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S03 | 19 % | pdf | `bedrock` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `bedrock_qwen` | 9/9 | 4/4 | 4/4 | – |
| S03 | 19 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S04 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S04 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S04 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S05 | Reverse Charge § 13b | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S06 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S06 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S07 | 19 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S07 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 0/3 | – |
| S07 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/3 | 0/3 | – |
| S07 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S08 | 19 %, Lizenz | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S08 | 19 %, Lizenz | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S09 | 7 % | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S09 | 7 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock_gptoss` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `bedrock_qwen` | 9/9 | 1/1 | 1/1 | – |
| S10 | Gutschrift, 7 % | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `bedrock_qwen` | 9/9 | 2/3 | 2/3 | – |
| S11 | Kleinbetragsrechnung | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S12 | 19 %, Energie | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S12 | 19 %, Energie | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S14 | 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S15 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `bedrock` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S16 | 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock` | 9/9 | 1/1 | 1/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock_gptoss` | 9/9 | 1/1 | 1/1 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `bedrock_qwen` | 8/9 | 1/1 | 1/1 | Reverse Charge / i. g. Erwerb |
| S17 | innergemeinschaftlicher Erwerb | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 2/3 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 3/3 | 1/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `placeholder` | 8/9 | 2/3 | 2/3 | Steuersätze, Positionsanzahl |
| S21 | Layout modern, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S21 | Layout modern, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S21 | Layout modern, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S22 | Schlussrechnung mit Abschlag, 19 % | pdf | `placeholder` | 6/9 | 2/2 | 0/2 | Rechnungsnummer, Steuer, Brutto |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock` | 9/9 | 1/2 | 1/2 | – |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `bedrock_qwen` | 9/9 | 1/2 | 1/2 | – |
| S23 | Kassenbon, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S24 | Englisch, Reverse Charge EU-Leistung | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock` | 9/9 | 28/28 | 28/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock_gptoss` | 9/9 | 28/28 | 20/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `bedrock_qwen` | 9/9 | 28/28 | 20/28 | – |
| S25 | Mehrseitig, 28 Positionen, 7 % und 19 % | pdf | `placeholder` | 5/9 | 0/28 | 0/28 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock_gptoss` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `bedrock_qwen` | 9/9 | 3/3 | 2/3 | – |
| S26 | Positionsrabatt, Versandkosten, 19 % | pdf | `placeholder` | 8/9 | 1/3 | 0/3 | Rechnungsnummer, Positionsanzahl |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `bedrock_qwen` | 9/9 | 0/2 | 0/2 | – |
| S27 | Bruttopreise über 250 €, 19 % | pdf | `placeholder` | 4/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 2/2 | – |
| S28 | Brief ohne Tabelle, Miete, 19 % | pdf | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock_gptoss` | 8/9 | 3/3 | 3/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `bedrock_qwen` | 8/9 | 0/3 | 0/3 | Rechnungsnummer |
| S29 | Bewirtungsbeleg, Kleinbetragsrechnung | pdf | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock` | 9/9 | 3/3 | 1/3 | – |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock_gptoss` | 8/9 | 3/3 | 0/3 | Rechnungsnummer |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `bedrock_qwen` | 9/9 | 0/3 | 0/3 | – |
| S30 | Handyfoto, Kassenbon, Kleinbetragsrechnung | foto | `placeholder` | 4/9 | 0/3 | 0/3 | Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Positionsanzahl |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `bedrock_qwen` | 9/9 | 2/2 | 0/2 | – |
| S31 | Scan auf dem Kopf, 7 % und 19 % | scan | `placeholder` | 5/9 | 0/2 | 0/2 | Rechnungsnummer, Rechnungsdatum, Brutto, Steuersätze, Positionsanzahl |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock` | 9/9 | 2/2 | 2/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock_gptoss` | 9/9 | 2/2 | 0/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `bedrock_qwen` | 9/9 | 2/2 | 1/2 | – |
| S32 | Viele Nummern auf dem Beleg, GWG, 19 % | pdf | `placeholder` | 8/9 | 2/2 | 1/2 | Rechnungsnummer |
<!-- MESSWERTE:ENDE -->

---

## 4. Befunde

1. **Auslesen: Alle drei Modelle erreichen den Zielwert deutlich.** Kopfdaten 99,2–99,5 %. Die verbleibenden Abweichungen:
   - **K01.11, K01.13:** In den KoSIT-Testdateien steht als Rechnungsnummer wörtlich „Rechnungsnummer“ (Platzhalter der Testsuite). Die Modelle geben keine Nummer zurück, was fachlich richtig ist. Fehler im Testdatensatz.
   - Kassenbons ohne Rechnungsnummer und mit Bruttopreisen sind für alle Modelle die schwierigste Belegart (89–96 % der Pflichtfelder).
2. **Der Prompt entscheidet mit.** In einer ersten Messung erreichte GPT-OSS bei den Positionen nur 58 %: Es hatte die Anweisung „Bruttopreise auf netto umrechnen“ auf alle Rechnungen angewendet und jeden Positionsbetrag durch 1,19 geteilt. Qwen schrieb Kontonummer und Kontoname zusammen („4910 Porto“). Nach einer eindeutigeren Anweisung und dem Herauslösen der Kontonummer: GPT-OSS 100 % bei den Positionen. Folgerung: Jede Prompt-Änderung muss gegen den Goldstandard gemessen werden; das Messskript ist dafür da.
3. **Kontierung: Claude 88,5 %, offene Modelle 62–68 %.** Die Fehler der offenen Modelle sind systematisch:
   - Betriebsbedarf (Spülmittel, Backpapier, Kartons) auf 3400 Wareneingang statt 4980 (GPT-OSS 13-mal, Qwen 10-mal)
   - Dienstleistungen (Werbung, Lizenzen, Wartung, Telefon, Porto) auf 3100 Fremdleistungen
   
   Claudes Abweichungen sind dagegen überwiegend Ermessensfragen (Schleifpapier als Ware oder Kleinmaterial). Systematische Fehler lassen sich mit einem Branchen-Regelwerk und Lernregeln je Mandant abfangen, die ohnehin vor der KI greifen (`CLAUDE.md` Abschnitt 5).
4. **Kosten:** Claude 1,27 Cent je Beleg, GPT-OSS 0,08 Cent, Qwen 0,07 Cent. GPT-OSS „denkt“ vor der Antwort und erzeugt etwa doppelt so viele Ausgabe-Token wie die anderen, ist wegen des Preises aber trotzdem sehr günstig. Bei 50.000 Belegen im Monat: Claude ca. 635 €, offene Modelle ca. 35–40 €, jeweils wenn jeder Beleg zur KI geht.
5. **E-Rechnungen brauchen keine KI.** Der eigene Parser liest XRechnung in UBL und CII vollständig. Mit der E-Rechnungspflicht im B2B-Bereich (Empfang seit 2025, Versand schrittweise bis 2028) sinkt der KI-Anteil weiter.
6. **Texterkennung:** docTR liest Scans, Kassenbons und das Handyfoto. Eine verkehrt herum gescannte Seite wird durch automatische Lageerkennung richtig gelesen. Große Fotos werden vorher verkleinert (30 s → 2 s).
7. **Pseudonymisierung: sechs Fehler gefunden und behoben** (Telefon-Regel mit unsichtbarem Steuerzeichen, zu gierige Personen-Regel, OCR-Lesefehler im Mandantennamen, fehlendes Hinweiswort „Geschäftsführer“, englische Hinweiswörter und Namenszusätze, Name unter Grußformel). Restrisiko: Namen natürlicher Personen ohne Hinweiswort; dafür kommt in Phase 1 Presidio mit deutschem NER-Modell dazu.
8. **Die regelbasierte Vergleichsstufe (`placeholder`) zeigt, warum KI nötig ist:** auf der eigenen Vorlage 97 %, bei fremden Layouts nur 44–56 %.

---

## 5. Empfehlung und Entscheidungsregel

**Abbruchkriterium Phase A: nicht erreicht.** Alle drei Modelle liegen deutlich über 90 %. Das Projekt kann in Phase B (Entwicklung) übergehen.

**Empfohlene Aufteilung:**

| Schritt | Womit | Warum |
|---|---|---|
| Auslesen (Kopfdaten, Positionen, Steuersätze) | **offenes Modell** (GPT-OSS 120B oder Qwen3 235B) | Gleiche Qualität wie Claude, ein Sechzehntel der Kosten, austauschbar (läuft auch bei IONOS oder auf eigenem Server) |
| Kontierung, Stufe 1–3 | Lernregeln je Mandant, Buchungshistorie, Branchen-Regelwerk | Ohne KI, nachvollziehbar, deckt mit der Zeit die meisten Belege ab |
| Kontierung, Stufe 4 (keine Regel greift) | **Claude** über Bedrock EU | Beste Kontierung ohne Vorwissen; fällt nur bei unbekannten Lieferanten und Positionen an |
| Steuerlogik | deterministischer Code | Prüft immer, unabhängig vom Modell (`CLAUDE.md` Regel 15) |

**Zur ursprünglichen Regel:** Die Regel vom 28.10.2026 bewertete nur die Pflichtfelder. Danach wäre ein offenes Modell „produktiv“ (99,2–99,5 % gegenüber 99,2 % bei Claude). Die Messung zeigt aber, dass die Kontierung der eigentliche Unterschied ist. Die Regel wird deshalb um die Kontierung ergänzt:

| Ergebnis | Entscheidung |
|---|---|
| Offenes Modell bei Pflichtfeldern und Positionen höchstens 3 Prozentpunkte unter Claude | Offenes Modell für das Auslesen (**erfüllt**) |
| Offenes Modell bei der Kontierung höchstens 5 Prozentpunkte unter Claude | Offenes Modell auch für die Kontierung (**nicht erfüllt**, 20–26 Punkte Abstand) |
| sonst | Claude für die Kontierung, bis das Branchen-Regelwerk den Abstand schließt; nach Phase 3 neu messen |

**Noch offen vor der endgültigen Wahl:** Messung von Claude Sonnet 5.5 (sobald AWS freischaltet) und Prüfung, ob ein deutscher Anbieter (IONOS) GPT-OSS oder Qwen anbietet und eine § 203-Vereinbarung abschließt.

---

## 6. So wird die Messung wiederholt

1. Modelle in `.env`: `BEDROCK_MODEL_ID` (Claude), `BEDROCK_MODEL_GPTOSS`, `BEDROCK_MODEL_QWEN`. Zugangsdaten nur direkt in `.env`, nie in einen Chat.
2. Im Ordner `backend`:
   ```
   .venv\Scripts\python scripts\machbarkeitstest.py
   .venv\Scripts\python scripts\auswertung.py
   ```
   Die Auswertung führt automatisch je Anbieter den jüngsten vollständigen Lauf zusammen; mit einem Ordner als Argument wertet sie nur diesen Lauf aus. Modell und Preise stehen im Lauf.
3. **Claude Sonnet 5.5:** AWS meldet „not available for this account“. Freischaltung über eine Support-Anfrage bei AWS (Verwaltungskonto, Region eu-central-1).

---

## 7. Grenzen des Tests

- Alle Belege sind synthetisch: sechs Layouts, 42 Belege. Echte Lieferanten haben Hunderte Layouts. Für Phase B ist ein Goldstandard mit mindestens 200 Belegen geplant (`CLAUDE.md`, Code-Konventionen).
- Die Sollkontierung ist eine von mehreren vertretbaren. Für eine belastbare Kontierungsquote sollte ein Sachbearbeiter der Kanzlei den Goldstandard einmal prüfen.
- Die erlaubte Kontenliste enthält nur Kontonummer und Namen (25 Konten). Kurze Beschreibungen je Konto könnten die Kontierung der offenen Modelle verbessern; noch nicht gemessen.
- An die KI geht nur Text, kein Bild (`docs/entscheidungen/2026-10-28_ki-eingabe-nur-text.md`).
- Gemessen wurde Claude Sonnet 4.6, nicht das in `CLAUDE.md` vorgesehene Sonnet 5.5.
- Preise (1 $ = 1 € gerechnet): Claude Sonnet 4.6 3 $ / 15 $ je Million Token; GPT-OSS 120B 0,15 $ / 0,60 $ und Qwen3 235B 0,22 $ / 0,88 $ laut Preisvergleichsseiten ([futureagi.com](https://futureagi.com/llm-cost-calculator/bedrock), [pricepertoken.com](https://pricepertoken.com/endpoints/compare/amazon-bedrock-vs-openrouter), [typingmind.com](https://custom.typingmind.com/tools/estimate-llm-usage-costs/amazon-bedrock/qwen-qwen3-235b-a22b-2507-v1-0)). Vor dem Pilot auf der offiziellen AWS-Preisseite für `eu-central-1` prüfen; die tatsächliche Abrechnung steht in der AWS-Konsole unter „Rechnungen“.
- Laufzeiten gemessen auf dem Entwicklungs-PC ohne Grafikkarte.
