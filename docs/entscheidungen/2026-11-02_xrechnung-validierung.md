# Entscheidung: Validierung von E-Rechnungen mit den offiziellen KoSIT-Prüfregeln

Datum: 02.11.2026 · Status: entschieden (Freigabe Paul Graß, auch für die beiden Downloads)

## Ausgangslage
E-Rechnungen (XRechnung, UBL und CII) wurden bisher strukturiert gelesen und rechnerisch sowie auf Pflichtangaben geprüft, aber nicht gegen die offiziellen Prüfregeln. Seit 2025 ist die E-Rechnung im B2B-Bereich Pflicht beim Empfang; eine Rechnung, die die Regeln der EN 16931 verletzt, ist keine ordnungsgemäße E-Rechnung.

## Entscheidung
- **Regelwerk:** offizielle Validator-Konfiguration der KoSIT für XRechnung 3.0.2, Release v2026-08-31 (`xrechnung-3.0.2-validator-configuration-2026-08-31.zip`, 0,5 MB, Apache-2.0, SHA-256 `2530cd10…21a8`). Enthält XML-Schemas (UBL 2.1, CII D16B), die EN-16931-Schematron-Regeln 1.3.16 und die XRechnung-Regeln 2.6.0, als XSLT kompiliert, sowie `scenarios.xml`.
- **Ausführung ohne Java:** Python mit `lxml` (Schema) und `saxonche` 13.1.1 (Saxon HE von Saxonica, XSLT 3.0, 37 MB) für die Schematron-Regeln. Ablauf wie im KoSIT-Validator: Szenario per `match`, Schema, Schematron, Auswertung der SVRL (`flag` fatal/error = Fehler, sonst Warnung). Code: `backend/app/erechnung/validierung.py`.
- Alternative KoSIT-Validator (Java, `validator-1.6.3-standalone.jar`) wurde verworfen, weil dafür eine Java-Laufzeit installiert werden müsste. Für den Betrieb (Phase 5) bleibt er eine Option, z. B. im Daemon-Modus in einem eigenen Container; die Regeln sind dieselben.
- **Einrichtung:** `backend/scripts/kosit_einrichten.py` lädt die feste Version, prüft die Prüfsumme und entpackt nach `tools/kosit/` (nicht im Repository). Ohne Einrichtung zeigt die Oberfläche „nicht eingerichtet“, die Tests werden übersprungen.
- **Datenschutz:** läuft vollständig lokal, keine Rechnungsdaten an Dritte.

## Wirkung in der Belegverarbeitung
- Abschnitt „Rechnungsprüfung“ zeigt bei E-Rechnungen oben das Ergebnis: „Gültige E-Rechnung“ oder „E-Rechnung ungültig“ mit Regelnummer (z. B. BR-CO-15), Text der Regel und Warnungen.
- Ungültige E-Rechnungen gehen zur Prüfung („E-Rechnung ungültig: n Fehler nach den XRechnung-Prüfregeln“) mit dem Hinweis, beim Lieferanten eine korrigierte Rechnung anzufordern.
- Kennzeichnung ohne passendes Szenario (z. B. XRechnung 2.x oder ZUGFeRD-Profil ohne XRechnung-Kennung) gilt als ungültig für XRechnung 3.0.

## Ergebnis mit den Testdaten
- Alle 64 KoSIT-Testrechnungen (UBL und CII) gültig, einige mit Warnung BR-DE-TMP-32.
- Neue Testrechnung F21 (aus KoSIT 01.01a, Käuferreferenz entfernt und Bruttobetrag verändert): ungültig mit BR-CO-15 und BR-DE-15.

## Datenschutz (DSGVO) der Prüfwerkzeuge
Geprüft am 02.11.2026:
- **Keine Übermittlung an Dritte:** saxonche (Saxon HE, Open-Source-Ausgabe von Saxonica, Betrieb mit `license=False`, ohne Lizenzprüfung), lxml und die KoSIT-Regeln laufen im eigenen Prozess. Kein Auftragsverarbeiter, keine AVV nötig.
- **Regeln laden nichts nach:** In den XSLT-Dateien gibt es nur `document(...)` auf die geprüfte Rechnung selbst; die enthaltenen Internetadressen sind ausschließlich Namensraum-Kennungen. Die XML-Schemas liegen lokal.
- **Schutz vor manipulierten Dateien (Art. 32 DSGVO):** XML wird ohne externe Entitäten und ohne Netzzugriff gelesen; Dateien mit DTD/ENTITY werden vor der Prüfung abgewiesen (Schutz vor XXE).
- **Logs:** nur Status und Laufzeiten, keine Rechnungsinhalte (CLAUDE.md Regel 7).
- Netzverkehr gab es nur bei der einmaligen Einrichtung (Download von GitHub und PyPI, ohne Rechnungsdaten).
- Lizenzen: KoSIT-Konfiguration Apache-2.0, lxml BSD, Saxon HE Open Source (Mozilla Public License 2.0 laut Saxonica). Vor dem Verkauf in der Lizenzprüfung aller Bibliotheken mit abhaken.

## Verständliche Meldungen
Sachbearbeiter sehen nicht die englischen Regeltexte, sondern kurze deutsche Sätze (`backend/app/erechnung/tabellen/xrechnung_klartext.json`): feste Übersetzung für die häufigen Regeln (z. B. BR-CO-15 „Rechenfehler: Der Bruttobetrag ist nicht Netto + Umsatzsteuer.“, BR-DE-15 „Die Käuferreferenz (Leitweg-ID) fehlt.“), Regelfamilien (Nachkommastellen, Steuerkategorien, Codelisten, technischer Aufbau) und für alle übrigen eine Ableitung aus den genannten Feldern (BT-Nummern → deutsche Feldnamen). Gleiche Sätze erscheinen nur einmal, Hinweise getrennt von Fehlern, darunter „Was tun?“. Regelnummer, Originaltext und Fundstelle stehen aufklappbar unter „Technische Details für Rückfragen beim Lieferanten“.

## Später
- ZUGFeRD/Factur-X: eingebettete XML aus dem PDF lesen und je nach Profil prüfen (die XRechnung-Konfiguration deckt nur das XRechnung-Profil ab).
- Neue KoSIT-Versionen: URL und Prüfsumme im Einrichtungsskript anpassen.
