# pdi w Claude Code

Serwer MCP `pdi` (narzędzia `record_decision`, `find_decisions`, `get_decision`, `supersede_decision`)
i komenda `/record-decision`. Specyfikacja: [dokument 14](../../docs/14-pdi-standalone.md).

## Wymagania
- [uv](https://docs.astral.sh/uv/) i klon repo pdi (`uv sync` w katalogu pdi).
- Katalog rejestru: osobne prywatne repo `pdi-decisions` ([decyzja D-S1](../../docs/decyzje.md)) — zapis robi
  w nim commit; push robisz sam. Na próbę wystarczy dowolny pusty katalog.

## Instalacja (dla wszystkich projektów — zakres `user`)

```bash
claude mcp add --scope user pdi \
  -e PDI_REGISTRY_PATH="$HOME/pdi-decisions" \
  -e PDI_DECIDED_BY="<twój podpis>" \
  -- uv run --directory /ścieżka/do/pdi pdi-mcp

mkdir -p ~/.claude/commands
cp /ścieżka/do/pdi/integrations/claude-code/record-decision.md ~/.claude/commands/
```

Opcjonalnie dopisz [`CLAUDE-fragment.md`](CLAUDE-fragment.md) do `~/.claude/CLAUDE.md` — Claude będzie sprawdzał
wcześniejsze decyzje, zanim coś zaproponuje.

Sprawdzenie: `claude mcp list` pokazuje `pdi` jako połączony; w sesji `/mcp` → `pdi` → 4 narzędzia.

## Użycie
- `/record-decision` — Claude przygotowuje szkic decyzji z rozmowy, pokazuje go i zapisuje po Twoim „tak”.
  Komenda ma z góry zezwolenie na narzędzia pdi, więc po „tak” nie ma drugiego pytania o uprawnienia
  (zapis jest w gicie i można go cofnąć).
- „Co już zdecydowaliśmy o …?” — Claude wywołuje `find_decisions`.
- Plik decyzji: `$PDI_REGISTRY_PATH/decisions/DEC-nnnn.md` (frontmatter YAML + czytelna treść).
