# Entscheidung: Einzelunternehmer und Teilnehmerlisten vor dem KI-Aufruf pseudonymisieren

Datum: 02.11.2026 · Status: entschieden (Freigabe Paul Graß)

## Lücke
Der Lieferantenname ging bisher immer im Klartext an die KI (`CLAUDE.md` Regel 4: „Lieferantenname (Firma)“). Bei Einzelunternehmern, e.K., Freiberuflern und Personengesellschaften ist der Firmenname aber oft ein Personenname („Bürowelt Kranich e.K.“, „Malerbetrieb Max Müller“) und damit ein personenbezogenes Datum (Regel 3). Gleiches galt für Namen ohne Anrede, etwa die bewirteten Personen auf einem Bewirtungsbeleg.

## Entscheidung
- **Lieferant als natürliche Person:** Der Name im Briefkopf wird geprüft. Kapitalgesellschaften müssen ihre Rechtsform im Namen führen (§ 4 GmbHG, § 4 AktG, § 5a GmbHG; ausländische Formen wie B.V., Inc., Ltd. ebenso). Fehlt eine solche Rechtsform oder steht e.K., GbR, OHG oder KG ohne GmbH dabei, gilt der Lieferant als natürliche Person. Behörden und Verbände ohne Rechtsform (Stadtwerke, Finanzamt, Kammer …) sind ausgenommen.
  Dann werden **Name, Anschrift und USt-IdNr. des Lieferanten** durch `[LIEFERANT_1]`, `[ANSCHRIFT_n]` und `[USTID_LIEFERANT_1]` ersetzt. Die KI gibt den Platzhalter zurück, er wird lokal zurückübersetzt.
- **Teilnehmerlisten:** Namen nach „Bewirtete Personen:“, „Teilnehmer:“, „Gäste:“, „Anwesend:“ (auch englisch) werden ersetzt, auch ohne Anrede. Im Zweifel wird mehr ersetzt (z. B. „Kunde Weber“), das ist die sichere Richtung.
- Inland/EU, Leistungsdatum und Pflichtangaben bestimmt das Programm weiterhin lokal aus dem Rohtext; dafür braucht die KI die Angaben nicht.
- Code: `backend/app/pseudo/pseudonymizer.py`, Tests in `backend/tests/test_pseudonymisierung.py`.

## Prüfung
- Alle 64 Testbelege eingeordnet: 62 Firmen (GmbH, GmbH & Co. KG, B.V., Inc.) bleiben, 2 Personen werden ersetzt (Bürowelt Kranich e.K., Gasthaus Zur Linde). Keine Reste von Name, Anschrift oder USt-IdNr. im KI-Text.
- Rückübersetzung geprüft: Lieferantenname und alle 9 Pflichtfelder kommen korrekt zurück.
- Beim Test gefunden und behoben: Muster für Postleitzahl und Straße liefen über Zeilenumbrüche („12345⏎Lindenweg“); Zeilen wie „Tel.449“ oder „CEO: John Smith“ wurden als Briefkopf gelesen.

## Grenzen
- Namen in Freitext ohne Anrede und ohne Teilnehmer-Kennwort (z. B. „Beratung Schulz“) erkennt die musterbasierte Pseudonymisierung nicht. Abhilfe später: Namenserkennung (NER) mit deutschem Modell, wie in `CLAUDE.md` (Presidio mit spaCy) vorgesehen.
- Bei ersetztem Lieferantennamen fehlt der KI der Name als Hinweis für die Kontierung (z. B. „Malerbetrieb“). Die Positionen reichen in der Regel; Lernregeln je Kreditor arbeiten lokal mit dem echten Namen.
- `CLAUDE.md` Regel 4 („Lieferantenname (Firma)“) sollte um den Zusatz „außer bei natürlichen Personen“ ergänzt werden.
