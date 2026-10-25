# Plan realizacji: K0 — kontrakt 0.4.0

**Data:** 2026-10-25 · **Źródło:** [plan G1/G2 §3](plan-g1-g2.md#3-k0--wspólny-krok-kontrakt-040)

**Stan:** zrealizowany 2026-10-25 — kontrakt 0.4.0, 300 testów, ruff, mypy `--strict`; zestaw wzorcowy 44 historyjki.

## Zakres
Jak w planie G1/G2 §3: `story.schema.json`, `release-plan.schema.json`, nowe pola w `task` i `event` (z nowym
zdarzeniem `release.stage_changed`), zestaw wzorcowy `contract/fixtures/story-shape/`, wersja 0.4.0, walidacja
w `pdi.contract`, przykłady, wpięcie G1/G2 w plan jednego flow. Wszystkie nowe pola są opcjonalne.

## Ustalenia do kodu (czego plan G1/G2 nie przesądza)
- **Decyzje DG1–DG7 nie są jeszcze przyjęte.** Kontrakt zakłada rekomendacje, ale tylko jako wartości domyślne
  i konwencje (`contract.json` → `conventions`): domyślny format AC `gwt` (DG1), słowa kluczowe EN i PL (DG2),
  linia wydania z prefiksem etykiety `release:` (DG4), plan wydania w osobnym `release.yaml` (DG6). Zmiana decyzji
  zmienia wartość domyślną, nie schematy.
- **Słowa kluczowe Gherkina:** z `gherkin-languages.json` (cucumber/gherkin, `main`, sprawdzone 2026-10-25), z polskimi
  wariantami: `Zakładając`, `Zakładając, że`, `Mając` / `Gdy`, `Kiedy`, `Jeżeli`, `Jeśli` / `Wtedy` / `Oraz`, `I` /
  `Ale`. tf rozpoznaje dziś tylko `Zakładając`, `Gdy` i `Wtedy` — to luka do uzupełnienia w G2.4.
- **Scenariusz w `story`:** format `gwt`, `ears` albo `free` (wolny tekst, `text`). `free` nie ma w planie G1/G2;
  dodane, bo historyjka z Jiry przed przepisaniem ma AC w wolnym tekście, a to stan, który opisuje reguła AC-001.
- **Zestaw wzorcowy:** `stories.json` (wejście jak z Jiry: tytuł, opis, surowe AC, opcjonalnie story points),
  `expected.json` (dla każdej historyjki: które reguły STORY/AC mają zadziałać i ile jednostek AC ma znaleźć parser;
  domyślna polityka i nadpisania dla pojedynczych przypadków), `vocabulary.json` (wspólne słownictwo dla tf
  i ci_for_sdlc: słowa kluczowe, słabe wyniki, słowa warstw, terminy implementacyjne z `LEAK_PATTERNS` tf
  rozszerzone o tabelę, kolumnę i endpoint), `README.md` (definicje reguł na potrzeby oznaczania).
- `expected.json` opisuje tylko reguły kształtu (STORY-001…003, AC-001…004). Tłumienie AC-002 tam, gdzie zadziałało
  już `REQ-003` ci_for_sdlc, to sprawa ci_for_sdlc i nie jest częścią wzorca.
- Wyrażenia regularne w `vocabulary.json` używają tylko składni wspólnej dla Pythona i JavaScriptu (bez lookbehind
  i grup nazwanych), bez `\b` obok liter spoza ASCII.

## Kolejność (TDD)
1. Testy: nowe schematy poprawne; przykłady przechodzą; przypadki niepoprawne odrzucane; zestaw wzorcowy spójny
   (44 historyjki, PL i EN, każda reguła z przypadkami pozytywnymi w obu językach, przypadki czyste, zgodność
   etykiet ze słownikiem tam, gdzie reguła opiera się na słowniku).
2. Schematy, `contract.json`, przykłady, zestaw wzorcowy.
3. `pdi.contract`, README kontraktu, plan jednego flow, status planu G1/G2.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src`.
