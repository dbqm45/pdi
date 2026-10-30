# Przebieg lokalny: od zgłoszenia do oceny skutku w jeden dzień

Lista kontrolna §5 [planu `sdlc up`](plan-sdlc-lokalnie.md) na repo próbnym (L5). Przy każdym kroku jest oczekiwany
wynik i miejsce, gdzie go sprawdzić. Legenda:
- **C**: czat Claude w klonie repo próbnego (serwery MCP `pdi` i `shipscope`);
- **SS**: ShipScope w przeglądarce (`http://localhost:3000/`);
- **T**: terminal w klonie pdi.

Skrócenie czasu:
- `review_by` w B1 na jutro;
- etapy flagi z `min_days: 0`;
- ShipScope synchronizuje co minutę, a zdarzenia wydania sprawdza co 5 minut, więc do ok. 6 minut opóźnienia.

## 0. Start

- [ ] **T** `uv run sdlc up` → kończy się „gotowe”. Za pierwszym razem są dwa kroki w przeglądarce: kliknięcie, które
  zakłada aplikację GitHub ShipScope, oraz zalogowanie się i utworzenie przestrzeni.
- [ ] **T** `uv run sdlc sandbox sdlc-proba` → „gotowe”, adres repo i klonu. Za pierwszym razem: SS Settings → GitHub
  → Install, z dostępem do repo próbnego, potem Enter.
- [ ] **T** `uv run sdlc status` → `ShipScope ↔ pdi: connected`, ci_for_sdlc → pdi `configured` (zmian jeszcze nie ma).
- [ ] **SS** Settings → GitHub: repo `sdlc-proba` śledzone. Settings → Sources: źródło z kodu `config/flags.{env}.json`.
- [ ] Nowa sesja **C** w klonie repo próbnego (`claude`); `/mcp` pokazuje `pdi` i `shipscope`.

## 1. Zgłoszenie i triaż

- [ ] **T** `uv run sdlc open` → formularz zgłoszeń. Wpisz zgłoszenie z README repo próbnego (albo **C**
  `record_problem`). Oczekiwane: PRB-1.
- [ ] **C** „przejrzyj PRB-1 i przyjmij je” → `triage_problem` z `accepted`. Oczekiwane: DEC-1 i CHG-1, a w
  `get_change CHG-1` jest `dispatch: {mode: local, status: running}`.
- [ ] Po kilku minutach `get_change CHG-1` pokazuje `dispatch.status: done` z `pr`, a w `list_inbox` jest bramka B1.
  Przy błędzie: `dispatch.step` i log w `$PDI_REGISTRY_PATH/runs/`; po poprawce `retry_dispatch CHG-1`.

## 2. Fazy z bramkami

- [ ] **B1 (intent):** przejrzyj PR na GitHubie, zrób merge, potem **C** `decide_inbox_item` z `approved`,
  `success_metric` i `review_by` na jutro. Oczekiwane: faza `requirements` startuje sama (`get_change`).
- [ ] **B2 (requirements):** PR, merge, decyzja → faza `architecture`.
- [ ] **B3 (architecture):** w PR jest `plan.md` i `release.yaml` z flagą (`owner`, `remove_by`, `rollout` z
  `min_days: 0`). Merge, decyzja → faza `design`.
- [ ] **design-review:** PR, merge, decyzja.

## 3. Gotowość i zatwierdzenie do budowy

- [ ] **T** `uv run sdlc check` → `pdi readiness.changed CHG-1 ready delivered`. `sdlc status`: ci_for_sdlc → pdi
  `connected`.
- [ ] **C** `list_inbox` → „Approve for implementation” (z prognozą). Decyzja `approved` → faza `delivery` startuje
  sama.

## 4. Dostarczenie (talos)

- [ ] Cięcia jako PR-y, a commity mają `Change: TSK-n` i `Flag: show_last_deployed`. W klonie `npm test` przechodzi.
  Merge po przeglądzie.
- [ ] **SS** zakładka Changes (repo): CHG-1 z tytułem z intencji. Release plan: linia R1.

## 5. Wdrożenia

- [ ] **T** `uv run sdlc deploy test`, potem `uv run sdlc deploy prod` → id wdrożenia i SHA.
- [ ] **SS** (do minuty) matryca Technical view z wdrożeniem na test i prod. Product view: zadania CHG-1 „Deployed
  (hidden)” na PROD; flaga `show_last_deployed` off na prod.

## 6. Etapy flagi

- [ ] PR do `config/flags.prod.json`, np. `{"enabled": true, "rollout": 10}`; merge, potem `uv run sdlc deploy prod`.
- [ ] Do ok. 6 minut **C** `list_inbox` pokazuje bramkę etapu (`release.stage_changed`). Decyzja.
- [ ] To samo dla 100%. Gdy cała R1 jest u użytkowników, ShipScope wysyła `feature.released`, a pdi planuje ocenę
  skutku (termin z B1). **C** `get_trace CHG-1` pokazuje pełny ślad.

## 7. Ocena skutku (następnego dnia)

- [ ] **T** `uv run pdi-impact-review` → w skrzynce jest ocena skutku MVP. Dane z ShipScope: wdrożenia i flaga.
  Użytkowników w repo próbnym nie ma, więc skutek oceniasz ręcznie.
- [ ] **C** `decide_inbox_item` dla oceny, potem `forecast_report` i `autonomy_report`.
- [ ] Luki z przebiegu: **C** `record_problem` (kanał dogfooding).

## Gdy coś nie działa

- `uv run sdlc status`: procesy, połączenia, ostatnie wpisy odbiornika, skrzynka.
- Logi: `~/.sdlc/logs/` (ShipScope, odbiornik), `$PDI_REGISTRY_PATH/runs/` (fazy tf).
- `uv run sdlc down` / `uv run sdlc up` restartuje stos; dane zostają.
