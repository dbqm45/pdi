# pdi — Product Decision Intelligence

Warstwa decyzji w procesie AI-native SDLC: zgłoszenia problemów, triaż, rejestr decyzji, skrzynka bramek,
orkiestracja etapów, graf śladu od zgłoszenia do wydania na PROD i ocena skutku decyzji. Współpracuje z tf
(fabryka agentów), ci_for_sdlc (kontrola spójności definicji) i ShipScope (status wydań).

Stan: **krok 1 trybu standalone zbudowany** — rejestr decyzji, serwer MCP i komenda `/record-decision`
([instalacja w Claude Code](integrations/claude-code/README.md)). Reszta flow SDLC na etapie planu.

Praca z kodem: `uv sync`, potem `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
`uv run mypy src`. Kod: `src/pdi/`, kontrakt: [`contract/`](contract/README.md), plan kroku: [`docs/plan-krok-1.md`](docs/plan-krok-1.md).

## Kierunek (od 2026-10-23)

- [`docs/14-pdi-standalone.md`](docs/14-pdi-standalone.md) — **pierwszy krok: pdi jako niezależny rejestr decyzji** z zapisem jednym kliknięciem tam, gdzie decyzje zapadają (najpierw Claude CLI przez MCP i `/record-decision`, potem Slack, Confluence, Jira); flow SDLC korzysta z tego samego rejestru. Specyfikacja MVP i kryteria walidacji na sobie.

- [`docs/decyzje.md`](docs/decyzje.md) — decyzje właściciela (przyjęte: D1 kontrakt w [`contract/`](contract/README.md), D2/R1 podział rejestru decyzji).
- [`docs/plan-jeden-flow-sdlc.md`](docs/plan-jeden-flow-sdlc.md) — plan połączenia czterech projektów w jeden flow (fazy F0–F6, decyzje D1–D7).
- [`docs/kontekst-rozmowy.md`](docs/kontekst-rozmowy.md) — kontekst i przekazanie dla kolejnej sesji.
- [`docs/13-rola-pdi-w-sdlc.md`](docs/13-rola-pdi-w-sdlc.md) — **rola pdi w procesie**: co posiada, co wywołuje, na których etapach pojawia się człowiek w pdi; rozbieżności między wersjami mapy i planem (R1: gdzie żyje rejestr decyzji). Źródło: [mapa procesu, wersje 1 i 2](docs/zrodla/2026-10-23-mapa-sdlc.md).
- [`docs/12-zmiana-kierunku-sdlc.md`](docs/12-zmiana-kierunku-sdlc.md) — **jak wcześniejsza praca koncepcyjna (dokumenty 01–11, testy v1 i v2) przechodzi do nowego kierunku**: co wchodzi do kontraktu i modułów pdi, co jest wstrzymane, propozycje do D2 i F0.

## Wcześniejsza praca koncepcyjna (2026-10-19 – 2026-10-22)

Powstała, gdy pdi było projektowane jako samodzielne narzędzie dla PM-ów. Wnioski z niej zasilają nowy kierunek
(szczegóły w [dokumencie 12](docs/12-zmiana-kierunku-sdlc.md)); dokumenty zostają jako uzasadnienie i materiał wejściowy.

| Obszar | Dokumenty | Status w nowym kierunku |
|---|---|---|
| Model decyzji (statusy epistemiczne, założenia nośne, warunki unieważnienia) | [02](docs/02-living-decision-model.md), [`model/living-decision-model.schema.json`](model/living-decision-model.schema.json) | **wejście do kontraktu** (schemat decyzji w `contract/`, F0) |
| Wzorce ryzyka R1–R12 | [03](docs/03-decision-risk-radar.md) | wejście do wzbogacenia i przeglądu intencji (B1) |
| Zamykanie luk w wiedzy | [04](docs/04-knowledge-gap-closure.md) | wejście do pytań doprecyzowujących (intake) |
| Poziomy uwagi i reguły antyszumowe | [05](docs/05-attention-intelligence.md) | wejście do skrzynki bramek i powiadomień |
| Strażnik podstaw decyzji (decyzja 11) | [11](docs/11-propozycja-wartosci.md) | wejście do rejestru decyzji i oceny skutku |
| Testy v1 i v2 (metoda ewaluacji, wyniki) | [eval/status-zamowienia](eval/status-zamowienia/README.md), [eval/v2-pamiec-decyzji](eval/v2-pamiec-decyzji/README.md) | wejście do evali flow (F6) |
| Wizja, plan projektu, weryfikacja planu, MVP | [01](docs/01-wizja.md), [06](docs/06-mvp-i-pilotaz.md), [08](docs/08-plan-projektu.md), [09](docs/09-weryfikacja-planu.md) | **zastąpione** planem jednego flow |
| Ryzyka, analiza konkurencji | [07](docs/07-ryzyka-i-otwarte-pytania.md), [10](docs/10-analiza-konkurencji.md) | tło; pytanie „produkt czy narzędzie wewnętrzne” rozstrzygnięte na rzecz narzędzia w ramach flow |
| Pozyskiwanie design partnerów (zewnętrzni PM-owie) | [outreach/](outreach/profil-design-partnera.md) | **wstrzymane** |
| Przykład roboczy | [`examples/status-zamowienia.yaml`](examples/status-zamowienia.yaml) | materiał testowy |
