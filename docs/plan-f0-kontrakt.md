# Plan realizacji: F0 — pozostałe schematy kontraktu

**Data:** 2026-10-23 · **Źródła:** [plan jednego flow §3](plan-jeden-flow-sdlc.md#3-wspólny-kontrakt-zrobić-najpierw), [dokument 13 R7](13-rola-pdi-w-sdlc.md#4-rozbieżności-między-wersjami-mapy-i-planem--do-rozstrzygnięcia), [dokument 12 §4.2](12-zmiana-kierunku-sdlc.md#42-nowe-zdarzenie-w-kontrakcie), [decyzje D1, D3](decyzje.md); nagłówek artefaktu z tf `core-project-record`

**Stan:** zrealizowany 2026-10-23 — kontrakt 0.3.0, 120 testów (w tym 51 dla kontraktu), ruff, mypy `--strict`.
R7 i `decision.basis_invalidated` przyjęte 2026-10-23 ([decyzje](decyzje.md)).

## Zakres

Kontrakt 0.3.0 w `contract/`:

| Plik | Co opisuje | Gdzie żyje obiekt |
|---|---|---|
| `contract.json` | wersja kontraktu, wzorzec klucza (kształt Jiry) i domyślne prefiksy `PRB`, `CHG`, `TSK`, `DEC` (D3: konfigurowalne) | — |
| `problem.schema.json` | zgłoszenie `PRB`: „kto nie może czego → skutek”, kanał, stan triażu, powód odrzucenia, próg powrotu, duplikat | baza pdi |
| `change.schema.json` | nagłówek YAML artefaktu w `changes/CHG-n/*.md` — nagłówek tf (`artifact`, `phase`, `status`, `version`, `author`, `created`, `updated`, `inputs`) + `change`, `source`, `tasks` | repo zmiany |
| `task.schema.json` | cięcie `TSK` z rodzicem `CHG` (wymiana między pdi, tf i ShipScope) | `plan.md` zmiany |
| `event.schema.json` | koperta zdarzenia + treść dla każdego typu z planu i `decision.basis_invalidated` | wymiana między projektami |
| `decision.schema.json` | bez zmian w polach; ID według wspólnego wzorca klucza zamiast stałego `DEC-` | rejestr |
| `examples/` | poprawny przykład dla każdego schematu i każdego typu zdarzenia | — |

## Ustalenia do kodu

- Stany zgłoszenia według **R7 (przyjęte 2026-10-23; tf bez zmian, tłumaczenie na granicy)** (`new`, `clarifying`, `ready_for_triage`, `accepted`, `rejected`,
  `parked`, `duplicate`) z mapowaniem na stany tf `proc-issue-triage` w `contract/README.md`.
- Warunki: `rejected` wymaga powodu z listy; `parked` — progu powrotu; `duplicate` — `duplicate_of`; `accepted` —
  `change`.
- `decision.basis_invalidated` z dokumentu 12 §4.2 wchodzi do kontraktu (przyjęte, D-Z1; używane dopiero w F5).
- Nagłówek artefaktu zmiany zostaje „prostym YAML” jak w tf (`klucz: wartość`, `klucz: [a, b]`) — bez obiektów
  zagnieżdżonych, żeby parser tf go czytał; szczegóły cięć w treści `plan.md`, w nagłówku tylko lista `tasks`.
- `contract_version` w każdym zdarzeniu (jak `schemaVersion` w ShipScope) — odbiorca przypina wersję.

## Kolejność (TDD)

1. Testy: każdy schemat jest poprawnym JSON Schema 2020-12; każdy przykład z `examples/` przechodzi; przypadki
   niepoprawne (brak pól, warunki stanów, zły typ zdarzenia, treść niepasująca do typu) są odrzucane.
2. Schematy i przykłady.
3. `pdi.contract` — jedno miejsce ładowania schematów; rejestr decyzji korzysta z niego.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src`.
