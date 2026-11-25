# DV7 — rozwiązanie bez kodu w triażu (Build vs. Don't Build)

Stan: 2026-11-25. Krok DV7 z `docs/plan-budowy-suity.md` §3d.

## Cel
Część zgłoszeń da się rozwiązać bez developmentu: zmianą konfiguracji, zmianą procesu albo istniejącą funkcją,
o której zgłaszający nie wie. Triaż ma to rozważyć przed „accepted” i zapisać jako osobny, mierzalny wynik, a nie
ginąć w „other” albo „already_exists”.

## Ustalenia
1. **Kontrakt 0.24.0** (zgodnie wstecz): nowy powód odrzucenia `no_code` w `problem.schema.json`
   i `triage-recommendation.schema.json` oraz obiekt `no_code` (`kind`: `configuration` / `process_change` /
   `existing_feature`, `how`: co zrobić, żeby problem zniknął), wymagany przy `rejection_reason: no_code`.
   `tools/check_contract.py` pilnuje, że oba schematy mają te same powody i ten sam `no_code`.
2. **tf** (`triage_pdi.py recommend`): `--no-code KIND --how TEXT` składa rekomendację `rejected` z powodem
   `no_code`; skill triażu każe rozważyć rozwiązanie bez kodu, zanim zarekomenduje `accepted`.
3. **pdi:** decyzja triażu przyjmuje `no_code`, zgłoszenie zapisuje je obok powodu; wiadomość do zgłaszającego
   podaje, co zrobić (`how`); decyzja triażu dostaje znacznik `bez-kodu`, więc takie zgłoszenia da się policzyć
   (`find_decisions(tags=["bez-kodu"])`); w konsoli powód „bez kodu” z rodzajem i opisem.

## Kolejność (TDD)
1. di-contract: sprawdzenie w `check_contract.py`, schematy, przykład, README; PR, tag `contract-v0.24.0`.
2. pdi: testy (czerwone) `tests/test_no_code.py` — zapis `no_code`, walidacja, wiadomość, MCP, konsola; kod; bramki.
3. tf: testy `recommend --no-code`; kod; skill; bramki.
