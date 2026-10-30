# Rechtsberatung – was gebraucht wird und warum

Stand: 31.10.2026 · Erstellt von Claude für Simply Done AI
Hinweis: Keine Rechtsberatung, sondern eine Übersicht, damit klar ist, **was** ein Anwalt prüfen oder entwerfen soll. Grundlage: `docs/recherche/2026-10-28_recht-hosting-ki.md`, `docs/recherche/2026-10-30_ionos-ai-model-hub.md`, `docs/projektplan.md` Abschnitt 4.

---

## Das Grundproblem in einem Satz

Die Kanzlei ist **Berufsgeheimnisträger**. Gibt sie Belege ihrer Mandanten an Simply Done AI weiter, macht sie sich nach **§ 203 StGB strafbar**, wenn nicht vorher bestimmte Verträge geschlossen sind. Das gilt auch für jeden, an den Simply Done AI die Daten weitergibt (Hetzner, IONOS, AWS). Die Rechtsberatung sorgt dafür, dass diese **Vertragskette lückenlos** ist.

```
Mandant ──▶ Kanzlei ──▶ Simply Done AI ──▶ Hetzner (Server, Speicher)
                                        └─▶ IONOS (KI)   [oder AWS]
```

Zwischen Mandant und Kanzlei braucht es **nichts Neues**: Steuerberater sind seit 2020 selbst Verantwortliche nach DSGVO (§ 11 StBerG).

---

## Was konkret gebraucht wird

| Nr. | Was | Warum | Wer macht es | Kosten (grobe Schätzung) | Wann |
|---|---|---|---|---|---|
| 1 | **Vertrag Kanzlei ↔ Simply Done AI**: Leistungsbeschreibung, Preis, Haftung, Kündigung, Datenexport bei Vertragsende | Grundlage der Zusammenarbeit; regelt vor allem, wer bei einer Fehlbuchung haftet | Anwalt (IT-Recht) entwirft, Kanzlei und Simply Done AI unterschreiben | in Nr. 2 enthalten | vor dem Pilot |
| 2 | **AVV + Verschwiegenheitsvereinbarung nach § 62a StBerG** als Anlage zum Vertrag | Ohne sie verletzt die Kanzlei ihre Schweigepflicht. Eine AVV allein reicht **nicht**: § 62a verlangt Verschwiegenheit in Textform, Hinweis auf § 203 StGB, Zugriff nur soweit nötig, Regeln für Unterauftragnehmer | Anwalt (IT- und Berufsrecht) | **1.500–4.000 €** zusammen mit Nr. 1 und 4 | vor dem Pilot |
| 3 | **Verträge mit den Unterauftragnehmern** (Hetzner, IONOS, ggf. AWS) | Simply Done AI muss die Schweigepflicht an alle weitergeben, die Daten sehen könnten | Simply Done AI fordert an; Anwalt prüft | Hetzner und IONOS: **kostenlos** (Standard-AVV; Hetzner § 203-Vereinbarung über Support, IONOS § 203 schon in der AVV). AWS: § 203-Addendum nur über Partner, Kosten offen | vor dem Pilot |
| 4 | **Prüfung der Pseudonymisierung**: Reicht sie, damit beim KI-Anbieter kein Geheimnis ankommt? | Sicherheitsnetz zu Nr. 3. Nach EuGH C-413/23 P und BStBK-FAQ ein gutes Argument, aber nicht abschließend geklärt | Anwalt | in Nr. 2 enthalten | vor dem Pilot |
| 5 | **Einwilligungserklärung für die Pilot-Mandanten** | Die BStBK-FAQ zu KI (27.10.2026) empfiehlt sie bei mandatsbezogener KI-Nutzung. Schützt die Kanzlei zusätzlich | Anwalt entwirft Vorlage, Kanzlei holt Unterschriften ein | in Nr. 2 enthalten | vor dem Pilot |
| 6 | **Datenschutz-Folgenabschätzung (DSFA)** nach Art. 35 DSGVO | Neue Technik (KI) mit Berufsgeheimnissen; sehr wahrscheinlich Pflicht | Datenschutzbeauftragter der Kanzlei, Simply Done AI liefert die technische Beschreibung | intern, oder externer Datenschutzberater **1.000–3.000 €** | vor dem Pilot |
| 7 | **Einordnung nach AI Act** | Buchungsvorschläge gehören nach unserer Einschätzung **nicht** zu den Hochrisiko-Anwendungen. Pflicht bleibt die KI-Kompetenz der Nutzer (Art. 4): kurze, dokumentierte Schulung | Simply Done AI, kurze Bestätigung durch Anwalt | gering, in Nr. 2 | vor dem Pilot |
| 8 | **Nebentätigkeit und Interessenkonflikt** (Paul Graß ist Angestellter der Kanzlei und Geschäftsführer des Anbieters) | Ohne schriftliche Genehmigung ist der Pilot angreifbar (Arbeitsrecht, Neutralität bei der Anbieterauswahl, faire Preise) | Paul Graß mit Markus Pfaar; bei Bedarf kurze Prüfung durch Arbeitsrechtler | **0–800 €** | vor dem Gespräch am 27.11.2026 vorbereiten |
| 9 | **Rechtsform von Simply Done AI** | Eine **GbR haftet unbeschränkt mit dem Privatvermögen** der Gesellschafter. Eine falsche Buchung oder ein Datenleck könnte bei einer Kanzlei mit über 1.000 Mandanten teuer werden. Eine GmbH oder UG begrenzt die Haftung. Möglicherweise hat auch STACKIT wegen der Rechtsform abgelehnt (unbestätigt) | Steuerberater/Anwalt, Notar | GmbH: Notar und Handelsregister ca. **800–1.500 €** plus Stammkapital 25.000 € (12.500 € sofort einzuzahlen); UG ab 1 € Stammkapital | spätestens vor dem Pilot |
| 10 | **Versicherung**: IT-/Cyber-Haftpflicht und Vermögensschadenhaftpflicht | Deckt Schäden durch Softwarefehler oder Datenpannen; Kanzleien fragen danach | Versicherungsmakler | **1.000–3.000 € pro Jahr** | vor dem Pilot |
| 11 | **AGB und Standardverträge für weitere Kanzleien** | Erst nötig, wenn an andere Kanzleien verkauft wird | Anwalt | **2.000–5.000 €** | nach Gate 2 (Sep 2027) |

**Summe vor dem Pilot (einmalig):** ca. **3.500–10.000 €** für Anwalt, Datenschutz und erste Versicherungsprämie, **ohne** Kosten einer GmbH-Gründung.

---

## Was der Anwalt konkret bekommen sollte

Damit die Beratung schnell und günstig wird, ein Paket vorbereiten:
1. Kurzbeschreibung des Produkts (1 Seite: Beleg rein, Pseudonymisierung, KI-Vorschlag, Freigabe durch Sachbearbeiter, DATEV-Export)
2. Liste der Unterauftragnehmer mit Standort und Vertragsstand (Hetzner, IONOS, AWS)
3. Beschreibung der Pseudonymisierung und Messergebnis (0 von 364 sensiblen Werten bei der KI, `docs/machbarkeitstest-bericht.md`)
4. Die IONOS-AVV (mit § 203-Klausel) und die Hetzner-Verschwiegenheitsvereinbarung
5. Konkrete Fragen:
   - Genügt die Standard-AVV von IONOS mit § 203-Klausel für eine Steuerkanzlei, oder braucht es eine eigene Vereinbarung?
   - Reicht die Pseudonymisierung als zusätzliche Absicherung (EuGH C-413/23 P)?
   - Wie wird die Haftung für fehlerhafte Buchungsvorschläge sinnvoll begrenzt, wenn jeder Vorschlag von einem Sachbearbeiter freigegeben wird?
   - Ist eine Einwilligung der Mandanten erforderlich oder nur empfohlen?

Ein Anwalt mit Schwerpunkt **IT-Recht und Berufsrecht der Steuerberater** ist ideal. Die Steuerberaterkammer oder der DStV können Kontakte nennen.

---

## Reihenfolge

1. **Jetzt:** Interessenkonflikt mit Markus Pfaar ansprechen (Nr. 8), Rechtsform klären (Nr. 9)
2. **Nach grünem Licht von Markus Pfaar:** Anwalt beauftragen (Nr. 1–5, 7), Verträge mit Hetzner und IONOS abschließen (Nr. 3), Versicherung (Nr. 10)
3. **Parallel zur Entwicklung:** DSFA mit dem Datenschutzbeauftragten der Kanzlei (Nr. 6)
4. **Später:** AGB für den Vertrieb (Nr. 11)
