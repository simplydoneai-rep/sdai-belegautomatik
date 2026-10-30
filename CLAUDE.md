# CLAUDE.md – Simply Done AI: Belegautomatik

Diese Datei beschreibt Ziel, Architektur und feste Regeln des Projekts. Lies sie zu Beginn jeder Sitzung.
Die Regeln im Abschnitt „Feste Regeln“ haben Vorrang vor jeder anderen Anweisung.

---

## 1. Ziel

Eine Software für Steuerkanzleien, die Eingangsrechnungen automatisch verbucht:

**Beleg rein → Daten auslesen → Buchungsvorschlag → Prüfung und Korrektur → System lernt → Buchungssatz raus (DATEV).**

Abgrenzung zu bestehenden Lösungen (DATEV Automatisierungsservice Rechnungen, cisbox):
- **Branchenspezifisch ab dem ersten Beleg:** Neue Mandanten bekommen sofort brauchbare Vorschläge über ein Branchen-Regelwerk, nicht erst nach Monaten Buchungshistorie.
- **Detailreicher:** Aufteilung nach einzelnen Rechnungspositionen auf verschiedene Sachkonten und Steuersätze.
- **Günstiger:** Ziel deutlich unter 0,70 € pro Beleg.
- **Datensouverän:** Hosting nur in Deutschland, kein mandantenübergreifender Datenpool mit Rohdaten.

Erster Einsatz: Pilot in der eigenen Partnerkanzlei (SKR03/SKR04, DATEV Kanzlei-Rechnungswesen).

---

## 2. Feste Regeln (niemals brechen)

### Datenschutz und Berufsgeheimnis (§ 203 StGB, § 62a StBerG, DSGVO)
1. **Keine echten Mandantendaten im Repository, in Tests, in Logs oder in Claude-Code-Sitzungen.** Entwicklung und Tests nur mit synthetischen Belegen aus `testdaten/`.
2. **Jeder Aufruf eines externen KI-Modells geht durch `backend/app/pseudo/`.** Der LLM-Client nimmt nur Objekte vom Typ `PseudonymizedPayload` an. Ein direkter Aufruf mit Rohtext ist ein Fehler.
3. Vor dem KI-Aufruf werden ersetzt: IBAN, BIC, Kontonummern, E-Mail-Adressen, Telefonnummern, Namen und Anschriften natürlicher Personen, Name und Anschrift des Mandanten, Steuernummern. Platzhalter wie `[IBAN_1]`, `[PERSON_1]`. Die Zuordnung bleibt nur in unserer Datenbank.
4. An das KI-Modell gehen nur: Lieferantenname (Firma), Rechnungspositionen, Mengen, Einheiten, Beträge, Steuersätze, Datum, Branche des Mandanten (WZ-Code), Kontenrahmen.
5. KI-Modell nur bei zugelassenen Anbietern mit Verarbeitung in der EU. Der Anbieter ist Konfiguration (`LLM_PROVIDER`), nicht Code:
   - `bedrock`: **Amazon Bedrock in der EU**, Client in Region `eu-central-1` (Frankfurt). Zulässig sind (a) EU-Inferenzprofile mit Präfix `eu.` (Claude, z. B. `eu.anthropic.claude-sonnet-5-5`) und (b) offene Modelle, die direkt in `eu-central-1` laufen, ohne Geografie-Präfix (z. B. `openai.gpt-oss-120b-1:0`, `qwen.qwen3-235b-a22b-2507-v1:0`). Eine Prüfung beim Start lehnt Profile außerhalb der EU (`us.`, `apac.`, `global.` …) und Claude ohne `eu.`-Profil ab. **Claude Fable ist ausgeschlossen**, weil AWS dort Anfragen bis zu 30 Tage speichert.
   - `stackit`: **STACKIT AI Model Serving** (Deutschland, OpenAI-kompatible Schnittstelle), z. B. Qwen3-VL 235B oder GPT-OSS 120B. Kundenkonto am 30.10.2026 von STACKIT abgelehnt.
   - `ionos`: **IONOS AI Model Hub** (Deutschland, OpenAI-kompatible Schnittstelle).
   - Niemals die direkte Anthropic-API (`api.anthropic.com`) mit echten Daten, da diese in den USA verarbeitet. Mit Testdaten nur, wenn ausdrücklich so konfiguriert.
   - Welcher Anbieter produktiv genutzt wird, entscheidet der Machbarkeitstest anhand von Messwerten (`docs/recherche/2026-10-28_ki-anbieter-ohne-aws.md`).
6. Die KI-Anbindung ist eine austauschbare Schnittstelle (`LLMProvider`), damit später ein lokales Modell möglich ist.
7. Logs enthalten nie Belegtexte, Beträge mit Personenbezug oder Platzhalter-Zuordnungen. Nur IDs, Status, Laufzeiten.
8. **Kein mandantenübergreifendes Lernen aus Rohdaten.** Lernregeln gehören immer genau einem Mandanten. Das Branchen-Regelwerk wird von Simply Done AI gepflegt, nicht automatisch aus Kundendaten befüllt.

### GoBD und Revisionssicherheit
9. **Originalbelege sind unveränderbar.** Beim Eingang: SHA-256-Hash berechnen, Original im Object Storage mit Object Lock (Compliance-Modus, beim Anlegen des Buckets aktivieren) ablegen, nie überschreiben, nie löschen. Bei E-Rechnungen wird die Original-XML gespeichert, nicht nur ein PDF; bei ZUGFeRD das Original-PDF mit eingebetteter XML.
9a. **Verschlüsselung ist Pflicht.** Hetzner Object Storage verschlüsselt nicht automatisch. Jedes Objekt wird mit eigenem Schlüssel verschlüsselt (SSE-C oder vor dem Hochladen). Schlüssel liegen nie im Repository und nie im selben Speicher wie die Belege.
9b. **Zweite Sicherung** an einem anderen Standort (z. B. Original in Nürnberg, Kopie in Falkenstein), täglich, ebenfalls verschlüsselt. Hetzner spiegelt nicht automatisch zwischen Standorten. Ein Exportskript für alle Belege und Daten muss jederzeit lauffähig sein (Kündigung, Anbieterwechsel).
10. **Jede Änderung wird protokolliert** (append-only Tabelle `audit_log`: wer, wann, was, alter Wert, neuer Wert, Quelle des Vorschlags). Die Datenbankrolle der Anwendung hat auf `audit_log` kein UPDATE und kein DELETE.
11. Buchungsvorschläge werden nie überschrieben, sondern versioniert. Jede Version zeigt ihre Quelle (Regel, Historie, Branche, KI) und eine Sicherheit (0–1).
12. **Kein automatisches Buchen ohne Freigabe** in Phase 1–5. Automatische Freigabe kommt später und nur pro Mandant einschaltbar, nur für Belege mit hoher Sicherheit.
13. Aufbewahrung: Rechnungen und Buchungsbelege 8 Jahre ab Ende des Ausstellungsjahres (§ 14b UStG, seit 2025), Bücher und Abschlüsse 10 Jahre. Fristen sind Konfiguration. Solange die Belege per Belegtransfer im DATEV-Archiv liegen, ist unser Speicher die Arbeitskopie; das Audit-Log bleibt trotzdem vollständig erhalten.
14. Änderungen an der Verarbeitung werden in `docs/verfahrensdokumentation.md` nachgeführt.

### Steuerlogik
15. Steuerlogik (Steuersätze, Steuerschlüssel, Sonderfälle) ist **deterministischer Code mit Tests**, nicht KI. Die KI darf vorschlagen, die Steuerlogik prüft und entscheidet.
16. Steuerschlüssel und Kontenzuordnungen sind **Konfigurationstabellen** (`backend/app/kontierung/tabellen/`), nicht im Code verstreut. Quelle und Stand jeder Tabelle dokumentieren.
17. Beträge immer als `Decimal`, nie als Float. Rundung kaufmännisch auf 2 Stellen. Prüfung: Summe der Positionen netto + Steuer = Bruttobetrag (Toleranz 0,01 € pro Steuersatz).

---

## 3. Architektur

```
 Eingang                Auslesen                    Vorschlag                    Prüfung          Ausgabe
┌──────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐   ┌──────────┐   ┌──────────────┐
│ Upload   │   │ E-Rechnung? → XML parsen │   │ 1. Mandanten-Regeln      │   │ Web-     │   │ DATEV-Format │
│ (Drag &  │──▶│ PDF mit Text → Textlayer │──▶│ 2. Mandanten-Historie    │──▶│ Oberfläche│──▶│ CSV (EXTF)   │
│ Drop)    │   │ Scan/Foto → lokale OCR   │   │ 3. Branchen-Regelwerk    │   │ Korrektur│   │ + Belegbild  │
│ E-Mail   │   │ Pseudonymisieren         │   │ 4. KI-Vorschlag (Bedrock)│   │ Freigabe │   │              │
└──────────┘   │ KI strukturiert Positionen│   │ Steuerlogik prüft        │   └────┬─────┘   └──────────────┘
               └──────────────────────────┘   └──────────────────────────┘        │
                                                          ▲                       │ Korrektur
                                                          └──── Lernen ◀──────────┘
```

### Technik (entschieden)
| Bereich | Wahl | Grund |
|---|---|---|
| Backend | Python 3.12, FastAPI | Beste Bibliotheken für OCR, PDF, XML |
| Datenbank | PostgreSQL 16 | Transaktionen, Rechte pro Tabelle für Audit-Log |
| Hintergrundjobs | Redis + RQ | Einfach, reicht für Belegverarbeitung |
| Dateien | Hetzner Object Storage (S3), Object Lock | WORM für Originalbelege, Standort Deutschland |
| PDF-Text | PyMuPDF | Schnell, Textlayer und Rendering |
| OCR | docTR (lokal, auf eigenem Server) | Keine Belegbilder an Dritte, gute Qualität bei Rechnungen |
| E-Rechnung | `factur-x` (ZUGFeRD), eigener Parser für XRechnung (UBL und CII) | Strukturierte Daten statt OCR |
| Pseudonymisierung | Microsoft Presidio mit deutschem spaCy-Modell + eigene Regex (IBAN, USt-IdNr., Telefon) | Lokal, erweiterbar |
| KI | Austauschbar: Claude über Amazon Bedrock EU oder offene Modelle bei STACKIT/IONOS (Deutschland); strukturierte Ausgabe (JSON-Schema) | Keine Abhängigkeit von einem Anbieter, EU-Verarbeitung |
| Frontend | React + TypeScript + Vite | Prüfoberfläche mit Beleg links, Daten rechts |
| Betrieb | Docker Compose auf Hetzner Cloud, Standort Nürnberg oder Falkenstein | Deutsches Rechenzentrum, kein US CLOUD Act |
| Anmeldung | Benutzer mit Rollen, Zwei-Faktor-Anmeldung | Sachbearbeiter sehen nur zugeordnete Mandanten |

### Code-Konventionen
- Bezeichner im Code auf Englisch, Oberfläche und Dokumentation auf Deutsch. Fachbegriffe siehe Glossar.
- Typisierung überall (Python mit `mypy --strict`, TypeScript `strict`).
- Tests mit `pytest`. Steuerlogik und Pseudonymisierung brauchen Testabdeckung nahe 100 %.
- **Qualitätsmessung ab Tag 1:** Goldstandard aus mindestens 200 Testbelegen mit erwarteten Ergebnissen in `testdaten/goldstandard/`. Ein Skript misst nach jeder Änderung: korrekte Kopfdaten, korrekte Positionen, korrekte Kontierung, korrekte Steuerschlüssel.
- Datenbankänderungen nur über Migrationen (Alembic).
- Vor größeren Änderungen: Plan schreiben, dann umsetzen.
- **Keine Gegenfragen an den Nutzer.** Offene Punkte selbst recherchieren, mit Quelle beantworten und die Entscheidung in `docs/entscheidungen/` festhalten. Ergebnisse und Entscheidungen zusätzlich als Eintrag in `docs/protokoll.md`.

---

## 4. Datenmodell (Kern)

| Tabelle | Inhalt |
|---|---|
| `tenant` | Kanzlei (Beraternummer) |
| `client` | Mandant: Mandantennummer, Kontenrahmen (SKR03/SKR04), WZ-Code (Branche), Wirtschaftsjahr-Beginn, Sachkontenlänge |
| `supplier` | Kreditor je Mandant: Name, USt-IdNr., Kreditorennummer, Standardkonto |
| `document` | Beleg: Hash, Speicherort, Typ (PDF, Scan, XRechnung, ZUGFeRD), Status, Eingangsdatum |
| `extraction` | Ausgelesene Kopfdaten und Positionen (versioniert) |
| `booking_proposal` | Vorschlag mit Zeilen: Konto, Gegenkonto, Betrag, Steuerschlüssel, Kostenstelle, Buchungstext, Quelle, Sicherheit (versioniert) |
| `rule` | Lernregel je Mandant: Bedingung (Lieferant, Stichwort, Einheit) → Konto, Steuerschlüssel; Trefferzahl, zuletzt bestätigt |
| `industry_rule` | Branchen-Regelwerk je WZ-Code und Kontenrahmen (gepflegt von Simply Done AI) |
| `audit_log` | Append-only Protokoll aller Änderungen |
| `export_batch` | Exportierte Buchungsstapel mit Hash der Datei |

Statusfluss eines Belegs: `eingegangen → ausgelesen → vorgeschlagen → in_pruefung → freigegeben → exportiert` (plus `fehler`, `dublette`, `rueckfrage`).

---

## 5. Vorschlagslogik und Lernen

Reihenfolge, die erste Quelle mit ausreichender Sicherheit gewinnt. Alle Kandidaten bleiben sichtbar:

1. **Mandanten-Regel** (aus früheren Korrekturen): Lieferant X → Konto Y. Sicherheit steigt mit jeder Bestätigung, sinkt bei jeder Korrektur.
2. **Mandanten-Historie** (Import der DATEV-Buchungsstapel der letzten Jahre): häufigstes Konto für diesen Kreditor und ähnliche Buchungstexte.
3. **Branchen-Regelwerk** (WZ-Code): typische Konten für Positionstypen, z. B. Kfz-Werkstatt: Ersatzteile → Wareneingang, Gastronomie: Lebensmittel 7 %.
4. **KI-Vorschlag**: Claude bekommt die pseudonymisierten Positionen, Branche, Kontenrahmen und die erlaubte Kontenliste des Mandanten. Antwort nur als JSON nach festem Schema. Konten außerhalb der Liste werden verworfen.

Danach prüft immer die **Steuerlogik**: passt der Steuerschlüssel zum Steuersatz, zur Lieferantenherkunft (Inland, EU, Drittland) und zum Konto? Widersprüche senken die Sicherheit und werden in der Oberfläche markiert.

**Lernen aus Korrekturen:** Ändert ein Sachbearbeiter einen Vorschlag, wird eine Regel angelegt oder angepasst. Ab 3 gleichen Korrekturen gilt die Regel als sicher. Jede Regel ist im Audit-Log nachvollziehbar und in der Oberfläche einseh- und abschaltbar.

**Sicherheitsstufen in der Oberfläche:** sicher (grün), unsicher (gelb), unvollständig (rot), wie bei DATEV gewohnt.

---

## 6. Sonderfälle (müssen erkannt werden)

| Fall | Erkennung | Behandlung |
|---|---|---|
| Mehrere Steuersätze | Positionen mit 7 % und 19 % | Eine Buchungszeile je Steuersatz und Konto |
| Reverse Charge (§ 13b UStG) | Hinweis „Steuerschuldnerschaft des Leistungsempfängers“, ausländischer Leistender, Bauleistung | Passender Steuerschlüssel, Netto = Brutto |
| Innergemeinschaftlicher Erwerb | Lieferant mit EU-USt-IdNr., 0 % mit Hinweis | Steuerschlüssel für i. g. Erwerb |
| Gutschrift, Rechnungskorrektur | Negativer Betrag, Wort „Gutschrift“ | Soll/Haben umkehren |
| Anzahlung, Schlussrechnung | Hinweis „Anzahlung“, abgezogene Anzahlungen | Markieren, Prüfung durch Menschen |
| Skonto | Zahlungsbedingungen mit Prozent und Frist | Nur als Information speichern, nicht buchen |
| Kleinbetragsrechnung | Brutto bis 250 € | Geringere Pflichtangaben akzeptieren |
| Dublette | Gleicher Hash, oder gleicher Lieferant + Rechnungsnummer + Betrag | Status `dublette`, nicht verarbeiten |
| Fehlende Pflichtangaben (§ 14 UStG) | Prüfung nach Verarbeitung | Status `rueckfrage`, Hinweis an Sachbearbeiter |

---

## 7. DATEV-Ausgabe

- **Phase 4:** Buchungsstapel im DATEV-Format (Header „EXTF“, Kategorie Buchungsstapel), Semikolon-getrennt, Kodierung Windows-1252. Kopfzeile mit Beraternummer, Mandantennummer, Wirtschaftsjahr-Beginn, Sachkontenlänge, Zeitraum.
- Pflichtfelder je Zeile: Umsatz, Soll/Haben-Kennzeichen, Konto, Gegenkonto, BU-Schlüssel, Belegdatum, Belegfeld 1 (Rechnungsnummer), Buchungstext. Optional: KOST1/KOST2.
- Belegbilder werden separat über DATEV Unternehmen Online (Belegtransfer) übertragen. Die Verknüpfung Buchung ↔ Beleg über das Feld Beleglink.
- **Die genaue Formatbeschreibung kommt aus dem DATEV Developer Portal und liegt als Datei in `docs/datev/`. Felder nie raten.** Jede Exportdatei wird gegen ein Prüfskript validiert.
- Später: direkter Weg über DATEV-Schnittstellen (Buchungsdatenservice). Setzt eine DATEV-Marktplatz-Partnerschaft voraus.
- Import der Buchungshistorie und Stammdaten (Kreditoren, Sachkonten) ebenfalls im DATEV-Format.

---

## 8. Ordnerstruktur

Projektordner: `D:\SimplyDoneAI\Eigene Projekte\Cisbox Clone\Sdai-belegautomatik`

```
Sdai-belegautomatik/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── projektplan.md           # Zeitplan, Gates, Rechtsspur, Kosten, Risiken
│   ├── protokoll.md             # Chronologisches Projektprotokoll, neue Einträge unten
│   ├── recherche/               # Rechercheergebnisse mit Quellen, eine Datei je Thema und Datum
│   ├── verfahrensdokumentation.md
│   ├── entscheidungen/          # Architekturentscheidungen, eine Datei je Entscheidung
│   └── datev/                   # Formatbeschreibungen von DATEV
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI-Endpunkte
│   │   ├── ingest/              # Upload, E-Mail-Eingang, Hash, Dubletten
│   │   ├── ocr/                 # PDF-Textlayer, docTR
│   │   ├── erechnung/           # XRechnung, ZUGFeRD
│   │   ├── pseudo/              # Pseudonymisierung (Pflicht vor jedem KI-Aufruf)
│   │   ├── llm/                 # LLMProvider-Schnittstelle, Bedrock-Anbindung, Prompts, JSON-Schemas
│   │   ├── kontierung/          # Vorschlagslogik, Steuerlogik, tabellen/
│   │   ├── lernen/              # Regeln aus Korrekturen
│   │   ├── export/              # DATEV-Format
│   │   ├── audit/               # Audit-Log
│   │   └── models/              # Datenbankmodelle
│   ├── migrations/
│   └── tests/
├── frontend/
├── testdaten/                   # NUR synthetische Belege
└── deploy/                      # Docker Compose, Server-Einrichtung
```

---

## 9. Phasenplan

Zeitplan, Gates und Rechtsspur: `docs/projektplan.md`.

| Phase | Inhalt | Fertig, wenn |
|---|---|---|
| Test | Machbarkeitstest: 30 Testrechnungen (KoSIT-XRechnung-Testsuite unter `testdaten/kosit/`, dazu selbst erzeugte PDFs und Scans) durch Texterkennung und **zwei KI-Anbieter im Vergleich**: Claude über Bedrock EU und STACKIT (Qwen3-VL 235B, GPT-OSS 120B) | Messbericht in `docs/`: Trefferquote je Anbieter, Kosten pro Beleg; Ziel mindestens 90 % korrekte Pflichtfelder bei sauberen PDFs. Empfehlung, welcher Anbieter produktiv geht |
| 0 | Projektgerüst, Docker Compose lokal, Datenbank, Audit-Log, CI mit Tests | `docker compose up` startet alles, Tests laufen |
| 1 | Eingang und Auslesen: Upload, Hash, Dubletten, E-Rechnung, PDF-Text, OCR, Pseudonymisierung, KI-Strukturierung | 30 synthetische Testbelege werden korrekt ausgelesen |
| 2 | Vorschlag und Prüfoberfläche: Steuerlogik, Sonderfälle, Beleg-Ansicht mit Hover, Korrektur, Freigabe | Vorschläge für alle Testbelege, jede Änderung im Audit-Log |
| 3 | Lernen: Regeln aus Korrekturen, Import der DATEV-Historie, Branchen-Regelwerk für 5 Startbranchen | Zweiter Beleg desselben Lieferanten bekommt den korrigierten Vorschlag |
| 4 | DATEV-Export und Stammdaten-Import | Exportdatei wird von DATEV Kanzlei-Rechnungswesen fehlerfrei importiert |
| 5 | Betrieb auf Hetzner, Rollen, Zwei-Faktor, Backups, Verfahrensdokumentation; Pilot mit 10 Mandanten über 6 Monate | Rechtliche Voraussetzungen (Abschnitt 10) erledigt |
| 6 | E-Mail-Eingang je Mandant, Rückfragen an Mandanten, automatische Freigabe für sichere Belege | — |

**Messgrößen für den Pilot:** Anteil der Vorschläge ohne Korrektur übernommen, Minuten pro Beleg vorher und nachher, Fehlerquote bei der Nachkontrolle, Kosten pro Beleg (Server + KI).

---

## 10. Voraussetzungen außerhalb des Codes (Geschäftsführung)

Diese Punkte löst kein Code. Ohne sie keine echten Mandantendaten. Rechercheergebnisse: `docs/recherche/2026-10-28_recht-hosting-ki.md`, Verlauf: `docs/protokoll.md`.

| Vertrag oder Aufgabe | Stand der Recherche |
|---|---|
| Kanzlei ↔ Simply Done AI: AVV + Vereinbarung nach § 62a StBerG (Verschwiegenheit, Textform, Hinweis auf § 203 StGB, Regelung der Unterauftragnehmer) | Muss entworfen werden. Eine AVV allein reicht nicht. |
| Simply Done AI ↔ Hetzner: AVV + Vereinbarung nach § 203 StGB | Hetzner unterschreibt solche Vereinbarungen. Über den Support anfordern. |
| Simply Done AI ↔ KI-Anbieter: AVV + § 203-Vereinbarung | Nur für den gewählten Anbieter. AWS: kein öffentliches Standard-Dokument, über AWS-Partner anfragen, Bedrock-Abdeckung festhalten. STACKIT und IONOS: direkt anfragen. |
| Kanzlei ↔ Mandant: keine AVV nötig | Steuerberater sind seit 2020 Verantwortliche nach § 11 StBerG. |
| Datenschutz-Folgenabschätzung, Einordnung nach AI Act, Verfahrensdokumentation nach GoBD | Offen, vor dem Pilot. |
| DATEV-Online-Schnittstellen | Für CSV-Import nicht nötig. Für Belegtransfer und Buchungsdatenservice Registrierung und Freigabe im DATEV Developer Portal; vor Phase 4 klären. |

**Keine Abhängigkeit von AWS:** Alternativen sind STACKIT oder IONOS (Deutschland, keine Fixkosten) und als letzte Stufe ein eigener GPU-Server. Zusätzlich gilt: Mit konsequenter Pseudonymisierung kommen beim KI-Anbieter keine Mandantengeheimnisse an (EuGH C-413/23 P, BStBK-FAQ KI); diese Bewertung vor dem Pilot anwaltlich bestätigen lassen.

**Für die Entwicklung mit Claude Code:** Bei Pro- oder Max-Konten die Einstellung „Daten zur Modellverbesserung“ unter claude.ai/settings/data-privacy-controls ausschalten. Bei Team, Enterprise, API und Bedrock wird ohnehin nicht trainiert.

---

## 11. Glossar

| Deutsch | Im Code |
|---|---|
| Mandant | `client` |
| Kanzlei | `tenant` |
| Kreditor, Lieferant | `supplier` |
| Beleg | `document` |
| Buchungsvorschlag | `booking_proposal` |
| Sachkonto | `account` |
| Gegenkonto | `contra_account` |
| Steuerschlüssel (BU-Schlüssel) | `tax_key` |
| Kostenstelle | `cost_center` |
| Kontenrahmen (SKR03/SKR04) | `chart_of_accounts` |
| Branche (WZ-Code) | `industry_code` |
| Lernregel | `rule` |
| Buchungsstapel | `export_batch` |
