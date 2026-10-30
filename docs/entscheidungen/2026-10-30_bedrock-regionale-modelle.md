# Entscheidung: Offene Modelle (GPT-OSS, Qwen) über Bedrock in Frankfurt zulassen

Datum: 30.10.2026 · Status: entschieden (Paul Graß: „Wir machen weiter mit AWS“)

## Kontext
- STACKIT hat das Kundenkonto von Simply Done AI am 30.10.2026 ohne Angabe von Gründen abgelehnt. Die geplante Messung der offenen Modelle GPT-OSS 120B und Qwen3 bei STACKIT fällt damit vorerst aus.
- Amazon Bedrock bietet in `eu-central-1` (Frankfurt) GPT-OSS 120B und Qwen3 235B A22B 2507 direkt an (Abfrage der Modellliste am 30.10.2026, Abrufart ON_DEMAND).
- `CLAUDE.md` Regel 5 verlangte bisher für Bedrock das Präfix `eu.`. Diese Modelle haben kein Geografie-Präfix, weil sie nur in der gewählten Region laufen.

## Entscheidung
Bei Bedrock sind zulässig:
1. EU-Inferenzprofile (`eu.`): Verarbeitung in EU-Regionen. Pflicht für Claude.
2. Modelle ohne Geografie-Präfix, aufgerufen mit Client in `eu-central-1`: Verarbeitung nur in Frankfurt.

Abgelehnt werden: Profile außerhalb der EU (`us.`, `us-gov.`, `apac.`, `global.`, `ca.`, `jp.`, `au.`), Claude ohne `eu.`-Profil, Claude Fable, jede andere Region als `eu-central-1`. Umsetzung: `backend/app/llm/bedrock.py`, Tests in `backend/tests/test_llm_und_vergleich.py`. Neue Anbieter `bedrock_gptoss` und `bedrock_qwen`, Modell-IDs in `.env`.

## Begründung
- Datenschutz: Modelle ohne Präfix werden nur in der Region des Clients ausgeführt; das ist enger als ein EU-Profil.
- Die Qualitätsfrage „Reicht ein offenes Modell?“ lässt sich so ohne STACKIT beantworten. Die gleichen Modelle laufen auch bei IONOS oder auf einem eigenen Server; das Ergebnis ist übertragbar.

## Folgen
- Weiterhin Abhängigkeit von AWS, solange kein deutscher Anbieter verfügbar ist. Alternativen: Nachfrage bei STACKIT über den Support, IONOS AI Model Hub, eigener GPU-Server (`docs/recherche/2026-10-28_ki-anbieter-ohne-aws.md`).
- § 203-Vereinbarung über einen AWS-Partner wird wichtiger (`docs/projektplan.md`, R3).
- Preise der offenen Modelle auf Bedrock stammen aus Preisvergleichsseiten und sind vor dem Pilot auf der offiziellen AWS-Preisseite für `eu-central-1` zu prüfen (`backend/app/llm/preise.json`).
