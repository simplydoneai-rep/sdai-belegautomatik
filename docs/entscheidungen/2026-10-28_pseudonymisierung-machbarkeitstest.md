# Entscheidung: Pseudonymisierung im Machbarkeitstest ohne Presidio

Datum: 28.10.2026 · Status: entschieden, gilt bis Phase 1

## Kontext
`CLAUDE.md` sieht Microsoft Presidio mit deutschem spaCy-Modell plus eigene Regeln vor. Presidio und spaCy sind in der Entwicklungsumgebung noch nicht installiert.

## Entscheidung
Im Machbarkeitstest arbeitet die Pseudonymisierung mit:
1. **Stammdaten des Mandanten** (Name, Anschrift, Ansprechpartner, eigene USt-IdNr.), exakt und **unscharf** (rapidfuzz, Schwelle 85), damit OCR-Lesefehler erkannt werden.
2. **Regeln** für IBAN, BIC, E-Mail, Telefon/Fax, Steuernummer, Kontonummer und Personennamen nach Hinweiswörtern (Herr/Frau, Ansprechpartner, Geschäftsführer, Inhaber u. a., OCR-tolerant).

Presidio mit deutschem NER-Modell kommt in **Phase 1** dazu, für Personennamen ohne Hinweiswort.

## Begründung
- Die Stammdaten des Mandanten sind bekannt; sie gezielt zu ersetzen ist zuverlässiger als eine allgemeine Namenserkennung.
- Messung: 0 von 248 sensiblen Werten im KI-Text (`docs/machbarkeitstest-bericht.md`).
- Der Test bleibt schlank; Presidio bringt ein großes Sprachmodell mit, das für die Messung der KI-Anbieter nichts ändert.

## Folgen
- Restrisiko: Namen natürlicher Personen ohne Hinweiswort. Vor echten Mandantendaten (Phase 5) ist Presidio Pflicht.
- Die Leckprüfung je Beleg (`app/qualitaet/vergleich.py: leaks`) bleibt dauerhaft Teil der Qualitätsmessung.
