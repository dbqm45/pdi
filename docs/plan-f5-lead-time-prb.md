# Plan — lead time od zgłoszenia (pdi, tf, ShipScope)

Stan: 2026-10-26. Krok z planu jednego flow (`docs/plan-jeden-flow-sdlc.md`, tabela zmian ShipScope: „Lead time od
zgłoszenia — Insights: PRB utworzone → wydane na prod”). ShipScope liczy dziś od daty intencji
(dbqm45/evdt-service-shipscope#112), bo daty zgłoszenia nie miał skąd wziąć. Decyzja właściciela z 2026-10-26: data
jedzie z repo, w nagłówku zmiany.

1. **pdi (kontrakt 0.5.0):** opcjonalne `source_reported_at` (data) w `change.schema.json`; przyjęcie zgłoszenia
   (F3) wysyła do fazy `intent` także `reported_at`.
2. **tf:** `decision_record.py change new … --source PRB-n --source-reported-at RRRR-MM-DD`; szablon `sdlc-phase.yml`
   bierze datę z treści zgłoszenia; `check` sprawdza format.
3. **ShipScope:** worker czyta `source_reported_at` z nagłówka `intent.md` (kolumna `work_items.source_reported_at`),
   zmiana dostaje `sourceReportedAt`, Insights pokazuje „Lead time: report → PROD” obok „intent → PROD”.

Zmiany założone przed tym krokiem nie mają daty zgłoszenia i zostają tylko w mierze od intencji.
