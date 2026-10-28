# Kostenübersicht – Simply Done AI: Belegautomatik

Stand: 28.10.2026 · Alle Hetzner-Preise netto (zzgl. 19 % USt., als Unternehmen abziehbar) · Dollarbeträge zur Sicherheit 1:1 in Euro gerechnet

---

## 1. Externe Fixkosten pro Monat

| Posten | Demo (bis Feb 2027) | Pilot (ab Mär 2027) |
|---|---|---|
| Claude Pro (Simply Done AI, bereits vorhanden) | 20 € | 20 € |
| Hetzner Server und Speicher | 0 € (läuft auf deinem PC) | 97 € (Minimum) bis 121 € (empfohlen) |
| KI-Anbieter (AWS, STACKIT oder IONOS) | 0 € Grundgebühr | 0 € Grundgebühr |
| Domain | 0 € | ca. 1 € |
| **Summe Fixkosten** | **20 €** | **ca. 120–145 €** |

**Variabel**, nur bei Nutzung: KI ca. 0,02 € pro Beleg. In der Demo einige hundert Testläufe, zusammen unter 10 €. Im Pilot bei ca. 500 Belegen ca. 10 € pro Monat.

**Wichtig:** Das Claude-Pro-Abo deckt die Arbeit mit Claude Code ab, nicht die KI-Aufrufe der eigenen Software. Die laufen immer über ein eigenes Konto beim KI-Anbieter und werden pro Verbrauch abgerechnet.

---

## 2. Hetzner im Pilot

| Posten | Produkt | Minimum | Empfohlen |
|---|---|---|---|
| Anwendung und Texterkennung | CPX42: 8 vCPU, 16 GB RAM, 320 GB SSD | 69,99 € | 69,99 € |
| Datenbank auf eigenem Server | CPX22: 2 vCPU, 4 GB RAM, 80 GB SSD | – (läuft mit auf CPX42) | 19,99 € |
| Server-Backups (ca. 20 % des Serverpreises) | | 14,00 € | 18,00 € |
| Belegspeicher Nürnberg, Object Lock | Object Storage, 1 TB inklusive | 6,49 € | 6,49 € |
| Zweite Sicherung Falkenstein | Object Storage, 1 TB inklusive | 6,49 € | 6,49 € |
| **Summe** | | **ca. 97 €** | **ca. 121 €** |

Ein getrennter Datenbank-Server ist sicherer, weil ein Angriff auf die Anwendung nicht direkt an die Daten kommt. Für 10 Pilot-Mandanten ist das Minimum vertretbar.

---

## 3. Verträge bei Aktivierung (vor dem ersten echten Beleg)

| Anbieter | Vertrag | Kosten |
|---|---|---|
| Hetzner | Auftragsverarbeitungsvertrag (online in der Konsole) + Verschwiegenheitsvereinbarung nach § 203 (über Support) | kostenlos |
| KI-Anbieter | Auftragsverarbeitungsvertrag (online) + § 203-Vereinbarung | AWS und STACKIT: kostenlos online; § 203 bei AWS über Partner, Konditionen offen; bei STACKIT anfragen |
| Kanzlei | AVV + Vereinbarung nach § 62a StBerG | Anwalt, einmalig |

### Einmalige externe Kosten vor dem Pilot (grobe Schätzung ohne Quelle, Angebote einholen)
| Posten | Größenordnung |
|---|---|
| Anwalt IT- und Berufsrecht (Verträge, Einwilligung, Prüfung Pseudonymisierung) | 1.500–4.000 € |
| Externer Sicherheitstest | 3.000–7.000 € |
| IT- und Cyber-Haftpflicht (pro Jahr) | 500–1.500 € |

---

## 4. KI-Anbieter: Fixkosten im Vergleich

| Anbieter | Fixkosten | Hinweis |
|---|---|---|
| AWS Bedrock (Claude) | keine | US-Konzern, § 203 nur über Partner |
| STACKIT AI Model Serving | keine | deutsch, offene Modelle, § 203 anfragen |
| IONOS AI Model Hub | keine genannt | deutsch, § 203-Bestätigung ausstehend |
| Telekom T-Cloud LLM Hub | 1.000 € Mindestumsatz pro Monat | rechtlich am saubersten, zu teuer für den Pilot |
| Eigener GPU-Server | 214 € (Helsinki) bzw. ab 1.499 € (Falkenstein) | nur bei hohem Volumen |

Details: `docs/recherche/2026-10-28_ki-anbieter-ohne-aws.md`.

---

## 5. Später: Betrieb für die ganze Kanzlei (ab Sep 2027)

Rund 1.000 Mandanten, ca. 50.000 Belege pro Monat (Annahme: 50 je Mandant).

| Posten | Produkt | Preis pro Monat |
|---|---|---|
| 2 Anwendungsserver | 2 × CCX33: 8 dedizierte vCPU, 32 GB RAM | 277,98 € |
| Datenbank-Server | CCX23: 4 dedizierte vCPU, 16 GB RAM | 86,49 € |
| Backups | ca. 20 % | ca. 73 € |
| Belegspeicher 2 Standorte | Object Storage | 12,98 € |
| Claude Pro | | 20 € |
| **Fixkosten** | | **ca. 470 €** |
| KI (variabel) | 50.000 × ca. 0,018 $ | ca. 900 € |
| **Gesamt** | | **ca. 1.370 €** ≈ **0,03 € pro Beleg** |

Zum Vergleich: cisbox bei 50.000 Belegen ca. 35.000 € pro Monat vor Rabatt.

---

## Preisrisiken
- Hetzner hat am 15.06.2026 die Cloud-Preise stark erhöht (CPX bis +176 %). Bestehende Server behalten ihren Preis. Die günstige CX-Linie ist seit Herbst 2026 nicht bestellbar.
- Bedrock-Preise für das EU-Profil können vom Anthropic-Listenpreis abweichen.

## Quellen
- [Hetzner Cloud Preise nach dem 15.06.2026 (Bitdoze)](https://www.bitdoze.com/md/es/hetzner-cloud-precios-2026.md)
- [WZ-IT: Hetzner-Preiserhöhung Juni 2026](https://wz-it.com/blog/hetzner-preiserhoehung-juni-2026-cpx-ccx-alternativen/)
- [Hetzner Object Storage Preise](https://www.hetzner.com/de/storage/object-storage/)
- [WZ-IT: Hetzner GPU-Server Vergleich, Stand 13.10.2026](https://wz-it.com/blog/hetzner-gpu-server-vergleich/)
- [Claude Sonnet 5.5 Preise (computingforgeeks)](https://computingforgeeks.com/claude-sonnet-5-5-released-features-benchmarks/)
- [Claude-Tarife 2026 (ai-toolbox)](https://www.ai-toolbox.co/claude-models/claude-pricing-plans-2026)
- [T-Systems LLM Hub: Tarife](https://docs.llmhub.t-systems.net/plans/)
- [STACKIT AI Model Serving (innFactory)](https://innfactory.de/de/cloud/stackit/produkte/ai-model-serving/)
