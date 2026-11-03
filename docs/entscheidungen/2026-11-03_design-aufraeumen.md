# Entscheidung: Design der Demo aufräumen (weniger „KI-Look“)

Stand: 03.11.2026 · Anlass: Rückmeldung Paul Graß, die Oberfläche wirke „KI-sloppig“

## Befund
- Das Stylesheet ist über viele Runden gewachsen: 45 Farbwerte, 21 Schriftgrößen, 9 Eckenradien.
- Viele Farbsignale gleichzeitig: farbige Symbol-Kästchen vor jeder Abschnittsüberschrift, Farbverläufe (Logo, Avatare, Kopfkarte, Sammelfreigabe), farbige Marken für Vorsteuer, Umsatzsteuer und Kreditor, eingefärbte Kontofelder **und** Ampelpunkt.
- Doppelte Aussagen: „Neuer Lieferant“ oben in den Prüfhinweisen und noch einmal als gelbe Zeile im Kreditor; „vorhanden“ hinter jedem grünen Haken; „✓ Summen stimmen“ auch dann, wenn alles stimmt.
- Erklärsätze, die ein Sachbearbeiter nicht braucht (Nummernkreis, „so bucht DATEV den Beleg“, Inland-Hinweis zur Vorsteuer, „Sonst bleibt es bei …“).

## Entscheidung
1. **Design-Tokens** oben in `style.css`: Flächen und Text (je 3 Stufen), ein Akzent (Blau), drei Statusfarben (ok, warn, fehler) mit je Fläche und Text. Schriftgrößen auf 5 Stufen (11 / 12,5 / 13,5 / 15 / 17 px, dazu Überschriften und Betrag), Radien auf 3 Stufen (6 / 10 / 14 px) plus Pille.
2. **Farbe nur für Status.** Ampel grün/gelb/rot bleibt (CLAUDE.md Abschnitt 5). Alles andere neutral: keine Symbol-Kästchen, keine Verläufe, Steuerschlüssel und Buchungsmarken grau.
3. **Jede Aussage einmal.** Prüfhinweise stehen oben gesammelt; der Abschnitt Kreditor zeigt nur das Formular. Grüne Haken ohne Zusatzwort, „Summen stimmen“ nur im Fehlerfall.
4. **Erklärtexte kürzen oder in den Tooltip.** Fachliche Hinweise bleiben, wo sie eine Entscheidung betreffen (§ 13b, i. g. Erwerb, ausländische Steuer, Fremdwährung, fehlende Pflichtangaben).
5. Funktionen, Daten und Schnittstellen bleiben unverändert; nur Stylesheet, Markup und Texte.

## Nicht entschieden
Ein eigener Styleguide durch einen Designer (Farben der Marke Simply Done AI, Schrift, Logo) ersetzt später die Tokens. Die Tokens sind so angelegt, dass das an einer Stelle geschieht.

## Nachtrag 03.11.2026: Markenfarben
Vorgabe Paul Graß, abgeglichen mit simplydone-ai.de: Primary `#FF7601`, Black `#0A0A0A`, White `#FFFFFF`, Grey `#888888`; Schrift Poppins, Knöpfe als Pillen.
- **Akzent = Primary.** Orange als Fläche nur für Aktionen (Freigeben, Anlegen, ＋ Mandant), Fokus und Hervorhebung im Beleg. Orange als Schrift (Links) in der dunkleren Stufe `#B85000`, weil `#FF7601` auf Weiß nur etwa 2,9 : 1 Kontrast hat (WCAG verlangt 4,5 : 1 für Fließtext).
- **Ausgewählte Rechnung schwarz** mit weißer Schrift, wie der schwarze Knopf der Website.
- **Ampel „unsicher“ ist jetzt Gelb** (`#FFCC00`) statt Orange. Sonst wäre ein Warnhinweis nicht vom Markenakzent zu unterscheiden. Grün und Rot bleiben.
- Grautöne neutral statt bläulich (iOS); Nebentext `#555555`, Beschriftungen Grey `#888888`.
- Kürzel der Sachbearbeiter grau, damit Orange nur für Aktionen steht.
- **Schrift Poppins** steht vorn in der Schriftliste und greift nur, wenn sie installiert ist; sonst Segoe UI. Für den Betrieb Poppins selbst ausliefern, nicht über Google Fonts einbinden: Das Nachladen von Google-Servern überträgt die IP-Adresse an Google (LG München I, Urteil vom 20.01.2022, Az. 3 O 17493/20).
