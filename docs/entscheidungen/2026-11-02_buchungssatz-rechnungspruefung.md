# Entscheidung: Vollständiger Buchungssatz, Rechnungsprüfung nach § 14 UStG, ausländische Umsatzsteuer

Datum: 02.11.2026 · Status: entschieden (Vorgaben Paul Graß)

## 1. Buchungssätze
Der Abschnitt „Buchungssätze“ zeigt zwei Sichten (`backend/app/demo/ansicht.py`, `_buchungssaetze`):

1. **Buchungssatz** (so bucht DATEV den Beleg): Aufwand und Vorsteuer im Soll, „an“ Kreditor im Haben; bei § 13b und i. g. Erwerb zusätzlich die Umsatzsteuer im Haben. Summe Soll = Summe Haben wird geprüft.
   - Inland: z. B. Soll 4250 680,00 / Soll 1576 129,20 an Haben 70003 809,20
   - § 13b: Soll 4964 216,00 / Soll 1577 41,04 an Haben 1787 41,04 / Haben Kreditor 216,00
   - i. g. Erwerb: Vorsteuer 1574 / Umsatzsteuer 1774
   - Gutschrift: Seiten getauscht.
2. **DATEV-Buchungsstapel**: **Konto = Kreditor, Gegenkonto = Sachkonto** (Vorgabe; so bucht man Eingangsrechnungen in DATEV üblicherweise). Das Soll/Haben-Kennzeichen bezieht sich auf das Konto: Rechnung „H“ (Kreditor im Haben), Gutschrift „S“. Der Steuerschlüssel gehört zum Gegenkonto (Sachkonto).

Steuerkonten aus dem SKR03 2026 als Tabelle `tabellen/skr03_steuerkonten.json` (1576/1571 Vorsteuer, 1577/1578 und 1787/1785 § 13b, 1574/1572 und 1774/1772 i. g. Erwerb). Offen vor Phase 4: Abgleich mit den Steuerschlüssel-Einstellungen in DATEV Kanzlei-Rechnungswesen.

## 2. Rechnungsprüfung (Pflichtangaben)
Jede Rechnung, nicht nur E-Rechnungen, wird lokal und ohne KI geprüft (`backend/app/kontierung/pflichtangaben.py`). Rechtsgrundlagen (gesetze-im-internet.de, abgerufen 02.11.2026):

| Punkt | Grundlage |
|---|---|
| Name und Anschrift von Lieferant und Mandant | § 14 Abs. 4 Nr. 1 UStG, § 31 Abs. 2, 3 UStDV |
| Steuernummer oder USt-IdNr. des Lieferanten | § 14 Abs. 4 Nr. 2 UStG |
| Ausstellungsdatum | Nr. 3 |
| Fortlaufende Rechnungsnummer | Nr. 4 |
| Menge und Art der Leistung | Nr. 5 |
| Zeitpunkt der Leistung (Kalendermonat genügt) | Nr. 6, § 31 Abs. 4 UStDV |
| Entgelt nach Steuersätzen, vereinbarte Minderungen (Skonto) | Nr. 7 |
| Steuersatz und Steuerbetrag oder Hinweis auf Befreiung | Nr. 8 |
| Hinweis „Steuerschuldnerschaft des Leistungsempfängers“ | § 14a Abs. 5 UStG |
| USt-IdNr. beider Seiten bei i. g. Lieferung | § 14a Abs. 3 UStG |
| Rechnerische Richtigkeit | Prüfung (keine Pflichtangabe) |

- **Kleinbetragsrechnung bis 250 € brutto** (§ 33 UStDV): nur Name und Anschrift des Lieferanten, Datum, Menge und Art, Entgelt mit Steuer in einer Summe und Steuersatz; die übrigen Punkte erscheinen als „nicht nötig“.
- **§ 13b:** Der Vorsteuerabzug hängt nicht an einer ordnungsgemäßen Rechnung (§ 15 Abs. 1 Satz 1 Nr. 4 UStG), fehlende Angaben sind dort nur Hinweise.
- Fehlende Pflichtangaben schicken den Beleg zur Prüfung („Pflichtangaben fehlen (§ 14 UStG): …“). Der Abschnitt „Rechnungsprüfung“ zeigt in der Kopfzeile immer das Ergebnis und klappt bei Lücken von selbst auf.
- **E-Rechnungen** werden aus den strukturierten Daten geprüft. Eine Validierung gegen die offiziellen XRechnung-Prüfregeln (KoSIT-Validator, Schematron) ist noch **nicht** eingebaut; das ist der nächste Schritt für E-Rechnungen.

## 3. Ausländische Rechnung ohne Reverse Charge
Neuer Steuerfall „ausländische Umsatzsteuer“: Lieferant aus dem Ausland (USt-IdNr. bzw. Anschrift) und die Rechnung weist ausländische Steuer aus (z. B. 20 % AT für einen Kongress in Wien, Leistungsort Österreich).
- Keine deutsche Vorsteuer, kein Steuerschlüssel; der Bruttobetrag geht in den Aufwand. Automatikkonten (z. B. 3400) passen nicht und werden markiert.
- Der Beleg geht zur Prüfung mit dem Hinweis auf das Vorsteuer-Vergütungsverfahren (Antrag über das BZSt).
- Ausländische Steuersätze bis 30 % gelten bei der Summenprüfung als zulässig.
- Weiterhin: Ausland **ohne** Steuer und ohne Hinweis gilt als § 13b (Leistung an Unternehmer, Ort im Inland).
- Nicht abgedeckt: Wareneinfuhr aus dem Drittland (Einfuhrumsatzsteuer über den Zollbescheid, Konto 1588) – braucht den Zollbeleg als eigenen Beleg.

Testrechnung F20: Kongresshaus Donaustadt GmbH, Wien, 2 × 390 € + 20 % AT-USt = 936 €, Konto 4945 Fortbildungskosten (in die Vorschlagsliste aufgenommen).
