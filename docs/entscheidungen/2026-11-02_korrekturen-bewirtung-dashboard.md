# Entscheidung: Korrekturen je Position, Bewirtung, Dashboard, Kreditor-USt-IdNr.

Datum: 02.11.2026 · Status: entschieden (Vorgaben Paul Graß, Sprachnachricht sortiert in Punkte A–E)

## A. Dashboard
- Die vier Kacheln (Mandanten, mit offenen Belegen, ältester Monat, fertig gebucht) sind entfernt.
- Je Mandant zwei klare Spalten: **„Zuletzt bearbeitet“** (Belegmonat der zuletzt freigegebenen Rechnungen) und **„Offene Belege“** je Monat, z. B. „Nov. 2026: 4 Belege offen · 2 sicher · 2 prüfen“. Höchstens drei Monate, ältere zusammengefasst.

## B. Rechnungsprüfung
- Kurze Zeilen mit Haken und Wort („Rechnungsnummer vorhanden“, „fehlt“, „nicht nötig“). Paragraphen nur beim Überfahren (Tooltip).

## C. Positionen und Konten
- **Steuerschlüssel von Hand:** Der Chip (BU 9, Automatik) ist eine Auswahl mit allen belegten DATEV-Schlüsseln (`tabellen/datev_steuerschluessel.json`, Abschnitt `auswahl`), gruppiert nach Vorsteuer, i. g. Erwerb, § 13b, Ausgangsrechnungen, Altfälle 2020. „Vorschlag übernehmen“ setzt zurück. Die Steuerlogik prüft auch den manuellen Schlüssel (Regel 15): falscher Satz, falscher Steuerfall, Umsatzsteuerschlüssel auf Eingangsrechnung oder Schlüssel auf Automatikkonto werden gelb markiert und begründet.
  - Offen: Sonderschlüssel (z. B. Aufhebung der Automatik, Generalumkehr, dreistellige Schlüssel) sind öffentlich nicht belegt und werden vor Phase 4 aus der DATEV-Dokumentation ergänzt.
- **Steuersatz korrigieren:** je Position (19, 7, 0 % oder laut Beleg). Abweichung vom Beleg bleibt gelb markiert.
- **Aufteilung:** Position auf 2–4 Konten in Prozent vom Netto, Summe 100 %, Rundungsrest auf das letzte Konto. Jeder Teil bekommt seinen Steuerschlüssel; im Buchungssatz eigene Zeilen.
- **Bewirtung:** erkannt am Wort „Bewirtung“ auf dem Beleg oder an einem Gastronomiebetrieb als Lieferant. Vorschlag 4650 Bewirtungskosten mit automatischer Aufteilung **70 % 4650 / 30 % 4654** (§ 4 Abs. 5 Nr. 2 EStG), Vorsteuer **voll** abziehbar (§ 15 Abs. 1a Satz 2 UStG). Speisen 7 % (seit 01.01.2026 dauerhaft), Getränke 19 % – aus den Positionen der Rechnung. Ein Bewirtungsbeleg geht immer zur Prüfung: „Anlass und Teilnehmer bitte prüfen“ bzw. „fehlen“. Testrechnung F22 (Gasthaus Zur Linde).
- **Markierung im Beleg:** Beim Überfahren einer Position wird ihre Zeile in der Rechnung rechts hervorgehoben (Suche im PDF-Textlayer). Bei Scans, Fotos und E-Rechnungen noch nicht.

## D. Buchungssätze
- Im Buchungssatz stand die Vorsteuer bei Automatikkonten bereits (z. B. 3400 → 1576); jetzt mit Vermerk „aus Automatikkonto 3400“. In der DATEV-Zeile steht zusätzlich „VSt … → 1576“.
- **Beratung zur doppelten Ansicht:** Buchungssatz (Soll an Haben) und DATEV-Zeile zeigen denselben Vorgang. Für Sachbearbeiter ist der Buchungssatz die verständliche Sicht; die DATEV-Zeile ist das Exportformat (Konto = Kreditor, Gegenkonto mit Steuerschlüssel) und nur für Kontrolle und Rückfragen nützlich. **Entscheidung:** Buchungssatz bleibt sichtbar, die DATEV-Zeile ist zugeklappt („So geht der Beleg an DATEV“). Wird sie nicht gebraucht, kann sie später ganz in die Export-Vorschau (Phase 4) wandern.

## E. Kreditor und innergemeinschaftlicher Erwerb
- Der Kreditor speichert **USt-IdNr. und EU-Land**. Beim Anlegen kommen beide automatisch aus der Rechnung; im Abschnitt Kreditor änderbar, mit Prüfung (Format, Land passt zur USt-IdNr.). Weicht die USt-IdNr. auf einer späteren Rechnung ab, geht sie zur Prüfung; fehlt sie beim i. g. Erwerb, ebenso.
- In der DATEV-Zeile steht bei i. g. Erwerb und § 13b die USt-IdNr. des Lieferanten. Die genauen Felder im Buchungsstapel (EU-Land und USt-IdNr.) werden in Phase 4 aus der DATEV-Formatbeschreibung übernommen (CLAUDE.md: Felder nie raten).
- Beim Mandanten ist die **eigene USt-IdNr.** erfassbar (Mandantenformular); sie wird für die Pflichtangabe beim i. g. Erwerb (§ 14a Abs. 3 UStG) geprüft.
- Später sinnvoll: Bestätigungsabfrage der USt-IdNr. beim BZSt (qualifizierte Abfrage); übermittelt werden nur USt-IdNrn., keine Rechnungsdaten.
