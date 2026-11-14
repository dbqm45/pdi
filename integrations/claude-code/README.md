# pdi w Claude Code

Serwer MCP `pdi` (narzędzia `record_decision`, `find_decisions`, `get_decision`, `supersede_decision` oraz skrzynka i zmiany:
`list_inbox`, `decide_inbox_item`, `list_changes`, `get_change`, `retry_dispatch`)
i komenda `/record-decision`. Specyfikacja: [dokument 14](../../docs/14-pdi-standalone.md).

**Konsola w przeglądarce (Z3-lokalnie, DZ14).** Gdy pracujesz lokalnie z `sdlc up`, obok serwera MCP działa konsola
`pdi-console` na `http://127.0.0.1:8788/` (port z `PDI_CONSOLE_PORT`, domyślnie 8788; token sesji w URL). Konsola i
MCP czytają to samo (rejestr, skrzynkę, logi przebiegów), a decyzje z konsoli i z `decide_inbox_item` idą tą samą
ścieżką przez `Inbox.decide` (ten sam kod, te same sprawdzenia PR-a, ten sam zapis w rejestrze). `sdlc open` otwiera
Tablicę konsoli, a `sdlc status` pokazuje, czy konsola działa. Konsola pokazuje trzy pasy, ślad zmiany z panelem
„Pliki” i bocznym postępem fazy na żywo (z `run.progress`); nic nie pisze do klonu produktu. Plan: [docs/plan-z3-lokalnie.md](../../docs/plan-z3-lokalnie.md).

## Instalacja krok po kroku (macOS / Linux)

**1. Zainstaluj uv** (menedżer Pythona; jeśli `uv --version` już działa, pomiń):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # albo: brew install uv
```
Zamknij i otwórz terminal, sprawdź: `uv --version`.

**2. Sklonuj pdi:**
```bash
cd ~
git clone https://github.com/dbqm45/pdi.git
cd pdi
```
Jeśli masz już klon na gałęzi roboczej: `git checkout main && git pull`.

**3. Zainstaluj zależności i sprawdź, że działa:**
```bash
uv sync               # tworzy .venv w katalogu pdi; Python pobierze się sam, jeśli go brak
uv run pytest -q      # oczekiwany wynik: „… passed”, bez „failed”
```

**4. Zarejestruj serwer w Claude Code** (raz, dla wszystkich projektów). Zakładam rejestr w `~/pdi-decisions`
(Twój klon prywatnego repo); podpis to dowolny tekst, np. login:
```bash
claude mcp add --scope user pdi \
  -e PDI_REGISTRY_PATH="$HOME/pdi-decisions" \
  -e PDI_DECIDED_BY="<twój podpis>" \
  -- uv run --directory "$HOME/pdi" pdi-mcp
claude mcp list       # pdi powinien mieć status „Connected”
```

**5. Dodaj komendę `/record-decision`:**
```bash
mkdir -p ~/.claude/commands
cp ~/pdi/integrations/claude-code/record-decision.md ~/.claude/commands/
cp ~/pdi/integrations/claude-code/decisions-from.md ~/.claude/commands/   # decyzje ze Slacka i spotkań (A5)
```

**6. Próba:** uruchom `claude` w dowolnym projekcie, wpisz `/mcp` — `pdi` z 9 narzędziami. Ustal z Claude cokolwiek
drobnego, wpisz `/record-decision`, zatwierdź szkic. W `~/pdi-decisions/decisions/` pojawi się `DEC-0001.md`
z commitem (`git -C ~/pdi-decisions log`). Push robisz sam: `git -C ~/pdi-decisions push`.

Aktualizacja pdi później: `cd ~/pdi && git pull && uv sync`.
Po aktualizacji do wersji z kontraktem 0.14.0 jednorazowo: `PDI_REGISTRY_PATH=~/pdi-decisions uv run --directory ~/pdi
pdi-records migrate` — dopisuje znacznik Decision Record (`record: decision`) w starszych plikach rejestru, jednym
commitem; nowe decyzje dostają go same.
Sprawdzenie rejestru (np. przed pushem albo w CI): `uv run --directory ~/pdi pdi-validate ~/pdi-decisions` — wg
[specyfikacji Decision Record](../../contract/decision-record.md); kod wyjścia 1 przy błędzie.

Decyzje techniczne jako ADR w repo projektu (MADR 4.0.0; `--format 2` dla narzędzi czytających MADR 2.1.2, np.
Log4brains, adr-log, pyadr): `PDI_REGISTRY_PATH=~/pdi-decisions uv run --directory ~/pdi pdi-records export-madr
--out ~/sklep/docs/decisions --project sklep`. Eksport nadpisuje tylko pliki, które sam wygenerował (komentarz
`<!-- pdi: DEC-n -->`); ADR-y napisane ręcznie zostawia i zgłasza jako konflikt.

Opcjonalnie dopisz [`CLAUDE-fragment.md`](CLAUDE-fragment.md) do `~/.claude/CLAUDE.md` — Claude będzie sprawdzał
wcześniejsze decyzje, zanim coś zaproponuje.

Sprawdzenie: `claude mcp list` pokazuje `pdi` jako połączony; w sesji `/mcp` → `pdi` → 9 narzędzi.

**Fazy tf na tym komputerze (tryb lokalny, tylko do rozwoju).** Żeby zatwierdzenie bramki (`decide_inbox_item`) albo
przyjęcie zgłoszenia (`triage_problem` z `accepted`) samo uruchamiało następną fazę w lokalnym klonie repo produktu,
bez GitHub Actions, dodaj do rejestracji serwera (i tak samo do `pdi-receiver`):
```bash
  -e PDI_DISPATCH=local \
  -e PDI_DISPATCH_CHECKOUT="$HOME/sklep" \
  -e PDI_PHASE_BUDGET_USD=3 \
  -e PDI_EVENTS_URL=http://127.0.0.1:8787 -e PDI_TF_SIGNING_SECRET=<sekret odbiornika> \
```
`PDI_DISPATCH_CHECKOUT` to bezwzględna ścieżka klonu repo produktu z tf (tryb mode-pdi), bez niezatwierdzonych zmian.
Faza idzie w tle i kończy się PR-em oraz nową bramką w skrzynce. `get_change CHG-n` pokazuje `dispatch.status`
(`running`, `done` z `pr`, `failed` z `step` i `error`) i ścieżkę logu; `retry_dispatch CHG-n` ponawia nieudaną fazę.
Druga decyzja dla zmiany, której faza jeszcze trwa, jest odrzucana. `git` i `gh` muszą być zalogowane na komputerze.
Na produkcji tego nie ustawiaj — fazy idą przez Actions (R4). Szczegóły: [README](../../README.md) i
[plan L2](../../docs/plan-l2-dispatch-lokalny.md).

## Obok ci_for_sdlc i ShipScope (K-1)

Jedna rozmowa może widzieć decyzje (pdi), gotowość wymagań (ci_for_sdlc) i stan wydań (ShipScope). Oba dodatkowe
serwery są tylko do odczytu, działają lokalnie (stdio, Node, bez zależności) i czytają API swojej usługi:

```bash
claude mcp add --scope user ci-sdlc -e CI_SDLC_URL=http://localhost:4317 \
  -- node ~/ci_for_sdlc/packages/mcp/src/ci-sdlc-mcp.js
claude mcp add --scope user shipscope -e SHIPSCOPE_URL=https://shipscope.example.com -e SHIPSCOPE_TOKEN=shps_… \
  -- node ~/evdt-service-shipscope/adapters/mcp/shipscope-mcp.js
```

Token ShipScope tworzysz w Settings → General → Service tokens i trzymasz tylko w konfiguracji Claude, nie w repo.
Narzędzia i ograniczenia: `packages/mcp/README.md` w ci_for_sdlc, `adapters/mcp/README.md` w ShipScope.

## Użycie
- `/record-decision` — Claude przygotowuje szkic decyzji z rozmowy, pokazuje go i zapisuje po Twoim „tak”.
- `/decisions-from <link>` — decyzje z wątku Slacka albo transkrypcji spotkania (A5): Claude wybiera to, co
  rzeczywiście ustalono, z dosłownymi cytatami; pdi sprawdza, że cytaty są w tekście, i wystawia szkice w skrzynce;
  każdy zatwierdzasz albo odrzucasz. Tekstu rozmowy pdi nie zapisuje — tylko cytaty i link.
  Komenda ma z góry zezwolenie na narzędzia pdi, więc po „tak” nie ma drugiego pytania o uprawnienia
  (zapis jest w gicie i można go cofnąć).
- „Co już zdecydowaliśmy o …?” — Claude wywołuje `find_decisions`.
- „Które decyzje są gotowe do automatyzacji?” — `autonomy_report`: dla każdego typu decyzji odsetek szkiców AI
  zatwierdzonych bez zmian i rekomendacja poziomu (próg: 95% z ostatnich 30). `propose_autonomy_changes` wkłada
  propozycje do skrzynki; zmiana poziomu to Twoja decyzja (`decide_inbox_item`), zapisana w `autonomy.yaml` rejestru.
- „Które PR-y są gotowe?” — `list_inbox`: pozycja „PR gotowy do Twojego przeglądu” (kind `pr_ready`) pojawia się
  dopiero, gdy pętla PR agenta tf (N2) skończyła się zielonymi checkami i zamkniętymi uwagami albo przekazaniem do
  Ciebie (`needs_human`, np. „nie udało się po 2 rundach”). Pytania z pętli są w polu `open_questions` i w sekcji
  „Przewodnik dokończenia” opisu PR; po przejrzeniu zamknij pozycję `decide_inbox_item` z `outcome: reviewed`
  (bez wpisu w rejestrze — scalasz w GitHubie). Rundy, koszt i powód: `get_change` (`pr_loop`) i `get_trace`.
- „Kiedy będzie CHG-12?” — `forecast_change` (cięcia z ShipScope × tempo dostarczonych zmian, z przedziałem
  i wątpliwościami); „Jak trafne są prognozy?” — `forecast_report`.
- Plik decyzji: `$PDI_REGISTRY_PATH/decisions/<projekt>/DEC-nnnn.md` (frontmatter YAML + czytelna treść);
  projekt = nazwa repo, w którym pracujesz; decyzje ogólne w `decisions/_ogolne/`. Numery są wspólne dla wszystkich
  projektów.
- Nazwa projektu jest też w samym pliku (pole `project` we frontmatterze i linia „projekt: …” w treści) i to ona
  rozstrzyga. Plik przeniesiony ręcznie do innego katalogu nadal jest znajdowany; przy najbliższej zmianie tej decyzji
  (np. zastąpieniu) rejestr odkłada go z powrotem do katalogu z pola `project`. Żeby zmienić projekt decyzji, zmień
  pole `project` w pliku i przenieś plik do katalogu o tej nazwie.
