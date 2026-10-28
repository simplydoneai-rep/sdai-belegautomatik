# Machbarkeitstest – Bericht

Stand: 28.10.2026 · Phase „Test“ aus `CLAUDE.md` · Plan: `docs/plan-machbarkeitstest.md`

---

## 1. Kurzfassung

| Frage | Ergebnis |
|---|---|
| Läuft die Strecke „Beleg rein → strukturierte Daten → Sachkonto-Vorschlag“? | **Ja.** XML, PDF mit Text und Scans laufen durch Auslesen, Pseudonymisierung, Anbieter-Schnittstelle, Steuerlogik-Prüfung und Vergleich mit dem Goldstandard. |
| E-Rechnungen (XRechnung, UBL und CII) | **100 % korrekte Pflichtfelder** bei 20 KoSIT-Dateien, ganz ohne KI. UBL und CII liefern bei allen 33 KoSIT-Fällen identische Werte. |
| Texterkennung für Scans (docTR, lokal) | Alle drei schlechten Scans (Bild, 2,5° schief, verrauscht) werden lesbar erkannt; ca. 5 s je Seite auf dem eigenen PC ohne Grafikkarte. |
| Pseudonymisierung | **0 von 248** geprüften sensiblen Werten erreichen den KI-Text (nach Behebung von vier Fehlern, Abschnitt 4). |
| KI-Anbieter im Vergleich (Bedrock, STACKIT Qwen3-VL, STACKIT GPT-OSS) | **Noch nicht gemessen.** Es liegen noch keine Zugangsdaten in `.env` vor. Die Messung dauert nach Eintragen der Schlüssel wenige Minuten (Abschnitt 6). |
| Kosten je Beleg (KI) | Geschätzt **0,06 Cent (GPT-OSS) bis 0,46 Cent (Claude)** je Beleg, also deutlich unter der Planannahme von 2 Cent. |
| Abbruchkriterium Phase A (unter 90 % bei sauberen PDFs) | Für die KI-Anbieter noch offen. Die regelbasierte Vergleichsstufe erreicht 100 %, ist aber auf die eigenen Testbelege abgestimmt und kein Beleg für fremde Layouts. |

**Vorläufige Empfehlung:** Zuerst STACKIT GPT-OSS 120B messen (deutsch, günstigste Stufe), dann Qwen3-VL 235B, Claude über Bedrock als Qualitätsreferenz. Entscheidungsregel in Abschnitt 5.

---

## 2. Aufbau des Tests

### Testbelege (30)
| Gruppe | Anzahl | Inhalt |
|---|---|---|
| Synthetische PDFs mit Textlayer | 17 | Erfundene Lieferanten und Mandanten aus 5 Branchen (Café, Kfz-Werkstatt, Zimmerei, Werbeagentur, Bäckerei). 7 %, 19 %, gemischt 7/19 % (4×), Gutschrift, Reverse Charge § 13b, innergemeinschaftlicher Erwerb, Kleinbetragsrechnung ohne Rechnungsnummer |
| Synthetische Scans | 3 | Bild in 150 dpi mit JPEG-Artefakten; 2,5° schief; verrauscht mit Flecken und geringem Kontrast |
| KoSIT-XRechnungen | 10 | Aus der offiziellen Testsuite (XRechnung 3.0): 0 %, 7 %, 19 %, gemischt, Reverse Charge (AE), über 20 Positionen, Zu- und Abschläge, negative Mengen. Jeder Fall läuft dreimal: als UBL, als CII (beide ohne KI) und als daraus erzeugte Sicht-PDF durch die KI-Strecke |

Erwartete Ergebnisse je Beleg: `testdaten/goldstandard/*.json`. Erzeugung reproduzierbar mit `backend/scripts/erzeuge_testbelege.py`.

### Ablauf je Beleg
```
XML ──────────────▶ E-Rechnungs-Parser (UBL/CII) ────────────────────────────────┐
PDF mit Text ─────▶ PyMuPDF-Textlayer ─┐                                         ├─▶ Steuerlogik prüft Summen ─▶ Vergleich Goldstandard
Scan ─────────────▶ docTR (lokal) ─────┴─▶ Pseudonymisierung ─▶ LLMProvider ─────┘
```

### Gemessene Felder
- **Pflichtfelder (9):** Lieferant, Rechnungsnummer, Rechnungsdatum, Netto, Steuer, Brutto, Steuersätze, Belegart, Reverse Charge.
- **Positionen:** Nettobetrag, Steuersatz, Sachkonto SKR03 (aus der erlaubten Kontenliste, 23 Konten).
- **Steuerlogik:** Netto + Steuer = Brutto, Steuer passt zu den Positionen, nur 0/7/19 %, Reverse Charge ohne Steuer (Toleranz 0,01 € je Steuersatz).
- **Pseudonymisierung:** Je Beleg werden 5–10 sensible Werte im Text gesucht, der an die KI ginge (exakt und unscharf).

---

## 3. Messwerte

<!-- MESSWERTE:START -->
**Lauf:** `2026-10-28_214731` · Belege: 30 · gemessene Anbieter: erechnung, placeholder

**Nicht gemessen:** `bedrock` (keine AWS-Zugangsdaten in .env); `stackit_qwen` (kein STACKIT_API_KEY in .env); `stackit_gptoss` (kein STACKIT_API_KEY in .env)

### Pflichtfelder je Anbieter und Belegart

| Anbieter | E-Rechnung XML (KoSIT) | PDF mit Text (synthetisch) | PDF mit Text (KoSIT-Sichtbeleg) | Scan (Bild, schief, verrauscht) | Gesamt |
|---|---|---|---|---|---|
| `erechnung` | 100.0 % (20) | – | – | – | **100.0 %** |
| `placeholder` | – | 100.0 % (17) | 100.0 % (10) | 100.0 % (3) | **100.0 %** |

In Klammern: Zahl der Belege. Zielwert Phase A: mindestens 90 % bei sauberen PDFs.

### Trefferquote je Feld (ohne XML)

| Feld | `placeholder` |
|---|---|
| Lieferant | 100.0 % |
| Rechnungsnummer | 100.0 % |
| Rechnungsdatum | 100.0 % |
| Netto | 100.0 % |
| Steuer | 100.0 % |
| Brutto | 100.0 % |
| Steuersätze | 100.0 % |
| Belegart (Rechnung/Gutschrift) | 100.0 % |
| Reverse Charge / i. g. Erwerb | 100.0 % |
| Positionen: Nettobetrag | 99.2 % (118/119) |
| Positionen: Steuersatz | 99.2 % (118/119) |
| Positionen: Sachkonto SKR03 | 94.1 % (48/51) |
| Steuerlogik: Summen plausibel | 100.0 % |

Sachkonten werden nur bei den synthetischen Belegen bewertet (KoSIT-Belege haben keine Sollkontierung).

### Pseudonymisierung

Geprüft: 248 sensible Werte in 30 Belegtexten (Mandantenname, Ansprechpartner, Anschrift, USt-IdNr. des Mandanten, IBAN, E-Mail, Telefon, Steuernummer, Namen natürlicher Personen beim Lieferanten).

**Im KI-Text verblieben: 0 von 248 (0.0 %)**

### Laufzeit je Beleg

| Schritt | Mittelwert | Maximum |
|---|---|---|
| XML parsen | 0.00 s | 0.00 s |
| PDF-Textlayer lesen | 0.00 s | 0.01 s |
| Texterkennung docTR (CPU) | 5.05 s | 8.96 s |
| Anbieter `placeholder` | 0.00 s | 0.00 s |

### Kosten je Beleg (KI-Aufruf)

| Anbieter | Preis Eingabe / Ausgabe je Mio. Token | Token je Beleg (Ø ein / aus) | Kosten je Beleg | Grundlage |
|---|---|---|---|---|
| `bedrock` | 2.00 € / 10.00 € | 1,011 / 262 | 0.0046 € | Schätzung aus Promptlänge, noch nicht gemessen |
| `stackit_qwen` | 1.50 € / 1.75 € | 1,011 / 262 | 0.0020 € | Schätzung aus Promptlänge, noch nicht gemessen |
| `stackit_gptoss` | 0.45 € / 0.65 € | 1,011 / 262 | 0.0006 € | Schätzung aus Promptlänge, noch nicht gemessen |

Hinzu kommen Serverkosten für Texterkennung und Anwendung (siehe `docs/kosten.md`).

### Ergebnisse je Beleg

| Beleg | Merkmale | Art | Anbieter | Pflichtfelder | Positionen Betrag | Konto | Abweichungen |
|---|---|---|---|---|---|---|---|
| K01.01 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.01 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | pdf | `placeholder` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (UBL) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.03 | Zwei Positionen, 7 % | xml (CII) | `erechnung` | 9/9 | 2/2 | – | – |
| K01.04 | Steuerbefreit, 0 % | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.04 | Steuerbefreit, 0 % | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.06 | Sieben Positionen, 19 % | pdf | `placeholder` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.06 | Sieben Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 7/7 | – | – |
| K01.11 | Drei Positionen, 19 % | pdf | `placeholder` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.11 | Drei Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 3/3 | – | – |
| K01.13 | Elf Positionen, 19 % | pdf | `placeholder` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (UBL) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.13 | Elf Positionen, 19 % | xml (CII) | `erechnung` | 9/9 | 11/11 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | pdf | `placeholder` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (UBL) | `erechnung` | 9/9 | 1/1 | – | – |
| K01.21 | Reverse Charge (Kategorie AE) | xml (CII) | `erechnung` | 9/9 | 1/1 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | pdf | `placeholder` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (UBL) | `erechnung` | 9/9 | 23/23 | – | – |
| K02.05 | Über 20 Positionen, 0 % und 19 %, Zu- und Abschläge | xml (CII) | `erechnung` | 9/9 | 23/23 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | pdf | `placeholder` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (UBL) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.01 | 14 Positionen, 7 % und 19 % | xml (CII) | `erechnung` | 9/9 | 14/14 | – | – |
| K03.06 | Austauschteile, negative Menge | pdf | `placeholder` | 9/9 | 3/4 | – | Positionsanzahl |
| K03.06 | Austauschteile, negative Menge | xml (UBL) | `erechnung` | 9/9 | 4/4 | – | – |
| K03.06 | Austauschteile, negative Menge | xml (CII) | `erechnung` | 9/9 | 4/4 | – | – |
| S01 | 7 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S02 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S03 | 19 % | pdf | `placeholder` | 9/9 | 4/4 | 4/4 | – |
| S04 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S05 | Reverse Charge § 13b | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S06 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 2/3 | – |
| S07 | 19 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S08 | 19 %, Lizenz | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S09 | 7 % | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S10 | Gutschrift, 7 % | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S11 | Kleinbetragsrechnung | pdf | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S12 | 19 %, Energie | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S13 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 1/2 | – |
| S14 | 7 % und 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S15 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S16 | 19 % | pdf | `placeholder` | 9/9 | 2/2 | 2/2 | – |
| S17 | innergemeinschaftlicher Erwerb | pdf | `placeholder` | 9/9 | 1/1 | 1/1 | – |
| S18 | Scan: Bild, 7 % und 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S19 | Scan: schief, 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
| S20 | Scan: verrauscht, 7 % und 19 % | scan | `placeholder` | 9/9 | 3/3 | 3/3 | – |
<!-- MESSWERTE:ENDE -->

---

## 4. Befunde

1. **E-Rechnungen brauchen keine KI.** Der eigene Parser liest XRechnung in UBL und CII vollständig. Mit der E-Rechnungspflicht im B2B-Bereich (Empfang seit 2025, Versand schrittweise bis 2028) sinkt der KI-Anteil und damit die Kosten weiter.
2. **Lokale Texterkennung reicht für typische Scans.** docTR liest auch den verrauschten Scan. Typische Lesefehler: Umlaute (ä → a, ß → B), einzelne Buchstaben („Herm“ statt „Herrn“), Punkt statt Komma in Beträgen. Beträge und Steuersätze kamen in allen drei Scans richtig an.
3. **Pseudonymisierung: vier Fehler gefunden und behoben**
   - Die Telefon-Regel enthielt ein unsichtbares Steuerzeichen und erkannte Nummern ohne „+49“ nicht.
   - Die Personen-Regel nahm den Text nach dem Namen über mehrere Leerzeichen hinweg mit (Anschrift des Lieferanten verschwand).
   - Bei OCR-Lesefehlern im Mandantennamen („Backerei Kornteld KG“) griff die exakte Ersetzung nicht. Jetzt unscharfer Abgleich für Mandantenname, Anschrift und Ansprechpartner.
   - „Geschäftsführer“ fehlte als Hinweiswort; auch verlesene Formen („Geschansfohrer“) werden jetzt erkannt.
4. **Restrisiko Pseudonymisierung:** Verlesene Namen natürlicher Personen beim Lieferanten ohne Hinweiswort (z. B. eine Unterschrift) erkennt die Regel nicht. Die Leckprüfung findet verlesene Kennungen (z. B. „449 4289 117“ statt „+49 911 4289 117“) ebenfalls nicht, weil sie Kennungen nur exakt sucht. In Phase 1 kommt Presidio mit deutschem NER-Modell dazu (`CLAUDE.md`, Technik).
5. **Die regelbasierte Vergleichsstufe (`placeholder`) ist kein Qualitätsmaßstab.** Sie ist auf die eine Vorlage der synthetischen Belege abgestimmt. Bei fremden Layouts fällt sie stark ab. Sie dient nur dazu, die Strecke ohne Zugangsdaten zu prüfen.
6. **Kleiner Prompt:** Im Mittel ca. 1.000 Eingabe-Token je Beleg (Planannahme 5.000), weil nur Text und eine kurze Kontenliste gesendet werden. Bei einer vollständigen Kontenliste des Mandanten (mehrere hundert Konten) steigt das auf ca. 3.000–5.000 Token; die Kosten bleiben unter 2 Cent.

---

## 5. Empfehlung und Entscheidungsregel

**Empfehlung, Stand heute:** Noch keine Anbieterwahl. Sie fällt nach der Messung mit Zugangsdaten nach dieser Regel:

| Ergebnis bei sauberen PDFs (Pflichtfelder) | Entscheidung |
|---|---|
| STACKIT-Modell ≥ 90 % und höchstens 3 Prozentpunkte unter Claude | **STACKIT produktiv.** Kein AWS nötig, kein § 203-Addendum über AWS-Partner. |
| STACKIT ≥ 90 %, aber mehr als 3 Punkte unter Claude | STACKIT für den Pilot, Claude als Rückfall für Belege mit geringer Sicherheit; nach 3 Monaten Pilot neu bewerten |
| Nur Claude ≥ 90 % | Bedrock EU, § 203-Addendum über AWS-Partner sofort anstoßen |
| Kein Anbieter ≥ 90 % | Abbruchkriterium Phase A: Architektur überdenken (z. B. Positionen zeilenweise statt im Ganzen auslesen) |

Bei gleicher Qualität entscheidet der Preis: GPT-OSS 120B kostet etwa ein Achtel von Claude.

---

## 6. So wird die Messung vervollständigt

1. `.env.example` nach `.env` kopieren und die Zugangsdaten **direkt in die Datei** eintragen (nicht in einen Chat).
   STACKIT: `STACKIT_API_KEY`, Modellnamen `STACKIT_MODEL_QWEN` und `STACKIT_MODEL_GPTOSS` exakt wie im STACKIT-Portal. Bedrock: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
2. Im Ordner `backend`:
   ```
   .venv\Scripts\python scripts\machbarkeitstest.py
   .venv\Scripts\python scripts\auswertung.py
   ```
3. Die Tabellen in Abschnitt 3 werden automatisch ersetzt. Erwartete Kosten für einen vollständigen Lauf: unter 0,10 € je Anbieter.

---

## 7. Grenzen des Tests

- Die 20 synthetischen Belege nutzen **eine** Vorlage. Echte Rechnungen haben hunderte Layouts. Für Phase B ist ein Goldstandard mit mindestens 200 Belegen aus vielen Vorlagen geplant (`CLAUDE.md`, Code-Konventionen).
- Die KoSIT-Sichtbelege nutzen dieselbe Vorlage; die Lieferantennamen der KoSIT-Dateien sind Platzhalter („[Seller name]“) und wurden durch erfundene Namen ersetzt.
- An die KI geht nur Text, kein Bild (Entscheidung `docs/entscheidungen/2026-10-28_ki-eingabe-nur-text.md`). Die Bildfähigkeit von Qwen3-VL wird deshalb nicht genutzt.
- Laufzeiten der Texterkennung gemessen auf dem Entwicklungs-PC ohne Grafikkarte.
- Der Preis für Claude Sonnet 5.5 über Bedrock (2 $ / 10 $ je Million Token) stammt aus dem Projektplan und ist vor dem Pilot im AWS-Preisrechner für `eu-central-1` zu prüfen. STACKIT-Preise: [STACKIT-Preisliste](https://stackit.com/en/asset/download/37788/file/STACKIT_price_list.pdf?version=18) (GPT-OSS 120B 0,45 € / 0,65 €; Qwen3-VL 1,75 € Ausgabe), Eingabepreis Qwen3-VL 1,50 € laut [european.cloud](https://european.cloud/2025/10/stackit-ai-model-serving/) und [wz-it.com](https://wz-it.com/en/blog/european-llm-api-comparison/), verbindlich bei STACKIT erfragen (E-Mail-Entwurf in `docs/naechste-schritte.md`).
