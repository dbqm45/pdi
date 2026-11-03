# Polecenia startowe planu „zespół jednoosobowy”: grupa A i Z2

**Data:** 2026-11-02 · **Źródło:** [plan „zespół jednoosobowy”](plan-zespol-jednoosobowy.md) §8, §8.2, decyzje DZ1–DZ14
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `e2cec98` (kontrakt 0.10.0), tf 5.55.0, ShipScope 0.2.67

Każde polecenie wklejasz jako pierwszą wiadomość nowej sesji Claude Code w katalogu z tabeli. Kroki idą po kolei: Z1,
potem Z2a, potem Z2b. Zgodnie z DZ5 Z1 idzie przed etapem 2, a Z2 przed etapem 3 ([etapy](polecenia-startowe-sdlc-lokalnie.md)).
Z8a i Z8c (uprząż) też idą przed etapem 2, czyli przed pierwszym przebiegiem na prawdziwym kodzie sprintdecka; Z8a
jest niezależny od Z1, a Z8c ma dwie części: najpierw Z8c-1 (ci_for_sdlc), potem Z8c-2 (tf).

| Krok | Co | Startuje po | Repo | Sesja w katalogu | Stan |
|---|---|---|---|---|---|
| [Z1](#z1--pdi--tf-wszystkie-decyzje-zmiany-w-każdej-fazie-domknięcie-prb-3) | wszystkie decyzje zmiany w każdej fazie (domknięcie PRB-3) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | zrobione (pdi #110, tf #135, #136) |
| [Z2a](#z2a--pdi-faza-discovery-i-bramka-b0-w-kontrakcie-i-przebiegu) | faza `discovery` i bramka B0 w kontrakcie i przebiegu | Z1 | pdi | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2b](#z2b--tf-wywiad-discovery-w-mode-pdi) | wywiad `/discovery` w mode-pdi; intencja z briefu | Z2a i tag kontraktu | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z8a](#z8a--pdi--tf-fazy-w-kontenerze) | fazy w kontenerze (izolacja persony i talosa) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | zrobione (pdi #111, tf 5.56.0), [plan](plan-z8a-izolacja-faz.md) |
| [Z8c-1](#z8c-1--ci_for_sdlc-wyniki-skanera-sarif-jako-ustalenia) | wyniki skanera (SARIF) jako ustalenia w ci_for_sdlc | — | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` | zrobione (ci_for_sdlc #109) |
| [Z8c-2](#z8c-2--tf-skaner-w-pętli-kawałka-talosa-i-w-ci) | skaner w pętli kawałka talosa i w CI | Z8c-1 | tf | `/Users/x/WebstormProjects/tf` | zrobione (tf #138; bez przebiegu na sdlc-proba, [lista](przebieg-lokalny.md#4-dostarczenie-talos)) |
| [N1](#n1--tf-przegląd-drugim-modelem) | przegląd drugim modelem (wymagania, plan, uwagi z review) | Z1 | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [N5](#n5--tf-evale-przebiegu) | evale przebiegu na 20 prawdziwych zadaniach | Z1 | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z7b-1a](#z7b-1a--pdi--tf-cele-zmiany-w-kontrakcie-i-planie) | cele zmiany (`targets`) w kontrakcie i planie, B3 | Z1 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z7b-1b](#z7b-1b--ci_for_sdlc-sprawdzanie-celów-zmiany) | sprawdzanie celów (pokrycie, testy mutacyjne) w ci_for_sdlc | Z7b-1a, Z8c-1 | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` | do zrobienia |
| [N2](#n2--pdi--tf-pętla-budujący-recenzent-na-pr-i-samonaprawa-ci) | pętla budujący–recenzent na PR i samonaprawa CI | Z8a, N1 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z3-lokalnie](#z3-lokalnie--pdi--tf-konsola-w-przeglądarce-na-macu) | konsola w przeglądarce na Macu: trzy pasy, ślad, postęp na żywo, decyzje przyciskami (DZ14) | A6 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |

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

Startuje po Z1 (zrobione). Sesja w klonie pdi; część tf to Z2b, po tagu kontraktu. **Stan przed startem
(2026-11-03):** pdi `084c104` (kontrakt 0.11.0), tf 5.57.0. Od pierwszej wersji tego polecenia weszły: Z1 (odpowiedzi
na pytania bramki w decyzji i decyzje z `links.chg` w każdej fazie), Z8a (krok `run` w kontenerze), Z8c-2; CI na
GitHubie znowu działa.

```text
Implement step Z2a of docs/plan-zespol-jednoosobowy.md (§3, §8) in dbqm45/pdi, under decisions DZ1 and DZ3 in
docs/decyzje.md: the interview runs first in a Claude chat with the pdi MCP server, not in a new service; its skills are
tf's (core-plan-interview, proc-product-discovery). Answer me in Polish; code, commits and PR title in English.

Goal: a change can start with an interview. Triage can accept a problem or idea "with discovery"; pdi then does not
dispatch a non-interactive phase but puts "interview waiting for you" in the inbox, with the exact command to start it.
The interview ends with brief.md and gate B0; approving B0 starts the intent phase as today.

Today (check each against the code before planning): src/pdi/flow.py GATES starts at B1 (produced_by intent);
triage_problem accepted creates CHG-n and dispatches intent (src/pdi/problems.py `triage` and `_accept`,
src/pdi/dispatch.py, src/pdi/dispatch_local.py with PRIOR_ARTIFACT and GATES); the contract is 0.11.0 and
contract/change.schema.json already allows phase `discovery`; protected autonomy types live in contract.json
`autonomy.protected_types` and are forced to level 3 in contract/autonomy.schema.json.

Already done (read first, do not redo): Z1 (docs/plan-z1-decyzje-w-fazach.md) — gate items carry the artifact's
`questions` and decide_inbox_item takes `answers`; every recorded decision with links.chg = the change reaches each tf
phase (src/pdi/phase_decisions.py, `decision import` in tf) and its prompt as quoted data. So B0 questions, their
answers and decisions recorded during the interview reach intent and later phases with no extra work: reuse that path,
do not build a second one.

1. Plan first in docs/plan-z2a-discovery.md (files, order, contract change, tests, what Z2b does in tf). TDD.
2. Contract: the next free minor version at the time of your PR (0.12.0 unless another open PR, e.g. Z7b-1a, already
   takes it — check open pdi PRs and coordinate the number); contract-v tag after merge, then tf regenerates its pinned
   copy in Z2b (as tf #136 did). Add: phase `discovery` and gate `B0` ("brief approved") in contract.json conventions;
   artifact `docs/project/changes/<CHG>/brief.md` with the same flat YAML header as intent.md (change, status, source)
   and the brief's sections (problem, outcome and its metric, users, scope, out of scope, constraints, open risks,
   `## Pytania do bramki`); the triage decision may carry start_with: intent | discovery; examples and
   contract/README.md.
3. Flow: Gate("B0", produced_by="discovery", next_phase="intent"), in the chain before B1 only for changes that start
   with discovery (missing_before must not ask a plain change for B0). B0 is a scope decision: make its decision type
   protected (always human, like scope.r1, DA2) in contract.json and autonomy.schema.json, and say so in the plan.
4. Triage: triage_problem gets start_with (default intent, so nothing changes). With discovery: create the change state,
   no dispatch, an inbox item kind discovery for the change with the command for the product repo (`/discovery CHG-n`
   in Claude Code, Z2b) and the problem's fields as data; list_changes and get_change show "waiting: discovery".
   gate.requested B0 from tf closes that item and opens the B0 gate (with the brief's questions, as any gate since Z1);
   approving it dispatches intent with the triage and interview decisions as linked decisions (Z1). The intent phase of
   a discovery change needs brief.md on the ref (dispatch_local PRIOR_ARTIFACT, like the other phases), and tf reads it
   in Z2b; pdi only passes the change.
5. Interview answers are decisions: record_decision with links.chg, kind product, tag discovery, the human's answer as a
   quoted evidence (the conversation is not stored, as in A5). Z1 already brings them to later phases.
6. If the local console of Z3-lokalnie is merged by then, show the discovery item and B0 there too (same read model, no
   new code path); otherwise note it for Z3-lokalnie in the plan.
7. Docs: README (start with an interview), integrations/claude-code/README.md, docs/przebieg-lokalny.md (a checklist
   item for me: one idea accepted with discovery, the interview in Claude, B0 with one answered question, intent
   starts and does not ask it again), docs/plan-zespol-jednoosobowy.md §10 and the Z2a row of
   docs/polecenia-startowe-zespol.md.

Tests: contract schemas and examples (brief header, B0, start_with, protected type), flow (B0 only in discovery changes,
next phase intent), triage with and without start_with (without it everything as today), the discovery inbox item and
its closing by gate.requested B0, approving B0 dispatches intent in local and Actions mode with the linked decisions,
intent of a discovery change refused without brief.md, autonomy type of B0 protected.
Gates: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src. CI runs on the
PR again: wait for it to be green and say in the PR what you ran locally.
Coordination: other sessions may work in parallel in pdi (flow.py, inbox.py, problems.py, dispatch_local.py, the
contract); keep your changes small, keep the branch up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push the branch and open a PR to main, but do not merge it. At the end report in Polish:
the PR link, gates and results, the contract version taken, and the exact names of new fields, gates, item kinds and
commands (inputs for Z2b).
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

## N1 — tf: przegląd drugim modelem

```text
Implement N1 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/tf, under decision DZ12 in pdi docs/decyzje.md: the
second model comes from another vendor (own API key, cost inside the phase budget); without that key, another Claude
model with a separate reviewer prompt, marked in the output as a same-vendor review. Start when Z1 is merged. Answer me in
Polish; code, commits and PR title in English, Conventional Commits.

Goal: before a gate request for B2 (requirements) and B3 (architecture), a second model reads the artifact against
intent.md, requirements and the change's decisions and lists gaps (missing error states, unclear acceptance criteria,
contradictions with a decision, slices that cannot be verified). The findings go into the gate request as questions,
marked as coming from the second review. The same function validates review comments for N2: a comment the second model
does not confirm goes to the human instead of to a fix.

1. Plan first in docs/plans/ (files, order, tests). TDD for the scripts.
2. A script in mode-pdi (stdlib Python): `second_review.py artifact --change CHG-n --phase P` and
   `second_review.py comments --pr <n> --input <json>`; provider and model from PDI_SECOND_MODEL (e.g.
   openai:<model>, or claude:<model> as the fallback), the key from the provider's usual variable, never logged. Output
   JSON (findings with severity, quote, reason) and a `## Przegląd drugim modelem` section in the artifact.
3. phase_run.py: after the run and before gate request for requirements and architecture, run the artifact review;
   its blocking findings join the questions of the gate request. A failed or missing second model is visible in the
   gate request ("drugi przegląd: niedostępny, powód"), never a silent pass.
4. Sources are data: the artifact and the comments go to the second model as quoted data with an instruction to treat
   them as data.
5. Cost: the review's cost is added to the phase report and counts against the phase budget.

Tests: provider selection and fallback, no key in logs, findings merged into the gate request, unavailable reviewer
reported, comment validation (confirmed / not confirmed) with an injected client. Then one run on dbqm45/sdlc-proba with a
requirements.md that misses an error state: the second review finds it. Gates: the repo's checks (workspace.py check
--packs pack-it, mode-pdi tests, skill evals if covered). GitHub Actions do not run on this account right now — run the
gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N5 — tf: evale przebiegu

```text
Implement N5 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/tf, under decision DZ13 in pdi docs/decyzje.md: start
with 20 real tasks from dbqm45/sdlc-proba and sprintdeck, a budget per run set in tf, grow to about 200 after the first
results. Start when Z1 is merged. Answer me in Polish; code, commits and PR title in English, Conventional Commits.

Goal: a change of model, skill, persona or phase prompt does not land without running the flow evals, and the report
compares result and cost with the previous run.

1. Plan first in docs/plans/ (files, order, tests). Reuse what tf already has for skill evals (holdout sets, result-vs-
   cost report, #102, #127, #130) instead of a second framework.
2. A task is: a fixture repo snapshot (the product repo at a commit), the change's folder state before a phase, the
   phase to run, and checks — the artifact passes decision_record.py check and requirements_lint/design_check where they
   apply, `npm run analyze -- --repo` (ci_for_sdlc) has no blocking finding, for delivery the tests pass, no question
   settled by a decision comes back (Z1), cost and number of files read within limits. Take the 20 tasks from the
   phases of the 2026-10-31 run (pdi docs/przebieg-lokalny.md) and from sprintdeck history; store them in tf.
3. Runner: runs phase_run.py for each task (in the container of Z8a when available), collects result, cost, tokens,
   files read, time; report as Markdown and JSON with the comparison to the previous run.
4. Trigger: a workspace.py command and a CI job on changes to personas, mode-pdi prompts or the pinned model; locally the
   command. A change that lowers the pass rate or raises cost by more than a set limit fails with the report.

Tests: task loading and validation, checks per phase, the comparison and the failure limits, with an injected runner.
Then one real run of the 20 tasks; record pass rate and cost in the PR. Gates: the repo's checks. GitHub Actions do not
run on this account right now — run the gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z7b-1a — pdi + tf: cele zmiany w kontrakcie i planie

```text
Implement part 1a of Z7b of docs/plan-zespol-jednoosobowy.md (§8.1, Z7b-1 in §0) in dbqm45/pdi, with the tf part in
dbqm45/tf (attach it with push access), under decisions DZ6 and DZ7 in docs/decyzje.md: the architect persona (tomasz)
proposes the change's targets in the plan, the human approves them at B3; for AI products evaluation thresholds are
mandatory. Start when Z1 is merged. Answer me in Polish; code, commits and PR titles in English.

Goal: every change carries measurable quality targets, approved at B3 and checked before B4, instead of judging PRs by
eye.

1. Plan first in docs/plan-z7b-cele.md (pdi). TDD.
2. Contract (next free minor version, contract-v tag after merge): `targets` in release-plan.schema.json (or a sibling
   schema linked from it): coverage of changed code (min %, with explicit exclusions), mutation score on changed code
   (min %; tools: StrykerJS for JS/TS, mutmut for Python, per N4), optional performance budgets (name, metric, limit),
   evaluation thresholds for AI features (eval set, metric, min). Examples and contract/README.md.
3. tf: the architecture phase writes `targets` with a short justification per target; plan.md template and
   decision_record.py check validate them against the contract copy (regenerated from the new tag, as tf #93 does).
4. pdi: the B3 gate shows the targets; approve-for-implementation and B4 show their status once ci_for_sdlc reports it
   (Z7b-1b); get_change and get_trace include them.
5. Docs: contract/README.md, README, plan §10.

Tests: schema and examples, tf template and check (missing or malformed targets), pdi gate items with targets. Gates:
pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the repo's
checks. GitHub Actions do not run on this account right now — run the gates locally and say so in the PRs. Commit and PR
on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z7b-1b — ci_for_sdlc: sprawdzanie celów zmiany

```text
Implement part 1b of Z7b of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md §8.1
and §0 (Z7b-1), the contract change of Z7b-1a (targets) and N4 in §8.3. Start when Z7b-1a and Z8c-1 are merged. Answer me
in Polish; code, commits and PR title in English, Conventional Commits.

Goal: the gate checks a change's `targets` against real reports, the way it reads JUnit (--tests) and SARIF (--sarif)
today, so a change below its targets is not ready for B4.

1. Plan first in docs/ (TARGETS-PLAN.md). TDD.
2. Inputs: `npm run analyze -- --repo <path> --coverage <lcov or cobertura> --mutation <Stryker JSON or mutmut
   results>` plus the change's `targets` from release.yaml. Readers with size limits; an unreadable or missing report
   for a set target fails the gate (a check that did not run is never "met").
3. Rules: TGT-001 coverage of changed code below target (blocking), TGT-002 mutation score on changed code below target
   (blocking), TGT-003 performance budget exceeded (warning unless the target says blocking), TGT-004 evaluation
   threshold not met for an AI feature (blocking). Changed code = the change's slices' files (commits with
   `Change: TSK-n`) or the PR diff in CI.
4. Readiness to pdi (--send-to-pdi) carries the targets' status; annotations on files in GitHub Actions; the
   change-check template gains optional coverage and mutation steps.

Tests: readers (valid, malformed, too big), changed-code filtering, TGT-001…004, exit codes and annotations, readiness
payload. Gates: npm test, npm run typecheck, npm run test:contract, npm run lint:commit. GitHub Actions do not run on
this account right now — run the gates locally and say so in the PR. Commit and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N2 — pdi + tf: pętla budujący–recenzent na PR i samonaprawa CI

```text
Implement N2 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/pdi, with the tf part in dbqm45/tf (attach it with
push access). Start when Z8a (phases in a container) and N1 (second review) are merged. Answer me in Polish; code,
commits and PR titles in English.

Goal: a talos PR reaches the human only with green checks and closed review comments, or with a clear "not done after
N rounds" and the reason. Background: Spotify's Honk opens a PR only after full verification kept apart from the agent
(engineering.atspotify.com, 2025-11); verify the details before relying on them.

1. Plan first in docs/plan-n2-petla-pr.md (pdi). TDD.
2. After delivery, per talos PR: AI review (tf REVIEW.md) → comment validation by the second model (N1) → talos fixes
   only the validated comments → re-review; at most 2 rounds (as DZ6), then the PR goes to the human with the open
   comments. Unvalidated comments go to the human as questions, not to a fix.
3. Red checks: the agent reads the failing log (local verification script of N3 while Actions do not run; CI log
   later), fixes, re-runs, waits for green; the same round limit. Every round runs in the container of Z8a.
4. pdi: the change state gets `pr_loop` per PR (round, status: reviewing | fixing | green | needs_human, last reason);
   the inbox shows "PR gotowy do Twojego przeglądu" only when green or when the limit is reached; get_trace shows the
   rounds; cost per round in the phase report and budget.
5. Docs: README, integrations/claude-code/README.md, mode-pdi GUIDE.md.

Tests: the round loop with injected review, validation and fix steps (green after 1 round, limit reached, unvalidated
comments to the human), red check fix path, state and inbox items, cost accounting. Then one run on dbqm45/sdlc-proba with
a talos PR that has one real review finding and one false one: the real one is fixed, the false one goes to the human.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the
repo's checks. GitHub Actions do not run on this account right now — run the gates locally and say so in the PRs. Commit
and PR on my request.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```


## Z3-lokalnie — pdi + tf: konsola w przeglądarce na Macu

Decyzja DZ14. Startuje po A6 (ponowny przebieg na `sdlc-proba`), przed etapem 2. Sesja w klonie pdi; część tf
osobnym PR-em. Wygląd: `design/konsola/v2-klikalna/` (trzy pasy). **Stan przed startem (2026-11-03):** pdi `f6c5533`
(kontrakt 0.11.0), tf 5.57.0. Od pierwszej wersji tego polecenia weszły: Z1 (odpowiedzi na pytania bramki, decyzje
zmiany w fazie), Z8a (krok `run` w kontenerze Docker), Z8c-2 (skaner w pętli talosa); CI na GitHubie znowu działa.

```text
Implement Z3-lokalnie of docs/plan-zespol-jednoosobowy.md (§0 row A7, §5, decision DZ14 in docs/decyzje.md) in
dbqm45/pdi, with the tf part in dbqm45/tf (attach it with push access). Answer me in Polish; code, commits and PR titles
in English.

Goal: on my Mac I follow and drive a whole change in the browser instead of the Claude console: I see where each change
is (the three lanes), its steps, what runs in the background right now with a live progress indicator, and I decide at
gates with buttons. No production service yet (that is Z3 after DA4), no chat, no notifications.

Read first: docs/plan-zespol-jednoosobowy.md §0, §5, §8.1 (Z7a, the three lanes) and §6; design/konsola/README.md and the
clickable mock-ups in design/konsola/v2-klikalna/ (Main = board in three lanes, Slad = change trace with steps,
Decyzje = decision register, Autonomia); contract/README.md and contract/event.schema.json (`run.progress`, $defs
run_progress); src/pdi/stack/cli.py (`sdlc up/down/status/open`), src/pdi/receiver.py and src/pdi/form.py (the existing
HTML pages without scripts, the per-start token), src/pdi/dispatch_local.py (phase runs: runs/<CHG>-<phase>-<time>.log
and .result.json; `_stream_run` already passes every output line to the log as it comes), src/pdi/phase_sandbox.py
(Z8a: the `run` step runs in a Docker container that sees only the product clone, not runs/), src/pdi/inbox.py,
src/pdi/trace.py, src/pdi/changes.py, src/pdi/mcp_server.py (what the MCP tools read and how decide_inbox_item decides,
including `answers` from Z1); docs/plan-z1-decyzje-w-fazach.md and docs/plan-z8a-izolacja-faz.md; in tf mode-pdi
`phase_run.py` (how the persona is started: `claude --print --output-format json`, `--settings $PDI_CLAUDE_SETTINGS`).

Already done (do not redo): gate items carry `questions`, and decide_inbox_item takes `answers` [{question, answer}]
checked against them (Z1, contract 0.11.0); the persona runs in a container with an egress proxy (Z8a); talos blocks
slices with security findings (Z8c-2).

1. Plan first in docs/plan-z3-lokalnie.md: files in both repos, order, tests, sources with dates, what stays for Z3. TDD.
2. tf (live progress): run the persona with streaming output (`--output-format stream-json`; check in the official
   Claude Code docs which flags it needs with --print, e.g. --verbose, and what each event carries, including the final
   result event that replaces today's JSON result) and turn the stream into progress lines: phase, step, status as in
   `run.progress` (started / in_progress / waiting_gate / done / failed), elapsed time, cost so far, the last action in
   plain words ("czyta plik X", "uruchamia testy", "pisze PR"). Because the run step is in a container that cannot see
   runs/ (Z8a), print the progress lines to stdout with a fixed prefix (one JSON object per line); pdi on the host
   picks them out of the streamed output. The final JSON result of `phase_run.py run` (status, cost_usd, detail,
   repeated_question from Z1) must stay exactly as today. Never put prompt text, file contents, decision texts or
   secrets into progress lines. Keep sdlc-phase.yml working (the progress lines simply go to the job log there).
3. pdi (progress on the host): dispatch_local writes the prefixed lines from the run step into
   runs/<…>.progress.jsonl next to the log (validated against run_progress, anything else ignored) and keeps them out
   of the plain log; settle() and get_change show the last progress line.
4. pdi (console): a local web console started by `sdlc up` (stopped by `sdlc down`, shown by `sdlc status` and opened by
   `sdlc open`), bound to 127.0.0.1 only, with a per-start token in the URL (as the problem form). Prefer the standard
   library as the receiver does, unless the plan shows a reason; threaded server, Server-Sent Events for live updates.
   Pages, following the v2 mock-ups:
   a. Board: every change in its lane and step (lane 1 Zaprojektuj i zbuduj, lane 2 Oceń i wydaj, lane 3 Wdróż,
      obserwuj, ulepszaj), "waiting for you" highlighted, a running phase with a live progress bar.
   b. Change trace: the steps of one change with state, decisions (with their answers), PRs, deployments and flag
      stages (what get_trace gives); the running phase shows its progress lines live and links the run log.
   c. Inbox: gate items with the draft, the artifact's questions with an answer field each (sent as `answers`), and
      buttons (approve / changes requested / reject, with a note). A button decision goes through the same code path as
      decide_inbox_item (one implementation, same checks, the PR-merged check of PRB-2 included), records who decided,
      that it came from the console (source.kind console) and drafted_by/draft_edited; a decision on a stale item
      (state changed meanwhile) is refused with a message.
   d. Decision register and autonomy report as read-only pages.
   Security: every value escaped (decision texts, questions and log lines are data), no inline scripts, a
   Content-Security-Policy, POSTs only with the token and a same-origin check, nothing listens outside 127.0.0.1, no
   secret ever reaches a page.
5. Docs: README, docs/przebieg-lokalny.md (the next run can be followed in the console; add a checklist item for me),
   integrations/claude-code/README.md, tf mode-pdi GUIDE.md.

Tests: stream-json to progress lines (from recorded sample streams, including a failed run, a run waiting at a gate and
a repeated_question failure), the unchanged final result, the host-side split of progress lines from the log, the
console's read model (lane and step of a change from registry states), SSE updates when a progress file grows, button
decisions (same result as decide_inbox_item, with answers, refused without token, refused for a stale item), escaping
and CSP, `sdlc up/down/status` with the console.
A local run on dbqm45/sdlc-proba needs my Mac (Docker, logged-in gh and claude): add it as a checklist item for me in
docs/przebieg-lokalny.md — one change followed only in the console, from intake to the first gate, a decision by button
(with an answer to one question) and the next phase visible live.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the
repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, the skill gate of pdi-decisions). CI runs on the
PRs again: wait for it to be green and say in the PRs what you also ran locally.
Coordination: other sessions may work in parallel in pdi src/pdi/dispatch_local.py and tf phase_run.py; keep your
changes there small, keep your branches up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push branches and open PRs to main (tf first if pdi depends on it), but do not merge them.
At the end report in Polish: PR links, gates and results, the merge order, and the exact names of new commands,
files, fields and variables.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```
