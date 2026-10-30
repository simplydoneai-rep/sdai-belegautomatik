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
| 10 | **Versicherung**: IT-/Cyber-Haftpflicht und Vermögensschadenhaftpflicht | Deckt Schäden durch Softwarefehler oder Datenpannen; Kanzleien fragen danach | Versicherungsmakler | **abgeschlossen** seit 01.08.2026: IT-Haftpflicht 125.000 €, Cyber 100.000 € je Baustein, zusammen ca. 596 € pro Jahr. Vor dem Pilot Deckung für unsere Tätigkeit und Höhe der Summen klären (Abschnitt „Versicherungen“) | vor dem Pilot klären |
| 11 | **AGB und Standardverträge für weitere Kanzleien** | Erst nötig, wenn an andere Kanzleien verkauft wird | Anwalt | **2.000–5.000 €** | nach Gate 2 (Sep 2027) |

**Summe vor dem Pilot (einmalig):** ca. **2.500–7.800 €** für Anwalt und Datenschutz, **ohne** Kosten einer GmbH-Gründung. Die Versicherungen bestehen bereits.

---

## Versicherungen (Stand 31.10.2026)

Beide bei Markel Insurance SE, betreut über den Makler SDV (Augsburg), Versicherungsnehmer SimplyDoneAI GbR, Laufzeit 01.08.2026–01.08.2027.

| | IT-Haftpflicht (Vermögensschaden) | Cyber-Versicherung |
|---|---|---|
| Deckt | Schäden bei Kunden durch Fehler in unserer Leistung (z. B. falscher Buchungsvorschlag führt zu Steuernachzahlung, Zinsen, Beraterkosten) | Hackerangriff, Datenleck, Erpressung, Ausfall; Ansprüche Dritter nach einem Datenvorfall |
| Summe | 125.000 € je Schaden, höchstens 375.000 € im Jahr | 100.000 € je Baustein, höchstens 200.000 € im Jahr |
| Selbstbehalt | 250 € | 1.000 € |
| Einstufung | Umsatz bis 50.000 €, „Tätigkeiten der IT- und Telekommunikationsbranche gemäß Ihren Angaben“ | Umsatz bis 100.000 € |
| Beitrag | 182,07 € im Jahr (15 % Startup-Nachlass für 2 Jahre) | 413,49 € im Jahr |

**Einschätzung (keine Versicherungsberatung):** Für die Entwicklung und einen Pilot mit 10 Mandanten ist das eine gute Grundlage. Vor dem Pilot mit dem Makler klären:

1. **Ist unsere Tätigkeit gedeckt?** Die IT-Haftpflicht deckt Tätigkeiten „gemäß Ihren Angaben“. Zu prüfen ist, ob dort Betrieb einer Software (SaaS) mit KI für Steuerkanzleien, Verarbeitung von Daten von Berufsgeheimnisträgern und **Buchungsvorschläge** angegeben sind. Manche IT-Policen schließen Tätigkeiten aus, die der Steuerberatung oder Buchhaltung nahekommen.
2. **Serienschaden:** Ein Fehler in der Kontierungslogik trifft viele Mandanten gleichzeitig. Häufig gilt das als **ein** Schaden, dann stehen insgesamt nur 125.000 € zur Verfügung. Für den Betrieb mit über 1.000 Mandanten ist eine höhere Summe zu prüfen (z. B. 500.000–1.000.000 €).
3. **Umsatzgrenzen:** Bei 0,35 € je Beleg und 50.000 Belegen läge der Umsatz bei ca. 210.000 € im Jahr, also über beiden Einstufungen. Steigenden Umsatz rechtzeitig melden.
4. **Versicherte Personen:** In der Cyber-Police ist Tim Ludwig als Mitversicherter genannt, in der IT-Haftpflicht nicht. Klären, ob alle Gesellschafter der GbR in beiden Policen geschützt sind.
5. **Rechtsformwechsel:** Wird aus der GbR eine GmbH oder UG, müssen beide Policen umgeschrieben werden.
6. **Haftungsgrenze im Vertrag mit der Kanzlei** (Nr. 1) an die Versicherungssumme anpassen, damit keine Lücke zwischen vertraglicher Haftung und Versicherungsschutz entsteht.

Hinweis zur GbR (Nr. 9): Die Versicherungen mindern das Risiko der persönlichen Haftung deutlich, beseitigen es aber nicht: über der Deckungssumme, bei Ausschlüssen oder bei Vorsatz haften die Gesellschafter weiterhin privat.

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
