# Decyzje przypięte do ścieżek (`applies_to`)

Stan: 2026-11-24. Pozycja z `TODO.md` („nic nie łączy decyzji z plikami”). Potrzebne przed DV3 (odtworzenie kontekstu
na start zadania) i regułą PR w ci_for_sdlc.

## Cel
Agent przed planem zmiany pyta rejestr: „które przyjęte decyzje obejmują pliki, które ruszam?” i dostaje je
z uzasadnieniem i założeniami nośnymi. Decyzja mówi, czego dotyczy: wzorce ścieżek w repo i nazwy komponentów.

## Ustalenia
1. **Kontrakt 0.22.0** (di-contract): opcjonalne `applies_to` w decyzji i w `decision.recorded` — obiekt z `paths`
   (wzorce ścieżek względem korzenia repo projektu decyzji) i/lub `components` (nazwy jak `project`). Zgodnie wstecz.
2. **Dopasowanie wzorca** (opisane w `decision-record.md`, przypadki w `contract/fixtures/applies-to/cases.json`,
   wzorcowa implementacja w `tools/check_contract.py`): separator `/`, wzorzec zakotwiczony w korzeniu repo, `*` —
   dowolne znaki w jednym segmencie, `?` — jeden znak, `**` jako cały segment — zero lub więcej segmentów; wzorzec
   pasuje do pliku albo do katalogu, w którym plik leży (`src/pdi` obejmuje `src/pdi/inbox.py`). Wielkość liter ma
   znaczenie. Ścieżka pliku: `\` → `/`, bez wiodącego `./`.
3. **pdi:** `record_decision` przyjmuje `applies_to`; `decision.recorded` przenosi je do rejestru; `find_decisions`
   dostaje `paths` i `components`: zwraca tylko decyzje, których `applies_to` pasuje (domyślnie bez zastąpionych),
   a w skrócie — `applies_to` i `matched` (które ścieżki i komponenty trafiły). Kontrakt przypięty na 0.22.0.
4. **tf:** `decision add --applies-to <wzorzec>` (powtarzalne) i `--component`; `decision pending` przekazuje
   `applies_to` do `record_decision`; skill `pdi-decisions` każe przed planem zmiany wołać `find_decisions(paths=…)`
   dla plików, które zmiana ruszy, i podać w podsumowaniu, które decyzje sprawdził.
5. Poza zakresem: szablon PR „Wpływ na decyzje” i reguła PR w ci_for_sdlc (osobny krok).

## Kolejność (TDD)
1. di-contract: test w `check_contract.py` (przypadki dopasowania, równe pole w decyzji i w `decision.recorded`),
   schemat, przykład, README, `decision-record.md`, `suite.yaml`; PR, tag `contract-v0.22.0`.
2. pdi: testy (czerwone) `tests/test_applies_to.py` — dopasowanie z przypadków kontraktu, `find_decisions` po
   ścieżkach i komponentach, zapis przez `record_decision` i `decision.recorded`; kod; bramki: `uv run pytest`, ruff,
   `mypy --strict src`, Python 3.11.
3. tf: testy `decision add --applies-to`, `pending`; kod; SKILL.md; bramki tf.
