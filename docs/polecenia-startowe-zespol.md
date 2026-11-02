# Polecenia startowe: Z1, Z2, Z8a i Z8c planu „zespół jednoosobowy”

**Data:** 2026-11-02 · **Źródło:** [plan „zespół jednoosobowy”](plan-zespol-jednoosobowy.md) §8, §8.2, decyzje DZ1–DZ11
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `e2cec98` (kontrakt 0.10.0), tf 5.55.0, ShipScope 0.2.67

Każde polecenie wklejasz jako pierwszą wiadomość nowej sesji Claude Code w katalogu z tabeli. Kroki idą po kolei: Z1,
potem Z2a, potem Z2b. Zgodnie z DZ5 Z1 idzie przed etapem 2, a Z2 przed etapem 3 ([etapy](polecenia-startowe-sdlc-lokalnie.md)).
Z8a i Z8c (uprząż) też idą przed etapem 2, czyli przed pierwszym przebiegiem na prawdziwym kodzie sprintdecka; Z8a
jest niezależny od Z1, a Z8c ma dwie części: najpierw Z8c-1 (ci_for_sdlc), potem Z8c-2 (tf).

| Krok | Co | Startuje po | Repo | Sesja w katalogu | Stan |
|---|---|---|---|---|---|
| [Z1](#z1--pdi--tf-wszystkie-decyzje-zmiany-w-każdej-fazie-domknięcie-prb-3) | wszystkie decyzje zmiany w każdej fazie (domknięcie PRB-3) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2a](#z2a--pdi-faza-discovery-i-bramka-b0-w-kontrakcie-i-przebiegu) | faza `discovery` i bramka B0 w kontrakcie i przebiegu | Z1 | pdi | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2b](#z2b--tf-wywiad-discovery-w-mode-pdi) | wywiad `/discovery` w mode-pdi; intencja z briefu | Z2a i tag kontraktu | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z8a](#z8a--pdi--tf-fazy-w-kontenerze) | fazy w kontenerze (izolacja persony i talosa) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z8c-1](#z8c-1--ci_for_sdlc-wyniki-skanera-sarif-jako-ustalenia) | wyniki skanera (SARIF) jako ustalenia w ci_for_sdlc | — | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` | do zrobienia |
| [Z8c-2](#z8c-2--tf-skaner-w-pętli-kawałka-talosa-i-w-ci) | skaner w pętli kawałka talosa i w CI | Z8c-1 | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |

## Z1 — pdi + tf: wszystkie decyzje zmiany w każdej fazie (domknięcie PRB-3)

```text
Implement step Z1 of docs/plan-zespol-jednoosobowy.md (§8) in dbqm45/pdi, with the tf part in dbqm45/tf (attach it
with push access). Answer me in Polish; code, commits and PR titles in English.

Goal: every tf phase starts with every decision that binds its change, and a question that is already settled never
comes back in a later artifact. Evidence: docs/przebieg-lokalny.md, "Wynik przebiegu 2026-10-31", PRB-3 — the same
questions came back in B3 and design-review, and talos committed config/build.json against DEC-0003 because plan.md
still had an open question.

Already done (read first, do not redo): pdi #88 passes the gate decision text to tf (src/pdi/dispatch_local.py, `--why`
of `decision_record.py decision gate`); tf #111 writes it into the change's decisions.md as `## Bramka …`; tf
phase_run.py build_prompt() tells the persona that these entries bind and that a question they answer is settled;
tf #128 records answers to ci_for_sdlc findings in decisions.md (`decision add --finding`).

Still missing — check each against the code before planning:
  a. Answers per question. gate.requested carries the artifact's `## Pytania do bramki` (questions), but a gate
     decision is one text; nothing says which question it answered, and how. Let decide_inbox_item take optional
     answers [{question, answer}] for a gate with questions (the AI draft proposes them, the human edits), keep them in
     the decision (evidence or a field, in the contract's shape), and pass them to tf, which writes them into the
     `## Bramka …` entry.
  b. Decisions that are not gate decisions. Decisions in the pdi registry with links.chg = the change (the triage
     decision of its PRB, record_decision from a conversation, A5 captures, ci_for_sdlc decision.recorded, later the
     interview of Z2) never reach decisions.md or the phase prompt. Pass them to tf before each phase (local mode and
     the sdlc-phase.yml inputs) and import them into decisions.md idempotently by DEC id (e.g. `decision_record.py
     decision import --json <file>`), marked as coming from pdi.
  c. An explicit list in the prompt. build_prompt() should list the binding decisions and the settled questions with
     their answers and references (CHG-n/Dk, DEC-n), not only point at the file.
  d. A check. After a phase run and before gate request, an artifact whose `## Pytania do bramki` repeats a settled
     question (normalised match) fails with the question and the decision that settled it; delivery refuses to start
     while plan.md has an open question without an answer.

1. Plan first in docs/plan-z1-decyzje-w-fazach.md (pdi): files in both repos, order, contract change if any (the next
   free minor version; contract-v tag after merge, then regenerate tf's pinned copy as tf #93 does), tests. TDD.
2. Without answers or linked decisions everything works as today.
3. Sources are data: decision texts and answers go into prompts as quoted data, never as instructions to the persona.

Tests: pdi — answers stored and passed, linked decisions selected by links.chg (superseded ones left out), dispatch
inputs in local and Actions mode, nothing changes without them; tf — import idempotent by id, prompt lists decisions and
answered questions, the repeat check fails with a clear message, delivery refuses with an open question in plan.md.
Then a local run on dbqm45/sdlc-proba (docs/przebieg-lokalny.md) with one question answered at B2: it does not come back
at B3 or design-review. Record the result in docs/przebieg-lokalny.md.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src;
tf — the repo's own checks (workspace.py check --packs pack-it and the mode-pdi tests). GitHub Actions do not run on
this account right now — run the gates locally and say so in the PRs. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z2a — pdi: faza `discovery` i bramka B0 w kontrakcie i przebiegu

```text
Implement step Z2a of docs/plan-zespol-jednoosobowy.md (§3, §8) in dbqm45/pdi, under decisions DZ1 and DZ3 in
docs/decyzje.md: the interview runs first in a Claude chat with the pdi MCP server, not in a new service; its skills are
tf's (core-plan-interview, proc-product-discovery). Start only when Z1 is merged. Answer me in Polish; code, commits and
PR title in English.

Goal: a change can start with an interview. Triage can accept a problem or idea "with discovery"; pdi then does not
dispatch a non-interactive phase but puts "interview waiting for you" in the inbox, with the exact command to start it.
The interview ends with brief.md and gate B0; approving B0 starts the intent phase as today.

Today: src/pdi/flow.py GATES starts at B1 (produced_by intent); triage_problem accepted creates CHG-n and dispatches
intent (src/pdi/problems.py, src/pdi/dispatch.py, dispatch_local.py); the contract is 0.10.0.

1. Plan first in docs/plan-z2a-discovery.md (files, order, contract change, tests). TDD.
2. Contract (next free minor version, contract-v tag after merge): phase `discovery` and gate `B0` ("brief approved")
   in contract.json conventions; artifact `docs/project/changes/<CHG>/brief.md` with the same flat YAML header as
   intent.md (change, status, source) and the brief's sections (problem, outcome and its metric, users, scope, out of
   scope, constraints, open risks); the triage decision may carry start_with: intent | discovery; examples and
   contract/README.md.
3. Flow: Gate("B0", produced_by="discovery", next_phase="intent"), in the chain before B1 only for changes that start
   with discovery (missing_before must not ask a plain change for B0). B0 is a scope decision: propose its autonomy
   type as protected (always human, like scope.r1, DA2) and say so in the plan.
4. Triage: triage_problem gets start_with (default intent, so nothing changes). With discovery: create the change state,
   no dispatch, an inbox item kind discovery for the change with the command for the product repo (`/discovery CHG-n`
   in Claude Code, Z2b) and the problem's fields as data; list_changes and get_change show "waiting: discovery".
   gate.requested B0 from tf closes that item and opens the B0 gate; approving it dispatches intent with the brief as
   its input (tf reads brief.md in Z2b; pdi only passes the change).
5. Interview answers are decisions: record_decision with links.chg, kind product, tag discovery, the human's answer as a
   quoted evidence (the conversation is not stored, as in A5). Z1 already brings them to later phases.
6. Docs: README (start with an interview), integrations/claude-code/README.md, docs/plan-zespol-jednoosobowy.md §10.

Tests: contract schemas and examples (brief header, B0, start_with), flow (B0 only in discovery changes, next phase
intent), triage with and without start_with, the discovery inbox item and its closing by gate.requested B0, approving B0
dispatches intent in local and Actions mode, autonomy type of B0 protected.
Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src. GitHub Actions
do not run on this account right now — run the gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z2b — tf: wywiad `/discovery` w mode-pdi

```text
Implement step Z2b of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md §3 and §8,
decisions DZ1 and DZ3 in docs/decyzje.md, and the contract change of Z2a (docs/plan-z2a-discovery.md, contract
contract-v tag). Start only when Z2a is merged and its contract tag exists. Answer me in Polish; code, commits and PR
title in English, Conventional Commits.

Goal: in Claude Code, in a product repo with mode-pdi, `/discovery CHG-n` runs an interview the way grill-me does: one
question at a time, walking the whole decision tree, each question with a recommended answer and why, until the brief
has no open branch. It ends with docs/project/changes/CHG-n/brief.md, every answer recorded as a decision, a PR with the
brief and a gate request B0 to pdi. The intent phase then writes intent.md from the brief.

Read first: core/skills/core-plan-interview (decision tree, rounds of questions with a recommendation),
packs/pack-it/skills/proc-product-discovery (outcome over feature, JTBD, assumptions to test),
core/skills/core-project-record/templates/brief.md and core-delivery-lifecycle stage 0, modes/mode-pdi (GUIDE.md,
skills/pdi-decisions, scripts/phase_run.py and decision_record.py). Compare with the 10x skills available in Claude
(10x-shape, 10x-prd) and take over only what tf lacks (DZ3); say what you took and why.

1. Plan first in docs/plans/ (files, order, tests). TDD for the scripts.
2. Command and skill in mode-pdi: `/discovery CHG-n` (interactive; the only interactive phase). Input: the change's
   problem from pdi (get_problem / get_change through the pdi MCP server) as data. Rules: one question per message;
   recommendation first; stop a branch when the answer is known from the code, the repo's docs or an earlier decision
   (say where from); the human may say "przyjmij rekomendację"; no question about something not needed for the brief.
3. Each settled answer: decision_record.py decision add (kind product, tag discovery) and, when the pdi MCP server is
   connected, record_decision with links.chg and the answer as a quote; decision mark with the DEC id.
4. brief.md from the template with the contract's header (Z2a); decision_record.py check validates it. At the end:
   branch pdi/CHG-n-discovery, commit with trailer "Change: CHG-n", PR, phase_run.py gate request --change CHG-n
   --gate B0 --url <PR>.
5. phase_run.py: `discovery` in PHASES refuses `run` with a message that it is interactive and names the command;
   build_prompt for intent reads brief.md when it exists and treats it and the discovery decisions as binding input.
6. Regenerate the pinned pdi contract copy from the new contract-v tag (as tf #93 does). Docs: mode-pdi GUIDE.md, CHANGELOG.

Tests: the command's script parts (brief header and check, gate request B0, decision add with tag discovery), phase_run
refusing to run discovery, intent prompt with and without brief.md, the contract copy. Then one interview on
dbqm45/sdlc-proba (a small idea) through brief, B0 and the intent PR; record what worked and what did not in pdi
docs/przebieg-lokalny.md (new section).
Gates: the repo's checks (workspace.py check --packs pack-it, mode-pdi tests, skill evals if the skill is covered). GitHub
Actions do not run on this account right now — run the gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z8a — pdi + tf: fazy w kontenerze

```text
Implement step Z8a of docs/plan-zespol-jednoosobowy.md (§8.2) in dbqm45/pdi, with the tf part in dbqm45/tf (attach it
with push access), under decision DZ9 in docs/decyzje.md. Answer me in Polish; code, commits and PR titles in English.

Goal: in local mode (PDI_DISPATCH=local) the persona and talos run inside a container that sees only the clone of the
product repo. They cannot read the owner's home directory, ~/.sdlc/env, ~/.ssh, other repos or keys, and can reach
only an allowlist of network hosts. Steps that need credentials (git push, gh pr create, phase_run.py gate request,
pushing talos cut branches) stay outside the container, as today.

Today: src/pdi/dispatch_local.py execute() runs the steps of sdlc-phase.yml on the host; step "run" is
`phase_run.py run` (claude --print --agent <persona> --permission-mode acceptEdits), with a filtered environment
(base, problem_env, claude_env) but full filesystem and network access. sdlc up (src/pdi/stack/) already requires
Docker. In GitHub Actions (tf modes/mode-pdi/.../templates/sdlc-phase.yml) the runner is ephemeral, but the persona
step still sees GITHUB_TOKEN through the checkout's credentials.

1. Plan first in docs/plan-z8a-izolacja-faz.md (pdi): image, mounts, network, authentication of claude inside the
   container, what stays on the host, tests. TDD.
2. Image: built by `sdlc up` (or pulled, pinned by digest), with the claude CLI pinned to the version sdlc-phase.yml
   uses, python3, node, git and the product's build tools when detectable; non-root user; no secrets baked in.
3. Run step: `docker run --rm` with only the clone mounted read-write at its path (worktree-safe), no home mount,
   read-only root filesystem where possible, a CPU/memory/time limit, and the environment of today's "run" step and
   nothing else. Claude authentication: a token passed only to this container (ANTHROPIC_API_KEY or a long-lived
   CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token`; set only one of the two, they conflict), never written into the log
   or the image. Handle the reported first-run issue where the token is ignored until onboarding is marked complete
   (`hasCompletedOnboarding` in ~/.claude.json inside the container); confirm it against the current docs.
4. Network: an allowlist (Anthropic API, package registries the product uses, the semgrep rule registry for Z8c) through
   an egress proxy container or an internal Docker network; Claude Code sandbox settings (network.allowedDomains,
   filesystem.denyRead, sandbox.failIfUnavailable: true) as a second layer, passed by pdi with --settings (settings in
   the product repo cannot loosen restrictions, and the repo is not trusted). A blocked host shows in the run
   log with the step and the host.
5. Configuration: PDI_DISPATCH_SANDBOX=docker (default once this lands) | none (explicit, logged as a warning at every
   run). Without Docker, sdlc up and the dispatch refuse with a clear message instead of falling back silently.
6. Actions (tf sdlc-phase.yml): checkout with persist-credentials: false before the persona step, GITHUB_TOKEN only in
   the push/PR steps, the same Claude Code sandbox settings.
7. Docs: README (local mode and its isolation), docs/plan-zespol-jednoosobowy.md §10, the local run checklist
   (docs/przebieg-lokalny.md).

Tests: the docker argv (mounts, no home, env, limits, network) for each phase with an injected runner; refusal without
Docker; `none` mode warns; tokens never in the log; Actions template keeps credentials out of the persona step. Then a
local run on dbqm45/sdlc-proba: the intent phase passes inside the container, and a persona told to read ~/.sdlc/env or
call a host outside the allowlist fails visibly in the log. Record the result in docs/przebieg-lokalny.md.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the
repo's checks. GitHub Actions do not run on this account right now — run the gates locally and say so in the PRs.
Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z8c-1 — ci_for_sdlc: wyniki skanera (SARIF) jako ustalenia

```text
Implement part 1 of step Z8c of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md
§8.2 (Z8c) and decision DZ11 in docs/decyzje.md (Semgrep with OWASP rules plus the package manager's dependency audit;
both results as SARIF). Answer me in Polish; code, commits and PR title in English, Conventional Commits.

Goal: the gate reads security scan results the way it reads JUnit XML today (G4, --tests): `npm run analyze -- --repo
<path> --sarif <file or directory>` turns findings into findings of the items they touch, and a blocking one fails the
gate and shows as an annotation on the file and line.

1. Plan first in docs/ (SECURITY-SCAN-PLAN.md: files, order, rules, tests). TDD.
2. Reader for SARIF 2.1.0 (results, rule ids, levels, locations), limits like the JUnit reader (size, count), a file
   that cannot be read fails the gate (as for --tests: a scan that did not run is never "no findings").
3. Mapping to items: a result on a file a change's slice touched (the slice's commits with `Change: TSK-n`, or the PR's
   diff in CI) belongs to that slice; otherwise to the change. New rules: SEC-001 blocking (SARIF level error, or
   warning with a CWE from the OWASP Top 10 list), SEC-002 warning (other warnings), SEC-003 info (notes). Policy
   `actions` and `disabledRules` apply as for every rule.
4. In GitHub Actions: annotations on the result's file and line, a table in the run summary. Docs: docs/REPO-CHANGES.md,
   README, and docs/templates/change-check.yml with an optional scan step (semgrep scan --config p/owasp-top-ten --sarif
   and the dependency audit converted to SARIF) and SARIF_REPORTS like TEST_REPORTS.
5. The result for pdi: blocking security findings count as blocking for readiness (--send-to-pdi unchanged otherwise).

Tests: SARIF reader (valid, malformed, too big), mapping by file to slice and change, SEC-001/002/003 levels and the
OWASP CWE list, gate exit codes and annotations, the template line. Gates: npm test, npm run typecheck,
npm run test:contract, npm run lint:commit. GitHub Actions do not run on this account right now — run the gates
locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z8c-2 — tf: skaner w pętli kawałka talosa i w CI

```text
Implement part 2 of step Z8c of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md
§8.2 (Z8c), decision DZ11 in docs/decyzje.md. Start when Z8c-1 (ci_for_sdlc --sarif) is merged. Answer me in Polish;
code, commits and PR title in English, Conventional Commits.

Goal: talos does not commit a slice with a blocking security finding, the same way it does not commit a red test, and
the product repo's CI runs the same scan on every PR.

Today: modes/mode-talos/skills/talos-story-run, section "Pętla kawałka": red test → smallest code → verification (plan
command, tests, lint, types from CLAUDE.md; `BRAMKA K<n>: PASS | FAIL (…, próba k/2)`) → scope review → commit.
Hooks (core/hooks): tdd_guard, scan_secrets, guard_bash, guard_paths; there is no vulnerability scan.

1. Plan first in docs/plans/ (files, order, tests). TDD for the scripts.
2. A scan script (stdlib Python, like the other mode scripts): semgrep on the slice's changed files with the OWASP rules
   (and the product's own .semgrep.yml if present), the dependency audit only when a manifest or lock file changed
   (npm audit / pip-audit, by detected stack), output SARIF into the run directory. A missing scanner is a clear FAIL
   with the install command, never a silent pass. Check on a clean install, without a Semgrep login, whether the
   p/owasp-top-ten registry rules download; if not, vendor the rules into the mode and pin their version.
2a. One verification script (N3 of the plan): the product's single command for format, lint, types, tests and this scan,
   named in the first line of the product's CLAUDE.md and used unchanged by talos and by CI.
2b. Dependency cooldown (N10): set the package manager's minimum release age to 7 days in the product (npm
   min-release-age, pnpm minimumReleaseAge in minutes, Yarn npmMinimalAgeGate, uv exclude-newer), lock files committed;
   adding a version younger than that stops the slice with an explanation. Mind the known pnpm 11 issue with
   Dependabot and --frozen-lockfile.
3. Verification step of the slice loop: the scan runs after tests; a blocking finding (ERROR, or WARNING with an OWASP
   Top 10 CWE — the same rule as ci_for_sdlc SEC-001) is a FAIL of that attempt with the finding (rule, file, line)
   fed back into the next attempt; after 2 attempts STOP like a red test. Findings below blocking go into the run report.
4. CI: the sdlc-phase / change-check templates in mode-pdi run the scan on the PR and pass the SARIF to ci_for_sdlc
   (`--sarif`, Z8c-1). Container allowlist for the semgrep rule registry is part of Z8a; note it in the docs.
5. Docs: talos-story-run, mode-pdi GUIDE.md, CHANGELOG.

Tests: the scan script (changed files only, manifests trigger the audit, SARIF written, missing scanner fails), the
verdict rule (blocking vs not), the loop's FAIL and STOP path with an injected scanner, the template step. Then one
talos slice on dbqm45/sdlc-proba with a deliberate SQL injection in the acceptance test's path: it fails, is fixed in the
second attempt and only then committed; record it in pdi docs/przebieg-lokalny.md. Gates: the repo's checks (workspace.py
check --packs pack-it, mode tests, skill evals if covered). GitHub Actions do not run on this account right now — run the
gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

