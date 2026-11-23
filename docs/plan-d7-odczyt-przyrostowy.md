# Plan realizacji: D7 — odczyt przyrostowy indeksu decyzji

**Data:** 2026-11-23 · **Źródło:** [plan budowy suity §3a](plan-budowy-suity.md) (krok D7, model pkt 5) ·
**Zależy od:** D2, D4 · **Odbiorcy:** D8 (pamięć podręczna w tf), D9 (w ci_for_sdlc)

## Cel
Aplikacja z lokalną pamięcią podręczną decyzji suity pobiera tylko to, co zmieniło się od ostatniego razu, razem
z decyzjami zastąpionymi, żeby kopia nie pokazywała nieaktualnej decyzji jako obowiązującej.

## Ustalenia
1. **Chwila zmiany decyzji** (`changed_at`): `recorded_at`; dla zastąpionej — `recorded_at` następczyni, bo wtedy
   zmienił się jej status. Bez nowego pola w kontrakcie.
2. **Znacznik (`cursor`):** `<changed_at>/<id>`, np. `2026-11-23T10:00:00Z/DEC-0007`. `since` przyjmuje znacznik
   z poprzedniej odpowiedzi (zwraca to, co po nim) albo samą chwilę UTC `RRRR-MM-DDTGG:MM:SSZ` (od niej włącznie);
   bez `since` — wszystko. Kolejność: `changed_at`, potem numer decyzji, więc znacznik jest jednoznaczny także przy
   kilku zmianach w tej samej sekundzie.
3. **Filtry zakresu:** `project`, `app` (jak w D4), `scope` (`origin.scope`, np. repo `owner/name`). Organizacji
   jeszcze nie ma (czeka na usługę tożsamości).
4. **Odpowiedź:** `decisions` — pełne wpisy z `changed_at` i `text` (plik Decision Record dosłownie, do zapisania
   w pamięci podręcznej), `next` (znacznik do następnego wywołania), `complete` (czy to koniec, czy jest dalsza
   strona; domyślnie 200 na stronę).
5. **Gdzie:** `Registry.changes_since`, polecenie `pdi-records changes [--since …] [--project …] [--app …]
   [--scope …] [--limit …]` (JSON na wyjściu — hook fabryki wywołuje je lokalnie) i narzędzie MCP
   `list_decision_changes`. API HTTP — razem z usługą pdi (DA4), bez nowego portu teraz.

## Pliki
`src/pdi/registry.py`, `src/pdi/records.py`, `src/pdi/mcp_server.py`, testy rejestru, CLI i MCP,
`docs/plan-budowy-suity.md`, `integrations/claude-code/README.md`.

## Kolejność (TDD)
1. Testy: pierwsze pobranie zwraca wszystko z `text`; drugie od `next` — tylko nowe; zastąpienie oddaje też starą
   decyzję ze statusem `superseded`; kilka zmian w jednej sekundzie i stronicowanie bez gubienia i powtórzeń; `since`
   jako chwila (włącznie) i błędny `since`; filtry `project`, `app`, `scope`; CLI (JSON) i MCP.
2. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
