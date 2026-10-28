"""Machbarkeitstest: alle Goldstandard-Belege durch Auslesen, Pseudonymisierung und KI-Anbieter.

Ablauf je Beleg:
  XML (XRechnung)      → E-Rechnungs-Parser (ohne KI)
  PDF mit Textlayer    → PyMuPDF → Pseudonymisierung → LLMProvider
  Scan                 → docTR (lokal) → Pseudonymisierung → LLMProvider

Zugangsdaten nur aus ``.env`` im Projektordner. Ohne Zugangsdaten läuft nur ``placeholder``.
Ergebnisse: ``testdaten/ausgaben/<Zeitstempel>/ergebnisse.jsonl``.
Konsolenausgabe enthält nur IDs, Status und Laufzeiten (CLAUDE.md Regel 7).

Aufruf (aus ``backend/``):
  .venv/Scripts/python scripts/machbarkeitstest.py [--anbieter placeholder,bedrock] [--nur S01,S02]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

from app.erechnung.parser import parse_file, without_parties  # noqa: E402
from app.kontierung.konten import load_accounts  # noqa: E402
from app.kontierung.steuerlogik import pruefe_summen  # noqa: E402
from app.llm.base import SYSTEM_PROMPT, LLMProvider, build_user_prompt  # noqa: E402
from app.llm.factory import build_providers, price_per_million  # noqa: E402
from app.ocr.text import read_document  # noqa: E402
from app.pseudo.pseudonymizer import ClientProfile, pseudonymize  # noqa: E402
from app.qualitaet.vergleich import compare, leaks  # noqa: E402

PROJECT = Path(__file__).resolve().parents[2]
TESTDATEN = PROJECT / "testdaten"


def client_profile(client: dict[str, Any]) -> ClientProfile:
    return ClientProfile(
        name_variants=(client["name"],),
        address_fragments=(client["street"], f'{client["postcode"]} {client["city"]}'),
        person_names=(client["person"],),
        industry_code=client["industry_code"],
        chart_of_accounts="SKR03",
    )


def restore(value: Any, mapping: dict[str, str]) -> Any:
    """Setzt Platzhalter in der KI-Antwort lokal zurück (Zuordnung verlässt den Prozess nie)."""
    if isinstance(value, str):
        for ph, original in mapping.items():
            value = value.replace(ph, original)
        return value
    if isinstance(value, list):
        return [restore(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: restore(v, mapping) for k, v in value.items()}
    return value


def estimate_tokens(chars: int) -> int:
    # Faustregel für deutschen Text mit Zahlen: ca. 3,5 Zeichen je Token.
    return math.ceil(chars / 3.5)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anbieter", help="Kommagetrennt; Standard: alle mit Zugangsdaten")
    ap.add_argument("--nur", help="Kommagetrennte Beleg-IDs")
    args = ap.parse_args()

    load_dotenv(PROJECT / ".env")
    providers, skipped = build_providers()
    if args.anbieter:
        wanted = args.anbieter.split(",")
        for w in wanted:
            if w not in providers:
                skipped.setdefault(w, "nicht verfügbar")
        providers = {k: v for k, v in providers.items() if k in wanted}

    mandanten = json.loads((TESTDATEN / "mandanten.json").read_text(encoding="utf-8"))["mandanten"]
    accounts = load_accounts("SKR03")
    golds = sorted((TESTDATEN / "goldstandard").glob("*.json"))
    if args.nur:
        ids = set(args.nur.split(","))
        golds = [g for g in golds if g.stem in ids]

    out_dir = TESTDATEN / "ausgaben" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lauf.json").write_text(
        json.dumps({"anbieter": list(providers), "uebersprungen": skipped, "belege": len(golds),
                    "modelle": {k: getattr(v, "model_id", None) or getattr(v, "model", None) for k, v in providers.items()},
                    "preise_eur_je_mio": {k: list(price_per_million(k)) for k in providers},
                    "start": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Anbieter: {', '.join(providers) or '-'}; übersprungen: {skipped or '-'}")

    with (out_dir / "ergebnisse.jsonl").open("w", encoding="utf-8") as out:
        for gpath in golds:
            gold = json.loads(gpath.read_text(encoding="utf-8"))
            client = mandanten[gold["client_id"]]
            for doc in gold["dokumente"]:
                path = TESTDATEN / doc["pfad"]
                expected = {**gold["erwartet"], **doc.get("abweichend", {})}
                layout = gold.get("layout") or ("klassisch" if gold["quelle"] == "synthetisch" else "kosit")
                base = {"id": gold["id"], "quelle": gold["quelle"], "art": doc["art"], "datei": doc["pfad"],
                        "layout": layout, "merkmale": gold.get("merkmale", [])}

                if doc["art"] == "xml":
                    t0 = time.perf_counter()
                    try:
                        data: dict[str, Any] | None = without_parties(parse_file(path))
                        error = None
                    except Exception as exc:
                        data, error = None, type(exc).__name__
                    rec = {**base, "anbieter": "erechnung", "methode": "xml", "fehler": error,
                           "laufzeit_s": round(time.perf_counter() - t0, 3), "lesezeit_s": 0.0,
                           "token_ein": 0, "token_aus": 0, "kosten_eur": 0.0,
                           "plausibel": pruefe_summen(data).ok if data else False,
                           "vergleich": compare(expected, data), "ausgabe": data}
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f'{gold["id"]:8} xml        erechnung      {"ok" if not error else error}')
                    continue

                read = read_document(path)
                pseudo = pseudonymize(read.text, client_profile(client), accounts, own_vat_ids=(client["vat_id"],))
                payload = pseudo.payload
                prompt_chars = len(SYSTEM_PROMPT) + len(build_user_prompt(payload))
                leak_idx = leaks(payload.text, gold.get("sensible_werte", []))

                for pname, provider in providers.items():
                    res = provider.extract(payload)
                    data = restore(res.data, pseudo.mapping) if res.data is not None else None
                    pin, pout = price_per_million(pname)
                    cost = (res.input_tokens * pin + res.output_tokens * pout) / 1_000_000
                    check = pruefe_summen(data) if data else None
                    rec = {
                        **base, "anbieter": pname, "methode": read.method, "fehler": res.error,
                        "laufzeit_s": round(res.latency_s, 3), "lesezeit_s": round(read.seconds, 3),
                        "token_ein": res.input_tokens, "token_aus": res.output_tokens, "kosten_eur": round(cost, 6),
                        "token_ein_geschaetzt": estimate_tokens(prompt_chars),
                        "token_aus_geschaetzt": estimate_tokens(len(json.dumps(gold["erwartet"], ensure_ascii=False))),
                        "plausibel": check.ok if check else False,
                        "plausi_hinweise": check.hinweise if check else ["keine_antwort"],
                        "pseudo_platzhalter": len(pseudo.mapping),
                        "pseudo_lecks": len(leak_idx), "pseudo_lecks_idx": leak_idx,
                        "pseudo_geprueft": len(gold.get("sensible_werte", [])),
                        "vergleich": compare(expected, data), "ausgabe": data,
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f'{gold["id"]:8} {doc["art"]:4} {read.method:9} {pname:14} '
                          f'{"ok" if not res.error else res.error} {res.latency_s:.1f}s')

    print(f"Ergebnisse: {out_dir}")


if __name__ == "__main__":
    main()
