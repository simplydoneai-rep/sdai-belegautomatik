# Entscheidung: Lesbares Belegbild für E-Rechnungen

Stand: 03.11.2026 · Anlass: Rückmeldung Paul Graß, rechts stand bei E-Rechnungen nur der rohe XML-Text

## Entscheidung
Die Belegansicht zeigt eine E-Rechnung (XRechnung, UBL und CII) als aufbereitete Rechnung: Verkäufer und Empfänger, Rechnungsdaten und Referenzen (Leitweg-ID, Bestellung, Vertrag, Projekt, vorherige Rechnung), Positionen, Zu- und Abschläge, Summen, Steueraufschlüsselung mit Befreiungsgrund, Zahlungsangaben und Hinweise. Darunter bleibt das **Original-XML** aufklappbar.

- Erzeugt von `backend/app/erechnung/belegbild.py` direkt aus dem XML, Schnittstelle `GET /api/beleg/belegbild`. Gleiche sichere XML-Einstellungen wie der Parser (keine externen Entitäten, kein Netzwerk).
- Codelisten für die Anzeige (Rechnungsart UNTDID 1001, Zahlungsart UNTDID 4461, Steuerkategorie UNTDID 5305) stehen im Modul; unbekannte Codes werden als Code gezeigt, nicht geraten.
- Optionale Summen (Abschläge, Zuschläge, Vorauszahlung, Rundung) nur, wenn sie nicht 0 sind. Betreff-Codes wie `#ADU#` vor Hinweisen werden entfernt.
- Beträge werden **so gezeigt, wie sie im XML stehen**, auch wenn sie falsch sind (z. B. F21: Brutto passt nicht zu Netto + Steuer). Die Prüfung macht die Validierung, nicht die Anzeige.
- Überfahren einer Position hebt die Zeile im Belegbild hervor (wie bei PDF-Belegen).

## GoBD
Maßgeblich ist das Original-XML; es wird nicht verändert und bleibt in der Ansicht erreichbar. Das Belegbild ist nur eine Darstellung und wird nicht gespeichert. An der Verarbeitung ändert sich nichts, daher kein Nachtrag in der Verfahrensdokumentation.

## Alternative (nicht gewählt)
Die offizielle Visualisierung der KoSIT (`xrechnung-visualization`, XSLT nach HTML/PDF) ist die Referenzdarstellung. Sie bräuchte ein weiteres heruntergeladenes Regelwerk und passt optisch nicht zur Oberfläche. Für den Pilot reicht die eigene Darstellung; bei Bedarf (z. B. PDF-Ausgabe der E-Rechnung für Mandanten) kann sie ergänzt werden.

## Prüfung
Tests in `backend/tests/test_erechnung.py`: Für alle KoSIT-Testrechnungen liefern UBL und CII dasselbe Belegbild (Positionen, Steuern, Summen); die Positionssumme stimmt mit der Rechnungssumme überein; Reverse Charge zeigt Kategorie und Befreiungsgrund.
