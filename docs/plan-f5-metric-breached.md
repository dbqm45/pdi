# Plan kroku F5 — `metric.breached` z tf jako nowy problem (pdi)

Stan: 2026-10-26. Domknięcie pętli „utrzymanie → nowy problem” z planu jednego flow (F5: „tf: pasma kontrolne na
metrykach z ShipScope → nowy PRB”; tabela zdarzeń: `metric.breached` tf → pdi, „nowy PRB z diagnozą”). tf wysyła
zdarzenie od dbqm45/tf#81 (`metric_watch.py check --send`); dotąd pdi przyjmowało od tf tylko `gate.requested` i
odpowiadało 400.

## Co
- `ACCEPTED["tf"]` dostaje `metric.breached`. Zdarzenie otwiera pozycję skrzynki `kind: problem` (ID = ID zdarzenia,
  więc codzienne `tf-metric-<metryka>-<dzień>` nie dubluje pozycji): podsumowanie z metryką, wartością, progiem,
  oknem i usługą, `metric` = treść zdarzenia, `change` tylko gdy tf go podał. Stanu żadnej zmiany nie zmienia.
- `decide_inbox_item` dla problemu wymaga `outcome`: `accepted` (to jest nowe zgłoszenie) albo `rejected`. Decyzja:
  `kind: triage`, tagi `metric-breached`, `problem:<wynik>`, `metric:<nazwa>`, odczyt pasma jako dowód
  (`observation`), `links.chg` tylko dla problemu ze zmianą, `links.prb` z szkicu, gdy człowiek założył zgłoszenie.
- Rejestr zgłoszeń (PRB) w pdi to F3 i ten krok go nie buduje: przyjęcie zapisuje decyzję z triażu, a klucz PRB
  podaje człowiek.

## Testy (najpierw czerwone)
`tests/test_inbox.py`: pozycja problemu (bez zmiany, ze zmianą), duplikat, decyzja z triażu z dowodem i tagami,
wymagany `outcome`, `links.chg` innej zmiany odrzucone, ShipScope nie może wysłać `metric.breached`.
`tests/test_receiver.py`: `POST /events/tf` z `metric.breached` → 202. `tests/test_mcp_server.py`: triaż przez narzędzie.

## Wynik (2026-10-26)
- 6 testów czerwonych przed kodem (400 jak dotąd), potem cały `pytest` 479/479, `ruff check`, `ruff format --check`,
  `mypy` (strict) czyste.
- Razem z tf (main po dbqm45/tf#81): `metric_watch.py check --csv … --send` do lokalnego `pdi-receiver` → 202 i
  pozycja `kind: problem` w skrzynce; zły sekret → 401.
