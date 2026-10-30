# Polecenia startowe: L1–L5 i etapy 2–4 planu `sdlc up`

**Data:** 2026-10-30 · **Źródło:** [plan `sdlc up`](plan-sdlc-lokalnie.md) §2 (Z1–Z5) i §4, decyzje DL1–DL3
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `9ec4e66`, ShipScope 0.2.64, ci_for_sdlc 0.1.34

L1, L2 i L3 są niezależne. Każdy idzie w osobnej sesji Claude Code w swoim repo. Polecenie wklejasz jako pierwszą
wiadomość sesji. L4 (`sdlc` w `pdi/stack/`) startuje dopiero po merge'u wszystkich trzech, a L5 (repo próbne)
po merge'u L4. Etap 2 (scenariusz S5 na sprintdecku) startuje po L5 i udanym przebiegu §5 na repo
próbnym. Etap 3 (produkcja, §7 planu) startuje po etapie 2, a etap 4 (usługa pdi
i konsola, krok K-2) po etapie 3.

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
