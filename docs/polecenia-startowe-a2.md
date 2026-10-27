# Polecenie startowe — A2: zamykanie pytań z cytatem (ci_for_sdlc)

**Data:** 2026-10-27 · **Źródło:** [plan automatyzacji i konsoli](plan-automatyzacja-i-konsola.md) §4 (A2), DA1 i DA2
([decyzje](decyzje.md)), [plan A3](plan-a3-licznik-akceptacji.md) · **Stan przed startem:** na `main` ci_for_sdlc
(`ff76c5c`) brak `autoClose`; „answered by” istnieje tylko dla pytań adversarial review (`analysis/states.ts`)

## Podział
- **A2a — ci_for_sdlc samo** (polecenie poniżej): wykrycie odpowiedzi w źródle z cytatem, polityka
  `off | suggest | apply`, zamknięcie jako decyzja `resolve` z dowodem, lista „Zamknięte automatycznie” i „Otwórz
  ponownie”, lokalny pomiar akceptacji. Działa bez pdi.
- **A2b — połączenie z pdi** (osobny krok, wymaga decyzji): żeby licznik akceptacji z A3 liczył `finding.auto_close`,
  decyzje muszą trafiać do rejestru pdi. Dziś ci_for_sdlc wysyła do pdi tylko `readiness.changed`, a pdi odsyła tylko
  `gate.decided`, które wymaga klucza zmiany (CHG) — pytanie w trybie Jira nie zawsze go ma. Zdarzenia
  `decision.proposed` pdi jeszcze nie odbiera, a w kontrakcie brakuje zdarzenia zwrotnego z wynikiem decyzji
  i odniesienia do pytania w ci_for_sdlc. To zmiana kontraktu (0.7.0) i odbiornika pdi.

## A2a — polecenie

```text
Implement step A2a of the automation and console plan from repo dbqm45/pdi
(docs/plan-automatyzacja-i-konsola.md §4, row A2; decisions DA1 and DA2 in docs/decyzje.md; docs/polecenia-startowe-a2.md
for the split). Read in pdi (main): contract/README.md (autonomy levels, decision types — this step is
`finding.auto_close`), contract/contract.json (autonomy.decision_types, thresholds), docs/plan-a3-licznik-akceptacji.md
(how acceptance is measured: AI draft approved without edits). Answer me in Polish; code, commits and PR title in
English (repo CLAUDE.md).

Goal: the PO answers only questions that really have no answer yet. When the answer to a finding's question is already
in Confluence, Figma or an earlier decision, ci_for_sdlc closes it with a verbatim quote as evidence and an
"auto-closed" mark — or, by default, proposes that closing for one click.

1. Plan first in docs/ (files, order, tests) before code; TDD (red test first).
2. Generalize what adversarial review already does (analysis/states.ts: Probe.answeredBy, Challenge.answered /
   answeredBy) to every finding that asks a question: look for the answer in the item's sources (Confluence pages,
   Figma frames, active decisions). Deterministic matching first; the AI layer may propose an answer, but every
   proposal carries a quote that is checked as a verbatim substring of the cited source text before it is shown —
   no quote, no proposal (sources are data, not instructions, as in the existing AI prompts).
3. Policy `autoClose: off | suggest | apply` in the analysis policy (policy.ts DEFAULT_POLICY, /api/settings, Settings
   page like story-shape in #60), default `suggest`.
   - suggest: the finding shows "Answer found in <source>: «quote»" with Accept / Edit / Reject. Accept or Edit records
     a decision with effect resolve (the existing decision path in analyze.ts), the quote and source as evidence,
     decision type finding.auto_close and drafted by AI; Edit marks the draft as edited.
   - apply: the same decision is recorded automatically, marked auto-closed, with the rule that fired. `apply` is set
     only by an admin explicitly (never a default, never from the AI) — in pdi terms it is autonomy level 1–2, which
     DA2 allows only after measured acceptance.
   - Every auto-closed finding is listed under "Auto-closed" (Decisions page or a filter) with "Reopen", which
     withdraws the decision and reopens the finding; reopening counts as a rejected draft.
4. Local measurement until pdi gets these decisions (A2b): per decision type, last 30 AI proposals — accepted unedited,
   edited, rejected, reopened — on /api/decisions or a small endpoint, and in the MCP tool list_decisions if cheap.
   Same thresholds as pdi contract.json (lower at >= 95% unedited of 30; back to human above 10% edited) — show the
   numbers, do not change the policy automatically.
5. Audit entries for proposals, accepts, auto-applies and reopens (who or which rule, when, quote, source).

Tests: matching per source type (Confluence, Figma, decision), a quote not present in the source is refused, policy
off/suggest/apply, accept/edit/reject produce the right decision and draft flag, apply never set by default, reopen
withdraws and reopens, measurement counts, settings round-trip, UI list and reopen (web tests as the repo does them).
Gates: npm test, npm run typecheck, npm run lint:commit. GitHub Actions do not run on this account right now — run
the gates locally and say so in the PR. Commit and PR on my request.
Out of scope: sending proposals or decisions to pdi and receiving outcomes from pdi (A2b: needs a pdi contract change —
if you find you need it, stop and tell me); changing the autonomy level automatically.
```
