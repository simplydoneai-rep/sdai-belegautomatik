# Verfahrensdokumentation (GoBD) – Entwurf

Stand: 04.11.2026 · Grundlage: Demo-Stand (Phase 2/3), noch nicht der Betrieb auf Hetzner (Phase 5) · CLAUDE.md Regel 14

Dieses Dokument beschreibt, wie Belege verarbeitet werden. Es wird bei jeder Änderung der Verarbeitung nachgeführt. Vor dem Pilot wird es um Betrieb, Rollen, Zwei-Faktor-Anmeldung, Datensicherung und Aufbewahrung ergänzt.

## 1. Belegfluss
`eingegangen → ausgelesen → vorgeschlagen → in Prüfung → freigegeben → exportiert`, daneben `entfernt`.

| Schritt | Was passiert | Wo protokolliert |
|---|---|---|
| Eingang | Upload oder Demo-Eingang; Original wird unverändert gespeichert (Betrieb: Object Storage mit Object Lock, CLAUDE.md Regel 9) | Protokoll „Eingang“ |
| Auslesen | E-Rechnung: XML; PDF: Textlayer; Scan/Foto: lokale OCR. Vor jedem KI-Aufruf Pseudonymisierung | – |
| Vorschlag | Mandanten-Regel, Historie, Branche, KI; danach prüft die Steuerlogik | Quelle und Sicherheit je Position |
| Prüfung | Sachbearbeiter ändert Konto, Steuerschlüssel, Aufteilung, Kreditor | jede Änderung mit altem und neuem Wert |
| Freigabe | nur von Hand (CLAUDE.md Regel 12); lernt Regeln je Mandant | Status, Lernregeln |
| Wieder öffnen | nimmt Freigabe und Gelerntes zurück; nicht mehr nach dem Export | Status |
| Entfernen | siehe 2. | Status mit Grund |
| Export | siehe 3. | Exportstapel mit Hash |

## 2. Belege entfernen
Ein Beleg, der nicht in die Buchhaltung dieses Mandanten gehört (anderer Mandant, Werbung oder Mahnung, doppelt eingegangen, privat, sonstiges), wird aus der Bearbeitung genommen.
- Nur offene Belege; freigegebene zuerst wieder öffnen, exportierte gar nicht.
- Ein Grund ist Pflicht. Person, Zeitpunkt und Grund stehen im Protokoll.
- **Das Original wird nicht gelöscht** (GoBD, CLAUDE.md Regel 9). Der Beleg bleibt unter „Entfernte Belege“ sichtbar und lässt sich wiederherstellen.

## 3. DATEV-Export
- Je Mandant und Monat (Belegdatum). Exportiert wird erst, wenn in diesem Monat kein Beleg mehr offen ist; entfernte Belege zählen nicht.
- Vor dem Export zeigt ein Fenster Mandant, Berater- und Mandantennummer, Sachbearbeiter, Monat, Anzahl, Summe und je Rechnung die Buchungszeilen.
- Die Datei (DATEV-Buchungsstapel, Format siehe `docs/datev/buchungsstapel.md`) wird vor der Ausgabe gegen ein Prüfskript geprüft (`app/export/datev.py: pruefe`).
- Jeder Export wird als Exportstapel festgehalten: Mandant, Monat, Belege, Dateiname, SHA-256 der Datei, Person, Zeitpunkt. Die Datei wird gespeichert und nie überschrieben; erneutes Herunterladen prüft den Hash.
- Exportierte Belege lassen sich nicht mehr wieder öffnen. Korrekturen erfolgen in DATEV per Storno und neuer Buchung.
- Festschreibung im Stapel: keine. Die Kanzlei schreibt in DATEV fest.

## 4. Protokoll
Append-only; im Betrieb Tabelle `audit_log` ohne UPDATE und DELETE für die Anwendung (CLAUDE.md Regel 10). Logs enthalten keine Belegtexte (Regel 7).

## Offen
- Betrieb: Speicherorte, Verschlüsselung, zweite Sicherung, Aufbewahrungsfristen, Rollen und Anmeldung.
- DATEV-Format: offizielle Formatbeschreibung und Testimport (Gate Phase 4).
