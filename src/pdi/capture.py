"""Szkice decyzji z wątków Slacka i transkrypcji spotkań (A5; plan docs/plan-a5-decyzje-z-rozmow.md).

Szkice wyciąga model w rozmowie z człowiekiem; pdi sprawdza, że każdy cytat naprawdę jest w tekście (dokument 14, W4:
szkic jest uczciwy), i robi z kandydatur pozycje skrzynki `kind: capture`. Tekstu rozmowy pdi nie zapisuje — tylko
cytaty i link do źródła.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from pdi.registry import Decision, InvalidDecision

SOURCE_KINDS = ("slack", "meeting")
MAX_TEXT = 200_000
MIN_QUOTE = 10
MAX_QUOTES = 5
CANDIDATE_FIELDS = ("statement", "why", "quotes", "kind", "decided_by", "decided_at", "change", "tags")
_QUOTE_MARKS = str.maketrans({c: '"' for c in "„”“«»‟″"} | {c: "'" for c in "‘’‚‛′"})
_SPACE = re.compile(r"\s+")
_CHANGE = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")


def normalize(text: str) -> str:
    """Białe znaki do jednej spacji, cudzysłowy i apostrofy do prostych."""
    return _SPACE.sub(" ", text.translate(_QUOTE_MARKS)).strip()


def quote_problem(quote: str, text: str) -> str | None:
    """Powód, dla którego cytat się nie nadaje, albo None."""
    q = normalize(quote)
    if len(q) < MIN_QUOTE:
        return f"cytat „{quote}” jest za krótki (najmniej {MIN_QUOTE} znaków)"
    if q not in normalize(text):
        return f"cytatu „{quote}” nie ma w tekście rozmowy"
    return None


def check_source(source: dict[str, Any], text: str) -> None:
    if source.get("kind") not in SOURCE_KINDS:
        raise InvalidDecision(f"source.kind: {' albo '.join(SOURCE_KINDS)}.")
    if not str(source.get("url") or "").strip():
        raise InvalidDecision(
            "source.url: podaj link do wątku, nagrania albo pliku — decyzja bez źródła jest bezużyteczna."
        )
    if not text.strip():
        raise InvalidDecision("Brak tekstu rozmowy: wklej wątek albo transkrypcję.")
    if len(text) > MAX_TEXT:
        raise InvalidDecision("Tekst rozmowy dłuższy niż 200 000 znaków — podziel go na części.")


def candidate_problem(candidate: dict[str, Any], text: str) -> str | None:
    """Powód odrzucenia kandydatury albo None."""
    for field in ("statement", "why"):
        if not str(candidate.get(field) or "").strip():
            return f"brak {field}"
    quotes = candidate.get("quotes") or []
    if not quotes:
        return "brak cytatu z rozmowy — szkic bez cytatu nie trafia do skrzynki"
    if len(quotes) > MAX_QUOTES:
        return f"najwyżej {MAX_QUOTES} cytatów"
    change = candidate.get("change")
    if change and not _CHANGE.match(str(change)):
        return f"change: {change} nie jest kluczem zmiany (np. CHG-12)"
    for quote in quotes:
        problem = quote_problem(str(quote), text)
        if problem:
            return problem
    return None


def item_id(source: dict[str, Any], candidate: dict[str, Any], day: str) -> str:
    digest = hashlib.sha256(f"{source['url']}\n{normalize(candidate['statement'])}".encode()).hexdigest()[:8]
    return f"capture-{day.replace('-', '')}-{digest}"


def item(source: dict[str, Any], candidate: dict[str, Any], *, item_id: str, at: str) -> dict[str, Any]:
    draft = {k: candidate[k] for k in CANDIDATE_FIELDS if candidate.get(k) not in (None, "", [])}
    return {
        "id": item_id,
        "kind": "capture",
        "status": "open",
        "change": draft.pop("change", None),
        "source": {k: source[k] for k in ("kind", "url", "title") if source.get(k)},
        "summary": f"Szkic decyzji z rozmowy ({source['kind']}): {candidate['statement']}",
        "received_at": at,
        "draft": draft,
    }


def decision_fields(item: dict[str, Any], draft: Decision) -> Decision:
    """Pola decyzji z zatwierdzonego szkicu: źródło i cytaty z pozycji, poprawka liczona, gdy jej nie podano."""
    proposal = item["draft"]
    quotes = proposal["quotes"]
    source = item["source"]
    fields: Decision = {
        "source": {"kind": source["kind"], "url": source["url"], "excerpt": " … ".join(quotes)},
        "evidence": [
            *(draft.get("evidence") or []),
            *({"text": q, "source_url": source["url"], "epistemic_status": "observation"} for q in quotes),
        ],
        "drafted_by": "ai",
        "kind": proposal.get("kind", "other"),
    }
    if "draft_edited" not in draft:
        fields["draft_edited"] = any(normalize(draft[k]) != normalize(proposal[k]) for k in ("statement", "why"))
    for key in ("decided_by", "decided_at"):
        if key in proposal and key not in draft:
            fields[key] = proposal[key]
    return fields
