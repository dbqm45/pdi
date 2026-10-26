# Plan realizacji: A0 — kontrakt 0.5.0 (poziomy autonomii)

**Data:** 2026-10-26 · **Źródło:** [plan automatyzacji i konsoli §3–4](plan-automatyzacja-i-konsola.md#3-model-poziomy-autonomii-kontrakt-050) · **Decyzje:** DA1, DA2 ([decyzje](decyzje.md))

**Stan:** zrealizowany 2026-10-26 — kontrakt 0.5.0, 538 testów, ruff, mypy `--strict`.

## Zakres
Jak w planie §3: nowy `autonomy.schema.json` (polityka organizacji), nowe pola decyzji (`decision_type`,
`automation`, `draft_edited`, źródło `console`), cztery zdarzenia (`decision.proposed`, `decision.auto_applied`,
`decision.vetoed`, `run.progress`), wersja 0.5.0 z katalogiem typów decyzji w `contract.json`. Wszystkie nowe pola
są opcjonalne; zdarzenia z `contract_version` 0.4.0 dalej są przyjmowane.

## Ustalenia do kodu (czego plan nie przesądza)
- `decision_type` to klucz z kropkami (`flag.stage_advance`, `triage`): wzorzec, nie lista zamknięta — organizacja może
  dodać własne typy. Znane typy są w katalogu w `contract.json`.
- `automation.level` w decyzji przyjmuje tylko 0–2: decyzja na poziomie 3 to decyzja człowieka i nie ma `automation`.
  Poziom 2 wymaga `veto_until`.
- `draft_edited` ma sens tylko przy szkicu AI: schemat wymaga wtedy `drafted_by: ai`.
- Polityka (`autonomy.schema.json`): poziom 2 wymaga `veto_window` (czas trwania ISO 8601, np. `PT4H`); typy chronione
  z DA2 mają w schemacie wymuszony poziom 3. Ta sama lista jest w katalogu w `contract.json`; test pilnuje zgodności.
- Wartości domyślne progów (DA2: 30 decyzji, 95%; podniesienie przy odsetku poprawek > 10% z planu) są w `contract.json`
  → `autonomy`; polityka organizacji może je nadpisać per typ.
- Zestaw wzorcowy `fixtures/story-shape/` się nie zmienia: zostaje w wersji 0.4.0 (wersja, w której zmienił się
  ostatnio). Test porównuje wersję zestawu z bieżącą wersją kontraktu jako „nie nowsza”, a nie „równa”.
- Rejestr decyzji i serwer MCP bez zmian w tym kroku (zapis `decision_type` i `draft_edited` przez narzędzia to A3).

## Kolejność (TDD)
1. Testy: nowe schematy i pola, przypadki niepoprawne, katalog typów zgodny ze schematem polityki, zgodność wstecz
   (przykłady i zdarzenia 0.4.0 przechodzą).
2. Schematy, `contract.json`, przykłady.
3. `pdi.contract`, README kontraktu, status planu automatyzacji.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
