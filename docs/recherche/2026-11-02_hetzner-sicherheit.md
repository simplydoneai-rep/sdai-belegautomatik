# Recherche: Wie sicher ist der Betrieb bei Hetzner?

Stand: 02.11.2026 · Anlass: Frage Paul Graß zur Cloud-Anwendung · Keine Rechtsberatung

## Was Hetzner liefert
| Punkt | Stand | Quelle |
|---|---|---|
| Unternehmen | Hetzner Online GmbH, Gunzenhausen; kein US-Mutterkonzern, kein US CLOUD Act | [Hetzner Informationssicherheit](https://docs.hetzner.com/de/general/company-and-policy/information-security-at-hetzner/) |
| ISO/IEC 27001:2022 | zertifiziert, Zertifikat als PDF abrufbar; laut Hetzner keine Ausschlüsse bei den Anhang-A-Maßnahmen | ebd. |
| BSI C5 | Testat Typ 2 für die Cloud-Dienste (Wirksamkeit über einen Zeitraum geprüft) | ebd. |
| KRITIS | vom BSI als Betreiber kritischer Dienstleistungen eingestuft, Nachweis nach § 8a BSIG | ebd. |
| AVV (Art. 28 DSGVO) | im Kundenkonto abschließbar; TOMs in Anlage 2; Prüfberichte erst nach Abschluss der AVV | ebd. |
| § 203 StGB | Vereinbarung zur beruflichen Verschwiegenheit erhältlich (über den Support) | `docs/recherche/2026-10-28_recht-hosting-ki.md` |
| Standorte | Nürnberg, Falkenstein (Deutschland), Helsinki; keine automatische Spiegelung zwischen Standorten | ebd. |
| Object Storage | Object Lock (Compliance-Modus) für GoBD; **keine automatische Verschlüsselung** – eigene Verschlüsselung nötig | ebd. |

Offen: Geltungsbereich und Gültigkeit der Zertifikate stehen nur in den PDFs; vor dem Pilot herunterladen und in die Verfahrensdokumentation aufnehmen. DDoS-Schutz bei Hetzner direkt erfragen.

## Was wir selbst absichern müssen (geteilte Verantwortung)
Hetzner sichert Rechenzentrum, Strom, Netz und Hardware. Für Server, Daten und Anwendung sind wir zuständig:
1. Verschlüsselung jedes Belegs mit eigenem Schlüssel (SSE-C oder vor dem Hochladen), Schlüssel getrennt vom Speicher (`CLAUDE.md` Regel 9a).
2. Zweite Sicherung an einem anderen Standort, täglich, verschlüsselt; Exportskript jederzeit lauffähig (Regel 9b).
3. Server härten: nur nötige Ports (Hetzner-Firewall), SSH nur mit Schlüssel, automatische Sicherheitsupdates, Datenbank nicht öffentlich erreichbar.
4. Anmeldung mit Rollen und Zwei-Faktor, Sachbearbeiter sehen nur zugeordnete Mandanten (Phase 5).
5. Audit-Log append-only, Logs ohne Belegtexte (Regeln 7, 10).
6. TLS für alle Verbindungen, Überwachung und Alarm bei Ausfall.
7. Notfallplan: Wiederherstellung aus der zweiten Sicherung regelmäßig üben.
