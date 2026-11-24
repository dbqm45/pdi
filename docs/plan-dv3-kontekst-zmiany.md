# DV3 — kontekst zmiany na start zadania (Context Reconstruction)

Stan: 2026-11-24. Krok DV3 z `docs/plan-budowy-suity.md` §3d, wersja „z grafem śladu od razu”. Zależy od F5 (graf
śladu, `pdi.trace`) i `applies_to` (kontrakt 0.22.0, [plan](plan-applies-to.md)).

## Cel
Agent (albo człowiek), który zaczyna pracę nad zmianą, dostaje jednym wywołaniem: po co jest zmiana, co już
zdecydowano i czego nie wybrano, które decyzje obejmują pliki, które ruszy, co jeszcze czeka na odpowiedź, które PR-y
już są i czego brakuje. Krótszy czas do pierwszej wartościowej zmiany, mniej pracy wbrew wcześniejszym decyzjom.

## Ustalenia
1. **`pdi.context.reconstruct(registry, change=None, paths=(), components=())`** — tylko odczyt, składa to, co pdi
   ma, bez ShipScope:
   - `change`: status, bramki zatwierdzone i oczekujące (stan zmiany);
   - `problem`: zgłoszenie z `links.prb` decyzji (`id`, `title`, `who`, `cannot`, `impact`, `status`), jeśli jest
     w bazie zgłoszeń;
   - `intent`: decyzja o intencji z metryką sukcesu (`impact.intent_decision`);
   - `decisions`: obowiązujące decyzje o zmianie (`links.chg`) — ustalenie, uzasadnienie, **odrzucone opcje**
     (`chosen: false`) i założenia nośne;
   - `code_decisions`: obowiązujące decyzje, których `applies_to` obejmuje `paths` / `components` (bez tych, które
     już są w `decisions`), z `matched`;
   - `open_questions`: otwarte pozycje skrzynki tej zmiany (bramka, pytania, opcja domyślna, termin);
   - `prs` i `gaps` z grafu śladu (`trace(..., live=False)`).
   Bez `change` — tylko `code_decisions` (start pracy poza zmianą CHG). Nieznana zmiana → błąd jak `get_trace`.
2. **MCP `change_context(change?, paths?, components?)`**; opis mówi: wołaj na start pracy nad zmianą, zanim
   napiszesz plan.
3. **tf** (osobny PR): skill `pdi-decisions` — na start zadania nad CHG `change_context` z plikami, które zmiana
   ruszy; bez serwera pdi — lokalnie `decision_record.py context CHG-n` (intencja z `intent.md`, decyzje z
   `decisions.md`, pytania do bramki z `plan.md`) i `decision_cache.py search`.
4. Poza zakresem: otwarte pytania z DI Definition (ci_for_sdlc) — wersja pełna po D8.

## Kolejność (TDD)
1. Testy (czerwone) `tests/test_context.py`: intencja, zgłoszenie, decyzje z odrzuconymi opcjami, decyzje dla plików
   bez powtórzeń, otwarte pytania, PR i luki z grafu, wywołanie bez zmiany, nieznana zmiana; MCP.
2. Kod, potem bramki: `uv run pytest`, ruff, `mypy --strict src`, Python 3.11.
