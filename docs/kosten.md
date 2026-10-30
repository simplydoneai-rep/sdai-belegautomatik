# Kostenübersicht – Simply Done AI: Belegautomatik

Stand: 31.10.2026 · Alle Preise netto (zzgl. 19 % USt., als Unternehmen abziehbar) · Dollarbeträge 1:1 in Euro gerechnet
Vorher: Stand 28.10.2026 mit geschätzten KI-Kosten; jetzt mit **gemessenen** KI-Kosten aus `docs/machbarkeitstest-bericht.md` und aktuellen Hetzner-Preisen nach der Preiserhöhung vom 15.06.2026.

---

## 1. Ergebnis auf einen Blick

| Phase | Belege pro Monat | Laufende Kosten pro Monat | pro Beleg |
|---|---|---|---|
| Demo (bis Feb 2027) | Testbelege | ca. 120 € (Claude Max für die Entwicklung, KI-Tests aus Guthaben) | – |
| Pilot (10 Mandanten, ab Mär 2027) | ca. 500 | ca. 530 € (Server 98 €, KI ca. 10 €, Werkzeuge, Versicherung, Steuerberatung) | ca. 1 € (Fixkosten auf wenige Belege verteilt) |
| Ganze Kanzlei | ca. 50.000 | ca. **3.550 €** inkl. Verwaltung, Rücklagen und Arbeitszeit | ca. **7 Cent** |

**Einmalig vor dem Pilot:** ca. 5.500–17.800 € (Anwalt, Datenschutz, Sicherheitstest, Versicherung), ohne GmbH-Gründung. Details in Abschnitt 5 und `docs/rechtsberatung.md`.

**Break-even** (laufende Kosten gedeckt): bei 0,35 € pro Beleg ab ca. **8.900 Belegen pro Monat**, das sind rund 180 Mandanten mit je 50 Belegen.

---

## 2. Speicher für 50.000 Belege im Monat

**Annahme:** im Schnitt 500 KB je Beleg. Echte Rechnungen mit Logo haben 100–300 KB, Scans 300 KB–1 MB je Seite, Handyfotos 1–4 MB, E-Rechnungen (XML) unter 100 KB. Dazu 20 % für Texterkennung, Vorschaubilder und Datenbank-Sicherungen.

| | Menge |
|---|---|
| Je Monat | ca. 30 GB |
| Je Jahr | ca. 0,36 TB |
| Nach Ablauf der Aufbewahrungsfrist (8 Jahre ab Ende des Ausstellungsjahres, also bis zu 9 Jahre) | ca. 3,2 TB je Kopie |

**Kosten Hetzner Object Storage** (6,49 € Grundpreis inkl. 1 TB Speicher und 1 TB Datenverkehr, darüber ca. 6,47 € je TB), zwei Standorte (Nürnberg und Falkenstein, `CLAUDE.md` Regel 9b):

| Zeitpunkt | Speicher je Kopie | Kosten für beide Standorte |
|---|---|---|
| nach 1 Jahr | 0,4 TB | ca. 13 € |
| nach 3 Jahren | 1,1 TB | ca. 14 € |
| nach 5 Jahren | 1,8 TB | ca. 23 € |
| nach 9 Jahren (Endstand) | 3,2 TB | ca. 42 € |

**Speicher ist also kein Kostenfaktor.** Unveränderbare Speicherung (Object Lock) ist bei Hetzner möglich und muss beim Anlegen des Speichers eingeschaltet werden; Verschlüsselung mit eigenem Schlüssel ist Pflicht, weil Hetzner nicht automatisch verschlüsselt.

Hinweis: Solange die Belege per Belegtransfer im DATEV-Archiv liegen, ist unser Speicher nur Arbeitskopie (`CLAUDE.md` Regel 13). Die Rechnung oben ist der ungünstigste Fall mit voller Aufbewahrung bei uns.

---

## 3. Server

**Last:** Belege kommen nicht gleichmäßig. Annahme: die Hälfte des Monats in 5 Arbeitstagen, also bis zu 5.000 Belege am Tag oder 500 pro Stunde.
- **Texterkennung** (nur Scans und Fotos, ca. 35 %, 1,5 Seiten, 4,5 s je Seite): im Mittel weniger als ein Prozessorkern dauerhaft belegt. Eine Grafikkarte ist nicht nötig.
- **KI-Aufrufe** laufen bei IONOS, nicht auf unserem Server. Bei Qwen3.5 (ca. 1 Minute je Beleg) sind in der Spitze etwa 4–5 Anfragen gleichzeitig offen; das erledigen Hintergrund-Jobs (Redis + RQ).
- **Datenbank:** ca. 1 GB je Monat (ausgelesene Daten, Vorschläge, Audit-Log), also ca. 12 GB im Jahr.

### Pilot (10 Mandanten, ca. 500 Belege im Monat)

| Posten | Produkt | Preis pro Monat |
|---|---|---|
| Anwendung, Texterkennung, Datenbank auf einem Server | CPX42: 8 vCPU (geteilt), 16 GB RAM | 69,49 € |
| Server-Sicherung (20 % des Serverpreises) | Hetzner Backups | ca. 14 € |
| Belegspeicher Nürnberg + Kopie Falkenstein | Object Storage, 2 × 1 TB inklusive | 12,98 € |
| IPv4-Adresse, Domain | | ca. 2 € |
| **Summe Server** | | **ca. 98 €** |

### Ganze Kanzlei (ca. 50.000 Belege im Monat)

| Posten | Produkt | Preis pro Monat |
|---|---|---|
| Anwendung und Texterkennung | CCX33: 8 dedizierte vCPU, 32 GB RAM | 138,49 € |
| Datenbank (getrennt, sicherer) | CCX23: 4 dedizierte vCPU, 16 GB RAM | 85,99 € |
| Server-Sicherung (20 %) | Hetzner Backups | ca. 45 € |
| Belegspeicher 2 Standorte | Object Storage | 13 € (Jahr 1) bis 42 € (Endstand) |
| IPv4, Domain, Überwachung | | ca. 10 € |
| **Summe Server** | | **ca. 290–320 €** |

Günstigere Alternative bei stabilem Betrieb: dedizierter Server AX42 (97,30 € im Monat, 49 € Einrichtung, Falkenstein), aber ohne die bequeme Skalierung und Sicherung der Cloud.

---

## 4. KI-Kosten (gemessen)

Gemessen am 30./31.10.2026 mit 42 Testbelegen (`docs/machbarkeitstest-bericht.md`):

| Modell | Anbieter | Kosten je Beleg | Wofür |
|---|---|---|---|
| GPT-OSS 120B | IONOS (Deutschland) | **0,09 Cent** | Auslesen |
| Qwen3.5 397B | IONOS (Deutschland) | 1,90 Cent | Kontierung, nur ohne Lernregel |
| Claude Sonnet 4.6 | AWS Bedrock (Frankfurt) | 1,27 Cent | Rückfallebene |

**Bei 50.000 Belegen im Monat, empfohlene Aufteilung:**

| Posten | Annahme | Kosten pro Monat |
|---|---|---|
| Auslesen mit GPT-OSS | alle Belege außer E-Rechnungen; vorsichtig: alle 50.000 | ca. 45 € |
| Kontierung mit Qwen3.5 | im 1. Jahr bei der Hälfte der Belege keine Lernregel | ca. 475 € |
| Kontierung mit Qwen3.5 | ab dem 2. Jahr bei 20 % der Belege | ca. 190 € |
| **Summe KI** | | **ca. 520 € (Jahr 1), ca. 235 € (danach)** |

Die Rechnung ist vorsichtig: E-Rechnungen brauchen gar keine KI, und wenn Qwen3.5 nur die offenen Positionen statt des ganzen Belegs bekommt, sinken die Kosten weiter.

---

## 5. Einmalige Kosten vor dem Pilot

| Posten | Kosten | Quelle / Grundlage |
|---|---|---|
| Anwalt IT- und Berufsrecht: Vertrag, AVV + § 62a StBerG, Prüfung Pseudonymisierung, Einwilligungsvorlage | 1.500–4.000 € | `docs/rechtsberatung.md` |
| Datenschutz-Folgenabschätzung (falls extern) | 0–3.000 € | `docs/rechtsberatung.md` |
| Externer Sicherheitstest | 3.000–7.000 € | `docs/projektplan.md` |
| Versicherung IT-/Cyber- und Vermögensschadenhaftpflicht, 1. Jahr | 1.000–3.000 € | Schätzung, Angebote einholen |
| Prüfung Nebentätigkeit (optional) | 0–800 € | `docs/rechtsberatung.md` |
| **Summe** | **ca. 5.500–17.800 €** | |
| Optional: Gründung GmbH statt GbR | ca. 800–1.500 € + 25.000 € Stammkapital (12.500 € sofort) | begrenzt die Haftung |

---

## 6. Verwaltung und laufende Kosten von Simply Done AI

| Posten | pro Monat | Annahme |
|---|---|---|
| Steuerberatung und Buchhaltung für Simply Done AI | ca. 150 € | extern, nicht über die Kanzlei (Interessenkonflikt) |
| Versicherung | ca. 170 € | 2.000 € im Jahr |
| Entwicklungswerkzeuge (Claude Max, GitHub, Kleinkram) | ca. 120 € | |
| Laufende Rechtsberatung | ca. 100 € | Rücklage |
| Rücklage Sicherheitstest (jährlich) | ca. 400 € | 5.000 € im Jahr |
| Rücklage IDW-PS-880-Testat | ca. 600 € | ca. 20.000 € alle 3 Jahre, erst für den Vertrieb an andere Kanzleien nötig |
| Arbeitszeit Betrieb und Support | ca. 1.200 € | 20 Stunden × 60 € kalkulatorisch |
| **Summe** | **ca. 2.740 €** | |

Die Arbeitszeit für die **Entwicklung** ist nicht eingerechnet.

---

## 7. Gesamtrechnung und Preisszenarien bei 50.000 Belegen

| | pro Monat |
|---|---|
| Server (Abschnitt 3) | ca. 300 € |
| KI, 1. Jahr (Abschnitt 4) | ca. 520 € |
| Verwaltung, Rücklagen, Arbeitszeit (Abschnitt 6) | ca. 2.740 € |
| **Gesamtkosten** | **ca. 3.560 €**, also ca. **7 Cent je Beleg** |

| Preis je Beleg | Umsatz pro Monat | Überschuss pro Monat | Ersparnis der Kanzlei gegenüber cisbox (0,70 €) | Break-even |
|---|---|---|---|---|
| 0,25 € | 12.500 € | ca. 8.900 € | ca. 22.500 € im Monat | ca. 12.600 Belege |
| **0,35 €** | **17.500 €** | **ca. 13.900 €** | **ca. 17.500 € im Monat** | **ca. 8.900 Belege** |
| 0,50 € | 25.000 € | ca. 21.400 € | ca. 10.000 € im Monat | ca. 6.100 Belege |

Break-even: Fixkosten ca. 3.000 € im Monat geteilt durch (Preis − ca. 1,1 Cent variable KI-Kosten).

**Einordnung:** Auch der niedrigste Preis trägt den Betrieb deutlich. Den Ausschlag geben der Preis des DATEV Automatisierungsservice (noch unbekannt, aus der Preisliste der Kanzlei) und der gemessene Nutzen im Pilot. Ein Kampfpreis weit unter 0,25 € ist nicht nötig und wirkt bei Kanzleisoftware eher unseriös.

---

## 8. Preisrisiken

- Hetzner hat die Cloud-Preise 2026 zweimal erhöht (1. April und 15. Juni). Bestehende Server behalten ihren Preis; die günstige CX-Linie ist nicht mehr bestellbar.
- KI-Preise ändern sich häufig, bisher meist nach unten. Die Schnittstelle `LLMProvider` erlaubt einen schnellen Wechsel.
- Qwen3.5 ist langsam und „denkt“ lange; wird es knapp, übernimmt Claude oder ein kleineres Modell mit Branchen-Regelwerk.
- Die Annahme von 50 Belegen je Mandant und Monat ist ungeprüft. Die echte Zahl kommt aus der Kanzlei.

---

## Quellen
- [Hetzner: Preisanpassung 15.06.2026 (CPX, CCX, AX42)](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
- [bitdoze: Hetzner Cloud Review 2026](https://www.bitdoze.com/hetzner-cloud-review/)
- [usehcm: Hetzner Cloud Pricing 2026](https://usehcm.com/hetzner-pricing)
- [whichdevtool: Hetzner Object Storage Preise 2026](https://whichdevtool.com/tools/hetzner-object-storage/)
- [GitHub agentdeals: Hetzner Object Storage, was der Grundpreis enthält](https://github.com/robhunter/agentdeals/issues/2555)
- [GitHub agentdeals: Einrichtungsgebühren AX42/AX102](https://github.com/robhunter/agentdeals/issues/2273)
- [Hetzner Docs: Object Lock](https://docs.hetzner.com/de/storage/object-storage/howto-protect-objects/protect-object-lock-retention)
- [IONOS Cloud Preisliste v2026-10-29](https://docs.ionos.com/cloud/support/general-information/price-list/ionos-cloud-gmbh-de)
- KI-Kosten gemessen: `docs/machbarkeitstest-bericht.md`
