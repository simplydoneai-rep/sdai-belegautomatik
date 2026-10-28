# Recherche: KI-Anbieter ohne AWS

Stand: 28.10.2026 · Erstellt von Claude für Simply Done AI
Hinweis: Keine Rechtsberatung. Bewertungen auf Basis der verlinkten Quellen.

## Ergebnis

**Simply Done AI ist nicht auf AWS angewiesen.** Es gibt drei Wege, AWS zu vermeiden oder die Abhängigkeit klein zu halten:

1. **Weniger KI brauchen.** E-Rechnungen (XRechnung, ZUGFeRD) sind strukturiert und brauchen keine KI. Lernregeln und Buchungshistorie brauchen keine KI. Die KI wird nur für PDFs und Scans von unbekannten Lieferanten gebraucht. Dieser Anteil sinkt mit jedem Monat Lernen und mit der E-Rechnungspflicht.
2. **Deutsche KI-Anbieter mit offenen Modellen** statt Claude über AWS (Tabelle unten).
3. **Konsequente Pseudonymisierung**, sodass beim KI-Anbieter keine Mandantengeheimnisse ankommen (Rechtslage unten).

## Anbieter im Vergleich

| Anbieter | Rechenzentrum | Modelle | Fixkosten | § 203 StGB | Bewertung |
|---|---|---|---|---|---|
| **AWS Bedrock** (Claude) | EU-Regionen, Einstieg Frankfurt | Claude Sonnet 5.5, Opus 5.5 | keine, nur Verbrauch | individuelles Addendum über AWS-Partner | Beste Qualität, US-Konzern, Addendum mit Vorlauf |
| **STACKIT AI Model Serving** (Schwarz Gruppe) | Deutschland (Region eu01) | Qwen3-VL 235B (Bild und Text), GPT-OSS 120B, Llama 3.3 70B, Gemma 4 31B | keine für gemeinsam genutzte Modelle, Abrechnung pro Token | nicht öffentlich dokumentiert, bei STACKIT anfragen | **Beste Alternative**: deutsch, keine Fixkosten, Modell mit Bilderkennung |
| **IONOS AI Model Hub** | Deutschland (Berlin) | offene Sprachmodelle | nicht genannt, Abrechnung pro Token | laut Gosign „bedingt“: produktspezifische Bestätigung steht noch aus | Option, § 203 vorher klären |
| **Telekom T-Cloud LLM Hub** | Deutschland | offene Modelle, z. B. Mistral | **Mindestumsatz 1.000 € pro Monat** | Verschwiegenheitsvereinbarung deckt die KI-Dienste ausdrücklich ab | Rechtlich am saubersten, aber zu teuer für Demo und Pilot |
| **Eigener GPU-Server** (Hetzner) | Falkenstein oder Helsinki | beliebige offene Modelle | 214 € (nur Helsinki) bzw. ab 1.499 € (Falkenstein) | nur Hetzner-Vereinbarung nötig | Nur bei hohem Volumen sinnvoll |
| Anthropic-API direkt | USA | Claude | keine | keine öffentliche Vereinbarung | Nur mit Testdaten, nie mit echten Belegen |

## Rechtslage zur Pseudonymisierung

- **EuGH, Urteil vom 04.09.2025, C-413/23 P (EDSB gegen SRB):** Pseudonymisierte Daten können für einen Empfänger, der die Personen nicht wieder erkennen kann, anonym sein. Für diesen Empfänger gilt die DSGVO dann nicht. Der Verantwortliche muss die Betroffenen aber vorher über die Weitergabe informieren und den Schlüssel bei sich behalten.
- **BStBK-FAQ zu KI vom 27.10.2026:** Ist der KI-Anbieter nicht zur Verschwiegenheit verpflichtet, müssen Namen, Anschriften, Steuernummern und ähnliche Merkmale vor der Nutzung entfernt werden. Das Berufsgeheimnis schützt auch Daten von Unternehmen, nicht nur von Personen.

**Einschätzung:** Mit der Pseudonymisierung aus der `CLAUDE.md` (Mandant, Personen, IBAN, Steuernummern ersetzt) gibt es ein vertretbares Argument, dass beim KI-Anbieter kein Geheimnis offenbart wird. Restrisiko: Eine ungewöhnliche Kombination aus Lieferant, Artikeln und Beträgen könnte Rückschlüsse auf einen Mandanten erlauben. **Empfehlung:** Die Pseudonymisierung ist Pflicht, die § 203-Vereinbarung trotzdem anstreben. Beides zusammen ist belastbar. Das Argument „Pseudonymisierung reicht allein“ vor dem Pilot von einem Anwalt bestätigen lassen.

## Was der AWS-Vertrag kostet

- Konto, Kundenvertrag und Auftragsverarbeitungsvertrag (DPA): online, kostenlos, ohne Grundgebühr.
- Bedrock: nur Verbrauch, ca. 0,02 € pro Beleg.
- § 203-Addendum: kein öffentliches Standard-Dokument; der Weg über einen AWS-Partner kann bedeuten, dass die Abrechnung über diesen Partner läuft. Konditionen beim Partner erfragen.

## Entscheidung

Die Wahl des KI-Anbieters fällt im **Machbarkeitstest** anhand von Messwerten: dieselben 30 Testrechnungen durch Claude (Bedrock) und durch STACKIT (Qwen3-VL 235B und GPT-OSS 120B). Erreicht STACKIT die Zielwerte, wird AWS nicht gebraucht.

## Hinweis zum Claude-Abo

Das Claude-Pro-Abo deckt die Arbeit mit Claude und Claude Code ab, **nicht** die KI-Aufrufe der eigenen Software. Diese werden immer separat beim KI-Anbieter abgerechnet (Bedrock, STACKIT oder Anthropic-Konsole).

## Quellen
- [STACKIT AI Model Serving (innFactory, Stand 17.09.2026)](https://innfactory.de/de/cloud/stackit/produkte/ai-model-serving/)
- [STACKIT AI Model Serving: Leistungsbeschreibung](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/basics/service-description/)
- [IONOS AI Model Hub (european-alternatives.eu)](https://european-alternatives.eu/de/produkt/ionos-ai-model-hub)
- [Gosign: KI-Modelle für Berufsgeheimnisträger, Hosting-Status](https://www.gosign.de/en/ai-models-professional-secrecy/model/mistral-small-3/)
- [T-Systems LLM Hub: Tarife und Preise](https://docs.llmhub.t-systems.net/plans/)
- [Heuking: EuGH-Urteil zur Pseudonymisierung (C-413/23 P)](https://www.heuking.de/de/news-events/newsletter-fachbeitraege/artikel/richtungsweisendes-eugh-urteil-zur-pseudonymisierung-personenbezogener-daten.html)
- [BStBK: FAQ zum Einsatz von KI, Stand 27.10.2026](https://www.bstbk.de/downloads/bstbk/digitalisierung/BStBK_FAQ-KI_end.pdf)
- [Anthropic-Hilfe: API-Nutzung wird getrennt vom Abo abgerechnet](https://support.anthropic.com/en/articles/9876003-i-subscribe-to-claude-pro-why-do-i-have-to-pay-separately-for-api-usage-on-console)
