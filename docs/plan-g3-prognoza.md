# Plan — prognoza zmiany i jej kalibracja (G3, krok 2)

Stan: 2026-10-27, **zrobione** (pdi #37). Luka G3 po decyzji D-E1 (25.10): prognozę „kiedy to będzie” liczy automat z liczby cięć planu tf
i historycznego czasu przepływu z ShipScope, a ludzie głosują tylko wtedy, gdy automat zgłasza wątpliwość. Krok 1
(dbqm45/evdt-service-shipscope#119) dał `GET /api/service/v1/flow`. Ten krok liczy prognozę w pdi, zapisuje ją
w stanie zmiany i po dostarczeniu porównuje z wynikiem. Pokazanie prognozy w pokoju sprintdecka przyjdzie po MVP
sprintdecka.

## Model (`pdi.forecast`, czyste reguły)
- **Historia:** zmiany dostarczone w ostatnich 180 dniach (`/flow`, `changes`: `tasks`, `flowDays`). Dla każdej
  tempo na cięcie = `flowDays / tasks`. Cięcia jednej zmiany idą częściowo równolegle, więc to tempo jest
  uczciwsze niż czas przepływu pojedynczego elementu.
- **Prognoza:** `tasks × mediana tempa`, przedział `tasks × P25` … `tasks × P75` (dni, jedna cyfra po przecinku).
  Bez dostarczonych zmian, a z elementami: `tasks × mediana czasu elementu`, podstawa `items` (górne oszacowanie,
  jakby cięcia szły jedno po drugim). Bez żadnej historii: brak liczby, tylko wątpliwość.
- **Wątpliwości** (D-E1 pkt 2, powód do głosu ludzi): mniej niż 5 dostarczonych zmian w historii; więcej cięć niż
  w największej zmianie z historii; podstawa `items`; brak historii.
- **Porównanie:** po dostarczeniu `actual_days` (z `/flow`), `ratio = actual / expected` i `within_range`.
- **Kalibracja:** po zmianach z prognozą i wynikiem: liczba, mediana `ratio`, odsetek w przedziale.

## Kiedy
- **Prognoza** powstaje przy decyzji `approved` na bramce `approve-for-implementation` (baseline planu): liczba cięć
  to `tasks` zmiany z `GET /api/service/v1/changes` (ShipScope pomija już `dropped`). Gdy ShipScope jeszcze nie zna
  cięć (plan nie trafił na gałąź domyślną) albo odczyt się nie udał, stan dostaje `forecast.status: failed` z powodem,
  a decyzja na bramce i tak się zapisuje. Bez `PDI_SHIPSCOPE_URL` prognozy nie ma.
- **Wynik:** po każdym `feature.released` tej zmiany i z `pdi-forecast` (cron, raz dziennie): czytany jest `/flow`
  od dnia prognozy; gdy zmiana jest wśród dostarczonych, prognoza dostaje `actual`. Ten sam przebieg uzupełnia
  nieudane prognozy, póki zmiana nie ma wyniku.
- **Claude (MCP):** `forecast_change(change)` liczy prognozę od nowa (np. po poprawie planu), `forecast_report()`
  pokazuje kalibrację i zmiany z prognozą. `pdi-stats` wypisuje kalibrację.

## Testy (najpierw czerwone)
`tests/test_forecast.py`: tempo i kwartyle, podstawa `items`, brak historii, wątpliwości, porównanie, kalibracja,
odczyt z ShipScope (adresy, token, zły kształt, błąd bez tokenu). `tests/test_inbox.py`: prognoza po
`approve-for-implementation`, nieudana prognoza nie blokuje decyzji, wynik po `feature.released`, przebieg
dzienny. `tests/test_mcp_server.py`: nowe narzędzia. `tests/test_stats.py`: kalibracja w podsumowaniu.
