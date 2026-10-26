# Przebieg na sobie: sprintdeck S5 przez cały ekosystem

Data: 2026-10-26 · Status: **scenariusz do wykonania** · Powiązane: [plan G1/G2](plan-g1-g2.md) §10,
[plan automatyzacji](plan-automatyzacja-i-konsola.md) §8

Cel: przeprowadzić jedną prawdziwą zmianę od zgłoszenia do skutku u użytkowników przez pdi, tf, ci_for_sdlc i
ShipScope. Zmiana ma być mała, ale ma przejść każdą fazę. Wynikiem jest dziennik przebiegu (§5). Dla każdego kroku
zapisujemy, czy zadziałał sam, czy trzeba go było popchnąć ręcznie, czy się zepsuł. Ten dziennik jest wejściem do
następnych kroków planów, zamiast zgadywania.

## 1. Wybrana zmiana

**sprintdeck S5: minimalna analityka produktowa**, czyli zdarzenia do metryk z `docs/PLAN.md` §9.

Dlaczego S5, a nie S2:

- S2 (podsumowanie + eksport), S4 (porównanie rund) i M11 (retencja 90 dni) są już w main sprintdecka.
- S5 jest mała. Ma naturalny podział na cięcia (zdarzenia, zapis, zapytanie metryki), przy którym każde cięcie
  zostawia aplikację działającą.
- S5 daje źródło danych dla kroku „skutek”: metryka aktywacji (% pokoi z ≥ 3 uczestnikami i ≥ 1 zatwierdzonym
  zadaniem) staje się mierzalna. Bez tego ocena skutku w pdi nie ma czego porównać.
- Zdarzenia można schować za flagą, więc przechodzi też krok udostępniania etapami.

## 2. Kto, gdzie, oznaczenia

| Oznaczenie | Kto | Gdzie |
|---|---|---|
| 👤 | człowiek (Ty) | wskazane miejsce |
| 🤖 | agent AI | sesja Claude Code albo workflow GitHub |
| ⚙️ | aplikacja sama | bez udziału człowieka |

Miejsca pracy:

| Skrót | Miejsce |
|---|---|
| **T-pdi** | terminal w `~/pdi` |
| **T-sd** | terminal w `~/sprintdeck` |
| **C-sd** | sesja Claude Code uruchomiona w `~/sprintdeck`, z serwerem MCP `pdi` |
| **SS** | ShipScope w przeglądarce |
| **GH** | GitHub w przeglądarce (repo `dbqm45/sprintdeck`) |
| **CI** | ci_for_sdlc w przeglądarce |

## 3. Przygotowanie (raz)

### P0. Odblokuj GitHub Actions 👤 GH

Settings konta → Billing and plans: ustaw limit wydatków albo metodę płatności. Dziś joby kończą się po 0 krokach.
Bez tego `sdlc-phase.yml` nie ruszy. Wtedy każdą fazę uruchamiasz lokalnie (wariant „lokalnie” w krokach niżej) i
zapisujesz to w dzienniku.

### P1. Zainstaluj tf w sprintdecku 👤 T-sd

```bash
cd ~/sprintdeck
git switch -c chore/tf-install
python3 ~/tools/tf/core/factory/tf.py --install-launcher        # tylko jeśli nie ma polecenia tf
tf install --packs pack-it,pack-docs --language pl --commit-language en --yes --shared
tf add mode-pdi
tf doctor
python3 .claude/skills/pdi-decisions/scripts/phase_run.py workflow install
python3 .claude/skills/pdi-decisions/scripts/metric_watch.py workflow install
git add .claude .github CLAUDE.md && git commit -m "chore: install tf with mode-pdi" && git push -u origin chore/tf-install
```

Oczekiwane: `tf doctor` bez błędów. Powstają `.github/workflows/sdlc-phase.yml` i `metric-watch.yml`. PR zmerguj w GH.

### P2. Sekrety i zmienne w sprintdecku 👤 GH

Settings → Secrets and variables → Actions:

| Typ | Nazwa | Wartość |
|---|---|---|
| secret | `ANTHROPIC_API_KEY` | klucz API |
| secret | `PDI_TF_SIGNING_SECRET` | losowy, ten sam co w P4 |
| secret | `SHIPSCOPE_TOKEN` | token usługi `shps_…` z P6 |
| variable | `PDI_EVENTS_URL` | publiczny adres z P4, bez `/events` |
| variable | `SHIPSCOPE_URL` | adres ShipScope |

### P3. Serwer MCP pdi w Claude Code 👤 T-pdi

```bash
cd ~/pdi && git pull && uv sync
claude mcp add --scope user pdi \
  -e PDI_REGISTRY_PATH="$HOME/pdi-decisions" \
  -e PDI_DECIDED_BY="<Twój podpis>" \
  -e PDI_DISPATCH_REPO="dbqm45/sprintdeck" \
  -e PDI_GITHUB_TOKEN="<token z prawem actions:write do sprintdecka>" \
  -e PDI_SHIPSCOPE_URL="<adres ShipScope>" -e PDI_SHIPSCOPE_TOKEN="<shps_…>" \
  -e PDI_CI_FOR_SDLC_URL="<adres ci_for_sdlc>" \
  -- uv run --directory "$HOME/pdi" pdi-mcp
claude mcp list          # pdi: connected
```

### P4. Odbiornik zdarzeń pdi z publicznym adresem 👤 T-pdi (dwa okna, mają działać przez cały przebieg)

Okno 1:

```bash
cd ~/pdi
export PDI_REGISTRY_PATH="$HOME/pdi-decisions" PDI_DECIDED_BY="<Twój podpis>"
export PDI_TF_SIGNING_SECRET="<…>" PDI_SHIPSCOPE_SIGNING_SECRET="<…>" PDI_CI_FOR_SDLC_SIGNING_SECRET="<…>"
export PDI_DISPATCH_REPO="dbqm45/sprintdeck" PDI_GITHUB_TOKEN="<…>" PDI_PHASE_BUDGET_USD=5
export PDI_FORM_TOKEN="<losowy>"
uv run pdi-receiver                 # 127.0.0.1:8787
```

Okno 2 (dowolny tunel, np. cloudflared):

```bash
cloudflared tunnel --url http://127.0.0.1:8787     # zapisz adres https://….trycloudflare.com
```

Ten adres to `PDI_EVENTS_URL` z P2. Odbiornik przyjmuje `POST /events/tf`, `/events/shipscope` i
`/events/ci_for_sdlc`.

Uwaga: adres darmowego tunelu zmienia się po restarcie. Wtedy popraw P2, P5 i P6 i zapisz to w dzienniku.

### P5. ci_for_sdlc 👤 CI

- Podłącz projekt Jira sprintdecka.
- Ustaw podpisywanie zdarzeń do pdi sekretem `PDI_CI_FOR_SDLC_SIGNING_SECRET`, adres `<PDI_EVENTS_URL>/events/ci_for_sdlc`.
- Webhook z pdi do ci_for_sdlc: `POST <adres ci_for_sdlc>/api/webhooks/pdi` (pdi wysyła tam `gate.decided`).

### P6. ShipScope 👤 SS

1. Śledź repo `dbqm45/sprintdeck`. Środowiska powstają z GitHub Deployments, które tworzy Vercel. Sprawdź w GH →
   Environments, czy Vercel je zgłasza. Jeśli nie, zapisz to w dzienniku jako lukę.
2. Settings → General → subskrypcja `release.stage_changed` i `feature.released` na adres
   `<PDI_EVENTS_URL>/events/shipscope`.
3. Settings → tokeny usługi → utwórz token dla pdi i tf (pokazywany raz). Wpisz go w P2 i P3.
4. Plik flag: wskażesz go w kroku 9, po tym jak powstanie w kodzie.

### P7. Sprawdzenie gotowości 👤 C-sd

W `~/sprintdeck` uruchom `claude` i napisz:

> Pokaż `autonomy_report` i `list_inbox` z pdi.

Oczekiwane: pusta skrzynka, wszystkie typy decyzji na poziomie 0 (człowiek decyduje o wszystkim).

## 4. Przebieg

Każdy krok ma: kto i gdzie → polecenie → oczekiwany wynik → co zapisać w dzienniku (§5).

### 1. Zgłoszenie problemu 👤 przeglądarka albo C-sd

Formularz: `http://127.0.0.1:8787/problems/new?token=<PDI_FORM_TOKEN>`. Wypełnij:

- **Kto:** prowadzący pokoju estymacji.
- **Czego nie może:** nie wie, czy sesje w sprintdecku kończą się decyzją, ani czy wraca.
- **Skutek:** nie da się ocenić metryk z §9 ani pilotażu.
- **Kanał:** dogfooding.

Albo w C-sd:

> Zapisz w pdi problem (`record_problem`, kind=problem): tytuł „Brak danych o użyciu sprintdecka”, who „prowadzący
> pokoju”, cannot „nie widzi, czy sesje kończą się decyzją i czy wraca”, impact „metryk z PLAN.md §9 nie da się
> policzyć”, reporter „<Ty>”, channel „dogfooding”.

Oczekiwane: `PRB-1` w `list_problems`. `find_similar_problems` zwraca pusto.

### 2. Triaż 🤖 + 👤 C-sd

> Zaproponuj triaż PRB-1 (`triage_problem`, drafted_by=ai) z uzasadnieniem. Nie zapisuj, pokaż szkic.

Przeczytaj szkic, popraw, potem:

> Zatwierdź: outcome=accepted, statement „Robimy S5: minimalna analityka produktowa”, why „<Twoje>”, source
> claude-cli, drafted_by=ai, z success_metric: aktywacja — % pokoi z ≥ 3 uczestnikami i ≥ 1 zatwierdzonym
> zadaniem, review_by za 30 dni.

Oczekiwane ⚙️: decyzja `DEC-n` w rejestrze, zmiana `CHG-1` ze źródłem PRB-1. pdi wysyła `workflow_dispatch` do
`sdlc-phase.yml` z fazą `intent`. Sprawdź w GH → Actions.

Zapisz w dzienniku, czy szkic AI zatwierdziłeś bez zmian (to wejście do licznika A3).

### 3. Intencja (Maja, B1) ⚙️ GH Actions albo lokalnie T-sd

Automatycznie: workflow `sdlc-phase` dla `CHG-1/intent` otwiera PR z `changes/CHG-1/intent.md`.

Lokalnie, gdy Actions stoi:

```bash
cd ~/sprintdeck
export PDI_EVENTS_URL="<…>" PDI_TF_SIGNING_SECRET="<…>"
python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-1 --source PRB-1
python3 .claude/skills/pdi-decisions/scripts/phase_run.py run --change CHG-1 --phase intent --dry-run   # podgląd
python3 .claude/skills/pdi-decisions/scripts/phase_run.py run --change CHG-1 --phase intent --budget-usd 2
python3 .claude/skills/pdi-decisions/scripts/phase_run.py gate request --change CHG-1 --phase intent \
  --summary "Intencja S5" --url "<link do PR>"
```

Oczekiwane: w skrzynce pdi bramka `intent` dla CHG-1.

### 4. Bramka intencji 👤 C-sd albo konsola pdi

> `list_inbox` → pokaż bramkę CHG-1/intent i szkic decyzji.

Po przeczytaniu PR:

> `decide_inbox_item` <id>: outcome approved, statement „Intencja CHG-1 zatwierdzona”, why „…”, source claude-cli,
> drafted_by ai.

Oczekiwane ⚙️: pdi zapisuje decyzję i zleca fazę `requirements`. Jeśli odrzucisz, zleca `--rework` tej samej fazy.

### 5. Wymagania (Ewa, B2) ⚙️ + 👤

Tak samo jak w kroku 3, z `--phase requirements`. Wynik: historyjki w kształcie STORY i AC Given/When/Then w
`changes/CHG-1/requirements.md`.

Sprawdzenie kształtu 👤 T-sd:

```bash
python3 .claude/skills/pdi-decisions/scripts/decision_record.py check
python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py changes/CHG-1/requirements.md --strict
```

Luka F2: ci_for_sdlc nie czyta jeszcze `changes/`. Ma te same reguły (test parzystości), ale widzi tylko Jirę.
Na czas przebiegu `requirements_lint` go zastępuje. Opcjonalnie przepisz historyjki do Jiry z etykietą
`change:CHG-1`, a ci_for_sdlc pokaże gotowość (krok 7). Zapisz w dzienniku, ile to kosztowało czasu.

Bramka 👤 jak w kroku 4.

### 6. Architektura i plan wydania (Tomasz, B3) ⚙️ + 👤

`--phase architecture`. Wynik: `changes/CHG-1/plan.md` i `release.yaml` z liniami wydania (R1 = MVP) i cięciami.

Oczekiwane cięcia, każde zostawia aplikację działającą:

1. Tabela `events` w Supabase z polityką RLS i 90-dniową retencją, plus funkcja `track()` za flagą `analytics_events`.
2. Zdarzenia: `room_created`, `participant_joined`, `round_started`, `task_approved`.
3. Zapytanie SQL metryki aktywacji (widok albo `scripts/metrics.sql`).

Sprawdź, czy flaga jest w `release.yaml` i w pliku flag. Bramka 👤 jak w kroku 4.

### 7. Gotowość (ci_for_sdlc) ⚙️ CI, częściowo

Jeśli historyjki są w Jirze z `change:CHG-1`, ci_for_sdlc wysyła `readiness.changed`. pdi pokazuje gotowość w
`get_change CHG-1`. Jeśli nie, zapisz „pominięte, luka F2”.

### 8. Dostarczenie (Talos) ⚙️ + 👤 GH

`--phase delivery` (lokalnie `phase_run.py run --change CHG-1 --phase delivery --budget-usd 5`). Wynik: jeden PR na
cięcie, każdy z odnośnikiem `CHG-1` i zielonymi testami (`npm run lint`, `npm test`, `npm run test:e2e`).

Ty 👤 GH: przegląd i merge PR-ów po kolei. Migracja Supabase: `supabase db push` z T-sd po merge'u cięcia 1.

### 9. Wdrożenie ukryte ⚙️ Vercel → ShipScope

Po merge'u ⚙️ Vercel wdraża, a GitHub Deployment trafia do ShipScope. Flaga `analytics_events` jest wyłączona w
`config/flags.production.json`.

Ty 👤 SS: w ustawieniach repo wskaż plik flag. ShipScope proponuje `config/flags.{env}.json`.

Oczekiwane: zakładka Release plan pokazuje CHG-1 jako wdrożony, flaga jest na etapie „off”.

### 10. Udostępnianie etapami 👤 + ⚙️

Zmieniaj `config/flags.production.json` PR-ami: najpierw własne pokoje (allowlista), potem 100%. Po każdej zmianie:

- ⚙️ ShipScope wysyła `release.stage_changed`, potem `feature.released` (linia R1 u użytkowników).
- ⚙️ pdi zapisuje to w śladzie zmiany. Sprawdź `get_trace CHG-1`.
- 👤 Bramka udostępnienia w skrzynce pdi, jeśli plan ją przewiduje (krok 4).

### 11. Skutek 👤 + ⚙️ (po 30 dniach)

- ⚙️ pdi: `open_due_impact_reviews` otwiera przegląd skutku decyzji z kroku 2 w skrzynce.
- 👤 T-sd: policz aktywację zapytaniem z cięcia 3 (Supabase SQL editor albo `psql`) i wpisz wartość w odpowiedź:

  > `decide_inbox_item` <id przeglądu>: outcome …, evidence: wynik zapytania aktywacji z datą.

- ⚙️ tf, codziennie: `metric-watch.yml` liczy pasma kontrolne na metrykach PROD z ShipScope (czas realizacji itp.).
  Wynik ręcznie: `python3 .claude/skills/pdi-decisions/scripts/metric_watch.py check` w T-sd. Wybicie poza 3σ
  wraca do pdi jako `metric.breached`, czyli nowy problem.

Na koniec 👤 C-sd:

> `get_trace CHG-1` i `autonomy_report` — podsumuj przebieg.

## 5. Dziennik przebiegu

Wypełniaj na bieżąco. Wynik: ✅ samo, ✋ popchnięte ręcznie (opisz jak), ❌ zepsute (opisz, link do błędu).

| Krok | Data | Wynik | Czas | Szkic AI bez zmian? | Uwagi / luka |
|---|---|---|---|---|---|
| P0–P7 przygotowanie | | | | — | |
| 1 zgłoszenie | | | | — | |
| 2 triaż | | | | | |
| 3 intencja | | | | — | Actions czy lokalnie? |
| 4 bramka intencji | | | | | |
| 5 wymagania + bramka | | | | | F2 |
| 6 architektura + bramka | | | | | |
| 7 gotowość | | | | — | F2 |
| 8 dostarczenie | | | | — | ile PR-ów, ile poprawek |
| 9 wdrożenie ukryte | | | | — | Vercel → Deployments? |
| 10 udostępnianie | | | | | |
| 11 skutek | | | | | |

Po przebiegu: luki z kolumny „Uwagi” trafiają jako problemy do pdi (`record_problem`, channel „dogfooding”), a
stan realizacji w [plan-g1-g2.md](plan-g1-g2.md) §10 dostaje odnośnik do tego dziennika.

## 6. Znane luki przed startem

| Luka | Skutek dla przebiegu | Obejście |
|---|---|---|
| GitHub Actions zablokowane przez billing | fazy nie ruszają same | P0 albo `phase_run.py run` lokalnie |
| F2: ci_for_sdlc nie czyta `changes/` | brak gotowości z repo | `requirements_lint.py` albo ręcznie do Jiry |
| sprintdeck nie ma flag | brak udostępniania etapami | plik `config/flags.{env}.json` w cięciu 1 |
| odbiornik pdi tylko na 127.0.0.1 | GitHub i ShipScope go nie widzą | tunel (P4) |
| Vercel może nie zgłaszać GitHub Deployments | ShipScope nie widzi wdrożeń | sprawdzić w P6; inaczej luka do zgłoszenia |
| konsola (K-1…K-4) to makieta | decyzje tylko w czacie Claude i formularzu | C-sd z MCP pdi |
