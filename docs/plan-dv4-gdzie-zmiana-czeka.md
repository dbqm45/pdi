# DV4 — gdzie zmiana czeka (Decision Delay + Delivery Waste Detector)

Stan: 2026-11-24. Krok DV4 z `docs/plan-budowy-suity.md` §3d. Zależy od N3 (terminy, zrobione) i od terminów z bramek
(#206). Daje dane dla DV1 (które kroki procesu nie zmniejszają ryzyka) i AN3 (pomiar wartości).

## Cel
Właściciel widzi, gdzie zmiany stoją: na której bramce i od kiedy, ile czasu przebiegu to czekanie na decyzję, a ile
praca, oraz które bramki i rodzaje pozycji skrzynki czekają najdłużej.

## Ustalenia
1. **Źródło:** historia stanu zmiany (`flow`: `gate.requested`, `gate.decided`, `feature.released`) i pozycje
   skrzynki (`received_at`, `decided_at`). Bez nowych zdarzeń i pól w kontrakcie.
2. **Oś zmiany** (`delays.timeline`): każda prośba o bramkę sparowana z najbliższą decyzją tej bramki (czas czekania,
   wynik, liczba rund przy `changes_requested`); bramka bez decyzji czeka „od … do teraz” z etapem terminu z
   `waiting.stages` (przypomnienie, po terminie, wstrzymana, do przeglądu). Czas przebiegu od pierwszego wpisu
   historii do wydania (`feature.released`) albo do teraz; **czekanie** to suma przedziałów otwartych bramek (bez
   podwójnego liczenia nakładających się), **praca** to reszta. Godziny zegarowe, nie robocze — wartości do porównań,
   nie do rozliczeń.
3. **Zestawienia** (`delays.report`): zmiany otwarte, które teraz czekają, od najdłużej czekającej; dla każdej bramki
   liczba decyzji, mediana i maksimum czekania, liczba otwartych; dla rodzajów pozycji skrzynki (bramka, zgłoszenie,
   przegląd skutków, autonomia…) mediana czasu od wpływu do decyzji i liczba otwartych.
4. **Gdzie widać:** strona konsoli `/flow` („Przepływ”) i narzędzie MCP `flow_delays` (JSON, dla agentów i DV1).
5. **Poza zakresem:** czas od PR do wdrożenia — te dane ma DI Release (`/flow` w ShipScope); połączenie przy AN3.

## Kolejność (TDD)
1. Testy (czerwone) `tests/test_delays.py`: parowanie próśb i decyzji, rundy, bramka otwarta z etapem terminu,
   czekanie bez podwójnego liczenia, praca do wydania, zestawienia bramek i pozycji; strona `/flow` w
   `tests/test_console.py`; narzędzie MCP.
2. Kod, potem bramki: `uv run pytest`, ruff, `mypy --strict src`, Python 3.11.
