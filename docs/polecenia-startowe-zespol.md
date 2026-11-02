# Polecenia startowe: Z1 i Z2 planu „zespół jednoosobowy”

**Data:** 2026-11-02 · **Źródło:** [plan „zespół jednoosobowy”](plan-zespol-jednoosobowy.md) §8, decyzje DZ1–DZ5
([decyzje](decyzje.md)) · **Stan przed startem:** pdi `e2cec98` (kontrakt 0.10.0), tf 5.55.0, ShipScope 0.2.67

Każde polecenie wklejasz jako pierwszą wiadomość nowej sesji Claude Code w katalogu z tabeli. Kroki idą po kolei: Z1,
potem Z2a, potem Z2b. Zgodnie z DZ5 Z1 idzie przed etapem 2, a Z2 przed etapem 3 ([etapy](polecenia-startowe-sdlc-lokalnie.md)).

| Krok | Co | Startuje po | Repo | Sesja w katalogu | Stan |
|---|---|---|---|---|---|
| [Z1](#z1--pdi--tf-wszystkie-decyzje-zmiany-w-każdej-fazie-domknięcie-prb-3) | wszystkie decyzje zmiany w każdej fazie (domknięcie PRB-3) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2a](#z2a--pdi-faza-discovery-i-bramka-b0-w-kontrakcie-i-przebiegu) | faza `discovery` i bramka B0 w kontrakcie i przebiegu | Z1 | pdi | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2b](#z2b--tf-wywiad-discovery-w-mode-pdi) | wywiad `/discovery` w mode-pdi; intencja z briefu | Z2a i tag kontraktu | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |

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
```
