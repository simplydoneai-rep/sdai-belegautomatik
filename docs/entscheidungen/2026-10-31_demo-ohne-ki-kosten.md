# Entscheidung: Demo spielt aufgezeichnete KI-Antworten ab

Datum: 31.10.2026 · Status: entschieden (Wunsch Paul Graß: Demo ohne Nutzung von IONOS oder AWS)

## Kontext
Für das Gespräch mit Markus Pfaar (spätestens 27.11.2026) braucht es eine Vorführung „Beleg rein → Buchungsvorschlag raus“. Jeder KI-Aufruf kostet bei IONOS oder AWS Geld; Qwen3.5 braucht außerdem ca. eine Minute je Beleg, zu lang für eine Live-Vorführung.

## Entscheidung
- Die Demo (`backend/app/api/demo.py`, Start mit `demo_starten.bat`) führt **alle Schritte live und lokal** aus: Eingang mit SHA-256, E-Rechnung lesen bzw. Texterkennung, Pseudonymisierung, Steuerlogik, Ampel, Soll-Ist-Abgleich.
- **Nur die KI-Antwort wird abgespielt**: aus den Messläufen vom 30./31.10.2026, verknüpft über die Prüfsumme der Datei (`testdaten/demo/aufzeichnungen.json`, erzeugt mit `backend/scripts/demo_aufzeichnungen.py`). Der Abspiel-Anbieter (`app/llm/replay.py`) nutzt die normale `LLMProvider`-Schnittstelle und nimmt nur `PseudonymizedPayload` an.
- Die Oberfläche zeigt offen an, dass es eine Aufzeichnung ist, mit damaliger Antwortzeit und damaligen Kosten.
- Unbekannte Belege (eigener Upload) gehen an den regelbasierten Platzhalter ohne KI; die Ampel ist dann höchstens Gelb.
- Voreinstellung: Qwen3.5 397B bei IONOS (beste deutsche Kontierung); umschaltbar auf GPT-OSS, Claude und Qwen3 über AWS.
- Oberfläche als einfache HTML/JavaScript-Seite, ausgeliefert von FastAPI. Die in `CLAUDE.md` vorgesehene React-Oberfläche folgt in Phase 2; für die Demo wäre der Aufbau unverhältnismäßig.
- Nur synthetische Testbelege; der Server lauscht nur auf 127.0.0.1.

## Ampel in der Demo
- **Rot:** Summen widersprüchlich (Steuerlogik) oder bei einer Position fehlen Konto, Betrag oder Steuersatz
- **Gelb:** Konto passt nicht zum Steuersatz (Automatikkonten, Tabelle `skr03_konto_steuersatz.json`), 0 % ohne Reverse Charge, Vorschlag ohne KI, keine Positionen, E-Rechnung noch ohne Kontierung
- **Grün:** sonst

Die Sicherheit 0–1 je Vorschlag (`CLAUDE.md` Abschnitt 5) folgt in Phase 2.

## Folgen
- Keine KI-Kosten für Vorführungen und Proben.
- Eine Live-Abfrage bei IONOS oder AWS lässt sich später zuschalten, ohne die Oberfläche zu ändern (gleiche Schnittstelle).
