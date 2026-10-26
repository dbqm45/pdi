# Plan realizacji: kontrakt 0.6.0 — schemat rekomendacji triażu (F3, strona kontraktu)

**Data:** 2026-10-26 · **Źródło:** [plan jednego flow §5](plan-jeden-flow-sdlc.md) (wiersz „`proc-issue-triage`
na wejściu z pdi — wyjście: rekomendacja według schematu”, F3); tf `docs/plans/2026-10-26-f3-triaz-prb.md` (schemat
zdefiniowany w tf jako propozycja do kontraktu, `triage_pdi.py recommend`).

**Stan:** zrealizowany 2026-10-26 — kontrakt 0.6.0, 621 testów, ruff, mypy.

## Zakres
Schemat `triage-recommendation.schema.json` przechodzi z tf do kontraktu pdi: rekomendacja triażu zgłoszenia `PRB`,
którą tf (albo inny wykonawca triażu) składa dla pdi. Stan i pola jak w `problem.schema.json` (R7), żeby pdi
przepisało je do zgłoszenia bez tłumaczenia; `tf_state` z tabeli mapowania w `contract/README.md`. Decyzję
podejmuje człowiek w pdi (triaż jest typem chronionym, poziom 3). Wersja kontraktu 0.6.0.

## Ustalenia do kodu
- **Pola bez zmian względem tf** (tf `modes/mode-pdi/.../triage-recommendation.schema.json`), żeby tf mógł zastąpić
  własną definicję kopią z kontraktu bez zmiany wyjścia `triage_pdi.py`. Zmieniają się tylko `$id`, `title`
  i `description` (styl kontraktu); warunki `if` dostają `required` jak w `problem.schema.json`.
- **Spójność wewnątrz kontraktu pilnowana testem:** stany rekomendacji ⊂ stany zgłoszenia (bez `new`
  i `ready_for_triage` — to stany wejścia); `rejection_reason`, `category`, `epistemic_status` dowodów = te same
  listy co w zgłoszeniu; `tf_state` zgodny z tabelą mapowania (clarifying → `needs-info`, rejected i duplicate →
  `wontfix`, parked → `needs-triage` z etykietą `deferred`, accepted → `ready-for-agent` / `ready-for-human`).
- **`accepted` bez `change`:** zmianę tworzy pdi po decyzji, więc rekomendacja wymaga `brief` i `executor`, nie
  `change` (inaczej niż zgłoszenie w stanie `accepted`). `tf_state` wynika z wykonawcy: `agent` → `ready-for-agent`,
  `human` → `ready-for-human` (tf już tak składa rekomendację; schemat tf tego nie wymuszał).
- **Wersja 0.6.0:** nowy schemat to nowa możliwość zgodna wstecz; w 0.x kontrakt podnosi drugą liczbę także przy
  dodaniu (jak 0.4.0 i 0.5.0). Tytuły schematów i `contract_version` w przykładach zdarzeń → 0.6.0; zdarzenia
  z 0.4.0 i 0.5.0 dalej przechodzą (wzorzec, nie lista wersji).
- **Bez zmian w kodzie pdi poza `pdi.contract`:** przyjmowanie rekomendacji od tf (np. szkic triażu z rekomendacji)
  to osobny krok, gdy tf zacznie ją wysyłać.

## Kolejność (TDD)
1. Testy (`tests/test_contract.py`): schemat `triage_recommendation` znany i poprawny (2020-12), przykład przechodzi,
   wymagane pola per stan (clarifying bez pytań, accepted bez briefu albo wykonawcy, rejected bez powodu albo
   z powodem spoza listy, `out_of_scope_recorded` bez pliku, parked bez progu, duplicate bez oryginału, stan wejścia
   `new`, stan tf niezgodny z mapowaniem) → błąd; spójność list ze zgłoszeniem; wersja 0.6.0.
2. Schemat, przykład `examples/triage-recommendation.json`, `SCHEMA_NAMES`, `contract.json`, tytuły i przykłady
   zdarzeń.
3. README kontraktu (tabela plików, historia, sekcja mapowania), status tego planu.

Bramka: `uv run pytest`, `ruff check src tests`, `ruff format --check src tests`, `mypy src`.

Strona tf (osobny PR w tf): kopia schematu z kontraktu obok `triage_pdi.py` i w `tests/fixtures/pdi-contract/`
z testem zgodności, `contract_version` rekomendacji 0.6.0.
