# Przebieg na sobie: sprintdeck S5 przez cały ekosystem

Wersja 2 · 2026-10-30 · Status: **scenariusz do wykonania** · Zastępuje wersję z 2026-10-26 (pdi #31)

Cel: przeprowadzić jedną prawdziwą zmianę od zgłoszenia do oceny skutku przez pdi, tf, ci_for_sdlc i ShipScope.
Wynikiem jest dziennik przebiegu (§7). Przy każdym kroku zapisujesz, czy zadziałał sam, czy trzeba go było popchnąć
ręcznie, czy się zepsuł. Polecenia sprawdziłem w kodzie na stanie main z 2026-10-30:

| Repo | Stan |
|---|---|
| pdi | `c4f233b`, kontrakt 0.9.0 |
| tf | 5.51.1, mode-pdi 0.6.0 |
| ci_for_sdlc | 0.1.34 |
| ShipScope | 0.2.64 |
| sprintdeck | `a9d700f` |

## 0. Co się zmieniło od wersji 1

| Było (26.10) | Jest (30.10) | Skutek dla przebiegu |
|---|---|---|
| ścieżka `changes/CHG-n/` | **`docs/project/changes/CHG-n/`** (tf, ShipScope, ci_for_sdlc) | wszystkie ścieżki niżej poprawione |
| ShipScope: token, subskrypcja i sekret zakładane osobno | **Settings → Integrations → pdi → Connect**: jeden przycisk daje trzy zmienne `PDI_SHIPSCOPE_*` | krok P5 krótszy |
| ShipScope czyta zmiany z repo zawsze | czyta je tylko przy aktywnym połączeniu z pdi (warstwa pdi) | Connect musi być przed pierwszą fazą |
| F2 w ci_for_sdlc: brak | **konektor repo jako CLI**: `npm run analyze -- --repo …`, szablon `change-check.yml`, reguły REL-001…008 | zamiast `requirements_lint` sprawdzasz zmianę bramką ci_for_sdlc |
| — | ci_for_sdlc **nie wysyła** gotowości zmian z repo do pdi (serwer czyta tylko Jirę) | bramkę `approve-for-implementation` wysyłasz z tf ręcznie (krok 8) |
| fazy: intent, requirements, architecture, delivery | doszła **faza `design`** (natalia, `design.md` z tabelą ramek, `design_check.py`, bramka `design-review`) | persona natalia z `pack-ux` w instalacji |
| `triage_problem` z `success_metric` (błąd w wersji 1) | `success_metric` i `review_by` podaje się w **decyzji B1** (o intencji); z niej pdi liczy termin oceny skutku | krok 4 |
| formularz `/problems/new?token=` (błąd w wersji 1) | **`/problems/new?t=<PDI_FORM_TOKEN>`** | krok 1 |
| — | **prognoza** przy `approve-for-implementation` (`forecast_change`, `pdi-forecast`) | krok 8 i 13 |
| — | serwery MCP ShipScope i ci_for_sdlc (K-1), komenda `/decisions-from` (A5) | P7, opcjonalnie |
| — | Insights w ShipScope to ustawienie przestrzeni (domyślnie wyłączone) | P5: włączyć, żeby widzieć lead time |

## 1. Zmiana

**sprintdeck S5: minimalna analityka produktowa**, czyli zdarzenia do metryk z `docs/PLAN.md` §9.

Dlaczego S5:
- Jest mała, a ma naturalne cięcia.
- Daje dane do oceny skutku: aktywacja to % pokoi z ≥ 3 uczestnikami i ≥ 1 zatwierdzonym zadaniem.
- Daje się schować za flagą, więc przechodzi też udostępnianie etapami.

S2, S4 i M11 są już w main sprintdecka. S5 nie ma: brak tabeli zdarzeń w `supabase/migrations/`.

## 2. Kto i gdzie

| Znak | Kto |
|---|---|
| 👤 | Ty |
| 🤖 | agent (persona tf, Claude) |
| ⚙️ | aplikacja sama |

| Skrót | Miejsce |
|---|---|
| **T-pdi** | terminal w `~/pdi` |
| **T-tun** | drugi terminal, tunel (otwarty przez cały przebieg) |
| **T-rcv** | trzeci terminal, `pdi-receiver` (otwarty przez cały przebieg) |
| **T-sd** | terminal w `~/sprintdeck` |
| **T-ci** | terminal w `~/ci_for_sdlc` |
| **C-sd** | sesja `claude` uruchomiona w `~/sprintdeck`, z serwerami MCP `pdi` (i opcjonalnie `shipscope`, `ci-sdlc`) |
| **SS** | ShipScope w przeglądarce |
| **GH** | GitHub (`dbqm45/sprintdeck`) |

Wszystkie terminale zaczynasz od `source ~/.pdi.env` (P2).

## 3. Co zainstalować i jakie konta założyć

### Programy na komputerze

| Program | Wersja | Do czego | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|---|
| git | dowolna | klony, gałęzie faz | `xcode-select --install` | `sudo apt install git` |
| GitHub CLI `gh` | ≥ 2.40 | PR-y, sekrety, przebiegi Actions | `brew install gh` | [cli.github.com](https://cli.github.com) → „Linux” |
| Python | ≥ 3.11 (pdi), ≥ 3.9 (skrypty tf) | pdi, tf | `brew install python@3.13` | `sudo apt install python3` |
| uv | aktualna | środowisko i uruchamianie pdi | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js + npm | ≥ 22.12 (wymóg ci_for_sdlc; wystarczy też dla sprintdecka i MCP ShipScope) | ci_for_sdlc, sprintdeck, serwer MCP ShipScope | `brew install node@22` | [nodejs.org](https://nodejs.org) albo `nvm install 22` |
| Claude Code | aktualna | sesja C-sd i persony tf (`claude --print --agent …`) | `curl -fsSL https://claude.ai/install.sh \| bash` | jak na macOS |
| cloudflared | aktualna | tunel do `pdi-receiver` (P4) | `brew install cloudflared` | [pakiet .deb z GitHub cloudflare/cloudflared](https://github.com/cloudflare/cloudflared/releases) |
| Docker (Desktop albo Engine) | aktualna | lokalna baza Supabase (`npm run db:start`) | Docker Desktop | `sudo apt install docker.io` |
| Supabase CLI | aktualna | lokalna baza, testy SQL, `supabase db push` | `brew install supabase/tap/supabase` | [pakiet z GitHub supabase/cli](https://github.com/supabase/cli/releases) |
| openssl | systemowy | generowanie sekretów (P2) | jest w systemie | jest w systemie |
| przeglądarki Playwright | jak w `package.json` | testy e2e sprintdecka | `cd ~/sprintdeck && npx playwright install` | `npx playwright install --with-deps` |

Logowania po instalacji:

```bash
gh auth login               # GitHub.com, HTTPS, w przeglądarce
claude                      # pierwsze uruchomienie: logowanie do Claude, potem /exit
supabase login              # token z supabase.com → Account → Access Tokens
```

Sprawdzenie:

```bash
git --version && gh --version && python3 --version && uv --version && node --version && claude --version \
  && cloudflared --version && docker --version && supabase --version
```

Nie instalujesz osobno: tf (klonujesz repo i dodajesz polecenie `tf` w P1), ci_for_sdlc i pdi (klony z
`npm install` / `uv sync`). ShipScope działa jako usługa, a z jego repo potrzebny jest tylko plik serwera MCP (P7).

### Konta i usługi

| Konto | Do czego | Uwagi |
|---|---|---|
| GitHub (`dbqm45`) | repo, PR-y, Actions | Actions z ustawionymi płatnościami (P0); fine-grained token dla pdi (P2) |
| Claude (subskrypcja albo konto API) | Claude Code lokalnie; `ANTHROPIC_API_KEY` dla Actions | klucz z console.anthropic.com, tylko gdy fazy idą w Actions |
| Vercel | wdrożenia sprintdecka (Production, Preview) | integracja z GitHubem tworzy GitHub Deployments, które czyta ShipScope |
| Supabase | baza sprintdecka i SQL editor do metryki | `ref` projektu do `supabase link` |
| ShipScope | przestrzeń robocza, admin | z GitHub App zainstalowaną na `dbqm45/sprintdeck` |
| Cloudflare | niepotrzebne | darmowy szybki tunel `trycloudflare.com` działa bez konta; konto daje stały adres |

Jira, Confluence i Figma w tym przebiegu nie są potrzebne. Zmiana żyje w repo, a design nie ma ekranów.

## 4. Przygotowanie (raz)

### P0. GitHub Actions 👤 T-sd

```bash
gh run list -R dbqm45/sprintdeck -L 3
```

Jeśli joby kończą się po 0 krokach, odblokuj płatności: GitHub → Settings → Billing and plans. Do tego czasu
każdą fazę uruchamiasz lokalnie funkcją `faza` (P9). Zapisz w dzienniku, który wariant szedł.

### P1. Klony 👤 dowolny terminal

```bash
cd ~
for r in pdi sprintdeck ci_for_sdlc evdt-service-shipscope; do
  [ -d "$r" ] || git clone "https://github.com/dbqm45/$r.git"
  git -C "$r" switch main && git -C "$r" pull --ff-only
done
[ -d ~/tools/tf ] || git clone https://github.com/dbqm45/tf.git ~/tools/tf
python3 ~/tools/tf/core/factory/tf.py --install-launcher        # polecenie tf w ~/.local/bin
cd ~/pdi && uv sync
cd ~/ci_for_sdlc && npm install
```

### P2. Plik ze zmiennymi `~/.pdi.env` 👤 dowolny terminal

Sekrety wspólne dla pdi, tf i ci_for_sdlc wygeneruj raz. Plik trzymaj tylko u siebie, nigdy w repo.

```bash
umask 077
cat > ~/.pdi.env <<EOF
export PDI_REGISTRY_PATH="\$HOME/pdi-decisions"
export PDI_DECIDED_BY="<Twój podpis>"
export PDI_TF_SIGNING_SECRET="$(openssl rand -hex 32)"
export PDI_FORM_TOKEN="$(openssl rand -hex 16)"
export PDI_DISPATCH_REPO="dbqm45/sprintdeck"
export PDI_GITHUB_TOKEN="<fine-grained token: repo dbqm45/sprintdeck, Actions: read and write>"
export PDI_PHASE_BUDGET_USD=5
export PDI_EVENTS_URL=""            # uzupełnisz w P4
export PDI_SHIPSCOPE_URL=""         # uzupełnisz w P5
export PDI_SHIPSCOPE_TOKEN=""       # uzupełnisz w P5
export PDI_SHIPSCOPE_SIGNING_SECRET=""   # uzupełnisz w P5
EOF
source ~/.pdi.env
```

`PDI_CI_FOR_SDLC_*` nie ustawiasz: w tym przebiegu ci_for_sdlc działa jako CLI na repo, bez serwera i bez Jiry.

### P3. Rejestr decyzji 👤 T-pdi

```bash
[ -d "$PDI_REGISTRY_PATH" ] || git init "$PDI_REGISTRY_PATH"
```

Jeśli masz prywatne repo rejestru, zamiast `git init` sklonuj je do `~/pdi-decisions`.

### P4. Tunel 👤 T-tun

```bash
cloudflared tunnel --url http://127.0.0.1:8787
```

Skopiuj adres `https://….trycloudflare.com` i wpisz go w `~/.pdi.env` jako `PDI_EVENTS_URL`, bez `/events` na
końcu. Darmowy tunel dostaje nowy adres po każdym restarcie. Wtedy popraw P4, P5 (Disconnect i Connect) i P8
(`gh variable set`), a w dzienniku zapisz „✋ tunel”.

### P5. ShipScope 👤 SS (admin przestrzeni)

1. **Settings → GitHub → Track repository** → `dbqm45/sprintdeck`.
2. Ołówek przy repo → **environments**. Vercel zgłasza wdrożenia jako `Production` i `Preview`. `Production` mapuje
   się samo na `prod`, a `Preview` bez mapy jest pomijane, więc ustaw `Preview → test`. Jeśli lista nazw jest
   pusta, Vercel nie tworzy GitHub Deployments: sprawdź Vercel → Project → Settings → Git i zapisz to jako lukę.
3. **Settings → Integrations → pdi → Connect**, adres: wartość `PDI_EVENTS_URL`. ShipScope pokaże raz trzy
   zmienne: `PDI_SHIPSCOPE_URL`, `PDI_SHIPSCOPE_TOKEN`, `PDI_SHIPSCOPE_SIGNING_SECRET`. Wpisz je do `~/.pdi.env`.
4. **Settings → General → Insights**: włącz.
5. **Settings → General → Service tokens**: utwórz drugi token, „tf metric-watch”. Przyda się w P8.

Plik flag wskażesz w kroku 11, kiedy powstanie w kodzie.

### P6. Odbiornik pdi 👤 T-rcv

```bash
source ~/.pdi.env && cd ~/pdi && uv run pdi-receiver
```

Oczekiwane w logu: `pdi-receiver: ShipScope: workspace <nazwa>, połączenie z pdi: …`. Potem w SS (Integrations →
pdi) kliknij **Test**. Stan ma przejść na `connected`.

### P7. Serwery MCP w Claude Code 👤 T-pdi

```bash
source ~/.pdi.env
claude mcp remove --scope user pdi 2>/dev/null
claude mcp add --scope user pdi \
  -e PDI_REGISTRY_PATH="$PDI_REGISTRY_PATH" -e PDI_DECIDED_BY="$PDI_DECIDED_BY" \
  -e PDI_DISPATCH_REPO="$PDI_DISPATCH_REPO" -e PDI_GITHUB_TOKEN="$PDI_GITHUB_TOKEN" \
  -e PDI_PHASE_BUDGET_USD="$PDI_PHASE_BUDGET_USD" \
  -e PDI_SHIPSCOPE_URL="$PDI_SHIPSCOPE_URL" -e PDI_SHIPSCOPE_TOKEN="$PDI_SHIPSCOPE_TOKEN" \
  -- uv run --directory "$HOME/pdi" pdi-mcp
# opcjonalnie (K-1): stan wydań ShipScope w tej samej rozmowie, tylko do odczytu
claude mcp add --scope user shipscope -e SHIPSCOPE_URL="$PDI_SHIPSCOPE_URL" -e SHIPSCOPE_TOKEN="$PDI_SHIPSCOPE_TOKEN" \
  -- node "$HOME/evdt-service-shipscope/adapters/mcp/shipscope-mcp.js"
mkdir -p ~/.claude/commands
cp ~/pdi/integrations/claude-code/{record-decision,decisions-from}.md ~/.claude/commands/
claude mcp list
```

Oczekiwane: `pdi: … Connected` (i `shipscope`).

### P8. tf w sprintdecku 👤 T-sd

```bash
source ~/.pdi.env && cd ~/sprintdeck && git switch main && git pull --ff-only
git switch -c chore/tf-install
tf install --packs pack-it,pack-docs,pack-ux --language pl --commit-language en --yes --shared
tf add mode-pdi mode-talos
tf doctor
python3 .claude/skills/pdi-decisions/scripts/phase_run.py workflow install
python3 .claude/skills/pdi-decisions/scripts/metric_watch.py workflow install
cp ~/ci_for_sdlc/docs/templates/change-check.yml .github/workflows/change-check.yml
git add -A && git commit -m "chore: install tf with mode-pdi, phase and change-check workflows"
git push -u origin chore/tf-install && gh pr create --fill
```

`pack-ux` daje personę natalia (faza `design`), a `mode-talos` daje personę talos (faza `delivery`). W
`change-check.yml` zmień `ref: main` na tag wydania ci_for_sdlc, np. `ref: v0.1.34`.

Sekrety i zmienne repozytorium:

```bash
gh secret set ANTHROPIC_API_KEY -R dbqm45/sprintdeck                 # wkleisz klucz
gh secret set PDI_TF_SIGNING_SECRET -R dbqm45/sprintdeck --body "$PDI_TF_SIGNING_SECRET"
gh secret set SHIPSCOPE_TOKEN -R dbqm45/sprintdeck                   # token „tf metric-watch” z P5
gh variable set PDI_EVENTS_URL -R dbqm45/sprintdeck --body "$PDI_EVENTS_URL"
gh variable set SHIPSCOPE_URL -R dbqm45/sprintdeck --body "$PDI_SHIPSCOPE_URL"
```

Potem przejrzyj PR w GH i go zmerguj. Oczekiwane: `tf doctor` bez błędów, w repo są `.github/workflows/sdlc-phase.yml`,
`metric-watch.yml` i `change-check.yml`.

### P9. Funkcja `faza`: uruchamianie fazy lokalnie, gdy Actions stoi 👤 T-sd

Funkcja robi to samo co `sdlc-phase.yml`, krok po kroku. Wklej ją do terminala T-sd albo do `~/.pdi.env`.
Persony uruchamia lokalny `claude`, na Twoim zalogowaniu.

```bash
faza() {   # faza CHG-1 intent PRB-1 | faza CHG-1 requirements | … | faza CHG-1 delivery
  local chg=$1 ph=$2 src=${3:-} S=.claude/skills/pdi-decisions/scripts url rep
  cd ~/sprintdeck && git switch main && git pull --ff-only && git switch -C "pdi/$chg-$ph" || return 1
  if [ "$ph" = intent ] && [ -n "$src" ] && [ ! -d "docs/project/changes/$chg" ]; then
    export PDI_PROBLEM="$(uv run --directory ~/pdi python -c 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1])), default=str))' "$PDI_REGISTRY_PATH/problems/$src.yaml")"
    rep=$(python3 -c 'import json,os; print(str(json.loads(os.environ["PDI_PROBLEM"]).get("reported_at",""))[:10])')
    python3 $S/decision_record.py change new "$chg" --source "$src" --author pdi ${rep:+--source-reported-at "$rep"} || return 1
  fi
  python3 $S/phase_run.py prompt --change "$chg" --phase "$ph" >/dev/null || return 1
  PDI_SOURCE="$src" python3 $S/phase_run.py run --change "$chg" --phase "$ph" --budget-usd "${PDI_PHASE_BUDGET_USD:-5}" || return 1
  [ "$ph" = delivery ] && return 0
  git add -A && { git diff --cached --quiet || git commit -m "docs($chg): faza $ph (pdi)" -m "Change: $chg"; }
  git push -u origin "pdi/$chg-$ph"
  url=$(gh pr view --json url -q .url 2>/dev/null || gh pr create --fill)
  python3 $S/phase_run.py gate request --change "$chg" --phase "$ph" --url "$url"
}
```

Po decyzji na bramce w pdi workflow zapisuje ją w `decisions.md` zmiany. Lokalnie robisz to sam, zaraz po
`decide_inbox_item`:

```bash
python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision gate CHG-1 --gate B1 --outcome approved --id DEC-<n>
```

### P10. Sprawdzenie gotowości 👤 C-sd

```bash
source ~/.pdi.env && cd ~/sprintdeck && claude
```

> Pokaż `get_shipscope_connection`, `autonomy_report` i `list_inbox` z pdi.

Oczekiwane:
- ShipScope `connected`,
- wszystkie typy decyzji na poziomie 0,
- pusta skrzynka.

## 5. Przebieg

Każdy krok podaje: kto i gdzie, polecenie, oczekiwany wynik i co zapisać w dzienniku.

Zasada przy każdej bramce: **najpierw zmerguj PR fazy, potem zatwierdź bramkę.** Następna faza startuje od `main`.

### 1. Zgłoszenie 👤 przeglądarka

Otwórz `http://127.0.0.1:8787/problems/new?t=<PDI_FORM_TOKEN>` (wartość z `~/.pdi.env`). Wypełnij:

| Pole | Wartość |
|---|---|
| Rodzaj | problem |
| Kto | prowadzący pokoju estymacji |
| Czego nie może | sprawdzić, czy sesje w sprintdecku kończą się decyzją i czy prowadzący wraca |
| Skutek | metryk z `docs/PLAN.md` §9 (aktywacja, czas do decyzji, retencja) nie da się policzyć, więc pilotażu nie da się ocenić |
| Kanał | dogfooding |

Zamiast formularza możesz w C-sd napisać:

> Zapisz w pdi problem przez `record_problem`: kind problem, tytuł „Brak danych o użyciu sprintdecka”, who
> „prowadzący pokoju”, cannot „sprawdzić, czy sesje kończą się decyzją i czy prowadzący wraca”, impact „metryk z
> PLAN.md §9 nie da się policzyć”, reporter „<Ty>”, channel „dogfooding”, ready true.

Oczekiwane: `PRB-1`. Strona formularza pokazuje podobne zgłoszenia (pusto).

### 2. Doprecyzowanie, opcjonalnie 🤖 + 👤 C-sd

> `clarify_problem PRB-1`: zaproponuj 3–5 pytań.

Na pytania odpowiadasz sam. Potem:

> `update_problem PRB-1` z odpowiedziami, ready true.

### 3. Triaż 🤖 + 👤 C-sd

> Przygotuj szkic triażu PRB-1 (accepted, drafted_by ai) z uzasadnieniem i dowodami. Nie zapisuj, pokaż szkic.

Popraw szkic, potem:

> Zapisz `triage_problem PRB-1`: outcome accepted, statement „Robimy S5: minimalna analityka produktowa za flagą
> analytics_events”, why „<Twoje>”, source claude-cli, drafted_by ai.

Oczekiwane ⚙️:
- decyzja `DEC-n` (kind triage),
- zmiana `CHG-1` ze źródłem PRB-1,
- pdi uruchamia `sdlc-phase.yml` z fazą `intent`. Widać to w GH → Actions, run „pdi: CHG-1 intent”.

Jeśli Actions stoi, `get_change CHG-1` pokaże błąd wysyłki. Uruchom wtedy fazę lokalnie (T-sd):

```bash
faza CHG-1 intent PRB-1
```

Zapisz w dzienniku, czy szkic AI zatwierdziłeś bez zmian; to wejście do licznika autonomii.

### 4. Intencja i bramka B1 🤖 maja → 👤 GH + C-sd

Wynik: PR `pdi/CHG-1-intent` z `docs/project/changes/CHG-1/intent.md`, a w skrzynce pdi bramka B1.

1. 👤 GH: przeczytaj PR i go zmerguj.
2. 👤 C-sd:

   > `list_inbox`, potem `decide_inbox_item` dla B1 CHG-1: outcome approved, statement „Intencja CHG-1
   > zatwierdzona”, why „…”, source claude-cli, drafted_by ai, success_metric {metric: „aktywacja: % pokoi z ≥ 3
   > uczestnikami i ≥ 1 zatwierdzonym zadaniem”, target: „>= <PRÓG>%”, horizon: „30 dni”}.

Oczekiwane ⚙️: pdi zleca fazę `requirements`. Metryka i horyzont z tej decyzji wyznaczą termin oceny skutku po
wydaniu R1. Lokalnie: najpierw `decision gate` (P9), potem `faza CHG-1 requirements`.

### 5. Wymagania i bramka B2 🤖 ewa → 👤

Wynik: `requirements.md` z kryteriami Given/When/Then.

👤 T-sd, kontrola kształtu przed bramką:

```bash
python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py docs/project/changes/CHG-1/requirements.md --strict
```

Merge i bramka jak w kroku 4 (B2, bez `success_metric`). Lokalnie: `faza CHG-1 architecture`.

### 6. Architektura, plan wydania i bramka B3 🤖 tomasz → 👤

Wynik: `plan.md` z tabelą cięć i `release.yaml` (linie R1…, flaga z etapami). Oczekiwane cięcia; każde zostawia
aplikację działającą:

| Cięcie | Zakres | Wydanie | Flaga |
|---|---|---|---|
| TSK-1 | migracja `events` (RLS: wstawia tylko serwer, brak odczytu dla `anon`), retencja jak pokoje; `track()` w kodzie, wyłączone flagą | R1 | `analytics_events` |
| TSK-2 | zdarzenia `room_created`, `participant_joined`, `round_started`, `task_approved` | R1 | `analytics_events` |
| TSK-3 | `scripts/metrics.sql`: aktywacja, czas do decyzji, retencja 14 dni | R1 | — |

Flaga w `release.yaml`: `owner`, `remove_by` i etapy `rollout` z `stage`, `min_days` i `exit`. Bez nich REL-007
zgłosi braki.

👤 T-ci, bramka ci_for_sdlc na zmianie z repo:

```bash
cd ~/ci_for_sdlc
npm run analyze -- --repo ~/sprintdeck --repo-url https://github.com/dbqm45/sprintdeck --fail-on critical
```

Kod 0 to przejście, 1 to element niegotowy albo zły plik (powód jest w raporcie), 2 to brak
`docs/project/changes`. Gdy Actions działa, ten sam check (`Definition check / check`) wejdzie sam na PR fazy.

Merge i bramka B3 jak w kroku 4. ⚙️ pdi zleca fazę `design`. Lokalnie: `faza CHG-1 design`.

### 7. Design i bramka design-review 🤖 natalia → 👤

S5 nie dodaje ekranów. Oczekiwane: `design.md`, w którym każdy wiersz tabeli ramek ma „nie dotyczy” z powodem
(„zdarzenia bez UI”). Wiersz „brak” to pytanie do projektanta.

👤 T-sd:

```bash
python3 .claude/skills/pdi-decisions/scripts/design_check.py check CHG-1
```

Problemy trafiają też jako pytania do prośby o bramkę. Merge i bramka `design-review` jak w kroku 4.

⚙️ Po tej bramce pdi **nie** uruchamia niczego. Czeka na `approve-for-implementation`.

### 8. Zatwierdzenie do budowy 👤 T-sd + C-sd

W trybie Jira tę prośbę wysyła ci_for_sdlc (`readiness.changed: ready`). Dla zmian z repo serwer ci_for_sdlc
jej nie wysyła, więc po zielonym `npm run analyze` (krok 6, powtórz na aktualnym `main`) wyślij ją z tf:

```bash
cd ~/sprintdeck && git switch main && git pull --ff-only
python3 .claude/skills/pdi-decisions/scripts/phase_run.py gate request --change CHG-1 --gate approve-for-implementation \
  --summary "ci_for_sdlc analyze --repo: kod 0" --url https://github.com/dbqm45/sprintdeck/tree/main/docs/project/changes/CHG-1
```

👤 C-sd:

> `decide_inbox_item` dla approve-for-implementation CHG-1: approved, … Potem pokaż `get_change CHG-1`, pole forecast.

Oczekiwane ⚙️:
- **prognoza**: cięcia × mediana dni z ShipScope. Przy pustej historii spodziewaj się `doubts` („mniej niż 5
  zmian”) albo `status: failed`; decyzji to nie blokuje,
- start fazy `delivery`. Lokalnie: `faza CHG-1 delivery`.

Zapisz w dzienniku prognozę. Porównasz ją z wynikiem w kroku 13.

### 9. Dostarczenie 🤖 talos → 👤 GH + T-sd

Talos robi cięcia po kolei. Commity mają dopiski `Change: TSK-n` i `Flag: analytics_events`. Jeśli lokalny
przebieg nie otworzył PR-ów, otwórz je sam: `git push -u origin HEAD && gh pr create --fill`.

👤 T-sd, przed merge'em każdego PR:

```bash
npm ci && npm run lint && npm run typecheck && npm test
npm run db:start && npm run db:test       # cięcie 1: testy RLS i migracji
npm run e2e
```

👤 GH: przegląd i merge PR po PR. Migracja na produkcyjną bazę po merge'u TSK-1:

```bash
supabase link --project-ref <ref projektu> && supabase db push
```

### 10. Bramka B4 (gotowość do wydania), opcjonalnie 👤 T-sd + C-sd

```bash
python3 .claude/skills/pdi-decisions/scripts/phase_run.py gate request --change CHG-1 --gate B4 --summary "TSK-1..3 na main, testy zielone"
```

> `decide_inbox_item` B4 CHG-1 approved.

### 11. Wdrożenie ukryte ⚙️ Vercel → ShipScope; 👤 SS

⚙️ Każdy merge do `main` to wdrożenie `Production`, a każdy PR to `Preview`. ShipScope widzi je w matrycy (Technical
view).

👤 SS, wskazanie pliku flag:
1. Settings → Sources → **Advanced sources** → **Find flags files** dla `dbqm45/sprintdeck`.
2. Wybierz `config/flags.{env}.json` (`test`, `prod`) → **Use this** → **Preview** → **Read from code**.
3. W Preview sprawdź, czy ShipScope czyta stan i `rollout` flagi tak, jak zapisał je talos.

Oczekiwane:
- Release plan: grupa CHG-1, linia R1, cięcia „Deployed (hidden)” na PROD,
- flaga `analytics_events`: etap „off”,
- zakładka Changes (repo): CHG-1 z tytułem z intencji.

### 12. Udostępnianie etapami 👤 GH + SS + C-sd; ⚙️

Etapy zmieniasz PR-ami do `config/flags.prod.json`: najpierw `test` na 100%, potem PROD na 10% (albo allowlista
własnych pokoi), potem PROD na 100%. Przed pierwszym etapem na PROD wyślij opcjonalnie B5 (autoryzacja PROD): to
samo polecenie co w kroku 10, z `--gate B5`.

Po każdym merge'u:
- ⚙️ Vercel wdraża, a ShipScope czyta plik flag przy wdrożonym commicie.
- ⚙️ Najpóźniej po 5 minutach ShipScope wysyła `release.stage_changed`, a pdi zakłada bramkę etapu w skrzynce.
- 👤 C-sd: `list_inbox`, potem `decide_inbox_item` dla etapu.
- ⚙️ Gdy cała linia R1 jest u użytkowników, ShipScope wysyła `feature.released` z `release: R1`. pdi planuje wtedy
  ocenę skutku (termin z decyzji B1) i rozlicza prognozę (`actual`).

👤 C-sd:

> `get_trace CHG-1` — pokaż graf i luki.

### 13. Skutek 👤 + ⚙️ (po 30 dniach od wydania R1)

⚙️ Raz dziennie, a ręcznie w T-pdi:

```bash
source ~/.pdi.env && cd ~/pdi && uv run pdi-impact-review && uv run pdi-forecast
```

Oczekiwane: pozycja `impact-CHG-1-R1` w skrzynce. Szkic będzie `unknown`, bo aktywacji nie ma w metrykach ShipScope
(automat ocenia tylko wdrożenia, nieudane wdrożenia, rollbacki i lead time).

👤 Supabase → SQL editor: uruchom zapytanie aktywacji z `scripts/metrics.sql` i zanotuj wynik z datą.

👤 C-sd:

> `decide_inbox_item impact-CHG-1-R1`: outcome met albo not_met, evidence: wynik zapytania aktywacji z datą i
> treścią zapytania.
> Potem `forecast_report` i `autonomy_report`.

⚙️ Codziennie `metric-watch.yml`, a ręcznie w T-sd:

```bash
SHIPSCOPE_URL="$PDI_SHIPSCOPE_URL" SHIPSCOPE_TOKEN="<token tf metric-watch>" \
  python3 .claude/skills/pdi-decisions/scripts/metric_watch.py check
```

Punkt poza 3σ z `--send` wraca do pdi jako nowy problem w skrzynce. Przy kilku wdrożeniach w historii spodziewaj
się `note` o zbyt krótkim szeregu.

### 14. Zamknięcie przebiegu 👤 C-sd

> Z kolumny „Uwagi” dziennika zapisz każdą lukę jako problem w pdi (`record_problem`, channel dogfooding).

Potem w T-pdi dopisz link do wypełnionego dziennika w `docs/plan-jeden-flow-sdlc.md` §8, w części „Do sprawdzenia na
prawdziwej pracy”.

## 6. Znane luki przed startem

| Luka | Skutek | Obejście w przebiegu |
|---|---|---|
| GitHub Actions bez płatności | fazy, `change-check` i `metric-watch` nie ruszają same | P0; funkcja `faza` i polecenia ręczne |
| serwer ci_for_sdlc nie czyta zmian z repo | brak `readiness.changed` do pdi | `npm run analyze -- --repo` + `gate request --gate approve-for-implementation` (krok 8) |
| odbiornik pdi tylko na 127.0.0.1 | GitHub i ShipScope go nie widzą | tunel (P4); adres zmienia się po restarcie |
| sprintdeck nie ma flag | brak etapów udostępniania | plik `config/flags.{env}.json` w cięciu TSK-1 |
| Vercel i GitHub Deployments | bez nich ShipScope nie widzi wdrożeń | sprawdzić w P5 (lista nazw środowisk) |
| aktywacja spoza metryk ShipScope | ocena skutku szkicuje `unknown` | wynik zapytania SQL jako dowód (krok 13) |
| krótka historia w ShipScope | prognoza z `doubts`, pasma bez wyniku | zapisać i porównać po kilku zmianach |
| konsola pdi to makieta | decyzje tylko w czacie i formularzu | C-sd z MCP pdi |

## 7. Dziennik przebiegu

Wynik: ✅ samo, ✋ popchnięte ręcznie (napisz jak), ❌ zepsute (napisz co, z linkiem).

| Krok | Data | Wynik | Czas | Szkic AI bez zmian? | Koszt fazy | Uwagi / luka |
|---|---|---|---|---|---|---|
| P0–P10 przygotowanie | | | | — | — | Actions? tunel? Vercel Deployments? |
| 1 zgłoszenie | | | | — | — | |
| 2 doprecyzowanie | | | | | — | |
| 3 triaż | | | | | — | dispatch: Actions czy `faza`? |
| 4 intencja + B1 | | | | | | |
| 5 wymagania + B2 | | | | | | lint |
| 6 architektura + B3 | | | | | | `analyze --repo`: kod, REL-007/008 |
| 7 design + design-review | | | | | | |
| 8 approve-for-implementation | | | | | — | prognoza: dni, przedział, doubts |
| 9 dostarczenie | | | | — | | ile PR-ów, ile poprawek |
| 10 B4 | | | | | — | |
| 11 wdrożenie ukryte | | | | — | — | plik flag odczytany? |
| 12 udostępnianie | | | | | — | zdarzenia doszły? po ilu minutach? |
| 13 skutek | | | | | — | prognoza a wynik |
| 14 zamknięcie | | | | — | — | |
