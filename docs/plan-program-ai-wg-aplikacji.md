# Plan programu AI — luki z oceny pokrycia rozpisane na aplikacje

Data: 2026-11-10 · Status: **propozycja** (do decyzji właściciela: D-P1…D-P6 w §5) · Źródło: ocena pokrycia siedmiu
obszarów (01 Repository Standards … 07 Metrics) z 2026-11-08, sprawdzona z kodem repozytoriów 2026-11-10.

## 0. Skrót

Ocena wskazała ~40 zadań „do zrobienia”. Po sprawdzeniu z repozytoriami:

- **~30 zadań mieści się w aplikacjach, które już są** (tf, pdi, ci_for_sdlc, ShipScope, ShipScope Flags, ev-testing,
  ev-intelligence, ev-domain-intelligence, aiux, sprintdeck) — §2.
- **Dwa obszary nie mieszczą się nigdzie** i rozciąganie istniejących aplikacji byłoby błędem: punkt wejścia dla
  wywołań modeli (bramka) oraz rejestr systemów AI z księgą wartości. Do tego kanał dla ludzi spoza IT. Proponuję
  trzy nowe aplikacje: **ai-gateway**, **ai-registry**, **ev-assistant** — §3.
- **Pięć rzeczy to decyzje, nie kod** (operating model, RACI, polityka danych, podział kontraktu, instalacja tf w pdi).
  Bez nich reszta nie ma kto zatwierdzać — §5.
- Plan w czterech falach (26 tygodni), z tym, co da się zrobić już w pierwszych sześciu — §4.

Co się zmieniło względem oceny z 8 XI (stan repo z 10 XI): tf jest w wersji **9.15.0** (ocena mówi o 5.74);
przegląd AI w CI już istnieje w tf (`REVIEW.md` produktu, `pr_loop.py review` w trybie pdi), więc zadanie z obszaru 02
to „uczynić go wymaganym”, nie „zbudować”; ShipScope ma `GET /metrics` (Prometheus) i audyt ustawień, a ShipScope
Flags ma dziennik zmian z autorem z sesji i dostęp awaryjny — oba są gotowymi wzorcami dla dziennika agentów.

## 1. Mapa aplikacji (co jest, do czego służy)

| Aplikacja | Repo | Rola w programie | Stan (sprawdzony 2026-11-10) |
|---|---|---|---|
| **tf** | `dbqm45/tf` | fabryka agentów instalowana w repo produktu: skille, persony, hooki, tryby `pdi`/`talos`/`team`, `tf doctor` | 9.15.0; packs: it, ev, ux, docs, editorial-pl; hooki: tdd_guard, quality_gate, scan_secrets, guard_bash, cleanroom, context_guard, jev_guard, log_usage |
| **pdi** | `dbqm45/pdi` | warstwa decyzji: zgłoszenia, triaż, rejestr decyzji (MADR), bramki B1–B5, autonomia 0–3, graf śladu, ocena skutku, `sdlc up`, **kontrakt** `contract/` 0.14 | F0–F5 planu jednego flow zrobione; tf **nie** jest zainstalowany (TODO.md, odłożone 2026-10-28) |
| **ci_for_sdlc** | `dbqm45/ci_for_sdlc` | spójność definicji: Jira + Confluence + Figma (+ rekonstrukcja z tf), gotowość, pytania, drift; recenzent AI z telemetrią kosztu i zestawem ewaluacyjnym | ~100 skilli lokalnie w `.claude/skills`; AI przez Bedrock UE z limitem $50/przestrzeń (T4) |
| **ShipScope** | `dbqm45/evdt-service-shipscope` | status wydań: wdrożenia × flagi × Jira/zmiany z repo; API usług (`/metrics`, `/flow`), zdarzenia do pdi, MCP read-only | ADR-003 (źródła flag), audyt ustawień i sekretów, Insights, połączenie z pdi |
| **ShipScope Flags** | `dbqm45/evdt-shipscope-flags` | zarządzanie flagami per serwis × środowisko: kolejność test→qa→prod, zależności, właściciel, `review by`, audyt z autorem z sesji, break-glass, OIDC | FR-001…017 zrobione; 0.7.x |
| **ev-testing (evtest)** | `dbqm45/ev-testing` | cyfrowy bliźniak floty OCPP 1.6J/2.0.1, 38 scenariuszy, chaos, GitHub Action z komentarzem w PR i porównaniem z bazą | V1 w repo, V2–V5 częściowo; Action `dbqm45/ev-testing@v0.1.1` |
| **ev-intelligence** | `dbqm45/ev-intelligence` | baza wiedzy EV dla agentów: 13 skilli, źródła klas A–D z SHA-256 i licencją, źródła poufne osobno, MCP (`ev_route/ev_search/ev_cite/ev_check`), evale skilli z `skill-gate.json` | taksonomia 1.1.0; luki tematyczne spisane w `docs/DO-ZROBIENIA.md` (NIS2, RODO historii ładowań…) |
| **ev-domain-intelligence** | `dbqm45/ev-domain-intelligence` | raporty AI z manifestem uruchomienia (wersje źródeł, reguł, modelu), ustalenie bez dowodu = hipoteza, ocena trafności przez człowieka | MVP (PR #3) |
| **aiux** | `dbqm45/aiux` | metodyka oceny: ślepa ocena ludzka, α Krippendorffa, A/B z bootstrapem; wirtualny panel UX | eksperyment |
| **sprintdeck** | `dbqm45/sprintdeck` | konsensus co do zrozumienia i ryzyka (D-E1), pierwszy „obcy” produkt dla przebiegu | MVP |
| **sdlc-proba** | `dbqm45/sdlc-proba` | repo próbne całego przebiegu (`sdlc sandbox`), workflow `sdlc-phase.yml` | używane w A6 |
| ev-team-factory, claude-team-factory | prywatne | poprzednicy tf / pack-ev | do archiwizacji (§2.10) [niezweryfikowane dla claude-team-factory: nie sprawdzałem zawartości] |

Poza zakresem (nie dotyczą programu): trip-resolver, mail_vault.

Granice, które plan szanuje (z decyzji już podjętych):

- tf jest **zawsze osobno** (instalowane w repo klienta, uruchamiane w jego CI) — `15-jedna-platforma.md` §1.
- Kontrakt między aplikacjami żyje w `pdi/contract/` do czasu czwartego konsumenta (D1). Nowe aplikacje z §3 to
  właśnie czwarty i piąty konsument, więc D1 się wyzwala (§5, D-P3).
- Decyzje o zmianie w repo zmiany, decyzje luźne w pdi (D2/R1). Rejestr systemów AI to nowy, trzeci rodzaj
  rejestru — nie decyzji, lecz **obiektów** (model, prompt, agent) z cyklem życia; stąd osobna aplikacja (§3.2).

## 2. Zadania z oceny rozpisane na istniejące aplikacje

Oznaczenia: obszar **01–07** z oceny; fala **F1–F4** z §4; „zależy od” wskazuje decyzję z §5 albo inne zadanie.

### 2.1 tf (fabryka)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| T1 | **`pack-data`**: role data engineer, ML engineer; skille: model card, data contract, eval dataset, prompt regression, metryki modelu w produkcji (drift, precision, % korekt). Metodykę oceny ludzkiej (ślepa ocena, α Krippendorffa, A/B z bootstrapem) przenieść z aiux jako skill `data-ai-evaluation` | 01, 02, 07 | F2 | generator `tf-new-pack`; skille zofia-* już są w `pack-it` (data-analysis, data-engineering) — pack-data je rozszerza, nie dubluje |
| T2 | **`repo-standard-check`** w `tf doctor` i jako krok `team-factory.yml`: czy repo ma CLAUDE.md z fabryki, `docs/project/` (TL;DR, przekazanie, lessons.md), ADR, PRD, GLOSSARY; wynik jako lista braków z poziomem (`error`/`warn`); jedna wersja standardu w `core/factory/PUBLIC_API.md` | 01 | F2 | sprintdeck jako pierwszy test (AGENTS.md tylko z regułami Next.js [niezweryfikowane: z oceny]) |
| T3 | **Jeden język instrukcji**: decyzja (pl albo en) i migracja szablonów `core/CLAUDE.md`; wyjątek dla repo z własnym AGENTS.md po angielsku (ShipScope, Flags) tylko gdy generowany z tej samej fabryki | 01 | F2 | D-P6 |
| T4 | **`eval-gate`**: skrypt `eval_gate.py` wzorowany na `skill_gate.py` + szablon workflow `eval-gate.yml` (zestaw, próg, budżet USD); czyta `targets` zmiany z kontraktu (DZ7: progi ewaluacji obowiązkowe dla produktów AI) i zgłasza wynik do pdi jako warunek bramki B5 | 02 | F2 | pdi P4; jeden format wyniku wspólny z `skill-gate.json` ev-intelligence i `spec-review.cases.json` ci_for_sdlc (§2.3, §2.7) |
| T5 | **Przegląd AI jako required check**: `pr_loop.py review` (REVIEW.md) + `security-reviewer` + `qa-change-review` uruchamiane w `sdlc-phase.yml` / `team-factory.yml` na każdym PR, wynik jako status check; dziś tylko w pętli PR trybu pdi | 02 | F2 | blokada: płatność GitHub Actions na koncie (sesja „Projekty SDLC”, 2026-10-30) |
| T6 | **`approved-models.yaml`** w `core/factory/`: lista zatwierdzonych modeli i dostawców z kryteriami (dane, region, koszt, umowa); `config.yaml` tiers i `profile.py` wybierają tylko z listy; ten sam plik czyta ai-gateway | 05 | F1 | D-P1; dziś tiers `fast/std/deep` wybierają po koszcie |
| T7 | **Eksport dziennika agentów**: `log_usage.py` i `delegation.jsonl` → zdarzenie `agent.audit_event` kontraktu (agent, model, narzędzie, pliki, kto zatwierdził) wysyłane do ai-registry; lokalne `.tf/logs/` zostają | 03 | F2 | kontrakt (D-P3), ai-registry R3 |
| T8 | **Macierz uprawnień agent → system → operacja** (`read` / `propose` / `execute`) jako plik `.tf/config/permissions.yaml` konsumowany przez `guard_bash`, `guard_paths` i `jev_guard`; źródłem prawdy jest ai-registry, tf pobiera kopię przy `tf update` | 03 | F3 | ai-registry R4 |
| T9 | **Cykl życia modelu w `core-delivery-lifecycle`**: shadow → asystent → ograniczona autonomia → wycofanie, z bramką i metryką na każdym przejściu; mapowanie na poziomy autonomii pdi 3→0 (DA1/DA2) | 06 | F3 | pdi P3; Flags S1 (§2.5) jako mechanizm przełączenia |
| T10 | **Role ludzi ↔ persony**: AI Champion, Data Owner, Product Owner AI w `proc-team-topologies` i `core-delivery-lifecycle`; RACI jako tabela w dokumencie operating model | 06 | F1 | D-P4 |
| T11 | **`pack-retail`** (handel: sklep, kierownik, asortyment, płatności) — dopiero gdy pierwszy asystent retail wejdzie do fali | 05 | F4 | brak dziś użytkownika; [założenie] że retail wchodzi w falę 2 |
| T12 | **Sandbox dla agentów operacyjnych**: `sandbox.settings.json` + `cleanroom.json` z profilem `operational` (tylko odczyt danych produkcyjnych przez MCP, bez Bash, wyjście tylko przez ai-gateway) | 03 | F3 | pdi `phase_sandbox.py` (L5, Z8a) jako baza |

### 2.2 pdi (decyzje, kontrakt, orkiestracja)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| P1 | **Dokument operating model** `docs/16-operating-model.md`: kto zatwierdza B1–B5 i w jakim SLA, co gdy nie zatwierdzi (eskalacja, decyzja domyślna), Business Owner pilotażu, RACI CoE ↔ zespoły; przyjęty jako decyzja w `decyzje.md` | 06 | F1 | D-P4 — **to blokuje wszystko, co ma bramkę** |
| P2 | **Operating model dla AI w operacjach**: kto odpowiada za decyzję asystenta, za model predykcyjny, za jego wycofanie; rozszerzenie `autonomy.schema.json` o `owner_role` i `withdrawal_trigger` | 06 | F3 | P1, T9 |
| P3 | **Nowy typ bramki `operational-ai`** w skrzynce (decyzja operacyjna AI: zmiana ceny, zlecenie serwisu, profil mocy) z SLA zatwierdzenia i typem chronionym (nigdy poniżej poziomu 3 do czasu decyzji właściciela); zdarzenie `gate.requested` od ev-assistant | 04 | F3 | kontrakt; ev-assistant A3 |
| P4 | **`targets` z progami ewaluacji jako warunek B5**: `gate.requested` z tf niesie wynik `eval-gate`; skrzynka pokazuje próg vs wynik; `not_met` → pętla DZ6 | 02 | F2 | T4 |
| P5 | **Kontrakt**: schematy `agent-audit-event`, `ai-system` (wpis inwentarza), `eval-result`, `llm-call` (sumaryczny rekord bramki); wersja 0.15 | 03, 04 | F1 | D-P3 rozstrzyga, czy to jeszcze `pdi/contract/`, czy nowe repo `contract` |
| P6 | **DPIA jako artefakt fazy** `requirements` dla zmian z danymi osobowymi: szablon w trybie pdi, sprawdzany przez `decision_record.py check`; skill `arch-privacy-compliance` daje treść | 04 | F3 | pierwsza DPIA: łączenie profilu EV + retail (gdy pojawi się taka zmiana) |
| P7 | **Instalacja tf w pdi** (TODO.md, odłożone 2026-10-28) — bez tego repo autora nie stosuje własnego standardu; T2 wykryje to jako pierwsze | 06 | F1 | D-P5 |
| P8 | **Konsola pdi / jedna platforma** (G6, P1 z `15-jedna-platforma.md`): to jest interfejs dla ludzi w SDLC (PO, dev); nie rozciągać jej na dyspozytora i sklep — to ev-assistant (§3.3) | 05 | wg planu Z3/A7 | decyzja G6/P1 (otwarta) |

### 2.3 ci_for_sdlc (spójność definicji)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| C1 | **Wywołania modelu przez ai-gateway**: `ai/providers.ts` dostaje dostawcę `gateway` (OpenAI-zgodny endpoint, nagłówek z identyfikatorem przestrzeni i celu); limit $50/przestrzeń (T4) zostaje jako limit aplikacji, bramka liczy limit organizacji | 03, 05, 07 | F1 | ai-gateway G1; zmiana zmiennych, nie kodu (`AI-PLATFORM.md` §1) |
| C2 | **Zestaw ewaluacyjny recenzenta jako eval-gate**: `spec-review.cases.json` + raport z `AI-QUALITY-PLAN.md` krok 2 uruchamiany w CI z progiem (czułość, zmyślone cytaty) — ten sam format wyniku co T4 | 02 | F2 | T4 |
| C3 | **Skille z tf zamiast kopii** (~100 w `.claude/skills`): instalacja `tf` z `pack-it` + `pack-docs`, własne skille produktu w `.tf/config/`; nocna „parity z tf” zostaje jako test regresji migracji | 05 | F4 | D-P5 (ta sama decyzja co P7); `tf doctor` po migracji |
| C4 | **Wpis w inwentarzu AI**: recenzent specyfikacji (prompt `SYSTEM_PROMPT`, model, region, klasa ryzyka) rejestrowany w ai-registry przy wdrożeniu; `GET /ai/usage` zasila księgę wartości | 04, 07 | F2 | ai-registry R1 |
| C5 | **Reguły gotowości dla zmian AI**: nowy wymiar `ai` (czy zmiana z modelem ma: wpis w inwentarzu, klasę AI Act, zestaw ewaluacyjny z progiem, politykę danych) — ustalenie `GAP` zamiast gotowości | 04 | F3 | R1, R2; analogicznie do wymiaru `delivery` (DG5) |

### 2.4 ShipScope (status wydań, metryki)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| S1 | **Incydenty (G8)**: źródło incydentów (PagerDuty/Opsgenie/webhook ogólny) powiązane z wdrożeniem i zmianą → **change failure rate** i **MTTR** w `/api/service/v1/metrics` (dziś 3 z 4 DORA) | 07 | F2 | decyzja G8 (narzędzie incydentów, otwarta od 2026-10-27) |
| S2 | **Eksport do księgi wartości**: `metrics` i `flow` per zmiana (CHG) z kosztem zmiany z pdi (`cost_usd` z `sdlc-phase.yml`) jako jeden rekord `value-ledger-row` do ai-registry | 07 | F3 | ai-registry R5; kontrakt P5 |
| S3 | **Metryki modeli w produkcji na dashboardzie?** — **nie**: ShipScope mierzy wdrożenia i flagi, nie jakość predykcji. Drift i trafność idą do ai-registry (R6); ShipScope pokazuje tylko, *która wersja modelu* jest gdzie wdrożona (przez istniejące `version` i flagi) | 07 | — | świadome „nie rozciągać” |
| S4 | Wzorce bezpieczeństwa (RLS, sealed-box, safeFetch, OIDC, audyt ustawień) jako **lista kontrolna** dla ai-gateway i ai-registry — skill w tf `arch-service-security-baseline` z linkami do `server/lib/` | 03 | F1 | nic do zmiany w ShipScope; wzorzec do skopiowania |

### 2.5 ShipScope Flags

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| FL1 | **Typ flagi `ai-feature`** z etapami cyklu życia modelu zamiast on/off: `shadow` → `assist` → `limited-autonomy` → `off` (wycofanie); kolejność test→qa→prod i zależności jak dziś; `review by` obowiązkowe; link do wpisu w ai-registry (`aiSystemId`); każda zmiana etapu na PROD = pozycja `operational-ai` w skrzynce pdi (P3) | 06, 03 | F3 | T9; to realizuje wymóg nadzoru człowieka i „kill switch” bez nowego systemu |
| FL2 | Dziennik zmian Flags jako **wzorzec** dziennika agentów (autor z sesji, nigdy z body; retencja 730 dni; webhook) — do skopiowania w ai-registry R3 | 03 | F1 | nic do zmiany w Flags |

### 2.6 ev-testing (evtest)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| E1 | **evtest jako required check w repo CPMS**: Action `v1` (dziś `v0.1.1`), przykład `examples/ci/github-actions.yml` jako szablon w tf `pack-ev` (`ev-cpms-ci-gate`), pilot na stagingu CPMS (sesja „Platforma CI/CD dla EV”: potrzebne endpoint OCPP i logowanie) | 02 | F2 | CPMS poza repo [założenie: dostęp do stagingu CPMS zależy od organizacji] |
| E2 | **Wynik evtest do pdi**: `result.json` → `gate.requested` B5 z `targets` (reconnect p95, error rate) — ta sama droga co eval-gate T4, tylko domena zamiast modelu | 02 | F3 | P4 |
| E3 | V7 „AI: analiza przyczyn awarii” z roadmapy — wpis w inwentarzu AI od pierwszego prototypu (klasa ryzyka, dane: logi OCPP z ID tokenów → polityka danych R2) | 04 | F4 | R1, R2; nie wcześniej |

### 2.7 ev-intelligence (wiedza EV)

| # | Zadanie | Obszar | Fala | Uwagi / zależy od |
|---|---|---|---|---|
| K1 | **MCP przez ai-gateway** z tokenem per konsument (ev-assistant, tf, ci_for_sdlc); `ev_confidential_check` tylko dla tokenów wewnętrznych do czasu opinii prawnej (eMIP/Gireve, `DO-ZROBIENIA.md`) | 03, 05 | F2 | G1; polityka danych R2 |
| K2 | **Wspólny format eval-gate**: `evals/skill-gate.json` i `tools/skill_check.py` → format wyniku z T4; evale płatne dalej tylko za zgodą | 02 | F2 | T4 |
| K3 | **Luki tematyczne potrzebne governance**: NIS2 i EN 18031, RODO historii ładowań (źródła A, potem skill) — wejście do klasyfikacji AI Act i DPIA | 04 | F2 | `DO-ZROBIENIA.md` już to listuje |
| K4 | **Rejestr źródeł jako wzorzec „data lineage” dla modeli**: klasy A–D, SHA-256, licencja → pole `sources[]` wpisu `ai-system` w kontrakcie | 04 | F1 | P5 |

### 2.8 ev-domain-intelligence

| # | Zadanie | Obszar | Fala |
|---|---|---|---|
| D1 | **Manifest uruchomienia → ai-registry**: każdy raport zgłasza `run-manifest` (wersje źródeł, reguł, modelu, trafność oceniona przez człowieka) — to gotowa definicja pola `reproducibility` wpisu inwentarza i pierwsze dane do „% korekt przez człowieka” | 04, 07 | F2 |

### 2.9 aiux, sprintdeck, sdlc-proba

| Repo | Zadanie | Obszar | Fala |
|---|---|---|---|
| aiux | metodyka oceny → skill w `pack-data` (T1); sam eksperyment zostaje repo badawczym; wpis w inwentarzu (wirtualny panel = system AI klasy niskiego ryzyka [założenie]) | 02, 04 | F2 |
| sprintdeck | pierwszy cel `repo-standard-check` (T2); poza tym bez zmian | 01 | F2 |
| sdlc-proba | poligon dla T5 (required checks) i eval-gate T4 zanim wejdą do produktów | 02 | F2 |

### 2.10 Konsolidacja (05)

| # | Zadanie | Fala |
|---|---|---|
| X1 | Archiwizacja `ev-team-factory` (dubluje `pack-ev`); `claude-team-factory` — sprawdzić, czy to nie poprzednik tf, i zarchiwizować [niezweryfikowane] | F4 |
| X2 | ci_for_sdlc na packach z tf (C3) | F4 |
| X3 | Kontrakt do osobnego repo (D1 wyzwolone) z wydaniami `contract-v<wersja>`; tf, ci_for_sdlc, ShipScope, ai-gateway, ai-registry generują przypięte kopie | F1 |

## 3. Nowe aplikacje (to, co nie pasuje do żadnej istniejącej)

Kryterium: zadanie dotyczy innego **użytkownika**, innych **danych** lub innej **granicy zaufania** niż aplikacja,
do której kusiłoby je dokleić.

### 3.1 `ai-gateway` — bramka wywołań modeli

**Po co.** Dziś każde repo woła dostawcę modeli wprost (`@anthropic-ai/sdk` w aiux, `ai/providers.ts` w ci_for_sdlc,
Claude Code w tf, Bedrock w ci_for_sdlc T4). Nie ma jednego miejsca, w którym: (a) obowiązuje lista zatwierdzonych
modeli i regionów, (b) obowiązuje polityka danych (co wolno wysłać: dane klientów? logi OCPP z ID tokenów RFID?),
(c) liczony jest koszt per organizacja / projekt / agent, (d) powstaje log wywołań. Bez tego nie ma adopcji (07),
ROI (07), audytu (03) ani egzekwowania listy modeli (05). Odblokowuje trzy obszary naraz.

**Dlaczego nie w istniejącej aplikacji.** ci_for_sdlc ma już dostawców i limit, ale jest aplikacją jednej domeny
(spójność definicji) z własnymi przestrzeniami; tf jest instalowane w repo klienta i nie może być usługą; pdi
jest warstwą decyzji, nie ruchu sieciowego. Bramka to usługa infrastrukturalna o innej granicy zaufania (widzi
treść promptów każdej aplikacji).

**Buy/Build.** Kupić silnik (klasa LiteLLM / Portkey: routing, klucze wirtualne, logi, limity), zbudować cienką
warstwę polityki: `approved-models.yaml` (T6, wspólny z tf), reguły danych (klasyfikacja wejścia: `public` /
`internal` / `personal` / `confidential`, redakcja ID tokenów RFID i danych osobowych przed wysyłką do modelu
zewnętrznego), eksport zdarzeń `llm-call` do ai-registry. Wzorce bezpieczeństwa z ShipScope (S4): tokeny per
aplikacja z datą ważności, `safeFetch`, audyt zmian polityki.

**Zakres G1 (fala 1):** uruchomienie, klucze wirtualne per aplikacja (ci_for_sdlc, ev-intelligence, aiux, tf w CI),
lista modeli, limit kosztu per klucz, log `llm-call` (bez treści promptu; z hashem, tokenami, kosztem, modelem,
celem). **G2 (fala 2):** polityka danych z redakcją; alert przy modelu spoza listy. **G3 (fala 3):** adopcja
(aktywni użytkownicy/agenci dziennie per zespół) jako widok w ai-registry.

### 3.2 `ai-registry` — rejestr systemów AI i księga wartości

**Po co.** Pierwsze pytanie audytora i pierwszy wymóg Aktu o AI: *jakie modele, prompty i agenty działają, gdzie, od
kiedy, w jakiej klasie ryzyka, na jakich danych, kto za nie odpowiada*. Dziś nie ma tego nigdzie; wiedza o AI Act
jest w skillach tf (`dom-ev-regulations-eu`), ale bez procedury i bez wyniku. Do tego samego rejestru naturalnie
dochodzą: dziennik działań agentów (03), macierz uprawnień (03), księga wartości koszt × efekt (07) i metryki modeli
w produkcji (07) — wszystkie są **atrybutami albo zdarzeniami systemu AI**, więc jeden obiekt główny.

**Dlaczego nie w pdi.** pdi rejestruje **decyzje** (zdarzenia w czasie, z bramkami) i zmiany; inwentarz AI to
rejestr **obiektów z cyklem życia** (jak rejestr flag w Flags), dla innego odbiorcy (compliance, kontroling,
audytor, nie PO) i z innym poziomem dostępu. Ocena z 8 XI dopuszczała „pdi lub nowy moduł”; po sprawdzeniu
`contract/` i `decyzje.md` rekomenduję nowy — a pdi dostaje tylko typ bramki `operational-ai` (P3) i link
`ai_system` w decyzjach, bo decyzje o AI dalej są decyzjami.

**Moduły (jedno repo, jedna usługa):**

| Moduł | Co trzyma | Skąd dane | Fala |
|---|---|---|---|
| R1 inwentarz | wpis `ai-system`: typ (model/prompt/agent/skill), wersja, właściciel (rola z RACI), gdzie działa, klasa ryzyka AI Act, dane wejściowe (klasa), źródła (K4), manifest odtwarzalności (D1), status cyklu życia (T9) | ręcznie na start (ci_for_sdlc, tf persony, ev-intelligence, ev-domain-intelligence, aiux, pdi triaż), potem z CI | F1 (yaml), F2 (usługa) |
| R2 klasyfikacja i polityka danych | procedura klasyfikacji wg AI Act jako skill tf + szablon decyzji (wynik zapisany w R1); polityka danych per system (co wolno wysłać) → reguła w ai-gateway | skill `arch-ai-act-classification` (nowy w pack-it) | F1 (procedura), F2 (egzekwowanie) |
| R3 dziennik agentów | `agent-audit-event` z hooków tf (T7) i `llm-call` z bramki: który agent, model, narzędzie, co zmienił, kto zatwierdził; wzorzec z Flags (FL2) | tf, ai-gateway | F2 |
| R4 macierz uprawnień | agent (klasa) → system → operacja `read/propose/execute`; eksport do tf (T8) i bramki | ręcznie, zatwierdzane jako decyzja w pdi | F3 |
| R5 księga wartości | inicjatywa × miesiąc × koszt × korzyść × źródło; właściciel: kontroling; koszt z bramki i `sdlc-phase.yml`, efekt z ShipScope (S2) i ocen skutku pdi; adopcja z bramki | ai-gateway, ShipScope, pdi | F3 |
| R6 metryki modeli | drift, trafność, koszt per decyzja, % korekt przez człowieka (z D1 i ev-assistant) | aplikacje przez kontrakt | F4 |
| R7 DPIA | artefakt per system/zmiana (P6) z datą przeglądu | tf (szablon), pdi (bramka) | F3 |

Stack: ten sam co pdi (Python, serwer MCP, pliki YAML w repo na start, baza dopiero przy R3, bo dziennik rośnie)
[założenie; do decyzji jak DA4 dla pdi].

### 3.3 `ev-assistant` — kanał dla ludzi spoza IT

**Po co.** Dyspozytor, analityk roamingu, kierownik sklepu nie dostaną nic z Claude Code i terminala (05). Asystenci
fali 1 potrzebują kanału (czat w Teams/Slack, formularz, panel) nad **tymi samymi** serwerami MCP, które już są
(ev-intelligence, ShipScope read-only, pdi, w przyszłości odczyt CPMS). Do tego sandbox dla agentów operacyjnych
(03): czytają dane produkcyjne, więc inna granica niż sandbox wytwarzania z pdi (L5/Z8a).

**Dlaczego nie konsola pdi.** Konsola pdi (`15-jedna-platforma.md`) jest dla ludzi **w procesie wytwarzania**
(PO, dev, QA): zmiany, bramki, wydania. Dyspozytor nie ma tam nic do roboty; mieszanie odbiorców rozmyłoby oba
produkty.

**Zakres A1 (fala 3):** bot Teams/Slack + cienki panel; jedna persona (dyspozytor) z `pack-ev` tf; wszystkie
wywołania modeli przez ai-gateway; każda odpowiedź z cytatem (`ev_cite`) albo oznaczona [hipoteza] (wzorzec
ev-domain-intelligence); poziom autonomii 3 (tylko propozycje). **A2:** ocena trafności przez człowieka
(👍/👎 + korekta) → R6. **A3:** propozycja działania (zlecenie serwisu, profil mocy) → `gate.requested`
`operational-ai` do pdi (P3); wykonanie dopiero po zatwierdzeniu; etap `assist`/`limited-autonomy` sterowany flagą
`ai-feature` (FL1).

### 3.4 Czego **nie** proponuję jako nowej aplikacji

- **Eval-gate dla modeli** — to narzędzie w tf (T4) z wynikiem w pdi (P4), nie usługa.
- **Dashboard adopcji / ROI** — widok w ai-registry (R5), nie osobna aplikacja.
- **Repo kontraktu** — to wydzielenie istniejącego `pdi/contract/` (X3), nie nowy produkt.

## 4. Plan wdrożeniowy

Założenia: jeden właściciel decyzji, praca w sesjach Claude Code na repo (jak dotąd), każdy punkt = osobny PR
w swoim repo (zasada z planu jednego flow), tygodnie liczone od przyjęcia decyzji D-P1…D-P6. Czas podany jako
przedział, bo blokada płatności GitHub Actions (T5) i dostęp do stagingu CPMS (E1) są poza repo.

### Fala 1 — Odblokowanie (tygodnie 1–6)

Cel: trzy rzeczy, które blokują resztę: bramka, inwentarz, operating model.

| Tydz. | Krok | Repo | Wynik |
|---|---|---|---|
| 1 | Decyzje D-P1…D-P6 zapisane w `pdi/docs/decyzje.md` | pdi | ADR per decyzja |
| 1–2 | P1 operating model (RACI, SLA bramek, eskalacja) | pdi | `16-operating-model.md` przyjęty |
| 1–2 | R1 inwentarz v0: `ai-systems.yaml` wypełniony ręcznie dla 7 istniejących systemów AI; R2 procedura klasyfikacji jako skill | ai-registry (nowe repo), tf | pierwszy wynik klasyfikacji AI Act |
| 2–3 | X3 repo `contract` z wersją 0.15: schematy P5 | contract (nowe repo z `pdi/contract/`) | `contract-v0.15.0` |
| 2–5 | G1 ai-gateway: silnik + klucze per aplikacja + `approved-models.yaml` (T6) + log `llm-call` | ai-gateway (nowe repo), tf | ci_for_sdlc (C1) i ev-intelligence (K1) wołają model przez bramkę |
| 3–4 | P7 instalacja tf w pdi; T10 role ludzi w skillach | pdi, tf | `tf doctor` czysty w pdi |
| 4–6 | S4 lista kontrolna bezpieczeństwa usług; K4 pole `sources[]`; FL2 wzorzec dziennika | tf, contract | — |

**Kryterium wyjścia:** każde wywołanie modelu w ci_for_sdlc i ev-intelligence przechodzi przez bramkę z kosztem
w logu; każda bramka B1–B5 ma nazwanego zatwierdzającego i SLA; każdy działający system AI ma wpis z klasą ryzyka.

### Fala 2 — Egzekwowanie (tygodnie 7–12)

| Krok | Repo | Zależy od |
|---|---|---|
| T2 `repo-standard-check` w `tf doctor` + CI; pierwszy przebieg na sprintdeck, pdi, ci_for_sdlc | tf | fala 1 |
| T4 `eval-gate` + P4 próg w B5 + C2/K2 wspólny format; poligon na sdlc-proba | tf, pdi, ci_for_sdlc, ev-intelligence | T6 |
| T5 przegląd AI jako required check | tf, sdlc-proba | płatność GitHub Actions |
| T1 `pack-data` (model card, data contract, eval dataset, `data-ai-evaluation` z aiux) | tf | — |
| T7 + R3 dziennik agentów (tf hooki → ai-registry); R1 jako usługa z MCP; C4, D1 wpisy automatyczne | tf, ai-registry, ci_for_sdlc, ev-domain-intelligence | contract 0.15 |
| G2 polityka danych z redakcją w bramce | ai-gateway, ai-registry | R2 |
| S1 incydenty → CFR i MTTR | ShipScope | decyzja G8 |
| E1 evtest `v1` + szablon w `pack-ev` + pilot na stagingu CPMS | ev-testing, tf | dostęp do CPMS |
| K3 źródła NIS2 / RODO historii ładowań; T3 jeden język instrukcji | ev-intelligence, tf | D-P6 |

**Kryterium wyjścia:** PR bez przeglądu AI i bez zielonego eval-gate (gdy zmiana ma `targets`) nie wchodzi na `main`
w sdlc-proba i w jednym produkcie; dziennik agentów ma wpisy z co najmniej dwóch repo; 4 z 4 metryk DORA w ShipScope.

### Fala 3 — Operacje i biznes (tygodnie 13–20)

| Krok | Repo | Zależy od |
|---|---|---|
| P2 operating model dla AI w operacjach; T9 cykl życia modelu; FL1 flaga `ai-feature` | pdi, tf, Flags | P1 |
| P3 bramka `operational-ai`; T12 sandbox operacyjny | pdi, tf | P2 |
| A1–A3 ev-assistant (dyspozytor) | ev-assistant (nowe repo) | G1, K1, P3, FL1 |
| R4 macierz uprawnień + T8 egzekwowanie w hookach | ai-registry, tf | R3 |
| R5 księga wartości + S2 eksport z ShipScope + G3 adopcja z bramki | ai-registry, ShipScope, ai-gateway | R1, S1 |
| P6/R7 DPIA jako artefakt fazy; C5 wymiar gotowości `ai` | pdi, tf, ai-registry, ci_for_sdlc | R2 |
| E2 wynik evtest do B5 | ev-testing, pdi | P4 |

**Kryterium wyjścia:** pierwszy asystent dla biznesu działa na żywych danych w poziomie 3 z oceną trafności;
kontroling widzi koszt i efekt jednej inicjatywy w jednym miejscu; żaden agent operacyjny nie ma `execute` bez
wpisu w macierzy.

### Fala 4 — Konsolidacja (tygodnie 21–26)

X1 archiwizacja ev-team-factory (i claude-team-factory po sprawdzeniu), X2/C3 ci_for_sdlc na packach tf, R6 metryki
modeli (drift, % korekt), T11 `pack-retail` (jeśli asystent retail wchodzi), E3 wpis dla V7 evtest.

### Co w pierwszych 6 tygodniach i dlaczego

Zgodnie z oceną: **bramka** (odblokowuje 03, 05, 07), **inwentarz + klasyfikacja** (04, warunek pilotaży na żywych
danych) i **operating model z RACI** (06, bez niego bramki pdi nie mają kto zatwierdzać). Z przeglądu repo dochodzi
czwarta, tania: **instalacja tf w pdi** (P7) — bez niej `repo-standard-check` z fali 2 jako pierwsze oflaguje repo
autora, co podważy wiarygodność standardu.

## 5. Decyzje do podjęcia przed startem

| ID | Decyzja | Rekomendacja | Powód |
|---|---|---|---|
| D-P1 | ai-gateway: buy (LiteLLM/Portkey-class) + build polityki, czy build od zera | **buy + build** | routing, klucze i logi są towarem; wartość jest w polityce danych i w integracji z inwentarzem |
| D-P2 | Rejestr systemów AI jako nowa aplikacja `ai-registry` czy moduł pdi | **nowa aplikacja** | inny odbiorca (compliance, kontroling), inny obiekt (system z cyklem życia, nie decyzja), inny poziom dostępu; pdi dostaje tylko typ bramki i link |
| D-P3 | Kontrakt do osobnego repo (D1: „przy czwartym konsumencie”) | **tak, w fali 1** | ai-gateway i ai-registry to konsumenci 4 i 5; przypięte kopie już działają (tf #93, ci_for_sdlc #85) |
| D-P4 | Operating model: kto zatwierdza B1–B5, SLA, eskalacja, Business Owner pilotażu, RACI CoE ↔ zespoły | **spisać w fali 1, tydzień 1–2** | to decyzja organizacyjna, nie kod; blokuje fale 2–3 |
| D-P5 | Instalacja tf w pdi i migracja ci_for_sdlc na packi (odłożone 2026-10-28) | **pdi w fali 1, ci_for_sdlc w fali 4** | pdi: tanie, rekomendacja z TODO.md gotowa; ci_for_sdlc: 100 skilli, zrobić po parity i po `repo-standard-check` |
| D-P6 | Jeden język instrukcji dla agentów | **polski w fabryce, angielski tylko w repo publikowanych na zewnątrz (ShipScope, Flags)** — albo odwrotnie, ale jedna reguła | dziś trzy style; `repo-standard-check` musi wiedzieć, czego pilnować |

Poza tym otwarte od wcześniej i potrzebne tu: **G8** (narzędzie incydentów → S1), **G6/P1** (jedna platforma →
P8), **DA4** (stack usługi pdi → ten sam dla ai-registry), płatność **GitHub Actions** (→ T5, E1).

## 6. Ryzyka

| Ryzyko | Skutek | Zabezpieczenie |
|---|---|---|
| Trzy nowe repo naraz przy jednoosobowym zespole | rozproszenie, nic nie dochodzi do „działa samo” | fala 1 tylko G1 i R1 w formie plików; ev-assistant dopiero w fali 3 |
| Bramka jako pojedynczy punkt awarii dla wszystkich aplikacji | przestój AI we wszystkich produktach | tryb awaryjny per aplikacja (ci_for_sdlc już działa bez AI po limicie, T4); SLO i status jak w ShipScope (`SLO.pl.md`) |
| Polityka danych zbyt ostra | asystent bez dostępu do danych, które są mu potrzebne | klasy danych per system (R2), nie globalnie; decyzja właściciela danych (Data Owner z RACI) |
| Operating model spisany, ale nieprzyjęty przez organizację | bramki dalej bez zatwierdzających | P1 jako decyzja z datą przeglądu i miarą: % bramek zatwierdzonych w SLA (z pdi `stats.py`) |
| Brak dostępu do CPMS i stagingu | E1/E2 nie wchodzą | ev-testing działa na mock CPMS i SteVe; required check najpierw na nich |
| Koszt evali w CI | zestawy płatne na każdym PR | eval-gate z budżetem i progiem (jak `skill_gate.py`); pełny zestaw tylko na `main` i co noc |

## 7. Czego ocena nie uwzględniła, a repo pokazują

- **Jev** (prompt-injection, cytaty z `sdlc-proba`) jest już w tf jako hooki `jev_guard.py`/`jev_client.py` — zadanie
  z 03 „osłona przed injection” jest zrobione tam, gdzie powinno; brak tylko eksportu zdarzeń do dziennika (T7).
- **Poziomy autonomii i licznik akceptacji** w pdi (DA1/DA2: obniżenie poziomu po 95% szkiców bez zmian w 30
  decyzjach) to gotowa mechanika dla cyklu życia modelu (T9) i dla „% korekt przez człowieka” (R6) — nie trzeba
  wymyślać nowej.
- **ev-domain-intelligence** ma manifest uruchomienia, czyli odtwarzalność raportu AI — ocena wymienia to w 04,
  ale to także gotowe pole inwentarza (D1), nie osobne zadanie.
- **ci_for_sdlc** ma już limit kosztu AI per przestrzeń i panel operatora (T4) — bramka nie zastępuje tego,
  tylko dodaje poziom organizacji.

## 8. Poza zakresem tego planu

Ten plan to **platforma i governance dla AI w wytwarzaniu oprogramowania** plus pierwszy pilot asystenta
operacyjnego. Ocena siedmiu obszarów, z której wyszedł, była oceną inżynierską, więc plan **nie jest** pełnym
programem wdrożenia AI w organizacji. Brakuje w nim ośmiu rzeczy; żadna nie powinna trafić do repozytoriów jako kod,
ale każda musi mieć właściciela i dokument, zanim platforma zacznie być używana poza zespołem autora.

| # | Obszar | Czego nie ma | Co w planie tego dotyka | Gdzie to powinno żyć |
|---|---|---|---|---|
| Z1 | **Portfel przypadków użycia** | lista procesów biznesowych, które dostaną AI, kolejność, oczekiwany efekt, ocena (RICE/WSJF) | bez niego ai-registry (R1) i księga wartości (R5) są puste; ev-assistant (A1) ma tylko jedną personę | dokument sponsora biznesowego; narzędzia są (triaż pdi, `proc-product-discovery`, `proc-lean`) |
| Z2 | **Ludzie i zmiana** | szkolenia, ścieżki kompetencji, zasady dopuszczalnego użycia AI przez pracowników, komunikacja, adopcja mierzona u ludzi, nie tylko w logach bramki | AI Champion i Data Owner to role w RACI (T10, P1), nie program | HR i CoE; polityka użycia AI jako krótki dokument w fali 1, obok operating modelu |
| Z3 | **Fundament danych i MLOps** | platforma danych, jakość i pochodzenie danych, cechy, trening i serwowanie modeli predykcyjnych | `pack-data` (T1) daje metodę i standard, eval-gate (T4) bramkę; infrastruktury nie ma | osobny plan; obszar 01 szacuje, że to 30–50% kodu programu |
| Z4 | **AI zwrócone do klienta** | czat dla kierowców, reklamacje, personalizacja: zgody, RODO wobec klientów, obowiązki informacyjne z Aktu o AI, ryzyko reputacyjne | ev-assistant jest dla pracowników; DPIA (P6) i klasyfikacja (R2) obejmą też te systemy, gdy powstaną | portfel (Z1) decyduje, czy i kiedy; wtedy osobny plan z prawnikiem |
| Z5 | **Zgodność formalna** | ocena zgodności i rejestracja systemów wysokiego ryzyka, umowy z dostawcami modeli (DPA, region, retencja), licencje danych, ubezpieczenie, audyt zewnętrzny | inwentarz (R1) i polityka danych (R2) są wejściem do tego, nie wynikiem; licencja eMIP/Gireve już jest otwarta w ev-intelligence | compliance i dział prawny |
| Z6 | **Bezpieczeństwo operacyjne AI** | procedura incydentu AI (prompt injection na produkcji, wyciek przez model, halucynacja ze skutkiem), red teaming, monitoring nadużyć | plan ma prewencję (hooki, sandbox T12, bramka G2), nie reakcję; skill `ops-security-operations` jest, procedury nie | SOC/bezpieczeństwo; procedura incydentu AI jako krótki dokument w fali 1 |
| Z7 | **Organizacja, budżet, dostęp** | skład i etaty CoE, budżet na modele i infrastrukturę, zakupy (silnik bramki, narzędzie incydentów G8), SSO i role dla trzech nowych aplikacji | operating model (P1) nazywa role, nie etaty; S4 daje listę kontrolną bezpieczeństwa, nie tożsamość | sponsor i IT; decyzja o tożsamości wspólnej (jak G6/P1 dla jednej platformy) |
| Z8 | **Infrastruktura modeli** | buy czy host, GPU, regiony, koszt jednostkowy | skill `ops-ai-inference` jest; bramka (G1) ukrywa wybór przed aplikacjami, ale go nie podejmuje | decyzja architektoniczna po portfelu (Z1), bo zależy od wolumenu i klas danych |

Do tego jedno założenie planu, które w organizacji przestaje być prawdą: **zdolność wykonawcza**. Plan zakłada
jednoosobowy zespół pracujący w sesjach Claude Code. Wdrożenie poza tym zespołem wymaga ludzi po stronie zespołów
produktowych i biznesu (właściciele danych, zatwierdzający bramki, użytkownicy pilotażu), których plan nie nazywa
i nie szacuje.

**Jak to domknąć.** Nadrzędny dokument „program AI w organizacji” z ośmioma obszarami powyżej, w którym ten plan
jest jedną z części. Właścicielem jest sponsor biznesowy, nie CoE. Pierwszy krok to portfel (Z1), bo wyznacza,
co wchodzi do inwentarza, do księgi wartości i do ev-assistant. Dwa krótkie dokumenty (polityka użycia AI z Z2,
procedura incydentu AI z Z6) można napisać już w fali 1, obok operating modelu, bo nie zależą od portfela.
