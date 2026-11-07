# Plan realizacji: zapis decyzji jako Decision Record

**Data:** 2026-11-07 · **Źródło:** [`TODO.md`](../TODO.md) („Format Decision Record”, krok 3), decyzje DR1–DR4
([decyzje](decyzje.md)) · **Zależy od:** kontrakt 0.14.0 ([plan](plan-kontrakt-0140.md))

## Cel
Każdy plik w rejestrze pdi jest rozpoznawalnym Decision Record: nagłówek ma `record: decision`, `schema`
i `contract_version`. Pola z MADR (`consequences`, `confirmation`) da się podać z Claude i widać je w treści pliku.

## Ustalenia
1. **Znacznik nadaje rejestr**, jak `id` i `status`: przy każdym zapisie pliku (nowa decyzja, zastąpiona decyzja)
   `record: decision`, `schema` = `$id` schematu decyzji, `contract_version` = bieżąca wersja kontraktu. Szkic
   z tymi polami jest odrzucany z podpowiedzią — wersji nie podaje klient.
2. **Migracja istniejących rejestrów:** `pdi-records migrate` dopisuje znacznik w plikach, które go nie mają,
   w miejscu, w którym leżą (bez przenoszenia między katalogami projektów), jednym commitem. Ponowne uruchomienie
   niczego nie zmienia. Nazwy plików bez zmian (DR2).
3. **Treść pliku:** sekcje „Skutki” (`[dobry]` / `[zły]` / `[neutralny]`) i „Jak sprawdzić” (`how`, rodzaj,
   odwołanie), gdy pola są podane.
4. **MCP:** `record_decision`, `supersede_decision` i `decide_inbox_item` przyjmują `consequences` i `confirmation`;
   komenda `/record-decision` podaje je tylko wtedy, gdy wynikają z rozmowy.
5. **tf bez zmian:** `changes/CHG-n/decisions.md` to dziennik wpisów, nie pliki decyzji; do rejestru trafia przez
   eksport (`decision_record.py export`), a znacznik nadaje wtedy rejestr pdi.

## Pliki
| Plik | Zmiana |
|---|---|
| `src/pdi/registry.py` | znacznik przy zapisie, `REGISTRY_FIELDS`, `add_record_markers`, sekcje w treści |
| `src/pdi/records.py` (nowy) | CLI `pdi-records migrate` |
| `pyproject.toml` | punkt wejścia `pdi-records` |
| `src/pdi/mcp_server.py` | `consequences`, `confirmation` w narzędziach |
| `integrations/claude-code/record-decision.md`, `TODO.md` | opis i stan |
| testy rejestru, CLI i MCP | |

## Kolejność (TDD)
1. Testy rejestru: znacznik w nowej decyzji i w obu plikach po zastąpieniu; szkic ze znacznikiem odrzucony;
   migracja (dopisuje, nie przenosi, commituje, druga nic nie robi); sekcje w treści.
2. Testy CLI i MCP: `pdi-records migrate` wypisuje liczbę; narzędzia przyjmują nowe pola.
3. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
