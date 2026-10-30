"""Wertet einen Lauf des Machbarkeitstests aus und schreibt die Messwerte in den Bericht.

Die Tabellen stehen in ``docs/machbarkeitstest-bericht.md`` zwischen den Markierungen
``<!-- MESSWERTE:START -->`` und ``<!-- MESSWERTE:ENDE -->`` und werden bei jedem Lauf ersetzt.
Text außerhalb der Markierungen bleibt erhalten.

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/auswertung.py [Ausgabeordner]``
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm.factory import price_per_million  # noqa: E402
from app.qualitaet.vergleich import PFLICHTFELDER  # noqa: E402

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "docs" / "machbarkeitstest-bericht.md"
START, ENDE = "<!-- MESSWERTE:START -->", "<!-- MESSWERTE:ENDE -->"
KI_ANBIETER = ("bedrock", "bedrock_gptoss", "bedrock_qwen", "ionos_gptoss", "ionos_qwen")

FELDNAMEN = {
    "supplier_name": "Lieferant", "invoice_number": "Rechnungsnummer", "invoice_date": "Rechnungsdatum",
    "net_total": "Netto", "tax_total": "Steuer", "gross_total": "Brutto", "tax_rates": "Steuersätze",
    "document_type": "Belegart (Rechnung/Gutschrift)", "reverse_charge": "Reverse Charge / i. g. Erwerb",
}
GRUPPEN = {
    "xml": "E-Rechnung XML (KoSIT)",
    "pdf_synth": "PDF mit Text (synthetisch)",
    "pdf_kosit": "PDF mit Text (KoSIT-Sichtbeleg)",
    "scan": "Scan / Foto",
}


def gruppe(r: dict[str, Any]) -> str:
    if r["art"] == "xml":
        return "xml"
    if r["art"] in ("scan", "foto"):
        return "scan"
    return "pdf_kosit" if r["quelle"] == "kosit" else "pdf_synth"


def pct(ok: float, total: float) -> str:
    return "–" if not total else f"{100 * ok / total:.1f} %"


def load_run(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lauf = json.loads((run_dir / "lauf.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (run_dir / "ergebnisse.jsonl").read_text(encoding="utf-8").splitlines()]
    return lauf, rows


def merge_runs(run_dirs: list[Path]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Je Anbieter und Belegdatei das jüngste Ergebnis. So zählen Nachmessungen einzelner Belege,
    und bezahlte Messungen müssen nicht wiederholt werden, wenn ein neuer Anbieter dazukommt."""
    runs = [(d, *load_run(d)) for d in sorted(run_dirs)]
    latest_row: dict[tuple[str, str], tuple[Path, dict[str, Any]]] = {}
    lauf_of: dict[Path, dict[str, Any]] = {}
    for d, lauf, rows in runs:
        lauf_of[d] = lauf
        for r in rows:
            latest_row[(r["anbieter"], r["datei"])] = (d, r)
    merged_rows = [r for _, r in latest_row.values()]
    herkunft: dict[str, set[str]] = {}
    for (a, _), (d, _) in latest_row.items():
        herkunft.setdefault(a, set()).add(d.name)
    newest_for = {a: max(ds) for a, ds in herkunft.items()}
    latest = runs[-1][1]
    lauf = {
        "belege": max(lf.get("belege", 0) for _, lf, _ in runs),
        "herkunft": {a: ", ".join(sorted(ds)) for a, ds in herkunft.items()},
        "modelle": {a: (lauf_of[next(d for d in lauf_of if d.name == n)].get("modelle") or {}).get(a)
                    for a, n in newest_for.items()},
        "preise_eur_je_mio": {a: p for a, n in newest_for.items()
                              if (p := (lauf_of[next(d for d in lauf_of if d.name == n)].get("preise_eur_je_mio") or {}).get(a))},
        "uebersprungen": {k: v for k, v in (latest.get("uebersprungen") or {}).items() if k not in herkunft},
    }
    return lauf, merged_rows


def build(lauf: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    anbieter = sorted({r["anbieter"] for r in rows}, key=lambda a: (a != "erechnung", a))
    out: list[str] = []

    herkunft = lauf.get("herkunft") or {}
    out.append(f"**Belege:** {lauf['belege']} · **gemessene Anbieter:** {', '.join(anbieter)}")
    if herkunft:
        out.append("")
        out.append("**Läufe:** " + "; ".join(f"`{a}` aus `{d}`" for a, d in sorted(herkunft.items())))
    modelle = {k: v for k, v in (lauf.get("modelle") or {}).items() if v}
    if modelle:
        out.append("")
        out.append("**Modelle:** " + "; ".join(f"`{k}` = `{v}`" for k, v in modelle.items()))
    if lauf.get("uebersprungen"):
        out.append("")
        out.append("**Nicht gemessen:** " + "; ".join(f"`{k}` ({v})" for k, v in lauf["uebersprungen"].items()))
    out.append("")

    # 1. Pflichtfelder je Anbieter und Belegart
    out += ["### Pflichtfelder je Anbieter und Belegart", "",
            "| Anbieter | " + " | ".join(GRUPPEN.values()) + " | Gesamt |",
            "|---|" + "---|" * (len(GRUPPEN) + 1)]
    for a in anbieter:
        cells, tok, ttot = [], 0, 0
        for g in GRUPPEN:
            sel = [r for r in rows if r["anbieter"] == a and gruppe(r) == g]
            ok = sum(sum(r["vergleich"]["felder"].values()) for r in sel)
            total = len(sel) * len(PFLICHTFELDER)
            tok, ttot = tok + ok, ttot + total
            cells.append(f"{pct(ok, total)} ({len(sel)})" if sel else "–")
        out.append(f"| `{a}` | " + " | ".join(cells) + f" | **{pct(tok, ttot)}** |")
    out += ["", "In Klammern: Zahl der Belege. Zielwert Phase A: mindestens 90 % bei sauberen PDFs.", ""]

    # 1b. Pflichtfelder je Layout (nur KI-Strecke)
    layouts = sorted({r.get("layout", "–") for r in rows if r["art"] != "xml"})
    ki_a = [a for a in anbieter if a != "erechnung"]
    out += ["### Pflichtfelder je Layout (PDF, Scan, Foto)", "",
            "| Layout | Belege | " + " | ".join(f"`{a}`" for a in ki_a) + " |",
            "|---|---|" + "---|" * len(ki_a)]
    for lay in layouts:
        cells = []
        n = 0
        for a in ki_a:
            sel = [r for r in rows if r["anbieter"] == a and r["art"] != "xml" and r.get("layout", "–") == lay]
            n = max(n, len(sel))
            ok = sum(sum(r["vergleich"]["felder"].values()) for r in sel)
            cells.append(pct(ok, len(sel) * len(PFLICHTFELDER)))
        out.append(f"| {lay} | {n} | " + " | ".join(cells) + " |")
    out += ["", "Layout „klassisch“ ist die Vorlage, auf die der Platzhalter abgestimmt ist. Die übrigen Layouts zeigen, "
            "wie gut ein Anbieter mit fremden Rechnungsbildern umgeht.", ""]

    # 2. Trefferquote je Feld
    out += ["### Trefferquote je Feld (ohne XML)", "", "| Feld | " + " | ".join(f"`{a}`" for a in anbieter if a != "erechnung") + " |",
            "|---|" + "---|" * len([a for a in anbieter if a != "erechnung"])]
    ki = [a for a in anbieter if a != "erechnung"]
    for f in PFLICHTFELDER:
        cells = []
        for a in ki:
            sel = [r for r in rows if r["anbieter"] == a]
            cells.append(pct(sum(r["vergleich"]["felder"][f] for r in sel), len(sel)))
        out.append(f"| {FELDNAMEN[f]} | " + " | ".join(cells) + " |")
    for key, label in (("betrag", "Positionen: Nettobetrag"), ("steuersatz", "Positionen: Steuersatz"),
                       ("konto", "Positionen: Sachkonto SKR03")):
        cells = []
        for a in ki:
            sel = [r for r in rows if r["anbieter"] == a]
            ok = sum(r["vergleich"]["positionen"][key][0] for r in sel)
            tot = sum(r["vergleich"]["positionen"][key][1] for r in sel)
            cells.append(f"{pct(ok, tot)} ({ok}/{tot})")
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    cells = []
    for a in ki:
        sel = [r for r in rows if r["anbieter"] == a]
        cells.append(pct(sum(r["plausibel"] for r in sel), len(sel)))
    out.append("| Steuerlogik: Summen plausibel | " + " | ".join(cells) + " |")
    out += ["", "Sachkonten werden nur bei den synthetischen Belegen bewertet (KoSIT-Belege haben keine Sollkontierung).", ""]

    # 3. Pseudonymisierung
    pdf_rows = [r for r in rows if r["art"] != "xml"]
    seen: dict[str, dict[str, Any]] = {}
    for r in pdf_rows:
        seen.setdefault(r["datei"], r)
    lecks = sum(r["pseudo_lecks"] for r in seen.values())
    geprueft = sum(r["pseudo_geprueft"] for r in seen.values())
    betroffen = sorted(r["id"] for r in seen.values() if r["pseudo_lecks"])
    out += ["### Pseudonymisierung", "",
            f"Geprüft: {geprueft} sensible Werte in {len(seen)} Belegtexten (Mandantenname, Ansprechpartner, Anschrift, "
            f"USt-IdNr. des Mandanten, IBAN, E-Mail, Telefon, Steuernummer, Namen natürlicher Personen beim Lieferanten).",
            "",
            f"**Im KI-Text verblieben: {lecks} von {geprueft} ({pct(lecks, geprueft)})**"
            + (f" · betroffene Belege: {', '.join(betroffen)}" if betroffen else ""), ""]

    # 4. Laufzeit
    out += ["### Laufzeit je Beleg", "", "| Schritt | Mittelwert | Maximum |", "|---|---|---|"]
    for label, sel in (("XML parsen", [r["laufzeit_s"] for r in rows if r["art"] == "xml"]),
                       ("PDF-Textlayer lesen", [r["lesezeit_s"] for r in seen.values() if r["methode"] == "textlayer"]),
                       ("Texterkennung docTR (CPU), Scan und Foto", [r["lesezeit_s"] for r in seen.values() if r["methode"] == "ocr"])):
        if sel:
            out.append(f"| {label} | {mean(sel):.2f} s | {max(sel):.2f} s |")
    for a in ki:
        lat = [r["laufzeit_s"] for r in rows if r["anbieter"] == a]
        out.append(f"| Anbieter `{a}` | {mean(lat):.2f} s | {max(lat):.2f} s |")
    out.append("")

    # 5. Kosten
    out += ["### Kosten je Beleg (KI-Aufruf)", "",
            "| Anbieter | Preis Eingabe / Ausgabe je Mio. Token | Token je Beleg (Ø ein / aus) | Kosten je Beleg | Grundlage |",
            "|---|---|---|---|---|"]
    est_in = mean(r["token_ein_geschaetzt"] for r in seen.values()) if seen else 0
    est_out = mean(r["token_aus_geschaetzt"] for r in seen.values()) if seen else 0
    any_measured = [r for r in rows if r["anbieter"] in KI_ANBIETER and r["token_ein"]]
    if any_measured:  # gemessene Tokenzahl eines Anbieters ist die bessere Schätzung für die übrigen
        est_in = mean(r["token_ein"] for r in any_measured)
        est_out = mean(r["token_aus"] for r in any_measured)
    run_prices = lauf.get("preise_eur_je_mio") or {}
    for a in KI_ANBIETER:
        pin, pout = run_prices.get(a) or price_per_million(a)
        measured = [r for r in rows if r["anbieter"] == a and r["token_ein"]]
        if measured:
            tin, tout = mean(r["token_ein"] for r in measured), mean(r["token_aus"] for r in measured)
            cost = mean(r["kosten_eur"] for r in measured)
            basis = f"gemessen ({len(measured)} Aufrufe)"
        else:
            tin, tout, basis = est_in, est_out, "Schätzung, noch nicht gemessen"
            cost = (tin * pin + tout * pout) / 1_000_000
        out.append(f"| `{a}` | {pin:.2f} € / {pout:.2f} € | {tin:,.0f} / {tout:,.0f} | {cost:.4f} € | {basis} |")
    out += ["", "Hinzu kommen Serverkosten für Texterkennung und Anwendung (siehe `docs/kosten.md`).", ""]

    # 6. Einzelbelege
    out += ["### Ergebnisse je Beleg", "", "| Beleg | Merkmale | Art | Anbieter | Pflichtfelder | Positionen Betrag | Konto | Abweichungen |",
            "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["id"], r["art"], r["anbieter"])):
        f = r["vergleich"]["felder"]
        p = r["vergleich"]["positionen"]
        bad = [FELDNAMEN[k] for k, v in f.items() if not v]
        if not p["anzahl"]:
            bad.append("Positionsanzahl")
        art = r["art"] + (" (CII)" if "uncefact" in r["datei"] else " (UBL)" if r["art"] == "xml" else "")
        konto = f'{p["konto"][0]}/{p["konto"][1]}' if p["konto"][1] else "–"
        out.append(f'| {r["id"]} | {", ".join(r["merkmale"])} | {art} | `{r["anbieter"]}` | {sum(f.values())}/{len(f)} | '
                   f'{p["betrag"][0]}/{p["betrag"][1]} | {konto} | {", ".join(bad) or "–"} |')
    return "\n".join(out)


def main() -> None:
    """Ohne Argument: alle Läufe in testdaten/ausgaben zusammenführen. Mit Argumenten: nur diese Läufe."""
    base = PROJECT / "testdaten" / "ausgaben"
    run_dirs = [Path(a) for a in sys.argv[1:]] or [p for p in base.iterdir() if (p / "ergebnisse.jsonl").exists()]
    lauf, rows = merge_runs(run_dirs)
    block = f"{START}\n{build(lauf, rows)}\n{ENDE}"
    if REPORT.exists():
        text = REPORT.read_text(encoding="utf-8")
        if START in text and ENDE in text:
            text = text[: text.index(START)] + block + text[text.index(ENDE) + len(ENDE):]
        else:
            text += "\n\n" + block + "\n"
    else:
        text = f"# Machbarkeitstest – Bericht\n\n## Messwerte\n\n{block}\n"
    REPORT.write_text(text, encoding="utf-8")
    print(f"Bericht aktualisiert: {REPORT} ({len(lauf['herkunft'])} Anbieter aus {len(set(lauf['herkunft'].values()))} Läufen)")


if __name__ == "__main__":
    main()
