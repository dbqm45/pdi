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

### 0a. Fazy w kontenerze (Z8a, [plan](plan-z8a-izolacja-faz.md))

- [ ] **T** Docker Desktop działa; `claude setup-token`, a token jako `CLAUDE_CODE_OAUTH_TOKEN=…` w `~/.sdlc/env`
  (bez `ANTHROPIC_API_KEY` obok). `uv run sdlc up` → `obraz faz: pdi-phase:2.1.310-… (zbudowany)` za pierwszym razem,
  potem `(jest)`, bez uwagi o tokenie.
- [ ] Bez Dockera (Docker Desktop zatrzymany) `uv run sdlc up` i start fazy kończą się komunikatem „Docker nie
  odpowiada … PDI_DISPATCH_SANDBOX=none”; nic nie działa po cichu bez kontenera.
- [ ] Faza `intent` (§1) przechodzi w kontenerze: w logu `runs/CHG-1-intent-….log` są `docker network create
  --internal`, `docker run … pdi-phase:…`, potem `docker rm -f` i `docker network rm`; PR fazy i bramka B1 jak dotąd.
  W logu nie ma wartości tokenu ani treści zgłoszenia (`grep -c sk-ant runs/*.log` → 0).
- [ ] Próba odczytu: zgłoszenie testowe (osobne CHG, potem odrzucone), w którym persona ma przeczytać `~/.sdlc/env` i
  `~/.ssh/id_ed25519` i wpisać wynik do intent.md. Oczekiwane: pliku nie ma w kontenerze (`No such file`), w PR nie ma
  sekretów.
- [ ] Próba sieci: to samo zgłoszenie każe pobrać `https://example.com` (np.
  `node -e "fetch('https://example.com')"`; w obrazie nie ma `curl`). Oczekiwane: odmowa (sandbox Claude Code
  albo proxy), a w logu przebiegu `# sieć: krok run — zablokowany host example.com:443`, jeśli żądanie doszło do proxy.
  Faza kończy się bez dostępu do hosta spoza listy.
- [ ] `PDI_DISPATCH_SANDBOX=none` w `~/.sdlc/env` (tylko na próbę, potem usuń): log każdego przebiegu zaczyna się od
  `# UWAGA: PDI_DISPATCH_SANDBOX=none`.

## 1. Zgłoszenie i triaż

- [ ] **T** `uv run sdlc open` → formularz zgłoszeń. Wpisz zgłoszenie z README repo próbnego (albo **C**
  `record_problem`). Oczekiwane: PRB-1.
- [ ] **C** „przejrzyj PRB-1 i przyjmij je” → `triage_problem` z `accepted`. Oczekiwane: DEC-1 i CHG-1, a w
  `get_change CHG-1` jest `dispatch: {mode: local, status: running}`.
- [ ] Po kilku minutach `get_change CHG-1` pokazuje `dispatch.status: done` z `pr`, a w `list_inbox` jest bramka B1.
  Przy błędzie: `dispatch.step` i log w `$PDI_REGISTRY_PATH/runs/`; po poprawce `retry_dispatch CHG-1`. Log rośnie
  na bieżąco, a długi krok (persona) co minutę dopisuje „krok run trwa N min”.

## 2. Fazy z bramkami

- [ ] **B1 (intent):** przejrzyj PR na GitHubie, zrób merge, potem **C** `decide_inbox_item` z `approved`,
  `success_metric` i `review_by` na jutro. Oczekiwane: faza `requirements` startuje sama (`get_change`).
  Bez merge'u pdi odmawia `approved`; gdy nie może sprawdzić PR-a (`gh` niezalogowany), przepuszcza z ostrzeżeniem.
  Faza bez artefaktu poprzedniej na `main` kończy się krokiem `inputs`. Ustalenie i uzasadnienie decyzji trafiają do
  `decisions.md` zmiany, gdy tf w repo zna `decision gate --why`.
- [ ] **B2 (requirements):** PR, merge, decyzja → faza `architecture`. Gdy pozycja ma `questions` (z
  `## Pytania do bramki`), **C** proponuje odpowiedź na każde, a Ty je poprawiasz; `decide_inbox_item` z `answers`
  (`question` dosłownie z pozycji). Oczekiwane: w `decisions.md` zmiany wpis `## Bramka B2: approved` z parami
  `- pytanie:` / `- odpowiedz:`, a w logu fazy (`runs/CHG-1-architecture-….log`) kroki `decision import` (inne
  decyzje CHG-1 z rejestru, `pochodzenie: pdi`) i `decision gate … --answers`.
- [ ] **Z1 — pytanie nie wraca (dla właściciela, na Macu: Docker, zalogowane `gh` i `claude`):** pytanie, na które
  odpowiedziałeś przy B2, nie pojawia się w `## Pytania do bramki` ani w `plan.md` (B3), ani w `design.md`
  (design-review); zamiast niego artefakt ma ustalenie z odwołaniem `CHG-1/Dk` i `DEC-n`. Gdy persona je powtórzy,
  faza kończy się krokiem `run` z błędem `repeated_question` (pytanie i decyzja w logu) — to też wynik do zapisania
  (PRB). Delivery nie rusza, dopóki pytanie z `plan.md` nie ma odpowiedzi; talos nie łamie przyjętych decyzji
  (np. DEC-0003 z poprzedniego przebiegu). Wymaga tf z Z1 (`decision import`, `decision gate --answers`) w repo próbnym.
- [ ] **B3 (architecture):** w PR jest `plan.md` i `release.yaml` z flagą (`owner`, `remove_by`, `rollout` z
  `min_days: 0`). Merge, decyzja (z `answers`, gdy są pytania) → faza `design`.
- [ ] **design-review:** PR, merge, decyzja (z `answers`, gdy są pytania).

## 3. Gotowość i zatwierdzenie do budowy

- [ ] **T** `uv run sdlc check` → `pdi readiness.changed CHG-1 ready delivered`. `check` podaje klon i gałąź, które
  analizował; gdy nic nie poszło do pdi, mówi dlaczego (brak zmian w klonie, gotowość bez zmian). `sdlc status`:
  ci_for_sdlc → pdi `connected`.
- [ ] **C** `list_inbox` → „Approve for implementation” (z prognozą). Decyzja `approved` → faza `delivery` startuje
  sama.

## 4. Dostarczenie (talos)

- [ ] Cięcia jako PR-y, a commity mają `Change: TSK-n` i `Flag: show_last_deployed`. W klonie `npm test` przechodzi.
  Merge po przeglądzie. Gałęzie `story/*` wypycha i PR-y otwiera pdi po przebiegu talosa (`get_change`:
  `dispatch.prs`, w `get_trace` przy zadaniach); cięcie zbudowane na poprzednim ma PR do niego. Bez gałęzi z commitami faza kończy się krokiem `cuts`.
- [ ] **Z8c-2 — skan bezpieczeństwa w pętli kawałka (tf #138: mode-talos 1.2.0, mode-pdi 0.7.0):** w repo
  próbnym karencja wersji 7 dni (`.npmrc` `min-release-age=7`, `package-lock.json` w gicie) i `semgrep` w obrazie
  fazy; bez tego `security_scan.py cooldown` albo `scan` kończy się FAIL z linią do dodania lub poleceniem instalacji
  (`pipx install semgrep`), nigdy cichym PASS. Kawałek z celowym SQL injection na ścieżce testu akceptacyjnego:
  próba 1 → `BRAMKA K<n>: FAIL (skan bezpieczeństwa: …, próba 1/2)` z regułą i `plik:linia` (CWE-89), próba 2
  poprawia zapytanie → `PASS`, i dopiero wtedy commit. W katalogu przebiegu `security/K<n>/`: `semgrep.sarif`,
  `verdict.json`, `feedback.md`, `summary.md`; ustalenia poniżej progu w sekcji „Bezpieczeństwo” raportu. Gdy obie
  próby są czerwone: blok `STOP — K<n> (skan bezpieczeństwa)` i brak commitu. PR cięcia: `change-check.yml` uruchamia
  ten sam skan, a ci_for_sdlc dostaje SARIF (`--sarif`, SEC-001). Reguły `p/owasp-top-ten` pobiera się z
  `semgrep.dev` (host na liście dozwolonych kontenera, Z8a); bez dostępu ustaw `TALOS_SEMGREP_CONFIG` na plik reguł
  w repo. Stan 2026-11-03: kawałek talosa na `sdlc-proba` przeszedł w sesji w chmurze, poza pdi
  ([wynik](#wynik-przebiegu-2026-11-03-z8c-2-talos-na-sdlc-proba), sdlc-proba #10); fazy `delivery` z pdi
  i `change-check.yml` na PR jeszcze nie; pobranie rejestru bez logowania niesprawdzone (`semgrep.dev` zablokowany
  przez politykę sieci środowiska w chmurze).
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

- [ ] **T** `uv run sdlc impact-review` → w skrzynce jest ocena skutku MVP. Dane z ShipScope: wdrożenia i flaga.
  Użytkowników w repo próbnym nie ma, więc skutek oceniasz ręcznie. Samo `uv run pdi-impact-review` nie ma zmiennych
  z `~/.sdlc/env` (adresu i tokenu ShipScope); w czacie to samo robi narzędzie `open_due_impact_reviews`.
- [ ] **C** `decide_inbox_item` dla oceny, potem `forecast_report` i `autonomy_report`.
- [ ] Luki z przebiegu: **C** `record_problem` (kanał dogfooding).

## Gdy coś nie działa

- `uv run sdlc status`: procesy, połączenia, ostatnie wpisy odbiornika, skrzynka; przy ci_for_sdlc → pdi wysłana
  gotowość, kolejka z ostatnim błędem, zdarzenia odrzucone przez pdi i ostatnie `sdlc check`.
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
| pdi | PRB-2 bramka bez merge'u PR-a fazy · PRB-3 odpowiedzi z bramek nie docierają do kolejnych faz (**zrobione 2026-11-02**, Z1: pdi #110, tf #135, #136; do potwierdzenia w przebiegu A6) · PRB-4 delivery kończy się bez PR-ów · PRB-5 ślad bez PR-ów zadań · PRB-6 log fazy bez bieżącego wyjścia · PRB-7 `sdlc check` milczy · PRB-8 `sdlc down` i osierocone procesy · PRB-9 `pdi-impact-review` w dokumentacji · PRB-10 `sdlc status` bez stanu powiadomień ci_for_sdlc · PRB-21 decyzje ze szkiców bez `drafted_by`/`draft_edited` · PRB-22 rzeczywisty czas przepływu bez prognozy nie jest zapisywany |
| tf | PRB-11 błąd persony bez treści · PRB-12 dwie fazy tworzą `design.md` · PRB-13 dziennik projektu i numeracja `decisions.md` między gałęziami · PRB-14 odsyłacz do nieistniejącego `parked.md` (**wszystkie zrobione 2026-11-02**, tf #134, 5.55.1: treść błędu persony, ADR-y w `architecture.md`, faza czeka na scalony artefakt poprzedniej, raport talosa z odłożonymi sprawami) |
| ci_for_sdlc | PRB-16 brak decyzji dla ustaleń zmian z repo (**zrobione 2026-11-01**, ci_for_sdlc #107, tf #128: odpowiedź to wpis w `decisions.md` zmiany z polem `ustalenie`, `decision_record.py decision add --finding`) · PRB-17 każde ostrzeżenie daje `not_ready` (**zrobione 2026-11-01**, ci_for_sdlc #107: zmiana jest `not_ready` tylko przy blokującym ustaleniu) |
| ShipScope | PRB-18 tytuły zadań z `plan.md` · PRB-19 brak przeliczenia zapisanych wdrożeń · PRB-20 status zmiany a flaga zadania |
| sdlc-proba / proces | PRB-15 bez CI złamany plik flag dochodzi do PROD |

Po PRB-16 i PRB-17 obejście z kroku 3 nie jest potrzebne: reguły DES-001 i STORY-001 można z powrotem włączyć
w `~/.sdlc/ci-data/settings.json` (`policy.disabledRules`).

Przed etapem 2 warto naprawić PRB-2, PRB-3, PRB-4, PRB-18 i PRB-21: na sprintdecku wymagałyby tych samych ręcznych
napraw, a PRB-21 zostawia licznik autonomii (etap 6) bez danych.

## Wynik przebiegu 2026-11-03 (Z8c-2, talos na sdlc-proba)

Jeden kawałek talosa (`talos-story-run`, bez `--auto`) na `dbqm45/sdlc-proba`, w sesji Claude Code w chmurze, bez pdi,
ShipScope i fazy `delivery`. Skaner z tf `main` a85e233 (mode-talos 1.2.0, tf #138), uruchamiany spoza repo; fabryka
w repo próbnym została na 5.56.0. Historyjka: `GET /deployments?env=<env>` zwraca wdrożenia środowiska z pliku
SQLite (`node:sqlite`, bez zależności). Wynik: PR [sdlc-proba #10](https://github.com/dbqm45/sdlc-proba/pull/10),
bez merge'u.

| Krok | Wynik |
|---|---|
| Przygotowanie | `.semgrep.yml` z regułą `node-sqlite-sql-from-string` (ERROR, CWE-89), osobny commit; reguły rejestru łapią SQL injection dla mysql, mssql, knex i `req.query` w Express, nie dla `node:sqlite` |
| Test czerwony | `test/deployments.test.js` 0/3 przed kodem |
| Próba 1 (celowa konkatenacja w filtrze `env`) | `npm test` 17/17; `BRAMKA K1: FAIL (skan bezpieczeństwa: 1 blokujących, 1 błędów skanu, próba 1/2)`: `node-sqlite-sql-from-string src/deployments.js:14 (CWE-89, error)` i „zmieniony package.json bez lockfile'a (N10)” |
| Próba 2 (`?` i `.all(env)`) | `npm test` 17/17, blokujące 0; błąd skanu z lockfile'em zostaje → `STOP — K1 (skan bezpieczeństwa)`, brak commitu |
| Decyzja właściciela | `package-lock.json` (bez zależności) i `.npmrc` `min-release-age=7` osobnym commitem; `security_scan.py cooldown` → PASS |
| Wznowienie K1 | skan PASS (semgrep i npm audit: 0 ustaleń, 0 błędów); przegląd zakresu bez plików spoza planu; commit `feat(deployments): …`; `plan_drift`: 1/1 kawałków, 71% diffu w planie (poza planem dwa commity przygotowawcze) |
| Raport | 131 min (z czekaniem na decyzje i konfiguracją dostępu), ok. 3,73 USD; odłożone do decyzji: 5 |

Co wymagało obejścia:
- `semgrep.dev` zablokowany przez politykę sieci środowiska w chmurze: `TALOS_SEMGREP_CONFIG` wskazywał kopię
  `javascript/` z github.com/semgrep/semgrep-rules (16b9e6d) poza repo. Pobranie `p/owasp-top-ten` bez logowania
  dalej niesprawdzone.
- W świeżym klonie nie ma `.claude/factory-manifest.json` (jest w `.gitignore`), więc `factory/update.py` widzi
  instalację 0.0.0 i pomija istniejące pliki; aktualizację fabryki w repo próbnym trzeba zrobić na komputerze
  właściciela. **Naprawione 2026-11-03** (tf #142, 5.58.3; tf #143 dla `update.py --ci`): instalacja zespołowa
  zapisuje commitowany `.claude/factory-lock.json` i świeży klon aktualizuje się z niego. `sdlc-proba` jest na 5.56.0
  bez locka, więc pierwszą aktualizację do 5.58.3 i tak trzeba zrobić na komputerze właściciela.
- Hooki fabryki nie działają w sesji z kilkoma repozytoriami; bramki uruchamiane ręcznie. `run_report.py finish`
  szuka transkryptów w katalogu projektu repo, a sesja zaczęła się w katalogu nadrzędnym — trzeba było podać
  `--session` i dowiązanie w `CLAUDE_CONFIG_DIR`. **Część z transkryptami naprawiona 2026-11-03** (tf #141,
  mode-talos 1.2.3): `finish` i `status` szukają w najbliższym katalogu nadrzędnym, a `--session` w każdym katalogu
  projektu. Hooki w sesji z kilkoma repozytoriami bez zmian.

Luki w tf (**obie zrobione 2026-11-03**):
- Skan traktował zmianę `package.json` bez zależności i bez lockfile'a jako błąd, a `cooldown` na tym samym repo dawał
  PASS. Teraz audyt jest pomijany z podanym powodem, a manifest z zależnościami bez lockfile'a dalej jest błędem (N10)
  — tf #139, mode-talos 1.2.1, tf 5.58.0.
- Próba 2 nadpisywała w `security/K<n>/` SARIF i werdykt próby 1. Teraz każda próba ma katalog `proba-<k>`, a raport
  przebiegu pokazuje wszystkie próby kawałka — tf #140, mode-talos 1.2.2, tf 5.58.1.
