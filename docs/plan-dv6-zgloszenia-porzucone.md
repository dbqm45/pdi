# DV6 — zgłoszenia porzucone (Zombie Work Detector)

Stan: 2026-11-25. Krok DV6 z `docs/plan-budowy-suity.md` §3d.

## Cel
Zgłoszenie odłożone (`parked`), które nie wraca, i zgłoszenie z pytaniem bez odpowiedzi (`clarifying`) wiszą w bazie
bez końca i zaśmiecają widok. pdi okresowo je wskazuje, a człowiek decyduje: zamknąć albo zwalidować ponownie.
Odzyskana przepustowość i czysta lista zgłoszeń.

## Ustalenia
1. **`pdi.stale.report(store, registry, now)`** — zgłoszenia:
   - `parked` od ponad **90 dni** (od decyzji triażu, która je odłożyła) — próg powrotu (`return_when`) nie zadziałał;
   - `clarifying` od ponad **30 dni** od ostatnich pytań — zgłaszający nie odpowiedział.
   Każda pozycja: zgłoszenie, stan, od kiedy, ile dni, powód i rekomendacja (`close` / `revalidate`). Progi jako stałe
   w kodzie, jak terminy OM1 (N1 da im źródło w operating modelu).
2. **`ProblemStore.review_stale(problem_id, outcome, draft)`** — decyzja człowieka w rejestrze (`kind: triage`,
   `decision_type: problem.stale_review`, `links.prb`, znacznik `porzucone`):
   - `close` → `rejected` z `rejection_reason: other` i notatką z decyzji; zgłaszający dostaje informację;
   - `revalidate` → z powrotem `ready_for_triage` (kolejka triażu); zgłaszający dostaje „wraca do oceny”.
   Tylko dla zgłoszeń, które raport wskazuje (inne → błąd).
3. **Gdzie widać:** MCP `stale_problems` (odczyt) i `review_stale_problem`; w konsoli sekcja „Zgłoszenia porzucone”
   z dwoma przyciskami.
4. Poza zakresem: stare historyjki w Jirze (ci_for_sdlc) — osobny krok.

## Kolejność (TDD)
1. Testy (czerwone) `tests/test_stale.py`: progi, rekomendacje, zamknięcie, ponowna walidacja, odmowa dla
   zgłoszenia spoza raportu, MCP, konsola.
2. Kod, potem bramki: `uv run pytest`, ruff, `mypy --strict src`, Python 3.11.
