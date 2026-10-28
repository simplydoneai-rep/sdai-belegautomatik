# Entscheidung: An die KI geht nur pseudonymisierter Text, kein Belegbild

Datum: 28.10.2026 · Status: entschieden

## Kontext
Qwen3-VL 235B (STACKIT) und Claude können Bilder lesen. Ein Bild der Rechnung würde Layout-Informationen mitliefern und OCR-Fehler ausgleichen.

## Entscheidung
Im Machbarkeitstest und bis auf Weiteres erhält jeder Anbieter **nur Text**: PDF-Textlayer oder lokale Texterkennung (docTR), danach pseudonymisiert.

## Begründung
- `CLAUDE.md` Regel 2–4: Jeder KI-Aufruf geht durch die Pseudonymisierung. Ein Bild lässt sich nicht zuverlässig pseudonymisieren (Name, Anschrift, IBAN, Unterschrift stehen im Bild).
- `CLAUDE.md` Technik: „Keine Belegbilder an Dritte“.
- Die Messung zeigt, dass docTR auch schlechte Scans lesbar erkennt (`docs/machbarkeitstest-bericht.md`).

## Folgen
- Die Bildfähigkeit von Qwen3-VL bleibt ungenutzt; der Vergleich ist fair, weil alle Anbieter denselben Text bekommen.
- Wenn die Texterkennung bei echten Belegen nicht reicht, wäre ein geschwärztes Bild (Mandantenbereiche abgedeckt) eine mögliche spätere Stufe. Das braucht eine eigene Entscheidung.
