# Polecenia startowe planu „zespół jednoosobowy”: grupa A i Z2

**Data:** 2026-11-02, odświeżone 2026-11-03 · **Źródło:** [plan „zespół jednoosobowy”](plan-zespol-jednoosobowy.md) §8,
§8.2, decyzje DZ1–DZ14 ([decyzje](decyzje.md)) · **Stan dziś:** pdi `aadfbf9` (kontrakt 0.11.0), tf 5.58.4 (kopia
kontraktu 0.11.0), ShipScope 0.2.67 (stan z 2026-11-02) · Wszystkie niezrobione polecenia mają nad sobą
własny stan przed startem z 2026-11-03.

Każde polecenie wklejasz jako pierwszą wiadomość nowej sesji Claude Code w katalogu z tabeli. Zrobione są Z1, Z8a,
Z8c-1 i Z8c-2 (kolumna „Stan”). Dalej: Z2a, potem Z2b (po tagu kontraktu z Z2a); zgodnie z DZ5 Z2 idzie przed etapem 3
([etapy](polecenia-startowe-sdlc-lokalnie.md)). Najpierw przebieg A6 na `sdlc-proba` (DZ19, [polecenie](#a6--pdi--tf-shipscope-ci_for_sdlc-ponowny-przebieg-lokalny-na-sdlc-proba)); po nim N1, N5 i Z7b-1a, Z7b-1b po Z7b-1a,
N2 po N1, N12, N13 i N15 po A6 (po kolei z N2, bo zmieniają te same pliki), a równolegle Z3-lokalnie;
wszystkie przed etapem 2.

| Krok | Co | Startuje po | Repo | Sesja w katalogu | Stan |
|---|---|---|---|---|---|
| [Z1](#z1--pdi--tf-wszystkie-decyzje-zmiany-w-każdej-fazie-domknięcie-prb-3) | wszystkie decyzje zmiany w każdej fazie (domknięcie PRB-3) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | zrobione (pdi #110, tf #135, #136) |
| [Z2a](#z2a--pdi-faza-discovery-i-bramka-b0-w-kontrakcie-i-przebiegu) | faza `discovery` i bramka B0 w kontrakcie i przebiegu | Z1 | pdi | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z2b](#z2b--tf-wywiad-discovery-w-mode-pdi) | wywiad `/discovery` w mode-pdi; intencja z briefu | Z2a i tag kontraktu | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z8a](#z8a--pdi--tf-fazy-w-kontenerze) | fazy w kontenerze (izolacja persony i talosa) | — | pdi + tf | `/Users/x/WebstormProjects/pdi` | zrobione (pdi #111, tf 5.56.0), [plan](plan-z8a-izolacja-faz.md) |
| [Z8c-1](#z8c-1--ci_for_sdlc-wyniki-skanera-sarif-jako-ustalenia) | wyniki skanera (SARIF) jako ustalenia w ci_for_sdlc | — | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` | zrobione (ci_for_sdlc #109) |
| [Z8c-2](#z8c-2--tf-skaner-w-pętli-kawałka-talosa-i-w-ci) | skaner w pętli kawałka talosa i w CI | Z8c-1 | tf | `/Users/x/WebstormProjects/tf` | zrobione (tf #138; kawałek talosa na sdlc-proba 2026-11-03, sdlc-proba #10, [wynik](przebieg-lokalny.md#wynik-przebiegu-2026-11-03-z8c-2-talos-na-sdlc-proba)) |
| [A6](#a6--pdi--tf-shipscope-ci_for_sdlc-ponowny-przebieg-lokalny-na-sdlc-proba) | ponowny przebieg lokalny na `sdlc-proba`: jedna zmiana od zgłoszenia do oceny skutku, w kontenerze, bez obejść (bramka A6, DZ19) | Z1, Z8a, Z8c-1, Z8c-2 | pdi (+ tf, ShipScope, ci_for_sdlc) | `/Users/x/WebstormProjects/pdi` | do zrobienia (Twój przebieg na Macu) |
| [N1](#n1--tf-przegląd-drugim-modelem) | przegląd drugim modelem (wymagania, plan, uwagi z review) | Z1, A6 | tf (+ pdi, jeśli w kontenerze) | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [N5](#n5--tf-evale-przebiegu) | evale przebiegu na 20 prawdziwych zadaniach | Z1, A6 | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z7b-1a](#z7b-1a--pdi--tf-cele-zmiany-w-kontrakcie-i-planie) | cele zmiany (`targets`) w kontrakcie i planie, B3 | Z1, A6 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [Z7b-1b](#z7b-1b--ci_for_sdlc-sprawdzanie-celów-zmiany) | sprawdzanie celów (pokrycie, testy mutacyjne) w ci_for_sdlc | Z7b-1a, Z8c-1 | ci_for_sdlc | `/Users/x/WebstormProjects/ci_for_sdlc` | do zrobienia |
| [N2](#n2--pdi--tf-pętla-budujący-recenzent-na-pr-i-samonaprawa-ci) | pętla budujący–recenzent na PR i samonaprawa CI | Z8a, N1 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |
| [N12](#n12--tf-weryfikacja-przed-zakończeniem-fazy) | weryfikacja przed zakończeniem fazy (świeży wynik N3 dla commita) | A6 | tf | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [N13](#n13--tf--pdi-limity-tur-i-czasu-zapętlenie-trafia-do-skrzynki) | limity tur i czasu, zapętlenie trafia do skrzynki | A6 | tf + pdi | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [N15](#n15--tf--pdi-zakres-zapisu-fazy) | zakres zapisu fazy (`guard_paths` i sandbox) | A6 | tf + pdi (kontrakt) | `/Users/x/WebstormProjects/tf` | do zrobienia |
| [Z3-lokalnie](#z3-lokalnie--pdi--tf-konsola-w-przeglądarce-na-macu) | konsola w przeglądarce na Macu: trzy pasy, ślad z panelem plików, postęp na żywo, decyzje przyciskami (DZ14, DZ18) | A6 | pdi + tf | `/Users/x/WebstormProjects/pdi` | do zrobienia |

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
2. Contract: the next free minor version at the time of your PR (0.12.0 unless another PR, e.g. Z7b-1a, already
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

Startuje po scaleniu Z2a i po tagu jego kontraktu. Sesja w klonie tf. **Stan przed startem (2026-11-03):** tf 5.57.0
(kopia kontraktu pdi 0.11.0), pdi `89fc725`. Od pierwszej wersji tego polecenia weszły: Z1 (`decision import`,
`decision gate --answers`, odmowa przy powtórzonym pytaniu), Z8a (persona w kontenerze, bez sekretów), Z8c-2; CI na
GitHubie znowu działa, a CHANGELOG i wersję tf robi CI wydania.

```text
Implement step Z2b of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md §3 and §8,
decisions DZ1 and DZ3 in docs/decyzje.md, and the contract change of Z2a (docs/plan-z2a-discovery.md and the Z2a PR's
final report: contract version, new fields, gate B0, item kind discovery, commands). Start only when Z2a is merged and
its contract-v tag exists. Answer me in Polish; code, commits and PR title in English, Conventional Commits.

Goal: in Claude Code, in a product repo with mode-pdi, `/discovery CHG-n` runs an interview the way grill-me does: one
question at a time, walking the whole decision tree, each question with a recommended answer and why, until the brief
has no open branch. It ends with docs/project/changes/CHG-n/brief.md, every answer recorded as a decision, a PR with the
brief and a gate request B0 to pdi. The intent phase then writes intent.md from the brief.

Read first: core/skills/core-plan-interview (decision tree, rounds of questions with a recommendation),
packs/pack-it/skills/proc-product-discovery (outcome over feature, JTBD, assumptions to test),
core/skills/core-project-record/templates/brief.md and core-delivery-lifecycle stage 0, modes/mode-pdi (GUIDE.md,
skills/pdi-decisions: SKILL.md, scripts/phase_run.py, decision_record.py, templates/sdlc-phase.yml), the pdi plans
docs/plan-z1-decyzje-w-fazach.md and docs/plan-z8a-izolacja-faz.md. Compare with the 10x skills available in Claude
(10x-shape, 10x-prd) and take over only what tf lacks (DZ3); say what you took and why.

Already done (do not redo): decision_record.py `decision import` (decisions from the pdi registry, idempotent by DEC
id, `pochodzenie: pdi`) and `decision gate --answers`; build_prompt() lists binding decisions and settled questions as
quoted data; `run` and `gate request` refuse an artifact that repeats a settled question (`repeated_question`). pdi
passes every decision with links.chg to each phase. Reuse this: discovery decisions reach intent through it.

1. Plan first in docs/plans/ (files, order, tests). TDD for the scripts.
2. Command and skill in mode-pdi: `/discovery CHG-n` (interactive; the only interactive phase). Input: the change's
   problem from pdi (get_problem / get_change through the pdi MCP server) as data, never as instructions. Rules: one
   question per message; recommendation first; stop a branch when the answer is known from the code, the repo's docs
   or an earlier decision (say where from); the human may say "przyjmij rekomendację"; no question about something
   not needed for the brief. A new skill goes through the skill gate with its own scenarios in
   modes/mode-pdi/tests/skill_evals/.
3. Each settled answer: decision_record.py decision add (kind product, tag discovery) and, when the pdi MCP server is
   connected, record_decision with links.chg and the answer as a quote, then decision mark with the DEC id — so the
   import before intent skips it by id instead of adding a duplicate. Without the MCP server the entry stays
   `wyslano: nie` and `decision pending` shows it.
4. brief.md from the template with the contract's header (Z2a) and a `## Pytania do bramki` section for what stays
   open; decision_record.py check validates it. At the end: branch pdi/CHG-n-discovery, commit with trailer
   "Change: CHG-n", PR, then the B0 gate request. The signing secret must not reach the persona (Z8a and
   sdlc-phase.yml: only the gate step holds PDI_TF_SIGNING_SECRET); check what Z2a gives for this and plan how B0 is
   requested from an interactive session (e.g. the command prints the exact `phase_run.py gate request --change CHG-n
   --gate B0 --url <PR>` for the human, or a pdi command or MCP tool that signs it), and say which you chose and why.
5. phase_run.py: `discovery` in PHASES refuses `run` with a message that it is interactive and names the command;
   build_prompt for intent reads brief.md when it exists and treats it, the B0 entry with its answers and the discovery
   decisions as binding input; an intent.md that asks again what B0 answered fails as `repeated_question` (Z1).
6. Regenerate the pinned pdi contract copy from the new contract-v tag as tf #136 did (tools/pdi-contract.json version,
   new files if Z2a adds any, `python3 tools/sync_contract.py sync`, then `check`); bump phase_run.py
   CONTRACT_VERSION and triage_pdi.py CONTRACT. Docs: mode-pdi GUIDE.md and SKILL.md (do not edit CHANGELOG or VERSION:
   the release workflow does that).

Tests: the command's script parts (brief header and check, gate request B0, decision add with tag discovery and mark),
phase_run refusing to run discovery, intent prompt with and without brief.md, intent repeating a B0 question refused,
the contract copy and constants, the skill gate of the new skill.
A run on dbqm45/sdlc-proba needs my Mac (logged-in gh and claude, the stack from `sdlc up`): add it as a checklist item
for me in pdi docs/przebieg-lokalny.md — one small idea through the interview, brief, B0 with one answered question and
the intent PR, which does not ask that question again.
Gates: the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, the mode-pdi tests, the skill gate
and skill evals validation). CI runs on the PR again: wait for it to be green and say in the PR what you ran locally.
Coordination: other sessions may work in parallel in mode-pdi (phase_run.py, decision_record.py, sdlc-phase.yml); keep
your changes there small, keep the branch up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push the branch and open a PR to main (and a small pdi PR for the checklist item), but do
not merge them. At the end report in Polish: PR links, gates and results, and the exact names of the new command,
skill, files and fields.
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

## A6 — pdi (+ tf, ShipScope, ci_for_sdlc): ponowny przebieg lokalny na sdlc-proba

Decyzja DZ19: bramka A6 idzie przed A3–A5. Przebieg robisz Ty na Macu (Docker, zalogowane `gh` i `claude`), a sesja
Claude Code w klonie pdi prowadzi Cię przez [listę przebiegu lokalnego](przebieg-lokalny.md), uruchamia polecenia
terminala, czyta logi i zapisuje wynik. Decyzje przy bramkach, merge'e PR-ów i ocenę skutku podejmujesz Ty. Jedna
nowa zmiana od zgłoszenia do oceny skutku (ocena następnego dnia), w kontenerze (Z8a), bez obejść z przebiegu
2026-10-31. **Stan przed startem (2026-11-03):** pdi `3210975` (kontrakt 0.11.0), tf 5.57.0 (Z1, Z8a, Z8c-2 z N3
i N10), ci_for_sdlc z Z8c-1 (#109); w `sdlc-proba` fabryka tf 5.56.0 i otwarty PR sdlc-proba #10 z kawałka talosa
z 2026-11-03. Koszt faz: budżet `PDI_PHASE_BUDGET_USD=3` (DL5), cały przebieg ok. 15 USD.

```text
Guide me through gate A6 of docs/plan-zespol-jednoosobowy.md (§0, decision DZ19 in docs/decyzje.md): a full local
run on dbqm45/sdlc-proba, one new change from intake to impact review, with phases in the container (Z8a) and no
workarounds from the 2026-10-31 run. You run in my pdi clone on my Mac. Answer me in Polish; commits and PR titles in
English.

Read first: docs/przebieg-lokalny.md (the checklist: §0, §0a, §1–§7, "Gdy coś nie działa", the 2026-10-31 result
table and the PRB list), docs/plan-sdlc-lokalnie.md (§5), docs/plan-z8a-izolacja-faz.md, docs/plan-z1-decyzje-w-fazach.md,
docs/decyzje.md (DL1–DL5, DZ9, DZ19), README.md, and `uv run sdlc --help`.

Roles:
- You run the terminal steps (T) yourself: sdlc up/status/sandbox/check/deploy/impact-review/down, git and gh reads,
  log reads under ~/.sdlc/logs/ and $PDI_REGISTRY_PATH/runs/. Before any command that changes something outside this
  machine (a push, a PR, a GitHub setting, anything in ShipScope settings) tell me what it does and wait for my OK.
- Chat steps (C) use the pdi and shipscope MCP tools. If they are available in this session (/mcp), use them; if not,
  give me the exact sentence to type in a Claude session in the sandbox clone and wait for the result.
- Gates, merges and the impact assessment are mine. For each gate show me the PR, the artifact's key points, the
  questions with a proposed answer each, and what the decision will record; record it with decide_inbox_item only
  after I answer, with my words, and with `answers` when the item has questions (question text verbatim).
- Never edit the sandbox repo, the registry or settings by hand to get a step through. If a step needs anything the
  checklist does not say, stop, show me the evidence (log lines, PR, command output), and record it as a PRB with
  record_problem (channel dogfooding, with the repo it belongs to) once I agree; then we decide whether to continue.

Steps:
0. Preflight, before any phase runs, and report in a short table:
   a. versions: pdi HEAD, contract version, tf version in my tf clone and in sdlc-proba (.claude or the factory
      marker), ci_for_sdlc and ShipScope HEADs; Docker running; ~/.sdlc/env has CLAUDE_CODE_OAUTH_TOKEN and no
      ANTHROPIC_API_KEY next to it; PDI_PHASE_BUDGET_USD=3; PDI_DISPATCH_SANDBOX not set to none.
   b. sdlc-proba needs tf with Z1 (decision import, decision gate --answers) and Z8c-2 (security_scan.py, mode-talos
      1.2.0): if it still has 5.56.0, show me how the factory is updated there (the tf way, not by copying files) and
      do it on my OK, as a PR to sdlc-proba that I merge.
   c. Z8c-2 prerequisites in sdlc-proba: .npmrc with min-release-age=7, package-lock.json in git, semgrep in the
      phase image; whether p/owasp-top-ten downloads without login from the container (check the Semgrep docs and
      note the date), otherwise TALOS_SEMGREP_CONFIG pointing to a rules file in the repo.
   d. Open state in sdlc-proba: PR #10 and any other open PRs or branches from earlier runs; propose what to do with
      each (close, keep) and wait for my decision. Existing changes in the registry stay; the new change gets the next
      PRB/CHG numbers.
   e. Which PRB from the 2026-10-31 list are fixed on main (git log, PR numbers) and which are still open, so we know
      what to watch for. PRB-2, PRB-3 and PRB-4 must be confirmed in this run.
1. §0 and §0a of the checklist: start the stack and run every §0a container check (token not in logs, no access to
   ~/.sdlc/env and ~/.ssh, blocked host in the run log, behaviour without Docker). The checks that need a test
   change use a separate CHG that we reject afterwards.
2. §1–§4 with one new change. The intake text: propose a small, visible change for the sandbox app behind a flag (in
   the style of PRB-1, different from it) and wait for my OK. At B2 or later answer at least one gate question with
   `answers` and check the Z1 item: the question does not come back in plan.md or design.md, and delivery does not
   start while plan.md has an open question. In delivery check the Z8c-2 item, including one deliberately injected
   SQL injection on the acceptance-test path that the scan must stop before commit.
3. §5–§6: deployments to test and prod, flag stages internal → 10% → 100% with their gates.
4. §7 the next day: impact review, forecast_report, autonomy_report. Today, before we stop, tell me exactly what to
   start tomorrow and with which sentence.
5. Result: add "## Wynik przebiegu <date> (A6)" to docs/przebieg-lokalny.md in the same shape as the 2026-10-31 one:
   the step table (result, what needed a workaround or failed, with PRB numbers), the cost of every phase from the run
   logs, the confirmed or still open PRB-2/3/4 and Z1/Z8a/Z8c-2 items, and new PRBs by repo. Tick the checklist items
   that passed. Update the A6 row in §0 and §10 of docs/plan-zespol-jednoosobowy.md and the state line of
   docs/polecenia-startowe-zespol.md. Commit on a branch, push and open a PR to main in pdi, but do not merge it.

At the end report in Polish: the step table, cost per phase and total, every PRB with its repo, what blocks A3–A5,
A7 or stage 2 (A8), the PR link, and the exact commands and tool calls you used.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N1 — tf: przegląd drugim modelem

Startuje po A6 (DZ19) i po Z1 (zrobione). Sesja w klonie tf; mała część pdi, jeśli przegląd działa w kontenerze fazy.
**Stan przed startem (2026-11-03):** tf 5.58.3 (kopia kontraktu pdi 0.11.0), pdi `0845e63`. Od pierwszej wersji tego
polecenia weszły: Z1 (decyzje zmiany i rozstrzygnięte pytania w prompcie, odmowa przy powtórzonym pytaniu), Z8a (krok
`run` w kontenerze z listą dozwolonych hostów i sandboxem Claude Code, tokeny niewidoczne dla persony), Z8c-2, a w
planie N14 (oznaczanie treści z zewnątrz) i N17 (reguły sędziego); CI na GitHubie znowu działa.

```text
Implement N1 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/tf, under decision DZ12 in pdi docs/decyzje.md: the
second model comes from another vendor (own API key, cost inside the phase budget); without that key, another Claude
model with a separate reviewer prompt, marked in the output as a same-vendor review. If the review needs a change in
pdi (see 4), make it a small separate PR in dbqm45/pdi. Start when A6 is done (DZ19). Answer me in Polish; code,
commits and PR titles in English, Conventional Commits.

Goal: before a gate request for B2 (requirements) and B3 (architecture), a second model reads the artifact against
intent.md, requirements and the change's decisions and lists gaps (missing error states, unclear acceptance criteria,
contradictions with a decision, slices that cannot be verified). The findings go into the gate request as questions,
marked as coming from the second review. The same function validates review comments for N2: a comment the second model
does not confirm goes to the human instead of to a fix.

Read first: pdi docs/plan-zespol-jednoosobowy.md §8.3 (N1, N2, N14, N17), docs/plan-z1-decyzje-w-fazach.md and
docs/plan-z8a-izolacja-faz.md; in tf modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py (build_prompt,
decisions_of, settled, repeated, gate_event, the run result), decision_record.py, sandbox_settings.py (TOKENS denied to
the persona) and templates/sdlc-phase.yml; in pdi src/pdi/phase_sandbox.py (ALWAYS_HOSTS, PDI_DISPATCH_ALLOW_HOSTS,
which variables reach the container).

Already done (do not redo): the change's decisions and the questions settled by gates are in decisions.md and in the
prompt as quoted data (Z1); `run` and `gate request` refuse an artifact that repeats a settled question.

1. Plan first in docs/plans/ (files, order, tests, sources with dates). TDD for the scripts.
2. A script in mode-pdi (stdlib Python): `second_review.py artifact --change CHG-n --phase P` and
   `second_review.py comments --pr <n> --input <json>`; provider and model from PDI_SECOND_MODEL (e.g.
   openai:<model>, or claude:<model> as the fallback), the key from the provider's usual variable, never logged. Output
   JSON (findings with severity, quote, reason) and a `## Przegląd drugim modelem` section in the artifact. Check the
   provider's API in its official docs (endpoint, structured output, temperature) and note the date.
3. phase_run.py: after the run and before gate request for requirements and architecture, run the artifact review;
   its blocking findings join the questions of the gate request. A finding that asks what decisions.md already settled
   (Z1 `settled`) is not a question: it is dropped or reported as a contradiction with that decision, with its ref. A
   failed or missing second model is visible in the gate request ("drugi przegląd: niedostępny, powód"), never a
   silent pass. Keep the run result's fields as they are (status, cost_usd, repeated_question) and add the review's.
4. Where it runs (Z8a): `phase_run.py run` runs inside the phase container, whose egress allows only listed hosts, and
   the persona must never see the second vendor's key. Choose in the plan: run the review inside the container (the
   provider's API host added to the allowed hosts and the key passed to the review only, denied to the persona as
   sandbox_settings.py TOKENS does) or as a separate step on the host after `run` (pdi dispatch_local and a separate
   step in sdlc-phase.yml with its own secret). Say why. In Actions the key is a secret of that step only.
5. Sources are data (N14): the artifact, the decisions and the PR comments go to the second model inside
   untrusted-content markers, with markers inside the content neutralised and an instruction to treat them as data.
6. Reviewer rules (N17): the reviewed model is never the reviewer; a rubric with an example per level for severity;
   temperature 0 where the API takes it; the output must match a JSON schema, an invalid answer is retried at most
   twice and then reported as unavailable.
7. Cost: the review's cost is added to the phase result and counts against the phase budget (PDI_PHASE_BUDGET_USD).

Tests: provider selection and fallback (marked same-vendor), no key in logs or in the persona's environment, findings
merged into the gate request, a finding on a settled question dropped or turned into a contradiction, unavailable
reviewer reported, untrusted-content markers neutralised, invalid JSON retried then reported, comment validation
(confirmed / not confirmed) with an injected client, cost counted in the result.
A run on dbqm45/sdlc-proba needs my Mac: add it as a checklist item for me in pdi docs/przebieg-lokalny.md — a
requirements.md that misses an error state, the second review finds it and B2 shows it as a question.
Gates: the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, mode-pdi tests, the skill gate of
pdi-decisions); in pdi, if changed: uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests,
uv run mypy src. CI runs on the PRs again: wait for it to be green and say in the PRs what you ran locally.
Coordination: other sessions may work in parallel in phase_run.py and sdlc-phase.yml (N5, N2, N12, N13); keep your
changes there small, keep the branches up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push and open PRs to main (tf first if pdi depends on it), but do not merge them. At the
end report in Polish: PR links, gates and results, the merge order, and the exact names of the new script, commands,
variables and output fields (inputs for N2).
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N5 — tf: evale przebiegu

Startuje po A6 (DZ19) i po Z1 (zrobione), razem z N17 (reguły sędziego). Sesja w klonie tf. **Stan przed startem
(2026-11-03):** tf 5.58.3, pdi `dbd3bb5`. Od pierwszej wersji tego polecenia weszły: Z1 (`repeated_question` jako
sprawdzalny wynik fazy), Z8a (krok `run` w kontenerze budowanym przez pdi), Z8c-2 (ustalenia skanera w delivery),
a w planie N16 (uczenie z logów faz, które czyta wyniki evali) i N17; CI na GitHubie znowu działa.

```text
Implement N5 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/tf, with N17 (judge rules), under decision DZ13 in
pdi docs/decyzje.md: start with 20 real tasks from dbqm45/sdlc-proba and sprintdeck, a budget per run set in tf, grow to
about 200 after the first results. Start when A6 is done (DZ19). Answer me in Polish; code, commits and PR title in
English, Conventional Commits.

Goal: a change of model, skill, persona or phase prompt does not land without running the flow evals, and the report
compares result and cost with the previous run.

Read first: pdi docs/plan-zespol-jednoosobowy.md §8.3 (N5, N16, N17), docs/przebieg-lokalny.md (the 2026-10-31 run and
the A6 rerun), docs/plan-z1-decyzje-w-fazach.md and docs/plan-z8a-izolacja-faz.md; in tf the skill evals
(core/tests/run_skill_evals.py, core/tests/skill_evals, the holdout sets and result-vs-cost reports of #102, #127,
#130), modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py (the run result: status, cost_usd, error such as
repeated_question) and the mode-pdi tests. Attach dbqm45/sprintdeck read-only if you take tasks from its history.

1. Plan first in docs/plans/ (files, order, tests, sources with dates). Reuse what tf already has for skill evals
   instead of a second framework.
2. A task is: a fixture repo snapshot (the product repo at a commit), the change's folder state before a phase (with
   its decisions.md, so Z1 applies), the phase to run, and checks — the artifact passes decision_record.py check and
   requirements_lint/design_check where they apply, `npm run analyze -- --repo` (ci_for_sdlc) has no blocking finding,
   the run does not end with repeated_question and no settled question comes back (Z1), for delivery the tests pass
   and the slice has no blocking security finding (Z8c-2), cost and number of files read within limits. Each task has
   a stable id: N16 will predict which tasks a proposed change fixes or breaks and check it against your report. Take
   the 20 tasks from the phases of the 2026-10-31 run and the A6 rerun and from sprintdeck history; store them in tf.
3. Runner: runs phase_run.py for each task and collects result, cost, tokens, files read, time; report as Markdown and
   JSON with the comparison to the previous run, per task id. The phase container (Z8a) is built by pdi
   (src/pdi/phase_sandbox.py); say in the plan whether the runner uses it (e.g. through pdi) or runs with tf's
   sandbox_settings.py only, and why. Evals and their checks are read-only for the runs they judge.
4. Judge (N17), where a check is not deterministic: a rubric with an example per level (correctness, agreement with
   the change's decisions, style), both orders when comparing two outputs with the difference in the report, a check
   that length is not rewarded, the judged model is never the judge, temperature 0 where the API takes it; agreement
   with my rating on a small sample in the report.
5. Trigger: a workspace.py command and a CI job on changes to personas, mode-pdi prompts or the pinned model; locally
   the command. The CI job needs a model secret: without it the job reports "skipped", never "passed". A change that
   lowers the pass rate or raises cost by more than a set limit fails with the report.

Tests: task loading and validation, checks per phase (including repeated_question and a security finding), the
comparison per task id and the failure limits, judge rules (both orders, length control) with an injected runner and
judge, the CI job skipped without the secret.
The first real run of the 20 tasks costs money: give me the expected cost first and run it only after I agree; if this
session has no model credentials, add it as a checklist item for me in pdi docs/przebieg-lokalny.md. Record pass rate
and cost in the PR.
Gates: the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, the skill gate, skill evals
validation). CI runs on the PR again: wait for it to be green and say in the PR what you ran locally.
Coordination: other sessions may work in parallel in phase_run.py (N1, N2, N12, N13); keep your changes there small,
keep the branch up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push and open a PR to main, but do not merge it. At the end report in Polish: the PR link,
gates and results, and the exact names of the new command, CI job, files, task fields and report fields (inputs for
N16).
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z7b-1a — pdi + tf: cele zmiany w kontrakcie i planie

Startuje po A6 (DZ19), po Z1 (zrobione) i Z8c-1 (zrobione), razem z N4 (pokrycie i testy mutacyjne) i N20 (co
najmniej dwie opcje w planie). Sesja w klonie pdi; część tf osobnym PR-em. **Stan przed startem (2026-11-03):** pdi
`b6f12b8` (kontrakt 0.11.0), tf 5.58.3 (kopia kontraktu 0.11.0). Od pierwszej wersji tego polecenia weszły: Z1
(decyzje z bramek wiążą kolejne fazy, `decision import`), Z8a, Z8c-1 i Z8c-2, a w planie N20 i Z10 (SLO i progi
wydajności oraz dostępności, które później dojdą do `targets`); CI na GitHubie znowu działa.

```text
Implement part 1a of Z7b of docs/plan-zespol-jednoosobowy.md (§8.1, row A4 in §0) in dbqm45/pdi, with the tf part in
dbqm45/tf (attach it with push access), together with N4 (coverage and mutation targets on changed code) and N20 (at
least two options in plan.md), under decisions DZ6 and DZ7 in docs/decyzje.md: the architect persona (tomasz)
proposes the change's targets in the plan, the human approves them at B3; for AI products evaluation thresholds are
mandatory. Start when A6 is done (DZ19). Answer me in Polish; code, commits and PR titles in English.

Goal: every change carries measurable quality targets, approved at B3 and checked before B4, instead of judging PRs by
eye.

Read first: docs/plan-zespol-jednoosobowy.md §8.1 (Z7b), §8.3 (N4, N20), §8.5 (Z10a `slo`, Z10e performance and
accessibility thresholds in `targets`); docs/plan-z1-decyzje-w-fazach.md; contract/release-plan.schema.json and
contract/README.md; src/pdi/flow.py, src/pdi/inbox.py, src/pdi/trace.py; in tf the persona tomasz,
packs/pack-it/skills/arch-tech-selection (it already asks for 2–3 candidates per area), modes/mode-pdi templates
plan.md and release.yaml, decision_record.py (check_plan, check_release) and tools/pdi-contract.json.

Already done (do not redo): Z1 — the B3 decision and its answers reach every later phase through decisions.md and the
phase prompt, so approved targets bind design and delivery without a new mechanism; ci_for_sdlc already turns scanner
results into findings (Z8c-1).

1. Plan first in docs/plan-z7b-cele.md (pdi): files in both repos, order, tests, sources with dates. TDD.
2. Contract: the next free minor version at the time of your PR. Z2a also bumps the contract: check main and open pdi
   PRs; whichever merges first takes 0.12.0 and the other rebases to the next number. contract-v tag after merge, then
   tf regenerates its pinned copy as tf #136 did. Add `targets` in release-plan.schema.json (or a sibling schema
   linked from it): coverage of changed code (min %, with explicit exclusions and their reason), mutation score on
   changed code (min %; tools: StrykerJS for JS/TS, mutmut for Python, per N4), optional performance budgets (name,
   metric, limit), evaluation thresholds for AI features (eval set, metric, min). Shape it so Z10a (`slo`) and Z10e
   (p95, bundle size, accessibility) can be added later as optional fields without a breaking change. In the same
   version add an optional field for the targets' status to readiness_changed in event.schema.json (today it has
   additionalProperties false), so ci_for_sdlc can report it in Z7b-1b. Examples and contract/README.md.
3. tf: the architecture phase writes `targets` with a short justification per target, and (N20) plan.md has at least
   two considered options with pros, cons and cost, the choice and why — check first what tomasz and
   arch-tech-selection already require and add only the missing part. plan.md and release.yaml templates and
   decision_record.py check validate targets against the contract copy and flag a plan with a single option.
4. pdi: the B3 gate shows the targets (and the options considered); approve-for-implementation and B4 show their status
   once ci_for_sdlc reports it (Z7b-1b); get_change and get_trace include them. A change of approved targets after B3
   should be a new decision (supersede), not a silent edit: propose in the plan how to detect it (e.g. the B3 entry
   records the approved targets and check compares them), or say why it waits.
5. Docs: contract/README.md, README, plan §10, the Z7b-1a row of docs/polecenia-startowe-zespol.md, and a checklist
   item for me in docs/przebieg-lokalny.md (B3 shows the targets and the options; approving them makes them binding).

Tests: schema and examples (targets valid and invalid, room for later optional fields), tf template and check (missing
or malformed targets, a plan with one option), pdi gate items with targets, get_change/get_trace, and the detection of a
changed target after B3 if the plan includes it.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the
repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, the skill gates of changed skills). CI runs on
the PRs again: wait for it to be green and say in the PRs what you ran locally.
Coordination: other sessions may work in parallel on the contract (Z2a), flow.py and inbox.py in pdi and on
decision_record.py and the tomasz persona in tf; keep your changes small, keep the branches up to date with main and
resolve conflicts keeping both behaviours.
When the gates pass, commit, push and open PRs to main (pdi with the contract first, then the tf PR with the copy after
the tag), but do not merge them. At the end report in Polish: PR links, gates and results, the contract version taken,
the merge order, and the exact names of the new fields (inputs for Z7b-1b).
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## Z7b-1b — ci_for_sdlc: sprawdzanie celów zmiany

Startuje po Z7b-1a (cele w kontrakcie i jego tag) i Z8c-1 (zrobione). Sesja w klonie ci_for_sdlc; szablon
`change-check.yml` jest w tf (mode-pdi), więc jego kroki idą małym PR-em w tf. **Stan przed startem (2026-11-03):** pdi
`18432c1` (kontrakt 0.11.0), tf 5.58.3; w ci_for_sdlc czytnik SARIF z Z8c-1 (#109) i odpowiedzi na ustalenia z PRB-16
(#107). CI na GitHubie znowu działa.

```text
Implement part 1b of Z7b of the plan "one-person team" from dbqm45/pdi (main): docs/plan-zespol-jednoosobowy.md §8.1
and §0 (row A4), the contract change of Z7b-1a (docs/plan-z7b-cele.md and its PR's final report: the contract version
and the names of the `targets` fields) and N4 in §8.3. Work in dbqm45/ci_for_sdlc; the optional coverage and mutation
steps of the change-check template go to dbqm45/tf (attach it with push access) as a small PR. Start when Z7b-1a is
merged and its contract tag exists. Answer me in Polish; code, commits and PR titles in English, Conventional Commits.

Goal: the gate checks a change's `targets` against real reports, the way it reads JUnit (--tests) and SARIF (--sarif)
today, so a change below its targets is not ready for B4.

Read first: in ci_for_sdlc the SARIF reader and rules of Z8c-1 (#109: readers with size limits, findings on the items
they touch, annotations) and the decisions that answer findings (#107, PRB-16: `decision add --finding` in the
change's decisions.md, effects resolve / accept_risk / dismiss / confirm); in tf
modes/mode-pdi/skills/pdi-decisions/templates/change-check.yml (Z8c-2) and the pinned contract copy; in pdi
contract/release-plan.schema.json and contract/event.schema.json (readiness_changed).

Already done (do not redo): SARIF findings and their annotations (Z8c-1), answers to findings recorded in
decisions.md and read back by ci_for_sdlc (PRB-16), a blocking finding only makes a change not_ready (PRB-17). Reuse
the same reader pattern, finding model and decision answers for the TGT rules.

1. Plan first in docs/ (TARGETS-PLAN.md: files, order, rules, tests, sources with dates). TDD.
2. Inputs: `npm run analyze -- --repo <path> --coverage <lcov or cobertura> --mutation <Stryker JSON or mutmut
   results>` plus the change's `targets` from release.yaml (validated against the contract version of Z7b-1a; update
   ci_for_sdlc's pinned contract the way it pins it today). Readers with size limits; an unreadable or missing report
   for a set target fails the gate (a check that did not run is never "met"). Check the report formats in the official
   docs of lcov/Cobertura, StrykerJS (mutation-testing-report-schema) and mutmut, with the date.
3. Rules: TGT-001 coverage of changed code below target (blocking), TGT-002 mutation score on changed code below target
   (blocking), TGT-003 performance budget exceeded (warning unless the target says blocking), TGT-004 evaluation
   threshold not met for an AI feature (blocking). Changed code = the change's slices' files (commits with
   `Change: TSK-n`) or the PR diff in CI; excluded paths from the target are skipped with their reason. A TGT finding
   can be answered like any other (e.g. accept_risk for a missed target, recorded in decisions.md); a new loop back to
   an earlier phase is Z7b-2, not this step. Leave room for the Z10e thresholds (p95, bundle size, accessibility).
4. Readiness to pdi (--send-to-pdi) carries the targets' status only if the contract has a field for it: in contract
   0.11.0 readiness_changed has additionalProperties false and no such field. Use what Z7b-1a added; if it added
   nothing, do not send unknown fields — note it in the plan and ask me for a small pdi contract PR.
5. tf: change-check.yml gains optional coverage and mutation steps (only when targets are set, mutation on changed files
   only), passing the reports to `npm run analyze`; secrets and inputs through env as in the rest of the template.

Tests: readers (valid, malformed, too big), changed-code filtering and exclusions, TGT-001…004, a missing report for a
set target fails, a TGT finding answered with accept_risk, exit codes and annotations, readiness payload (with and
without the contract field); in tf the template steps.
A run on dbqm45/sdlc-proba needs my Mac: add it as a checklist item for me in pdi docs/przebieg-lokalny.md — a slice
below its coverage target is not ready before B4, and accepting the risk at the gate makes it ready.
Gates: ci_for_sdlc — npm test, npm run typecheck, npm run test:contract, npm run lint:commit; tf — the repo's checks
(workspace.py check --packs mode-pdi, the skill gate of pdi-decisions). CI runs on the PRs again: wait for it to be
green and say in the PRs what you ran locally.
Coordination: other sessions may change ci_for_sdlc rules and the tf templates; keep the branches up to date with main
and resolve conflicts keeping both behaviours.
When the gates pass, commit, push and open PRs to main, but do not merge them. At the end report in Polish: PR links,
gates and results, the merge order, and the exact names of the new options, rules and payload fields.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N2 — pdi + tf: pętla budujący–recenzent na PR i samonaprawa CI

Startuje po A6 (DZ19), Z8a (zrobione) i N1. Sesja w klonie pdi; część tf osobnym PR-em. W tej samej grupie A5 są N12,
N13 i N15 — mają osobne polecenia, bo dotykają tych samych plików, więc sesje trzeba prowadzić po
kolei albo uzgadniać zmiany. **Stan przed startem (2026-11-03):** pdi `d170ecb` (kontrakt 0.11.0), tf 5.58.3. Od
pierwszej wersji tego polecenia weszły: Z1 (decyzje zmiany wiążą poprawki), Z8a (persona w kontenerze; push, PR i
tokeny GitHuba tylko na hoście), Z8c-2 (ustalenia skanera blokują kawałek, skan PR w CI), a w planie rozszerzenie N2
(wcześniejsze wyjście po progu wagi uwag, „Przewodnik dokończenia” w PR, wspólny z N7); CI na GitHubie znowu działa.

```text
Implement N2 of docs/plan-zespol-jednoosobowy.md (§8.3) in dbqm45/pdi, with the tf part in dbqm45/tf (attach it with
push access). Start when A6 is done (DZ19) and N1 (second review) is merged: read N1's plan and its PR's final report
for the names of the review script, its commands and output fields. Answer me in Polish; code, commits and PR titles
in English.

Goal: a talos PR reaches the human only with green checks and closed review comments, or with a clear "not done after
N rounds" and the reason, and always with a completion guide. Background: Spotify's Honk opens a PR only after full
verification kept apart from the agent (engineering.atspotify.com, 2025-11); verify the details before relying on
them.

Read first: docs/plan-zespol-jednoosobowy.md §8.3 (N2, N7, N12, N13), docs/plan-z1-decyzje-w-fazach.md,
docs/plan-z8a-izolacja-faz.md and N1's plan; src/pdi/dispatch_local.py (delivery: `_publish_cuts`, PRs opened on the
host), src/pdi/phase_sandbox.py, src/pdi/changes.py, src/pdi/inbox.py, src/pdi/trace.py; in tf the talos skills
(talos-story-run), REVIEW.md, modes/mode-pdi phase_run.py, templates/sdlc-phase.yml and change-check.yml (Z8c-2).

Already done (do not redo): talos's slices go to PRs from the host (pdi, PRB-4); the persona runs in a container
without GitHub tokens (Z8a); security findings block a slice and PRs are scanned in CI (Z8c-2); the change's decisions
reach every phase (Z1); N1 validates review comments with a second model.

1. Plan first in docs/plan-n2-petla-pr.md (pdi): files in both repos, order, tests, sources with dates. TDD.
2. After delivery, per talos PR: AI review (tf REVIEW.md) → comment validation by the second model (N1) → talos fixes
   only the validated comments → re-review; at most 2 rounds (as DZ6), then the PR goes to the human with the open
   comments. The loop ends early when only comments below a severity threshold remain (no blocking or important
   ones); those go into the PR as a list. Unvalidated comments go to the human as questions, not to a fix, and so does
   a comment that contradicts a decision of the change (Z1), with the decision's ref.
3. Red checks: CI runs on PRs again. The host reads the failing check's log (gh, with the token that stays on the host;
   locally the verification script of N3 as a fallback), passes it to talos as quoted data (it is external content),
   talos fixes, the host pushes and waits for green; the same round limit. Every fix round runs in the container of
   Z8a; pushing and reading CI stay on the host.
4. Completion guide (shared with N7): every talos PR has a fixed section "Przewodnik dokończenia" — what is done, what
   is left for the human (files, steps), decisions taken outside the plan with a request to approve them, risks; it is
   updated after each round.
5. pdi: the change state gets `pr_loop` per PR (round, status: reviewing | fixing | green | needs_human, last reason);
   the inbox shows "PR gotowy do Twojego przeglądu" only when green or when the limit is reached; get_trace shows the
   rounds; cost per round in the phase report and within the phase budget. If the local console (Z3-lokalnie) is
   merged, show pr_loop there too.
6. Docs: README, integrations/claude-code/README.md, mode-pdi GUIDE.md, a checklist item for me in
   docs/przebieg-lokalny.md (below).

Tests: the round loop with injected review, validation and fix steps (green after 1 round, limit reached, early exit by
severity, unvalidated and decision-contradicting comments to the human), the red-check path with a recorded CI log,
the completion guide updated per round, state and inbox items, cost accounting, no GitHub token in the container.
A run on dbqm45/sdlc-proba needs my Mac: add it as a checklist item for me in docs/przebieg-lokalny.md — a talos PR with
one real review finding and one false one: the real one is fixed, the false one goes to me, the PR has the guide.
Gates: pdi — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy src; tf — the
repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, skill gates of changed skills). CI runs on the
PRs again: wait for it to be green and say in the PRs what you ran locally.
Coordination: N12, N13 and N15 change the same files (phase_run.py, talos, dispatch_local.py); keep your changes small,
keep the branches up to date with main and resolve conflicts keeping both behaviours.
When the gates pass, commit, push and open PRs to main (tf first if pdi depends on it), but do not merge them. At the
end report in Polish: PR links, gates and results, the merge order, and the exact names of the new state fields,
statuses, commands and PR sections.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
```

## N12 — tf: weryfikacja przed zakończeniem fazy

Grupa A5. Startuje po A6 (DZ19); N3 jest zrobione z Z8c-2. Sesja w klonie tf. Dotyka tych samych plików co N2, N13 i
N15 (talos, `phase_run.py`): prowadź po kolei albo uzgadniaj zmiany. **Stan przed startem (2026-11-03):** pdi `aadfbf9` (kontrakt 0.11.0), tf 5.58.4. Już jest: Z1, Z8a (krok `run`
w kontenerze z sandboxem Claude Code), Z8c-2 z N3 (jedno polecenie weryfikacji w pierwszej linii CLAUDE.md produktu,
wzór `templates/verify.sh` w talos-story-run); CI na GitHubie działa.

```text
Implement N12 of docs/plan-zespol-jednoosobowy.md (§8.3, row A5 in §0) from dbqm45/pdi (main) in dbqm45/tf. Answer me
in Polish; code, commits and PR title in English, Conventional Commits.

Goal: the delivery phase and a talos slice cannot end as a success when the code changed after the last verification:
there must be a fresh result of the product's verification command (N3) for the current commit. A missing result turns
"done" into a continuation with the instruction to run the verification, visible in the log.

Read first: pdi docs/plan-zespol-jednoosobowy.md §8.3 (N3, N12, N13) and docs/plan-z8a-izolacja-faz.md; in tf
modes/mode-talos/skills/talos-story-run (SKILL.md: the slice loop, `BRAMKA K<n>: PASS|FAIL`, templates/verify.sh,
scripts/security_scan.py), modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py (the run result) and
sandbox_settings.py, core/hooks (how hooks are registered; project_record.py already has a Stop hook).

Already done (do not redo): N3 — one verification command in the first line of the product's CLAUDE.md, run in the
slice loop; the security scan per slice (Z8c-2).

1. Plan first in docs/plans/ (files, order, tests, sources with dates). TDD.
2. A verification record: after each run of the verification command, a small file in the run directory with the
   commit (HEAD and whether the tree is clean), the command, the exit code and the time — written by a script, not by
   the persona's own claim.
3. Enforcement on stop: check in the official Claude Code docs how a Stop (and SubagentStop) hook can block the end of
   a turn and send the agent back with a reason, and with which fields; then a hook that refuses to stop when the code
   changed after the last passing verification record, with the exact command to run. A loop guard: after N refusals
   in a row the hook lets the session stop with status "verification missing" instead of looping (N13 will count it).
4. phase_run.py: the delivery result and talos's report show the verification record of the last slice; a slice
   without a fresh passing record is not "done".
5. Docs: talos-story-run SKILL.md, mode-talos and mode-pdi GUIDE.md.

Tests: the record written and read (clean and dirty tree, different commit), the hook allows stop with a fresh passing
record and refuses without it (with the command in the reason), the loop guard, phase_run's delivery result.
A run on dbqm45/sdlc-proba needs my Mac: add it as a checklist item for me in pdi docs/przebieg-lokalny.md (a slice that
changes code after its last verification is sent back to verify, and the log shows it).
Gates: pdi (if changed) — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy
src; tf — the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, plus --packs mode-talos when talos
changes, skill gates of changed skills). CI runs on the PRs: wait for it to be green and say in the PRs what you ran
locally.
When the gates pass, commit, push and open PRs to main (tf first if pdi depends on it), but do not merge them.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
At the end report in Polish: the PR link, gates and results, and the exact names of the hook, the record file and its
fields.
```

## N13 — tf + pdi: limity tur i czasu, zapętlenie trafia do skrzynki

Grupa A5. Startuje po A6 (DZ19). Sesja w klonie tf; część pdi (pozycja w skrzynce) osobnym PR-em. Dotyka tych samych
plików co N2, N12 i N15: prowadź po kolei albo uzgadniaj zmiany. **Stan przed startem (2026-11-03):** pdi `aadfbf9` (kontrakt 0.11.0), tf 5.58.4. Już jest: Z1, Z8a (krok `run`
w kontenerze z sandboxem Claude Code), Z8c-2 z N3 (jedno polecenie weryfikacji w pierwszej linii CLAUDE.md produktu,
wzór `templates/verify.sh` w talos-story-run); CI na GitHubie działa.

```text
Implement N13 of docs/plan-zespol-jednoosobowy.md (§8.3, row A5 in §0) from dbqm45/pdi (main) in dbqm45/tf, with the pdi
part in dbqm45/pdi (attach both with push access). Answer me in Polish; code, commits and PR titles in English.

Goal: cheap limits stop a phase that runs away, with a readable reason, and a loop goes to the pdi inbox instead of
using up the budget: a turn limit next to the cost limit, a time limit, and a counter of identical tool calls (three in
a row → an inbox item "faza się powtarza" with the last steps).

Read first: pdi docs/plan-zespol-jednoosobowy.md §8.3 (N13, N12, N16) and docs/plan-z8a-izolacja-faz.md; in tf
modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py (how claude is started: --print, --max-budget-usd from
PDI_PHASE_BUDGET_USD, --settings), sandbox_settings.py, templates/sdlc-phase.yml, core/hooks; in pdi
src/pdi/dispatch_local.py (STEP_TIMEOUT_SECONDS, the run result), src/pdi/inbox.py (item kinds), src/pdi/receiver.py and
contract/event.schema.json.

1. Plan first in docs/plans/ (tf; files in both repos, order, tests, sources with dates). TDD.
2. Limits: check in the official Claude Code docs the flags for a turn limit in print mode (`--max-turns`), how the run
   ends when a limit is hit (result subtype, exit code) and what is reported; then pass a turn limit and a time limit
   per phase from the product's settings (e.g. .claude/pdi-phases.json next to the persona override) with safe
   defaults. A phase stopped by a limit ends `failed` with a readable reason (which limit, the value, the last step),
   not a generic error; pdi's step timeout stays the outer bound.
3. Loop counter: a PreToolUse/PostToolUse hook counts identical consecutive tool calls (same tool, same normalised
   input); at three in a row it stops the phase with status `looping` and the last steps (tool names and short,
   secret-free summaries — no file contents, prompts or tokens).
4. pdi: a looping or limit-stopped phase gives an inbox item (kind e.g. `phase_stuck`: change, phase, reason, last
   steps, log link) with options "ponów" (retry_dispatch) and "zatrzymaj". It needs a way for the result to reach pdi:
   in local mode dispatch_local reads it from the run result; in Actions mode decide in the plan whether it is a new
   event type or a field of an existing one, and if the contract changes take the next free minor version
   (coordinate with Z2a and Z7b-1a, which also bump it; tag after merge, then tf's pinned copy as tf #136).
5. Docs: mode-pdi GUIDE.md, README, a checklist item for me in pdi docs/przebieg-lokalny.md (a phase with a low turn
   limit stops with a clear reason; a forced loop gives the inbox item).

Tests: limit flags passed from settings and defaults, the result for each limit, the loop counter (three identical
calls, different inputs not counted, no secrets in the summary), the pdi inbox item and its options, retry.
Gates: pdi (if changed) — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy
src; tf — the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, plus --packs mode-talos when talos
changes, skill gates of changed skills). CI runs on the PRs: wait for it to be green and say in the PRs what you ran
locally.
When the gates pass, commit, push and open PRs to main (tf first if pdi depends on it), but do not merge them.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
At the end report in Polish: PR links, gates and results, the merge order, the contract version taken (if any), and the
exact names of the settings, statuses, hook and inbox item kind.
```

## N15 — tf + pdi: zakres zapisu fazy

Grupa A5. Startuje po A6 (DZ19). Sesja w klonie tf; lista ścieżek fazy w kontrakcie pdi osobnym PR-em. Dotyka tych
samych plików co N2, N12 i N13 (hooki, persony): prowadź po kolei albo uzgadniaj zmiany. **Stan przed startem (2026-11-03):** pdi `aadfbf9` (kontrakt 0.11.0), tf 5.58.4. Już jest: Z1, Z8a (krok `run`
w kontenerze z sandboxem Claude Code), Z8c-2 z N3 (jedno polecenie weryfikacji w pierwszej linii CLAUDE.md produktu,
wzór `templates/verify.sh` w talos-story-run); CI na GitHubie działa.

```text
Implement N15 of docs/plan-zespol-jednoosobowy.md (§8.3, row A5 in §0) from dbqm45/pdi (main) in dbqm45/tf, with the
contract part in dbqm45/pdi (attach both with push access). Answer me in Polish; code, commits and PR titles in English.

Goal: a phase can write only its own files. guard_paths gets a list of allowed paths per phase (e.g. intent: only the
change's intent.md; requirements: requirements.md; architecture: plan.md, release.yaml and architecture.md; design:
design.md; delivery: code, tests and the change's run report); every phase may also add entries to decisions.md only
through decision_record.py. A write outside the scope is a refusal in the log, not a silent skip.

Read first: pdi docs/plan-zespol-jednoosobowy.md §8.3 (N15), contract/contract.json (conventions) and
contract/change.schema.json; in tf core/hooks/guard_paths.py (secrets, guardrails, context economy), how hooks are
registered for personas, modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py (PHASES with the artifact of each
phase; the persona runs with --settings $PDI_CLAUDE_SETTINGS) and sandbox_settings.py (Z8a: filesystem.allowWrite),
the tf #134 change that moved ADRs to architecture.md.

1. Plan first in docs/plans/ (tf; files in both repos, order, tests, sources with dates). TDD.
2. Contract: the list of writable paths per phase in contract.json conventions (patterns relative to the product repo,
   with `<CHG>`), the next free minor version (coordinate with Z2a, which adds the `discovery` phase and brief.md, and
   with Z7b-1a and N13, which may also bump it); tag after merge, then tf's pinned copy as tf #136.
3. Enforcement in two layers: guard_paths refuses Edit/Write/NotebookEdit outside the phase's list (the phase from an
   environment variable set by phase_run.py, never from the persona), with the allowed list in the message; and the
   Claude Code sandbox settings for the phase (check in the official docs how filesystem write rules and
   permissions.deny apply to Bash and to Edit/Write, and note the date) narrow writes the same way, so a shell command
   cannot bypass the hook. Outside a pdi phase (no variable) guard_paths behaves as today.
4. The delivery phase writes code; talos's own rules stay. Rework of a phase uses the same list.
5. Docs: mode-pdi GUIDE.md and SKILL.md, contract/README.md (pdi), a checklist item for me in pdi
   docs/przebieg-lokalny.md (the architecture persona cannot change code or another phase's artifact; the refusal is
   in the log).

Tests: the contract list and examples, guard_paths per phase (allowed, refused with the list, decisions.md through the
script only, no phase → as today), the sandbox settings per phase, a shell write outside the scope refused.
Gates: pdi (if changed) — uv run pytest, uv run ruff check src tests, uv run ruff format --check src tests, uv run mypy
src; tf — the repo's checks (workspace.py check --packs pack-it and --packs mode-pdi, plus --packs mode-talos when talos
changes, skill gates of changed skills). CI runs on the PRs: wait for it to be green and say in the PRs what you ran
locally.
When the gates pass, commit, push and open PRs to main (tf first if pdi depends on it), but do not merge them.
Verification rule (docs/plan-zespol-jednoosobowy.md §8.4): before planning, check the behaviour of every external tool, API or setting this step relies on against its official documentation and note the date; test locally what the docs leave unclear; list the sources in your plan.
At the end report in Polish: PR links, gates and results, the merge order, the contract version taken, and the exact
names of the contract field, the environment variable and the refusal message.
```

## Z3-lokalnie — pdi + tf: konsola w przeglądarce na Macu

Decyzje DZ14 i DZ18. Startuje po A6 (ponowny przebieg na `sdlc-proba`), przed etapem 2. Sesja w klonie pdi; część tf
osobnym PR-em. Wygląd: `design/konsola/v2-klikalna/` (trzy pasy). **Stan przed startem (2026-11-03):** pdi `f6c5533`
(kontrakt 0.11.0), tf 5.57.0. Od pierwszej wersji tego polecenia weszły: Z1 (odpowiedzi na pytania bramki, decyzje
zmiany w fazie), Z8a (krok `run` w kontenerze Docker), Z8c-2 (skaner w pętli talosa); CI na GitHubie znowu działa.

```text
Implement Z3-lokalnie of docs/plan-zespol-jednoosobowy.md (§0 row A7, §5, decisions DZ14 and DZ18 in docs/decyzje.md) in
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
   e. Files panel in the change trace (DZ18), read-only: the change's artifacts from the product clone pdi already
      uses for phase runs (intent.md, requirements.md, plan.md, design.md, release.yaml under
      docs/project/changes/<CHG>/) and the diff of the current slice (its branch against its base), refreshed live over
      SSE while a phase writes them. At a gate item the panel shows the exact files and commit the decision is about,
      and the inbox refuses the decision if they changed after the page was loaded. Only paths inside the clone, no
      symlinks out of it, no binary files, a size limit with a link to the PR, files like .env or keys never shown;
      no editing, no writes to the clone.
   f. Side panel in the board and the trace: the running phase's progress (current action, elapsed time, cost so far
      from run.progress), with room for the OpenTelemetry data of Z10c (cost, tokens, errors, refusals) later.
   Security: every value escaped (decision texts, questions and log lines are data), no inline scripts, a
   Content-Security-Policy, POSTs only with the token and a same-origin check, nothing listens outside 127.0.0.1, no
   secret ever reaches a page.
5. Docs: README, docs/przebieg-lokalny.md (the next run can be followed in the console; add a checklist item for me),
   integrations/claude-code/README.md, tf mode-pdi GUIDE.md.

Tests: stream-json to progress lines (from recorded sample streams, including a failed run, a run waiting at a gate and
a repeated_question failure), the unchanged final result, the host-side split of progress lines from the log, the
console's read model (lane and step of a change from registry states), SSE updates when a progress file grows, button
decisions (same result as decide_inbox_item, with answers, refused without token, refused for a stale item), escaping as decide_inbox_item, with answers, refused without token, refused for a stale item),
the files panel (artifacts and slice diff from a sample clone, live refresh when a file changes, refusal when files
changed under a gate item, paths outside the clone, symlinks, binary and secret-like files refused), escaping
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
