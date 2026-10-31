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
  Bez merge'u pdi odmawia `approved`; gdy nie może sprawdzić PR-a (`gh` niezalogowany), przepuszcza z ostrzeżeniem.
  Faza bez artefaktu poprzedniej na `main` kończy się krokiem `inputs`. Ustalenie i uzasadnienie decyzji trafiają do
  `decisions.md` zmiany, gdy tf w repo zna `decision gate --why`.
- [ ] **B2 (requirements):** PR, merge, decyzja → faza `architecture`.
- [ ] **B3 (architecture):** w PR jest `plan.md` i `release.yaml` z flagą (`owner`, `remove_by`, `rollout` z
  `min_days: 0`). Merge, decyzja → faza `design`.
- [ ] **design-review:** PR, merge, decyzja.

## 3. Gotowość i zatwierdzenie do budowy

- [ ] **T** `uv run sdlc check` → `pdi readiness.changed CHG-1 ready delivered`. `check` podaje klon i gałąź, które
  analizował; gdy nic nie poszło do pdi, mówi dlaczego (brak zmian w klonie, gotowość bez zmian). `sdlc status`: ci_for_sdlc → pdi
  `connected`.
- [ ] **C** `list_inbox` → „Approve for implementation” (z prognozą). Decyzja `approved` → faza `delivery` startuje
  sama.

## 4. Dostarczenie (talos)

- [ ] Cięcia jako PR-y, a commity mają `Change: TSK-n` i `Flag: show_last_deployed`. W klonie `npm test` przechodzi.
  Merge po przeglądzie. Gałęzie `story/*` wypycha i PR-y otwiera pdi po przebiegu talosa (`get_change`:
  `dispatch.prs`, w `get_trace` przy zadaniach); cięcie zbudowane na poprzednim ma PR do niego. Bez gałęzi z commitami faza kończy się krokiem `cuts`.
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

## Wynik przebiegu 2026-10-31

Repo próbne `dbqm45/sdlc-proba` (z szablonu `dbqm45/sdlc-sandbox`), zmiana CHG-1 ze zgłoszenia PRB-1 (data ostatniego
wdrożenia w stopce za flagą `show_last_deployed`). **Przebieg przeszedł od zgłoszenia do oceny skutku** (wynik `met`),
ale nie bez ręki: część kroków wymagała obejść, a luki są zapisane w rejestrze pdi jako PRB-2…PRB-22 (kanał
dogfooding). Koszt faz tf: około 7 USD (intent 0,64, requirements 0,58, architecture 0,92, design 1,23 nieudana
i 1,49, delivery 2,20).

| Krok | Wynik | Co wymagało obejścia |
|---|---|---|
| 0. Start | zaliczony | `sdlc up` padał na restarcie odbiornika (poprawione w pdi #85) i nie wykrywał obcego procesu na porcie 3000 (pdi #86); repo-szablonu nie było na GitHubie — odtworzony z commitu `377315a` i założony ręcznie; powrót z GitHuba bez `state` dawał surowy błąd (ShipScope #128) |
| 1. Zgłoszenie i triaż | zaliczony | faza intent przez kilka minut bez wpisów w logu (PRB-6) |
| 2. Fazy z bramkami | zaliczony z obejściami | bramki zatwierdzane przed merge'em PR-ów faz, więc kolejne fazy startowały od nieaktualnego `main` (PRB-2); konflikty `docs/project/README.md`, `decisions.md` i `design.md` rozwiązane ręcznie (PRB-12, PRB-13); te same pytania wracały w B3 i design-review (PRB-3); faza design najpierw padła bez treści błędu persony (PRB-11) |
| 3. Gotowość | zaliczony z obejściami | `sdlc check` milczał przy klonie bez zmian (PRB-7); `not_ready` przez ostrzeżenia DES-001 i STORY-001 bez możliwości decyzji dla zmian z repo (PRB-16, PRB-17; reguły wyłączone w `~/.sdlc/ci-data/settings.json`); `release.yaml` uzupełniony ręcznie (właściciel, `min_days: 0`, kryterium wyjścia etapu `100%`); prognoza bez historii |
| 4. Dostarczenie | zaliczony z obejściami | talos zrobił TSK-1 i TSK-2 z dopiskami `Change:` i `Flag:`, ale nie wypchnął gałęzi ani nie otworzył PR-ów (PRB-4); TSK-1 commitował `config/build.json` wbrew DEC-0003, bo `plan.md` miał nierozstrzygnięte pytanie (PRB-3) — poprawione ręcznie; złe tytuły zadań w ShipScope (PRB-18) |
| 5. Wdrożenia | zaliczony z obejściami | pierwsze wdrożenie (merge commit bez kluczy) nie łączyło się z zadaniami (ShipScope #129); przeliczenie zapisanych wdrożeń wymagało odpięcia repo (PRB-19); `sdlc down` zostawił osierocone procesy ShipScope (PRB-8) |
| 6. Etapy flagi | zaliczony | złamany JSON w `config/flags.prod.json` doszedł do PROD bez CI, ShipScope słusznie odmówił odczytu (PRB-15); bramki `internal` i `100%` przyszły z ShipScope; R1 wydane 2026-10-31T19:08Z; `get_trace` bez PR-ów zadań (PRB-5); status zmiany `deployed_code_only` mimo flagi zadania (PRB-20) |
| 7. Ocena skutku | zaliczony | `pdi-impact-review` bez zmiennych z `~/.sdlc/env` nie czyta ShipScope, użyte narzędzie MCP `open_due_impact_reviews` (PRB-9); szkic `unknown` (cel jakościowy), decyzja `met` po sprawdzeniu stopki na `APP_ENV=prod`; `forecast_report` bez danych (PRB-22), `autonomy_report` z zerem mierzonych decyzji (PRB-21) |

Luki według repozytorium:

| Repo | Zgłoszenia |
|---|---|
| pdi | PRB-2 bramka bez merge'u PR-a fazy · PRB-3 odpowiedzi z bramek nie docierają do kolejnych faz · PRB-4 delivery kończy się bez PR-ów · PRB-5 ślad bez PR-ów zadań · PRB-6 log fazy bez bieżącego wyjścia · PRB-7 `sdlc check` milczy · PRB-8 `sdlc down` i osierocone procesy · PRB-9 `pdi-impact-review` w dokumentacji · PRB-10 `sdlc status` bez stanu powiadomień ci_for_sdlc · PRB-21 decyzje ze szkiców bez `drafted_by`/`draft_edited` · PRB-22 rzeczywisty czas przepływu bez prognozy nie jest zapisywany |
| tf | PRB-11 błąd persony bez treści · PRB-12 dwie fazy tworzą `design.md` · PRB-13 dziennik projektu i numeracja `decisions.md` między gałęziami · PRB-14 odsyłacz do nieistniejącego `parked.md` |
| ci_for_sdlc | PRB-16 brak decyzji dla ustaleń zmian z repo · PRB-17 każde ostrzeżenie daje `not_ready` |
| ShipScope | PRB-18 tytuły zadań z `plan.md` · PRB-19 brak przeliczenia zapisanych wdrożeń · PRB-20 status zmiany a flaga zadania |
| sdlc-proba / proces | PRB-15 bez CI złamany plik flag dochodzi do PROD |

Przed etapem 2 warto naprawić PRB-2, PRB-3, PRB-4, PRB-18 i PRB-21: na sprintdecku wymagałyby tych samych ręcznych
napraw, a PRB-21 zostawia licznik autonomii (etap 6) bez danych.
