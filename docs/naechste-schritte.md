# Nächste Schritte – Start der Umsetzung

Stand: 28.10.2026 · Ziel bis Ende November 2026: Machbarkeitstest fertig und kleine Demo „Beleg rein → Buchungsvorschlag raus“ zum Zeigen.

---

## Warum Ende November wichtig ist

Die Kanzlei wägt gerade ab: cisbox testen oder DATEV ausbauen. Wenn sie sich vorher für einen cisbox-Test entscheidet, ist das Zeitfenster für Simply Done AI erst einmal zu. Deshalb: **nicht bis Februar warten**, sondern mit dem Ergebnis des Machbarkeitstests spätestens Ende November zu Markus Pfaar gehen. Messwerte plus eine kleine Demo reichen als Gesprächsgrundlage.

---

## Schritt 1 – Einrichtung auf deinem PC (heute oder morgen, ca. 45 Minuten)

| Nr. | Was | Wie |
|---|---|---|
| 1 | Datenschutz-Einstellung in Claude | claude.ai → Einstellungen → Datenschutz → „Daten zur Modellverbesserung“ ausschalten |
| 2 | Git für Windows | git-scm.com/downloads/win → installieren, Standardeinstellungen |
| 3 | Python 3.12 | python.org/downloads → beim Installieren „Add python.exe to PATH“ anhaken |
| 4 | Claude Code | Einfachster Weg: in der Claude-Desktop-App den Bereich für Code öffnen und den Projektordner wählen. Alternativ PowerShell: `irm https://claude.ai/install.ps1 \| iex`, danach im Projektordner `claude` starten und mit dem Pro-Konto anmelden |
| 5 | GitHub | Privates Repository `sdai-belegautomatik` anlegen. Claude Code verbindet den Ordner damit, wenn du es in der ersten Sitzung sagst |
| 6 | Docker Desktop | Erst für Phase 0 nötig (nach dem Machbarkeitstest) |

Modell in Claude Code: `/model opusplan`, Effort: `/effort high`.

---

## Schritt 2 – Erste Sitzung in Claude Code

Im Projektordner starten und diesen Auftrag einfügen:

```text
Lies CLAUDE.md, docs/projektplan.md und docs/recherche/2026-10-28_ki-anbieter-ohne-aws.md.
Setze die Phase „Test“ (Machbarkeitstest) um. Stelle keine Rückfragen, triff Entscheidungen
selbst und halte sie in docs/entscheidungen/ fest. Schreib zuerst einen kurzen Plan.

Umfang:
1. Richte Git ein (.gitignore mit .env, __pycache__, testdaten/ausgaben/) und verbinde das
   private GitHub-Repository sdai-belegautomatik.
2. Lade die Beispielrechnungen der KoSIT-XRechnung-Testsuite nach testdaten/kosit/.
3. Erzeuge 20 synthetische PDF-Rechnungen von erfundenen Firmen nach testdaten/synthetisch/:
   verschiedene Branchen, 7 % und 19 %, gemischte Steuersätze auf einer Rechnung,
   eine Gutschrift, eine Reverse-Charge-Rechnung (§ 13b), eine Kleinbetragsrechnung,
   drei als schlechte Scans (Bild, schief, verrauscht). Zu jeder Rechnung die erwarteten
   Ergebnisse als JSON in testdaten/goldstandard/.
4. Baue ein Python-Skript: Rechnung einlesen (XML direkt, PDF-Textlayer mit PyMuPDF,
   Scans mit docTR), pseudonymisieren, über die LLMProvider-Schnittstelle an zwei
   Anbieter schicken: bedrock (eu.anthropic.claude-sonnet-5-5, Region eu-central-1)
   und stackit (Qwen3-VL 235B und GPT-OSS 120B). Ausgabe als JSON nach festem Schema:
   Kopfdaten, Positionen, Steuersätze, Vorschlag Sachkonto SKR03.
5. Zugangsdaten nur aus .env. Lege .env.example mit leeren Platzhaltern an.
   Solange .env leer ist, teste alles mit einem Platzhalter-Anbieter.
6. Vergleiche mit dem Goldstandard und schreibe docs/machbarkeitstest-bericht.md:
   Trefferquote je Feld und Anbieter, Kosten pro Beleg, Laufzeit, Empfehlung.
7. Trage das Ergebnis in docs/protokoll.md ein.
```

---

## Schritt 3 – Konten für die KI-Anbieter (diese Woche)

Beide ohne Grundgebühr, Abrechnung nur nach Verbrauch. Konten auf **Simply Done AI** anlegen.

| Anbieter | Was tun | Ergebnis |
|---|---|---|
| AWS | Konto anlegen → Budget-Alarm bei 20 € → Bedrock → Region Frankfurt (`eu-central-1`) → Zugang zu Anthropic-Modellen beantragen (einmaliges Formular) → Zugangsschlüssel für einen eigenen Benutzer erzeugen | Werte in `.env` eintragen |
| STACKIT | Geschäftskonto anlegen → Projekt → AI Model Serving aktivieren → Zugangstoken erzeugen | Wert in `.env` eintragen |

**Zugangsschlüssel nie in einen Chat kopieren**, auch nicht in Claude Code. Nur direkt in die Datei `.env` im Projektordner schreiben.

---

## Schritt 4 – E-Mail an STACKIT (diese Woche, kostet nichts)

Keine Anfrage an cisbox (Entscheidung vom 28.10.2026).

### E-Mail an STACKIT

**Betreff:** Anfrage AI Model Serving – Einsatz für Steuerkanzleien (§ 203 StGB)

> Guten Tag,
>
> die Simply Done AI entwickelt eine Software, die Eingangsrechnungen für Steuerkanzleien ausliest und Buchungsvorschläge erstellt. Für die KI-Verarbeitung prüfen wir STACKIT AI Model Serving. Da unsere Kunden Berufsgeheimnisträger sind, bitten wir um Auskunft zu folgenden Punkten:
>
> 1. Schließen Sie für AI Model Serving eine Vereinbarung zur Verschwiegenheit nach § 203 StGB bzw. § 62a StBerG ab?
> 2. Werden Eingaben und Ausgaben gespeichert oder protokolliert? Wenn ja, wie lange und wozu?
> 3. Findet die Verarbeitung ausschließlich in Rechenzentren in Deutschland statt?
> 4. Wie ist der Auftragsverarbeitungsvertrag geregelt?
> 5. Welche Preise gelten pro Million Token für Qwen3-VL 235B und GPT-OSS 120B?
>
> Vielen Dank und freundliche Grüße
> Paul Graß
> Geschäftsführender Gesellschafter, Simply Done AI

---

## Schritt 5 – Termin mit Markus Pfaar (spätestens 27.11.2026)

Mitbringen:
- Machbarkeitstest-Bericht mit Trefferquoten
- Kurze Live-Demo: eine Testrechnung rein, Buchungsvorschlag raus
- Kostenvergleich aus `docs/kosten.md` (cisbox ca. 35.000 € gegen ca. 1.400 € pro Monat bei 50.000 Belegen)
- Offenlegung: Rolle als Angestellter und Geschäftsführer von Simply Done AI, Vorschlag für eine schriftliche Regelung
- Vorschlag Pilot: 10 Mandanten, 6 Monate, Vergleich mit dem DATEV-Service
