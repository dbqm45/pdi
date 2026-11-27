# G7 — kolejka bramek obok jakości wydań — plan

Stan: 2026-11-27, zrobione i sprawdzone na żywo. Właściciel zlecił zrobić to według rekomendacji. Źródło: `TODO.md`, „Propozycja do G7 „miary
przepływu”: wskaźniki wyprzedzające w parze z opóźnionymi”, punkt „Para z wskaźnikiem opóźnionym z ShipScope”.
Ciąg dalszy DV4 ([plan](plan-dv4-gdzie-zmiana-czeka.md)).

## Co jest dziś (sprawdzone 2026-11-27)

- Strona `/flow` („Przepływ”) i narzędzie MCP `flow_delays`: bramki czekające teraz, mediana i p90 czekania na
  bramkach, czekanie i praca zmian. Wszystko „na teraz”, bez osi czasu.
- ShipScope `GET /api/service/v1/metrics?from&to&format=json` (token usługi `shps_…`): dla każdego dnia UTC na PROD
  `deployments` (tylko udane), `failedDeployments`, `rollbacks` (wśród udanych), mediana czasu realizacji. pdi czyta je już przy ocenie skutku
  (`impact.collect`).
- Zgłoszenia (`problems/<PRB>.yaml`) mają `reported_at`.
- ShipScope nie odróżnia hotfiksu od zwykłego wdrożenia; zgłoszenie nie wskazuje wydania, po którym powstało.

## Decyzje (według rekomendacji)

1. **Oś tygodni:** ostatnie 8 tygodni ISO (poniedziałek–niedziela, UTC), z bieżącym niepełnym na końcu.
2. **Wskaźniki wyprzedzające (pdi):** w tygodniu prośby o bramkę, decyzje, mediana czekania decyzji z tego tygodnia
   i **kolejka na koniec tygodnia** (bramki poproszone, a nierozstrzygnięte; dla bieżącego tygodnia — teraz).
3. **Wskaźniki opóźnione:** z ShipScope wdrożenia, nieudane, rollbacki i **CFR** = (nieudane + rollbacki) /
   (udane + nieudane) (brak, gdy nie było prób); z pdi **nowe zgłoszenia** (PRB) w tygodniu. Hotfiksy i powiązanie PRB
   z wydaniem — poza zakresem, bo dane ich nie niosą (zapisane w `TODO.md`).
4. **Sygnał „przegląd może nie nadążać”:** w ostatnim pełnym tygodniu kolejka na koniec i CFR są wyższe niż w
   poprzednim. Tylko podpowiedź do rozmowy, nie alarm; miary dla systemu, nigdy dla osoby.
5. **Gdzie widać:** sekcja „Kolejka a jakość” na `/flow` i narzędzie MCP `flow_quality`. Bez ShipScope (brak
   ustawień albo błąd) kolumny ShipScope są puste, a strona mówi dlaczego, bez tokenu.
6. Bez zmiany kontraktu i bez nowej zależności.

## Kroki

1. Czerwone testy: `tests/test_quality.py` (tygodnie, kolejka na koniec tygodnia, CFR, PRB, sygnał, bez ShipScope),
   `impact.read_metrics`, strona `/flow`, narzędzie MCP.
2. Kod: `src/pdi/quality.py`, `impact.read_metrics`, `Inbox.prod_metrics`, konsola, MCP.
3. Na żywo: lokalny ShipScope z danymi przykładowymi i konsola pdi.
4. README, instrukcja użytkownika, `TODO.md`.

## Co wyszło przy wdrożeniu (2026-11-27)

- **Jak ShipScope liczy wdrożenia:** `deployments` w `/metrics` to tylko udane, nieudane są osobno w
  `failedDeployments`, a rollback jest udanym wdrożeniem. Pierwsza wersja dzieliła przez `deployments` i na żywo
  dała odsetek ponad 100%. CFR dzieli teraz przez wszystkie próby: (nieudane + rollbacki) / (udane + nieudane).
- **Na żywo** (lokalny ShipScope 0.2.73 połączony z pdi przez `local-pdi.js connect`, wdrożenia PROD wpisane do bazy,
  rejestr pdi z sześcioma zmianami i dwoma zgłoszeniami): w W47 2 udane wdrożenia (w tym rollback) i 1 nieudane, CFR
  67%, kolejka na koniec 3 (tydzień wcześniej 1, CFR 0%). Strona „Przepływ” i `flow_quality` pokazały podpowiedź
  dla W47. Ze złym tokenem: „ShipScope odpowiedział 401 na metryki PROD”, bez tokenu w treści, dane pdi zostają.
- **Poza zakresem:** hotfiksy (ShipScope ich nie odróżnia) i PRB powiązane z wydaniem (zgłoszenie nie wskazuje
  wydania). Dryf specyfikacji jako drugi wskaźnik wyprzedzający — osobna pozycja w `TODO.md`.
