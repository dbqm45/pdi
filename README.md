# pdi — Product Decision Intelligence

Warstwa decyzji w procesie AI-native SDLC: zgłoszenia problemów, triaż, rejestr decyzji, skrzynka bramek,
orkiestracja etapów, graf śladu od zgłoszenia do wydania na PROD i ocena skutku decyzji. Współpracuje z tf
(fabryka agentów), ci_for_sdlc (kontrola spójności definicji) i ShipScope (status wydań).

Stan: **krok 1 trybu standalone zbudowany** — rejestr decyzji, serwer MCP i komenda `/record-decision`
([instalacja w Claude Code](integrations/claude-code/README.md)) — oraz skrzynka bramek z orkiestracją zmian
(G1.5 i strona pdi F4, niżej). Reszta flow SDLC na etapie planu.

Praca z kodem: `uv sync`, potem `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
`uv run mypy src` (te same kroki w CI: `.github/workflows/ci.yml`). Walidacja na sobie: [`eval/dogfood/`](eval/dogfood/README.md). Kod: `src/pdi/`, kontrakt 0.3.0 (decyzja, zgłoszenie, zmiana, cięcie, zdarzenia): [`contract/`](contract/README.md), plan kroku: [`docs/plan-krok-1.md`](docs/plan-krok-1.md).

## Skrzynka bramek i orkiestracja (G1.5, F4)

ShipScope wysyła podpisane zdarzenia kontraktu: `release.stage_changed` (flaga z planu wydania przeszła na PROD do
innego etapu) i `feature.released` (linia wydania u ludzi; `release: R1` = MVP). `pdi-receiver` je odbiera,
sprawdza podpis i schemat, a w katalogu rejestru zapisuje pozycje `inbox/<ID zdarzenia>.yaml` (z commitem, gdy to
repo git): bramkę dla zmiany etapu. W Claude `list_inbox` pokazuje, co czeka,
a `decide_inbox_item` zapisuje decyzję (`kind: gate` z wynikiem albo `kind: product`, zawsze z `links.chg`) i zamyka
pozycję. Wydanie MVP planuje ocenę skutku (niżej). Plan i zakres: [`docs/plan-g15-pdi.md`](docs/plan-g15-pdi.md).

Od F4 ([plan](docs/plan-f4-pdi.md)) skrzynka przyjmuje też `gate.requested` z tf i ci_for_sdlc (B1, B2, B3,
`design-review`, `approve-for-implementation`, B4, B5) oraz `readiness.changed` z ci_for_sdlc (`ready` = prośba o
„Approve for implementation”). Stan każdej zmiany jest w `changes/<CHG>.yaml`: zatwierdzone bramki, na co czeka,
gotowość, wydane linie, historia. Decyzja na bramce zostawia `gate.decided` w `outbox/` i uruchamia następną fazę
tf przez `workflow_dispatch` (po `changes_requested` — poprawki tej samej fazy). `list_changes`, `get_change` i
`retry_dispatch` w Claude pokazują i ponawiają.

```bash
PDI_REGISTRY_PATH=~/pdi-decisions \
PDI_SHIPSCOPE_SIGNING_SECRET=<sekret podpisu z ShipScope: Settings → Sources> \
PDI_TF_SIGNING_SECRET=<sekret wspólny z tf> PDI_CI_FOR_SDLC_SIGNING_SECRET=<sekret wspólny z ci_for_sdlc> \
PDI_DISPATCH_REPO=<właściciel/repo produktu> PDI_GITHUB_TOKEN=<token z prawem actions:write> \
uv run pdi-receiver        # http://127.0.0.1:8787/events/<shipscope|tf|ci_for_sdlc>
```

Wystarczy jeden sekret; ścieżka nadawcy bez sekretu odpowiada 404. tf i ci_for_sdlc podpisują tak samo jak ShipScope,
w nagłówkach `X-PDI-Timestamp`, `X-PDI-Event`, `X-PDI-Signature`. Szablon fazy (`PDI_DISPATCH_WORKFLOW`, domyślnie
`sdlc-phase.yml` na `PDI_DISPATCH_REF`, domyślnie `main`) dostaje wejścia `change`, `phase`, `gate`, `outcome`,
`decision`, `rework` i `budget_usd` (`PDI_PHASE_BUDGET_USD`). Bez `PDI_DISPATCH_REPO` decyzje się zapisują, a faza
jest oznaczona `skipped`. Ten sam `PDI_DISPATCH_*` musi być ustawiony dla serwera MCP, który zapisuje decyzje.

Decyzja na bramce `approve-for-implementation` trafia też do ci_for_sdlc: podpisane `gate.decided` na
`PDI_CI_FOR_SDLC_URL/api/webhooks/pdi` (sekret `PDI_CI_FOR_SDLC_SIGNING_SECRET`, ten sam, którym ci_for_sdlc podpisuje
`readiness.changed`; tam `PDI_SIGNING_SECRET`). ci_for_sdlc zatwierdza wtedy historyjki zmiany (etykieta `change:CHG-n`)
z numerem decyzji. Nieudana wysyłka zostaje w stanie zmiany (`ci_for_sdlc.status: failed`); `retry_dispatch` ją ponawia.

ShipScope wysyła tylko na publiczny adres `https://`, więc przed odbiornikiem stoi proxy TLS albo tunel (np.
Cloudflare Tunnel); ten adres z `/events/shipscope` dodaje admin w ShipScope: Settings → General → Outgoing events.
Odbiornik obsługuje jedno żądanie naraz i przyjmuje najwyżej 64 KB; 2xx kończy ponowienia ShipScope.

### Ocena skutku (F5)

`feature.released` z `release: R1` planuje ocenę skutku MVP w stanie zmiany (`impact_review.due`): `review_by` decyzji
o intencji (najnowszej obowiązującej z `links.chg` i `success_metric`), albo dzień wydania + `success_metric.horizon`
(„30 dni”, „4 tygodnie”, `P30D`), albo + 30 dni. Raz dziennie `pdi-impact-review` (cron; w Claude
`open_due_impact_reviews`) otwiera pozycje `impact-<CHG>-R1`, których termin minął: czyta z API usług ShipScope status
zmiany i dzienny szereg PROD od wydania i szkicuje wniosek (`draft.verdict`). `met`/`not_met` tylko dla metryki z
ShipScope (`deployments`, `failed_deployments`, `rollbacks` — suma; `lead_time_days_median` — mediana) z celem typu
`<= 1`; inaczej `unknown` z powodem. Człowiek potwierdza wynik: `decide_inbox_item` z `outcome` `met`, `not_met` albo
`unknown`; decyzja zależy od decyzji o intencji i dostaje odczyt jako dowód. Plan:
[`docs/plan-f5-ocena-skutku.md`](docs/plan-f5-ocena-skutku.md).

```bash
PDI_REGISTRY_PATH=~/pdi-decisions PDI_SHIPSCOPE_URL=https://<ShipScope> \
PDI_SHIPSCOPE_TOKEN=<token usługi shps_… z ShipScope: Settings → General → Service tokens> \
uv run pdi-impact-review   # {"opened": [{"id": "impact-CHG-12-R1", "change": "CHG-12", "verdict": "met"}]}
```

Bez `PDI_SHIPSCOPE_URL` pozycja otwiera się z `unknown` i błędem w `data.errors`. Te same `PDI_SHIPSCOPE_*` ustawia się
dla serwera MCP.

### Graf śladu (F5)

`get_trace(change)` w Claude składa graf jednej zmiany: PRB → CHG → bramki i decyzje → TSK → PR → wdrożenia
(TEST/QA/PROD, status z API usług ShipScope) → wydania → ocena skutku. Źródła to rejestr decyzji (`links.prb`,
`links.tsk`, `links.pr`), stan zmiany, skrzynka i zadania z `feature.released`. Wynik: `nodes`, `edges`, `gaps` (luki,
np. brak PRB, PR albo zamkniętej oceny skutku — do pokazania, nie do naprawiania) i `mermaid` (flowchart do
wklejenia). `live=false` nie pyta ShipScope; przy `live` najwyżej 20 odczytów na graf. Plan:
[`docs/plan-f5-graf-sladu.md`](docs/plan-f5-graf-sladu.md).

### Problemy z pasm kontrolnych tf (F5)

tf (`metric_watch.py check --send`, tryb `mode-pdi`) wysyła na `/events/tf` podpisane `metric.breached`, gdy metryka
PROD z ShipScope wyjdzie poza 3σ. Skrzynka otwiera wtedy pozycję `kind: problem` („nowy problem do triażu”), którą
`decide_inbox_item` zamyka z `outcome` `accepted` albo `rejected` jako decyzję `kind: triage` z odczytem pasma jako
dowodem. Plan: [`docs/plan-f5-metric-breached.md`](docs/plan-f5-metric-breached.md).

### Zgłoszenia i powiadomienia zgłaszającego (F5)

`record_problem` zapisuje zgłoszenie `problems/PRB-n.yaml` w kształcie `contract/problem.schema.json` (kto nie może
czego, z jakim skutkiem, od kogo i którędy); `triage_problem` (`accepted` ze zmianą, `rejected`, `parked`,
`duplicate`) zapisuje decyzję `kind: triage` z `links.prb` i wynik w zgłoszeniu. Zgłaszający dostaje podpisane
`problem.notification` na `PDI_NOTIFY_URL` (sekret `PDI_NOTIFY_SIGNING_SECRET`, nagłówki `X-PDI-*`) po triażu, po
wydaniu zmiany z tego zgłoszenia (każda linia) i po ocenie jej skutku; odbiorca (workflow Slacka, przekaźnik e-mail,
automatyzacja Jiry) wybiera kanał po `reporter` i `channel`. Dziennik wysyłek: `notifications/<PRB>.yaml`;
`retry_problem_notifications` ponawia. Te same `PDI_NOTIFY_*` ustawia się dla serwera MCP i `pdi-receiver`. Pełny
intake zgłoszeń to F3. Plan: [`docs/plan-f5-powiadomienia.md`](docs/plan-f5-powiadomienia.md).

### Intake, wzbogacenie i przyjęcie do budowy (F3)

- **Formularz**: z `PDI_FORM_TOKEN` odbiornik podaje `GET /problems/new?t=<token>` (strona bez skryptów) i przyjmuje
  `POST /problems`; zgłoszenie dostaje `channel: form`, a strona po zapisie pokazuje numer i podobne zgłoszenia. Link z
  tokenem rozsyła się zgłaszającym (np. w Slacku albo intranecie); bez tokenu ścieżki odpowiadają 404.
- **Claude**: `clarify_problem` (3–5 pytań, status `clarifying`, pytania idą do zgłaszającego powiadomieniem),
  `update_problem` (opis, `ready` → `ready_for_triage`), `find_similar_problems`.
- **Wzbogacenie**: triaż `duplicate` dopisuje oryginałowi liczbę zgłoszeń, dowód i powiązanie; odłożone z progiem „N
  nowe zgłoszenia” wraca do triażu po tylu duplikatach.
- **Przyjęcie**: `triage_problem` z `accepted` bez `change` nadaje kolejny `CHG-n`, zakłada stan zmiany, zostawia
  `problem.accepted` w `outbox/` i uruchamia w tf fazę `intent` (wejścia `source` i `problem`); persona tf pisze
  `intent.md`, otwiera PR i prosi o B1. Plan: [`docs/plan-f3-pdi.md`](docs/plan-f3-pdi.md).

## Kierunek (od 2026-10-23)

- [`docs/14-pdi-standalone.md`](docs/14-pdi-standalone.md) — **pierwszy krok: pdi jako niezależny rejestr decyzji** z zapisem jednym kliknięciem tam, gdzie decyzje zapadają (najpierw Claude CLI przez MCP i `/record-decision`, potem Slack, Confluence, Jira); flow SDLC korzysta z tego samego rejestru. Specyfikacja MVP i kryteria walidacji na sobie.

- [`docs/decyzje.md`](docs/decyzje.md) — decyzje właściciela (przyjęte: D1 kontrakt w [`contract/`](contract/README.md), D2/R1 podział rejestru decyzji).
- [`docs/plan-jeden-flow-sdlc.md`](docs/plan-jeden-flow-sdlc.md) — plan połączenia czterech projektów w jeden flow (fazy F0–F6, decyzje D1–D7).
- [`docs/plan-g1-g2.md`](docs/plan-g1-g2.md) — plan domknięcia luk G1 (plan wydania i MVP) i G2 (kształt historyjki
  i kryteriów akceptacji): reguły, zmiany plik po pliku w pdi, tf, ci_for_sdlc i ShipScope, kroki, decyzje DG1–DG7.
- [`docs/plan-automatyzacja-i-konsola.md`](docs/plan-automatyzacja-i-konsola.md) — gdzie jeszcze automatyzować
  (poziomy autonomii 0–3 zdobywane na danych, kroki A0–A8) i konsola pdi: oś zdarzeń, skrzynka decyzji, rozmowa z Claude.
- [`docs/kontekst-rozmowy.md`](docs/kontekst-rozmowy.md) — kontekst i przekazanie dla kolejnej sesji.
- [`docs/13-rola-pdi-w-sdlc.md`](docs/13-rola-pdi-w-sdlc.md) — **rola pdi w procesie**: co posiada, co wywołuje, na których etapach pojawia się człowiek w pdi; rozbieżności między wersjami mapy i planem (R1: gdzie żyje rejestr decyzji). Źródło: [mapa procesu, wersje 1 i 2](docs/zrodla/2026-10-23-mapa-sdlc.md).
- [`docs/12-zmiana-kierunku-sdlc.md`](docs/12-zmiana-kierunku-sdlc.md) — **jak wcześniejsza praca koncepcyjna (dokumenty 01–11, testy v1 i v2) przechodzi do nowego kierunku**: co wchodzi do kontraktu i modułów pdi, co jest wstrzymane, propozycje do D2 i F0.

## Wcześniejsza praca koncepcyjna (2026-10-19 – 2026-10-22)

Powstała, gdy pdi było projektowane jako samodzielne narzędzie dla PM-ów. Wnioski z niej zasilają nowy kierunek
(szczegóły w [dokumencie 12](docs/12-zmiana-kierunku-sdlc.md)); dokumenty zostają jako uzasadnienie i materiał wejściowy.

| Obszar | Dokumenty | Status w nowym kierunku |
|---|---|---|
| Model decyzji (statusy epistemiczne, założenia nośne, warunki unieważnienia) | [02](docs/02-living-decision-model.md), [`model/living-decision-model.schema.json`](model/living-decision-model.schema.json) | **wejście do kontraktu** (schemat decyzji w `contract/`, F0) |
| Wzorce ryzyka R1–R12 | [03](docs/03-decision-risk-radar.md) | wejście do wzbogacenia i przeglądu intencji (B1) |
| Zamykanie luk w wiedzy | [04](docs/04-knowledge-gap-closure.md) | wejście do pytań doprecyzowujących (intake) |
| Poziomy uwagi i reguły antyszumowe | [05](docs/05-attention-intelligence.md) | wejście do skrzynki bramek i powiadomień |
| Strażnik podstaw decyzji (decyzja 11) | [11](docs/11-propozycja-wartosci.md) | wejście do rejestru decyzji i oceny skutku |
| Testy v1 i v2 (metoda ewaluacji, wyniki) | [eval/status-zamowienia](eval/status-zamowienia/README.md), [eval/v2-pamiec-decyzji](eval/v2-pamiec-decyzji/README.md) | wejście do evali flow (F6) |
| Wizja, plan projektu, weryfikacja planu, MVP | [01](docs/01-wizja.md), [06](docs/06-mvp-i-pilotaz.md), [08](docs/08-plan-projektu.md), [09](docs/09-weryfikacja-planu.md) | **zastąpione** planem jednego flow |
| Ryzyka, analiza konkurencji | [07](docs/07-ryzyka-i-otwarte-pytania.md), [10](docs/10-analiza-konkurencji.md) | tło; pytanie „produkt czy narzędzie wewnętrzne” rozstrzygnięte na rzecz narzędzia w ramach flow |
| Pozyskiwanie design partnerów (zewnętrzni PM-owie) | [outreach/](outreach/profil-design-partnera.md) | **wstrzymane** |
| Przykład roboczy | [`examples/status-zamowienia.yaml`](examples/status-zamowienia.yaml) | materiał testowy |
