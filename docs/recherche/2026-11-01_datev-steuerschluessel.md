# Recherche: DATEV-Steuerschlüssel für Eingangsrechnungen

Datum: 01.11.2026 · Anlass: Vorgabe Paul Graß, Steuerschlüssel in der Buchungslogik nach DATEV-Logik

## Ergebnis

| Fall | Steuersatz | BU-Schlüssel | Bemerkung |
|---|---|---|---|
| Inland, Vorsteuer | 19 % | **9** | |
| Inland, Vorsteuer | 7 % | **8** | Nicht 7: Schlüssel 7 ist Vorsteuer 16 % (Zeitraum 2020/2021) |
| Innergemeinschaftlicher Erwerb (§ 1a UStG) | 19 % | **19** | Gilt für den Erwerb (Einkauf), nicht für die i. g. Lieferung (Verkauf) |
| Innergemeinschaftlicher Erwerb | 7 % | **18** | |
| § 13b UStG (z. B. Leistung eines ausländischen Unternehmers) | 19 % | **94** | |
| § 13b UStG | 7 % | **91** | |
| Automatikkonto (Kennzeichen AV, z. B. 3400, 3300, 3120, 3425) | aus dem Konto | **kein Schlüssel** | DATEV rechnet die Steuer aus dem Konto |
| Ohne Vorsteuer (z. B. Versicherung, 0 %) | 0 % | kein Schlüssel | |

Hinweise:
- In DATEV Kanzlei-Rechnungswesen gibt es zusätzlich dreistellige Schlüssel (z. B. 231 i. g. Lieferung), die beim Datenaustausch zugeordnet werden. Für Eingangsrechnungen reichen die zweistelligen Schlüssel oben.
- Die Steuer bei Automatikkonten ergibt sich aus der DATEV-Kontenbezeichnung im SKR 03 2026 („Wareneingang 19 % Vorsteuer“, „Bauleistungen … 19 % Vorsteuer und 19 % Umsatzsteuer“). Das Programm liest Satz und Fall aus der Bezeichnung (Kennzeichen AV).

## Quellen
- Lexware Support, FAQ 000002619 „DATEV-Steuerschlüssel hinterlegen“ (Tabelle, gültig ab 01.01.2021): https://www.lexware.de/support/faq/faq-beitrag/000002619-datev-steuerschluessel-hinterlegen/
- DATEV-Community, „Steuerschlüssel DATEV 19 oder 94 bei Reverse Charge“ (19 = i. g. Erwerb § 1a UStG, 94 = § 13b UStG): https://www.datev-community.de/t5/Betriebliches-Rechnungswesen/Steuerschl%C3%BCssel-DATEV-19-oder-94-bei-reverse-charge/m-p/154820
- DATEV-Kontenrahmen SKR 03 2026, Art.-Nr. 11174 (Kennzeichen AV)

## Offen
Vor dem DATEV-Export (Phase 4) die Liste gegen die offizielle DATEV-Dokumentation der Steuerschlüssel aus dem Developer Portal prüfen und dort ablegen (`docs/datev/`), siehe CLAUDE.md Abschnitt 7 „Felder nie raten“. Eine offizielle DATEV-Liste war in der Recherche nicht frei zugänglich.
