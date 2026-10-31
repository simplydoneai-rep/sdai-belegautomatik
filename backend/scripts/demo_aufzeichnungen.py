"""Stellt die KI-Antworten aus den Messläufen für die Demo zusammen (keine neuen KI-Kosten).

Für jede Testdatei und jedes KI-Modell das jüngste Ergebnis aus ``testdaten/ausgaben``,
verknüpft über die SHA-256-Prüfsumme der Datei. Ergebnis: ``testdaten/demo/aufzeichnungen.json``.
Nur synthetische Testbelege (CLAUDE.md Regel 1).

Aufruf (aus ``backend/``): ``.venv/Scripts/python scripts/demo_aufzeichnungen.py``
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auswertung import merge_runs  # noqa: E402

PROJECT = Path(__file__).resolve().parents[2]
TESTDATEN = PROJECT / "testdaten"
KI = ("bedrock", "bedrock_gptoss", "bedrock_qwen", "ionos_gptoss", "ionos_qwen")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    runs = [p for p in (TESTDATEN / "ausgaben").iterdir() if (p / "ergebnisse.jsonl").exists()]
    lauf, rows = merge_runs(runs)
    records: dict[str, dict[str, object]] = {}
    for r in rows:
        if r["anbieter"] not in KI or r.get("fehler") or not r.get("ausgabe"):
            continue
        path = TESTDATEN / r["datei"]
        entry = records.setdefault(sha256(path), {"datei": r["datei"], "id": r["id"], "antworten": {}})
        entry["antworten"][r["anbieter"]] = {  # type: ignore[index]
            "modell": (lauf.get("modelle") or {}).get(r["anbieter"]),
            "lauf": lauf["herkunft"].get(r["anbieter"]),
            "laufzeit_s": r["laufzeit_s"],
            "token_ein": r["token_ein"],
            "token_aus": r["token_aus"],
            "kosten_eur": r["kosten_eur"],
            "ausgabe": r["ausgabe"],
        }
    out = TESTDATEN / "demo" / "aufzeichnungen.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"_meta": {"hinweis": "KI-Antworten aus den Messläufen, nur synthetische Testbelege",
                                         "modelle": lauf.get("modelle")},
                               "belege": records}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(e["antworten"]) for e in records.values())  # type: ignore[arg-type]
    print(f"{len(records)} Belege, {n} aufgezeichnete Antworten → {out}")


if __name__ == "__main__":
    main()
