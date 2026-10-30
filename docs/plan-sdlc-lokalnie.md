# Plan: cały workflow lokalnie dwoma poleceniami (`sdlc up`)

Data: 2026-10-30 · Status: **plan, do realizacji** · Zastępuje na razie: [przebieg na sobie S5](przebieg-na-sobie-s5.md)
(wraca jako etap 2, po L5)

## 1. Problem

Scenariusz S5 wymaga ok. 30 ręcznych kroków przygotowania:
- sekrety przepisywane między czterema aplikacjami,
- tunel z adresem zmieniającym się po restarcie,
- płatności GitHub Actions,
- Vercel i Supabase,
- lokalny ShipScope z ręcznie dopisywanym kluczem.

Test workflow zamienia się w test konfiguracji. Cel: przebieg od zgłoszenia do oceny skutku uruchamiany lokalnie
w kilka minut, a później na produkcji z tą samą konfiguracją i innymi adresami.

## 2. Skąd ta złożoność (sprawdzone w kodzie 2026-10-30)

| # | Przyczyna | Gdzie | Co ją usuwa | Krok |
|---|---|---|---|---|
| Z1 | ShipScope wysyła zdarzenia i ping tylko na publiczny `https` (`checkUrl()`, `forbiddenAddress()`), stąd tunel | ShipScope `server/lib/safe-fetch.js` | tryb lokalny: `http://localhost` / `127.0.0.1` dozwolone tylko przy `PUBLIC_BASE_URL` na localhost (ten sam warunek co `dev:mock`) | L1 |
| Z2 | pdi uruchamia fazy tylko przez `workflow_dispatch` (Actions), stąd płatności i funkcja `faza` | pdi `src/pdi/dispatch.py` | `PDI_DISPATCH=local`: pdi uruchamia `phase_run.py` w lokalnym klonie repo produktu | L2 |
| Z3 | sekrety, tokeny i adresy przepisywane ręcznie (P2, P5, P7, P8 scenariusza S5) | wszystkie | `sdlc up` generuje sekrety, łączy pdi z ShipScope przez API (`POST …/pdi-connection`) i zapisuje jeden plik środowiska | L4 |
| Z4 | ci_for_sdlc nie wysyła do pdi gotowości zmian z repo (CLI bez pdi, serwer czyta tylko Jirę), stąd ręczne `gate request --gate approve-for-implementation` | ci_for_sdlc `packages/server/src/gate.ts` | `npm run analyze -- --repo … --send-to-pdi`: po analizie `readiness.changed` jak w trybie Jira | L3 |
| Z5 | wdrożenia wymagają Vercela i Supabase | sprintdeck | repo próbne i `sdlc deploy <env>`: GitHub Deployment ze statusem `success` zakładany z terminala (`gh api`); ShipScope czyta tylko GitHub Deployments | L4, L5 |

## 3. Docelowo

```bash
sdlc up                 # Postgres w Dockerze; ShipScope, pdi-receiver i ci_for_sdlc jako procesy na localhost; sekrety i połączenia gotowe
sdlc open               # przeglądarka: ShipScope i formularz zgłoszenia; serwery MCP pdi i ShipScope zarejestrowane w Claude Code
sdlc deploy prod        # GitHub Deployment bieżącego main repo próbnego (zamiast Vercela)
sdlc status             # co działa, połączenia, ostatnie zdarzenia, skrzynka pdi
sdlc down               # zatrzymuje procesy, dane zostają
```

Dalej cały przebieg idzie w czacie Claude, w repo próbnym: zgłoszenie, triaż, bramki, decyzje. Od człowieka zostają
tylko decyzje i przegląd PR-ów.

Potrzebne:
- Docker,
- konto GitHub (`gh auth login`),
- zalogowany Claude Code,
- jedno kliknięcie przy pierwszym `sdlc up`, które zakłada aplikację GitHub ShipScope (przepływ manifestu z
  `npm run dev`).

Niepotrzebne: tunel, płatności Actions, Vercel, Supabase, Jira, przepisywanie sekretów.

## 4. Kroki

Każdy krok to osobny PR w swoim repo, z testami najpierw czerwonymi. Każda aplikacja dalej działa sama: zmiany są
trybami albo dodatkowymi opcjami, domyślne zachowanie się nie zmienia.

### L1. ShipScope: tryb lokalny dla adresów pdi (Z1)
- **Co:** przy `PUBLIC_BASE_URL` na `http://localhost:*` albo `http://127.0.0.1:*` `checkUrl()` przyjmuje adres
  odbiornika pdi na localhost (`http`, dowolny port) dla subskrypcji zdarzeń, pingu i Connect. Poza tym trybem
  reguły się nie zmieniają, a log przy starcie mówi, że tryb lokalny jest włączony (jak `SHIPSCOPE_MOCK_DATA`).
- **Też:** `npm run dev` generuje `TOKEN_ENCRYPTION_KEY`, jeśli go brak (bez niego Connect odmawia).
  `SYNC_INTERVAL_MINUTES` już dziś przyjmuje wartości od 1.
- **Testy:** `server/test/safe-fetch.test.js` (localhost odrzucony bez trybu, przyjęty w trybie, prywatne adresy
  poza localhost dalej odrzucone), `server/test/dev.test.js` (klucz generowany raz, nie nadpisywany).
- **Gotowe, gdy:** lokalny ShipScope łączy się z `http://127.0.0.1:8787` bez tunelu, a Test pokazuje `connected`.

### L2. pdi: fazy uruchamiane lokalnie (Z2)
- **Co:** `PDI_DISPATCH=local` z `PDI_DISPATCH_CHECKOUT=<klon repo produktu>`. Po decyzji na bramce pdi robi to,
  co dziś `sdlc-phase.yml` (P9 scenariusza S5):
  1. gałąź `pdi/CHG-n-<faza>`,
  2. `decision gate`,
  3. `phase_run.py run` z budżetem,
  4. commit, push, PR przez `gh`,
  5. `gate request`.

  Przebieg w tle, jeden naraz na zmianę, log w `$PDI_REGISTRY_PATH/runs/`. Błąd zapisuje się w stanie zmiany jak
  dziś, a `retry_dispatch` ponawia.
- **Wymaga decyzji DL1:** `dispatch.py` mówi dziś „pdi nie uruchamia agentów u siebie (dokument 13, R4)”. Tryb
  lokalny to wyjątek tylko dla `PDI_DISPATCH=local`. Na produkcji zostaje Actions.
- **Testy:** `tests/test_dispatch.py` (polecenia i ich kolejność przy podstawionym wykonawcy, brak tokenów w logu,
  odmowa bez checkoutu), `tests/test_receiver.py` (decyzja na bramce uruchamia lokalny przebieg).
- **Gotowe, gdy:** zatwierdzenie B1 w czacie samo otwiera PR fazy `requirements` w repo próbnym, bez Actions.

### L3. ci_for_sdlc: gotowość zmian z repo do pdi (Z4)
- **Co:** `npm run analyze -- --repo <ścieżka> --send-to-pdi` (z `PDI_EVENTS_URL` i `PDI_SIGNING_SECRET`) wysyła po
  analizie `readiness.changed` dla każdej zmiany `CHG-n` z repo, tą samą kolejką i podpisem co serwer
  (`packages/server/src/pdi.ts`). `ready` daje w pdi bramkę `approve-for-implementation`. Bez flagi CLI działa jak
  dziś.
- **Też:** pdi w trybie `local` wywołuje to polecenie po scaleniu PR fazy `design` (albo `sdlc check CHG-n`).
- **Testy:** `packages/server/test/gate.test.ts` (wysyłka tylko z flagą i oboma zmiennymi, kod wyjścia bez zmian),
  test kontraktu zdarzenia.
- **Gotowe, gdy:** po design-review w skrzynce pdi pojawia się approve-for-implementation bez ręcznego
  `gate request`.

### L4. `sdlc`: jedno polecenie dla całego stosu (Z3, Z5)
- **Gdzie:** `pdi/stack/` (decyzja DL3), skrypt Pythona uruchamiany przez `uv run sdlc …`, bez nowych zależności.
- **`sdlc up`:**
  - sprawdza Dockera, `gh`, `claude`, Node i `uv`, a przy braku podaje jedno polecenie instalacji,
  - czyta ścieżki klonów z `~/.sdlc/config.toml`; przy pierwszym uruchomieniu pyta raz i zapisuje (np.
    `/Users/x/WebstormProjects`),
  - przy pierwszym uruchomieniu generuje sekrety do `~/.sdlc/env` (uprawnienia 600),
  - uruchamia Postgres ShipScope w Dockerze oraz ShipScope (web i worker), `pdi-receiver` i ci_for_sdlc jako
    procesy na localhost (decyzja DL2), z logami w `~/.sdlc/logs/`,
  - zakłada przestrzeń ShipScope i połączenie z pdi przez API, a trzy zmienne `PDI_SHIPSCOPE_*` zapisuje
    w `~/.sdlc/env`,
  - rejestruje serwery MCP `pdi` i `shipscope` w Claude Code (`claude mcp add --scope user`) z tymi samymi
    zmiennymi.
- **`sdlc deploy <env>`:** `gh api` zakłada GitHub Deployment dla `HEAD` gałęzi `main` repo próbnego ze statusem
  `success` (środowisko `production` albo `test`). ShipScope odczyta plik flag przy tym commicie.
- **`sdlc status`, `sdlc open`, `sdlc down`, `sdlc reset`:**
  - `reset` usuwa dane po pytaniu z nazwą wpisaną z klawiatury,
  - `status` pokazuje stan połączenia z `GET /api/service/v1/connection` i `get_shipscope_connection`.
- **Testy:** `tests/test_stack.py` (generowanie env bez nadpisywania, kolejność startu, polecenia `gh api` przy
  podstawionym wykonawcy, brak sekretów w logach).
- **Gotowe, gdy:** na czystym Macu z zainstalowanymi narzędziami `sdlc up` kończy się linią „gotowe”, a `sdlc status`
  pokazuje `connected` dla ShipScope ↔ pdi i ci_for_sdlc → pdi.

### L5. Repo próbne `sdlc-sandbox` (Z5)
- **Co:** repo-szablon na GitHubie z:
  - małą aplikacją (statyczna strona albo prosty serwer w Node), testami i plikiem flag `config/flags.{env}.json`,
  - tf zainstalowanym w trybie zespołowym z `pack-it`, `pack-ux`, `mode-pdi` i `mode-talos`,
  - `.claude/pdi-metrics.json`,
  - `README` z jednym zgłoszeniem do wpisania.

  `sdlc sandbox <nazwa>` zakłada z szablonu repo użytkownika (`gh repo create --template`), klonuje je, śledzi
  w ShipScope (`Track repository` przez API) i ustawia `PDI_DISPATCH_CHECKOUT`.
- **Gotowe, gdy:** cały scenariusz z §5 przechodzi na repo próbnym w jeden dzień.

## 5. Przebieg testowy po L1–L5

1. `sdlc up`, `sdlc sandbox sdlc-proba`, `sdlc open`.
2. Formularz albo czat: zgłoszenie. Czat: triaż `accepted`.
3. ⚙️ Faza intent → PR, a w skrzynce B1. Przegląd PR, merge, decyzja B1 z `success_metric` i `review_by` na jutro.
4. ⚙️ Requirements → B2, architecture → B3, design → design-review; każda bramka to merge i decyzja w czacie.
5. ⚙️ ci_for_sdlc sprawdza zmianę i wysyła gotowość, a w skrzynce pojawia się approve-for-implementation (z
   prognozą). Decyzja.
6. ⚙️ Talos robi cięcia jako PR-y. Przegląd i merge.
7. `sdlc deploy test`, `sdlc deploy prod`. ShipScope pokazuje „Deployed (hidden)”.
8. PR-y z etapami flagi (`min_days: 0`), po każdym `sdlc deploy prod`. ⚙️ `release.stage_changed` daje bramkę etapu
   w skrzynce, a `feature.released` z R1 planuje ocenę skutku.
9. Następnego dnia `uv run pdi-impact-review` → ocena skutku w skrzynce → decyzja. Potem `get_trace`,
   `autonomy_report`, `forecast_report`.

Skrócenie czasu:
- w B1 `review_by` na jutro (albo `horizon: "1 dzień"`),
- etapy flagi z `min_days: 0`,
- `SYNC_INTERVAL_MINUTES=1`.

Zdarzenia ShipScope sprawdza co 5 minut (`eventsTick()`), więc między etapem flagi a bramką w pdi mija do ok.
6 minut.

## 6. Co ten przebieg testuje, a czego nie

| Etap | Testowany naprawdę? |
|---|---|
| zgłoszenie (formularz albo czat), doprecyzowanie, triaż | tak |
| fazy intent → requirements → architecture → design: prawdziwe persony tf, prawdziwe PR-y na GitHubie | tak (z prawdziwym kosztem modelu) |
| bramki w skrzynce pdi, decyzje w rejestrze, automatyczny start następnej fazy | tak |
| sprawdzenie zmiany w ci_for_sdlc (REL-001…008, testy kryteriów) i wysyłka gotowości do pdi | tak |
| prognoza przy zatwierdzeniu do budowy | tak, choć przy pustej historii z `doubts` |
| dostarczenie przez talos, cięcia jako PR-y z `Change:` i `Flag:` | tak |
| wdrożenia, flagi, plan wydania i ślad zmiany w ShipScope | tak, na wdrożeniach z `sdlc deploy` |
| zdarzenia `release.stage_changed` i `feature.released` do pdi, bramki etapów | tak |
| ocena skutku, graf śladu, licznik autonomii | tak, ze skróconym terminem |

| Czego nie testuje | Dlaczego | Kiedy sprawdzić |
|---|---|---|
| fazy w GitHub Actions (`sdlc-phase.yml`) | lokalnie fazy uruchamia pdi | przed produkcją, po odblokowaniu płatności; ten sam `phase_run.py`, inna droga uruchomienia |
| prawdziwe wdrożenie (Vercel, baza, migracje) | `sdlc deploy` tylko zakłada GitHub Deployment | etap 2: [scenariusz S5](przebieg-na-sobie-s5.md) na sprintdecku |
| ci_for_sdlc w trybie Jira | przebieg idzie na zmianach z repo | osobno, dla zespołów w Jirze |
| webhooki GitHuba do ShipScope | localhost ich nie dostaje; ShipScope pobiera dane co 1 min | na produkcji |
| kontrola adresów i podpisów przy publicznych adresach | tryb lokalny luzuje ją dla localhosta | na produkcji (testy jednostkowe ją pokrywają) |
| skutek u prawdziwych użytkowników | repo próbne nie ma użytkowników ani metryki aktywacji | etap 2 na sprintdecku |
| wybicia metryk (`metric_watch`, pasma 3σ) | potrzebna historia wielu dni wdrożeń | po kilku tygodniach albo `metric_watch.py check --csv <plik>` |
| design z prawdziwym plikiem Figmy | repo próbne nie ma ekranów | osobno (D-F3) |

## 7. Na produkcji

To samo `~/.sdlc/env` zamienia się w zmienne środowisk usług:

| Lokalnie | Na produkcji |
|---|---|
| localhost | domeny (ShipScope na Render, pdi według DA4) |
| tryb lokalny ShipScope (L1) | wyłączony sam, bo `PUBLIC_BASE_URL` nie jest localhostem |
| `PDI_DISPATCH=local` | Actions (`sdlc-phase.yml`) |
| `sdlc deploy` | prawdziwy pipeline wdrożeń produktu |

Nazwy zmiennych i kontrakt się nie zmieniają, więc przejście to zmiana adresów i miejsca uruchamiania faz, nie
konfiguracji.

## 8. Decyzje do podjęcia

| # | Pytanie | Rekomendacja |
|---|---|---|
| DL1 | Czy pdi może uruchamiać fazy u siebie? | **przyjęte 2026-10-30** ([decyzje](decyzje.md)): tak, tylko w `PDI_DISPATCH=local` (rozwój, demo); na produkcji Actions zgodnie z R4 |
| DL2 | Procesy na hoście czy wszystko w Docker Compose? | **przyjęte 2026-10-30**: procesy na hoście, w Dockerze tylko Postgres: wszystko jest na localhost (bez wyjątków adresów poza L1), persony korzystają z logowania Claude i `gh` na hoście |
| DL3 | Gdzie mieszka `sdlc`? | **przyjęte 2026-10-30**: `pdi/stack/` (pdi już jest orkiestratorem); osobne repo dopiero, gdy pojawi się produkcyjny deploy całości |
| DL4 | Aplikacja repo próbnego | statyczna strona w Node bez zależności: najmniej do psucia, flagi w JSON |
| DL5 | Budżet przebiegu | `PDI_PHASE_BUDGET_USD=3` na fazę w repo próbnym; koszt każdej fazy w dzienniku |

## 9. Kolejność i stan

| Krok | Repo | Zależy od | Stan |
|---|---|---|---|
| L1 | ShipScope | — | zrobione (ShipScope #125) |
| L2 | pdi | DL1 | zrobione ([plan L2](plan-l2-dispatch-lokalny.md), pdi #59) |
| L3 | ci_for_sdlc | — | zrobione (ci_for_sdlc #102) |
| L4 | pdi | L1, L2, L3, DL2, DL3 | zrobione ([plan L4](plan-l4-sdlc.md)) |
| L5 | nowe repo `sdlc-sandbox` + pdi | L4, DL4 | do zrobienia |

L1, L2 i L3 są niezależne i mogą iść równolegle w trzech sesjach. Polecenia startowe L1–L5:
[`polecenia-startowe-sdlc-lokalnie.md`](polecenia-startowe-sdlc-lokalnie.md).
