# Plan kroku F5 — graf śladu (pdi)

Stan: 2026-10-26. Krok z planu jednego flow (`docs/plan-jeden-flow-sdlc.md` §6, F5: „pdi: … graf śladu”; moduł
„Graf śladu”: PRB → CHG → TSK → PR → wdrożenie → wydanie → skutek, z danymi z repo, ci_for_sdlc i ShipScope; rola:
podgląd). Po ocenie skutku (pdi #18) pdi ma wszystkie ogniwa poza wdrożeniem; to czyta z API usług ShipScope
(dbqm45/evdt-service-shipscope#110).

## Co
Narzędzie MCP `get_trace(change, live=true)` i funkcja `pdi.trace.trace()` składają graf jednej zmiany z tego, co pdi
już ma, bez nowego zapisu:

| Węzeł | Skąd |
|---|---|
| `PRB-n` (problem) | `links.prb` decyzji o tej zmianie |
| `CHG-n` (zmiana) | `changes/<CHG>.yaml`: status, gotowość, rozjazd z baseline |
| bramka (`gate:B1`, `gate:stage:<flaga>:<etap>`) | zatwierdzone i oczekujące w stanie zmiany, pozycje skrzynki (otwarte, odrzucone) |
| decyzja (`DEC-nnnn`) | rejestr: decyzje z `links.chg` tej zmiany |
| `TSK-n` (cięcie) | `links.tsk` decyzji i zadania z `feature.released` (`tasks`, od teraz zapisywane w stanie: `release_tasks`) |
| PR | `links.pr` decyzji |
| środowisko (`env:test`/`qa`/`prod`) | ShipScope `GET /api/service/v1/items/<CHG>`: status jak pill w dashboardzie |
| wydanie (`release:R1`…) | `releases` w stanie zmiany |
| skutek (`impact:R1`) | `impact_review` w stanie zmiany (termin, szkic, wynik, decyzja) |

Krawędzie: problem → zmiana, decyzja → bramka (rozstrzyga) albo decyzja → zmiana (dotyczy), zmiana → bramka, zmiana →
cięcie, cięcie → PR (gdy jedna decyzja łączy oba; inaczej zmiana → PR), zmiana → środowisko, cięcie → wydanie (zadania
z `feature.released`), zmiana → wydanie, wydanie R1 → skutek, decyzja → skutek. Cięcia dostają też status PROD z
ShipScope (najwyżej 20 odczytów na graf).

Wynik: `{ change, nodes, edges, gaps, mermaid }`. `gaps` to luki pokazane, nie naprawiane: brak PRB, brak decyzji o
intencji z metryką sukcesu, brak cięć, brak PR, zmiana wydana bez oceny skutku, błąd albo brak konfiguracji ShipScope.
`mermaid` to `flowchart LR` do wklejenia (etykiety obcięte do 60 znaków, bez cudzysłowów i nowych linii). `live=false`
nie pyta ShipScope. Zmiana, której pdi nie zna ani ze stanu, ani z rejestru, to błąd z podpowiedzią `list_changes`.

## Elementy
`src/pdi/trace.py` (czyste składanie grafu, `mermaid()`), `src/pdi/impact.py` (`read_item()` wspólne z oceną skutku),
`src/pdi/flow.py` (`feature_released` zapisuje `release_tasks`), `src/pdi/inbox.py` (przekazuje `tasks`),
`src/pdi/mcp_server.py` (`get_trace`), README.

## Testy (najpierw czerwone)
`tests/test_trace.py`: pełny przebieg (PRB, intencja, B1, TSK, PR, wydanie R1, ocena skutku) daje oczekiwane węzły i
krawędzie; status środowisk i cięć z atrapy ShipScope; `live=false` nic nie czyta; luki dla gołej zmiany; nieznana
zmiana → błąd; Mermaid z etykietą z cudzysłowem i nową linią; limit odczytów cięć. `tests/test_flow.py`:
`release_tasks`. `tests/test_mcp_server.py`: narzędzie.

## Wynik (2026-10-26)
- Testy napisane przed kodem (`tests/test_trace.py` czerwone bez `trace.py`), potem kod; cały `pytest` 471/471,
  `ruff check`, `ruff format --check`, `mypy` (strict) czyste.
- Odczyt ShipScope sprawdzony na atrapie zgodnej z `GET /api/service/v1/items/:key`, nie na działającym ShipScope.
- Poza zakresem: widok w konsoli i panel w Jirze (K-4 w `plan-automatyzacja-i-konsola.md`), węzeł historyjek US/AC z
  ci_for_sdlc i koszt agentów w grafie — pdi nie trzyma jeszcze tych danych.
