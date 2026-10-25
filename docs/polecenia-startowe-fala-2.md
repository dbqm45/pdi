# Polecenia startowe — fala 2 planu G1/G2 (G2.4 w tf, G2.1 w ci_for_sdlc)

**Data:** 2026-10-25 · **Źródło:** [plan G1/G2](plan-g1-g2.md) §4.4, §4.5, §4.7 · **Wymaga:** K0 (kontrakt 0.4.0 na `main` pdi)

Oba kroki mogą iść równolegle. Każde polecenie wklejasz w nowej sesji uruchomionej w katalogu danego repo
(wtedy działają jego hooki). Sesja potrzebuje odczytu `dbqm45/pdi`, żeby skopiować zestaw wzorcowy — jeśli nie ma
dostępu, skopiuj katalog `contract/fixtures/story-shape/` ręcznie i podaj ścieżkę.

## G2.4 — tf: autor historyjek

Kopia tego polecenia jest też w tf: `docs/plans/2026-10-23-integracja-pdi.md` (gałąź `claude/magical-dirac-wjvn8y`).

```text
Realizujemy krok G2.4 planu G1/G2 z repo dbqm45/pdi (docs/plan-g1-g2.md, §4.2 reguły, §4.5 zmiany w tf, §4.7 kroki).
Przeczytaj też w pdi (main, kontrakt 0.4.0): contract/README.md (sekcja „Konwencje”) i cały katalog
contract/fixtures/story-shape/ (README.md — jak oznaczono przypadki; stories.json; expected.json; vocabulary.json).

Cel: wymagania pisane z agentem mają GWT, jedną ścieżkę na historyjkę i identyfikatory AC; Talos nie zaczyna
historyjki, która miesza ścieżki.

1. Zestaw wzorcowy: skopiuj contract/fixtures/story-shape/ z pdi do packs/pack-it/tests/fixtures/pdi-story-shape/
   (z plikiem VERSION = 0.4.0). Nie zmieniaj etykiet w kopii — rozbieżność z expected.json to błąd lintera albo
   zgłoszenie do pdi (zmiana kontraktu), nie poprawka kopii.
2. requirements_lint.py (packs/pack-it/skills/proc-requirements-shaping/scripts/):
   - wydziel funkcję sprawdzającą pojedynczą historyjkę (tytuł, opis, surowe AC, opcjonalnie story points) i używaj
     jej przy lincie pliku requirements.md;
   - słowa kluczowe GWT z vocabulary.json, w tym brakujące dziś polskie warianty (Zakładając, że / Mając / Kiedy /
     Jeżeli / Jeśli / Oraz / I / Ale);
   - nowe sprawdzenia z identyfikatorami reguł kontraktu: AC-001 (scenariusz bez Then/Wtedy, AC poza formatem),
     AC-002 (słaby wynik z weak_results), AC-004 (druga akcja w scenariuszu), STORY-001 (kilka akcji: spójniki
     w tytule/celu, kilku aktorów, różne akcje główne w scenariuszach), STORY-003 (tytuł od warstwy);
     istniejące LEAK_PATTERNS jako AC-003 z rozszerzeniem z vocabulary.json (tabela, kolumna, endpoint);
     STORY-002 tylko z liczby scenariuszy i akcji (bez estymaty);
   - nowe problemy jako ostrzeżenia (kod 0); --strict zamienia je w kod 1. Istniejące zachowanie bez zmian.
3. Test w packs/pack-it/tests/: na kopii zestawu, z polityką z expected.json (i nadpisaniami policy w przypadkach),
   dla reguł zaimplementowanych w tf wynik ma się zgadzać z expected.json; raportuj precyzję i czułość per reguła
   (cel z planu §4.8: precyzja ≥ 0,8, czułość ≥ 0,7). Liczba jednostek AC zgodna z polem scenarios.
4. Skille: proc-requirements-shaping (faza 4: każda US-NN ma ≥ 1 scenariusz AC-n w GWT i jedną akcję; więcej akcji →
   podział wg mapa-i-dzielenie.md), proc-agile/references/mapa-i-dzielenie.md (sekcja „Sygnały, że historyjka
   miesza funkcjonalności” — te same sygnały co STORY-001…003), talos-story-run (§1 Przyjęcie: lint historyjki;
   z --auto historyjka łamiąca STORY-001 kończy się blokiem STOP z propozycją podziału), qa-spec-first-testing
   (test akceptacyjny nazwany identyfikatorem scenariusza, np. US-02/AC-3).

Zasady repo tf: plan (pliki, kolejność, testy) zapisany przed kodem; TDD (najpierw czerwony test); skille zmieniasz
wg core-skill-authoring (najpierw scenariusze ewaluacji), płatne ewaluacje tylko za moją zgodą; claude-team-factory
i ev-team-factory nietknięte. Bramki: python3 tools/workspace.py check --packs all; python3 tools/workspace.py refs;
for t in tests/test_*.py; do python3 "$t" || exit 1; done; skill_gate dla zmienionych skilli w złożonym projekcie;
tytuł PR: python3 scripts/check_commit_message.py "<tytuł>". Commit i PR — na moją prośbę.
Poza zakresem: G1.1 (plan wydania) i reguły REL; zmiany w kontrakcie pdi.
```

## G2.1 — ci_for_sdlc: parser kryteriów akceptacji

```text
Implement step G2.1 of the G1/G2 plan from repo dbqm45/pdi (docs/plan-g1-g2.md: §4.1, §4.4, §4.7).
Read in pdi (main, contract 0.4.0): contract/README.md, contract/story.schema.json and the whole
contract/fixtures/story-shape/ directory (README.md — how cases are labelled; stories.json; expected.json;
vocabulary.json). Answer me in Polish; code, commits and PR title in English (repo CLAUDE.md).

Goal: ci_for_sdlc sees GWT scenarios as whole units and knows their identifiers (AC-n).

1. Fixtures: copy contract/fixtures/story-shape/ from pdi to packages/core/test/fixtures/pdi-contract/0.4.0/story-shape/
   (pinned contract version in the path). Do not edit labels in the copy — a mismatch with expected.json is a parser
   bug or a contract change request to pdi.
2. packages/core/src/analysis/acceptance.ts (new): parser that groups AC lines into units — GWT scenarios (EN and PL
   keywords from vocabulary.json, incl. Zakładając, że / Mając / Kiedy / Jeżeli / Jeśli / Oraz / I / Ale; a scenario
   may be written on one line), EARS sentences, free-text points; assigns AC-1…AC-n; extracts the main action from
   When/Gdy (verb + object, normalised so that data variants map to the same action) and flags extra actions in a
   scenario (second When, or And/Oraz right after When). Input: the same string[] the connector produces today
   (bullets(acRaw) in connectors/atlassian.ts) — check how bullets() splits GWT text and blank lines; if it loses
   information the parser needs, change the connector minimally and say so.
3. packages/core/src/model.ts: RequirementItem gets acScenarios?: AcScenario[] and storyPoints?: number (types aligned
   with contract/story.schema.json scenario: id, format gwt|ears|free, given[], when, then[], text).
4. connectors/atlassian.ts: optional storyPointsField (like acceptanceCriteriaField); AC fetching unchanged.
5. Tests: packages/core/test/acceptance.test.ts on the fixture copy — for every story the number of units equals
   expected.json "scenarios"; format detection, AC-n ids, main action equal for same-action scenarios (e.g. SS-01,
   SS-06, SS-41 have one distinct main action), extra action detected where expected.json lists AC-004.
   Optional in this step: COV-001 counting coverage per scenario instead of per line — only if it does not change
   existing results on demo data; otherwise leave it for G2.2 and note it.
6. No new rules in this step (STORY/AC rules are G2.2). Existing rules, demo data and rule-coverage must stay green.

Way of working: write the plan (files, order, tests) before code; TDD (failing test first). Start from a fresh branch
off origin/main. Gates: npm test, npm run typecheck, npm run lint:commit on the PR title; update API contract snapshots
only if the API changes (npm run test:contract:update). Commit and PR — when I ask.
Out of scope: G2.2 rules, G2.3 AI proposals, UI, changes to the pdi contract.
```
