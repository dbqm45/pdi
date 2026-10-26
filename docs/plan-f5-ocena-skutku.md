# Plan kroku F5 — ocena skutku decyzji (pdi)

Stan: 2026-10-26. Krok z planu jednego flow (`docs/plan-jeden-flow-sdlc.md` §6, F5: „pdi: … ocena skutku decyzji”,
moduł „Ocena skutku”: po wydaniu i N dniach porównuje metrykę sukcesu z intencji z danymi; AI zbiera dane i
szkicuje wniosek, człowiek potwierdza wynik). Dane czyta z API usług ShipScope (dbqm45/evdt-service-shipscope#110).

## Co się zmienia
Do teraz `feature.released` z `release: R1` od razu otwierał w skrzynce pozycję „ocena skutku”, bez danych i bez
porównania z metryką. Teraz:

1. **Termin.** `feature.released` R1 tylko planuje ocenę: w stanie zmiany `impact_review = { status: scheduled,
   due, basis, intent, released_at }`. Decyzja o intencji to najnowsza zapisana (`status: recorded`) decyzja z
   `links.chg` tej zmiany i z `success_metric` (najpierw `kind: intent`). Termin:
   - `review_by` tej decyzji, gdy nie wcześniejszy niż dzień wydania (`basis: review_by`);
   - inaczej dzień wydania + `success_metric.horizon` („30 dni”, „30d”, „4 tygodnie”, „2 miesiące”, `P30D`;
     miesiąc = 30 dni) (`basis: horizon`);
   - inaczej 30 dni (`basis: default`).
   Odpowiedź na zdarzenie: `scheduled` (HTTP 200, bez pozycji).
2. **Otwarcie.** `pdi-impact-review` (polecenie do crona, raz dziennie) i narzędzie MCP `open_due_impact_reviews`
   otwierają pozycje, których termin minął: pdi czyta z ShipScope (`PDI_SHIPSCOPE_URL`, `PDI_SHIPSCOPE_TOKEN` —
   token usługi `shps_…` z Settings → General) status zmiany (`GET /api/service/v1/items/<CHG>`) i dzienny szereg
   PROD od dnia wydania do dziś (`GET /api/service/v1/metrics`, najwyżej 400 dni), i szkicuje wniosek
   (`draft: { verdict, reason, observed }`):
   - metryka z ShipScope (`deployments`, `failed_deployments`, `rollbacks` — suma w oknie; `lead_time_days_median`
     — mediana median dziennych) z celem z porównaniem (`<= 1`, `< 5`, `>= 10`, `≤`, `≥`, `=`) → `met` / `not_met`;
   - każda inna metryka, cel bez porównania, brak decyzji o intencji, brak danych albo błąd ShipScope → `unknown`
     z powodem (pdi niczego nie zgaduje; człowiek ocenia sam).
   Brak konfiguracji ShipScope nie blokuje otwarcia: pozycja ma wtedy `unknown` i błąd w `data.errors`. Token nigdy
   nie trafia do pozycji, stanu ani logu.
3. **Zamknięcie.** `decide_inbox_item` dla oceny skutku wymaga `outcome`: `met`, `not_met` albo `unknown` — to
   potwierdzenie człowieka, może różnić się od szkicu. Decyzja (`kind: product`, „lekcja”) dostaje `links.chg`,
   tagi `mvp-impact` i `impact:<outcome>`, w `dependencies` ID decyzji o intencji, a w `evidence` odczyty z ShipScope
   (`epistemic_status: observation`). Stan zmiany: `impact_review.status = decided`, `outcome`, `decision`; zmiana
   `done`.

Pozycje otwarte przed tym krokiem (bez `draft`) zamyka się tak samo, z `outcome`.

## Elementy
`src/pdi/impact.py` (czyste reguły: decyzja o intencji, termin, horyzont, szkic wniosku; odczyt ShipScope;
`main()`), `src/pdi/inbox.py` (`receive` planuje, `open_due_reviews()`, `decide` z `outcome` oceny), `src/pdi/flow.py`
(`impact_scheduled`, `impact_opened`, `impact_reviewed` z wynikiem), `src/pdi/mcp_server.py` (narzędzie
`open_due_impact_reviews`, `outcome` oceny), `pyproject.toml` (`pdi-impact-review`), README.

## Testy (najpierw czerwone)
`tests/test_impact.py`: horyzont (formy, nieczytelny → None), termin (review_by, horizon, default, review_by przed
wydaniem), wybór decyzji o intencji (intent przed product, superseded pominięta, bez metryki pominięta), szkic
(`rollbacks <= 1` met / not_met, lead time, metryka spoza ShipScope, cel bez porównania, błąd danych), odczyt
ShipScope (nagłówek Bearer, okno od dnia wydania, 401 → błąd bez tokenu, brak konfiguracji). `tests/test_inbox.py`:
R1 planuje zamiast otwierać, `open_due_reviews` przed terminem nic, po terminie otwiera raz, decyzja wymaga
`outcome` oceny i dostaje dowody, zależność i tagi. `tests/test_mcp_server.py`: nowe narzędzie.

## Wynik (2026-10-26)
- Najpierw czerwone (`tests/test_impact.py`, nowe przypadki w `test_inbox.py`, `test_flow.py`, `test_receiver.py`,
  `test_mcp_server.py`), potem kod; cały `pytest` 460/460, `ruff check`, `ruff format --check`, `mypy` (strict) czyste.
- Zmiana zachowania: `feature.released` R1 nie otwiera już pozycji od razu (odpowiedź `scheduled`), pozycja ma ID
  `impact-<CHG>-R1`, a zamknięcie oceny wymaga `outcome`.
- Odczyt ShipScope sprawdzony na atrapie zgodnej z `server/routes/service.js` (dbqm45/evdt-service-shipscope#110),
  nie na działającym ShipScope.
