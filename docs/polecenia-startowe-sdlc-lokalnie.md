# Polecenia startowe: L1–L5 i etapy 2–18 planu `sdlc up`

**Data:** 2026-10-30 · **Źródło:** [plan `sdlc up`](plan-sdlc-lokalnie.md) §2 (Z1–Z5) i §4, decyzje DL1–DL3
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `9ec4e66`, ShipScope 0.2.64, ci_for_sdlc 0.1.34

L1, L2 i L3 są niezależne. Każdy idzie w osobnej sesji Claude Code w swoim repo. Polecenie wklejasz jako pierwszą
wiadomość sesji. L4 (`sdlc` w `pdi/stack/`) startuje dopiero po merge'u wszystkich trzech, a L5 (repo próbne)
po merge'u L4. Etap 2 (scenariusz S5 na sprintdecku) startuje po L5 i udanym przebiegu §5 na repo
próbnym. Etap 3 (produkcja, §7 planu) startuje po etapie 2, a etap 4 (usługa pdi
i konsola, krok K-2) po etapie 3. Etap 5 (graf śladu, rejestr decyzji i panel w Jirze, krok K-4) startuje po
etapie 4, a etap 6 (autonomia zdobywana na danych) po etapie 5.
Etap 7 (etapy flag według reguły i metryki ochronne) startuje po etapie 6, a etap 8 (uproszczone review
i lustro Jira ↔ repo) po etapie 7. Etap 9 (incydenty i aplikacja Slacka) startuje po etapie 8,
a etap 10 (rozmowa w konsoli, krok K-3) po etapie 9. Etap 11 (zaległe kroki G1/G2) startuje po etapie 10, a etap 12
(jedno wejście dla ludzi i miary przepływu) po etapie 11. Etap 13 (przełącznik funkcjonalności i pierwsze łączenie
backendów) startuje po etapie 12, a etap 14 (kolejne moduły łączenia backendów, powtarzany) po etapie 13.
Etap 15 (pilotaż z design partnerami) startuje po etapach 13–14. Etap 16 (utrzymanie i niezawodność platformy)
startuje po etapie 15, a etap 17 (cennik i rozliczenia) po etapie 16. Etap 18 (przegląd na dowodach
i nowa mapa drogowa) startuje po etapie 17.

| Krok | Repo | Sesja w katalogu |
|---|---|---|
| L1 | ShipScope | `/Users/x/WebstormProjects/evdt-service-shipscope` |
| L2 | pdi | `/Users/x/WebstormProjects/pdi` |
| L3 | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` |
| L4 | pdi | `/Users/x/WebstormProjects/pdi` |
| L5 | pdi (+ nowe repo `sdlc-sandbox`) | `/Users/x/WebstormProjects/pdi` |
| etap 2 | pdi (+ sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 3 | pdi (+ ShipScope, tf, sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 4 | pdi | `/Users/x/WebstormProjects/pdi` |
| etap 5 | pdi (+ nowe repo panelu Forge) | `/Users/x/WebstormProjects/pdi` |
| etap 6 | pdi (+ ci_for_sdlc) | `/Users/x/WebstormProjects/pdi` |
| etap 7 | pdi (+ ShipScope, tf, sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 8 | pdi (+ tf, ci_for_sdlc, sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 9 | pdi (+ ShipScope, tf, sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 10 | pdi (+ ci_for_sdlc, ShipScope) | `/Users/x/WebstormProjects/pdi` |
| etap 11 | pdi (+ ci_for_sdlc, sprintdeck) | `/Users/x/WebstormProjects/pdi` |
| etap 12 | pdi (+ ShipScope, ci_for_sdlc, tf) | `/Users/x/WebstormProjects/pdi` |
| etap 13 | pdi (+ ShipScope, tf) | `/Users/x/WebstormProjects/pdi` |
| etap 14 | pdi (+ ShipScope, ci_for_sdlc) | `/Users/x/WebstormProjects/pdi` |
| etap 15 | pdi (+ repo, w których pilotaż odsłoni luki) | `/Users/x/WebstormProjects/pdi` |
| etap 16 | pdi (+ ShipScope, ci_for_sdlc) | `/Users/x/WebstormProjects/pdi` |
| etap 17 | pdi (+ ShipScope, ci_for_sdlc) | `/Users/x/WebstormProjects/pdi` |
| etap 18 | pdi (pozostałe repo tylko do odczytu) | `/Users/x/WebstormProjects/pdi` |

GitHub Actions na tym koncie nie działa (płatności). Każde polecenie każe więc uruchomić bramki lokalnie i napisać
o tym w PR.

## L1 — ShipScope: tryb lokalny dla adresów pdi

```text
Implement step L1 of the plan "whole workflow locally with sdlc up" from repo dbqm45/pdi (main):
docs/plan-sdlc-lokalnie.md §2 row Z1 and §4 L1; decision DL2 in docs/decyzje.md (all services run as processes on
localhost, only Postgres in Docker). Answer me in Polish; code, commits and PR title in English, Conventional Commits
(repo CLAUDE.md).

Goal: a ShipScope started with `npm run dev` connects to a pdi-receiver on the same machine
(http://127.0.0.1:8787) without a tunnel, and Settings → Integrations → pdi → Test shows `connected`.

Today: server/lib/safe-fetch.js checkUrl() allows only https on port 443 with a public host name, and
resolvePublic()/forbiddenAddress() refuse loopback. lib/pdi-connection.js (Connect: receiverUrl) and
lib/outgoing-events.js (subscriptions, deliverEvents(), the pdi ping) go through it. server/scripts/dev.js creates
server/.env from .env.example but leaves TOKEN_ENCRYPTION_KEY empty, so Connect answers "This server cannot connect
pdi: TOKEN_ENCRYPTION_KEY is not set".

1. Plan first in design-docs/ (files, order, tests) before code; TDD (red test first).
2. Local mode, on only when PUBLIC_BASE_URL is http://localhost:<port> or http://127.0.0.1:<port> (the same
   condition dev:mock uses to refuse otherwise). Decide it once at start, pass it explicitly (no global reads in pure
   code), and log a warning at start like SHIPSCOPE_MOCK_DATA does.
3. In local mode, and only for the pdi receiver (Connect, its event subscription, deliveries and the ping), accept
   http or https to the loopback host names localhost, 127.0.0.1 and ::1 on any port. Connect to the loopback address
   itself, never through DNS, and keep no redirects, the time limit and the size limit. Every other address keeps
   today's rules, also in local mode: private networks (10/8, 192.168/16 …), other ports on public hosts, endpoint flag
   sources and customer URLs.
4. dev.js: when server/.env has no TOKEN_ENCRYPTION_KEY, generate one (32 random bytes, base64) once and write it; never
   replace an existing value. Tell the user in the dev output that it was created.
5. Docs: server/README.md (local setup, local mode and what it allows), CLAUDE.md where safe-fetch and the pdi
   connection are described, design-docs/SECURITY.md (why this is safe: only with a localhost PUBLIC_BASE_URL, only
   loopback, only the pdi receiver).

Tests (node:test): safe-fetch — loopback refused without local mode, accepted in local mode for the pdi purpose, a
private non-loopback address and a public http address still refused in local mode, no redirect followed;
pdi-connection — Connect with http://127.0.0.1:8787 in local mode creates the token, subscription and connection, and
the same call without local mode is refused as today; outgoing events — a delivery and a ping to a local test server
in local mode; dev.test.js — the key is generated once and an existing one is kept.
Gates: npm test (root) and npm test in server/ (with TEST_DATABASE_URL for the Postgres tests), node
scripts/check-module-boundaries.js, npm run lint:commit. GitHub Actions do not run on this account right now — run the
gates locally and say so in the PR. Commit and PR on my request.
```

## L2 — pdi: fazy uruchamiane lokalnie (`PDI_DISPATCH=local`)

```text
Implement step L2 of docs/plan-sdlc-lokalnie.md (§2 row Z2, §4 L2) in this repo, under decision DL1 in
docs/decyzje.md: pdi may run tf phases itself only when PDI_DISPATCH=local; in production phases stay in GitHub
Actions (R4). Answer me in Polish; code, commits and PR title in English.

Goal: approving a gate in Claude (decide_inbox_item) or accepting a problem (triage_problem accepted) starts the next tf
phase on this machine, in a local clone of the product repo, and ends with the phase PR and a gate.requested in the
inbox, with no GitHub Actions.

Today: src/pdi/dispatch.py dispatch_phase() only sends workflow_dispatch of sdlc-phase.yml (inbox.py _run(),
problems.py on accept, retry_dispatch). The workflow it starts is tf
modes/mode-pdi/skills/pdi-decisions/templates/sdlc-phase.yml (read it in dbqm45/tf main). Do the same steps in the same
order:
  a. refuse when the checkout has uncommitted changes; git fetch, switch main, pull --ff-only;
  b. branch pdi/<CHG>-<phase> (reuse the remote one when it exists, so rework lands in the same PR);
  c. for phase intent with a source: decision_record.py change new <CHG> --source <PRB> --author pdi
     [--source-reported-at <day from the problem>] when the change folder does not exist;
  d. phase_run.py prompt (input check), then decision_record.py decision gate when there is a decision;
  e. phase_run.py run --change --phase [--rework --gate --decision] [--budget-usd], with PDI_SOURCE and
     PDI_PROBLEM in its environment;
  f. except for delivery: commit "docs(<CHG>): faza <phase> (pdi)" with trailer "Change: <CHG>", push, PR with gh
     (existing PR reused), then phase_run.py gate request --change --phase --url <PR>.

1. Plan first in docs/ (plan-l2-dispatch-lokalny.md: files, order, tests) before code; TDD.
2. Config: PDI_DISPATCH=local plus PDI_DISPATCH_CHECKOUT (absolute path of the product repo clone; it must be a git repo
   with .claude/skills/pdi-decisions/scripts). PDI_DISPATCH_REPO and PDI_GITHUB_TOKEN are not needed in this mode;
   PDI_PHASE_BUDGET_USD applies. Without PDI_DISPATCH the behaviour is exactly today's.
3. Run in the background so the MCP call and the receiver answer at once: one detached run at a time per change (a
   second request for a change with a running phase is refused with a clear message). Every command is an argument list,
   never a shell string; inputs are validated as today (change key, phase from the list, gate, outcome, DEC id).
   The run writes its log to $PDI_REGISTRY_PATH/runs/<CHG>-<phase>-<timestamp>.log and its result next to it. The
   change state gets dispatch {mode: local, status: running | done | failed, log, pr?, error?}. get_change and
   list_changes show it, and retry_dispatch reruns a failed one.
4. Never put a token or the problem text into the log or the state, beyond what the run itself prints. Stop at the
   first failing step and record which step failed.
5. Docs: README (local mode, its variables, that it is for development; R4 still holds in production),
   integrations/claude-code/README.md, and the module docstring of dispatch.py (it says today "pdi nie uruchamia agentów
   u siebie").

Tests: the command list and order for intent with a source, for a rework and for delivery (no PR, no gate request),
with an injected runner; refusal without a checkout, with a dirty checkout and with a running phase; state transitions
running → done/failed; retry_dispatch after failed; no token in logs; unchanged behaviour without PDI_DISPATCH.
Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src. GitHub Actions
do not run on this account right now — run the gates locally and say so in the PR. Commit and PR on my request.
```

## L3 — ci_for_sdlc: gotowość zmian z repo do pdi

```text
Implement step L3 of the plan "whole workflow locally with sdlc up" from repo dbqm45/pdi (main):
docs/plan-sdlc-lokalnie.md §2 row Z4 and §4 L3. Answer me in Polish; code, commits and PR title in English,
Conventional Commits (repo CLAUDE.md).

Goal: after `npm run analyze -- --repo <path> --send-to-pdi`, pdi gets readiness.changed for every CHG-n read from the
repo, exactly as the server sends it in Jira mode. A ready change opens approve-for-implementation in the pdi inbox
without a hand-made gate request.

Today: packages/server/src/gate.ts runGate() analyses a repo checkout (docs/project/changes/, docs/REPO-CHANGES.md) and
reports, but never talks to pdi. packages/server/src/pdi.ts PdiLink queues and sends readiness.changed (signature
v1=HMAC-SHA256(PDI_SIGNING_SECRET, "<ts>.<body>"), outbox, retries, readiness only when it differs from the last one
sent), and it is used only by the server after an analysis.

1. Plan first in docs/ (PDI-L3-PLAN.md: files, order, tests) before code; TDD (red test first).
2. New flag --send-to-pdi for the CLI gate. With it, PDI_EVENTS_URL and PDI_SIGNING_SECRET are required: without them
   exit 2 with a clear message, before the analysis. After the analysis, enqueue the readiness of every change from the
   repo through the same PdiLink and its store in CI_DATA_DIR, then deliver what is due once, with a short bounded
   wait, since the CLI exits. Undelivered entries stay queued for the next run and are listed.
3. The gate's exit code means what it means today (readiness against --fail-on, file problems). A delivery failure is
   reported but does not change it. Print one line per change sent: CHG, readiness, delivered or queued.
4. Without the flag, nothing changes (no pdi traffic, same output).
5. Docs: docs/REPO-CHANGES.md (running it with pdi), README variables table, and docs/templates/change-check.yml as an
   optional commented line.

Tests (packages/server/test/gate.test.ts and the pdi tests): with the flag and both variables, a fake pdi receiver gets
one signed readiness.changed per change with the contract's shape; nothing is sent again when readiness did not
change; refusal without variables (exit 2); exit code unchanged on a failed delivery; no traffic without the flag;
contract test of the event against the pinned pdi contract copy.
Gates: npm test, npm run typecheck, npm run test:contract, npm run lint:commit. GitHub Actions do not run on this
account right now — run the gates locally and say so in the PR. Commit and PR on my request.
```

## L4 — pdi: `sdlc`, jedno polecenie dla całego stosu

Start dopiero po merge'u L1, L2 i L3 (L3: ci_for_sdlc #102). Sesja w klonie pdi.

```text
Implement step L4 of docs/plan-sdlc-lokalnie.md (§2 rows Z3 and Z5, §4 L4) in this repo, under decisions DL2
(services run as processes on localhost, only Postgres in Docker) and DL3 (`sdlc` lives in pdi/stack/) in
docs/decyzje.md. Answer me in Polish; code, commits and PR title in English, Conventional Commits.

Precondition: L1 (ShipScope local mode, dbqm45/evdt-service-shipscope), L2 (PDI_DISPATCH=local in this repo) and L3
(ci_for_sdlc `--send-to-pdi`, dbqm45/ci_for_sdlc #102) are merged to main. Check this first (pdi knows
PDI_DISPATCH=local; ShipScope's safe-fetch accepts loopback with a localhost PUBLIC_BASE_URL). If one is missing, stop
and tell me; do not work around it.

Goal: on a Mac with Docker, gh, claude, Node and uv installed, `uv run sdlc up` ends with a line "gotowe", and
`uv run sdlc status` shows `connected` for ShipScope ↔ pdi and ci_for_sdlc → pdi. Nobody copies a secret, token or
address by hand (S5 steps P2, P5, P7 and P8 in docs/przebieg-na-sobie-s5.md are what this replaces).

Today:
- pdi-receiver (src/pdi/receiver.py) listens on 127.0.0.1:8787. It verifies senders with PDI_SHIPSCOPE_SIGNING_SECRET,
  PDI_TF_SIGNING_SECRET and PDI_CI_FOR_SDLC_SIGNING_SECRET, and reads ShipScope through PDI_SHIPSCOPE_URL and
  PDI_SHIPSCOPE_TOKEN.
- The MCP server is `pdi-mcp`; impact/forecast read the same ShipScope variables.
- ShipScope's Settings → Integrations → pdi → Connect (lib/pdi-connection.js) gives the three PDI_SHIPSCOPE_* values
  once.
- ci_for_sdlc runs as a CLI on the repo:
  - command: `npm run analyze -- --repo <path> --send-to-pdi`, with PDI_EVENTS_URL, PDI_SIGNING_SECRET (=
    pdi's PDI_CI_FOR_SDLC_SIGNING_SECRET) and CI_DATA_DIR;
  - output lines: `pdi: <url>`, `  pdi readiness.changed <CHG> <readiness> delivered|queued (<why>)|unchanged`,
    `  pdi queued <type> <CHG> attempts=N next=<iso> (<error>)`;
  - exit 2 when the pdi config is missing.
  Its server is `npm start` on PORT (default 4317).
- Read ShipScope's server for its port, its dev start (`npm run dev`, web and worker), the Postgres it needs, how the
  GitHub App is created (manifest flow), and the API behind Connect and Track repository, including which
  credentials those calls need.

1. Plan first in docs/ (plan-l4-sdlc.md: commands, files, order, tests, open questions) before code; TDD (red test
   first).
   If Connect or another step can only be done by a signed-in admin in the browser, say so in the plan and propose the
   smallest way (a one-time step `sdlc up` waits for, or a separate ShipScope change for later). Do not change
   ShipScope in this PR.
2. The package src/pdi/stack/ (DL3's "pdi/stack/"; the wheel packages only src/pdi) with the entry point
   `sdlc = "pdi.stack.cli:main"` in [project.scripts]. Stdlib only:
   - argparse;
   - tomllib to read the config;
   - subprocess with argument lists, never shell strings;
   - urllib for the HTTP calls.
3. `sdlc up`, idempotent (a second run starts what is not running and changes nothing else):
   a. Check docker, gh (and `gh auth status`), claude, node, npm and uv. On a miss, print one install command per tool
      and exit 1.
   b. Config in ~/.sdlc/config.toml: the paths of the pdi, ShipScope and ci_for_sdlc clones, the decision registry
      (PDI_REGISTRY_PATH) and the optional product checkout (PDI_DISPATCH_CHECKOUT). On the first run, ask once and
      write it; afterwards never ask.
   c. ~/.sdlc/env (mode 600, ~/.sdlc 700):
      - generate the missing secrets once and never overwrite them: PDI_TF_SIGNING_SECRET,
        PDI_CI_FOR_SDLC_SIGNING_SECRET, PDI_FORM_TOKEN and ShipScope's TOKEN_ENCRYPTION_KEY;
      - set PDI_EVENTS_URL=http://127.0.0.1:8787, PDI_DISPATCH=local and the budget (DL5 recommendation:
        PDI_PHASE_BUDGET_USD=3).
   d. Start in order, each waiting for its health check with a timeout:
      - Postgres for ShipScope in Docker: a named container and a named volume, so `down` keeps the data;
      - ShipScope web and worker with a localhost PUBLIC_BASE_URL (L1 local mode);
      - pdi-receiver;
      - the ci_for_sdlc server if the plan needs it (the repo flow needs only the CLI).
      Processes run detached with pid files and logs in ~/.sdlc/logs/.
   e. On the first run, connect ShipScope to pdi through ShipScope's API and write the three PDI_SHIPSCOPE_* values into
      ~/.sdlc/env. Restart pdi-receiver so it picks them up.
   f. Register the MCP servers `pdi` and `shipscope` in Claude Code (`claude mcp add --scope user`) with the same
      variables. Re-registering replaces, never duplicates. Say in the docs where claude stores those values.
   g. Print each service with its URL and end with "gotowe".
4. `sdlc deploy <prod|test> [--repo owner/name]`:
   - use `gh api` to create a GitHub Deployment for the HEAD of main of the trial repo (environment `production` or
     `test`), then a `success` status;
   - print the deployment id and the sha.
5. `sdlc status`:
   - each process (running, pid, URL) and Postgres;
   - ShipScope ↔ pdi from ShipScope `GET /api/service/v1/connection` and pdi's get_shipscope_connection view;
   - ci_for_sdlc → pdi from the last `--send-to-pdi` result (delivered or still queued in its CI_DATA_DIR);
   - the last events in the receiver log and the open items in the pdi inbox.
   `sdlc open`: open ShipScope and the problem form in the browser. `sdlc down`: stop the processes and the Postgres
   container, keep the data. `sdlc reset`: delete the data only after I type the name it asks for.
6. Secrets:
   - never in argv of child processes (pass them through the environment), and never in logs or in sdlc's own output;
   - `status` shows only whether each is set;
   - the env file is written atomically.
7. Docs:
   - README (`sdlc` section: requirements, the five commands, the files in ~/.sdlc);
   - docs/plan-sdlc-lokalnie.md §9 (L4 state).

Tests (tests/test_stack.py, with an injected command runner, HTTP client and home dir; no real Docker, network or
processes):
- env generated with mode 600 and existing values never overwritten;
- missing tools reported with install commands;
- start order and health-check waits, and an idempotent second `up`;
- the exact `gh api` calls for deploy prod and test;
- the `claude mcp add` calls;
- the connection step writes the three variables;
- no secret in argv, logs or output;
- `reset` refuses without the typed name;
- `down` keeps the volume.

Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src. GitHub
Actions do not run on this account right now: run the gates locally and say so in the PR. Commit and PR on my request.
```

## L5 — pdi + nowe repo `sdlc-sandbox`: repo próbne

Start dopiero po merge'u L4. Sesja w klonie pdi; repo-szablon zakłada ta sama sesja, po Twojej zgodzie.

```text
Implement step L5 of docs/plan-sdlc-lokalnie.md (§2 row Z5, §4 L5, §5 test run) in this repo, under DL2 and DL3
(docs/decyzje.md). Answer me in Polish; code, commits and PR titles in English, Conventional Commits.

Precondition: L4 is merged (`uv run sdlc up` ends with "gotowe", `uv run sdlc status` shows connected for
ShipScope ↔ pdi and ci_for_sdlc → pdi, `sdlc deploy` works). Check this first. If it is missing, stop and tell me.

Decisions first: DL4 (trial app: a static page in Node with no dependencies, flags in JSON) and DL5 (budget
PDI_PHASE_BUDGET_USD=3 per phase, each phase's cost in the log) are open (plan §8, decyzje.md "Otwarte"). Show me the
recommendation for each, wait for my answer, then record both in docs/decyzje.md and the plan's §8 table.

Goal: `uv run sdlc sandbox <name>` gives me a private repo of my own, created from a template, cloned locally,
tracked in ShipScope and set as pdi's PDI_DISPATCH_CHECKOUT. On it the whole §5 scenario passes in one day: report
→ intent, requirements, architecture and design phases with gates → ci_for_sdlc readiness and approve-for-implementation
→ talos slices → `sdlc deploy test|prod` → flag stages → impact review.

Today:
- The S5 run (docs/przebieg-na-sobie-s5.md) used sprintdeck, which needs Vercel and Supabase. Its step P8 shows how
  tf goes into a product repo:
  - `tf install --packs pack-it,pack-docs,pack-ux --language pl --commit-language en --yes --shared`;
  - `tf add mode-pdi mode-talos`;
  - `tf doctor`;
  - the phase_run.py / metric_watch.py `workflow install` commands;
  - ci_for_sdlc's docs/templates/change-check.yml.
  P8 also set repo secrets and variables for Actions.
- Steps 11–12 of S5 show the flags files `config/flags.{env}.json` (`test`, `prod`). ShipScope finds them under
  Settings → Sources → Advanced sources and reads `rollout` stages from them at the deployed commit.
- ShipScope reads deployments only from GitHub Deployments, which `sdlc deploy` creates (L4).
- L4's docs/plan-l4-sdlc.md says which ShipScope API calls `sdlc` can make (Connect, Track repository) and which
  steps need a signed-in admin. Read it before planning.

1. Plan first in docs/ (plan-l5-sandbox.md: the template's files, the `sdlc sandbox` steps, tests, open questions)
   before code; TDD for the pdi part (red test first).
2. Template repo dbqm45/sdlc-sandbox (GitHub template repository, private). Build it in a local directory first and
   show me the file list. Create the GitHub repo and push only after I say so. Contents:
   a. The app per DL4:
      - a static page served by a Node server with no dependencies;
      - `npm test` using node:test;
      - one visible behaviour behind a flag read from config/flags.{env}.json, in the shape ShipScope reads (check
        ShipScope's flags reader, and mode-pdi's release.yaml rollout stages).
   b. tf installed as in S5 P8 (team mode, pack-it, pack-ux, mode-pdi, mode-talos, `tf doctor` clean). Pin the tf
      version in the README. Keep the workflow files tf installs, but note that the local run never needs them.
   c. .claude/pdi-metrics.json in the format mode-pdi expects (find it in tf's mode-pdi). Use a metric the trial app
      can produce without users, or say in the plan that impact is judged by hand.
   d. docs/project/changes/ empty, ready for CHG-1.
   e. A README with the one report to enter (small, one flag, two slices, finishable in a day) and the §5 steps.
3. `sdlc sandbox <name> [--owner <login>]` in src/pdi/stack/, idempotent:
   a. `gh repo create <owner>/<name> --template dbqm45/sdlc-sandbox --private --clone` into the folder from
      ~/.sdlc/config.toml. If the repo exists, reuse it and only clone or pull.
   b. Track the repo in ShipScope through its API and set its flags source to config/flags.{env}.json.
      If a step needs the admin in the browser, print the exact clicks once and wait for Enter (as L4 does).
   c. Set PDI_DISPATCH_CHECKOUT in ~/.sdlc/env and restart pdi-receiver.
   d. Print the repo URL, the clone path and the first step of §5. End with "gotowe".
4. Shorten time for the trial (§5 "Skrócenie czasu"):
   - SYNC_INTERVAL_MINUTES=1 for ShipScope in `sdlc up`, if L4 did not set it;
   - the README tells me `review_by` tomorrow in B1 and `min_days: 0` for flag stages.
5. Docs:
   - README `sdlc` section (`sandbox`);
   - docs/plan-sdlc-lokalnie.md §9 (L5 state);
   - a short docs/przebieg-lokalny.md: the §5 scenario as a checklist with the expected result of each step and where
     to look (ShipScope screen, inbox, `sdlc status`).

Tests (tests/test_stack.py or tests/test_sandbox.py, injected runner, HTTP client and home dir; no real gh, network or
processes):
- the exact `gh repo create` call, and reuse when the repo exists;
- the ShipScope calls for tracking and the flags source;
- PDI_DISPATCH_CHECKOUT written without touching other values;
- no secret in argv, logs or output;
- a second run changes nothing.
In the template: `npm test` passes, and `tf doctor` is clean.

Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src, plus
`npm test` in the template. GitHub Actions do not run on this account right now: run the gates locally and say so in
the PR. At the end, run `sdlc up` and `sdlc sandbox sdlc-proba` with me and walk §5 step 1. The rest of §5 I run
myself with docs/przebieg-lokalny.md. Commit, PR and the new repo on my request.
```

## Etap 2 — pdi + sprintdeck: scenariusz S5 na prawdziwym wdrożeniu

Start dopiero po merge'u L5 i udanym przebiegu §5 na repo próbnym. Sesja w klonie pdi. Sprintdeck zmieniają tylko
PR-y faz tf, a poza tym tylko po Twojej zgodzie. Tunel nie jest potrzebny: Vercel zakłada GitHub Deployments
w sprintdecku, a lokalny ShipScope pobiera je co minutę.

```text
Implement stage 2 of docs/plan-sdlc-lokalnie.md (line 4 "wraca jako etap 2, po L5"; §6 rows "prawdziwe wdrożenie"
and "skutek u prawdziwych użytkowników"): scenario S5 (docs/przebieg-na-sobie-s5.md) on dbqm45/sprintdeck, run on the
local stack from L4/L5 instead of the manual setup. Decisions DL2–DL5 in docs/decyzje.md apply. Answer me in Polish;
code, commits and PR titles in English, Conventional Commits.

Precondition: L5 is merged (`sdlc sandbox` exists) and the §5 local run passed on the trial repo (docs/przebieg-lokalny.md).
Check main and ask me about the run. If either is missing, stop and tell me.

Goal: with `uv run sdlc up` running on my Mac, one command attaches sprintdeck to the stack, and the S5 change
("minimalna analityka produktowa" behind the flag `analytics_events`) goes from report to impact review on the real
Vercel + Supabase deployment, with real users. Nobody copies a secret, token or address by hand, and there is no tunnel.

Today:
- S5 version 2 (2026-10-30) has prep steps P0–P10. L4 replaced P2, P5 (Connect), P7 and the receiver part of P6.
  L5 showed P8 (tf in a product repo) on the template. P4 (tunnel) existed only because GitHub and the production
  ShipScope had to reach pdi. Locally, ShipScope polls GitHub every minute and sends to pdi on 127.0.0.1.
- ShipScope sees deployments only through GitHub Deployments. Vercel's GitHub integration creates them on sprintdeck
  (`Production` for main, `Preview` for PRs). `sdlc deploy` must not be used here. Check the environment names Vercel
  writes and how ShipScope maps them to its environments and to config/flags.{env}.json (`test`, `prod`).
- `sdlc sandbox` (src/pdi/stack/cli.py, `track()` via ShipScope's `server/scripts/local-pdi.js track`) creates a repo
  from a template, then tracks it, sets the flags source, sets PDI_DISPATCH_CHECKOUT and `[deploy] repo`, and restarts
  the receiver. For an existing repo only the part after creation applies.
- S5 step 13 judges impact with an activation query in sprintdeck's scripts/metrics.sql, run by hand in Supabase.
  metric_watch.py needs a second ShipScope service token ("tf metric-watch", P5.5 and P8), which today is copied by hand.
- GitHub Actions do not run on this account (billing). Phases run locally through PDI_DISPATCH=local. change-check and
  metric-watch run by hand.

1. Plan first in docs/ (plan-etap2-sprintdeck.md: what S5 steps remain, what `sdlc` replaces, the new command, tests,
   open questions) before code; TDD for the pdi part (red test first). Read sprintdeck (clone it read-only) for:
   - whether tf is already installed and at which version (S5 P8);
   - whether config/flags.*.json, .claude/pdi-metrics.json and scripts/metrics.sql exist;
   - its Vercel config.
   Say which of these the S5 change itself must add (as slices) and which must exist before the run.
2. `sdlc attach <owner/name> [--path <clone>]` in src/pdi/stack/, idempotent: clone or pull into the folder from
   ~/.sdlc/config.toml, track in ShipScope with the flags source, set PDI_DISPATCH_CHECKOUT and `[deploy] repo`,
   restart pdi-receiver, print what changed and end with "gotowe". Share the code with `sandbox` (sandbox = create +
   attach); do not duplicate it. A second attach of another repo switches the checkout and says so.
   `sdlc status` shows the attached repo and whether its deployments come from GitHub Deployments (Vercel) or
   `sdlc deploy`. `sdlc deploy` refuses on a repo whose deployments come from Vercel, unless `--force`.
3. The metric-watch token without copying: if ShipScope's local-pdi.js can mint a service token the way `connect`
   does, propose the smallest ShipScope change (separate PR in dbqm45/evdt-service-shipscope, after my OK) and have
   `sdlc` keep it in ~/.sdlc/env. Otherwise say in the plan that metric_watch stays manual in stage 2.
4. Rewrite docs/przebieg-na-sobie-s5.md as version 3:
   - prep is `sdlc up` + `sdlc attach dbqm45/sprintdeck` + the browser steps that remain (ShipScope GitHub App access
     to sprintdeck, Vercel check);
   - drop the tunnel, ~/.pdi.env, `claude mcp add -e` and the `faza` function, or say why each one stays;
   - steps 1–14 with the expected result and where to look, as in docs/przebieg-lokalny.md;
   - §6 known gaps updated;
   - an empty §7 journal.
   Keep the S5 change, its gates and the 30-day impact window. Note where the trial run's shortcuts (`review_by` tomorrow,
   `min_days: 0`) must not be used.
5. Docs: the README `sdlc` section (`attach`), plan-sdlc-lokalnie.md §6 and §9 (stage 2 state).

Tests (tests/test_stack.py, injected runner, HTTP client and home dir; no real gh, git, network or processes):
- the clone and pull calls, and reuse of an existing clone;
- the ShipScope track call with the flags source;
- PDI_DISPATCH_CHECKOUT and `[deploy] repo` written without touching other values;
- switching from the trial repo to sprintdeck;
- `sandbox` still passes its tests through the shared code;
- `deploy` refused on a Vercel repo without `--force`;
- no secret in argv, logs or output;
- a second run changes nothing.

Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src. GitHub
Actions do not run on this account right now: run the gates locally and say so in the PR. At the end, run
`sdlc attach dbqm45/sprintdeck` with me and walk S5 version 3 through step 3 (triage → CHG-1 dispatched). The rest I
run myself, filling the §7 journal. Commit, PR and any ShipScope or sprintdeck change on my request.
```

## Etap 3 — pdi (+ ShipScope, tf): z localhosta na produkcję

Start dopiero po etapie 2 (wypełniony dziennik S5 v3, luki zapisane w pdi). Sesja w klonie pdi; zmiany w ShipScope,
tf i sprintdecku osobnymi PR-ami, po Twojej zgodzie. Etap zależy od dwóch rzeczy spoza kodu: płatności GitHub
Actions (na produkcji fazy idą przez Actions, R4) i decyzji DA4 (stack usługi pdi), dlatego najpierw sprawdza warunki
i zbiera decyzje, a kod pisze dopiero według zatwierdzonego planu.

```text
Implement stage 3 of docs/plan-sdlc-lokalnie.md: §7 "Na produkcji" — the same flow as stage 2 (S5 on
dbqm45/sprintdeck, docs/przebieg-na-sobie-s5.md version 3), but with hosted services instead of localhost and tf
phases in GitHub Actions instead of PDI_DISPATCH=local. Answer me in Polish; code, commits and PR titles in English,
Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 2 is done: S5 version 3 has a filled §7 journal and its gaps are recorded in pdi (`record_problem`, channel
  dogfooding). Ask me for the journal link;
- GitHub Actions run on this account: `gh run list -R dbqm45/sprintdeck -L 3` shows jobs with steps (not 0-step
  billing failures). If not, stop: production phases need Actions (R4, DL1).

Goal: no process of the flow runs on my Mac. A report entered in the hosted pdi form goes through the phases with
gates (phases in sprintdeck's Actions, `sdlc-phase.yml`), ci_for_sdlc readiness, delivery, Vercel deployments, flag
stages and the impact review, with the production ShipScope and a hosted pdi. Secrets live only in the hosting
platforms and in GitHub repo secrets; nobody copies them by hand between services, as in L4.

Today:
- Plan §7 maps local to production:
  - localhost → domains (ShipScope on Render, pdi per DA4);
  - ShipScope local mode (L1) → off by itself, because PUBLIC_BASE_URL is not localhost;
  - PDI_DISPATCH=local → Actions (`sdlc-phase.yml`);
  - `sdlc deploy` → the real pipeline (on sprintdeck, Vercel from stage 2).
  Variable names and contracts do not change.
- DA4 (docs/plan-automatyzacja-i-konsola.md) is open: recommendation TypeScript + Fastify + Postgres for the pdi
  service, with the MCP server staying in Python. Today pdi is a Python CLI + receiver (src/pdi/receiver.py) +
  MCP server over a file registry (PDI_REGISTRY_PATH); plan-f4-pdi.md says "orkiestrator najpierw jako CLI".
- Plan §6 lists what local runs never tested: Actions phases, GitHub webhooks to ShipScope, URL and signature checks
  on public addresses. These are the stage's risks.
- `sdlc up` keeps everything in ~/.sdlc/env and connects ShipScope to pdi through local-pdi.js. In production,
  Connect runs in ShipScope's UI and shows the three PDI_SHIPSCOPE_* values once.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md:
   a. How pdi is hosted for stage 3: the current Python receiver + registry as a service (smallest step; where;
      where the registry lives and how it is backed up) versus starting the DA4 service now. Recommend one and say
      what the other costs later.
   b. Where pdi-impact-review, pdi-forecast and metric_watch run on a schedule (Actions cron in which repo, or the
      host's scheduler).
   c. How the PDI_SHIPSCOPE_* values from Connect reach pdi's hosting without being copied by hand (e.g. a one-time
      `sdlc` step that reads them and writes them through the platform's CLI or API from stdin, never argv). If no
      such path exists, say so and propose the least manual one.
   d. The budget for production phases (DL5 was 3 USD per phase on the trial repo).
2. Then a plan in docs/ (plan-etap3-produkcja.md): services and their domains, each variable from ~/.sdlc/env and where
   it goes (platform env, GitHub secret, nowhere), the order of the switch, how to roll back to the local stack, tests,
   open questions. Wait for my OK on the plan.
3. Implement only what the plan approves, TDD for the pdi part (red test first). Likely pieces, each its own PR:
   - pdi: deployable receiver (config from env only, health endpoint, public-address checks on, no local-mode
     shortcuts) and, if 1c allows it, a `sdlc` command that pushes the env to the hosting and to GitHub secrets
     without printing or passing secrets in argv;
   - sprintdeck: `sdlc-phase.yml` and change-check enabled with repo secrets and variables (tf's files, not edited by
     hand);
   - ShipScope or tf: only if the plan finds a gap, as a separate PR in its repo after my OK.
4. Docs: docs/przebieg-na-sobie-s5.md version 4 (production run: prep, steps 1–14, gaps, empty journal), the README
   (production section), plan-sdlc-lokalnie.md §7 and §9 (stage 3 state).

Tests (pdi, injected runner, HTTP client and env; no real network, platforms or GitHub):
- the receiver refuses to start in production without required variables and names only the missing names;
- local-mode shortcuts (loopback, PDI_DISPATCH=local) are off when the public URL is not localhost;
- the env push sends secrets via stdin or API body, never argv, logs or output;
- a second push changes nothing.

Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src, plus the
Actions checks once they run. At the end, walk S5 version 4 with me through step 3 (triage → phase intent started in
sprintdeck's Actions). The rest I run myself. Commit, PRs, platform changes and any secret setting on my request.
```

## Etap 4 — pdi: usługa (DA4) i konsola, krok K-2

Start dopiero po etapie 3 (hostowany pdi prowadzi S5 v4). Źródło: [plan automatyzacji i konsoli](plan-automatyzacja-i-konsola.md)
§5.3 (K-2–K-4), decyzje DA3–DA5 i makieta w `design/konsola/`. Etap obejmuje tylko K-2: skrzynkę i oś zdarzeń
w prawdziwym interfejsie, z decyzją podejmowaną przyciskiem. K-3 (rozmowa w konsoli) i K-4 (graf śladu i panel
w Jirze) to kolejne etapy; plan każe budować K-3 dopiero wtedy, gdy K-1 pokaże, że rozmowa jest głównym sposobem
pracy. Sesja w klonie pdi; usługa i konsola powstają w pdi (DA3), a osobne repo tylko po Twojej zgodzie.

```text
Implement stage 4: the pdi service (DA4) and the console step K-2 (inbox and event timeline in a real UI) from
docs/plan-automatyzacja-i-konsola.md §5.3, after stage 3 (production, docs/plan-sdlc-lokalnie.md §7). Answer me in
Polish; code, commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 3 is done: hosted pdi runs S5 version 4 on sprintdeck, and docs/decyzje.md records how pdi is hosted (stage 3
  decision 1a: Python receiver + file registry, or the DA4 service already started);
- docs/decyzje.md and the plan's §2 table: DA3 (console lives in pdi), DA4 (stack), DA5 (no approval by chat text).

Goal: I open the console's domain, sign in with GitHub, and see:
- "Czeka na Ciebie": the same inbox items `list_inbox` returns;
- "Teraz": the live event timeline from the receiver (problem.recorded, gate.decided, readiness.changed,
  release.stage_changed, feature.released, phase runs and their cost);
- per item: approve, reject or request changes with a button, with the same fields and validation as
  `decide_inbox_item`.
A decision made in the console is visible to the MCP `pdi` server at once, and the reverse. Nothing in the console
approves by text alone (DA5).

Today:
- pdi is Python: CLI, receiver (src/pdi/receiver.py), MCP server, file registry under PDI_REGISTRY_PATH, contract
  0.5.0+ (src/pdi/contract.py), inbox and trace on the data side ("skrzynka i graf śladu są w pdi po stronie danych;
  brakuje interfejsu", plan §8 row K-2).
- DA4 recommends TypeScript + Fastify + Postgres with ShipScope's patterns (GitHub App login, multi-tenant with RLS,
  token encryption), with the MCP server staying in Python. DA4 is open.
- The console mockup is in design/konsola/ (Main, Slad, Decyzje, Autonomia; preview link in its README). K-2 covers
  only the inbox and the "Teraz" timeline from Main; Slad (K-4), the chat panel (K-3), Decyzje and Autonomia come later.
- Local dev must keep working: `sdlc up` starts the stack on localhost (L4), and S5 versions 3 and 4 must still pass.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plan's §2 table:
   a. DA4 itself, given what stage 3 chose: build the TS service now, or put the console on the Python service first.
      Compare the cost of each for K-2 and for K-3/K-4, and where tenancy and login come from.
   b. One source of truth: the registry moves to Postgres (migration of existing files, and how the Python MCP server
      and CLI read it) or stays in files behind one API. No two writers to one record.
   c. Live timeline: SSE, polling or websockets, with the hosting from stage 3.
   d. Where the code lives (DA3 says pdi; a monorepo folder such as service/ and console/, or a separate repo).
2. Then a plan in docs/ (plan-etap4-konsola.md): the API (inbox list, item, decide, events stream), auth and roles,
   data migration and rollback, how `sdlc up` starts the service locally, the K-2 screens from the mockup with every
   state (empty, loading, error, stale item, already decided elsewhere), tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs:
   - the service and its API, contract-validated against src/pdi/contract.py's schemas (generate or share them, do
     not copy by hand);
   - the data migration, idempotent, with a dry run;
   - the console K-2 screens;
   - `sdlc up`, `sdlc status` and the MCP server switched to the service;
   - the production deploy per stage 3, after my OK.
4. Docs: README, design/konsola/README.md (which screens are live), plan-automatyzacja-i-konsola.md §8 (K-2 state),
   docs/przebieg-na-sobie-s5.md (decisions may now be made in the console).

Tests:
- the API: decide with the same validation and errors as `decide_inbox_item`; a second decide on a decided item is
  refused with a clear message; no approval without an explicit action (DA5);
- tenancy: one tenant never sees another's items (RLS or equivalent), unauthenticated calls refused;
- the migration: every existing record readable after it, a second run changes nothing;
- the MCP server and the console see each other's decisions;
- console: the screens' states, keyboard use and accessible names (WCAG AA), e2e for list → decide → timeline entry;
- no secret or token in logs, URLs or client bundles.

Gates: the existing Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the new service's
lint, typecheck and tests, and the e2e suite, all in Actions (working since stage 3). At the end, decide one inbox
item in the console with me and show it in `list_inbox` and in the timeline. Commit, PRs, migration on real data,
production deploy and any new repo on my request.
```

## Etap 5 — pdi: graf śladu, rejestr decyzji i panel w Jirze (K-4)

Start dopiero po etapie 4 (skrzynka i oś zdarzeń działają w konsoli na produkcji). Źródło: [plan automatyzacji
i konsoli](plan-automatyzacja-i-konsola.md) §5.3 (K-4), [plan G1/G2](plan-g1-g2.md) (G2.5) i decyzje DG3, DG7.
Część A to widok śladu zmiany („Ślad”) i rejestr decyzji („Decyzje”) w konsoli. Część B to panel w Jirze, który
korzysta z tej samej skrzynki i powstaje tylko wtedy, gdy działa tryb SaaS ci_for_sdlc. K-3 (rozmowa w konsoli) jest
poza etapem, bo plan każe ją budować dopiero wtedy, gdy K-1 pokaże, że rozmowa jest głównym sposobem pracy. Ekran
„Autonomia” też, bo nie ma jeszcze danych o zatwierdzeniach. Sesja w klonie pdi. Panel w Jirze to jedna aplikacja
Atlassian Forge dla ekosystemu (DG7), więc nowe repo powstaje tylko po Twojej zgodzie.

```text
Implement stage 5: console step K-4 from docs/plan-automatyzacja-i-konsola.md §5.3 — the trace graph as a change
view, the decision registry, and the Jira panel (G2.5, docs/plan-g1-g2.md; DG7 in docs/decyzje.md) using the same
inbox — after stage 4 (console K-2). Answer me in Polish; code, commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 4 is done: the console serves "Czeka na Ciebie" and "Teraz" in production, decisions by button only (DA5),
  and docs/plan-etap4-konsola.md plus docs/decyzje.md record the service stack and the single source of truth;
- K-3 stays out: ask me whether K-1 usage showed chat is the main mode (plan §5.3: build K-3 only then). If I say
  yes, stop and tell me to start a K-3 stage instead;
- for part B only: ci_for_sdlc and ShipScope reachable publicly (ci_for_sdlc SaaS mode, docs/SAAS.md there). If not,
  do part A and say part B waits.

Goal:
A. In the console, for any change (CHG-n) or problem (PRB-n): the trace view from design/konsola/Slad.dc.html
   (report → problem → intent → plan → tasks → PRs → readiness → deployments → flag stages → impact review), each node
   with its source link and state, and the decision registry from Decyzje.dc.html (every decision with who, when,
   evidence and the item it decided). Both read pdi's existing trace and decision data; nothing is recomputed in the
   browser.
B. A Jira issue panel (Forge) showing that issue's trace summary and its open inbox items, deciding with the same
   button and validation as the console, and linking to the console. One panel for the ecosystem (DG7); the
   ci_for_sdlc readiness and ShipScope release parts come from their own APIs, with logic staying in those services.

Today:
- pdi holds the trace graph and the decision registry on the data side (contract 0.5.0+, src/pdi/contract.py);
  the console (stage 4) shows only the inbox and the timeline.
- design/konsola/ has the mockups (Slad, Decyzje; Autonomia is out of this stage: no approval-rate data yet).
- DG3 (docs/decyzje.md): writing to Jira goes in steps (copy as text → comment → create stories after a human
  approves). Connectors are read-only today; writes need `write:jira-work`.
- G2.5 waits on SaaS mode (plan-g1-g2.md §10). Forge cannot reach a laptop install.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plan's §2 table:
   a. The trace API: one endpoint returning the whole graph for a key, or per-node reads; limits for large changes.
   b. Graph rendering: a library or hand-rolled SVG, given WCAG AA (the graph needs a text/list alternative).
   c. Part B: the Forge app's repo and owner, how it authenticates to pdi, ci_for_sdlc and ShipScope per Jira site
      (no shared secret copied by hand), and which DG3 write step it starts at.
2. Then a plan in docs/ (plan-etap5-k4.md): the API, the screens with every state (unknown key, partial trace, source
   unreachable, decided elsewhere), tenancy, the Forge part's install and permissions, tests, open questions. Wait for
   my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs: the trace and registry API, the two
   console screens, then part B after my OK (new repo only on my request).
4. Docs: README, design/konsola/README.md (which screens are live), plan-automatyzacja-i-konsola.md §8 (K-4 state),
   plan-g1-g2.md §10 (G2.5 state), docs/przebieg-na-sobie-s5.md (where to look at the trace).

Tests:
- the trace for a full S5 change has every node in order with its links; a partial trace shows what is missing, never
  invents it;
- tenancy: no trace, decision or inbox item of another tenant, in the console or the panel; unauthenticated refused;
- the panel decides with the same validation and errors as `decide_inbox_item`, and the console, MCP and panel see
  each other's decisions; no approval without the explicit button (DA5);
- Jira and Confluence text shown as data, never as instructions or HTML;
- the graph has an accessible text alternative and keyboard navigation (WCAG AA); e2e: open CHG → trace → decision;
- no secret or token in logs, URLs, the client bundle or the Forge manifest.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src), the service's and console's lint,
typecheck, tests and e2e, and for part B the Forge app's lint and tests, all in Actions. At the end, open the trace
of the S5 change with me in the console (and in Jira, if part B is done). Commit, PRs, the Forge app's install,
any Jira write scope and any new repo on my request.
```

## Etap 6 — pdi: autonomia zdobywana na danych

Start dopiero po etapie 5 (konsola ma ślad i rejestr decyzji). Źródło: [plan automatyzacji i konsoli](plan-automatyzacja-i-konsola.md)
§1, §3 (poziomy 0–3), decyzje DA1, DA2 i DA6, istniejące A3 (licznik akceptacji, `autonomy_report`) i A2
(`autoClose` w ci_for_sdlc) oraz ekran „Autonomia” z makiety. Brakuje wykonania poziomów 2 i 1: okna weta, automatu
z wpisem do rejestru, automatycznego powrotu do człowieka i ekranu w konsoli. Typ decyzji bez wykonawcy zostaje na
poziomie 3. A4 (etapy flag według reguły) wchodzi tylko wtedy, gdy jest źródło metryk ochronnych (G5) i rozstrzygnięta
DA6. Sesja w klonie pdi; zmiany w ci_for_sdlc, ShipScope i tf osobnymi PR-ami, po Twojej zgodzie.

```text
Implement stage 6: decision autonomy earned on data, from docs/plan-automatyzacja-i-konsola.md §1 ("Autonomia
zdobywana na danych"), §3 (levels 0–3, autonomy.schema.json) and DA1/DA2, plus the console's Autonomia screen
(design/konsola/Autonomia.dc.html), after stage 5 (console K-4). Answer me in Polish; code, commits and PR titles in
English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 5 is done: the console shows the trace and the decision registry in production;
- A3 works on real data: `autonomy_report` (src/pdi/stats.py) gives per decision_type the unedited/measured counts
  from the registry. Show me the current report; if no type has 30 measured decisions, say so (nothing can be lowered
  yet, but the mechanism can still be built and tested);
- docs/decyzje.md for DA2 (≥ 95% unedited in the last 30 of a type, lowering always a human decision) and DA6 (who
  changes a flag stage).

Goal: I open "Autonomia" in the console and see, per decision_type, its level, the measured acceptance, the DA2
threshold and the history of level changes. When a type crosses the threshold, a level-change proposal lands in my
inbox; I approve it with a button. From then on:
- level 2: the decision appears in the inbox with a veto deadline and is applied by its executor when the window ends,
  unless I stop it (`decision.vetoed`);
- level 1: applied at once, recorded in the registry and the "Teraz" timeline (`decision.auto_applied`);
- when the share of my edits or vetoes on a type rises above `raise_when`, the type goes back to level 3 by itself
  and I am told why.
Types listed as never below 3 (triage, scope.r1, release.go, outcome.assessment, review.sensitive, migration) cannot
be lowered by any path, including a hand-edited policy.

Today:
- Contract 0.5.0+ has `autonomy.schema.json` (level, veto_window, rule, lower_when, raise_when) and the decision's
  `automation` (`level`, `rule`, `veto_until`, `vetoed_by`) and `draft_edited`; check what the current contract
  version in src/pdi/contract.py carries and what is still unused.
- A3 (plan-a3-licznik-akceptacji.md): the counter and the lowering proposal as an inbox decision exist; nothing
  executes level 2 or 1 yet.
- A2 (ci_for_sdlc): `finding.auto_close` already has its own `autoClose: off | suggest | apply` policy there and
  sends `decision.recorded` to pdi. Two switches for one type must not disagree.
- Executors: only some types have one today. `flag.stage_advance` and `flag.removal_pr` (A4) wait on DA6 and on a
  guard-metrics source (gap G5); `review.light` (A7) and `dependency.update` are not built. A type without an executor
  stays at level 3 whatever its numbers say.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plan's §2 table:
   a. Where the policy lives and who may change it (pdi service, per tenant; a change only through an approved
      decision, audited), and how ci_for_sdlc's `autoClose` follows it (pdi as the source, ci_for_sdlc reads it).
   b. The veto timer: which process applies a level-2 decision at the deadline, what happens if it is down at that
      moment (late apply or back to the inbox), and the default window per type.
   c. `raise_when`: the measure (edits, vetoes, reverts) and window, and whether the return to level 3 is automatic
      (plan §7 says yes) or proposed.
   d. Which types this stage actually enables (only those with a working executor), and whether A4 is in: only if a
      guard-metrics source exists (G5) and DA6 is decided; otherwise `flag.stage_advance` stays at 3 and A4 is a
      later stage.
2. Then a plan in docs/ (plan-etap6-autonomia.md): the policy model and its API, the executor interface per type,
   the timer, the events, the Autonomia screen with every state (not enough data, below threshold, proposal pending,
   level 2 with a running window, returned to 3), tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs: the policy and its change-by-decision, the
   level-2 timer and veto, level-1 apply with the registry and timeline entries, the automatic return, the Autonomia
   screen, then the ci_for_sdlc `autoClose` link and any executor (separate PRs in their repos, after my OK).
4. Docs: README, design/konsola/README.md (Autonomia live), plan-automatyzacja-i-konsola.md §8 (state of the levels,
   A3, A4), docs/przebieg-na-sobie-s5.md (what may now happen without a click, and where it shows).

Tests:
- a type below 30 measured decisions or below 95% is never proposed for lowering; at 95% of the last 30 it is,
  once;
- no level change without an approved decision; a never-below-3 type refuses every path to a lower level;
- level 2: applied after the window, not applied after a veto, a veto after the deadline is refused clearly, a timer
  missed while down follows decision 1b, a second run never applies twice;
- level 1: applied once, recorded in the registry and the timeline;
- the automatic return to level 3 when `raise_when` is crossed, with the reason in the inbox;
- a type without an executor stays at 3; ci_for_sdlc's `autoClose` and pdi's policy cannot disagree;
- tenancy as in stages 4–5; the Autonomia screen's states, keyboard use and accessible names (WCAG AA); no secret in
  logs, URLs or the client bundle.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
lint, typecheck, tests and e2e, all in Actions. At the end, show me the Autonomia screen with the real report and walk
one level-2 decision in a test tenant with me: the inbox entry with its deadline, a veto, then one applied after the
window. Commit, PRs, any policy change on the real tenant and changes in other repos on my request.
```

## Etap 7 — pdi (+ ShipScope, tf): etapy flag według reguły (A4) i metryki ochronne (G5)

Start dopiero po etapie 6 (poziomy 2 i 1, okno weta i automatyczny powrót do człowieka działają). Źródło: [plan
automatyzacji i konsoli](plan-automatyzacja-i-konsola.md) (A4, DA6, ryzyko „etap flagi bez wiarygodnych metryk”),
[plan G1/G2](plan-g1-g2.md) (`release.stage_changed`, G1.5) i [plan jednego flow](plan-jeden-flow-sdlc.md) (G5 —
narzędzie analityki produktu, wybór właściciela). Jako punkt wyjścia dla G5 polecenie bierze to, co istnieje po S5:
zdarzenia w sprintdecku za flagą `analytics_events` (Supabase) i `metric_watch.py` w tf, i każe porównać je
z zewnętrznym narzędziem. Sesja w klonie pdi; zmiany w ShipScope, tf i sprintdecku osobnymi PR-ami, po Twojej zgodzie.
ShipScope nadal tylko obserwuje flagi (ADR-001, ADR-003). Etap zmienia wykonawca z DA6.

```text
Implement stage 7: A4 "flags by rule" from docs/plan-automatyzacja-i-konsola.md §4 (flag.stage_advance,
flag.removal_pr, rollback proposal at level 1) together with its blocker, gap G5 (a guard-metrics source;
docs/plan-jeden-flow-sdlc.md), on the autonomy mechanism from stage 6. Answer me in Polish; code, commits and PR
titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 6 is done: levels 2 and 1, the veto timer, `decision.auto_applied`/`decision.vetoed` and the automatic return
  to level 3 work in production, and the Autonomia screen is live (docs/plan-etap6-autonomia.md);
- ShipScope sends `release.stage_changed` and `feature.released` to the hosted pdi (G1.5), and sprintdeck has a
  `release.yaml` with flag stages and `min_days` from the S5 change;
- docs/decyzje.md for DA6 (who changes a flag stage; ShipScope only observes) and ShipScope's ADR-001/ADR-003.

Goal: for a flag in a change's release.yaml:
- when its exit criteria are met (stage reached, `min_days` passed, guard metrics within limits), pdi gets a
  `decision.proposed` of type `flag.stage_advance` with the evidence (stage, days, each guard metric with its value,
  limit and window); at level 3 I approve it with a button, at level 2 it is applied after the veto window; the DA6
  executor changes the stage and ShipScope sees the new state on its own;
- when a guard metric crosses its limit during a stage, a rollback proposal comes at level 1 (applied at once,
  recorded, shown in "Teraz"), as the plan says;
- when a flag has been at 100% longer than X days, Talos (tf) opens a PR removing the flag from code
  (`flag.removal_pr`); merging it stays mine.
Nothing advances when a guard metric is missing, stale or unreadable: that is "criteria not met", with the reason.

Today:
- G5 waits on a tool choice by the owner (plan-jeden-flow-sdlc.md, kontekst-rozmowy.md). After S5, sprintdeck has
  product events behind the flag `analytics_events` in Supabase, scripts/metrics.sql and tf's metric_watch.py with a
  ShipScope service token; check what they measure and whether they can serve as guard metrics per flag stage.
- ShipScope knows each flag's state per service and environment, its freshness and the release plan's stages and
  `min_days` (`flagPlanStatus()`, `releasePlanModel()`); it never changes flags (ADR-001/ADR-003).
- The plan's risk table: without reliable guard metrics `flag.stage_advance` stays at level 3.
- Flag changes today: sprintdeck's flags live in config/flags.{env}.json (code), so a stage change is a PR to that
  file through tf, unless DA6 picks a provider adapter.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plans' tables:
   a. G5: the guard-metrics source. Compare the S5 setup (Supabase + metric_watch.py) with an external product
      analytics tool on cost, latency, per-flag-stage cohorts and who owns it; say which metrics are guards (errors,
      activation, key action) and how a limit and a window are declared per flag (release.yaml or elsewhere; contract
      change if so).
   b. DA6: the executor of a stage change for sprintdeck (PR to config/flags.{env}.json through tf, merged by whom;
      or a provider adapter), and for a rollback at level 1 (it must be fast: a PR that waits for review is not).
   c. Who detects "exit criteria met": ShipScope (it has flag state and the plan) emitting an event, or pdi from
      ShipScope's API; one detector only.
   d. The removal threshold X days and the flag types that are never removed automatically.
2. Then a plan in docs/ (plan-etap7-flagi.md): the guard-metrics source and its contract, the detector, the
   executors, the events and decisions with their evidence, how stage 6's levels apply (start at 3 for every flag
   type), the failure cases (metric missing or stale, executor fails, ShipScope state stale, two proposals for one
   flag), rollback, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the
   guard-metrics source, the detector, pdi's decisions and evidence, the stage executor, the rollback path, Talos's
   removal PR.
4. Docs: README, plan-automatyzacja-i-konsola.md §8 (A4), plan-jeden-flow-sdlc.md (G5 state),
   docs/przebieg-na-sobie-s5.md (the flag's stages now advance by rule; where to see why), ShipScope and tf docs for
   their parts.

Tests:
- criteria met only when every condition holds; a missing, stale or unreadable metric blocks with its reason;
- one proposal per flag and stage; a second detection does not duplicate it;
- level 3 needs my button, level 2 is applied after the window unless vetoed, both through the DA6 executor only;
- a guard breach proposes and applies a rollback once, recorded with its evidence;
- the removal PR opens once after X days at 100%, never for an excluded flag, and is never merged by the automation;
- ShipScope never writes a flag; an executor failure leaves the decision open with the error, never half-applied;
- tenancy as before; no secret or token in logs, URLs, events or PR bodies.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src), the service's and console's
checks, and each touched repo's own gates, all in Actions. At the end, walk with me one stage advance of the S5
flag on sprintdeck at level 3: the proposal with its evidence, my approval, the executor's change, ShipScope showing
the new stage. Commit, PRs, any flag change on production, the analytics tool's setup and changes in other repos
on my request.
```

## Etap 8 — pdi (+ tf, ci_for_sdlc): uproszczone review (A7) i lustro Jira ↔ repo (A8)

Start dopiero po etapie 7 (autonomia i jej wykonawcy działają, Actions od etapu 3). Źródło: [plan automatyzacji
i konsoli](plan-automatyzacja-i-konsola.md) (A7, A8, typ `review.light` z §3, lista wrażliwych obszarów), [plan
jednego flow](plan-jeden-flow-sdlc.md) (krok 10 „Review i merge”, D4: dla nowych zmian źródłem prawdy jest repo,
Jira najwyżej jako lustro), [plan G1/G2](plan-g1-g2.md) (DG3: zapis do Jiry etapami) i mechanizm autonomii
z etapu 6. Plan opisuje A8 w obie strony („i odwrotnie”), a D4 czyni źródłem repo, więc polecenie każe najpierw
rozstrzygnąć kierunek. Sesja w klonie pdi; zmiany w tf, ci_for_sdlc i sprintdecku osobnymi PR-ami, po Twojej zgodzie.
Merge kodu z auth, płatnościami, migracjami i IaC zawsze zostaje u człowieka (§1 planu).

```text
Implement stage 8: the last wave of docs/plan-automatyzacja-i-konsola.md — A7 "light review" (`review.light`) and
A8 "Jira ↔ repo mirror" — on the autonomy mechanism from stage 6. Answer me in Polish; code, commits and PR titles
in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 7 is done, and stage 6's levels, veto timer and executor interface work in production
  (docs/plan-etap6-autonomia.md);
- GitHub Actions run on sprintdeck and tf's AI review in CI (`REVIEW.md`, tf #86) runs on its PRs;
- docs/decyzje.md and the plans for: D4 (plan-jeden-flow-sdlc.md: for new changes the repo is the source of truth,
  Jira at most a mirror), DG3 (Jira writes in steps: copy as text → comment → create stories after a human approves),
  and plan §1 ("never automate value or the irreversible": merges touching auth, payments, migrations, IaC stay human).

Goal:
A7. A PR in a product repo is classified as `review.light` or `review.sensitive` by one rule: small change (tests,
    docs, small fixes), green CI, AI review without blocking findings, and no path on the repo's sensitive-paths list.
    A light PR becomes a `decision.proposed` of type `review.light` in pdi with the evidence (diff size, paths, CI run,
    AI review summary); at level 3 I approve it with a button and the executor merges; at a lower level stage 6's rules
    apply. A sensitive PR never enters this path: `review.sensitive` stays at level 3 for good, and so does any PR the
    classifier cannot judge.
A8. An approved change in the repo (intent, plan, tasks, release lines) is reflected on its Jira issues, and a Jira
    edit to a mirrored field is handled by the direction chosen in decision 1c, with the history kept on both sides.
    Writes start at the DG3 step decided in 1d and never happen without an approved decision.

Today:
- tf runs AI review in CI with REVIEW.md (tf #86); there is no `review.light` mode and no sensitive-paths list
  (plan §8 row A7). ci_for_sdlc reads PRs and readiness.
- The decision type `review.light` is in the contract's catalogue at level 3; `review.sensitive` and `migration`
  are in the never-below-3 list.
- Connectors to Jira are read-only today; writes need `write:jira-work` (DG3). ShipScope reads release lines from
  Jira or from release.yaml; ci_for_sdlc reads Jira for readiness. G2.5's Jira panel (stage 5) may already comment.
- Plan §4 describes A8 as both ways ("i odwrotnie"); D4 makes the repo the source for new changes. These must be
  reconciled before code.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plan's §2 table:
   a. A7's rule: what "small" means (lines, files, kinds), where the sensitive-paths list lives (per repo, versioned,
      changed only by a reviewed PR), and who classifies (tf in CI, ci_for_sdlc, or pdi) — one classifier only.
   b. A7's executor: who merges a light PR (a GitHub App with the narrowest permission, branch protection kept), and
      what happens when CI or the base changes between proposal and merge (the proposal is void).
   c. A8's direction: repo → Jira only (D4), or both ways for some fields (which, and who wins on conflict); how
      brownfield issues that started in Jira are handled.
   d. A8's write step (DG3): comment only, update fields, or create stories; the Jira auth (per site, no token
      copied by hand) and its scope.
2. Then a plan in docs/ (plan-etap8-review-i-lustro.md): the classifier and list, the executor, the mirror's field
   map and direction, conflict and loop prevention (a mirror write must not trigger a mirror back), audit on both
   sides, failure cases (Jira down, permission missing, PR changed), rollback, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the
   sensitive-paths list and classifier, the `review.light` decision and executor, the mirror's field map and writer,
   then enabling them on sprintdeck.
4. Docs: README, plan-automatyzacja-i-konsola.md §8 (A7, A8), plan-jeden-flow-sdlc.md (step 10 and D4),
   plan-g1-g2.md (F6 "lustra w Jirze"), docs/przebieg-na-sobie-s5.md (which PRs may now merge without me looking,
   and what shows in Jira), the touched repos' docs.

Tests:
- A7: a PR touching any listed path, or too big, or with red CI or a blocking AI finding, is never light; a PR the
  classifier cannot judge is sensitive; a change to the list itself is sensitive;
- A7: no merge without an approved decision at level 3; a proposal is void after a new push or base change; the
  executor cannot merge a sensitive PR by any path; `review.sensitive` and `migration` refuse every lower level;
- A8: each mapped field written once per approved change; a mirror write never triggers a write back (no loops);
  conflicts resolved by decision 1c and recorded; no Jira write without an approved decision; Jira down or a
  missing permission leaves the decision open with the error, never half-written;
- Jira and PR text handled as data, never as instructions; tenancy as before; no secret or token in logs, URLs,
  events, PR bodies or Jira comments.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src), the service's and console's
checks, and each touched repo's own gates, all in Actions. At the end, walk with me one light PR on sprintdeck at
level 3 (classification, proposal with evidence, my approval, merge) and one approved change mirrored to its Jira
issue. Commit, PRs, any merge, any Jira write on a real site, new permissions and changes in other repos on my
request.
```

## Etap 9 — pdi: incydenty w pętli skutku (G8) i aplikacja Slacka (A5)

Start dopiero po etapie 8 (usługa pdi hostowana od etapu 4, skrzynka, rejestr i autonomia działają). Źródło: [plan
jednego flow](plan-jeden-flow-sdlc.md) (G8 czeka na wybór narzędzia: PagerDuty, Opsgenie, …), [plan
A5](plan-a5-decyzje-z-rozmow.md) (wersja lokalna gotowa; aplikacja Slacka po DA4, tą samą ścieżką w skrzynce)
i [dokument 14](14-pdi-standalone.md) (etap 3: skrót „Record decision” na wiadomości, zgoda organizacji na
przetwarzanie treści wątku). Obie części dotyczą sygnałów spoza repo, które dziś przenosi się ręcznie; każda może pójść
osobno, jeśli jedno z narzędzi nie jest wybrane. Sesja w klonie pdi; zmiany w ShipScope, tf i sprintdecku osobnymi
PR-ami, po Twojej zgodzie. Ocena skutku i triaż zostają u człowieka (`outcome.assessment` i `triage` nigdy poniżej
poziomu 3).

```text
Implement stage 9: gap G8 (incidents in the outcome loop; docs/plan-jeden-flow-sdlc.md) and the Slack app for A5
(docs/plan-a5-decyzje-z-rozmow.md "Aplikacja Slacka dochodzi po DA4"; docs/14-pdi-standalone.md stage 3), both on the
hosted pdi service from stage 4. Answer me in Polish; code, commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 8 is done, and the pdi service, inbox, registry, timeline and autonomy run in production (stages 4–6);
- A5's local version works: `propose_decisions_from_conversation` and `/decisions-from` produce drafts with verbatim
  quotes checked against the text, each approved or rejected in the inbox (contract 0.10.0, `source.kind: meeting`);
- the S5 impact review (step 13 in docs/przebieg-na-sobie-s5.md) and how `outcome.assessment` is decided today.
Either part may go alone: if no incident tool is chosen, do part B and say A waits; if Slack is not allowed in the
workspace, do part A and say B waits.

Goal:
A. G8: an incident in the chosen tool that touches a released change (by service, time window after a deployment or
   flag stage, or an explicit link) shows up in pdi: as evidence on that change's trace and on its impact review
   (`outcome.assessment` stays a human decision at level 3), in the "Teraz" timeline, and, when it is new work, as a
   report that goes through triage like any other (A6 grouping applies). If stage 7's guard metrics exist, an open
   incident on a flag's service blocks its stage advance with that reason.
B. Slack: a "Record decision" message shortcut reads the thread, drafts `DEC-n` with verbatim quotes and a link to the
   thread through the same path as A5's local version, and puts it in the inbox; nothing is recorded without my
   button (DA5). Optionally, inbox items I can act on are announced in a chosen channel with a link to the console;
   decisions are never made by a Slack reply.

Today:
- G8 waits on a tool choice by the owner (PagerDuty, Opsgenie, …; plan-jeden-flow-sdlc.md, kontekst-rozmowy.md).
  pdi's impact review reads ShipScope's metrics and, after stage 7, guard metrics; incidents are not read anywhere.
- A5 works locally only: a thread is pasted or read by Claude's Slack connector, then drafts go to the inbox.
  docs/14-pdi-standalone.md lists for Slack: the app, a hosted pdi, and the organisation's consent to process thread
  content (and the model provider's terms).
- Thread and incident text is untrusted (plan risk: hidden instructions in Jira or Confluence text reaching the chat);
  approval is only by button.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plans' tables:
   a. G8's tool and how incidents reach pdi (its webhook to the pdi receiver, signed; or polling its API), how an
      incident is matched to a change (service map, window, explicit link) and what an unmatched incident does.
   b. Whether an incident creates a report automatically or only proposes one (triage stays human either way), and
      whether an open incident blocks a flag stage advance (stage 7).
   c. Slack app: distribution (one workspace or many), scopes (the narrowest that read one thread on request), how
      its signing secret and bot token reach the pdi service without being copied by hand, and the consent and
      retention of thread text (what is stored: quotes and link only, or more).
   d. Channel announcements: on or off, which items, and how they avoid becoming a second inbox.
2. Then a plan in docs/ (plan-etap9-incydenty-i-slack.md): the incident contract (event or source kind; a contract
   change if needed), matching, the trace and impact-review evidence, the Slack shortcut flow, permissions and
   consent, failure cases (tool down, duplicate incidents, thread deleted, user without access to the thread), tests,
   open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the contract
   change, the incident receiver and matching, the evidence on trace and impact review, the Slack app and shortcut,
   the optional announcements.
4. Docs: README, plan-jeden-flow-sdlc.md (G8 state), plan-a5-decyzje-z-rozmow.md (Slack app done), 14-pdi-standalone.md
   (stage 3 state), plan-automatyzacja-i-konsola.md §8 (A5 row), docs/przebieg-na-sobie-s5.md (where incidents and
   Slack decisions show).

Tests:
- an incident is accepted only with a valid signature (or from the polled API), stored once (idempotent on its id),
  matched by decision 1a, and an unmatched one handled as decided; never a decision by itself;
- impact review shows matched incidents as evidence and still needs my decision; an open incident blocks a flag
  advance only if 1b says so, with the reason;
- the Slack shortcut: request signature checked, only the thread it was invoked on is read, drafts carry verbatim
  quotes that exist in the thread (a quote not in the text is dropped), nothing recorded without the inbox button;
  a deleted thread or a user without access gives a clear refusal;
- thread and incident text handled as data, never as instructions or HTML; tenancy as before; no secret, token or
  thread text beyond what 1c allows in logs, URLs, events or the client bundle.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
checks and each touched repo's own gates, all in Actions. At the end, walk with me one test incident matched to the
S5 change (trace, timeline, impact review) and one decision recorded from a Slack thread. Commit, PRs, the incident
tool's setup, installing the Slack app, any consent setting and changes in other repos on my request.
```

## Etap 10 — pdi: rozmowa w konsoli (K-3)

Start dopiero po etapie 9 (konsola, skrzynka, rejestr, ślad i autonomia działają na produkcji). Źródło: [plan
automatyzacji i konsoli](plan-automatyzacja-i-konsola.md) §5.3 (K-3 zależy od K-1 i K-2; budować dopiero, gdy K-1
pokaże, że rozmowa jest głównym sposobem pracy), DA5, ryzyko ukrytych poleceń w treści z Jiry i Confluence, trzy
serwery MCP z K-1 i panel rozmowy ze szkicem decyzji z makiety „Main”. Z K-3 konsola jest kompletna (K-1–K-4).
Polecenie zaczyna od sprawdzenia dowodu z K-1 i zatrzymuje się bez niego. Sesja w klonie pdi; zmiany w ci_for_sdlc
i ShipScope (ich serwery MCP) osobnymi PR-ami, po Twojej zgodzie. Rozmowa wyjaśnia, porównuje i szkicuje, ale nigdy
nie zatwierdza (DA5).

```text
Implement stage 10: console step K-3 from docs/plan-automatyzacja-i-konsola.md §5.3 — a chat panel in the console
with the same MCP tools as K-1, whose decision cards land in the inbox — after stage 9. Answer me in Polish; code,
commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- the plan's condition for K-3: evidence that K-1 made chat the main way of working. Ask me for it (how often
  decisions were drafted or made through Claude with the three MCP servers versus the console and Jira since stage
  4; the registry's `source.kind`/`drafted_by` can show part of it). If the answer is no, stop and say so;
- stages 4–9 run in production: console (inbox, timeline, trace, registry, Autonomia), decisions by button only (DA5);
- the three K-1 servers: pdi's MCP server (Python), ci_for_sdlc `packages/mcp` and ShipScope `adapters/mcp`, both
  read-only (`SHIPSCOPE_TOKEN` `shps_…`, `CI_SDLC_TOKEN`).

Goal: next to the inbox, a chat panel (as in design/konsola/Main.dc.html) where I ask about my work ("co blokuje
CHG-7?", "co się stanie, jeśli przesuniemy PAY-142 do R2?") and get answers with links to their sources, using the
same tools as K-1, scoped to my tenant and my permissions. When I ask for a decision or a change, the chat produces a
decision card (draft with recommendation, evidence, consequences) that lands in the inbox as `decision.proposed`
with `drafted_by` set and `source.kind: console`; I approve, edit or reject it there with a button. The chat has no
tool that approves, decides, merges, writes to Jira or changes a flag or an autonomy level.

Today:
- K-1 runs locally as stdio servers in Claude Code and Claude Desktop; the console (stages 4–9) has no chat.
- The plan's risks: text from Jira, Confluence, Slack threads, incidents and PRs may hide instructions; tools of the
  chat must not have approval rights (plan §7). A5 already checks that quotes exist verbatim in the source text.
- The contract has `drafted_by`, `draft_edited` and `source.kind: console` (stage 6's acceptance counter reads them,
  so chat drafts count toward autonomy like any other).
- No model, budget or data-retention rule exists for a hosted chat; check the current Claude models and pricing in
  the docs, not from memory.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plan's §2 table:
   a. How the console reaches the tools: the three MCP servers run as remote (HTTP) servers next to the service, or
      the service calls the same APIs directly; one tool definition per capability, shared with K-1, not copied.
   b. The model and its call path (Claude API from the pdi service, with tool use), the per-tenant budget and limits,
      and where the API key lives (the hosting's secrets, never in the browser).
   c. What is stored: conversation text, tool results, for how long, who can read it; and whether the model provider
      may see Jira/Confluence/Slack text (the organisation's consent, as in stage 9).
   d. The tool set: read tools only plus one "draft decision" tool that writes to the inbox as a proposal; anything
      else out.
2. Then a plan in docs/ (plan-etap10-rozmowa.md): the architecture, the tool set and its permissions per user, the
   card flow into the inbox, prompt-injection defences (source text as data, tool results labelled, no approval
   tool), the panel's states (thinking, tool running, source unreachable, budget reached, card created), cost
   tracking per tenant, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs: the remote tools (or the shared tool
   layer), the chat endpoint with streaming, the draft-decision tool, the panel, budget and limits, then the
   production deploy after my OK. Changes to ci_for_sdlc or ShipScope MCP servers in their repos after my OK.
4. Docs: README, design/konsola/README.md (chat live), plan-automatyzacja-i-konsola.md §8 (K-3 state),
   docs/przebieg-na-sobie-s5.md (asking and drafting in the console).

Tests:
- the chat's tool list has no approving or writing tool except "draft decision"; a request to approve, merge, write to
  Jira or change a flag gets a card or a refusal, never the action;
- a card lands in the inbox as a proposal with `drafted_by` and `source.kind: console`, and only my button decides;
  edits are recorded as `draft_edited` so stage 6 counts them;
- injected instructions in Jira, Confluence, Slack, incident or PR text (fixtures) do not change what tools are called
  or produce a decision; quotes in a card exist verbatim in their source;
- tenancy: the chat only sees the signed-in user's tenant and what that user may see; unauthenticated refused;
- budget: a tenant over its limit is refused clearly; costs recorded per tenant; no API key, token or secret in logs,
  URLs, the client bundle or the conversation;
- the panel's states, keyboard use and accessible names (WCAG AA); e2e: question → answer with sources → card →
  approve in the inbox → entry in the registry.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
lint, typecheck, tests and e2e, and the touched repos' own gates, all in Actions. At the end, with me: ask the chat
what blocks the S5 change, then have it draft one decision and approve it in the inbox. Commit, PRs, the model's API
key setup, production deploy and changes in other repos on my request.
```

## Etap 11 — ci_for_sdlc (+ pdi, sprintdeck): zaległe kroki G1/G2 (G2.3, G1.6, G2.6)

Start dopiero po etapie 10. Źródło: [plan G1/G2](plan-g1-g2.md) §10 i decyzje D-G23, DG3, DG7, D-E1. Wszystkie trzy
kroki są w planie warunkowe: G2.3 wstrzymała D-G23 do rozstrzygnięcia po pilocie reguł G2.2 i G1.2, G1.6 jest
„warunkowo, po pilocie”, a G2.6 czeka na MVP pokoi z importem z Jiry (D-E1 zmieniła rolę sprintdecka na konsensus co do
zrozumienia i ryzyka). Polecenie najpierw zbiera wynik pilota i rozstrzyga, które kroki wracają, i uwzględnia, co
zmieniły etapy 5, 8 i 10 (panel w Jirze, lustro, rozmowa w konsoli mogą częściowo zastąpić G2.3). Sesja w klonie pdi
(plan, decyzje, kontrakt); kod G2.3 w ci_for_sdlc, G1.6 w konsoli pdi, G2.6 w sprintdecku i ci_for_sdlc, każdy
osobnym PR-em w swoim repo, po Twojej zgodzie. Propozycja AI nigdy nie zmienia gotowości bez człowieka.

```text
Implement stage 11: the remaining steps of docs/plan-g1-g2.md — G2.3 (AI proposals: story split and AC rewrite),
G1.6 (story-map editor) and G2.6 (estimation signal from a sprintdeck room) — after stage 10. Each is conditional in
the plan; decide which come back before any code. Answer me in Polish; code, commits and PR titles in English,
Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 10 is done (or stopped at its K-1 check, which is fine), and stages 5 and 8 state what exists: the Jira panel
  (G2.5) and the Jira ↔ repo mirror with its DG3 write step;
- the pilot of rules G2.2 and G1.2 on a real backlog (plan-g1-g2.md §4.8, §5.9, §11 point 2). Ask me for its result:
  whether POs asked for a ready split, and the share of stories fixed after the rules' questions. Without a pilot
  result, stop: D-G23 and G1.6 depend on it;
- docs/decyzje.md: D-G23 (G2.3 on hold until the pilot; comes back if POs ask for a split or few stories get fixed
  after questions, dropped if POs fix them themselves), DG3, DG7, D-E1 (sprintdeck's role: consensus on understanding
  and risk, not effort; people vote only when the automation flags doubt).

Goal: for each of the three steps, a recorded decision (back, dropped, or replaced by something already built), and
for those that come back, the step done as the plan describes, adjusted to what stages 4–10 built:
- G2.3 (ci_for_sdlc): a separate "story shape reviewer" AI call with a proposal schema (`split` or `rewrite_ac`),
  proposals without a quote dropped, a "Proponowany podział" card with "Kopiuj jako tekst Jiry" and "Zatwierdź",
  approval recorded as a decision in pdi; a proposal never changes readiness without a human. If the console chat
  (stage 10) or the Jira panel (stage 5) already gives POs a split on request, say whether G2.3 is still needed.
- G1.6 (pdi console): a story-map editor for release lines, only if the pilot shows teams need a visual map; it
  edits the same source as today (release.yaml in repo mode, Jira lines otherwise; through the stage 8 mirror),
  never a second copy.
- G2.6 (sprintdeck + ci_for_sdlc): a room shows the story's shape state before voting; a "dwa obozy" or "szeroki
  rozrzut" result offers "Zgłoś niejasność", which creates a question in ci_for_sdlc with a new finding origin `team`
  (next to `rule`, `ai`, `drift`). Per D-E1 this uses the understanding and risk decks, not effort points.

Today:
- plan-g1-g2.md §10: G2.3 on hold (#62, ci_for_sdlc docs/BACKLOG-DEFERRED.md), G1.6 conditional, G2.6 waiting:
  sprintdeck has rooms, the "Risk" deck (S6) and limits (S3) (#4–#11), but no import from Jira.
- The contract has fixtures for story shape (`pdi/contract/fixtures/story-shape`); a new finding origin or proposal
  kind may need a contract change.
- After stages 5, 8 and 10: a Jira panel, a repo → Jira mirror and a console chat that drafts decisions exist (check
  which are live).

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md (D-G23 updated) and plan-g1-g2.md §10:
   a. G2.3: back or dropped, from the pilot result and the D-G23 rule; if back, whether it lives in ci_for_sdlc as
      planned or as a tool of the console chat; the model, cost per call and the noise limit.
   b. G1.6: build or drop, from the pilot; if built, where (console) and how it writes (the one source per mode).
   c. G2.6: whether sprintdeck's Jira import is in this stage or a precondition; the exact vote patterns that offer
      "Zgłoś niejasność"; the `team` origin in the contract.
2. Then a plan in docs/ (plan-etap11-g1-g2.md) for the steps that come back: changes per repo, contract changes,
   screens and their states, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK.
4. Docs: plan-g1-g2.md (§10 and header status), docs/decyzje.md, the touched repos' README/ROADMAP/BACKLOG-DEFERRED,
   docs/przebieg-na-sobie-s5.md if the flow changes.

Tests (for the steps that come back):
- G2.3: a proposal without a quote that exists in the story is dropped; proposals never change readiness; approval
  creates one decision in pdi; the AI contract test pins the schema; Jira text handled as data, never instructions;
- G1.6: editing a line writes to the one source for the mode and nowhere else; a conflicting edit from the other side
  is refused clearly; keyboard use and accessible names (WCAG AA);
- G2.6: only the agreed vote patterns offer the button; one question per room and story; the finding carries origin
  `team` and a link to the room; no vote data beyond what the plan allows leaves sprintdeck;
- tenancy as before; no secret or token in logs, URLs or client bundles.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) and each touched repo's own gates,
all in Actions. At the end, show me each recorded decision, and for each step that came back walk it once with me on
a real story. Commit, PRs, contract changes and changes in other repos on my request.
```

## Etap 12 — pdi: jedno wejście dla ludzi (G6, P1) i miary przepływu (G7)

Start dopiero po etapie 11 (konsola ma skrzynkę, oś zdarzeń, ślad, decyzje, autonomię i rozmowę). Źródło: [plan
jednego flow](plan-jeden-flow-sdlc.md) (G6, G7, P1 i P2 do decyzji właściciela), [dokument 15](15-jedna-platforma.md)
z makietą `design/platforma/` (menu według pytań, konsola pdi jako powłoka czytająca istniejące API, łączenie
backendu moduł po module, tf zawsze osobno; kolejność w §6) i istniejące miary: API usług ShipScope (`/metrics`,
`/flow`), kalibracja prognozy G3 i `control_band.py` w tf. G6, G7 i P1 to decyzje architektoniczne, więc etap
zaczyna się od decyzji na piśmie, a kod obejmuje tylko kroki 1–4 z §6 dokumentu 15 (powłoka z ekranami tylko do
odczytu); łączenie backendów zostaje na później. Sesja w klonie pdi; zmiany w ShipScope, ci_for_sdlc i tf osobnymi
PR-ami, po Twojej zgodzie. Silniki zostają osobno: ShipScope i ci_for_sdlc działają też bez platformy, tf zawsze
w repo klienta.

```text
Implement stage 12: gaps G6 (one entry point for people) and G7 (flow measures) from docs/plan-jeden-flow-sdlc.md,
with P1 (one platform), following the proposal in docs/15-jedna-platforma.md (mockup: design/platforma/), after
stage 11. Decisions on paper first; code only for its §6 steps 1–4 (decision, ADR check, contract, read-only shell).
Answer me in Polish; code, commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 11 is done, and the console from stages 4–10 runs in production (inbox, timeline, trace, decisions, Autonomia,
  chat if built);
- docs/15-jedna-platforma.md and design/platforma/ (README and preview link): the layers table (§1), the menu by
  questions (§2: Now, Problems, Work, Product, Releases, Consistency, Outcomes, Decisions, Autonomy), the order (§6)
  and the open questions (§7);
- the measures that exist today: ShipScope's service API `GET /api/service/v1/metrics` (PROD per day: deployments,
  failed, rollbacks, median lead time Done → PROD) and `GET /api/service/v1/flow` (first commit → first PROD, G3
  step 1), pdi's forecast calibration (G3 step 2), tf's control_band.py, stage 6's acceptance counter and stage 9's
  incidents if built.

Goal:
- one product for people: one sign-in and workspace, one menu by questions, the console as the shell; each section
  reads the existing APIs (pdi, ci_for_sdlc, ShipScope's service API) read-only, with links into the engines where
  an action lives there; ShipScope and ci_for_sdlc keep working on their own;
- G7: one agreed set of flow measures in "Outcomes" (e.g. lead time report → PROD and intent → PROD, deployment
  frequency, change failure rate, time to restore, forecast accuracy, share of decisions made by automation), each
  with its definition, source, and the period it covers, computed in one place, not per screen.

Today:
- people use four apps with separate sign-ins (doc 15 intro); the console from stage 4 already signs in with GitHub;
- G6, G7, P1 and P2 (Jira or repo) are open owner decisions (plan-jeden-flow-sdlc.md "Do decyzji właściciela");
  doc 15 is a proposal, not a decision;
- doc 15 §6 step 2 is an ADR-004 in ShipScope (flag state written by executors, ShipScope as dashboard); stage 7's DA6
  may already have settled it — check before writing anything;
- the "Product" section needs a feature catalogue in the contract (doc 15 §6 step 3: `feature` in the change header,
  domain, parts per service), which does not exist yet.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md and the plans' tables:
   a. G6/P1: accept doc 15's model (one shell, engines stay separate, backends merge module by module later) or a
      different one; the product name; what "one workspace" means across pdi tenants, ShipScope workspaces and
      ci_for_sdlc projects (mapping, who creates it, what happens to existing ones).
   b. One identity: GitHub sign-in as today, how the shell calls ci_for_sdlc and ShipScope for the signed-in user
      (per-user tokens, a service token per workspace, or a shared session), without a secret copied by hand.
   c. G7: the measure set, each definition (start and end event, what counts as failure, restore), the one place that
      computes them, and how tf's control band and ShipScope's /metrics fit (reuse, not a second formula).
   d. Scope of this stage: which menu sections ship read-only now, whether the feature catalogue (Product) is in this
      stage or the next, and P2 (Jira or repo as the source of work) as the shell's default.
2. Then a plan in docs/ (plan-etap12-platforma.md): the workspace mapping and identity, the menu and each section's
   data source, the measures with definitions, the contract change if Product is in, what stays in each engine, the
   failure cases (an engine down, a user without access in one engine, stale data), migration for existing users,
   tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the identity
   and workspace mapping, the shell's menu and read-only sections, the measures in Outcomes, the feature catalogue if
   approved. No backend merging in this stage.
4. Docs: README, docs/15-jedna-platforma.md (status: decided, what is built), design/platforma/README.md (which
   screens are live), plan-jeden-flow-sdlc.md (G6, G7, P1, P2 state), docs/przebieg-na-sobie-s5.md (one entry point).

Tests:
- one sign-in reaches every section; a user without access in one engine sees that section's clear refusal, never
  another workspace's data; unauthenticated refused;
- each section shows the same numbers as its engine's own UI or API for the same period;
- each measure: its definition pinned by a test on fixed fixtures, computed in one place, with its source and period
  shown; a missing source shows "no data", never zero;
- an engine down degrades only its section; ShipScope and ci_for_sdlc still work alone;
- menu, sections and charts: keyboard use and accessible names (WCAG AA); no secret or token in logs, URLs or the
  client bundle.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
lint, typecheck, tests and e2e, and each touched repo's own gates, all in Actions. At the end, walk the shell with me:
sign in once, go from "Now" to the S5 change in "Work", its release in "Releases", and its numbers in "Outcomes".
Commit, PRs, the product name, any change to existing users' workspaces and changes in other repos on my request.
```

## Etap 13 — pdi (+ ShipScope, tf): przełącznik funkcjonalności i pierwsze łączenie backendów

Start dopiero po etapie 12 (powłoka i sekcje tylko do odczytu działają, G6, G7 i P1 rozstrzygnięte). Źródło:
[dokument 15](15-jedna-platforma.md) §3 (funkcjonalność jako trwały byt, dwa rodzaje flag), §4 (przełącznik
funkcjonalności), §6 kroki 5–6 i §7 (otwarte pytania), ADR-001 i ADR-003 w ShipScope, DA6 z wykonawcami z etapu 7
i poziomy autonomii z etapu 6. Część A: jeden przełącznik na funkcjonalność i środowisko, plan przełączenia (BE przed
FE przy włączaniu, odwrotnie przy wyłączaniu), najpierw na sucho, potem pierwszy wykonawca zapisu. Część B: plan
łączenia backendów i pierwszy moduł (pdi z warstwą pdi w ShipScope). Dokument 15 §4 mówi wprost, że przełącznik
zmienia zasadę „ShipScope tylko obserwuje” i wymaga nowego ADR, więc polecenie zaczyna od ADR-004. Sesja w klonie pdi;
ADR-004 i zmiany w ShipScope osobnymi PR-ami w jego repo, po Twojej zgodzie. Włączenie na PROD zawsze jest decyzją
człowieka, a ekran pokazuje to, co odczytano, nie to, co zlecono.

```text
Implement stage 13: steps 5–6 of docs/15-jedna-platforma.md §6 — the feature switch from §4 (one switch per feature
and environment, a switch plan, dry run first, then the first write executor) and the first backend merge (pdi with
ShipScope's pdi layer) — after stage 12. Answer me in Polish; code, commits and PR titles in English, Conventional
Commits.

Preconditions, check them first and stop if one is missing:
- stage 12 is done: G6, G7, P1 and P2 are recorded in docs/decyzje.md, the shell runs with read-only sections, and
  the feature catalogue (doc 15 §3: `feature` in the intent header, domain → feature → parts per service) exists in
  the contract, or stage 12 left it for this stage (then it is part of step 2 below);
- stage 7's DA6 executors (stage change by PR to the flags file through tf, or a provider adapter) and stage 6's
  autonomy levels work in production;
- ShipScope's ADR-001 and ADR-003 ("ShipScope only observes"), and doc 15 §4's note that the switch changes this
  rule and needs a new ADR; doc 15 §7's open questions (where flags live in the services, whether
  evdt-shipscope-flags stays the flag backend, whether PROD always goes through a pdi decision).

Goal:
A. On the Product screen, one switch per feature and environment. Using it creates a switch plan: on = BE parts
   first, then FE; off = the reverse; each step names its service, flag, kind (release flag or permanent switch) and
   executor. A step whose code is not deployed on that environment makes the switch inactive with the reason. The
   plan runs dry first (what would change, nothing written), then for real: TEST and QA through autonomy level 1–2,
   PROD as an inbox decision at level 3. The screen shows what ShipScope read back, not what was ordered; a mismatch
   is visible and stops the plan.
B. A written plan for merging backends module by module, starting with pdi and ShipScope's pdi layer (doc 15 §1:
   most integration code is between them: service tokens, signed events, connection checks), and only its first
   module done in this stage, after my OK.

Today:
- Flags are per service: config/flags.{env}.json in sprintdeck (code flags, changed by PR through tf), endpoints and
  pushed sources in ShipScope; stage 7 added executors for stage changes of release flags.
- Doc 15 §3: a release flag belongs to a change and goes after full release; a permanent switch steers a feature for
  good. §4: the first runtime candidate executor is evdt-shipscope-flags (environments, services, order, log).
- ShipScope reads flags and confirms state; with ADR-001/003 it never writes them.
- pdi and ShipScope's pdi layer talk through a service token, signed events and connection pings (ShipScope's
  lib/pdi-connection.js, pdi's receiver).

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md, the plans' tables and, for ShipScope, an ADR-004 draft:
   a. ADR-004: who writes flag state (executors only, ShipScope stays a reader and confirms from its read), and what
      that changes in ADR-001/003; the PR to ShipScope only after my OK.
   b. The executors per flag kind: code flags (PR through tf, enters with the deploy), runtime flags (provider adapter;
      evdt-shipscope-flags or another), and what a switch does for a feature whose parts use different kinds.
   c. The switch plan's rules: order (BE → FE, reverse for off), the "code deployed" check per part, timeouts between
      steps, what a partial failure does (stop and propose rollback of done steps, never leave it half on silently).
   d. Levels: TEST/QA at 1 or 2, PROD always 3 (or doc 15 §7's alternative: roles and a log); the decision type
      (`flag.stage_advance` as doc 15 says, or a new `feature.switch`, a contract change).
   e. Part B: the first module to merge and the target (into the pdi service, or a shared module both call), what is
      removed (tokens, signatures, pings between them), migration of existing connections, rollback.
2. Then a plan in docs/ (plan-etap13-przelacznik.md): the catalogue and switch model, the plan and its dry run, the
   executors, confirmation from ShipScope's read, the failure cases (executor down, read-back mismatch, deploy rolled
   back mid-plan, two switches at once), the part B merge plan, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the contract
   change if any, the switch plan with dry run, the Product screen's switch, the first write executor, the
   confirmation from ShipScope, then part B's first module.
4. Docs: README, docs/15-jedna-platforma.md (§4 and §6 state, §7 answers), design/platforma/README.md (Product live),
   plan-jeden-flow-sdlc.md, ShipScope's ADR-004 and README for its part, docs/przebieg-na-sobie-s5.md (turning the S5
   feature on for users).

Tests:
- the plan orders BE before FE for on and the reverse for off; a part without deployed code makes the switch
  inactive with the reason; the dry run writes nothing;
- TEST/QA at the agreed level, PROD only after my button; every step through its executor only;
- a step failure stops the plan and proposes a rollback of done steps; never half on without a visible state;
- the screen shows ShipScope's read-back; a mismatch is shown and stops the next step;
- one plan per feature and environment at a time; a second switch is refused clearly;
- part B: the merged module keeps the contract's behaviour (existing pdi and ShipScope tests pass unchanged or are
  replaced one for one), existing connections migrate, rollback restores the previous path;
- tenancy as before; no secret or token in logs, URLs, events, PR bodies or the client bundle.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
checks and each touched repo's own gates, all in Actions. At the end, with me: a dry run of the S5 feature's switch
on TEST, then a real switch on TEST, then the PROD decision in the inbox (I decide whether to approve). Commit, PRs,
ADR-004, any real switch on QA or PROD, migration of existing connections and changes in other repos on my request.
```

## Etap 14 — pdi (+ ShipScope, ci_for_sdlc): łączenie backendów moduł po module

Start dopiero po etapie 13 (pierwszy moduł połączony i działa na produkcji, plan łączenia z części B zatwierdzony).
Źródło: [dokument 15](15-jedna-platforma.md) §1 (granice: tf zawsze osobno, ShipScope i ci_for_sdlc jako osobne
silniki we wspólnym produkcie) i §6 krok 6 oraz plan łączenia z etapu 13 (`plan-etap13-przelacznik.md`, część B).
Zakres zna dopiero ten plan, więc polecenie jest pętlą: jedna sesja to jeden moduł, a etap powtarza się, dopóki plan ma
kolejne moduły. Cennika i rozliczeń z §1 dokumentu 15 nie obejmuje, bo żaden plan ich nie opisuje. Sesja w klonie
pdi; zmiany w ShipScope i ci_for_sdlc osobnymi PR-ami w ich repo, po Twojej zgodzie.

```text
Implement stage 14: the next module of the backend merge from docs/15-jedna-platforma.md §6 step 6 ("łączenie
backendu moduł po module"), following the merge plan written in stage 13 part B (docs/plan-etap13-przelacznik.md).
One module per session; repeat the stage while the plan has modules left. Answer me in Polish; code, commits and PR
titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 13 is done: the feature switch works, the first module (pdi with ShipScope's pdi layer) is merged and in
  production, and its rollback was tested;
- the merge plan from stage 13 part B is approved and lists the remaining modules in order, each with what it removes
  and what it keeps; tell me which module is next and whether any earlier one is unfinished (if so, finish that first);
- doc 15 §1's boundaries: tf always separate (it runs in the customer's repo and CI); ShipScope (deployments, flags,
  drift) and ci_for_sdlc (definition consistency) are separate engines with value on their own, and their trust
  boundaries differ (ShipScope's worker holds sealed customer tokens, ci_for_sdlc reads Confluence and Figma).

Goal: the next module is merged so that its integration code (tokens between services, signed events, connection
checks, duplicate models) is gone, behaviour seen by users and by the contract does not change, and the engine it
came from still works alone where the plan says it must. After it: the plan's table shows it done, what was removed,
and what is next.

Today:
- The shell (stage 12) reads pdi, ci_for_sdlc and ShipScope's service API; stage 13 merged the first module.
- Three stacks: Node + Fastify + Postgres with RLS (ShipScope), a TypeScript monorepo (ci_for_sdlc), Python (pdi's
  MCP server and CLI) plus the pdi service from stage 4. The contract in contract/ is the boundary between modules,
  so merging should not need rewrites (doc 15 §1).
- Each engine has hundreds of tests; they are the proof that behaviour did not change.

1. Before any code, for the next module, show me and wait for my answer, then record it in docs/decyzje.md and the
   merge plan:
   a. What moves, where to (into the pdi service or a shared module), and in which language and stack; why this
      costs less than keeping the integration (doc 15 §1's test).
   b. Data: which tables or files move, the migration (idempotent, with a dry run), tenancy and RLS after the move,
      and how sealed secrets move without being decrypted outside their worker.
   c. What the source engine keeps so it still works alone (or the decision that it no longer needs to), and what
      changes for its existing users and settings.
   d. Rollback: how to return to the previous path, and for how long both paths are kept.
2. Then add the module's section to the merge plan: steps, tests carried over (one for one), contract checks, failure
   cases, cut-over order. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: the moved
   code behind the existing contract, the migration with a dry run, the switch of callers, then removal of the old
   integration code once the new path has run in production for the agreed time.
4. Docs: the merge plan's table, docs/15-jedna-platforma.md §6 state, the touched engines' README and architecture
   docs (ShipScope's CLAUDE.md and design-docs, ci_for_sdlc's docs), docs/przebieg-na-sobie-s5.md if anything a user
   does changes.

Tests:
- the module's existing tests pass in their new place unchanged or are replaced one for one, with a list of each
  mapping in the PR;
- contract tests on both sides of every remaining boundary pass;
- the migration: every record readable after it, a second run changes nothing, the dry run writes nothing;
- tenancy and RLS hold after the move (one tenant never sees another's data); sealed secrets are never decrypted
  outside their worker;
- the source engine still works alone where the plan says so;
- rollback restores the previous path with its data; no secret or token in logs, URLs, events or client bundles.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
checks and each touched repo's own gates, all in Actions. At the end, with me: run S5's main path through the
merged module (report → change → release → outcome) and show the removed integration code. Commit, PRs, the
migration on real data, the cut-over, the removal of the old path and changes in other repos on my request.
```

## Etap 15 — pdi: pilotaż z design partnerami na platformie

Start dopiero po etapach 13–14 (platforma działa jako jeden produkt: powłoka, jedno logowanie, przełącznik
funkcjonalności; nie trzeba czekać na połączenie wszystkich modułów). Pilotaż z partnerami jest od 2026-10-23
wstrzymany ([dokument 11](11-propozycja-wartosci.md)), a materiały w `outreach/` i kryteria z
[dokumentów 06](06-mvp-i-pilotaz.md) i [08](08-plan-projektu.md) opisują starą propozycję wartości (strażnik podstaw
decyzji dla PM-a). Dlatego polecenie najpierw odwiesza pilotaż jako decyzję, przepisuje propozycję i kryteria pod
platformę ([dokument 15](15-jedna-platforma.md): jeden flow od zgłoszenia do skutku), a dopiero potem przygotowuje
wdrożenie u partnera. Sesja w klonie pdi. Kontakt z kandydatami, umowy i dostęp do ich systemów są zawsze po Twojej
stronie; żadna wiadomość nie wychodzi bez Ciebie.

```text
Implement stage 15: a pilot of the platform with external design partners, after stages 13–14. The partner part of
the project is on hold (docs/11-propozycja-wartosci.md, note of 2026-10-23: "Część dotycząca zewnętrznych design
partnerów jest wstrzymana") and its materials describe the earlier value (the decision-basis guardian for a PM).
Restart it for the platform: decision first, then materials, onboarding and measurement. Answer me in Polish; code,
commits and PR titles in English, Conventional Commits; pdi docs and outreach materials in Polish.

Preconditions, check them first and stop if one is missing:
- the platform works as one product for me: stage 12's shell and single sign-in, stage 13's feature switch, and the
  S5 flow on sprintdeck end to end (report → change → release → outcome); list what is still missing and whether
  it blocks a partner;
- the pilot materials as they are: docs/06-mvp-i-pilotaz.md (§6.4 metrics, §6.5 live pilot), docs/08-plan-projektu.md
  (stage 0 and 5, §4 stop criteria, §5 success measures), docs/11-propozycja-wartosci.md, docs/15-jedna-platforma.md,
  outreach/ (propozycja-dla-pm.md, profil-design-partnera.md, wiadomosc-kontaktowa.md, zasady-poufnosci.md,
  lista-kandydatow.md, rejestr-kandydatow-szablon.csv);
- the evidence so far: the S5 journals (stages 2–3), stage 6's acceptance counter, stage 12's G7 measures.

Goal: a recorded decision to restart the pilot for the platform, a rewritten value proposition and success
criteria that the platform's own data can measure, updated outreach materials ready for me to send, and an onboarding
path for one partner team that takes a day, not a week: their workspace, tf in their repo, their Jira/Confluence/
Figma connected with the least access, their first report through the flow. During the pilot, a weekly evidence
report per partner from the platform's own measures, and a final go/no-go against criteria written before it began.

Today:
- doc 11's value ("strażnik podstaw decyzji") moved into pdi's decision registry (doc 12 §3–4); the platform (doc 15)
  offers one flow from report to outcome with decisions, readiness, release state and autonomy;
- outreach/ targets PMs with 1–3 decisions under way and a 4–6 week watch; the platform's user is wider (PO, dev,
  ops) and its pilot needs a repo, CI and a tracker;
- the confidentiality rules (outreach/zasady-poufnosci.md) were written for weekly documents, not for a service that
  reads a partner's code, Jira, Confluence and Slack;
- doc 08 §4 has stop criteria and doc 06 §6.4 metrics for the old scope.

1. Decisions first, before any material or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md (and a note at the top of doc 11):
   a. Restart: yes or not yet, from the evidence and what still blocks a partner; the pilot's one main question
      (e.g. "does a team get from report to released change with fewer hand-offs and known decisions?").
   b. The partner profile: team size, stack, tracker, CI, who uses the platform (PO, dev, ops), how many partners
      (doc 08 aimed at 3+), how long (weeks), and what they must already have (GitHub, Actions, Jira or repo mode).
   c. Success and stop criteria, each measurable by the platform (G7 measures, acceptance rate, decisions recorded,
      hand-offs removed, partner's own rating), with thresholds set before the pilot.
   d. Data and confidentiality: what the platform reads from a partner, where it is stored, retention, who at our side
      can see it, the model provider's terms, deletion at the end; a written agreement before any access.
2. Then a plan in docs/ (plan-etap15-pilotaz.md): the decisions, the onboarding path step by step with what is still
   manual, the weekly report, the support model (who answers, how fast), the risks (a partner's CI or Jira differs,
   a secret mishandled, noise), open questions. Wait for my OK.
3. Then, only what the plan approves:
   - rewrite outreach/ for the platform (offer, profile, contact templates, confidentiality rules, candidate register)
     and a one-page pilot agreement draft; I send and sign, never you;
   - the onboarding path: gaps found by walking it on a fresh test workspace with a fresh test repo, each fixed in its
     repo by TDD (red test first), small PRs after my OK;
   - the weekly evidence report from the platform's data (no partner data in our repos or logs).
4. Docs: docs/decyzje.md, doc 11 (status), docs/06 and docs/08 (pilot sections point to the new plan),
   docs/15-jedna-platforma.md (pilot state), README (how a partner starts).

Tests:
- the onboarding path on a fresh test workspace and repo reaches the first report in the flow without a step that
  needs a secret copied by hand;
- a partner's workspace is isolated (tenancy and RLS as before); deleting a partner removes their data per 1d;
- the weekly report computes each criterion from fixed fixtures the same way as G7 does, and shows "no data", never
  zero, when a source is missing;
- no partner name, code, issue text or secret in our repos, logs, events or reports beyond what 1d allows.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus each touched repo's own gates,
all in Actions. At the end, walk the onboarding path with me on a fresh test workspace and repo, and show me the
outreach materials ready to send. Commit, PRs, every message to a candidate, any agreement, any access to a partner's
systems and changes in other repos on my request.
```

## Etap 16 — pdi (+ ShipScope, ci_for_sdlc): utrzymanie i niezawodność platformy

Start dopiero po etapie 15 (pierwsi partnerzy polegają na platformie albo mają zacząć). Zakres: usługa pdi i konsola
(etapy 4–10), powłoka (etap 12), połączone backendy (etapy 13–14) i ich styki z ci_for_sdlc i ShipScope. Wzorem jest
to, co ShipScope ma już u siebie: `server/SLO.pl.md` (SLO, budżet błędów, alerty, publiczna strona `/status`),
`server/KOPIE.pl.md` (kopie i kwartalny test odtworzenia `verify-restore`, tylko do odczytu), `server/SEKRETY.pl.md`
(rotacja kluczy z pierścieniem kluczy), `/health/worker`, `/metrics` za tokenem i logi JSON bez sekretów. Polecenie
każe przenieść te wzorce na całą platformę zamiast wymyślać je od nowa i zaczyna od decyzji, co obiecujemy partnerom
i ile to może kosztować. Sesja w klonie pdi; zmiany w ShipScope i ci_for_sdlc osobnymi PR-ami w ich repo, po Twojej
zgodzie. Ustawienia hostingu, alertów i dyżurów zmieniasz Ty albo dzieje się to na Twoje polecenie.

```text
Implement stage 16: operations and reliability for the whole platform — the pdi service and console (stages 4–10),
the shell (stage 12), the merged backends (stages 13–14) and their links to ci_for_sdlc and ShipScope — after stage
15. Reuse ShipScope's patterns instead of inventing new ones. Answer me in Polish; code, commits and PR titles in
English, Conventional Commits; runbooks in Polish.

Preconditions, check them first and stop if one is missing:
- stage 15's state: whether partners are live or about to be, and what docs/plan-etap15-pilotaz.md promised them
  (support model, response time, data deletion);
- the hosting chosen in stage 3 (decision 1a) and how each service runs today (web, worker, scheduler, database);
- ShipScope's operating docs as the pattern: server/SLO.pl.md (SLOs, error budget, alerts, public /status page),
  server/KOPIE.pl.md (backups, restore, quarterly restore test with `npm run verify-restore`, read only,
  `RESTORE_DATABASE_URL`), server/SEKRETY.pl.md (keys, first setup, rotation with a key ring), /health/worker,
  /metrics behind a token, JSON logs through a logger that masks credentials.

Goal: for every service of the platform:
- written SLOs per user journey (sign in, see the inbox, decide, event received → shown, phase dispatched), an error
  budget, and alerts on burn rate that reach a person, with a public status page for partners;
- health endpoints that judge real work (queues drained, schedulers on time, last successful sync), metrics behind
  a token, JSON logs with request and tenant ids and no secret or partner content;
- backups with a tested restore (a scheduled, read-only restore check like ShipScope's), a stated RPO and RTO;
- every secret listed with its owner, where it lives, how it rotates (a key ring, no downtime) and when it last did;
- runbooks for the likely incidents (database down, worker stuck, webhook backlog, a partner's token revoked, model
  provider down, cost spike), and a monthly cost view per service and per tenant.

Today:
- ShipScope has all of the above for itself; pdi's service, console and merged backends have whatever stages 3–14
  built (check each: health, metrics, logs, backups, secrets).
- Stage 9 may have brought an incident tool (G8); stage 10 a model budget per tenant; stage 12 the G7 measures.
- Partners from stage 15 see outages directly; the platform now holds their data and sealed tokens.

1. Decisions first, before any plan or code. Show me the recommendation for each, wait for my answer, then record
   them in docs/decyzje.md:
   a. The SLOs and their windows per journey, and what partners are told (status page, response time).
   b. Alerting and on-call: where alerts go (the stage 9 tool, if any, or another), who is on call, quiet hours.
   c. Backups: RPO/RTO, where copies live (one copy outside the hosting, as ShipScope's KOPIE says), the restore test
      cadence, and partner data deletion at the end of a pilot (stage 15's 1d).
   d. Costs: the budget per month, the per-tenant view (model calls, compute, storage), and the limits that stop a
      runaway (tie to stage 10's budget if built).
2. Then a plan in docs/ (plan-etap16-utrzymanie.md): a table of services × (health, metrics, logs, backups, secrets,
   SLO, alerts, runbook) with today's state and the gap, the order of work, tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: health and
   metrics, log fields and masking, the restore check, the secret inventory and rotation, the status page, the cost
   view, then the runbooks (docs/ in Polish, as ShipScope's).
4. Docs: README (operations section), the runbooks, docs/15-jedna-platforma.md (operations state), the pilot plan's
   support section, and each touched engine's operating docs.

Tests:
- each health endpoint fails on the cases it is meant to catch (stalled scheduler, undrained queue, failing sync), on
  fixtures, as ShipScope's /health/worker tests do;
- metrics are refused without the token; log lines carry request and tenant ids and never a secret, token, flag value
  or partner content (a test feeds secrets through every logger path);
- the restore check is read only, refuses the production URL, and finds a planted mismatch;
- rotation: data sealed with the old key opens after rotation, re-sealing finishes, no request fails meanwhile;
- the status page computes each component from the same health judgment, with no script on the page;
- cost limits stop work for one tenant without affecting others.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
checks and each touched repo's own gates, all in Actions. At the end, with me: one restore test on a copy, one key
rotation on a test workspace, and one alert fired end to end. Commit, PRs, any change to hosting, alerting or on-call
settings, any rotation on production, and changes in other repos on my request.
```

## Etap 17 — pdi: cennik i rozliczenia platformy

Start dopiero po etapie 16 (pilotaż ma wyniki, a widok kosztów na tenanta działa). Żaden plan nie opisuje cennika;
[dokument 15](15-jedna-platforma.md) §1 wymienia go tylko jako warstwę wspólną od razu. Dlatego polecenie zaczyna od
dokumentu decyzyjnego opartego na dowodach z pilotażu (etap 15: za co partnerzy cenią platformę, miary G7),
rzeczywistych kosztach z etapu 16 (koszt na tenanta: wywołania modelu, obliczenia, przechowywanie) i świeżym badaniu
cen konkurencji (analiza z 2026-10-19 dotyczyła starej propozycji wartości). Kod obejmuje dopiero zatwierdzony model:
plany, limity, uprawnienia i integrację z dostawcą płatności. Sesja w klonie pdi; zmiany w ShipScope i ci_for_sdlc
(limity w ich silnikach) osobnymi PR-ami, po Twojej zgodzie. Sprawy prawne i podatkowe (regulamin, faktury, VAT)
polecenie tylko wypisuje jako pytania do Ciebie i doradcy. Żadna płatność ani zmiana planu prawdziwego klienta nie
dzieje się bez Ciebie.

```text
Implement stage 17: pricing and billing for the platform (docs/15-jedna-platforma.md §1: name, menu, UI, sign-in,
workspace and pricing are one from the start), after stage 16. No plan describes pricing yet: write the decision
document first, from the pilot's evidence, the real costs and fresh market research; code only the approved model.
Answer me in Polish; code, commits and PR titles in English, Conventional Commits; pdi docs in Polish.

Preconditions, check them first and stop if one is missing:
- stage 15's pilot has results: the go/no-go against its criteria, the weekly evidence reports, and what partners
  said they would pay for (ask me for anything not in docs/plan-etap15-pilotaz.md). Without results, stop: pricing
  without evidence is a guess;
- stage 16's cost view per service and per tenant (model calls, compute, storage) for at least one full month;
- the old market notes are for the earlier scope: docs/10-analiza-konkurencji.md and
  docs/research/20261019-konkurencja/ (e.g. one enterprise price); do not reuse them as current prices.

Goal: a recorded pricing model (who pays, for what unit, which plans, what each includes, the free or trial tier,
limits and what happens at a limit), its margin against the real cost per tenant, and, once approved, the platform
enforcing it: plans and entitlements per workspace, usage counted from the data the platform already has, limits
that degrade one tenant clearly without touching others, a billing portal through the chosen payment provider, and
an admin view of plan, usage and invoices. Pilot partners move to a plan only by an explicit, recorded choice.

Today:
- No plans, entitlements or payments exist. Stage 10 may have a model budget per tenant; stage 16 has cost limits and
  a cost view; ShipScope has per-workspace settings and per-token rate limits; ci_for_sdlc has its own SaaS mode.
- The platform's value as the pilot measured it (G7 measures, decisions, hand-offs removed) is the basis for the unit.
- Prices of comparable tools change often; check them in primary sources with dates, not from memory.

1. Research and decisions first, before any code. Show me the recommendation for each, wait for my answer, then
   record them in docs/decyzje.md:
   a. Market: current prices of the closest tools (by category from doc 10, plus AI coding and delivery platforms),
      each with its source and date; what they charge for (seats, projects, usage).
   b. The unit and plans: per seat, per workspace, per repo, per change delivered, usage-based for model calls, or a
      mix; the plans and limits; the trial or free tier; how pilot partners transition.
   c. Margin: the price against stage 16's cost per tenant, the model-call share, and the limits that keep a plan
      profitable.
   d. Payments: the provider (and why), what we store (only its customer and subscription ids, never card data),
      webhooks and their signature, failed payments and grace period, cancellation and data deletion (stage 15's
      rule). Legal and tax questions (terms, invoices, VAT, consumer vs business) listed for me and an adviser, not
      decided by you.
2. Then a plan in docs/ (plan-etap17-cennik.md): the model, the entitlements per plan, how usage is counted from
   existing data, limit behaviour per engine, the provider integration, the admin and customer views, migration of
   existing workspaces (pilot partners, my own), failure cases (provider down, webhook replay, plan change mid-period,
   usage counted twice), tests, open questions. Wait for my OK.
3. Implement only what the plan approves, TDD (red test first), small PRs, each in its repo after my OK: entitlements
   and plans, usage counting, limits per engine, the provider integration in its test mode, the views, then live mode
   only on my request.
4. Docs: README (plans), docs/15-jedna-platforma.md (pricing state), the pilot plan (transition), outreach materials if
   they mention terms, and runbooks for billing incidents (stage 16's format).

Tests:
- each plan's entitlements are enforced in every engine; a limit degrades only that tenant, with a clear message and
  no data loss;
- usage counted once from the source data (a replayed event or retried job does not count twice), and matches the
  cost view for the same period;
- provider webhooks: signature checked, idempotent on event id, out-of-order events handled, unknown events ignored
  safely; failed payment → grace period → limited mode as decided;
- no card data stored; no provider key, customer secret or payment detail in logs, URLs, events or client bundles;
- a plan change mid-period and a cancellation behave as decided, and deletion follows stage 15's rule;
- tenancy as before; admin views only for the workspace's admins.

Gates: the Python gates (uv run pytest, ruff check, ruff format --check, mypy src) plus the service's and console's
checks and each touched repo's own gates, all in Actions. At the end, with me: one full cycle in the provider's test
mode (trial → plan → usage → limit → upgrade → cancellation). Commit, PRs, prices published anywhere, the provider
account and live mode, any charge, any change to a real customer's plan, and changes in other repos on my request.
```

## Etap 18 — pdi: przegląd na dowodach i nowa mapa drogowa

Start dopiero po etapie 17 (wyniki pilotażu, co najmniej kwartał danych z produkcji, pierwszy pełny miesiąc
rozliczeń, jeśli etap 17 doszedł do trybu produkcyjnego). Ten etap nie dokłada funkcji: zestawia dowody z pilotażu,
produkcji, kosztów i miar z założeniami planów, z których powstały etapy 2–17, zapisuje, co kontynuować, zmienić
albo wyciąć, i pisze plan kolejnych etapów. Wynikiem jest tylko dokumentacja i decyzje; wycięcie kodu albo funkcji
polecenie proponuje jako osobne etapy, nigdy nie usuwa niczego samo. Sesja w klonie pdi (plany, decyzje, polecenia
startowe); pozostałe repo tylko do odczytu. Każda decyzja „kontynuować, zmienić, wyciąć” należy do Ciebie.

```text
Run stage 18: an evidence-based review of everything stages 2–17 built, and a new roadmap. No new features in this
stage: the output is a review, recorded decisions and a plan for the next stages. Answer me in Polish; pdi docs in
Polish; commits and PR titles in English, Conventional Commits.

Preconditions, check them first and stop if one is missing:
- stage 17 is done or stopped at a recorded point, and you know which stages 2–17 were completed, partly done,
  skipped or stopped (from docs/polecenia-startowe-sdlc-lokalnie.md, docs/decyzje.md and each stage's plan file);
- evidence exists for at least one quarter of production: the pilot's weekly reports and go/no-go (stage 15), the G7
  measures (stage 12), the autonomy report (stage 6), the cost view (stage 16), incidents (stage 9, if built), the SLO
  and error budget history (stage 16), billing data (stage 17, if live). Name each source you could not read;
- the other repos (ShipScope, ci_for_sdlc, tf, sprintdeck) are read-only for this stage.

Goal: one review document and one roadmap I can decide on:
- for each stage and each major capability (inbox, timeline, trace, registry, autonomy levels, flag rules, light
  review, Jira mirror, incidents, Slack, chat, one shell, feature switch, merged backends, pilot, operations,
  pricing): the assumption it was built on (quote the plan or decision), the evidence of use and value now, the cost
  to keep it (code size, tests, incidents, model and hosting cost), and a recommendation: keep, change, or cut;
- the decisions still open across the docs (decyzje.md, plans' "do decyzji" sections, doc 15 §7) and which the
  evidence now answers;
- a new roadmap: the next stages, in order, each with its reason from the evidence, its dependency and its stop
  criterion, in the same shape as the earlier starter prompts' preconditions.

Today:
- Stages 2–17 were written ahead of the evidence, each with "decisions first" and conditions (e.g. K-3 only if chat
  was the main mode, G2.3 only after the pilot, A4 only with guard metrics).
- docs/kontekst-rozmowy.md, plan-jeden-flow-sdlc.md, plan-automatyzacja-i-konsola.md §8, plan-g1-g2.md §10 and
  docs/15-jedna-platforma.md hold status tables that may have drifted from what is live.
- Some documents describe earlier directions (docs/01–11, outreach/) and are marked as superseded only in part.

1. Collect before judging. Build a table of capability × (built? live? used how often, by whom; value measure; cost;
   incidents; open decisions), each cell with its source (file, query, report, date). Mark every guess as a guess.
   Show me the table and the gaps in the evidence before any recommendation.
2. Then the review (docs/przeglad-etap18.md): per capability, the assumption, the evidence, the cost and the
   recommendation with its reason; what surprised us; what the evidence cannot yet answer and what would answer it.
   Wait for my decisions on each keep/change/cut, then record them in docs/decyzje.md.
3. Then the roadmap (docs/plan-po-przegladzie.md): the next stages in order, each with goal, reason (from the
   review), dependency, preconditions, stop criterion and rough size; cuts listed as their own stages (what is removed,
   migration for users, rollback), never removed silently. Wait for my OK.
4. Docs, after my OK: update the status tables (kontekst-rozmowy.md, plan-jeden-flow-sdlc.md,
   plan-automatyzacja-i-konsola.md §8, plan-g1-g2.md §10, docs/15-jedna-platforma.md) so they match what is live;
   mark superseded documents at their top with a link to what replaces them; add the new roadmap's first stage to
   docs/polecenia-startowe-sdlc-lokalnie.md only when I ask.

Checks (instead of tests, since this stage writes no code):
- every number in the review has a source and a date; every recommendation names the evidence it rests on;
- no status table claims a capability is live when its evidence says otherwise;
- no partner name, issue text, code or secret in the review or roadmap beyond what stage 15's confidentiality rule
  allows; aggregated numbers only;
- the markdown passes the repo's doc checks if any (links resolve, tables render).

Gates: uv run pytest (doc-related tests, if any) and the repo's lint for docs. Commit, PR, any decision to cut a
capability, any message to partners about changes, and any change in other repos on my request.
```
