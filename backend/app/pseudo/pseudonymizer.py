"""Pseudonymisierung vor jedem KI-Aufruf (CLAUDE.md, Regeln 2-4).

Die Zuordnung Platzhalter -> Originalwert bleibt in ``PseudonymizationResult.mapping``
und verlässt den Prozess nie. Der LLM-Client akzeptiert nur ``PseudonymizedPayload``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TOKEN = object()


@dataclass(frozen=True)
class PseudonymizedPayload:
    """Das einzige Objekt, das ein LLMProvider entgegennimmt."""

    text: str
    industry_code: str
    chart_of_accounts: str
    allowed_accounts: tuple[tuple[str, str], ...]
    _token: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _TOKEN:
            raise TypeError("PseudonymizedPayload nur über pseudonymize() erzeugen")


@dataclass(frozen=True)
class ClientProfile:
    """Stammdaten des Mandanten, die vor dem KI-Aufruf entfernt werden müssen."""

    name_variants: tuple[str, ...]
    address_fragments: tuple[str, ...] = ()
    person_names: tuple[str, ...] = ()
    industry_code: str = "00.00"
    chart_of_accounts: str = "SKR03"


@dataclass
class PseudonymizationResult:
    payload: PseudonymizedPayload
    mapping: dict[str, str]  # Platzhalter -> Originalwert, bleibt lokal


_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?\b")
_BIC = re.compile(r"\b(?:BIC|SWIFT)[:\s-]*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_PHONE = re.compile(
    r"(?i)(?:(?:Tel(?:efon)?|Fax|Mobil|Handy)\.?[: \t]*)(\+?\d[\d ()/\-]{6,}\d)|(\+\d{2}[\d ()/\-]{6,}\d)"
)
_TAXNO = re.compile(r"(?i)\b(?:Steuer-?(?:nr|nummer)\.?|St\.?-?Nr\.?)[:\s]*([\d /]{8,})")
_VATID = re.compile(r"\b(?:DE\s?\d{9}|ATU\d{8}|[A-Z]{2}[A-Z0-9]{8,12})\b")
_PERSON = re.compile(
    r"\b(?:Herrn?|Frau|Hr\.|Fr\.|Ansprechpartner(?:in)?:?|Sachbearbeiter(?:in)?:?|Fahrer:?|Kontakt:?"
    r"|Gesch\w{0,4}f\w{0,2}hr(?:er|erin|ung)?:?|Inhaber(?:in)?:?|GF:?|Vorstand:?"
    r"|Mr\.?|Mrs\.?|Ms\.?|Attn\.?:?|Contact(?: person)?:?|(?:Managing )?[Dd]irector:?|CEO:?|Owner:?)[ \t]+"
    r"((?:Dr\.[ ]|Prof\.[ ])?[A-ZÄÖÜ][a-zäöüß]+"
    r"(?:[ ](?:(?:van|von|de|der|den|du|zu|ter)[ ])?[A-ZÄÖÜ][a-zäöüß-]+){0,2})"
)
# Name in der Zeile nach einer Grußformel (Unterschrift ohne Hinweiswort)
_SIGNATURE = re.compile(
    r"(?im:(?:mit )?freundlichen gr[üu](?:ß|ss)en|freundliche gr[üu](?:ß|ss)e|viele gr[üu](?:ß|ss)e"
    r"|kind regards|best regards|sincerely|yours faithfully)[,.]?[ \t]*\n(?:[ \t]*\n)*[ \t]*"
    r"((?:Dr\.[ ]|Prof\.[ ])?[A-ZÄÖÜ][a-zäöüß]+(?:[ ](?:(?:van|von|de|der|den|zu)[ ])?[A-ZÄÖÜ][a-zäöüß-]+){1,2})[ \t]*$",
    re.M,
)
_ACCOUNTNO = re.compile(r"(?i)\b(?:Konto-?(?:nr|nummer)\.?|Kto\.?-?Nr\.?)[:\s]*(\d{5,12})")

_UMLAUT = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "b", "Ä": "A", "Ö": "O", "Ü": "U", "é": "e"})
FUZZY_MIN_SCORE = 85.0  # rapidfuzz-Ähnlichkeit 0–100, fängt OCR-Lesefehler in Mandantendaten


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.translate(_UMLAUT).lower())


def _replace_fuzzy(text: str, needle: str, placeholder: str) -> str:
    """Ersetzt ``needle`` exakt und zusätzlich unscharf (OCR-Fehler wie "Kornteld" statt "Kornfeld").

    Verglichen werden Wortfenster gleicher Wortzahl innerhalb einer Zeile.
    """
    from rapidfuzz import fuzz

    text = re.sub(re.escape(needle), lambda _m: placeholder, text, flags=re.I)
    n = len(needle.split())
    target = _norm(needle)
    if n == 0 or len(target) < 5:
        return text
    out_lines = []
    for line in text.split("\n"):
        spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", line)]
        hits: list[tuple[int, int]] = []
        i = 0
        while i + n <= len(spans):
            start, end = spans[i][0], spans[i + n - 1][1]
            window = line[start:end]
            if "[" not in window and fuzz.ratio(_norm(window), target) >= FUZZY_MIN_SCORE:
                hits.append((start, end))
                i += n
            else:
                i += 1
        for start, end in reversed(hits):
            line = line[:start] + placeholder + line[end:]
        out_lines.append(line)
    return "\n".join(out_lines)


class _Registry:
    def __init__(self) -> None:
        self.mapping: dict[str, str] = {}
        self._reverse: dict[tuple[str, str], str] = {}
        self._counters: dict[str, int] = {}

    def token(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._reverse:
            n = self._counters.get(kind, 0) + 1
            self._counters[kind] = n
            placeholder = f"[{kind}_{n}]"
            self._reverse[key] = placeholder
            self.mapping[placeholder] = value
        return self._reverse[key]


def _sub_group(pattern: re.Pattern[str], text: str, reg: _Registry, kind: str, group: int = 0) -> str:
    def repl(m: re.Match[str]) -> str:
        value = m.group(group)
        full = m.group(0)
        ph = reg.token(kind, value.strip())
        return full.replace(value, ph) if group else ph

    return pattern.sub(repl, text)


def pseudonymize(
    raw_text: str,
    client: ClientProfile,
    allowed_accounts: tuple[tuple[str, str], ...],
    own_vat_ids: tuple[str, ...] = (),
) -> PseudonymizationResult:
    """Ersetzt personenbezogene und mandantenbezogene Angaben durch Platzhalter.

    Lieferantenname, Positionen, Beträge, Steuersätze und Datum bleiben erhalten.
    Fremde USt-IdNr. des Lieferanten bleiben ebenfalls erhalten (Firmenangabe, für die
    Steuerlogik nötig: Inland/EU); die USt-IdNr. des Mandanten wird ersetzt.
    """
    reg = _Registry()
    text = raw_text

    # Reihenfolge wichtig: zuerst feste Mandantendaten, dann Muster.
    for variant in sorted(client.name_variants, key=len, reverse=True):
        text = _replace_fuzzy(text, variant, reg.token("MANDANT", client.name_variants[0]))
    for frag in sorted(client.address_fragments, key=len, reverse=True):
        text = _replace_fuzzy(text, frag, reg.token("ANSCHRIFT", frag))
    for person in client.person_names:
        text = _replace_fuzzy(text, person, reg.token("PERSON", person))
    for vat in own_vat_ids:
        text = text.replace(vat, reg.token("USTID_MANDANT", vat))

    text = _sub_group(_IBAN, text, reg, "IBAN")
    text = _sub_group(_BIC, text, reg, "BIC", group=1)
    text = _sub_group(_EMAIL, text, reg, "EMAIL")
    text = _sub_group(_TAXNO, text, reg, "STEUERNR", group=1)
    text = _sub_group(_ACCOUNTNO, text, reg, "KONTO", group=1)
    text = _sub_group(_PERSON, text, reg, "PERSON", group=1)
    text = _sub_group(_SIGNATURE, text, reg, "PERSON", group=1)
    # Einmal erkannte Personennamen auch an Stellen ohne Hinweiswort ersetzen.
    for placeholder, value in list(reg.mapping.items()):
        if placeholder.startswith("[PERSON_") and len(value) >= 5:
            text = text.replace(value, placeholder)
    text = _PHONE.sub(
        lambda m: m.group(0).replace(m.group(1) or m.group(2), reg.token("TELEFON", (m.group(1) or m.group(2)).strip())),
        text,
    )

    payload = PseudonymizedPayload(
        text=text,
        industry_code=client.industry_code,
        chart_of_accounts=client.chart_of_accounts,
        allowed_accounts=allowed_accounts,
        _token=_TOKEN,
    )
    return PseudonymizationResult(payload=payload, mapping=reg.mapping)
