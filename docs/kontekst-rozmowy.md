# Kontekst rozmowy (2026-10-23) — punkt startowy dla kolejnej sesji

Podsumowanie rozmowy, z której powstał [`plan-jeden-flow-sdlc.md`](plan-jeden-flow-sdlc.md). Następna sesja
zaczyna od tego pliku i od planu.

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
- Stan: **nic nie zostało jeszcze zaimplementowane**. Jest plan, 7 decyzji do podjęcia i kolejność faz F0–F6.
- Następny krok: **F0 — kontrakt** (schematy w `pdi/contract/` + dziennik per zmiana w tf).

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
pdi · D6 budżet agentów · D7 format dziennika w ShipScope. Rekomendacje są w planie; **żadna nie została jeszcze
zatwierdzona przez właściciela**.

## Przekazanie — jak kontynuować
1. Przeczytaj ten plik, `docs/plan-jeden-flow-sdlc.md`, `docs/13-rola-pdi-w-sdlc.md` (rola pdi, rozbieżność R1
   co do rejestru decyzji) i `docs/12-zmiana-kierunku-sdlc.md` (propozycje pól schematu
   decyzji i zdarzenia `decision.basis_invalidated`, wynikające z testów v1 i v2).
2. Zatwierdź albo zmień decyzje D1–D3 (blokują F0).
   **Pierwszy krok budowy (2026-10-23):** pdi standalone — `docs/14-pdi-standalone.md`: schemat decyzji,
   rejestr w markdown, serwer MCP (`record_decision`, `find_decisions`), komenda `/record-decision`,
   10 dni walidacji na sobie (kryteria W1–W4).
3. F0 w pdi: `contract/` ze schematami JSON (problem, zmiana, decyzja, zdarzenie), zasady ID, testy walidacji;
   rozważ instalację tf w pdi (`tf`) i przejście fazy 0–4 cyklu tf dla samego pdi (przebieg próbny).
4. F0 w tf (osobna sesja z repo tf): `core-project-record` — dziennik per zmiana `docs/project/changes/<ID>/`,
   pola `change` i `source` w nagłówku, `project_record.py change new`.
5. Potem F1 (dopisek `Change:` w tf + sync elementów z repo w ShipScope) — szczegóły w planie.

Wersja HTML planu (prywatny artifact): https://claude.ai/artifact/DoRYpdhzHwjTpGEnBx3UvV
