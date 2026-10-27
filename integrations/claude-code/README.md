# pdi w Claude Code

Serwer MCP `pdi` (narzędzia `record_decision`, `find_decisions`, `get_decision`, `supersede_decision` oraz skrzynka i zmiany:
`list_inbox`, `decide_inbox_item`, `list_changes`, `get_change`, `retry_dispatch`)
i komenda `/record-decision`. Specyfikacja: [dokument 14](../../docs/14-pdi-standalone.md).

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
```

**6. Próba:** uruchom `claude` w dowolnym projekcie, wpisz `/mcp` — `pdi` z 9 narzędziami. Ustal z Claude cokolwiek
drobnego, wpisz `/record-decision`, zatwierdź szkic. W `~/pdi-decisions/decisions/` pojawi się `DEC-0001.md`
z commitem (`git -C ~/pdi-decisions log`). Push robisz sam: `git -C ~/pdi-decisions push`.

Aktualizacja pdi później: `cd ~/pdi && git pull && uv sync`.

Opcjonalnie dopisz [`CLAUDE-fragment.md`](CLAUDE-fragment.md) do `~/.claude/CLAUDE.md` — Claude będzie sprawdzał
wcześniejsze decyzje, zanim coś zaproponuje.

Sprawdzenie: `claude mcp list` pokazuje `pdi` jako połączony; w sesji `/mcp` → `pdi` → 9 narzędzi.

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
  Komenda ma z góry zezwolenie na narzędzia pdi, więc po „tak” nie ma drugiego pytania o uprawnienia
  (zapis jest w gicie i można go cofnąć).
- „Co już zdecydowaliśmy o …?” — Claude wywołuje `find_decisions`.
- „Które decyzje są gotowe do automatyzacji?” — `autonomy_report`: dla każdego typu decyzji odsetek szkiców AI
  zatwierdzonych bez zmian i rekomendacja poziomu (próg: 95% z ostatnich 30). `propose_autonomy_changes` wkłada
  propozycje do skrzynki; zmiana poziomu to Twoja decyzja (`decide_inbox_item`), zapisana w `autonomy.yaml` rejestru.
- „Kiedy będzie CHG-12?” — `forecast_change` (cięcia z ShipScope × tempo dostarczonych zmian, z przedziałem
  i wątpliwościami); „Jak trafne są prognozy?” — `forecast_report`.
- Plik decyzji: `$PDI_REGISTRY_PATH/decisions/<projekt>/DEC-nnnn.md` (frontmatter YAML + czytelna treść);
  projekt = nazwa repo, w którym pracujesz; decyzje ogólne w `decisions/_ogolne/`. Numery są wspólne dla wszystkich
  projektów.
- Nazwa projektu jest też w samym pliku (pole `project` we frontmatterze i linia „projekt: …” w treści) i to ona
  rozstrzyga. Plik przeniesiony ręcznie do innego katalogu nadal jest znajdowany; przy najbliższej zmianie tej decyzji
  (np. zastąpieniu) rejestr odkłada go z powrotem do katalogu z pola `project`. Żeby zmienić projekt decyzji, zmień
  pole `project` w pliku i przenieś plik do katalogu o tej nazwie.
