# Plan L5: repo próbne `sdlc-sandbox` i `sdlc sandbox`

Data: 2026-10-30 · Źródło: [plan `sdlc up`](plan-sdlc-lokalnie.md) §2 Z5, §4 L5 i §5 · Decyzje: DL2, DL3, a teraz też
DL4 (aplikacja: strona w Node bez zależności, flagi w JSON) i DL5 (3 USD na fazę), przyjęte 2026-10-30
([decyzje](decyzje.md)) · Warunek: L4 na `main` (pdi #63, ShipScope #126).

## Cel

`uv run sdlc sandbox <nazwa>` daje prywatne repo z szablonu `dbqm45/sdlc-sandbox`:
- sklonowane obok pozostałych klonów;
- śledzone w ShipScope razem z plikiem flag;
- ustawione jako repo faz tf (`PDI_DISPATCH_CHECKOUT`).

Na nim cały scenariusz §5 przechodzi w jeden dzień. Lista kroków z oczekiwanymi wynikami:
[`przebieg-lokalny.md`](przebieg-lokalny.md).

## Szablon `dbqm45/sdlc-sandbox` (prywatne repo-szablon)

- **Aplikacja (DL4):**
  - `src/server.js` (moduł `http`, `APP_ENV=test|prod`, `PORT`), `src/page.js`, `src/flags.js`, `public/style.css`;
  - `npm test` przez `node:test`, siedem testów;
  - za flagą jest jedno zachowanie, baner `welcome_banner`.
- **Flagi:** `config/flags.{test,prod}.json` w postaci `{ "<klucz>": { "enabled": bool, "rollout": 0-100 } }`.
  ShipScope czyta je jako źródło z kodu: `{"file": "config/flags.{env}.json", "valuePath": "enabled", "rolloutPath":
  "rollout"}` (wyłączona flaga zostaje off, a włączona ma stan według `rollout`).
- **tf 5.51.1, tryb zespołowy:**
  - pakiety `pack-it`, `pack-ux` (plus `pack-editorial-pl`), tryby `mode-pdi` i `mode-talos`;
  - `tf doctor` czysty (jedno ostrzeżenie samego tf o długości listy skilli);
  - workflowy `sdlc-phase.yml`, `metric-watch.yml`, `team-factory.yml` i `change-check.yml` (ci_for_sdlc v0.1.35)
    zostają w repo, ale lokalny przebieg ich nie potrzebuje;
  - `CLAUDE.md` ma prawdziwe komendy (`npm test`; lint, typecheck i build: brak).
- **`.claude/pdi-metrics.json`:** metryki wdrożeń z ShipScope (`deployments`, `rollbacks`), `baseline: 7`,
  `recent: 2`, `service: sdlc-sandbox`. Repo próbne nie ma użytkowników, więc **skutek ocenia się ręcznie**. Pasma
  kontrolne mają sens dopiero po kilku tygodniach wdrożeń.
- **`docs/project/changes/`:** pusty katalog, gotowy na CHG-1.
- **README:** jedno zgłoszenie (data ostatniego wdrożenia w stopce za flagą `show_last_deployed`, dwa cięcia, R1 to
  cała zmiana), skrócenie czasu (`review_by` na jutro, `min_days: 0`) i kroki §5.

Szablon powstaje lokalnie. Repo na GitHubie (prywatne, oznaczone jako szablon) zakładam dopiero po Twojej zgodzie.

## `sdlc sandbox <nazwa> [--owner <login>]` (idempotentne)

1. **Właściciel:** `--owner` albo `gh api user --jq .login`.
2. **Repo i klon:**
   - repo istnieje (`gh repo view`) → klon albo `git pull --ff-only`;
   - nie istnieje → `gh repo create <owner>/<nazwa> --template dbqm45/sdlc-sandbox --private --clone`.

   Klon trafia do katalogu klonów, czyli obok klonu pdi z `config.toml`.
3. **ShipScope:** `node server/scripts/local-pdi.js track --repo <owner>/<nazwa> --flags '<config źródła z kodu>'`
   (ShipScope, osobny PR). Śledzi repo i dodaje źródło flag z kodu; oba kroki są idempotentne.
   - Kod 5 (aplikacja GitHub ShipScope nie widzi repo): raz wypisuje dokładne kliknięcia — w ShipScope Settings →
     GitHub → Install, dostęp do wszystkich repozytoriów albo do tego jednego — i czeka na Enter, potem ponawia.
   - Kod 3: najpierw `sdlc up`.
4. **pdi:** `checkout` i `[deploy] repo` w `~/.sdlc/config.toml`. Z tego `sdlc` buduje `PDI_DISPATCH_CHECKOUT` (L4: jedno
   źródło prawdy, bez drugiej kopii w `env`); pozostałe wartości zostają nietknięte. Restart `pdi-receiver`, tylko gdy
   repo produktu się zmieniło. Serwer MCP pdi czyta konfigurację przy starcie, więc zmiana działa od następnej sesji
   Claude.
5. Adres repo, ścieżka klonu i pierwszy krok §5, na końcu „gotowe”.

## Testy (najpierw czerwone)

`tests/test_stack.py` (podstawiony świat jak w L4):
- dokładne wywołanie `gh repo create`, a przy istniejącym repo tylko klon albo `pull`;
- wywołanie `local-pdi.js track` z konfiguracją źródła flag; przy kodzie 5 instrukcja raz, czekanie na Enter i
  ponowienie;
- `checkout` i `deploy_repo` zapisane bez zmiany innych ścieżek i bez zmiany `~/.sdlc/env`; restart odbiornika;
- brak sekretu w argv i wyjściu;
- drugie uruchomienie niczego nie zmienia (bez restartu i bez zapisu).

W szablonie: `npm test` i `tf doctor`. W ShipScope: `server/test/local-pdi.test.js` (`track`).

## Otwarte pytania

- **Założenie repo-szablonu na GitHubie** czeka na Twoją zgodę. Ta sesja może nie mieć prawa tworzyć repozytoriów;
  wtedy wystarczą `gh repo create dbqm45/sdlc-sandbox --private --source . --push` i `gh repo edit --template` z
  katalogu szablonu.
- **Pierwszy przebieg z Tobą** (`sdlc up`, `sdlc sandbox sdlc-proba`, krok 1 §5) wymaga Twojego Maca: Dockera,
  zalogowanego `gh` i `claude`. W tej sesji chmurowej mogę go przejść tylko na atrapach.
- **Aplikacja GitHub ShipScope:** jest prywatna i należy do Twojego konta, więc repo próbne musi należeć do tego
  samego konta (`--owner` = Twój login).
