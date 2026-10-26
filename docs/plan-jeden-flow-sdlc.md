# Jeden flow SDLC — plan aktualizacji pdi, tf, ci_for_sdlc i ShipScope

Data: 2026-10-23 · Status: **propozycja** (nic jeszcze nie zrobione) · Wersja HTML: https://claude.ai/artifact/DoRYpdhzHwjTpGEnBx3UvV

Jak połączyć cztery projekty w jeden proces od zgłoszenia problemu do informacji, że funkcja jest wydana na PROD
i czy przyniosła oczekiwany efekt. Co zrobić w każdym repo i w jakiej kolejności. Kontekst rozmowy, z której plan
wynika: [`kontekst-rozmowy.md`](kontekst-rozmowy.md).

## 1. Kto za co odpowiada

Każdy projekt robi jedną rzecz. pdi spina całość, ale nie powiela logiki pozostałych: wywołuje tf, pyta
ci_for_sdlc, słucha ShipScope.

| Projekt | Pytanie | Zakres |
|---|---|---|
| **pdi** (Product Decision Intelligence) | Co, czy i dlaczego? | zgłoszenia, triaż, rejestr decyzji, skrzynka bramek, orkiestracja etapów, graf śladu, ocena skutków decyzji |
| **tf** (fabryka agentów) | Jak to zrobić? | persony, skille, hooki, artefakty w `docs/project/`, Talos (historyjka → PR), rekonstrukcja z kodu, pasma kontrolne |
| **ci_for_sdlc** | Czy wiemy, co budujemy? | spójność definicji między źródłami, gotowość do implementacji, pytania do ludzi, drift po zatwierdzeniu |
| **ShipScope** | Czy to już działa u ludzi? | wdrożone vs wydane (flagi), drift środowisk, rollbacki, release notes, lead time |

## 2. Przepływ

**[B]** = bramka człowieka: bez akceptacji proces stoi.

| # | Etap | Kto wykonuje | Wynik |
|---|---|---|---|
| 01 | Zgłoszenie problemu lub pomysłu | pdi | `PRB-34`: „kto nie może czego → skutek”, pytania doprecyzowujące od AI |
| 02 | Wzbogacenie | pdi + tf + ci_for_sdlc | duplikaty, kontekst z kodu (rekonstrukcja tf) i z Confluence/Jiry (`/api/impact` ci_for_sdlc), odrzucone wcześniej pomysły, rekomendacja |
| 03 | Triaż **[B]** | człowiek | przyjęte do analizy / potrzebne informacje / odłożone / odrzucone z powodem |
| 04 | Intencja i zakres (B1) **[B]** | tf | PR z `changes/CHG-12/intent.md`: warianty, koszt, metryki sukcesu, `source: PRB-34` |
| 05 | Domena i wymagania (B2) **[B]** | tf | wymagania z kryteriami akceptacji jako przykłady, słownik |
| 06 | Architektura i plan cięć (B3) **[B]** | tf | ADR, model zagrożeń, cięcia pionowe TSK-57…TSK-60 |
| 07 | Design **[B]** | tf + Figma MCP (nowe) | ramki per journey i stan, linki w `design.md` |
| 08 | Kontrola spójności i gotowość **[B]** | ci_for_sdlc | luki i konflikty → pytania w skrzynce pdi → decyzje; „Approve for implementation” = baseline |
| 09 | Build | tf (Talos) | PR na cięcie, commit na kawałek z dopiskiem `Change: TSK-57`, raport kosztu |
| 10 | Review i merge **[B]** | tf + ci_for_sdlc | CI, AI review według `REVIEW.md`, drift spec ↔ kod, merge przez code ownera |
| 11 | Gotowość i wydanie (B4, B5) **[B]** | tf | przegląd gotowości, autoryzacja PROD |
| 12 | Status wydania **[B]** | ShipScope | Not deployed / Deployed (hidden) / Released per CHG; włączenie flagi to decyzja biznesowa |
| 13 | Powiadomienie zgłaszającego | pdi | „PRB-34 rozwiązane, na PROD od v2.4”, po zdarzeniu `feature.released` z ShipScope |
| 14 | Ocena skutku decyzji **[B]** | pdi | po N dniach: metryka sukcesu z intencji osiągnięta / nie / nie wiadomo |
| 15 | Utrzymanie i pętla | tf + ShipScope + pdi | pasma kontrolne na metrykach z ShipScope; przy 3σ nowy PRB wraca na początek |

## 3. Wspólny kontrakt (zrobić najpierw)

Bez niego każde połączenie będzie osobną, kruchą integracją.

### Identyfikatory

| ID | Co oznacza | Gdzie żyje | Uwagi |
|---|---|---|---|
| `PRB-34` | zgłoszony problem lub pomysł | baza pdi | większość zostanie odrzucona, więc nie zaśmieca repo |
| `CHG-12` | zmiana przyjęta do budowy (intencja) | repo: `docs/project/changes/CHG-12/` | od tej chwili źródłem prawdy jest repo |
| `TSK-57` | cięcie pionowe zmiany, osobne ID z rodzicem CHG-12 | repo: `plan.md` zmiany | jak sub-task w Jirze; ShipScope już umie liczyć sub-task do rodzica |
| `DEC-201` | decyzja człowieka (triaż, bramka, odpowiedź na pytanie, wydanie) | rejestr w pdi | tf i ci_for_sdlc trzymają lokalne wpisy z tym ID |

**Kształt ID jak w Jirze** (`[A-Z]{2,}-[0-9]+`). ShipScope wyciąga klucze z commitów dokładnie tym wyrażeniem
(`extractIssueKeys()` w `server/lib/deployment-logic.js`), a ci_for_sdlc akceptuje taki klucz elementu
(`itemKeyParams` w `packages/server/src/schemas.ts`). Ślad w commitach działa więc w ShipScope bez zmiany parsera.
Prefiksy muszą być konfigurowalne per organizacja, bo `CHG` może być istniejącym projektem w Jirze.

### Artefakty zmiany w repo

Rozszerzenie dziennika tf (`core-project-record`), który dziś jest per projekt. Ten sam nagłówek YAML
(`artifact`, `phase`, `status`, `version`, `inputs`…), dwa nowe pola: `change` i `source`.

```
docs/project/changes/CHG-12/
  intent.md        # artifact: intent · change: CHG-12 · source: PRB-34 · status: accepted
                   # problem, warianty, wybrany wariant, metryki sukcesu, poza zakresem
  requirements.md  # kryteria akceptacji jako przykłady, dane osobowe, wymagania jakości
  design.md        # linki do ramek Figmy per journey i stan
  plan.md          # cięcia: TSK-57 … TSK-60 (wartość, pliki, weryfikacja)
  decisions.md     # lokalne wpisy DEC-… z linkiem do pdi
  runs/TSK-57.md   # raport Talosa: plan, odstępstwa, koszt, wynik bramek
```

### Ślad w commitach

```
feat(charging): add bulk configuration endpoint

Change: TSK-57
```

### Zdarzenia

| Zdarzenie | Wysyła | Odbiera | Po co |
|---|---|---|---|
| `problem.accepted` | pdi | tf | start fazy intencji (bez interakcji) |
| `gate.requested` | tf, ci_for_sdlc | pdi | pozycja w skrzynce bramek |
| `gate.decided` | pdi | tf, ci_for_sdlc | następny etap albo poprawki |
| `readiness.changed` | ci_for_sdlc | pdi | status gotowości i drift na grafie śladu |
| `feature.released` | ShipScope | pdi | powiadomienie zgłaszającego, start oceny skutku |
| `metric.breached` | tf (pasma kontrolne) | pdi | nowy PRB z diagnozą |

Schematy JSON (problem, zmiana, decyzja, zdarzenie) w `pdi/contract/`, z numerem wersji. Pozostałe projekty
przypinają wersję tak, jak ShipScope robi to dziś z `schemaVersion` kontraktu flag.

## 4. pdi — co powinno być w środku

Rdzeniem jest **decyzja**: kto, kiedy i dlaczego zdecydował, na jakich dowodach, jakie były opcje i czy decyzja
przyniosła efekt. Ostatni element odróżnia pdi od zwykłego trackera.

| Moduł | Co robi | AI | Człowiek | MVP |
|---|---|---|---|---|
| Intake | formularz (później Slack/Teams, support, post-mortemy); format „kto nie może czego → skutek” | przeformułowuje rozwiązanie na problem, 3–5 pytań | zgłaszający odpowiada | tak |
| Wzbogacenie | grupuje duplikaty (liczba zgłoszeń to dowód), dociąga kontekst z rekonstrukcji tf i `/api/impact` ci_for_sdlc, sprawdza `.out-of-scope/` | całość, przez skill `proc-issue-triage` z tf | – | tak |
| Triaż i priorytety | stany z `proc-issue-triage`, obowiązkowy powód odrzucenia, „odłożone” z progiem powrotu (np. 3 nowe zgłoszenia), punktacja RICE/WSJF jako podpowiedź | rekomendacja z uzasadnieniem | PO decyduje | tak |
| Rejestr decyzji | jedno miejsce na decyzje z całego flow: triaż, B1–B6, odpowiedzi na pytania ci_for_sdlc, wydania; wersje i zastępowanie; dług decyzyjny | wykrywa decyzje sprzeczne z wcześniejszymi | autor decyzji | tak |
| Przyjęcie do budowy | po akceptacji tworzy w docelowym repo PR z `changes/CHG-n/intent.md` (GitHub App) | szkic wariantów przez personę tf | B1 jako approve PR | tak |
| Skrzynka bramek | jedna lista „czeka na Ciebie”: akceptacje artefaktów, pytania z ci_for_sdlc, wydania, oceny skutków | – | wszystkie bramki | później |
| Orkiestrator | maszyna stanów per CHG; po decyzji na bramce uruchamia następną fazę tf bez interakcji; budżet kosztu per zmiana | wykonują persony tf | – | później |
| Graf śladu | PRB → CHG → TSK → PR → wdrożenie → wydanie → skutek, z danymi z repo, ci_for_sdlc i ShipScope | – | podgląd | później |
| Ocena skutku | po wydaniu i N dniach porównuje metrykę sukcesu z intencji z danymi; wynik wraca do rejestru decyzji jako lekcja | zbiera dane, szkicuje wniosek | potwierdza wynik | później |
| Powiadomienia | status zgłoszenia dla zgłaszającego, w tym „wydane” | – | – | później |

**Czego pdi nie robi:** nie analizuje spójności (ci_for_sdlc), nie pisze kodu ani artefaktów (tf), nie liczy
statusu wdrożeń (ShipScope). Jeśli w pdi zaczyna powstawać kopia którejś z tych logik, to sygnał, że brakuje API
w tamtym projekcie.

**Stack (rekomendacja do bramki B3):** TypeScript + Fastify + Postgres, z wzorcami z ShipScope: logowanie przez
GitHub App, wielu klientów z RLS i `withScope()`, szyfrowanie tokenów (`secret-box`), webhooki przez kolejkę. Sam
pdi warto zbudować przez flow tf (fazy 0–6) jako pierwszy przebieg próbny.

## 5. tf — zmiany w fabryce

tf ma już cykl dostarczenia (fazy 0–9, bramki B1–B6), dziennik artefaktów, Talosa, triaż i pasma kontrolne.
Brakuje pracy per zmiana, uruchamiania bez interakcji i wyjść w formacie maszynowym.

| Co | Gdzie | Po co | Faza |
|---|---|---|---|
| Dziennik per zmiana | `core-project-record`, `project_record.py change new CHG-12 --source PRB-34`, szablony intent/plan | w brownfieldzie wiele zmian idzie równolegle; dziś dziennik jest per projekt | F0 |
| Instalacja w pozostałych repo | tf w ShipScope i pdi; aktualizacja starszej instalacji w `ci_for_sdlc/.claude` | jeden sposób pracy agentów wszędzie | F0 |
| Dopisek `Change:` w commitach | `core-conventional-commits`, `core-git-workflow`, hook commit-msg | ślad dla ShipScope i ci_for_sdlc | F1 |
| Talos czyta cięcia z `plan.md` zmiany | `modes/mode-talos/skills/talos-story-run` | historyjka = TSK; dopisek w każdym commicie | F1 |
| Raport Talosa w repo | z `.claude/runs/` (ignorowane przez git) do `changes/CHG/runs/TSK-n.md` albo do opisu PR | ślad audytowy; miary z planu F3 rekonstrukcji (`plan_drift.py`) | F1 |
| Dokończenie `eng-project-reconstruction` | F1a–F2 z `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` | fundament brownfieldu; szkice `CLAUDE.md` i `REVIEW.md` | F2 |
| Eksport rekonstrukcji w JSON | obok `rules.md`, `requirements.md`, `domain.md`: te same treści z dowodami `plik:linia` | źródło dla ci_for_sdlc | F2 |
| `proc-issue-triage` na wejściu z pdi | wejście: PRB w JSON; wyjście: rekomendacja według schematu | wzbogacenie i triaż w pdi bez kopiowania logiki | F3 |
| Uruchamianie person bez interakcji | np. `tf run <persona> --change CHG-12 --phase requirements`; kończy się stanem „czeka na bramkę” i kodem wyjścia | orkiestrator w pdi zamiast ręcznego startu kolejnej persony | F4 |
| Szablon workflow fazy | `core/workflows/sdlc-phase.yml` (`workflow_dispatch` z pdi) | fazy biegną w CI z budżetem, nie na laptopie | F4 |
| Pasma kontrolne na danych z ShipScope | `control_band.py` + adapter API ShipScope; przy 3σ zdarzenie `metric.breached` | pętla utrzymanie → nowy problem | F5 |
| AI review w CI | szablon workflow z claude-code-action i `REVIEW.md` z rekonstrukcji | etap 10 | F6 |
| Evale nowego flow | scenariusze PRB → intent, intent → plan; decyzja D5 tf o przebiegach według harmonogramu | zmiana skilli nie psuje flow | F6 |

## 6. ci_for_sdlc — zmiany w kontroli spójności

Silnik zostaje bez zmian: konektory → `ProjectContext` → graf → reguły → pytania → decyzje → gotowość → drift.
Dochodzą nowe źródła i wyjścia. Ścieżka przez Jirę zostaje dla organizacji, które jej używają.

| Co | Gdzie | Po co | Faza |
|---|---|---|---|
| Konektor artefaktów z repo | nowy `packages/core/src/connectors/repo.ts`: `changes/*/` → RequirementContext (elementy CHG/TSK), `02-domain` i ADR → DocumentationContext, linki z `design.md` → istniejący konektor Figmy | wariant bez Jiry | F2 |
| Konektor wyniku rekonstrukcji tf | reguły i wymagania z kodu (z dowodami `plik:linia`) jako źródło „stan obecny” | konflikt „spec mówi X, kod robi Y” bez łamania zasady MVP „nie analizujemy kodu”: kod analizuje tf | F2 |
| Status check na PR | GitHub Action z CLI `analyze --fail-on critical` zawężonym do zmienionej zmiany | bramka gotowości w miejscu, gdzie człowiek i tak klika approve | F2 |
| Słownik claims per domena | `analysis/claims.ts`, `analysis/vocabulary.ts`; pakiet EV zasilony z `dom-ev-glossary` (moc w kW, wersja OCPP, definicja uptime, status złącza) | dziś typy claims pasują do demo checkoutu | F2 |
| Wychodzące webhooki | podpisane zdarzenia `readiness.changed`, `gate.requested` (dziś jest tylko wewnętrzne SSE `/api/events`) | pdi wie o stanie bez odpytywania | F3 |
| Decyzje we współpracy z pdi | `/api/decisions` przyjmuje decyzję z ID z pdi; pytania trafiają do skrzynki pdi; opcjonalny zapis do `changes/CHG/decisions.md` | jeden rejestr decyzji zamiast dwóch | F4 |
| Zatwierdzenie jako bramka | `POST /api/items/:key/approve` wywoływane decyzją z pdi; baseline dla driftu | etap 8 w skrzynce pdi | F4 |
| Wiele repo / projektów | przestrzeń robocza per repo (zgodnie z `docs/SAAS.md`: Storage, Identity) | flow obejmuje kilka produktów | F5 |
| OpenAPI jako źródło | Faza 2 z `docs/ROADMAP.md` | kontrakt API vs wymagania i design | F6 |

## 7. ShipScope — zmiany w statusie wydań

Klucze z commitów już działają dla ID w kształcie Jiry. Brakuje drugiego źródła elementów pracy (repo zamiast
Jiry), zdarzeń wychodzących i API dla innych usług.

| Co | Gdzie | Po co | Faza |
|---|---|---|---|
| Źródło elementów pracy z repo | nowy sync w workerze: `docs/project/changes/*/intent.md` i `plan.md` przez GitHub Contents API (uprawnienie `contents: read` już jest w `TOKEN_PERMISSIONS`); nowa tabela w `RLS_TABLES`, zapytania w `withScope()`, test usuwania klienta | tytuły, hierarchia CHG → TSK i powiązanie z PRB bez Jiry | F1 |
| Hierarchia CHG → TSK | analogicznie do `subtaskKeys` w `issueKeys()`: commit z TSK-57 liczy się dla CHG-12 | status wydania całej zmiany | F1 |
| Grupowanie po zmianach | widok produktowy: obok Epic/PI grupowanie po CHG lub kamieniu milowym (nowy rytm obok `pi`/`sprint`/`release`/`flow`) | widok bez sprintów | F1 |
| Flagi powiązane z CHG/TSK | dziś `jira_keys` w kontrakcie `schemaVersion: 2`; nowe opcjonalne pole albo uogólnienie nazwy (Fastify odrzuca nieznane pola, więc zmiana schematu jest konieczna) | „released” dla zmian spoza Jiry | F1 |
| Zdarzenie `feature.released` | worker zapamiętuje ostatni status per element i środowisko; przy przejściu na `released` lub `deployed_code_only` na prod wysyła podpisany webhook | powiadomienie zgłaszającego, start oceny skutku | F5 |
| API dla usług | token usługi (wzorem `ingest_tokens`): status elementu, eksport metryk (rollbacki, drift, lead time) jako JSON/CSV | graf śladu w pdi, pasma kontrolne w tf | F5 |
| Release notes z intencji | Delivery summary bierze tytuł i opis z `intent.md`, nie z ticketu | notatki pisane językiem problemu | F5 |
| Lead time od zgłoszenia | Insights: PRB utworzone → wydane na prod (daty z pdi) | pełna miara „od pomysłu do produkcji” | F5 |

## 8. Kolejność realizacji

> **Aktualizacja 2026-10-23:** dodana faza **F0+ — pdi standalone** (rejestr decyzji z zapisem z Claude CLI przez MCP), niezależna od tf, ci_for_sdlc i ShipScope; w F0 najpierw schemat decyzji. Szczegóły: [`14-pdi-standalone.md`](14-pdi-standalone.md#7-zmiana-kolejności-w-planie-jednego-flow).

Każda faza kończy się czymś, co działa samo, nawet jeśli następna się opóźni. Każdy punkt to osobny PR w danym repo.

### F0 — Kontrakt
- **pdi:** repo startowe, `contract/`: schematy problem, zmiana, decyzja, zdarzenie; zasady ID; testy walidacji.
- **tf:** dziennik per zmiana (`project_record.py change new`), szablony intent/plan; instalacja tf w ShipScope i pdi.
- **Działa po fazie:** zmianę da się opisać w repo w jednym, sprawdzalnym formacie.

> **G1 i G2 (plan wydania, kształt historyjki)** — kroki z [planu G1/G2](plan-g1-g2.md) w fazach: K0 (kontrakt
> 0.4.0) razem z F0; G2.1–G2.3 i G1.2 (tryb Jira w ci_for_sdlc), G2.4 i G1.1 (tf) bez zależności od F1–F5;
> G1.3 (ShipScope) w trybie repo po F1; G1.4 (REL w repo) po F2; G1.5 (bramki etapów i zdarzenia) po F4–F5.

### F1 — Ślad w commitach
- **tf:** dopisek `Change:` i hook; Talos czyta `plan.md` zmiany; raport przebiegu w repo.
- **ShipScope:** sync elementów z repo, hierarchia CHG → TSK, grupowanie po zmianach, flagi z kluczami zmian.
- **Działa po fazie:** ShipScope pokazuje „CHG-12: Deployed (hidden) na PROD” bez Jiry i bez pdi.

### F2 — Spójność na repo
- **tf:** rekonstrukcja F1a–F2 z eksportem JSON.
- **ci_for_sdlc:** konektor repo, konektor rekonstrukcji, status check na PR, słownik claims EV.
- **Działa po fazie:** PR z wymaganiami dostaje czerwony check, gdy wymaganie przeczy dokumentacji albo stanowi kodu.

### F3 — pdi MVP
- **pdi:** intake, wzbogacenie, triaż, rejestr decyzji, przyjęcie do budowy jako PR z `intent.md`.
- **tf:** `proc-issue-triage` z wejściem i wyjściem w JSON.
- **ci_for_sdlc:** wychodzące webhooki.
- **Działa po fazie:** pilot na dwóch problemach EV (operacje masowe w Control Tower, definicja uptime) od
  zgłoszenia do przyjętej intencji. Bramki to wciąż zwykłe PR-y.

### F4 — Orkiestracja
- **tf:** uruchamianie person bez interakcji, szablon workflow fazy z budżetem — **zrobione 2026-10-26** (tf #79, `phase_run.py` i `sdlc-phase.yml` w `mode-pdi`).
- **pdi:** maszyna stanów per CHG, skrzynka bramek — **zrobione 2026-10-26** (pdi #16, [plan](plan-f4-pdi.md); w Pythonie, na skrzynce z G1.5).
- **ci_for_sdlc:** pytania i zatwierdzenia przez pdi, decyzje z ID z pdi — **zrobione 2026-10-26** (ci_for_sdlc #66: gotowość zmiany z historyjek `change:CHG-n` do pdi, zatwierdzenie po `gate.decided`; pdi: wysyłka `gate.decided` do ci_for_sdlc).
- **Działa po fazie:** człowiek klika tylko na bramkach; kolejne fazy startują same.

### F5 — Zamknięcie pętli
- **ShipScope:** `feature.released`, API usług (**zrobione 2026-10-26**, dbqm45/evdt-service-shipscope#110), release notes z intencji, lead time od zgłoszenia.
- **pdi:** powiadomienia (**zrobione 2026-10-26**, [plan](plan-f5-powiadomienia.md): mały rejestr PRB, podpisany webhook do zgłaszającego po triażu, wydaniu i ocenie skutku), ocena skutku decyzji (**zrobione 2026-10-26**, [plan](plan-f5-ocena-skutku.md): termin z intencji po wydaniu R1, dane z API usług ShipScope, szkic wniosku, wynik potwierdza człowiek), graf śladu (**zrobione 2026-10-26**, [plan](plan-f5-graf-sladu.md): `get_trace`, luki pokazane, nie naprawiane).
- **tf:** pasma kontrolne na metrykach z ShipScope → nowy PRB.
- **Działa po fazie:** pełna pętla zgłoszenie → wydanie → skutek → nowe zgłoszenie.

### F6 — Rozszerzenia
- **tf:** faza designu przez Figma MCP, AI review w CI, evale flow.
- **ci_for_sdlc:** OpenAPI jako źródło, porównanie ekranów z ramkami Figmy.
- **pdi:** kanały Slack/Teams, lustro w Jirze dla organizacji, które go potrzebują.

## 9. Decyzje do podjęcia

| # | Pytanie | Rekomendacja |
|---|---|---|
| D1 | Gdzie trzymać kontrakt? | w `pdi/contract/`, z wersją; osobne repo dopiero gdy pojawi się czwarty konsument — **przyjęte 2026-10-23** ([decyzje](decyzje.md)) |
| D2 | Kto jest właścicielem rejestru decyzji? | pdi; ci_for_sdlc i tf trzymają lokalne wpisy z ID z pdi. Dwa niezależne rejestry szybko się rozjadą — **zmienione 2026-10-23:** przyjęty podział z R1 (decyzje bez zmiany w pdi, decyzje o zmianie w repo, pdi indeksuje; [decyzje](decyzje.md)) |
| D3 | Format ID | kształt Jiry, prefiksy konfigurowalne per organizacja; cięcie jako osobne ID z rodzicem — **przyjęte 2026-10-23** ([decyzje](decyzje.md)) |
| D4 | Jira w brownfieldzie | zostaje źródłem dla ci_for_sdlc i ShipScope; dla nowych zmian źródłem prawdy jest repo, Jira najwyżej jako lustro |
| D5 | Model wdrożenia pdi | usługa dla wielu klientów jak ShipScope; między usługami tokeny serwisowe i podpisane webhooki |
| D6 | Koszt agentów bez interakcji | twardy budżet per zmiana i per faza (mechanizm `--budget` z Talosa), raport kosztu w grafie śladu |
| D7 | Format dziennika w ShipScope | dziś `context/foundation/` (10xDevs); przejść na `docs/project/` z tf przy okazji F0, bez pośpiechu |

---

Sprawdzone w kodzie 2026-10-23: `extractIssueKeys()` i `TOKEN_PERMISSIONS` w ShipScope, wzorzec klucza elementu
i trasy API w ci_for_sdlc, dziennik, Talos, triaż i plan rekonstrukcji w tf. Zakres pdi to propozycja.
