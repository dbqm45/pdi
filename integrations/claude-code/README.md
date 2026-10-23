# pdi w Claude Code

Serwer MCP `pdi` (narzędzia `record_decision`, `find_decisions`, `get_decision`, `supersede_decision`)
i komenda `/record-decision`. Specyfikacja: [dokument 14](../../docs/14-pdi-standalone.md).

## Instalacja krok po kroku (macOS / Linux)

**1. Zainstaluj uv** (menedżer Pythona; jeśli `uv --version` już działa, pomiń):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # albo: brew install uv
```
Zamknij i otwórz terminal, sprawdź: `uv --version`.

**2. Sklonuj pdi i przejdź na gałąź z kodem:**
```bash
cd ~
git clone https://github.com/dbqm45/pdi.git
cd pdi
git checkout claude/magical-dirac-wjvn8y
```
(Po scaleniu gałęzi do `main` krok `git checkout` nie będzie potrzebny.)

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

**6. Próba:** uruchom `claude` w dowolnym projekcie, wpisz `/mcp` — `pdi` z 4 narzędziami. Ustal z Claude cokolwiek
drobnego, wpisz `/record-decision`, zatwierdź szkic. W `~/pdi-decisions/decisions/` pojawi się `DEC-0001.md`
z commitem (`git -C ~/pdi-decisions log`). Push robisz sam: `git -C ~/pdi-decisions push`.

Aktualizacja pdi później: `cd ~/pdi && git pull && uv sync`.

Opcjonalnie dopisz [`CLAUDE-fragment.md`](CLAUDE-fragment.md) do `~/.claude/CLAUDE.md` — Claude będzie sprawdzał
wcześniejsze decyzje, zanim coś zaproponuje.

Sprawdzenie: `claude mcp list` pokazuje `pdi` jako połączony; w sesji `/mcp` → `pdi` → 4 narzędzia.

## Użycie
- `/record-decision` — Claude przygotowuje szkic decyzji z rozmowy, pokazuje go i zapisuje po Twoim „tak”.
  Komenda ma z góry zezwolenie na narzędzia pdi, więc po „tak” nie ma drugiego pytania o uprawnienia
  (zapis jest w gicie i można go cofnąć).
- „Co już zdecydowaliśmy o …?” — Claude wywołuje `find_decisions`.
- Plik decyzji: `$PDI_REGISTRY_PATH/decisions/DEC-nnnn.md` (frontmatter YAML + czytelna treść).
