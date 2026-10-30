# Projektprotokoll – Simply Done AI: Belegautomatik

Chronologisches Protokoll aller Termine, Recherchen und Entscheidungen. Neueste Einträge unten anfügen.

---

## 22.10.2026 – Projektidee

- Idee: Teil der cisbox-Funktionen selbst bauen. Eingangsrechnung rein, Texterkennung, Buchungsvorschlag, Korrektur, System lernt dazu, Ausgabe als Buchungssatz.
- Einschätzung: technisch machbar. Schwierigkeiten liegen bei Sonderfällen (mehrere Steuersätze, Reverse Charge, Gutschriften), Kontenrahmen, Kreditorenstammdaten, GoBD und Datenschutz.

## 27.10.2026 – Vorbereitung cisbox-Termin

- Fragenkatalog als Dokument erstellt: Datenschutz, Hosting, KI, Buchungsvorschlag, Sicherheit, Schnittstellen, Kosten.
- Schwerpunktfragen: Datenverarbeitung in Vietnam, eingesetzte KI-Modelle, Training mit Kundendaten, Lernlogik.

## 28.10.2026 – Termin mit cisbox

**Teilnehmer:** Anna Matysiak, Marcus Wenzel, Paul Graß, später Markus Pfaar.
**Quelle:** Mitschrift von Paul Graß (Präsentationsfolie, Demo, mündliche Aussagen).

### Aussagen cisbox
| Thema | Aussage |
|---|---|
| KI | „Eigene KI“, keine US-amerikanischen KI-Anbieter. Keine Angabe zu Art oder Modell. |
| Hosting und Sicherheit | EU-Hosting, ISO 27001, revisionssicheres Archiv mit Zertifikat. |
| Lernen | Mandantenübergreifend aus einem globalen, anonymisierten Datenbestand mit branchenspezifischen Buchungssätzen. |
| Branchenerkennung | Analyse der Website des Mandanten, daraus Anpassung von Branche und Buchungslogik. |
| Datenschutz | AVV mit Steuerbüro und AVV zwischen Steuerbüro und Mandant. |
| Eingang | Upload per Drag & Drop, E-Mail-Adresse je Mandant, Scan. Automatische Rückmail an Mandanten bei Fehlern. |
| DATEV | Stammdaten aus DATEV-Export, Ausgabe über Buchungsdatenservice nach Unternehmen Online. |
| Schnittstellen | Offene APIs. |
| Funktionen (Demo) | Dublettenprüfung, Gruppierung nach Kreditor, Kategorisierung und Aufteilung von Positionen, Originalbeleg mit Hover-Ansicht, Einheiten, interne und Mandanten-Kommunikation, Rechte je Sachbearbeiter und Mandant, Export nach Sachkonto. |
| Planung | Q2 2027 einfaches Zahlungswesen mit Mahnwesen. Ausgangsrechnungen nicht geplant. |
| Preis | 0,70 € pro Beleg, günstiger bei mehr Belegen (ohne genannte Grenze). |
| Test | 1–2 Monate mit 4 Mandanten. |

### Kritik Markus Pfaar (Geschäftsführer Kanzlei)
- Testphase zu kurz und zu klein. Besser 10 Mandanten über 6 Monate.
- Kanzleigröße: 5,5 Mio. € Umsatz, 50 Mitarbeiter, über 1.000 Mandanten.

### Bewertung
- **Kosten:** Bei angenommenen 50 Eingangsrechnungen je Mandant und Monat rund 50.000 Belege, also etwa 35.000 € im Monat oder 420.000 € im Jahr vor Rabatt. Entspricht etwa 7–8 % des Kanzleiumsatzes.
- **„Eigene KI“ nicht belegt.** „Keine US-KI“ ist nicht dasselbe wie eine eigene KI.
- **Mandantenübergreifendes Lernen ist berufsrechtlich heikel** (§ 203 StGB, § 62a StBerG). Anonymisierung von Rechnungsdaten ist oft nicht vollständig.
- **AVV zwischen Steuerbüro und Mandant ist nicht nötig** (§ 11 StBerG, siehe Recherche Nr. 5).
- **Vietnam nicht angesprochen.** Offen, ob dort Menschen Belege sehen.
- Testphase nur mit vorher festgelegten Messgrößen sinnvoll.

## 28.10.2026 – Entscheidung zum eigenen Projekt

- Die Kanzlei wägt ab: cisbox testen oder den DATEV Automatisierungsservice weiter ausbauen.
- Simply Done AI (Paul Graß, geschäftsführender Gesellschafter) prüft, die Lösung selbst und günstiger zu bauen.
- **Alleinstellung gegenüber DATEV:** branchenspezifische Vorschläge ab dem ersten Beleg, detailreichere Aufteilung nach Positionen, günstigerer Preis.
- **Konzept erstellt:** `CLAUDE.md` mit Ziel, Architektur, Regeln, Lernlogik, DATEV-Export und Phasenplan.
- **Arbeitsweise:** Umsetzung in Claude Code mit `opusplan` (Opus 5.5 plant, Sonnet 5.5 setzt um), Effort `high`. Fable nicht nötig.
- **Arbeitsregel für Claude:** Keine Gegenfragen. Offene Punkte selbst recherchieren und beantworten.

## 28.10.2026 – Recherche zu Recht, Hosting und KI

Vollständige Ergebnisse mit Quellen: `docs/recherche/2026-10-28_recht-hosting-ki.md`.

**Kernergebnisse:**
1. Hetzner unterschreibt Verschwiegenheitsvereinbarungen nach § 203 StGB.
2. AWS bietet ein § 203-Addendum nur individuell über Partner an. Bedrock-Abdeckung muss ausdrücklich drinstehen.
3. Claude über Bedrock mit EU-Inferenzprofil hält die Daten in der EU. Fable ausschließen.
4. Hetzner Object Storage verschlüsselt nicht automatisch. Eigene Verschlüsselung ist Pflicht.
5. Steuerberater sind keine Auftragsverarbeiter ihrer Mandanten.
6. Für Claude Code bei Pro/Max die Trainings-Einstellung ausschalten.

**Änderungen an der CLAUDE.md:** Verschlüsselung, Zweitsicherung, Bedrock-Profil, Fable-Ausschluss und erledigte Rechtsfragen eingearbeitet.

## 28.10.2026 – Projektplan erstellt

Vollständiger Plan: `docs/projektplan.md`.

**Ergebnis:** Projekt ist umsetzbar. Größte Risiken: Kapazität neben dem Hauptberuf, Wettbewerb mit dem DATEV-Service, Vertragskette nach § 203 StGB.

**Neue Erkenntnisse:**
- BStBK-FAQ zu KI vom 27.10.2026: private KI-Konten für berufliche Zwecke unzulässig; bei mandatsbezogener KI-Nutzung Einwilligung der Mandanten ratsam; Berufsträger bleibt verantwortlich; KI-Kompetenzpflicht nach Art. 4 AI Act.
- KI-Kosten ca. 0,02 € pro Beleg (Claude Sonnet 5.5: 2 $ / 10 $ je Million Token).
- Echte XRechnung-Testbelege frei verfügbar (KoSIT-Testsuite).

**Zeitplan:** Machbarkeitstest bis 15.11.2026, erstes Produkt bis Ende Februar 2027, Pilot März bis August 2027, Entscheidung Markteintritt September 2027.

**Entscheidungen:**
- Pilot ist ein Vergleichstest gegen den DATEV Automatisierungsservice bei denselben Mandanten.
- Interessenkonflikt (Angestellter Kanzlei und Geschäftsführer Simply Done AI) wird vor dem Pilot schriftlich geregelt.
- Revisionssicherheit in zwei Stufen: im Pilot DATEV als Archiv, nach Markteintritt IDW-PS-880-Testat.

## 28.10.2026 – Vorgehen und Kosten

**Entscheidung:** Erst bauen, dann mit einer Demo zu Markus Pfaar. Rechtliche Verträge laufen parallel und sind erst vor dem ersten echten Mandantenbeleg Pflicht. Bis dahin nur Testdaten.

**Kosten** (Details: `docs/kosten.md`):
- Bauen und Demo: ca. 110–160 € pro Monat, davon 100 $ Claude Max
- Pilot: ca. 230 € pro Monat plus ca. 5.000–12.000 € einmalig (Schätzung)
- Betrieb ganze Kanzlei: ca. 1.450 € pro Monat, ca. 0,03 € pro Beleg

**Neue Erkenntnisse:**
- Hetzner hat die Cloud-Preise am 15.06.2026 stark erhöht; günstige CX-Linie nicht bestellbar.
- Rückfallebene mit eigenem KI-Modell in Deutschland kostet mindestens 1.499 € pro Monat (GEX131); günstiger GEX45 nur in Helsinki.

## 28.10.2026 – Abhängigkeit von AWS und Fixkosten

Details: `docs/recherche/2026-10-28_ki-anbieter-ohne-aws.md`, `docs/kosten.md`.

**Ergebnis:** Simply Done AI ist nicht auf AWS angewiesen.
- Deutsche Alternativen ohne Fixkosten: STACKIT AI Model Serving (u. a. Qwen3-VL 235B mit Bilderkennung) und IONOS AI Model Hub.
- Telekom T-Cloud LLM Hub ist rechtlich am saubersten, hat aber 1.000 € Mindestumsatz pro Monat.
- E-Rechnungen, Lernregeln und Buchungshistorie brauchen keine KI; die KI wird nur für PDFs und Scans unbekannter Lieferanten gebraucht.
- EuGH C-413/23 P (04.09.2025) und BStBK-FAQ: Bei wirksamer Pseudonymisierung kommen beim KI-Anbieter keine Geheimnisse an. Vor dem Pilot anwaltlich bestätigen lassen.

**Fixkosten extern:** Demo 20 € pro Monat (nur Claude Pro). Pilot ca. 120–145 € pro Monat (Claude Pro + Hetzner). KI-Anbieter ohne Grundgebühr.

**Korrektur:** Das Claude-Pro-Abo deckt nicht die KI-Aufrufe der eigenen Software; diese laufen über ein separates Konto beim KI-Anbieter (Verbrauch, in der Demo unter 10 €).

**Entscheidung:** Der KI-Anbieter wird im Machbarkeitstest anhand von Messwerten gewählt (Claude über Bedrock gegen STACKIT). `CLAUDE.md` Regel 5 entsprechend erweitert.

## 28.10.2026 – Start der Umsetzung

Anleitung mit Einrichtung, erstem Auftrag für Claude Code und E-Mail-Entwürfen: `docs/naechste-schritte.md`.

**Entscheidung:** Gespräch mit Markus Pfaar nicht erst im Februar, sondern spätestens 27.11.2026 mit Machbarkeitstest-Bericht und kleiner Demo. Grund: Die Kanzlei entscheidet gerade über einen cisbox-Test.

**Entscheidung Paul Graß:** Es erfolgt keine E-Mail an cisbox. Die offenen Punkte zu cisbox (KI-Modell, Zugriff aus Vietnam, Unterauftragsverarbeiter) werden nicht weiter verfolgt.

## 28.10.2026 – Machbarkeitstest: Strecke gebaut, KI-Vergleich wartet auf Zugangsdaten

Umgesetzt mit Claude Code. Plan: `docs/plan-machbarkeitstest.md`, Bericht: `docs/machbarkeitstest-bericht.md`.

**Gebaut:**
- 30 Testbelege mit Goldstandard: 20 synthetische (davon 3 schlechte Scans) und 10 KoSIT-XRechnungen (je als UBL, CII und Sicht-PDF).
- Strecke: E-Rechnungs-Parser (UBL, CII), PDF-Textlayer, lokale Texterkennung docTR, Pseudonymisierung, Anbieter Bedrock / STACKIT / Platzhalter, Steuerlogik-Prüfung der Summen, Vergleich mit Goldstandard, automatisch erzeugte Messtabellen.
- 85 automatische Tests (Pseudonymisierung, Beträge, Steuerlogik, E-Rechnung, Vergleich, Anbieter-Schnittstelle).

**Ergebnisse:**
- E-Rechnungen: 100 % korrekte Pflichtfelder ohne KI.
- Texterkennung: alle drei schlechten Scans lesbar, ca. 5 s je Seite ohne Grafikkarte.
- Pseudonymisierung: 0 von 248 sensiblen Werten im KI-Text, nach Behebung von vier Fehlern (u. a. Telefon-Regel griff wegen eines unsichtbaren Steuerzeichens nur bei Nummern mit „+“, Mandantenname mit OCR-Lesefehler wurde nicht ersetzt).
- Kosten KI je Beleg (Schätzung): GPT-OSS 120B ca. 0,06 Cent, Qwen3-VL ca. 0,2 Cent, Claude Sonnet 5.5 ca. 0,5 Cent. STACKIT-Preise recherchiert und in `backend/app/llm/preise.json` mit Quelle hinterlegt.
- **Offen:** Messung der drei KI-Anbieter. Keine Zugangsdaten in `.env`. Danach zwei Befehle (Bericht, Abschnitt 6).

**Entscheidungen** (`docs/entscheidungen/`): nur Text an die KI, kein Bild; Zusammensetzung Testbelege und Goldstandard; Pseudonymisierung ohne Presidio bis Phase 1; regelbasierter Platzhalter-Anbieter; Python 3.14 für den Test, Ziel 3.12. Dazu eine Entscheidungsregel für die Anbieterwahl (Bericht, Abschnitt 5).

**Git:** Repository eingerichtet (`.gitignore`, `.gitattributes`, `.env.example`) und zu GitHub hochgeladen: `https://github.com/simplydoneai-rep/sdai-belegautomatik` (privat).

**Verfahrensdokumentation:** Keine Änderung nötig, es werden noch keine echten Belege verarbeitet. Wird mit Phase 0 angelegt.

## 28.10.2026 – Konten, Zusatzbelege und erste KI-Messung

**Konten:**
- STACKIT: Kundenkonto für Simply Done AI beantragt, Prüfung durch STACKIT läuft.
- AWS: Konto auf bezahlten Tarif umgestellt (Guthaben 100 $ bleibt), erweiterte Funktionen aktiviert (nicht umkehrbar; hartes Ausgabenlimit entfällt dadurch), Budget-Alarm 20 $ im Verwaltungskonto, Anthropic-Formular eingereicht, langfristiger Bedrock-API-Schlüssel (30 Tage) in `.env`. Claude Sonnet 5 und 5.5 sind für das neue Konto noch gesperrt („not available for this account“), Sonnet 4.6 funktioniert.

**Zusatzbelege:** 12 Belege mit fremden Layouts (modern, englisch, Kassenbon, Brief, Handyfoto, Scan auf dem Kopf), zusammen jetzt 42 Belege. Entscheidung: `docs/entscheidungen/2026-10-28_zusatzbelege.md`.

**Dabei gefunden und behoben:** Texterkennung las verkehrt herum gescannte Seiten nicht (jetzt automatische Lageerkennung). Pseudonymisierung übersah englische Hinweiswörter, Namenszusätze („van“) und Namen unter Grußformeln. 90 Tests grün.

**Erste KI-Messung (Claude Sonnet 4.6, Bedrock Frankfurt):** 99,2 % richtige Pflichtfelder über alle 42 Belege, 100 % bei allen fremden Layouts, Sachkonto 88,5 % ohne Lernen, 1,2 Cent je Beleg. Zielwert 90 % klar erreicht, **Abbruchkriterium Phase A nicht erreicht**. Pseudonymisierung: 0 von 364 sensiblen Werten bei der KI. Bericht: `docs/machbarkeitstest-bericht.md`.

**Offen:** STACKIT-Messung nach Freischaltung, dann Anbieterwahl nach der Regel im Bericht (Abschnitt 5). Freischaltung Claude Sonnet 5.5 bei AWS anfragen.

## 30.10.2026 – STACKIT-Absage, Vergleich von drei Modellen über Bedrock

**STACKIT** hat das Kundenkonto von Simply Done AI ohne Angabe von Gründen abgelehnt. Nachfrage über den STACKIT-Support möglich.

**Claude Sonnet 5.5** ist für das AWS-Konto weiterhin gesperrt („not available for this account“); Freischaltung nur über eine Support-Anfrage bei AWS.

**Entscheidung (Paul Graß: „Wir machen weiter mit AWS“):** Die offenen Modelle GPT-OSS 120B und Qwen3 235B werden über Bedrock gemessen; sie laufen dort direkt in Frankfurt. `CLAUDE.md` Regel 5 entsprechend erweitert. Details: `docs/entscheidungen/2026-10-30_bedrock-regionale-modelle.md`.

**Ergebnis** (42 Belege, gleicher Prompt, Bericht `docs/machbarkeitstest-bericht.md`):

| | Claude Sonnet 4.6 | GPT-OSS 120B | Qwen3 235B |
|---|---|---|---|
| Pflichtfelder | 99,2 % | 99,2 % | 99,5 % |
| Positionen | 99,4 % | 100 % | 93,6 % |
| Sachkonto | 88,5 % | 62,5 % | 68,3 % |
| Kosten je Beleg | 1,27 Cent | 0,08 Cent | 0,07 Cent |

**Erkenntnisse:**
- Beim Auslesen sind die offenen Modelle so gut wie Claude, bei einem Sechzehntel der Kosten. Bei der Kontierung ist Claude deutlich besser.
- Eine missverständliche Prompt-Anweisung hatte GPT-OSS anfangs auf 58 % bei den Positionen gedrückt (Nettobeträge fälschlich durch 1,19 geteilt). Nach Präzisierung 100 %. Kontonummern werden jetzt aus der KI-Antwort herausgelöst und gegen die erlaubte Liste geprüft.
- Kosten aller Messläufe bisher zusammen ca. 1,20 $ aus dem AWS-Guthaben.

**Empfehlung:** Auslesen mit offenem Modell, Kontierung über Lernregeln und Branchen-Regelwerk, Claude nur für Positionen ohne Regel. Endgültige Wahl nach Messung von Sonnet 5.5 und Prüfung eines deutschen Anbieters (IONOS).

## 30.10.2026 – IONOS AI Model Hub als deutsche Alternative

Recherche: `docs/recherche/2026-10-30_ionos-ai-model-hub.md`.

**Ergebnis:** IONOS (IONOS Cloud GmbH, Rechenzentren in Deutschland) bietet GPT-OSS 120B zu 0,15 € / 0,65 € je Million Token an, also dasselbe Modell, das über Bedrock 99,2 % der Pflichtfelder und 100 % der Positionen erreichte. Prompts und Antworten werden laut IONOS nicht gespeichert und nicht zum Training genutzt. Die Standard-AVV enthält eine Verpflichtung nach § 203 StGB. Kein Claude im Angebot.

**Vorbereitet:** Anbieter `ionos_gptoss` und `ionos_qwen` (Qwen3.5-397B), Skript `backend/scripts/ionos_modelle.py` zum Abfragen der Modellnamen, Preise in `preise.json`.

**Nächster Schritt (Paul Graß):** IONOS-Cloud-Konto für Simply Done AI anlegen, Token erzeugen und in `.env` eintragen.

## 31.10.2026 – Messung bei IONOS: deutsche Lösung ohne AWS möglich

**Konto:** IONOS-Cloud-Konto lief zunächst als „Testdrive“; Zugangstoken erst nach Freischaltung der Vollversion (200 € Startguthaben). Token (30 Tage) in `.env`.

**Ergebnis** (42 Belege, gleicher Prompt wie bei AWS):

| | Claude Sonnet 4.6 (AWS) | GPT-OSS 120B (IONOS) | Qwen3.5 397B (IONOS) |
|---|---|---|---|
| Pflichtfelder | 99,2 % | 98,9 % | 98,7 % |
| Positionen | 99,4 % | 100 % | 100 % |
| Sachkonto | 88,5 % | 61,5 % | **87,5 %** |
| Kosten je Beleg | 1,27 Cent | 0,09 Cent | 1,90 Cent |
| Antwortzeit | 3 s | 6 s | 61 s |

**Erkenntnisse:**
- Qwen3.5 397B bei IONOS kontiert fast so gut wie Claude. Damit ist eine komplett deutsche Lösung möglich, mit § 203-Klausel in der Standard-AVV.
- Qwen3.5 denkt lange; bei IONOS nicht abschaltbar. Zwei lange Rechnungen brachen beim Limit von 8.192 Token ab; mit 24.000 Token vollständig richtig.
- GPT-OSS liefert bei IONOS und AWS dieselbe Qualität.

**Empfehlung (Bericht, Abschnitt 5):** Auslesen mit GPT-OSS bei IONOS, Kontierung über Regeln, Qwen3.5 bei IONOS nur für Positionen ohne Regel, Claude über AWS als Rückfallebene. Vorher anwaltlich prüfen lassen, ob die IONOS-AVV reicht.

**Kosten der Messungen:** IONOS ca. 0,90 € aus dem Startguthaben; AWS bisher ca. 1,20 $ aus dem Guthaben.

## Nächste Schritte

Die aktuelle Aufgabenliste steht in `docs/projektplan.md`, Abschnitt 10. Die Liste unten ist der Stand vom 28.10.2026 vor dem Projektplan.

| Nr. | Aufgabe | Zuständig |
|---|---|---|
| 1 | Trainings-Einstellung in claude.ai prüfen und ausschalten | Paul Graß |
| 2 | Claude Code im Projektordner starten, Phase 0 umsetzen | Paul Graß mit Claude Code |
| 3 | § 203-Vereinbarung bei Hetzner anfordern | Simply Done AI |
| 4 | § 203-Addendum für AWS Bedrock über AWS-Partner anfragen (Vorlauf einplanen) | Simply Done AI |
| 5 | Preis des DATEV Automatisierungsservice aus der Kanzlei-Preisliste ermitteln | Kanzlei |
| 6 | ~~Bei cisbox schriftlich anfordern: KI-Modell, Vietnam-Zugriff, Liste der Unterauftragsverarbeiter, AVV, Testat zur Revisionssicherheit~~ – entfällt, Entscheidung 28.10.2026 | – |
| 7 | Messgrößen für jeden Test festlegen (Übernahmequote, Minuten pro Beleg, Fehlerquote) | Kanzlei und Simply Done AI |
| 8 | Vereinbarung Kanzlei ↔ Simply Done AI (AVV + § 62a StBerG) entwerfen lassen | Simply Done AI |
