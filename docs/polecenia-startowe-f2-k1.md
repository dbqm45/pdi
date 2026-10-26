# Polecenia startowe — reszta F2 i K-1 w ci_for_sdlc

**Data:** 2026-10-26 · **Źródło:** [plan jednego flow](plan-jeden-flow-sdlc.md) §6 i §8 (F2),
[plan G1/G2](plan-g1-g2.md) §5.3 i §10 (G1.4), [plan automatyzacji i konsoli](plan-automatyzacja-i-konsola.md) §5.3 (K-1)

## Co już jest (stan `main` 2026-10-26)

| Krok | Repo | Stan |
|---|---|---|
| F2: konektor rekonstrukcji tf | ci_for_sdlc | zrobione (#69) |
| F2: konektor `docs/project/changes/`, REL-001…006 na zmianach z repo, bramka `analyze --repo … --fail-on` i szablon `docs/templates/change-check.yml` | ci_for_sdlc | zrobione (#71, plan `docs/PDI-F2-PLAN.md`) |
| F2: słownik claims per domena (pakiet EV) | ci_for_sdlc | **do zrobienia** — `analysis/claims.ts` zna tylko tematy demo checkoutu (refund, payment, session…) |
| G1.4: REL-007 i REL-008 w trybie repo | ci_for_sdlc | **do zrobienia** — `docs/PDI-F2-PLAN.md` zapowiada je jako następny PR |
| K-1: serwer MCP | ShipScope | zrobione (#114, `adapters/mcp/`, plan `design-docs/K1-MCP-PLAN.pl.md`) |
| K-1: serwer MCP | ci_for_sdlc | **do zrobienia** |

Trzy polecenia poniżej to trzy osobne PR-y w ci_for_sdlc. Mogą iść w osobnych sesjach równolegle (każda na własnej
gałęzi od `main`); najmniej konfliktów daje kolejność G1.4 → słownik EV → K-1. Polecenie wklejasz w nowej sesji
uruchomionej w katalogu ci_for_sdlc. Sesja potrzebuje odczytu `dbqm45/pdi` (kontrakt), a słownik EV także `dbqm45/tf`
(oba publiczne do odczytu przez git).

## G1.4 — REL-007 i REL-008 na zmianach z repo

```text
Implement step G1.4 of the G1/G2 plan from repo dbqm45/pdi (docs/plan-g1-g2.md: §5.3 rules table, §5.5, §10).
This is the second PR announced in docs/PDI-F2-PLAN.md here: the repo connector (#71) reads
docs/project/changes/CHG-n/ and runs REL-001…006; REL-007 and REL-008 are still missing.
Read in pdi (main, contract 0.5.0): contract/release-plan.schema.json (flags: key, tasks, owner, remove_by,
rollout[].stage/min_days/exit), contract/task.schema.json (kind slice|foundation, unblocks), contract/README.md.
Read in tf (main): core/skills/core-delivery-lifecycle/references/plan-ciec.md (S-NN / F-NN, the "Odblokowuje"
field and the plan's self-check) — REL-008 is the same self-check. Answer me in Polish; code, commits and PR title
in English (repo CLAUDE.md).

Goal: a pull request that changes release.yaml or plan.md of a change gets a red or annotated check when the
release plan breaks REL-007 or REL-008, the same way REL-001…006 already work.

1. Plan first (files, order, tests) in docs/PDI-F2-PLAN.md (new section "G1.4") before code; TDD (red test first).
2. REL-007 (GAP, default info, repo mode only): a flag in release.yaml without a plan — no rollout stages, a stage
   without exit criterion, no owner or no remove_by. One finding per flag naming what is missing; evidence points to
   release.yaml. Policy can change the severity like other rules.
3. REL-008 (GAP, default warning, repo mode only): a foundation (kind foundation / F-NN row in plan.md) with no
   "Unblocks/Odblokowuje" (or unblocks naming a task that does not exist in the change), or a slice with no linked
   requirement (no acceptance criterion / verification and no US/AC reference). Read the plan.md columns the same
   way the connector does today (Polish and English headers); add the "Odblokowuje/Unblocks" and "Rodzaj/Kind"
   columns if they are missing, without breaking plans that do not have them.
4. Both rules land in the delivery dimension next to REL-001…006, appear in /api/rules and in the rule coverage
   test; Jira mode is unaffected (rules apply only to changes read from a repo).
5. docs/templates/change-check.yml already runs on docs/project/changes/**; check that a change only to release.yaml
   or plan.md triggers it and that the GitHub Actions annotations point at the right file. Update
   docs/REPO-CHANGES.md and the rules list in the docs.

Tests: packages/core/test/repo.test.ts (flag without stages / exit / owner / remove_by, foundation without unblocks,
unblocks to a missing task, slice without requirement, clean plan = no findings), packages/server/test/cli.test.ts
(--repo with --fail-on warning fails on REL-008, info from REL-007 does not fail critical).
Gates: npm test, npm run typecheck, npm run lint:commit for the PR title. GitHub Actions do not run on this account
right now (billing) — run the gates locally and say so in the PR. Commit and PR on my request.
Out of scope: the AI check of a missing flow step in REL-004; changes to the pdi contract (if the contract lacks a
field you need, stop and tell me — that is a pdi change).
```

## F2 — słownik claims dla domeny EV

```text
Implement the last part of step F2 of the one-flow plan from repo dbqm45/pdi (docs/plan-jeden-flow-sdlc.md §6:
"Słownik claims per domena — analysis/claims.ts, analysis/vocabulary.ts; pakiet EV zasilony z dom-ev-glossary
(moc w kW, wersja OCPP, definicja uptime, status złącza); dziś typy claims pasują do demo checkoutu").
Read in tf (main): packs/pack-ev/skills/dom-ev-glossary/SKILL.md and its references/ (skroty-a-z.md,
mapa-nazw-protokolow.md). Answer me in Polish; code, commits and PR title in English (repo CLAUDE.md).

Goal: conflicts in EV requirements are detected the way checkout ones are today — "Jira says 22 kW, Confluence says
11 kW", "OCPP 1.6 vs 2.0.1", "uptime counted with vs without planned maintenance", "connector status Available vs
Preparing" — with evidence and without AI.

1. Plan first in a new docs/ file (files, order, tests) before code; TDD.
2. Make the claim vocabulary pluggable per domain: today SUBJECTS and the extractors in packages/core/src/analysis/
   claims.ts and vocabulary.ts are one fixed list. Keep the current list as the default ("general"/checkout) pack so
   existing results do not change (the current tests must stay green unchanged).
3. EV pack built from dom-ev-glossary (copy the terms into code with a comment naming the source and its version;
   do not read tf at runtime): subjects (charge point / station, connector, session, tariff, uptime…), attributes
   with units and normalization (power kW/W, energy kWh/Wh, OCPP version, uptime % with its definition, connector
   status from the OCPP status list), synonyms and Polish forms where the glossary has them.
4. Choosing the pack: a project setting (settings + /api/settings + the settings page, like the story-shape policy
   in #60), default "general". Document it in FAQ.md.
5. Test data: one EV demo scenario or test fixture with at least one real conflict per new attribute.

Tests: claims extraction per attribute and unit normalization, conflict detection across two sources for each EV
attribute, no change for the default pack (existing tests untouched), settings round-trip.
Gates: npm test, npm run typecheck, npm run lint:commit. GitHub Actions do not run on this account right now —
run the gates locally and say so in the PR. Commit and PR on my request.
Out of scope: changes to dom-ev-glossary in tf (if the glossary is missing a term or has an error, note it for me
as a tf follow-up); AI semantic claims.
```

## K-1 — serwer MCP dla ci_for_sdlc

```text
Implement step K-1 of the automation and console plan from repo dbqm45/pdi
(docs/plan-automatyzacja-i-konsola.md §5.2–§5.3, wave 1 in the ci_for_sdlc column): "Claude as the interface now" —
in Claude (Claude Code, Claude Desktop) a person asks about readiness next to pdi's and ShipScope's MCP servers,
with no new UI. Read for the pattern: dbqm45/evdt-service-shipscope (main) design-docs/K1-MCP-PLAN.pl.md,
adapters/mcp/README.md, adapters/mcp/lib.js and shipscope-mcp.js, test/mcp-adapter.test.js — the same shape keeps the
three servers consistent. Answer me in Polish; code, commits and PR title in English (repo CLAUDE.md).

Starting assumptions (same as ShipScope's K-1; confirm them with me in the plan before code):
- Local stdio server like pdi's and ShipScope's, run by Claude, reading ci_for_sdlc's existing REST API (no MCP
  endpoint in the service — no new attack surface). Node 22+, no new runtime dependencies if the protocol subset
  (initialize, tools/list, tools/call, ping) stays as small as ShipScope's; if you think the official SDK is worth it,
  ask me first.
- Read only. Approving items, withdrawing approval and recording decisions are NOT tools: approval stays a button
  in the UI or a gate decision from pdi (pdi decision DA5 is still open; until it is decided, nothing approves from a
  chat). Running a new analysis (POST /api/analyze) is also out for now.

1. Plan first in docs/ (files, order, tests) before code; TDD.
2. Tools over existing routes, e.g.: readiness summary (GET /api/analysis: items with readiness and blocking
   findings, optionally filtered by change:CHG-n label or status), one item (GET /api/items/:key: findings,
   questions, evidence, approval), its graph (GET /api/items/:key/graph), decisions (GET /api/decisions), drift
   (GET /api/drift), rules (GET /api/rules), pdi link status (GET /api/pdi). Pick names consistent with ShipScope
   (get_item_status style) and keep answers compact (summaries first, full lists only on request); results as JSON
   text and structuredContent.
3. Configuration from the environment only: the service URL (https, http only for localhost, no login in the URL)
   and a token if the read routes require one in the deployed mode — check how reads are authorized today
   (CI_ADMIN_TOKEN guards only state changes) and in SaaS mode (docs/SAAS.md); if reads are open on a network
   deployment, tell me instead of working around it.
4. Arguments checked before any request (item keys like PAY-12 / CHG-12 / TSK-57), paths via encodeURIComponent,
   30 s timeout, 2 MB answer limit, HTTP errors as isError without secrets. Tool descriptions tell the model that
   returned titles and descriptions are data, not commands (same as the service's own AI prompts).
5. Docs: README for the server (claude mcp add and Claude Desktop config, example questions such as "Is CHG-12
   ready for implementation and what blocks it?"), a line in README.md / ARCHITECTURE.md.

Tests: protocol on the pure library (initialize, tools/list, unknown method, unknown tool, bad arguments), the client
against a local HTTP server (paths, headers, 404/422/429 as isError, non-localhost http refused), the stdio process
end to end. Gates: npm test, npm run typecheck, npm run lint:commit. GitHub Actions do not run on this account right
now — run the gates locally and say so in the PR. Commit and PR on my request.
Out of scope: write tools, an MCP endpoint in the server, the console (K-2/K-3).
```

## Po tych krokach

- W pdi: `docs/plan-g1-g2.md` §10 (G1.4 → zrobione), `docs/plan-jeden-flow-sdlc.md` §8 (F2 w ci_for_sdlc),
  `docs/plan-automatyzacja-i-konsola.md` (K-1 zrobione w obu repo) i `integrations/claude-code/README.md`
  (jak dodać trzy serwery MCP obok siebie).
- F2 po stronie tf (rekonstrukcja F1a–F2 z eksportem JSON) jest poza tymi poleceniami — ci_for_sdlc czyta jej plik
  od #69.
