"""LLMProvider-Schnittstelle. Nimmt ausschließlich pseudonymisierte Nutzdaten an."""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.pseudo.pseudonymizer import PseudonymizedPayload

OUTPUT_SCHEMA: dict[str, Any] = {
    "document_type": "invoice | credit_note",
    "supplier_name": "string (Firma des Rechnungsstellers)",
    "invoice_number": "string",
    "invoice_date": "YYYY-MM-DD",
    "currency": "ISO-4217, z. B. EUR",
    "net_total": "Dezimalzahl als String, Vorzeichen wie auf dem Beleg",
    "tax_total": "Dezimalzahl als String",
    "gross_total": "Dezimalzahl als String",
    "reverse_charge": "true, wenn der Leistungsempfänger die Steuer schuldet (§ 13b UStG oder innergemeinschaftlicher Erwerb)",
    "lines": [
        {
            "description": "string",
            "quantity": "Dezimalzahl als String",
            "unit": "string",
            "unit_price": "Dezimalzahl als String",
            "net_amount": "Dezimalzahl als String",
            "tax_rate": "Steuersatz in Prozent als String, z. B. 19, 7, 0",
            "account_skr03": "nur die Kontonummer (z. B. \"3400\") aus der erlaubten Kontenliste",
        }
    ],
}

SYSTEM_PROMPT = (
    "Du liest Eingangsrechnungen für eine deutsche Steuerkanzlei aus. "
    "Der Belegtext ist pseudonymisiert: Platzhalter wie [IBAN_1] oder [MANDANT_1] unverändert lassen. "
    "Antworte ausschließlich mit einem JSON-Objekt nach dem vorgegebenen Schema, ohne Erklärung, ohne Markdown. "
    "Beträge als Dezimalzahl mit Punkt (z. B. \"1234.56\"). Nichts erfinden: Fehlt eine Angabe, setze null. "
    "Bei einer Gutschrift bleiben die Beträge so, wie sie auf dem Beleg stehen (negativ, falls negativ gedruckt). "
    "net_amount und unit_price sind Nettowerte. Weist die Rechnung Nettopreise aus (Normalfall: "
    "Positionen netto, Umsatzsteuer erst in der Summe), übernimm die Positionsbeträge unverändert. "
    "Nur wenn der Beleg ausdrücklich Bruttopreise zeigt (z. B. Kassenbon, Kleinbetragsrechnung, "
    "\"inkl. MwSt.\"), rechne die Positionen mit ihrem Steuersatz auf netto um. "
    "tax_rate ist der auf dem Beleg für die Position ausgewiesene Satz (bei Reverse Charge oder "
    "steuerfreier Lieferung 0). account_skr03 enthält nur die vierstellige Kontonummer, z. B. \"3400\". "
    "Fehlt eine Rechnungsnummer, setze invoice_number auf null. "
    "Für jede Position schlägst du genau ein Sachkonto aus der erlaubten Liste vor; "
    "Konten außerhalb der Liste sind unzulässig."
)


def build_user_prompt(payload: PseudonymizedPayload) -> str:
    accounts = "\n".join(f"{nr} {name}" for nr, name in payload.allowed_accounts)
    return (
        f"Kontenrahmen: {payload.chart_of_accounts}\n"
        f"Branche des Mandanten (WZ-Code): {payload.industry_code}\n\n"
        f"Erlaubte Sachkonten:\n{accounts}\n\n"
        f"JSON-Schema:\n{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=1)}\n\n"
        f"Belegtext:\n<<<\n{payload.text}\n>>>"
    )


@dataclass
class ProviderResult:
    data: dict[str, Any] | None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    error: str | None = None
    raw: str = field(default="", repr=False)


_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


def parse_json_answer(raw: str) -> dict[str, Any]:
    cleaned = _FENCE.sub("", _THINK.sub("", raw)).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("keine JSON-Antwort")
    obj = json.loads(cleaned[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("JSON ist kein Objekt")
    return obj


class LLMProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def _complete(self, system: str, user: str) -> tuple[str, int, int]:
        """Liefert (Antworttext, Eingabe-Token, Ausgabe-Token)."""

    def extract(self, payload: PseudonymizedPayload) -> ProviderResult:
        # Laufzeitschutz zusätzlich zur Typisierung (CLAUDE.md Regel 2).
        if not isinstance(payload, PseudonymizedPayload):
            raise TypeError("LLMProvider akzeptiert nur PseudonymizedPayload")
        t0 = time.perf_counter()
        raw = ""
        try:
            raw, tin, tout = self._complete(SYSTEM_PROMPT, build_user_prompt(payload))
            data = parse_json_answer(raw)
            return ProviderResult(data, tin, tout, time.perf_counter() - t0, None, raw)
        except Exception as exc:  # Fehlertext ohne Belegdaten loggen
            return ProviderResult(None, 0, 0, time.perf_counter() - t0, f"{type(exc).__name__}", raw)
