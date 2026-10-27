"""Tabela ramek z `design.md` zmiany (kontrakt 0.9.0, etap 07 Design, F6): parser referencyjny.

Format opisuje `contract/contract.json` → `conventions.design`; wynik ma kształt `design-links.schema.json`.
tf i ci_for_sdlc mają własne parsery sprawdzane tym samym wzorcem (`examples/design.md` ↔ `examples/design-links.json`).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from pdi import contract

_FIGMA_PATH = re.compile(r"^/(design|file|proto)/([A-Za-z0-9]+)(/|$)")
_NODE = re.compile(r"^([0-9]+)[-:]([0-9]+)$")


class DesignFormatError(ValueError):
    """Tabela ramek niezgodna z kontraktem; komunikat podaje numer wiersza tabeli (od 1)."""


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _frame(url: str, row: int) -> dict[str, str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    match = _FIGMA_PATH.match(parsed.path)
    if parsed.scheme != "https" or host not in ("figma.com", "www.figma.com") or not match:
        raise DesignFormatError(f"wiersz {row}: link do ramki musi prowadzić do pliku w figma.com")
    node = unquote((parse_qs(parsed.query).get("node-id") or [""])[0])
    node_match = _NODE.match(node)
    if not node_match:
        raise DesignFormatError(f"wiersz {row}: link do ramki bez node-id (ramka, nie cały plik)")
    return {"file_key": match.group(2), "node_id": f"{node_match.group(1)}:{node_match.group(2)}", "url": url}


def parse_design_md(text: str) -> dict[str, Any]:
    """Pierwsza tabela z nagłówkiem z kontraktu → `{"rows": [...]}`; błąd formatu → `DesignFormatError`."""
    conv = contract.settings()["conventions"]["design"]
    headers = [[h.lower() for h in cols] for cols in conv["columns"].values()]
    missing = {v.lower() for v in conv["missing"]}
    not_applicable = {v.lower() for v in conv["not_applicable"]}
    requirement = re.compile(conv["requirement_pattern"])
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("|") and [c.lower() for c in _cells(ln)] in headers),
        None,
    )
    if start is None:
        raise DesignFormatError("brak tabeli ramek (nagłówek: " + " | ".join(conv["columns"]["pl"]) + ")")
    rows: list[dict[str, Any]] = []
    for line in lines[start + 2 :]:
        if not line.strip().startswith("|"):
            break
        n = len(rows) + 1
        cells = _cells(line)
        if len(cells) != 5:
            raise DesignFormatError(f"wiersz {n}: oczekiwano 5 kolumn, jest {len(cells)}")
        req, journey, state, frame, note = cells
        if not requirement.match(req):
            raise DesignFormatError(f"wiersz {n}: identyfikator wymagania '{req}' (np. US-3 albo US-3/AC-2)")
        if not journey:
            raise DesignFormatError(f"wiersz {n}: pusta ścieżka")
        if state not in conv["states"]:
            raise DesignFormatError(f"wiersz {n}: nieznany stan '{state}' (lista w conventions.design.states)")
        row: dict[str, Any] = {"requirement": req, "journey": journey, "state": state}
        if frame.lower() in missing | not_applicable:
            row["status"] = "missing" if frame.lower() in missing else "not_applicable"
            if not note:
                raise DesignFormatError(f"wiersz {n}: '{frame}' wymaga uwagi z powodem albo pytaniem")
        else:
            row["status"] = "linked"
            row["frame"] = _frame(frame, n)
        if note:
            row["note"] = note
        rows.append(row)
    return {"rows": rows}
