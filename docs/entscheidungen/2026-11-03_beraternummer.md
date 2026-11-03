# Entscheidung: Beraternummer für Kanzlei und Mandant

Stand: 03.11.2026 · Anlass: Paul Graß – Beraternummer für den späteren DATEV-Export, auch Kanzleien mit mehreren Beraternummern bedenken

## Hintergrund
Der DATEV-Buchungsstapel trägt im Kopfsatz Beraternummer und Mandantennummer (CLAUDE.md Abschnitt 7). In DATEV ist jeder Mandant unter genau einer Beraternummer angelegt; die Mandantennummer ist nur innerhalb dieser Beraternummer eindeutig. Mehrere Beraternummern in einer Kanzlei kommen vor, z. B. je Berufsträger, bei Sozietäten oder nach Übernahme einer Kanzlei.

## Entscheidung
1. **Die Kanzlei führt eine Liste ihrer Beraternummern** mit Bezeichnung; eine davon ist **Standard** für neue Mandanten. Pflege nur durch die Kanzleileitung (Übersicht → „Beraternummern“). Jede Änderung steht im Protokoll.
2. **Jeder Mandant speichert seine Beraternummer** (Auswahl im Mandanten-Formular, vorbelegt mit dem Standard). Ein späterer Wechsel des Standards ändert bestehende Mandanten nicht.
3. **Mandantennummern sind je Beraternummer eindeutig**, nicht kanzleiweit. Die vorgeschlagene nächste Nummer richtet sich nach der gewählten Beraternummer.
4. Entfernen geht nur für Beraternummern ohne Mandanten und nicht für den Standard.
5. Für den Export liefert `kanzlei.beraternummer(mandant_id)` die Nummer (Phase 4).
6. Anzeige: in der Belegverarbeitung „Beraternummer / Mandantennummer“ (wie in DATEV üblich), in der Übersicht unter der Mandantennummer, sobald die Kanzlei mehr als eine Beraternummer hat.
7. Ältere Stammdaten ohne Beraternummer bekommen beim Laden die Start-Beraternummer (Demo: erfundene 29098 „Hauptkanzlei“).

## Wertebereich – noch zu bestätigen
Geprüft wird 1001 bis 9999999 (höchstens 7 Stellen). Diese Angabe stammt bisher aus Sekundärquellen, die sich auf die DATEV-Formatbeschreibung berufen; die Seite im DATEV Developer Portal war nicht abrufbar. **Vor Phase 4 gegen die offizielle Formatbeschreibung prüfen** (`docs/datev/`, CLAUDE.md: Felder nie raten). Der Wert steht an einer Stelle: `kanzlei.BERATERNUMMER`.

Quellen:
- [DATEV Buchungsstapel erzeugen mit R (investmentgarage.de)](https://investmentgarage.de/datev-buchungsstapel-erzeugen-mit-r/) – Feld 11 Beraternummer 1001–9999999
- [DATEV-Community: DATEV Format Schnittstellenbeschreibung](https://www.datev-community.de/t5/Betriebliches-Rechnungswesen/DATEV-Format-Schnittstellenbeschreibung/td-p/24100) – Verweis auf die Satzbeschreibung im Developer Portal
- [DATEV Developer Portal: DTVF](https://developer.datev.de/datev/platform/en/dtvf) – offizielle Beschreibung (Inhalt nicht abrufbar)
