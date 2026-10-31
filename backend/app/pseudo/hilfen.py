"""Hilfen rund um die Pseudonymisierung: Mandantenprofil aus Stammdaten, Platzhalter zurücksetzen."""

from __future__ import annotations

from typing import Any

from app.pseudo.pseudonymizer import ClientProfile


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
