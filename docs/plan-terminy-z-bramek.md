# Terminy i opcja domyślna z bramek (po N2 i N4)

Stan: 2026-11-24. Domyka N2 (di-contract #8, kontrakt 0.19.0) i N4 (tf #420) po stronie pdi. Dziś termin pozycji
skrzynki liczy się tylko z tabeli OM1 (`waiting.business_days`: rodzaj pozycji i bramka), a pdi przypina kontrakt
0.17.0, więc `gate.requested` z nowymi polami 0.19.0 nie przeszedłby walidacji.

## Cel
Bramka niesie swoją odwracalność, termin, opcję domyślną i pytanych; pdi je zapisuje w pozycji, liczy z nich terminy
i pokazuje je w „czeka na Ciebie”.

## Ustalenia
1. **Kontrakt:** przypięcie pdi na 0.19.0 (`tools/contract-pin.json`, `tools/sync_contract.py`).
2. **Pozycja bramki** zapisuje z `gate.requested`: `reversibility`, `closes_at`, `default_option`, `asked`.
3. **Termin:**
   - `closes_at` w przyszłości względem wpływu → termin to `closes_at`; przypomnienie w połowie czasu, „termin dziś”
     na początku dnia terminu, „wstrzymana” po 2 × czasie, „do przeglądu” po 4 × czasie (te same proporcje co OM1);
   - bez `closes_at`: tabela OM1 jak dziś; `reversibility: one_way` na bramce bez własnego terminu w OM1 (wszystkie
     poza B3, B5 i etapem flagi na PROD) daje 5 dni roboczych, jak bramka trudna do cofnięcia w OM1 §3.
4. **„Czeka na Ciebie”:** `due` z tego terminu; do tego `default_option` (gdy jest) i `reversibility`.
5. **Bez zmiany:** bramka nigdy nie zatwierdza się sama (OM1). Opcja domyślna po terminie dalej czeka na człowieka —
   automatyczne przyjęcie decyzji tymczasowej to osobna decyzja właściciela.

## Kolejność (TDD)
1. Testy (czerwone) w `tests/test_waiting.py` i `tests/test_inbox.py`: pola w pozycji; terminy z `closes_at`;
   `one_way` na B1; OM1 bez nowych pól jak dziś; wiadomość z opcją domyślną.
2. Przypięcie kontraktu, kod, potem bramki: `uv run pytest`, ruff, `mypy --strict src`, Python 3.11.
