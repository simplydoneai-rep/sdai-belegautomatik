# Entscheidung: Regelbasierter Platzhalter-Anbieter ohne KI

Datum: 28.10.2026 · Status: entschieden

## Entscheidung
`app/llm/placeholder.py` implementiert die `LLMProvider`-Schnittstelle ohne KI. Er liest den pseudonymisierten Text mit Regeln aus und läuft immer mit, auch wenn Zugangsdaten vorhanden sind.

## Begründung
- Auftrag: „Solange .env leer ist, teste alles mit einem Platzhalter-Anbieter.“
- Er nimmt wie jeder Anbieter nur `PseudonymizedPayload` an, prüft also dieselbe Strecke.
- Er liefert eine Untergrenze „ohne KI“ zum Vergleich.

## Grenzen
Er ist auf die Vorlage der synthetischen Belege abgestimmt; seine Trefferquote sagt nichts über fremde Layouts. Im Bericht ausdrücklich so gekennzeichnet. Er wird nicht produktiv eingesetzt.
