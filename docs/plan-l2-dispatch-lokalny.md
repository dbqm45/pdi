# Plan L2 — pdi uruchamia fazy tf lokalnie (`PDI_DISPATCH=local`)

Data: 2026-10-30 · Status: **zrobione** · Krok L2 [planu `sdlc up`](plan-sdlc-lokalnie.md) (§2 wiersz Z2, §4 L2),
w granicach decyzji **DL1** ([decyzje](decyzje.md)): pdi uruchamia fazy u siebie tylko przy `PDI_DISPATCH=local`
(rozwój, próby); na produkcji fazy dalej idą przez GitHub Actions (R4 bez zmian).

## Cel

Zatwierdzenie bramki w Claude (`decide_inbox_item`) albo przyjęcie zgłoszenia (`triage_problem` z `accepted`)
uruchamia następną fazę tf na tym komputerze, w lokalnym klonie repo produktu. Przebieg kończy się PR-em fazy i
`gate.requested` w skrzynce pdi, bez GitHub Actions.

## Kroki przebiegu (te same i w tej samej kolejności co `sdlc-phase.yml` w tf)

| Krok (`step` w stanie) | Polecenia (lista argumentów, `cwd` = klon) |
|---|---|
| `checkout` | `git status --porcelain` (niepusto → odmowa), `git fetch origin`, `git switch <ref>`, `git pull --ff-only origin <ref>` |
| `branch` | `git ls-remote --exit-code --heads origin pdi/<CHG>-<faza>`: jest → `git switch -C <gałąź> origin/<gałąź>` (poprawki w tym samym PR), brak → `git switch -C <gałąź>` |
| `change` | tylko `intent` ze zgłoszeniem i bez `docs/project/changes/<CHG>/`: `python3 …/decision_record.py change new <CHG> --source <PRB> --author pdi [--source-reported-at <dzień>]` |
| `prompt` | `python3 …/phase_run.py prompt --change --phase` (sprawdzenie wejść; wynik nie trafia do logu, bo zawiera treść zgłoszenia) |
| `decision` | gdy jest decyzja: `python3 …/decision_record.py decision gate <CHG> --gate --outcome --id` |
| `run` | `python3 …/phase_run.py run --change --phase [--rework --gate --decision] [--budget-usd]`, z `PDI_SOURCE` i `PDI_PROBLEM` w środowisku |
| `commit` | poza `delivery`: `git add -A`, `git diff --cached --quiet` (kod 1 → `git commit -m "docs(<CHG>): faza <faza> (pdi)" -m "Change: <CHG>"`) |
| `push` | `git push -u origin <gałąź>` |
| `pr` | `gh pr view <gałąź> --json url -q .url`, a gdy go nie ma: `gh pr create --fill --head <gałąź>` |
| `gate` | `python3 …/phase_run.py gate request --change --phase --url <PR>` (`PDI_EVENTS_URL` i `PDI_TF_SIGNING_SECRET` ze środowiska pdi) |

Przebieg zatrzymuje się na pierwszym nieudanym kroku i zapisuje jego nazwę.

## Pliki

1. **`src/pdi/dispatch.py`**: `DispatchConfig` dostaje `mode` (`PDI_DISPATCH`) i `checkout`
   (`PDI_DISPATCH_CHECKOUT`). `dispatch_phase()` przy `mode == "local"` przekazuje pracę do `dispatch_local.start()`;
   bez `PDI_DISPATCH` zachowanie jest dokładnie dzisiejsze, a inna wartość daje `failed` z opisem. Docstring modułu:
   wyjątek DL1.
2. **`src/pdi/dispatch_local.py`** (nowy):
   - `start()` — synchronicznie: walidacja wejść (klucz zmiany, faza z listy, bramka, wynik, `DEC-n`, `PRB-n`,
     budżet, dzień zgłoszenia), sprawdzenie klonu (ścieżka bezwzględna, repo git, `.claude/skills/pdi-decisions/scripts`,
     czysty `git status`), odmowa, gdy dla zmiany trwa przebieg; potem start odłączonego procesu
     `python -I -m pdi.dispatch_local` (opis przebiegu na stdin, treść zgłoszenia tylko w środowisku procesu).
     Wynik: `{mode: local, status: running, log, …}` albo `failed` z `error`.
   - `execute()` — kroki z tabeli z podstawianym wykonawcą (`Run`); wynik `{status: done | failed, step?, error?, pr?}`.
   - `main()` — proces w tle: `execute()` z `subprocess.run`, wynik do `<log>.result.json`.
   - `running()` — czy dla zmiany trwa przebieg (log bez wyniku, zmieniany w ostatnich 3 h); start chroni
     `runs/<CHG>.lock` (`O_EXCL`), więc dwa procesy pdi (MCP i odbiornik) nie wystartują jednej zmiany dwa razy.
   - `settle()` — dopisuje wynik przebiegu do `dispatch` w stanie (`running` → `done` / `failed`) przy odczycie.
3. **`src/pdi/changes.py`**: `ChangeStore.get()` przepuszcza stan przez `settle()`, więc `get_change`,
   `list_changes` i `retry_dispatch` widzą wynik bez osobnego zapisu. Proces w tle nie pisze stanu zmiany (ten sam
   plik zmienia odbiornik po `gate.requested` z kroku `gate`).
4. **`src/pdi/inbox.py`**: odmowa decyzji, która uruchomiłaby fazę zmiany z trwającym przebiegiem (przed zapisem
   decyzji); `retry_dispatch` ponawia tylko `failed` i `skipped`, przy `running` odmawia z jasnym komunikatem; w trybie
   lokalnym treść zgłoszenia nie trafia do stanu — przy ponowieniu odtwarza się ją ze zgłoszenia (`source`).
5. **`src/pdi/problems.py`**: ta sama odmowa przy przyjęciu do znanej zmiany z trwającym przebiegiem; `problem`
   poza stanem w trybie lokalnym; `phase_problem()` wspólne dla przyjęcia i ponowienia.
6. **Dokumentacja**: `README.md` (tryb lokalny, zmienne, tylko do rozwoju, R4 na produkcji),
   `integrations/claude-code/README.md`, ten plan i stan L2 w planie `sdlc up`.

## Stan zmiany

`dispatch` w trybie lokalnym: `mode: local`, `status: running | done | failed`, `phase`, `rework`, `at`, `gate`,
`outcome`, `decision`, `source?`, `log` (ścieżka logu), po zakończeniu `finished_at`, `pr?` (adres PR fazy),
`step?` i `error?` (krok i opis błędu). Historia dostaje `dispatch.done` albo `dispatch.failed`.

Log: `$PDI_REGISTRY_PATH/runs/<CHG>-<faza>-<RRRRMMDDTHHMMSSZ>.log`, wynik obok: `….result.json`. W logu są
polecenia i to, co same wypisują; pdi nie dopisuje tokenów ani treści zgłoszenia, a proces w tle nie dostaje
`PDI_*_TOKEN` ani sekretów pdi poza `PDI_TF_SIGNING_SECRET` (potrzebnym do `gate request`).

## Konfiguracja

| Zmienna | Znaczenie |
|---|---|
| `PDI_DISPATCH=local` | fazy lokalnie; brak — dzisiejszy `workflow_dispatch` |
| `PDI_DISPATCH_CHECKOUT` | bezwzględna ścieżka klonu repo produktu (repo git z `.claude/skills/pdi-decisions/scripts`) |
| `PDI_DISPATCH_REF` | gałąź bazowa (domyślnie `main`) — jak dziś |
| `PDI_PHASE_BUDGET_USD` | limit kosztu fazy — jak dziś |
| `PDI_EVENTS_URL`, `PDI_TF_SIGNING_SECRET` | dla `phase_run.py gate request` (adres odbiornika, `http://127.0.0.1:8787`) |

`PDI_DISPATCH_REPO` i `PDI_GITHUB_TOKEN` nie są w tym trybie potrzebne (`git` i `gh` korzystają z logowania na
komputerze).

## Testy (najpierw czerwone)

`tests/test_dispatch_local.py`:
- polecenia i ich kolejność przy podstawionym wykonawcy: `intent` ze zgłoszeniem, poprawki (`rework`, istniejąca
  gałąź zdalna, istniejący PR) i `delivery` (bez PR i bez `gate request`);
- zatrzymanie na pierwszym błędzie z nazwą kroku;
- odmowa bez klonu, z klonem bez skryptów, z brudnym klonem i przy trwającym przebiegu; złe wejścia;
- środowisko procesu w tle bez `PDI_GITHUB_TOKEN`, brak tokenu i treści zgłoszenia w logu, opisie i stanie;
- `settle()`: `running` → `done` / `failed`, przebieg bez wyniku po czasie → `failed`.

`tests/test_inbox.py`, `tests/test_problems.py`: decyzja na bramce i przyjęcie zgłoszenia uruchamiają lokalny
przebieg (podstawiony start procesu), `get_change` pokazuje `done` z PR, `retry_dispatch` po `failed`, odmowa
drugiej decyzji przy trwającej fazie; bez `PDI_DISPATCH` dotychczasowe testy bez zmian.

Bramki: `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`
(lokalnie — GitHub Actions nie działa teraz na tym koncie).
