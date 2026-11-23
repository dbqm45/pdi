# Plan realizacji: D4 — wyszukiwarka decyzji całej suity

**Data:** 2026-11-23 · **Źródło:** [plan budowy suity §3a](plan-budowy-suity.md) (krok D4) · **Zależy od:** D2
(pdi #196: indeks z `decision.recorded` od każdej aplikacji, pole `origin`)

## Cel
`find_decisions` znajduje decyzję po tym, co w niej naprawdę jest (także cytaty i skutki), pozwala zawęzić wynik do
aplikacji, z której decyzja pochodzi, i od razu podaje link do oryginału u właściciela.

## Ustalenia
1. **Szukane pola** (dziś: ustalenie, uzasadnienie, rodzaj, opcje, założenia, zależności, znaczniki) dochodzą:
   dowody (`evidence[].text`), skutki (`consequences[].text`), sposób potwierdzenia (`confirmation.how`), odpowiedzi
   na pytania (`answers`), cytat źródła (`source.excerpt`) i identyfikator u właściciela (`origin.local_id`, np.
   „D-012”).
2. **Aplikacja źródłowa** każdej decyzji: `origin.app`; bez `origin` — `source.kind`, gdy to aplikacja suity
   (decyzje ci_for_sdlc sprzed 0.16.0); inaczej `pdi` (decyzja podjęta w DI Decision).
3. **Filtr `app`** w `Registry.find` i w narzędziu MCP `find_decisions`: `pdi`, `tf`, `ci_for_sdlc`, `shipscope`
   (wartości `source` zdarzenia z kontraktu).
4. **Skrót wyniku** dostaje `app`, `link` (`origin.url`, inaczej `source.url`, gdy jest adresem `http(s)`) i, gdy
   jest, `origin` (`app`, `scope`, `local_id`), żeby agent mógł iść do oryginału zamiast zmieniać kopię w indeksie.

## Pliki
`src/pdi/registry.py` (pola, filtr, skrót), `src/pdi/mcp_server.py` (parametr i opis), `tests/test_registry.py`,
`tests/test_mcp_server.py`, `docs/plan-budowy-suity.md` (stan D4).

## Kolejność (TDD)
1. Testy: trafienie po dowodzie, skutku, potwierdzeniu, odpowiedzi, `local_id`; filtr `app` (z `origin`, ze starego
   `source.kind`, decyzja pdi); `app`, `link` i `origin` w skrócie; parametr `app` w MCP.
2. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
