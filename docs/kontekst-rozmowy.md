# Kontekst rozmowy (2026-10-23) — punkt startowy dla kolejnej sesji

Podsumowanie rozmowy, z której powstał [`plan-jeden-flow-sdlc.md`](plan-jeden-flow-sdlc.md). Następna sesja
zaczyna od sekcji „Stan na 2026-10-27” i „Przekazanie” niżej oraz od planu. Reszta pliku to zapis stanu z 23.10,
zostawiony jako uzasadnienie planu.

## TL;DR
- Cel: jeden proces **AI-native SDLC** od zgłoszenia problemu (lub pomysłu) do wydania na PROD i oceny skutku,
  zbudowany z czterech projektów: **pdi**, **tf**, **ci_for_sdlc**, **ShipScope**.
- Punkt odniesienia: playbook Anthropic „The AI-Native SDLC Playbook”
  (https://claude.com/resources/articles/the-ai-native-sdlc-playbook): pętla zamiast linii, łańcuch artefaktów
  w gicie, człowiek na bramkach, agent działa do bramki produkcyjnej i nie dalej.
- **pdi = Product Decision Intelligence**: warstwa decyzji (zgłoszenia, triaż, rejestr decyzji, skrzynka bramek,
  orkiestracja, graf śladu, ocena skutku). Na `main` repo było puste (tylko README); równolegle na gałęzi
  `claude/magical-dirac-wjvn8y` powstała wcześniejsza praca koncepcyjna (dokumenty 01–11, testy v1 i v2) —
  jak przechodzi do tego kierunku: [`12-zmiana-kierunku-sdlc.md`](12-zmiana-kierunku-sdlc.md).
- Stan na 23.10: nic nie było jeszcze zaimplementowane (plan, 7 decyzji, fazy F0–F6). Stan dzisiejszy: niżej.

## Stan na 2026-10-27
- **Fazy F0–F5 planu jednego flow są zrobione, F6 częściowo** (AI review w CI, serwery MCP, faza designu
  z tabelą ramek Figmy; kontrakt 0.9.0). Pętla zgłoszenie →
  triaż → intencja → bramki → fazy tf → wydanie → ocena skutku → nowe zgłoszenie działa w kodzie wszystkich
  czterech aplikacji; szczegóły i numery PR-ów w planie, §8.
- **Luki z mapy ekosystemu:** G1 i G2 zrobione (poza krokami zależnymi od trybu SaaS i sprintdecka; G2.3 wstrzymane,
  D-G23); G3 kroki 1–2 zrobione (czas przepływu w ShipScope #119, prognoza i kalibracja w pdi #37); G4 zrobione
  (ci_for_sdlc #75–#77); G5 i G8 czekają na wybór narzędzia; G6 i G7 to decyzje architektoniczne.
- **Automatyzacja:** A0, A1, A2 (zamykanie pytań z cytatem: ci_for_sdlc #81, #82, pdi kontrakt 0.7.0), A3, A6 i K-1
  zrobione; A4, A5, A7, A8 i konsola K-2–K-4 do zrobienia ([plan](plan-automatyzacja-i-konsola.md), §8).
- **ShipScope bez pdi i z pdi:** warstwa pdi (zmiany z repo, plan wydania, zdarzenia, API usług) działa tylko dla
  workspace'u połączonego z pdi (ShipScope #115–#118).
- **CI:** GitHub Actions znowu uruchamia zadania (zielone przebiegi 27.10 na pdi #37, ShipScope #119,
  ci_for_sdlc #79).

## Repozytoria i co w nich jest (sprawdzone)

| Repo | Czym jest | Rola w SDLC |
|---|---|---|
| `dbqm45/pdi` | puste (README z tytułem), teraz z tym planem | warstwa decyzji, do zbudowania |
| `dbqm45/tf` | „team factory”: fabryka agentów Claude Code instalowana w projektach. Następca `claude-team-factory` i `ev-team-factory` (te są nietknięte). Publiczne repo | wykonanie: cały cykl i agenci |
| `dbqm45/ci_for_sdlc` | „Continuous Intelligence for Product & Software Definition”: TS monorepo (`packages/core`, `server` Fastify, `web` React, `sandbox`), Jira + Confluence + Figma → graf kontekstu → reguły GAP/CONFLICT/AMBIGUITY/OUTDATED/MISSING_COVERAGE/DRIFT → pytania → decyzje → gotowość. Świadomie **nie analizuje kodu** | Design → bramka przed Build |
| `dbqm45/evdt-service-shipscope` | ShipScope: wielodostępna usługa (Node + Fastify + Postgres z RLS, Render), łączy wdrożenia z GitHuba, flagi (push z zewnątrz) i Jirę → status per środowisko: none / deployed (hidden) / released / partial | Deploy/Release i część Maintain |

### tf — najważniejsze elementy
- `core/skills/core-delivery-lifecycle`: fazy 0–9, bramki człowieka B1–B6, ścieżka skrócona, referencja
  `references/ai-native-sdlc.md` (playbook już opracowany), `scripts/control_band.py` (pasma 1σ/2σ/3σ).
- `core/skills/core-project-record`: dziennik `docs/project/01-discovery … 08-operations`, `decisions.md` (D-001…),
  nagłówek YAML artefaktu (`artifact`, `phase`, `status: draft|proposed|accepted|superseded|rejected`, `inputs`),
  sekcje TL;DR / Otwarte pytania / Przekazanie. **Dziennik jest per projekt, nie per zmiana.**
- Persony: dyspozytor `maja` (pack-it) / `iwona` (pack-ev), `natalia` UX, `ewa` domena, `tomasz` architekt,
  `kasia` testy, `piotr` DevOps/SRE, `kuba` product engineer i inne.
- `modes/mode-talos`: historyjka → plan z pionowych kawałków → TDD → commit na kawałek → PR + raport kosztu;
  przebiegi w `.claude/runs/` (**ignorowane przez git**).
- `packs/pack-it/skills/proc-issue-triage`: stany `needs-triage → needs-info → ready-for-agent / ready-for-human /
  wontfix`, baza odrzuconych pomysłów `.out-of-scope/` — gotowy fundament „report a problem”.
- `proc-requirements-shaping` (PRD, `requirements_lint.py`), `proc-product-discovery`, `core-plan-interview`
  (grill-me), `ddd-*`, `arch-*`, `ux-design-systems` / `ux-feature-design` (wiedza o Figmie), hooki `tdd_guard`,
  `guard_paths`, `guard_bash`, `scan_secrets`.
- `packs/pack-ev`: ~35 skilli domeny EV (OCPP, OCPI, AFIR/regulacje, KPI, operacje na assetach…).
- Plan w toku: `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` — skill `eng-project-reconstruction` (raport z kodu
  z dowodami `plik:linia`, `domain.md`, `rules.md`, `requirements.md`, szkice `CLAUDE.md`/`REVIEW.md`); F0 gotowe.

### Fakty techniczne ważne dla integracji
- ShipScope wyciąga klucze z commitów wyrażeniem `[A-Z]{2,}-[0-9]+` (`extractIssueKeys()` w
  `server/lib/deployment-logic.js`) → ID w kształcie Jiry (`CHG-12`, `TSK-57`) działają bez zmiany parsera.
- ShipScope ma `contents: read` w `TOKEN_PERMISSIONS` (`server/lib/github-app.js`) → może czytać artefakty
  zmian z repo przez GitHub Contents API.
- ShipScope liczy sub-taski do rodzica (`issueKeys()` + `subtaskKeys`) — wzór dla CHG → TSK.
- ShipScope: każda tabela klienta w `RLS_TABLES` i zapytania w `withScope()`; Fastify odrzuca nieznane pola
  (zmiana kontraktu flag wymaga zmiany schematu).
- ci_for_sdlc: klucz elementu `^[A-Za-z0-9][A-Za-z0-9_.-]*$` (`packages/server/src/schemas.ts`); API m.in.
  `/api/decisions`, `/api/items/:key/approve`, `/api/impact`, `/api/webhooks/:source`, SSE `/api/events`;
  dane w `.ci-data/` (JSON, opcjonalnie AES-256-GCM); CLI `npm run analyze -- --fail-on critical`;
  plan SaaS w `docs/SAAS.md`, roadmapa źródeł w `docs/ROADMAP.md` (GitHub i OpenAPI w Fazie 2).
- Instalacja fabryki w `ci_for_sdlc/.claude` jest starsza niż obecny tf.
- ShipScope trzyma kontekst w formacie 10xDevs (`context/foundation/prd.md` itd.), ci_for_sdlc we własnym `docs/`,
  tf w `docs/project/` — trzy różne formaty.

## Jak doszliśmy do planu (przebieg rozmowy)
1. **Ocena wobec playbooka:** ci_for_sdlc pasuje do Design (bramka gotowości), ShipScope do Deploy/Release
   (obserwacja, bez bramek). Brakowało Build/Test, bramek wdrożeń, pętli Maintain → Plan i śladu między
   etapami. Oba łączą dane po kluczu Jiry — dobry fundament.
2. **Wizja greenfield:** pomysł → grill/burza mózgów → plan → etapy i zadania → design system i ekrany w Figmie
   → stack → kontrola spójności → kod, lintery, testy → merge → CI → release notes → status wdrożenia.
   Ustalenie: **źródłem prawdy jest repo (markdown + ID), bramką jest PR**, Jira niepotrzebna w greenfieldzie
   (najwyżej lustro).
3. **Brownfield — „report a problem”:** zgłoszenia w formie „[kto] nie może [co] → [skutek]”, np.
   „Control Tower can't apply a configuration change or operation to many chargers at once”,
   „Network team can't report uptime as the time chargers were available to drivers”. Dwie bramki: tania
   („czy analizować”) i droga („czy budować”). Zgłoszenia w bazie pdi, do repo trafia dopiero przyjęta intencja.
   Odrzucenie zawsze z powodem; zgłaszający dostaje informację „wydane”, gdy ShipScope potwierdzi wydanie.
4. **Odkrycie tf:** tf już ma cykl, bramki, dziennik, triaż, Talosa i pasma kontrolne → pdi robi się cienki
   (UI + decyzje + orkiestracja), logika procesu zostaje w tf.
5. **Plan aktualizacji** wszystkich czterech projektów → [`plan-jeden-flow-sdlc.md`](plan-jeden-flow-sdlc.md).

## Gdzie jest człowiek
Triaż · B1 zakres · B2 wymagania · B3 architektura i plan · review designu · gotowość (ci_for_sdlc
„Approve for implementation”) · merge (code owner) · B4 gotowość do wydania · B5 autoryzacja PROD · włączenie
flagi · ocena skutku decyzji · B6 utrzymanie. Resztę robią agenci (AI) albo deterministyczne skrypty.

## Otwarte decyzje (szczegóły w planie, sekcja 9)
D1 gdzie kontrakt · D2 właściciel rejestru decyzji · D3 format ID · D4 Jira w brownfieldzie · D5 model wdrożenia
pdi · D6 budżet agentów · D7 format dziennika w ShipScope. Rekomendacje są w planie. **Przyjęte 2026-10-23: D1 (kontrakt w `pdi/contract/`) i D2 w wersji R1** (decyzje bez
zmiany w pdi, o zmianie w repo, pdi indeksuje) — rejestr w `docs/decyzje.md`. Pozostałe otwarte.

## Przekazanie — jak kontynuować
1. Przeczytaj „Stan na 2026-10-27” wyżej, [plan jednego flow](plan-jeden-flow-sdlc.md) §8 (fazy i luki),
   [plan G1/G2](plan-g1-g2.md) §10 i [plan automatyzacji](plan-automatyzacja-i-konsola.md) §8 (stan realizacji)
   oraz [`decyzje.md`](decyzje.md).
2. Pełna lista tego, co zostało (do zbudowania, do sprawdzenia, do decyzji, ręcznie): plan jednego flow, §8,
   „Co zostało”. Najbliższe kroki, od najmniejszej zależności:
   - **Przebieg na sobie i pilot:** jedna prawdziwa zmiana przez wszystkie aplikacje
     ([przebieg S5](przebieg-na-sobie-s5.md)), potem pilot na backlogu według planu G1/G2 (§4.8, §5.9); jego wynik
     rozstrzyga D-G23.
   - **G3 krok 3:** prognoza przy zadaniu w pokoju sprintdecka, po MVP sprintdecka (konta, import z Jiry).
     Prognozy zbierają historię dopiero od ShipScope 0.2.60 (data pierwszego commita).
   - **G5, G8:** wybór narzędzia przez właściciela; A4 (flagi według reguły) czeka na G5.
   - **A5, A7, A8, konsola K-2–K-4:** według planu automatyzacji.
   - ci_for_sdlc: nowy wzorzec wizualny `settings.png` (ręcznie, `update_snapshots`).
3. Zasady: odpowiedzi po polsku; plan przed kodem, testy najpierw czerwone; przypiętych schematów kontraktu nie
   edytuje się w aplikacjach (kopie 1:1); wersji i changelogów nie podbija się ręcznie.

Wersja HTML planu (prywatny artifact): https://claude.ai/artifact/DoRYpdhzHwjTpGEnBx3UvV
