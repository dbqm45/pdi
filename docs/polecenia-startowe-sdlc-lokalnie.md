# Polecenia startowe: L1–L4 planu `sdlc up`

**Data:** 2026-10-30 · **Źródło:** [plan `sdlc up`](plan-sdlc-lokalnie.md) §2 (Z1–Z5) i §4, decyzje DL1–DL3
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `9ec4e66`, ShipScope 0.2.64, ci_for_sdlc 0.1.34

L1, L2 i L3 są niezależne. Każdy idzie w osobnej sesji Claude Code w swoim repo. Polecenie wklejasz jako pierwszą
wiadomość sesji. L4 (`sdlc` w `pdi/stack/`) startuje dopiero po merge'u wszystkich trzech, potem L5 (repo próbne).

| Krok | Repo | Sesja w katalogu |
|---|---|---|
| L1 | ShipScope | `/Users/x/WebstormProjects/evdt-service-shipscope` |
| L2 | pdi | `/Users/x/WebstormProjects/pdi` |
| L3 | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` |
| L4 | pdi | `/Users/x/WebstormProjects/pdi` |

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
