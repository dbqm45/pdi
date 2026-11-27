# Decyzje o skrzynce i triaż tylko przyciskiem w konsoli — plan

Stan: 2026-11-27. Właściciel zlecił zrobić to według rekomendacji. Ciąg dalszy
[zapisu decyzji po zatwierdzeniu](plan-zapis-decyzji-po-zatwierdzeniu.md): tam agent dostał szkic i zgodę z konsoli,
tu znikają narzędzia, którymi agent zamykał sprawy po samym „tak” w czacie.

## Co jest dziś

- `decide_inbox_item` (bramki, oceny skutku, problemy z pasm, autonomia, proces, szkice z rozmów, PR do przeglądu),
  `triage_problem` i `review_stale_problem` zapisują decyzję od razu, gdy model je wywoła.
- Konsola ma przyciski dla tych samych spraw, z dwoma brakami: propozycji procesu (`process`) nie da się odrzucić,
  a triaż zna tylko `accepted` i `rejected` (bez `parked` i `duplicate`).

## Decyzje (według rekomendacji)

1. Trzy narzędzia znikają z MCP (34 narzędzia). Agent czyta skrzynkę i zgłoszenia, wystawia propozycje i szkice,
   a człowiekowi podaje konsolę.
2. Konsola dostaje brakujące przyciski: `process` — approve i reject; triaż — **park** (warunek powrotu wymagany)
   i **duplicate** (oryginał `PRB-n` wymagany).
3. Decyzja przyciskiem idzie jak dotąd przez `Inbox.decide` i `ProblemStore.triage` (te same sprawdzenia).
4. Bez zmiany kontraktu i bez nowej zależności. tf `mode-pdi` opisuje stare narzędzia — osobny PR w tf.

## Kroki

1. Czerwone testy: brak narzędzi w MCP, instrukcja serwera, triaż park/duplicate w konsoli, odrzucenie `process`.
2. Kod: `mcp_server.py`, `console.py`; testy narzędzi przepisane na `Inbox.decide` i `ProblemStore.triage`.
3. Na żywo: lista narzędzi przez stdio; park i duplicate przyciskiem w przeglądarce.
4. README, instrukcja użytkownika, `integrations/claude-code`, `TODO.md`.
