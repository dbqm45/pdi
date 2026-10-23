# Plan realizacji: krok 1 pdi standalone

**Data:** 2026-10-23 · **Specyfikacja:** [dokument 14 §4](14-pdi-standalone.md#4-pierwszy-krok-mvp--specyfikacja) · **Decyzje:** D1, D-S1–S3 ([decyzje](decyzje.md))

**Stan:** zrealizowany 2026-10-23 — 53 testy (z `pdi-stats`), ruff, mypy `--strict`; testy przechodzą też na Pythonie 3.11.
Sprawdzenie ręczne: serwer uruchomiony poleceniem z instrukcji (`uv run --directory … pdi-mcp`) przez klienta MCP —
zapis i wyszukiwanie działają. Instalacja u właściciela i próbny zapis przez `/record-decision` — działa (2026-10-23).

## Zakres

Schemat decyzji, rejestr w plikach markdown, serwer MCP (stdio) z czterema narzędziami, komenda `/record-decision`
i instrukcja instalacji w Claude Code. Bez Slacka, bez usługi HTTP, bez UI.

## Pliki

| Plik | Zawartość |
|---|---|
| `contract/decision.schema.json` | JSON Schema 2020-12, wersja kontraktu 0.1.0 |
| `pyproject.toml`, `uv.lock` | pakiet `pdi` (src layout), Python ≥ 3.11; zależności: `mcp` 2.x, `pyyaml`, `jsonschema`; dev: `pytest`, `ruff`, `mypy` |
| `src/pdi/registry.py` | rejestr: `record`, `get`, `find`, `supersede`; zapis `decisions/DEC-nnnn.md` (frontmatter YAML = źródło prawdy, treść = widok dla człowieka); walidacja schematem; commit, jeśli rejestr jest repo git |
| `src/pdi/mcp_server.py` | serwer MCP `pdi`: `record_decision`, `find_decisions`, `get_decision`, `supersede_decision`; błędy z podpowiedzią naprawy |
| `integrations/claude-code/` | komenda `/record-decision`, fragment `CLAUDE.md` do odczytu (§4.5), instrukcja instalacji |
| `tests/` | testy schematu, rejestru i serwera MCP |

## Kontrakt rejestru (ustalenia do kodu)

- Pola nadawane przez rejestr: `id` (`DEC-0001`…, kolejny numer), `status: recorded`, `recorded_at` (UTC).
  `recorded_at` to **dodatek do pól z §4.1** — znacznik zapisu potrzebny do pomiarów W1–W2.
- Domyślne: `decided_at` = dzisiejsza data; `decided_by` = zmienna `PDI_DECIDED_BY`. Brak obu → błąd z podpowiedzią.
- Konfiguracja: `PDI_REGISTRY_PATH` (katalog rejestru). W testach zawsze `tmp_path`.
- Ponowienie tego samego zapisu (ta sama treść decyzji, źródło i data) zwraca istniejący wpis zamiast duplikatu.
- `supersede`: tylko decyzja o statusie `recorded`; nowa dostaje `supersedes`, stara `status: superseded` i `superseded_by`.
- Wyszukiwanie: dopasowanie słów zapytania (bez rozróżniania wielkości liter, także jako fragment słowa) w treści,
  uzasadnieniu, opcjach, założeniach, zależnościach i tagach; filtry `tags`, `since`, `status`, `kind`; limit.

## Kolejność (TDD: test czerwony → kod → zielony)

1. Schemat: poprawna decyzja przechodzi; brak pól wymaganych, zły `kind` i `epistemic_status`, nieznane pole → błąd.
2. Rejestr: zapis i odczyt, numeracja, wartości domyślne, błędy walidacji, duplikat, wyszukiwanie i filtry,
   zastępowanie, commit w repo git.
3. Serwer MCP: lista narzędzi, zapis i wyszukiwanie przez `call_tool`, błąd z podpowiedzią, brak `PDI_REGISTRY_PATH`.
4. Integracja z Claude Code: komenda i instrukcja; test uruchomienia serwera przez stdio (`initialize` + `tools/list`).

Bramka: `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict src`.

## Poza zakresem kroku 1

Sprawdzenie samej komendy `/record-decision` (jakość szkicu) odbywa się w walidacji na sobie (§6, W2 i W4) — to prompt,
nie kod; w kroku 1 sprawdzamy tylko, że narzędzia działają.
