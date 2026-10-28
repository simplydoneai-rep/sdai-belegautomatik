# Recherche: Recht, Hosting und KI

Stand: 28.10.2026 · Erstellt von Claude für Simply Done AI
Hinweis: Keine Rechtsberatung. Die Bewertungen sind fachliche Einschätzungen auf Basis der unten verlinkten Quellen.

## Ergebnisse auf einen Blick

| Nr. | Frage | Antwort | Bewertung |
|---|---|---|---|
| 1 | Unterschreibt Hetzner eine Verschwiegenheitsvereinbarung nach § 203 StGB? | Ja. Es gibt eine veröffentlichte Hetzner-Vereinbarung „zur beruflichen Verschwiegenheit“ vom 26.04.2021 mit einem Kunden, die auf bestehende Verträge mit Berufsgeheimnisträgern verweist. | Geringes Risiko. Über den Hetzner-Support anfordern. |
| 2 | Unterschreibt AWS (für Claude über Bedrock) eine Vereinbarung nach § 203 StGB? | Es gibt kein öffentliches Standard-Dokument. Ein individuelles Addendum ist über AWS-Partner (z. B. innFactory mit TD SYNNEX) erhältlich und wird direkt mit AWS geschlossen. | Machbar, aber Vorlauf einplanen. Im Addendum ausdrücklich festhalten, dass Amazon Bedrock abgedeckt ist. |
| 3 | Bleiben die Daten bei Claude über Bedrock in der EU? | Ja, mit dem EU-Inferenzprofil. Sonnet 5.5 läuft nicht direkt in Frankfurt, sondern über das Profil `eu.anthropic.claude-sonnet-5-5`, das nur EU-Regionen nutzt (Frankfurt, Stockholm, Mailand, Spanien, Irland, Paris). Bedrock gibt Prompts nicht an Anthropic weiter und speichert sie nicht. | Gut. Ausnahme: Claude Fable nicht verwenden, dort speichert AWS bis zu 30 Tage zur Missbrauchserkennung. |
| 4 | Ist die direkte Anthropic-API zulässig? | Nein, nicht für Mandantendaten. Sie verarbeitet in den USA und speichert Ein- und Ausgaben standardmäßig bis zu 30 Tage. Zero Data Retention gibt es nur per Sondervereinbarung für Enterprise-Kunden. | Bestätigt die Regel in der CLAUDE.md: nur Bedrock EU. |
| 5 | Braucht es eine AVV zwischen Steuerbüro und Mandant (Aussage cisbox)? | Nein. Seit der Änderung von § 11 StBerG zum Jahreswechsel 2020 handeln Steuerberater bei Steuerberatung und Buchführung weisungsfrei und sind Verantwortliche nach DSGVO, keine Auftragsverarbeiter. | Die cisbox-Aussage ist so nicht zutreffend. Nötig ist eine AVV und eine Vereinbarung nach § 62a StBerG zwischen Kanzlei und Dienstleister. |
| 6 | Reicht eine AVV für externe Dienstleister? | Nein. § 62a StBerG verlangt zusätzlich eine Verschwiegenheitsverpflichtung in Textform mit Hinweis auf § 203 StGB, Zugriff nur soweit erforderlich, Regelung zu Unterauftragnehmern. Bei Anbietern im Ausland muss das Schutzniveau vergleichbar sein. | Gilt für Simply Done AI gegenüber der Kanzlei und für Hetzner und AWS. |
| 7 | Was passiert bei Hetzner mit Daten nach Vertragsende, und sind sie verschlüsselt? | Daten werden nur während eines aktiven Vertrags gespeichert. Hetzner Object Storage hat **keine automatische Verschlüsselung** der gespeicherten Daten; Verschlüsselung beim Hochladen (SSE-C) muss man selbst einschalten. Standorte: Nürnberg, Falkenstein, Helsinki. Keine automatische Spiegelung zwischen Standorten. | Pflicht: Verschlüsselung mit eigenem Schlüssel, zweite Sicherung an anderem Standort, Exportplan bei Kündigung. In CLAUDE.md übernommen. |
| 8 | Kann Hetzner Belege technisch unveränderbar speichern? | Ja. Object Lock mit Compliance-Modus, der sich nicht vorzeitig beenden lässt. Muss beim Anlegen des Speichers aktiviert werden. | Erfüllt die technische Anforderung „unveränderbar“ der GoBD. |
| 9 | Wie lange müssen Rechnungen aufbewahrt werden? | 8 Jahre ab Ende des Ausstellungsjahres (§ 14b UStG). Bei E-Rechnungen muss die Original-XML unverändert erhalten bleiben; ein PDF ersetzt sie nicht. Bei ZUGFeRD das Original-PDF mit eingebetteter XML. | Bestätigt die CLAUDE.md. |
| 10 | Nutzt Anthropic unseren Code aus Claude Code zum Training? | Bei Team, Enterprise, API und Bedrock: nein. Bei Pro und Max: nur wenn die Einstellung „Daten zur Modellverbesserung“ eingeschaltet ist; dann 5 Jahre Speicherung, sonst 30 Tage. | Einstellung unter claude.ai/settings/data-privacy-controls ausschalten. Nie echte Mandantendaten in Claude Code. |
| 11 | Braucht man für den DATEV-Export eine Partnerschaft? | Für den CSV-Import im DATEV-Format: nein. Für die Online-Schnittstellen (Belegtransfer, Buchungsdatenservice) ist eine Registrierung im DATEV Developer Portal mit Freigabe durch DATEV nötig. Konditionen sind nicht öffentlich dokumentiert. | Für den Pilot reicht CSV. Vor Phase 4 Kontakt mit DATEV aufnehmen. |
| 12 | Was kostet der DATEV Automatisierungsservice Rechnungen? | Kein öffentlicher Preis. Freischaltung direkt in Kanzlei-Rechnungswesen unter „Bestand > Automatisierungsservices“. Voraussetzungen: SKR03/04, Unternehmen Online, OPOS-Buchführung, Datenarchivierung im DATEV-Rechenzentrum. | Preis ist in der DATEV-Preisliste der Kanzlei einsehbar. Wichtig für den Preisvergleich. |
| 13 | Was steckt hinter der „eigenen KI“ von cisbox, und sehen Mitarbeiter in Vietnam die Belege? | Nicht öffentlich dokumentiert. Bekannt ist nur: Entwicklung und Data Labeling in Ho-Chi-Minh-Stadt. | Bleibt offen. Laut Entscheidung vom 28.10.2026 keine Anfrage an cisbox. |

## Einschätzung von Claude

**Das Projekt ist rechtlich umsetzbar.** Kein Punkt spricht grundsätzlich dagegen. Der Aufwand liegt in Verträgen, nicht in der Technik.

**Empfohlene Konstellation:**
1. Server und Speicher bei Hetzner in Nürnberg oder Falkenstein, mit eigener Verschlüsselung und Object Lock.
2. KI über Amazon Bedrock mit EU-Inferenzprofil, ohne Fable, mit individuellem § 203-Addendum von AWS.
3. Vor jedem KI-Aufruf Pseudonymisierung. Das senkt das Risiko zusätzlich, weil AWS dann kaum Mandantengeheimnisse sieht.
4. Vertragskette: Kanzlei ↔ Simply Done AI (AVV + § 62a), Simply Done AI ↔ Hetzner (AVV + § 203), Simply Done AI ↔ AWS (DPA + § 203-Addendum).

**Rückfallebene**, falls AWS das Addendum nicht oder nur langsam liefert: ein lokales Open-Source-Modell auf einem Hetzner-GPU-Server. Die Schnittstelle `LLMProvider` in der Architektur ist genau dafür vorgesehen. Schwächere Qualität, dafür kein externer KI-Anbieter.

**Nicht empfohlen:**
- Microsoft Azure: Es gibt dort zwar ein Standard-§-203-Addendum, aber Modelle von Drittanbietern aus dem Marketplace fallen nicht darunter.
- Google Vertex AI: § 203-Addendum nur auf Anfrage unter Geheimhaltungsvereinbarung, ohne verlässlichen Zeitrahmen.

## Quellen

- [Hetzner: Vereinbarung zur beruflichen Verschwiegenheit (veröffentlicht von Dropscan)](https://www.dropscan.de/assets/main/downloads/dropscan-verschwiegenheitsverpflichtung-Hetzner.pdf)
- [Hetzner Docs: Object Lock Retention](https://docs.hetzner.com/de/storage/object-storage/howto-protect-objects/protect-object-lock-retention)
- [Hetzner Docs: Object Storage FAQ](https://docs.hetzner.com/de/storage/object-storage/faq/general)
- [innFactory: § 203 StGB in der Public Cloud (Azure, AWS, Google), Juli/August 2026](https://innfactory.de/en/blog/138-berufsgeheimnis-203-stgb-public-cloud/)
- [Pexon Consulting: Claude unter § 203 StGB nutzen, Leitfaden für Kanzleien 2026](https://pexon-consulting.de/blog/claude-stgb-203-berufsgeheimnis/)
- [AWS: Model Card Claude Sonnet 5.5 auf Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-5-5.html)
- [compound.law: Anthropic API, DSGVO und EU-Verarbeitung](https://compound.law/en-DE/tools/anthropic-api/)
- [Deubner: § 62a StBerG und KI in der Steuerkanzlei, Stand August 2026](https://www.deubner-steuern.de/themen/digitalisierung-steuerberatung/ki/62a-stberg.html)
- [CMS: Update § 203 StGB, Outsourcing bei Berufsgeheimnisträgern](https://cms.law/de/deu/legal-updates/update-203-stgb-rechtssicherheit-fuer-outsourcing-bei-berufsgeheimnistraegern)
- [Heuking: Steuerberater sind keine Auftragsverarbeiter (§ 11 StBerG)](https://www.heuking.de/de/news-events/newsletter-fachbeitraege/artikel/steuerberater-sind-keine-auftragsverarbeiter.html)
- [Claude Code Docs: Data usage](https://code.claude.com/docs/en/data-usage)
- [kostenlose-erechnung.de: Aufbewahrung von E-Rechnungen](https://kostenlose-erechnung.de/ratgeber/e-rechnung-archivierung-pflicht/)
- [DATEV: Automatisierungsservice Rechnungen](https://www.datev.de/web/de/steuerberatung/loesungen/rechnungswesen/buchfuehrung-erstellen/automatisierungsservices-rechnungswesen/datev-automatisierungsservice-rechnungen)
- [Apideck: DATEV API Integration Guide](https://www.apideck.com/blog/datev-api-integration-guide)
