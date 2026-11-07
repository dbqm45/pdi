"""Pętla PR talosa (N2, docs/plan-n2-petla-pr.md): rundy przegląd → walidacja → poprawka ze wstrzykniętymi krokami."""

from __future__ import annotations

from typing import Any

import pytest

from pdi import pr_loop

PR = "https://github.com/o/r/pull/44"
CUT = pr_loop.Cut(branch="story/tsk-1-badge", pr=PR, base="main")
BODY = (
    "# Raport przebiegu TSK-1\n\n## Odłożone do decyzji\n\n- duplikaty CDR między plikami\n\n"
    "- [założenie] znacznik tylko w nagłówku\n\nChange: CHG-4\n"
)


def finding(fid: str, severity: str = "important", **extra: Any) -> dict[str, Any]:
    return {"id": fid, "severity": severity, "file": "src/page.js", "line": 3, "body": f"uwaga {fid}", **extra}


class FakeSteps:
    """Kroki z nagranymi odpowiedziami; każda lista to kolejne rundy."""

    def __init__(
        self,
        reviews: list[dict[str, Any]],
        *,
        validations: list[dict[str, Any]] | None = None,
        checks: list[dict[str, Any]] | None = None,
        verify: dict[str, Any] | None = None,
        ci_log: str = "",
        fix_cost: float = 0.1,
    ) -> None:
        self.reviews = reviews
        self.validations = validations or []
        self.checks_seq = checks or [{"state": "green", "checks": [{"name": "check", "bucket": "pass"}]}]
        self.verify_result = verify or {"status": "pass", "log": "ok"}
        self.log = ci_log
        self.fix_cost = fix_cost
        self.calls: list[tuple[Any, ...]] = []
        self.body_now = BODY
        self.bodies: list[str] = []

    def review(self, cut: pr_loop.Cut, round_no: int, budget: float | None) -> dict[str, Any]:
        self.calls.append(("review", round_no, budget))
        return self.reviews[min(round_no - 1, len(self.reviews) - 1)]

    def validate(self, cut: pr_loop.Cut, findings: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(("validate", [f["id"] for f in findings]))
        if self.validations:
            return self.validations.pop(0)
        return {
            "status": "ok",
            "cost_usd": 0.01,
            "comments": [{"id": f["id"], "confirmed": True, "reason": "tak"} for f in findings],
        }

    def checks(self, cut: pr_loop.Cut) -> dict[str, Any]:
        self.calls.append(("checks",))
        return self.checks_seq.pop(0) if len(self.checks_seq) > 1 else self.checks_seq[0]

    def ci_log(self, cut: pr_loop.Cut, checks: dict[str, Any]) -> str:
        self.calls.append(("ci_log",))
        return self.log

    def verify(self, cut: pr_loop.Cut) -> dict[str, Any]:
        self.calls.append(("verify",))
        return self.verify_result

    def fix(self, cut: pr_loop.Cut, round_no: int, data: dict[str, Any], budget: float | None) -> dict[str, Any]:
        self.calls.append(("fix", round_no, [c["id"] for c in data.get("comments") or []], data.get("ci_log"), budget))
        return {"status": "ok", "cost_usd": self.fix_cost}

    def push(self, cut: pr_loop.Cut) -> None:
        self.calls.append(("push",))

    def commits(self, cut: pr_loop.Cut) -> list[str]:
        return ["feat(page): znacznik środowiska", "docs(CHG-4): raport TSK-1"]

    def body(self, cut: pr_loop.Cut) -> str:
        return self.body_now

    def edit_body(self, cut: pr_loop.Cut, body: str) -> None:
        self.body_now = body
        self.bodies.append(body)


def run(steps: FakeSteps, **kw: Any) -> dict[str, Any]:
    updates: list[dict[str, Any]] = []
    out = pr_loop.run_loop([CUT], steps, on_update=lambda s: updates.append(s), **kw)
    assert updates, "stan zapisywany w trakcie (konsola)"
    return out[PR]


def ok(*findings: dict[str, Any], cost: float = 0.05) -> dict[str, Any]:
    return {"status": "ok", "review_md": "product", "cost_usd": cost, "findings": list(findings)}


def kinds(steps: FakeSteps) -> list[str]:
    return [c[0] for c in steps.calls]


def test_green_after_first_round_without_findings() -> None:
    steps = FakeSteps([ok()])
    entry = run(steps)
    assert entry["status"] == "green" and entry["round"] == 1
    assert "fix" not in kinds(steps) and "validate" not in kinds(steps)
    assert "## Przewodnik dokończenia" in steps.body_now and "Change: CHG-4" in steps.body_now


def test_fix_then_green_in_second_round() -> None:
    steps = FakeSteps([ok(finding("R1")), ok()])
    entry = run(steps)
    assert entry["status"] == "green" and entry["round"] == 2
    fix = next(c for c in steps.calls if c[0] == "fix")
    assert fix[2] == ["R1"]
    assert kinds(steps).index("push") > kinds(steps).index("fix")
    assert entry["fixed"] == ["R1"] and len(entry["rounds"]) == 2
    assert "R1" in steps.bodies[-1] and len(steps.bodies) == 2  # przewodnik po każdej rundzie


def test_limit_reached_goes_to_human_with_open_comments() -> None:
    steps = FakeSteps([ok(finding("R1")), ok(finding("R2")), ok(finding("R3"))])
    entry = run(steps, max_rounds=2)
    assert entry["status"] == "needs_human"
    assert entry["reason"].startswith("nie udało się po 2 rundach")
    assert [c[1] for c in steps.calls if c[0] == "fix"] == [1, 2]
    assert [o["id"] for o in entry["open"]] == ["R3"]
    assert "nie udało się po 2 rundach" in steps.body_now and "R3" in steps.body_now


def test_early_exit_when_only_minor_remain() -> None:
    steps = FakeSteps([ok(finding("R1", "minor"), finding("R2", "minor"))])
    entry = run(steps)
    assert entry["status"] == "green" and "fix" not in kinds(steps) and "validate" not in kinds(steps)
    assert [m["id"] for m in entry["minor"]] == ["R1", "R2"]
    assert "### Drobne uwagi (poza pętlą)" in steps.body_now and "uwaga R2" in steps.body_now


def test_unvalidated_comment_goes_to_human_not_to_fix() -> None:
    validation = {
        "status": "ok",
        "cost_usd": 0.01,
        "comments": [
            {"id": "R1", "confirmed": True, "reason": "tak"},
            {"id": "R2", "confirmed": False, "reason": "kodu nie ma"},
        ],
    }
    steps = FakeSteps([ok(finding("R1"), finding("R2")), ok()], validations=[validation])
    entry = run(steps)
    fix = next(c for c in steps.calls if c[0] == "fix")
    assert fix[2] == ["R1"]
    assert entry["status"] == "needs_human"  # zielone, ale zostało pytanie
    assert any(
        q["id"] == "R2" and "[niepotwierdzone]" in q["text"] and "kodu nie ma" in q["text"] for q in entry["questions"]
    )


def test_validation_unavailable_means_question_and_risk() -> None:
    steps = FakeSteps([ok(finding("R1"))], validations=[{"status": "unavailable", "reason": "no_api_key"}])
    entry = run(steps)
    assert "fix" not in kinds(steps)
    assert entry["status"] == "needs_human"
    assert entry["questions"][0]["text"].startswith("[niepotwierdzone: drugi przegląd niedostępny (no_api_key)]")
    assert "drugi przegląd niedostępny (no_api_key)" in steps.body_now.split("### Ryzyka", 1)[1]


def test_comment_contradicting_decision_goes_to_human_with_ref() -> None:
    steps = FakeSteps([ok(finding("R1", decision_ref="CHG-4/D2"))])
    entry = run(steps)
    assert "fix" not in kinds(steps) and "validate" not in kinds(steps)
    assert entry["questions"][0]["text"].startswith("[sprzeczne z CHG-4/D2]")


def test_red_check_log_goes_to_fix_then_green() -> None:
    red = {
        "state": "red",
        "checks": [{"name": "check", "bucket": "fail", "link": "https://github.com/o/r/actions/runs/7/job/9"}],
    }
    green = {"state": "green", "checks": [{"name": "check", "bucket": "pass"}]}
    steps = FakeSteps([ok(), ok()], checks=[red, green], ci_log="FAILED test_badge\nAssertionError")
    entry = run(steps)
    fix = next(c for c in steps.calls if c[0] == "fix")
    assert fix[2] == [] and "FAILED test_badge" in fix[3]
    assert entry["status"] == "green" and entry["rounds"][0]["checks"]["state"] == "red"


def test_no_checks_is_not_green() -> None:
    steps = FakeSteps([ok()], checks=[{"state": "none", "checks": []}])
    entry = run(steps)
    assert "verify" in kinds(steps)
    assert entry["status"] == "needs_human" and entry["reason"].startswith("no_ci_checks")


def test_no_checks_and_failing_local_verify_is_fixed() -> None:
    steps = FakeSteps(
        [ok(), ok()],
        checks=[{"state": "none", "checks": []}, {"state": "green", "checks": [{}]}],
        verify={"status": "fail", "log": "npm test: 1 failing"},
    )
    entry = run(steps)
    fix = next(c for c in steps.calls if c[0] == "fix")
    assert "1 failing" in fix[3]
    assert entry["status"] == "green"


def test_cost_per_round_and_budget() -> None:
    steps = FakeSteps([ok(finding("R1"), cost=0.2), ok(finding("R2"), cost=0.2)], fix_cost=0.5)
    entry = run(steps, budget_usd=1.0)
    assert entry["rounds"][0]["cost_usd"] == pytest.approx(0.2 + 0.01 + 0.5)
    assert steps.calls[0] == ("review", 1, 1.0)
    # po 1. rundzie zostało 0.29; 2. przegląd 0.2 + walidacja 0.01 → 0.08 < koszt poprawki? pętla nie przerywa,
    # bo budżet > 0; poprawka dostaje pozostałą kwotę
    second_fix = [c for c in steps.calls if c[0] == "fix"][1]
    assert second_fix[4] == pytest.approx(1.0 - 0.71 - 0.21)
    assert entry["cost_usd"] == pytest.approx(sum(r["cost_usd"] for r in entry["rounds"]))


def test_budget_exhausted_stops_loop() -> None:
    steps = FakeSteps([ok(finding("R1"), cost=0.6)])
    entry = run(steps, budget_usd=0.5)
    assert entry["status"] == "needs_human" and entry["reason"].startswith("budget")
    assert "fix" not in kinds(steps)


def test_review_failure_goes_to_human() -> None:
    steps = FakeSteps([{"status": "failed", "reason": "no_structured_output", "cost_usd": 0.01, "findings": []}])
    entry = run(steps)
    assert entry["status"] == "needs_human" and "no_structured_output" in entry["reason"]


def test_replace_guide_keeps_report_and_change_line() -> None:
    first = pr_loop.replace_guide(BODY, "## Przewodnik dokończenia\n\nA")
    second = pr_loop.replace_guide(first, "## Przewodnik dokończenia\n\nB")
    assert second.count("## Przewodnik dokończenia") == 1 and "\nB\n" in second and "\nA\n" not in second
    assert second.startswith("# Raport przebiegu TSK-1") and second.rstrip().endswith("Change: CHG-4")
    assert "duplikaty CDR" in second


def test_guide_lists_decisions_outside_plan() -> None:
    steps = FakeSteps([ok()])
    run(steps)
    guide = steps.body_now.split("## Przewodnik dokończenia", 1)[1]
    assert "duplikaty CDR między plikami" in guide and "[założenie] znacznik tylko w nagłówku" in guide
    assert "feat(page): znacznik środowiska" in guide


def test_checks_state_and_run_id() -> None:
    assert pr_loop.checks_state([]) == "none"
    assert pr_loop.checks_state([{"bucket": "pass"}, {"bucket": "skipping"}]) == "green"
    assert pr_loop.checks_state([{"bucket": "pass"}, {"bucket": "pending"}]) == "pending"
    assert pr_loop.checks_state([{"bucket": "cancel"}, {"bucket": "pending"}]) == "red"
    assert pr_loop.run_id_of("https://github.com/o/r/actions/runs/123/job/456") == "123"
    assert pr_loop.run_id_of("https://example.com/x") is None
