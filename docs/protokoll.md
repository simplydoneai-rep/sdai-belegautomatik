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

## 31.10.2026 – Kalkulation: Server, Speicher, Verwaltung, Rechtsberatung, Preis

Vollständig: `docs/kosten.md` (neu gefasst), `docs/rechtsberatung.md` (neu).

**Ergebnisse bei 50.000 Belegen im Monat:**
- **Speicher:** ca. 30 GB im Monat, 3,2 TB je Kopie nach voller Aufbewahrung; Hetzner Object Storage an zwei Standorten 13 € (Jahr 1) bis 42 € im Monat. Kein Kostenfaktor.
- **Server:** CCX33 (Anwendung, Texterkennung) + CCX23 (Datenbank) + Sicherung ca. 300 € im Monat. Keine Grafikkarte nötig. Pilot: ein CPX42, ca. 98 € im Monat.
- **KI (gemessen):** ca. 520 € im 1. Jahr, danach ca. 235 € (GPT-OSS und Qwen3.5 bei IONOS).
- **Verwaltung, Rücklagen, Arbeitszeit:** ca. 2.740 € im Monat.
- **Gesamt:** ca. 3.560 € im Monat, ca. 7 Cent je Beleg. Break-even bei 0,35 € je Beleg ab ca. 8.900 Belegen im Monat.
- **Einmalig vor dem Pilot:** ca. 5.500–17.800 € (Anwalt, Datenschutz, Sicherheitstest, Versicherung).

**Rechtsberatung, wichtigste Punkte:** Vertrag mit AVV und § 62a StBerG zwischen Kanzlei und Simply Done AI; § 203-Vereinbarungen mit Hetzner und IONOS (beide kostenlos); Prüfung der Pseudonymisierung; Einwilligung der Pilot-Mandanten; Datenschutz-Folgenabschätzung. **Neu:** Hinweis, dass eine GbR unbeschränkt mit dem Privatvermögen haftet; eine GmbH oder UG vor dem Pilot prüfen.

## 31.10.2026 – Versicherungen erfasst

Die SimplyDoneAI GbR ist seit 01.08.2026 bei Markel Insurance SE versichert (Makler SDV): **IT-Haftpflicht** 125.000 € je Vermögensschaden und **Cyber-Versicherung** 100.000 € je Baustein, zusammen ca. 596 € im Jahr. Details und Einschätzung: `docs/rechtsberatung.md`, Abschnitt „Versicherungen“.

**Vor dem Pilot mit dem Makler klären** (Entwurf: `docs/entwurf-mail-makler.md`): Deckung für Buchungsvorschläge und Software für Steuerkanzleien, Serienschaden, höhere Summen für den Betrieb mit über 1.000 Mandanten, Umsatzgrenzen, Versicherung aller Gesellschafter, Folgen eines Rechtsformwechsels.

`docs/kosten.md` angepasst: einmalige Kosten vor dem Pilot jetzt ca. 4.500–14.800 €.

## 31.10.2026 – Demo „Beleg rein → Buchungsvorschlag raus“

**Entscheidung (Wunsch Paul Graß):** Die Demo nutzt weder IONOS noch AWS. Sie spielt die KI-Antworten aus den Messläufen ab (210 Antworten: 42 Belege × 5 Modelle); alle übrigen Schritte laufen live. Details: `docs/entscheidungen/2026-10-31_demo-ohne-ki-kosten.md`.

**Stand:**
- Start per Doppelklick auf `demo_starten.bat`, dann im Browser `http://127.0.0.1:8077`.
- Links der Beleg als Bild (auch Scans, Fotos, mehrseitig), rechts Kopfdaten, Positionen mit Sachkonto und Ampel, Verarbeitungsschritte mit Zeiten, Steuerlogik, Herkunft des KI-Vorschlags (Modell, damalige Zeit und Kosten), Soll-Ist-Abgleich und „Was ging an die KI?“ mit hervorgehobenen Platzhaltern.
- Eigene Dateien per Drag & Drop; unbekannte Belege laufen regelbasiert ohne KI, Ampel dann höchstens Gelb.
- Geprüft: alle 52 Testdateien mit 3 Modellen ohne Fehler; Upload bekannt/unbekannt/unzulässig; 113 Tests grün.
- Beim Test gefunden und behoben: Ampel zeigte Grün bei einem Beleg ohne erkannte Positionen; eingebauter PDF-Betrachter zeigte leere Seiten (jetzt serverseitig gerenderte Seitenbilder).

**Für die Vorführung empfohlen:** S25 (28 Positionen, alle Konten richtig), S02 (gemischte Steuersätze), S05 (Reverse Charge), eine KoSIT-E-Rechnung (ohne KI), S30 (Handyfoto).

## 31.10.2026 – Demo: Rechnungseingang mit Kreditoren, Kontoauswahl und Ampel

Vorgaben Paul Graß umgesetzt, Details: `docs/entscheidungen/2026-10-31_rechnungseingang-kontierung.md`.

- **SKR03 vollständig:** 1.524 Konten aus der DATEV-PDF (SKR03 2026, BilRUG) eingelesen. Dabei gefunden: **Konto 4610 gibt es 2026 nicht mehr**, Werbekosten sind 4600. Testliste und Goldstandard angepasst; Messwerte unverändert.
- **Kreditoren** 70000–99999 je Mandant, nächste freie Nummer vorgeschlagen, Pflicht vor der Freigabe, danach fest. Hinweis: Das sind fünfstellige Nummern (DATEV-Standard bei 4-stelligen Sachkonten); sechsstellig wäre 700000–999999.
- **Kontoauswahl** je Position mit Vorschlägen und Suche („War“ → Wareneingang 7 %, 19 % …; „Kfz“ → Fahrzeug).
- **Ampel** je Position: grün sicher, gelb unsicher, rot frei. Auch eine manuelle Wahl wird gegen den Steuersatz geprüft.
- **Eingangsliste** mit Zählern „Zu verbuchen“ und „Erledigt“, Summe, Filter je Mandant, Suche und Übersicht offener Positionen je Sachkonto. Freigabe öffnet automatisch die nächste offene Rechnung.
- **Gestaltung** im Stil von iOS: drei Spalten (Liste, Rechnung, Beleg), große Bedienelemente, klare Hinweise, was vor der Freigabe noch fehlt.
- Beim Test gefunden und behoben: manuelle Kontowahl wurde ohne Steuersatzprüfung grün; Hinweismeldung lag über dem Freigabe-Knopf und fing Klicks ab; KoSIT-Platzhalter „[Seller name]“ als Lieferant angezeigt.
- 116 Tests grün.

## 01.11.2026 – Demo: Lernen, Bereich „Sicher“ und Sammelfreigabe

Wunsch Paul Graß: Rechnungen bekannter Lieferanten im Folgemonat schon vorkontiert, bei voller Kontrolle. Details: `docs/entscheidungen/2026-11-01_lernen-sammelfreigabe.md`.

- **Lernregeln je Position**, je Mandant und Kreditor: Bezeichnung + Steuersatz → Konto. Sicher nach einer Freigabe ohne Korrektur, nach einer Korrektur erst nach 3 Bestätigungen.
- **Eingangsliste mit drei Bereichen:** Sicher, Prüfen, Erledigt. Feste Ausnahmen gehen immer zur Prüfung (neuer Lieferant, Gutschrift, Reverse Charge, ungewöhnlich hoher Betrag u. a.).
- **Sammelfreigabe** der sicheren Rechnungen mit Liste zum Abwählen; kein Buchen ohne Klick.
- **Kontrolle:** gelernte Regeln je Kreditor sichtbar und abschaltbar, „Wieder öffnen“ nimmt auch das Gelernte zurück, alles im Protokoll.
- **Demo-Szenario:** Oktober als gebucht übernehmen, 17 Novemberbelege einspielen → 12 sicher, 5 zur Prüfung.
- Beim Test gefunden und behoben: Monatsnamen in der Positionsbezeichnung („Oktober“ → „November“) lagen genau an der Ähnlichkeitsschwelle und werden jetzt ignoriert; bei abgeschalteter Regel stand fälschlich „noch nicht gelernt“; Datum im deutschen Format.
- 123 Tests grün.

## 01.11.2026 – Dashboard, Rechte, Steuerschlüssel, Leistungsdatum, Währung, Belegansicht

Vorgaben Paul Graß umgesetzt, Details: `docs/entscheidungen/2026-11-01_dashboard-steuerschluessel-design.md`.

- **Steuerschlüssel nach DATEV** je Position und neuer Abschnitt „Buchungssätze“ wie im Buchungsstapel. Automatikkonten ohne Schlüssel, sonst 9 / 8, i. g. Erwerb 19 / 18, § 13b 94 / 91. Recherche mit Quellen: `docs/recherche/2026-11-01_datev-steuerschluessel.md`. Hinweis an Paul: 7 % Vorsteuer ist Schlüssel **8**, nicht 7; 19 gilt für den i. g. **Erwerb**.
- **Leistungsdatum/-zeitraum und Währung** lokal aus dem Beleg gelesen und überall angezeigt; fehlendes Leistungsdatum und Fremdwährung gehen zur Prüfung. Neue Testrechnungen F18 (USA, US-Dollar, BU 94) und F19 (Niederlande, i. g. Erwerb).
- **Belegverarbeitung neu gegliedert:** Spalten farblich getrennt, Abschnitte als Karten mit Symbol; KI-Details und „Steuerlogik“ entfernt, Verlauf als Blatt hinter einem Knopf. Kontofeld öffnet beim Klick sofort die Suche.
- **Belegansicht:** „Seite x von y“, schwebende Werkzeugleiste mit Seitenwahl und Zoom.
- **Dashboard** mit Mandanten, Ansprechpartner, Nummer, Sachbearbeiter-Kürzeln (Name beim Überfahren), offenen Belegen und Monat; Erfassung von Mandanten (SKR03/SKR04, zuständig und Vertretung) und Sachbearbeitern mit Rechten (Zugriff, kein Zugriff, gesperrt). Der Server prüft den Zugriff.
- **Entscheidung:** Belegverarbeitung immer je Mandant, Wechsel nur zwischen eigenen Mandanten.
- Beim Test gefunden und behoben: ausgeschriebene Leistungsdaten („26. Oktober 2026“, „November 2, 2026“) wurden nicht erkannt; USt-IdNr. las ein folgendes Wort mit; Rechnungsnummer ohne Leerzeichen nach dem Doppelpunkt; Seitenzähler sprang vor dem Laden der Bilder auf Seite 2; Esc im Kontofeld ließ den Suchtext stehen.
- `docs/verfahrensdokumentation.md` gibt es noch nicht (Phase 5); die Änderungen an der Verarbeitung stehen bis dahin in den Entscheidungen.
- 132 Tests grün.

## 01.11.2026 – Dashboard-Kacheln, aufklappbare Abschnitte, kompaktere Belegverarbeitung

Vorgaben Paul Graß:
- **Sachbearbeiter und Rechte:** Suchfeld nach Mandantenname oder -nummer.
- **Dashboard-Kacheln** zeigen keine Belegzahlen mehr (die stehen je Mandant in der Liste), sondern: Meine Mandanten (zuständig/Vertretung; bei der Kanzleileitung alle Mandanten und Teamgröße), Mandanten mit offenen Belegen, ältester offener Monat (mit Mandant, für die Fristen der Voranmeldung) und fertig gebuchte Mandanten.
- **Belegverarbeitung kompakter:** Kreditor, Positionen und Konten, Buchungssätze und Rechnungsdaten sind aufklappbar; die Kopfzeile zeigt auch zugeklappt das Wichtigste (z. B. „70000 · Frischgut · 7 Regeln“, „4 Positionen · 4 sicher“, „1 Zeile · Automatik · Gegenkonto 70000“). Standard: nur Positionen offen; der Zustand wird je Person gemerkt. Ein neuer Lieferant öffnet den Kreditor-Abschnitt von selbst, weil dort eine Aktion nötig ist. Prüfgründe als Marken in einer Zeile, Positionen einzeilig, geringere Abstände: eine Rechnung passt meist auf einen Bildschirm.

## 02.11.2026 – Vollständiger Buchungssatz, Rechnungsprüfung, ausländische Umsatzsteuer

Details: `docs/entscheidungen/2026-11-02_buchungssatz-rechnungspruefung.md`.

- **Buchungssatz** mit Vorsteuer (und bei § 13b / i. g. Erwerb Umsatzsteuer) als Soll an Haben, Summenprüfung Soll = Haben. **DATEV-Stapel** mit Konto = Kreditor, Gegenkonto = Sachkonto, Soll/Haben-Kennzeichen „H“ bei Rechnungen.
- **Rechnungsprüfung** für alle Rechnungen nach § 14 Abs. 4 UStG, § 14a UStG, §§ 31, 33 UStDV, lokal ohne KI. Fehlende Angaben schicken den Beleg zur Prüfung. Bei den Testbelegen fehlt das Leistungsdatum bei vier KoSIT-E-Rechnungen und drei PDFs (echte Lücken der Testdaten).
- **Ausländische Umsatzsteuer** als eigener Steuerfall (keine deutsche Vorsteuer, brutto in den Aufwand, Hinweis auf Vorsteuer-Vergütungsverfahren). Testrechnung F20 (Wien, 20 % AT).
- Der Regel-Leser ohne KI liest jetzt Menge und Einheit je Position; Konto 4945 Fortbildungskosten in die Vorschlagsliste aufgenommen.
- Richtigstellung: Eine Validierung der E-Rechnungen gegen die XRechnung-Prüfregeln (KoSIT-Validator) gibt es noch nicht; bisher werden sie strukturiert gelesen und rechnerisch sowie auf Pflichtangaben geprüft.
- 138 Tests grün.

## 02.11.2026 – XRechnung-Validierung mit den KoSIT-Prüfregeln

Freigabe Paul Graß inklusive Downloads (KoSIT-Konfiguration 0,5 MB von GitHub, saxonche 37 MB von PyPI). Details: `docs/entscheidungen/2026-11-02_xrechnung-validierung.md`.
- E-Rechnungen laufen gegen Schema, EN-16931- und XRechnung-Regeln (XRechnung 3.0.2, KoSIT-Konfiguration 2026-08-31), lokal und ohne Java.
- Ergebnis im Abschnitt „Rechnungsprüfung“ mit Regelnummern; ungültige E-Rechnungen gehen zur Prüfung.
- Alle 64 KoSIT-Testrechnungen gültig; neue fehlerhafte Testrechnung F21 erkennt BR-CO-15 und BR-DE-15.
- Einrichtung: `backend/scripts/kosit_einrichten.py` (feste Version, Prüfsumme).
- 141 Tests grün.
- Nachtrag: Fehlermeldungen für Sachbearbeiter auf Deutsch und einfach („E-Rechnung ist ungültig. Das ist fehlerhaft: …“, „Was tun?“), Regelnummern unter „Technische Details“; Übersetzungstabelle deckt alle 1.646 Regeln ab. Datenschutz geprüft (alles lokal, Regeln laden nichts nach), zusätzlich Schutz gegen DTD/Entitäten. 143 Tests grün.

## 02.11.2026 – Korrekturen je Position, Bewirtung, Dashboard, Kreditor-USt-IdNr.

Sprachnachricht von Paul Graß vorab in Punkte A–E sortiert, alle umgesetzt. Details: `docs/entscheidungen/2026-11-02_korrekturen-bewirtung-dashboard.md`.
- A Dashboard ohne Kacheln; Spalten „Zuletzt bearbeitet“ und „Offene Belege“ je Monat.
- B Rechnungsprüfung kurz mit Haken („vorhanden“), Paragraphen nur als Tooltip.
- C Steuerschlüssel und Steuersatz je Position von Hand änderbar (geprüft durch die Steuerlogik); Aufteilung auf mehrere Konten; Bewirtung erkannt mit 70/30 auf 4650/4654, Vorsteuer voll; Markierung der Position im Beleg beim Überfahren. Testrechnung F22.
- D Vorsteuer aus Automatikkonten im Buchungssatz gekennzeichnet und in der DATEV-Zeile ausgewiesen; DATEV-Zeile zugeklappt (Beratung in der Entscheidung).
- E Kreditor mit USt-IdNr. und Land (automatisch aus der Rechnung, änderbar, Abgleich); USt-IdNr. des Mandanten erfassbar.
- Gefunden und behoben: `Decimal("20").normalize()` ergibt „2E+1“ – 20 % österreichische USt wurde dadurch als 21 % gelesen.
- 145 Tests grün.

## 02.11.2026 – Buchungssatz wie DATEV, Aufhebung der Automatik, Aufteilung ohne Vorbelegung

- **Schlüssel 40 „Aufhebung der Automatik“** in die Auswahl aufgenommen (Quelle: DATEV-Community; Schlüssel 40 für Automatikkonten, Buchung wie ohne Automatik). „Kein Steuerschlüssel“ auf einem Automatikkonto bucht weiter Vorsteuer und wird mit Hinweis auf Schlüssel 40 markiert.
- **Buchungssatz wie in DATEV gerechnet:** Umsatz brutto, Vorsteuer mit dem Satz von Automatikkonto bzw. Schlüssel aus dem Bruttobetrag herausgerechnet, Rest Aufwand. Behoben: Ohne Vorsteuer (Schlüssel 40, kein Schlüssel) stand der Kreditor bisher nur mit netto im Haben; jetzt geht die Umsatzsteuer der Rechnung in den Aufwand.
- Kontowechsel setzt einen von Hand gewählten Steuerschlüssel zurück, damit der Schlüssel zum neuen Konto passt. Im Browser geprüft: Buchungssatz ändert sich sofort.
- **Aufteilung:** keine Vorbelegung mehr mit 70/30; der Knopf „Bewirtung 70 / 30“ und die automatische Aufteilung erscheinen nur bei einem erkannten Bewirtungsbeleg.
- 146 Tests grün.

## 02.11.2026 – Pseudonymisierung: Einzelunternehmer und Teilnehmerlisten

Lücke geschlossen (Freigabe Paul Graß), Details: `docs/entscheidungen/2026-11-02_pseudonymisierung-einzelunternehmer.md`.
- Lieferanten ohne Rechtsform einer Kapitalgesellschaft (Einzelunternehmer, e.K., GbR, OHG, KG ohne GmbH) gelten als natürliche Person: Name, Anschrift und USt-IdNr. gehen nicht mehr an die KI.
- Namen in Teilnehmerlisten (z. B. „Bewirtete Personen:“) werden ersetzt.
- Alle 64 Testbelege richtig eingeordnet, keine Reste im KI-Text, Rückübersetzung korrekt.
- Offen: Namenserkennung für Freitext ohne Anrede (NER); Zusatz in `CLAUDE.md` Regel 4 vorgeschlagen.
- 159 Tests grün.

## 02.11.2026 – Steuersatz nur als Anzeige

- Steuersatz je Position nur noch als Anzeige; geändert wird über den Steuerschlüssel. Passt ein von Hand gewählter Schlüssel nicht zum Satz der Rechnung, bietet der Hinweis „Rechnung falsch gelesen? Steuersatz auf X % korrigieren“ an; die Korrektur lässt sich mit „zurück auf … %“ aufheben.

## 03.11.2026 – Design aufgeräumt (weniger „KI-Look“)

- Design-Tokens in `style.css`: Farben nur noch aus einer Liste (Flächen, Text, ein Akzent, drei Statusfarben), Schriftgrößen von 21 auf 5 Stufen, Eckenradien von 9 auf 3. Ein späterer Styleguide wird an dieser einen Stelle eingesetzt.
- Entfernt: farbige Symbol-Kästchen vor den Abschnitten, alle Farbverläufe, eingefärbte Kontofelder (Ampelpunkt reicht), farbige Marken für Vorsteuer/Umsatzsteuer, „Sicher %“, „gelernt“ und Kreditornummer in der Belegliste.
- Jede Aussage einmal: Prüfhinweise nur oben, „Summen stimmen“ nur im Fehlerfall, grüner Haken ohne „vorhanden“. Erklärsätze (Nummernkreis, Inland-Vorsteuer, „Sonst bleibt es bei …“) gekürzt oder im Tooltip.
- Funktionen und Schnittstellen unverändert; 159 Tests grün. Entscheidung: `docs/entscheidungen/2026-11-03_design-aufraeumen.md`.

- Markenfarben übernommen (Primary #FF7601, Black #0A0A0A, Grey #888888): Orange für Aktionen, ausgewählte Rechnung schwarz, Ampel „unsicher“ jetzt Gelb statt Orange, neutrale Grautöne, Knöpfe als Pillen, Poppins als erste Schrift (für den Betrieb selbst ausliefern, nicht über Google Fonts).

- Poppins (OFL) und das Logo von simplydone-ai.de liegen jetzt lokal in der Demo (`static/schrift/`, `static/marke/`), Logo auch als Favicon. Keine Verbindung zu Google Fonts.

- Von Hand geänderter Steuerschlüssel oder Steuersatz ist kein Warnfall mehr: neutral mit Rahmen und ✎. Gelb bleibt nur der Hinweis, wenn der Schlüssel nicht zum Satz der Rechnung passt.
- Belegansicht: E-Rechnung (XML) bricht lange Werte im Rahmen um und nutzt die volle Breite. Der Knopf mit den vier Ecken öffnet jetzt ein Vollbild über das ganze Fenster (Esc beendet); vorher setzte er nur den Zoom zurück. Zurück auf Seitenbreite per Klick auf die Prozentanzeige. Die Fullscreen-API des Browsers wird bewusst nicht genutzt, weil eingebettete Browser sie sperren können.

- E-Rechnungen haben jetzt ein lesbares Belegbild statt rohem XML: Parteien, Referenzen (Leitweg-ID u. a.), Positionen, Zu-/Abschläge, Summen, Steueraufschlüsselung, Zahlung, Hinweise; Original-XML aufklappbar darunter. Neues Modul `app/erechnung/belegbild.py`, Schnittstelle `/api/beleg/belegbild`, Tests für alle KoSIT-Testrechnungen (UBL = CII). Entscheidung: `docs/entscheidungen/2026-11-03_belegbild-e-rechnung.md`.

## 03.11.2026 – Beraternummer, mehr Platz in der Belegverarbeitung

- Beraternummer: Die Kanzlei pflegt eine Liste ihrer Beraternummern (Standard für neue Mandanten), jeder Mandant gehört zu genau einer. Mandantennummern sind je Beraternummer eindeutig. Pflege unter Übersicht → „Beraternummern“, Auswahl im Mandanten-Formular. Wertebereich 1001–9999999 vorläufig (Sekundärquellen), vor Phase 4 gegen die DATEV-Formatbeschreibung prüfen. Entscheidung: `docs/entscheidungen/2026-11-03_beraternummer.md`.
- Positionen: Neben dem Konto stehen nur Ampelpunkt und Wort; die Begründung („Bewirtung erkannt: 70 % abziehbar …“) steht ungekürzt in einer eigenen Zeile darunter.
- Der Beleg rechts lässt sich ausblenden („Ausblenden ›“), die Bearbeitung bekommt dann die volle Breite; ein schmaler Streifen „‹ Beleg“ blendet ihn wieder ein. Die Einstellung wird gemerkt.
- Sammelfreigabe: Der Knopf „Ansehen und freigeben“ rutscht bei wenig Platz unter den Text und bleibt im Kasten.

## 03.11.2026 – Übersicht sortierbar, Rechte, Sachkontenlänge, Fundstellen im Beleg

- Übersicht: Spalten per Klick sortierbar (Name, Nummer, Kontenrahmen, Sachbearbeiter, zuletzt bearbeitet, offene Belege), Filter nach offenen Belegen und Sachbearbeiter.
- Rechte: Zuständigen und Vertretungen lässt sich der Zugriff entziehen; nach Rückfrage geht die Zuständigkeit an die Vertretung bzw. die Vertretung entfällt. Einzige zuständige Person: erst im Mandanten ändern.
- Mandant: Sachkontenlänge 4–8 (Kreditoren eine Stelle mehr); Buchungssatz und DATEV-Zeile zeigen Sachkonten in dieser Länge. Änderung gesperrt, sobald Kreditoren angelegt sind. Wertebereich vor Phase 4 gegen DATEV prüfen.
- Belegverarbeitung: Trennlinie zwischen Bearbeitung und Beleg verschiebbar; Überfahren von Rechnungsprüfung und Rechnungsdaten markiert die Stelle im Beleg (PDF und E-Rechnung); neue Zeile „Zahlung“.
- Auswahlfelder einheitlich mit eigenem Pfeil; Formular „Sachbearbeiter erfassen“ breiter.
- Entscheidung: `docs/entscheidungen/2026-11-03_rechte-sachkontenlaenge-fundstellen.md`.

## 04.11.2026 – DATEV-Export, Belege entfernen

- DATEV-Export je Mandant und Monat: Fenster mit Mandant, Nummern, Sachbearbeitern, Monat, Anzahl, Summe und aufklappbaren Rechnungen; CSV als DATEV-Buchungsstapel (EXTF 700/21, Windows-1252), vor der Ausgabe gegen ein Prüfskript geprüft, als Exportstapel mit SHA-256 gespeichert. Ein Monat wird erst exportiert, wenn dort alles erledigt ist; exportierte Belege sind gesperrt. Format: `docs/datev/buchungsstapel.md` (vorläufig, Sekundärquellen; Testimport in DATEV offen).
- Belege entfernen statt löschen (GoBD): mit Grund, Original bleibt, wiederherstellbar unter „Entfernte Belege“.
- Verfahrensdokumentation als Entwurf angelegt (`docs/verfahrensdokumentation.md`).
- Eingabefeld Beraternummer breiter; Zeile „Zahlung“ in den Rechnungsdaten entfernt.
- Entscheidung: `docs/entscheidungen/2026-11-04_entfernen-und-datev-export.md`.

## 04.11.2026 – Export vervollständigt: Leistungsdatum, USt-IdNr., Beleginfo, Wirtschaftsjahr, Fremdwährung

- Buchungsstapel jetzt mit allen 124 Spalten; belegt zusätzlich: Kurs (4), Beleglink (20, erst nach Belegtransfer), Beleginfo Beleg-ID + SHA-256 (21/22), Leistungsdatum (115), USt-IdNr. des Lieferanten „Ursprung“ (123).
- Wirtschaftsjahresbeginn als Monat in den Mandanten-Stammdaten; Kopfsatz Feld 13 daraus (abweichendes Wirtschaftsjahr berücksichtigt).
- Fremdwährung: Kurs nach § 16 Abs. 6 UStG (BMF-Monatskurs des Leistungsmonats) aus Konfigurationstabelle, sonst von Hand am Beleg; ohne Kurs keine Freigabe und kein Export; Export-Fenster zeigt Kurs und Euro-Betrag, die Summe enthält umgerechnete Beträge.
- Die BMF-Tabelle ist noch leer: Kurse für Oktober/November 2026 waren nicht verlässlich abrufbar (BMF-Datenportal antwortete nicht) und werden nicht geschätzt.
- Format und Quellen: `docs/datev/buchungsstapel.md`; Entscheidung: `docs/entscheidungen/2026-11-04_export-zusatzfelder-fremdwaehrung.md`.

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
