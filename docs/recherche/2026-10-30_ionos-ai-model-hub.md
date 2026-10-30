# Recherche: IONOS AI Model Hub als deutscher KI-Anbieter

Stand: 30.10.2026 · Erstellt von Claude für Simply Done AI · Anlass: Absage von STACKIT am 30.10.2026
Hinweis: Keine Rechtsberatung. Bewertungen auf Basis der verlinkten Quellen.

## Ergebnis

**IONOS ist eine vollwertige deutsche Alternative für das Auslesen der Belege.** Das Modell GPT-OSS 120B, das wir über Bedrock gemessen haben (Pflichtfelder 99,2 %, Positionen 100 %), gibt es bei IONOS zu fast demselben Preis. Rechtlich ist IONOS günstiger als AWS: Die Standard-AVV enthält bereits eine Verpflichtung nach § 203 StGB.

**Einschränkung:** IONOS bietet **kein Claude** an. Für die Kontierung, bei der Claude im Test deutlich besser war (88,5 % gegenüber 62,5 % bei GPT-OSS), bleibt entweder Claude über Bedrock oder das größere Qwen-Modell bei IONOS, das noch nicht gemessen ist.

## Eckdaten

| Punkt | Stand | Quelle |
|---|---|---|
| Vertragspartner | IONOS Cloud GmbH, Berlin | [noirdoc.de](https://www.noirdoc.de/anbieter/ionos/) |
| Rechenzentrum | Alle Inferenz in Deutschland, Zugriff auf Betriebsdaten nur durch Personal in der EU | [IONOS Data Handling](https://docs.ionos.com/cloud/ai/ai-model-hub/governance-and-compliance/data-handling) |
| Speicherung von Prompts und Antworten | Keine dauerhafte Speicherung, nicht in Logs; nur Zeitpunkt, Modell und Tokenzahl werden protokolliert | [IONOS Data Handling](https://docs.ionos.com/cloud/ai/ai-model-hub/governance-and-compliance/data-handling) |
| Training mit Kundendaten | Nein | [IONOS Data Handling](https://docs.ionos.com/cloud/ai/ai-model-hub/governance-and-compliance/data-handling) |
| Aufbewahrung der Metadaten | Keine Frist veröffentlicht („nur so lange wie nötig“) | [IONOS Data Handling](https://docs.ionos.com/cloud/ai/ai-model-hub/governance-and-compliance/data-handling), [actcomp.de](https://actcomp.de/en/tools/ionos-ai-model-hub) |
| AVV | Standard-AVV, Teil des Vertrags; kein eigener Anhang für den AI Model Hub | [IONOS AVV](https://www.ionos.de/terms-gtc/avv/), [actcomp.de](https://actcomp.de/en/tools/ionos-ai-model-hub) |
| § 203 StGB | Standard-AVV verpflichtet zur Wahrung von Berufsgeheimnissen nach § 203 StGB | [IONOS AVV](https://www.ionos.de/terms-gtc/avv/), [noirdoc.de](https://www.noirdoc.de/anbieter/ionos/) |
| Schnittstelle | OpenAI-kompatibel; Zugang über Token aus dem Token Manager des Data Center Designer | [european.cloud](https://european.cloud/2026/01/ionos-ai-model-hub/), [IONOS Access Management](https://docs.ionos.com/cloud/ai/ai-model-hub/how-tos/access-management) |
| Konto | Vertrag für die IONOS Public Cloud nötig; Tokens sind an Cloud-Nutzer gebunden. Anforderungen an Geschäftskunden (z. B. GbR) nicht veröffentlicht | [IONOS Access Management](https://docs.ionos.com/cloud/ai/ai-model-hub/how-tos/access-management) |
| Fixkosten | keine, Abrechnung pro Token | [IONOS Preisliste](https://docs.ionos.com/cloud/support/general-information/price-list/ionos-cloud-gmbh-de) |

## Preise (netto, je Million Token, gültig ab 29.10.2026)

Quelle: [IONOS Cloud GmbH Preisliste](https://docs.ionos.com/cloud/support/general-information/price-list/ionos-cloud-gmbh-de)

| Modell | Eingabe | Ausgabe | Einordnung für uns |
|---|---|---|---|
| **gpt-oss-120b** | 0,15 € | 0,65 € | Gleiches Modell wie bei Bedrock gemessen. Erste Wahl fürs Auslesen |
| **Qwen3.5-397B-A17B** | 0,60 € | 3,60 € | Größtes Modell, Kandidat für bessere Kontierung; noch nicht gemessen |
| Llama 3.3 70B Instruct | 0,65 € | 0,65 € | Älteres Modell, Vergleich optional |
| Mistral Small 24B Instruct | 0,10 € | 0,30 € | Klein und günstig; vermutlich zu schwach für Positionen |
| Qwen3.8-27B | 0,40 € | 2,70 € | Mittelgroß |
| LightOnOCR 2 | 0,15 € | 0,30 € | Texterkennung; wir erkennen lokal mit docTR und schicken keine Bilder (Entscheidung 2026-10-28) |

Hochrechnung mit den gemessenen Tokenzahlen von GPT-OSS (ca. 1.330 ein, 1.010 aus): **ca. 0,09 Cent je Beleg**, bei 50.000 Belegen ca. 45 € im Monat.

## Vergleich mit AWS Bedrock

| | AWS Bedrock (Frankfurt) | IONOS AI Model Hub |
|---|---|---|
| Firmensitz | USA (US CLOUD Act) | Deutschland |
| § 203 StGB | Nur individuell über AWS-Partner | In der Standard-AVV |
| Claude | ja | nein |
| GPT-OSS 120B | ja, 0,15 $ / 0,60 $ | ja, 0,15 € / 0,65 € |
| Konto vorhanden | ja | nein |

## Messergebnis (31.10.2026)

Gemessen mit 42 Testbelegen, Details in `docs/machbarkeitstest-bericht.md`:

| | GPT-OSS 120B | Qwen3.5-397B-A17B |
|---|---|---|
| Pflichtfelder | 98,9 % | 98,7 % |
| Positionen | 100 % | 100 % |
| Sachkonto | 61,5 % | **87,5 %** (Claude: 88,5 %) |
| Kosten je Beleg | 0,09 Cent | 1,90 Cent |
| Antwortzeit | 6 s | 61 s, Denkmodus nicht abschaltbar, Token-Limit 24.000 nötig |

Modellnamen bei IONOS: `openai/gpt-oss-120b`, `Qwen/Qwen3.5-397B-A17B`. Neue Konten laufen als „Testdrive“; Zugangstoken erst nach Freischaltung der Vollversion.

## Empfehlung

1. **IONOS-Konto für Simply Done AI beantragen** (Public-Cloud-Vertrag). Falls IONOS wie STACKIT ablehnt, beim Support nach den Kriterien fragen.
2. Nach Freischaltung **GPT-OSS 120B und Qwen3.5-397B bei IONOS messen**. Der Code ist vorbereitet (Anbieter `ionos_gptoss`, `ionos_qwen`).
3. Erreicht GPT-OSS bei IONOS dieselbe Qualität wie bei Bedrock: **Auslesen bei IONOS**, Kontierung über Regeln und für den Rest entweder Qwen3.5-397B bei IONOS (falls gut genug) oder Claude über Bedrock.
4. Anwaltlich prüfen lassen, ob die Standard-AVV mit § 203-Klausel für eine Steuerkanzlei ausreicht (Teil der Rechtsspur R3/R3a im Projektplan).
