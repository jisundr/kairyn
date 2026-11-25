"""afk.py: the script that runs the build, gates and review stages AFK (task 2026-11-23-build-stage).

Tests run afk.py against tests/stubs/claude, so they cost no tokens. Test names carry the
design slice (`slice1` ... `slice6`) so each slice's done condition is `pytest -k slice<n>`.
"""
import os
import re
import subprocess
import sys

import pytest

from helpers import PLUGIN, ROOT

AFK = PLUGIN / "scripts" / "afk.py"
STUB = ROOT / "tests" / "stubs" / "claude"
TASK = "2026-01-05-feature"
# Runs every check_*.py, so it passes on the base commit (no checks yet) and after build.
GOOD_GATE = 'python3 -c "import glob; [__import__(f[:-3]) for f in sorted(glob.glob(\'check_*.py\'))]"'

STATE = """---
task: {task}
title: Feature
stage: build
status: in-progress
stages:
  requirements: done
  design: done
  build: pending
  gates: pending
  review: pending
created: 2026-01-05T09:00:00Z
updated: 2026-01-05T09:20:00Z
---

# Log

2026-01-05T09:20:00Z [design] Approved by Eval User.
"""

DESIGN = """---
task: {task}
stage: design
summary: "two slices"
---

# Design: Feature

## Tasks
- T1: Tracer bullet. Done: `python3 check_t1.py` exits 0.
- T2: Widen it. after: T1. Done: `python3 check_t2.py` exits 0.

Approval: Eval User, 2026-01-05T09:20:00Z, "Approve"
"""


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for k, v in (("user.name", "Eval User"), ("user.email", "eval@example.com")):
        git(root, "config", k, v)
    task = root / "docs" / "tasks" / TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(STATE.format(task=TASK))
    (task / "DESIGN.md").write_text(DESIGN.format(task=TASK))
    (root / ".kairyn").mkdir()
    (root / ".kairyn" / "afk.yml").write_text(f"gates:\n  testing: {GOOD_GATE}\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


def run(repo, *args, mode="good", log=None):
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "STUB_LOG": str(log or repo.parent / "stub.log"),
           "STUB_MODE": mode}
    return subprocess.run([sys.executable, str(AFK), *args, "--root", str(repo)], capture_output=True, text=True,
                          env=env)


def worktree(repo):
    return repo / ".git" / "kairyn" / "worktrees" / TASK


def task_file(repo, name):
    return (worktree(repo) / "docs" / "tasks" / TASK / name).read_text()


def front(text, key):
    m = re.search(rf"^{key}:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def calls(repo):
    log = repo.parent / "stub.log"
    return log.read_text().splitlines() if log.exists() else []


# --- slice 1: tracer bullet ------------------------------------------------------------------


def test_slice1_task_graph_orders_by_blockers():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    text = "## Tasks\n- T1: a. after: T3. Done: `x1` exits 0.\n- T2: b. Done: `x2` exits 0.\n- T3: c. Done: `x3` exits 0.\n"
    assert [t.id for t in afk.task_graph(text)] == ["T2", "T3", "T1"]
    assert afk.task_graph(text)[0].done == "x2"


def test_slice1_task_graph_rejects_a_cycle_and_a_missing_done():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    with pytest.raises(ValueError, match="cycle"):
        afk.task_graph("- T1: a. after: T2. Done: `x` exits 0.\n- T2: b. after: T1. Done: `y` exits 0.\n")
    with pytest.raises(ValueError, match="T1 has no done command"):
        afk.task_graph("- T1: a.\n")


def test_slice1_afk_yml_sections():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    data = afk.parse_afk("# limits\nlimits:\n  build_usd: 10\ngates:\n  testing: pytest -q  # all\n  security:\n"
                         "approval:\n  - '**/migrations/**'\n")
    assert data == {"limits": {"build_usd": 10}, "gates": {"testing": "pytest -q", "security": ""},
                    "approval": ["**/migrations/**"]}
    assert list(data["gates"]) == ["testing", "security"]


def test_slice1_order_resume(repo):
    result = run(repo, "run", TASK)
    assert result.returncode == 0, result.stdout + result.stderr
    prompts = [p for p in calls(repo) if "reviewer" not in p]
    assert [re.search(r"\bT\d\b", p).group(0) for p in prompts[:2]] == ["T1", "T2"]
    assert all("BUILD.md" in p for p in prompts[:2]) and "REVIEW.md" in prompts[2] and len(prompts) == 3
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked")
    assert re.search(r"^  build: done$", state, re.M) and re.search(r"^  gates: done$", state, re.M)
    assert git(worktree(repo), "branch", "--show-current").strip() == f"kairyn/{TASK}"
    # A blocked task does not run again.
    again = run(repo, "run", TASK)
    assert again.returncode == 0 and len(calls(repo)) == 4
    assert "blocked" in again.stdout


def test_slice1_resumes_at_the_stage_in_state(repo):
    run(repo, "run", TASK)
    wt = worktree(repo)
    state = wt / "docs" / "tasks" / TASK / "STATE.md"
    text = state.read_text().replace("stage: review", "stage: gates").replace("status: blocked", "status: in-progress")
    state.write_text(text)
    (repo.parent / "stub.log").unlink()
    assert run(repo, "run", TASK).returncode == 0
    prompts = calls(repo)
    assert len(prompts) == 1 and "REVIEW.md" in prompts[0], "resume at gates runs no build session"


def test_slice1_red_green(repo):
    assert run(repo, "run", TASK).returncode == 0
    build = task_file(repo, "BUILD.md")
    assert front(build, "stage") == "build"
    row = next(line for line in build.splitlines() if line.startswith("| T1 |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    test_sha, red, feat_sha, green = cells[1], cells[2], cells[3], cells[4]
    log = git(worktree(repo), "log", "--format=%h %s")
    assert f"{test_sha} test(T1)" in log and f"{feat_sha} feat(T1)" in log
    assert red != "0" and green == "0"


def test_slice1_a_red_check_that_passes_fails_build(repo):
    result = run(repo, "run", TASK, mode="no_red")
    assert result.returncode == 0, result.stderr
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"\[build\] .*T1.*red check", state)
    assert len(calls(repo)) == 1, "the run stops at the first failed slice"


def test_slice1_gate(repo):
    assert run(repo, "run", TASK).returncode == 0
    gates = task_file(repo, "GATES.md")
    assert re.search(r"^\| testing \| pass \| 0 \|", gates, re.M)


def test_slice1_failing_gate_blocks(repo):
    gate = "python3 -c \"import os, sys; sys.exit(3 if os.path.exists('feature_t1.py') else 0)\""
    (repo / ".kairyn" / "afk.yml").write_text(f"gates:\n  testing: {gate}\n")
    git(repo, "commit", "-qam", "failing gate")
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert re.search(r"\[gates\] .*testing", state)
    assert "REVIEW.md" not in " ".join(calls(repo))


def test_slice1_approve(repo):
    run(repo, "run", TASK)
    result = run(repo, "approve", TASK, "--words", "Ship it")
    assert result.returncode == 0, result.stdout + result.stderr
    review = task_file(repo, "REVIEW.md")
    assert re.search(r'^Decision: Eval User, \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ, "Ship it"$', review, re.M)
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "done")
    assert re.search(r"^  review: done$", state, re.M)


def test_slice1_approve_needs_a_pending_decision(repo):
    result = run(repo, "approve", TASK, "--words", "Ship it")
    assert result.returncode == 1 and result.stdout.startswith("FAIL:")


# --- slice 2: reviewer, one fix round, flags ---------------------------------------------------


def reviewer_calls(repo):
    return [p for p in calls(repo) if "reviewer" in p]


def test_slice2_reviewer_runs_read_only_after_build(repo):
    assert run(repo, "run", TASK).returncode == 0
    prompts = calls(repo)
    order = ["T1" if "T1" in p and "BUILD.md" in p else "T2" if "T2" in p and "BUILD.md" in p else
             "reviewer" if "reviewer" in p else "review" for p in prompts]
    assert order == ["T1", "T2", "reviewer", "review"]
    args = (repo.parent / "stub.log.args").read_text().splitlines()[2]
    assert "--disallowedTools" in args and "Edit" in args and "Write" in args
    assert "bypassPermissions" not in args
    assert "Findings: none" in task_file(repo, "BUILD.md")


def test_slice2_fix_round_clears_a_finding(repo):
    assert run(repo, "run", TASK, mode="review_fixable").returncode == 0
    assert sum("fix round" in p and "reviewer" not in p for p in calls(repo)) == 1 and len(reviewer_calls(repo)) == 2
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked"), "the run reached review"
    assert "fix: cover VALUE 0" in git(worktree(repo), "log", "--format=%s")
    assert "feature_t1.VALUE has no test for 0." in task_file(repo, "BUILD.md")


def test_slice2_escalates(repo):
    """D3: one fix round only. A finding that stays blocks the run with the finding."""
    assert run(repo, "run", TASK, mode="review_stuck").returncode == 0
    assert sum("fix round" in p and "reviewer" not in p for p in calls(repo)) == 1 and len(reviewer_calls(repo)) == 2
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"\[build\] Blocked: .*fix round.*feature_t1.VALUE has no test for 0", state)


def test_slice2_fix_round_must_stay_green(repo, tmp_path):
    """D3: after the fix round each done command must still exit 0."""
    (repo / "docs" / "tasks" / TASK / "DESIGN.md").write_text(
        DESIGN.format(task=TASK).replace("`python3 check_t2.py`", "`python3 check_t2.py && grep -vq fixed feature_t1.py`"))
    git(repo, "commit", "-qam", "green check that the fix breaks")
    assert run(repo, "run", TASK, mode="review_fixable").returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"\[build\] Blocked: .*T2.*after the fix round", state)


def test_slice2_flags(repo):
    """D12, D19: a feat commit that edits a test file, and an added escape hatch, are listed for the reviewer."""
    assert run(repo, "run", TASK, mode="weaken").returncode == 0
    build = task_file(repo, "BUILD.md")
    assert re.search(r"test edit: `check_t1.py` in feat\(T1\)", build)
    assert "check_t1.py" in reviewer_calls(repo)[0]


def test_slice2_escape_hatch_flag(repo):
    assert run(repo, "run", TASK, mode="noqa").returncode == 0
    build = task_file(repo, "BUILD.md")
    assert re.search(r"escape hatch: `feature_t1.py:1` `# noqa` in feat\(T1\)", build)
    assert "# noqa" in reviewer_calls(repo)[0]


def test_slice2_escape_hatches_come_from_afk_yml():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    assert "# noqa" in afk.escape_patterns({})
    assert afk.escape_patterns({"escape_hatches": ["TODO"]}) == ["TODO"]


def test_slice2_review_and_retro_turn_findings_into_constraints():
    """D20: review writes leftover findings to learnings as constraints; retro sends them to the backlog."""
    review = (PLUGIN / "stages" / "REVIEW.md").read_text()
    assert "learnings.md" in review.split("## Learnings", 1)[1] and "lint rule" in review
    steps = (PLUGIN / "stages" / "RETRO.md").read_text().split("## Steps", 1)[1]
    assert "agent-written code" in steps and "lint rule" in steps


# --- slice 3: readiness check and limits -------------------------------------------------------


def set_afk(repo, text):
    (repo / ".kairyn" / "afk.yml").write_text(text)
    git(repo, "commit", "-qam", "afk.yml")


def test_slice3_readiness_needs_a_testing_command(repo):
    set_afk(repo, "gates:\n  testing:\n  security:\n")
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"\[build\] Blocked: readiness: .*testing", state) and calls(repo) == []


def test_slice3_readiness_needs_gates_green_on_the_base(repo):
    set_afk(repo, "gates:\n  testing: python3 -c 'raise SystemExit(4)'\n")
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert re.search(r"\[build\] Blocked: readiness: gate testing exits 4 on the base commit", state)
    assert calls(repo) == []


def test_slice3_readiness_needs_a_clean_worktree(repo):
    run(repo, "run", TASK, mode="review_stuck")
    wt = worktree(repo)
    (wt / "feature_t1.py").write_text("VALUE = 9\n")
    state = wt / "docs" / "tasks" / TASK / "STATE.md"
    state.write_text(state.read_text().replace("status: blocked", "status: in-progress"))
    n = len(calls(repo))
    assert run(repo, "run", TASK).returncode == 0
    assert re.search(r"\[build\] Blocked: readiness: the worktree has changes: feature_t1.py", task_file(repo, "STATE.md"))
    assert len(calls(repo)) == n


def test_slice3_readiness_ignores_untracked_files(repo):
    """The tracer run left __pycache__/ in the worktree; that must not block a resume."""
    run(repo, "run", TASK, mode="review_stuck")
    wt = worktree(repo)
    (wt / "__pycache__").mkdir(exist_ok=True)
    (wt / "__pycache__" / "x.pyc").write_text("")
    state = wt / "docs" / "tasks" / TASK / "STATE.md"
    state.write_text(state.read_text().replace("status: blocked", "status: in-progress"))
    run(repo, "run", TASK, mode="good")
    assert "readiness" not in task_file(repo, "STATE.md")


def args_log(repo):
    return (repo.parent / "stub.log.args").read_text().splitlines()


def test_slice3_limits_stage_cost(repo):
    set_afk(repo, f"limits:\n  build_usd: 10\n  run_usd: 20\ngates:\n  testing: {GOOD_GATE}\n")
    r = subprocess.run([sys.executable, str(AFK), "run", TASK, "--root", str(repo)], capture_output=True, text=True,
                       env={**os.environ, "KAIRYN_CLAUDE": str(STUB), "STUB_LOG": str(repo.parent / "stub.log"),
                            "STUB_COST": "6"})
    assert r.returncode == 0, r.stderr
    budgets = [re.search(r"--max-budget-usd (\S+)", a).group(1) for a in args_log(repo)]
    assert budgets[:2] == ["10.00", "4.00"], "each session gets what is left of the stage cap"
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"Blocked: limit build_usd \$10 reached: spent \$12\.00 in build, \$12\.00 in this run\. "
                     r"Last failed command: `python3 check_t2.py` exit 1 at the red check", state)


def test_slice3_limits_run_cost(repo):
    set_afk(repo, f"limits:\n  build_usd: 10\n  run_usd: 5\ngates:\n  testing: {GOOD_GATE}\n")
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "STUB_LOG": str(repo.parent / "stub.log"), "STUB_COST": "3"}
    subprocess.run([sys.executable, str(AFK), "run", TASK, "--root", str(repo)], env=env, capture_output=True)
    assert re.search(r"Blocked: limit run_usd \$5 reached: spent \$6\.00", task_file(repo, "STATE.md"))


def test_slice3_limits_stage_time(repo):
    set_afk(repo, f"limits:\n  stage_minutes: 0.01\ngates:\n  testing: {GOOD_GATE}\n")
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "STUB_LOG": str(repo.parent / "stub.log"), "STUB_SLEEP": "3"}
    subprocess.run([sys.executable, str(AFK), "run", TASK, "--root", str(repo)], env=env, capture_output=True)
    assert re.search(r"Blocked: limit stage_minutes 0.01 reached in build", task_file(repo, "STATE.md"))


def test_slice3_limit_names_the_last_failed_command(repo):
    """D8: a limit logs the last failed command with its output."""
    set_afk(repo, f"limits:\n  build_usd: 1\ngates:\n  testing: {GOOD_GATE}\n")
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "STUB_LOG": str(repo.parent / "stub.log"), "STUB_COST": "2"}
    subprocess.run([sys.executable, str(AFK), "run", TASK, "--root", str(repo)], env=env, capture_output=True)
    state = task_file(repo, "STATE.md")
    assert re.search(r"Last failed command: `python3 check_t1.py` exit 1 at the red check: .*ModuleNotFoundError", state)


def test_slice3_stage_cost_is_logged(repo):
    assert run(repo, "run", TASK).returncode == 0
    assert re.search(r"\[build\] All 2 tasks green\. Cost \$0\.75\. Next: gates\.", task_file(repo, "STATE.md"))


def test_slice3_afk_yml_template_parses_with_defaults():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    data = afk.parse_afk((PLUGIN / "templates" / "afk.yml").read_text())
    assert data["limits"] == afk.DEFAULT_LIMITS
    assert list(data["gates"]) == ["testing", "contract", "accessibility", "performance", "observability", "security"]
    assert set(data["gates"].values()) == {""}
    assert afk.escape_patterns(data) == afk.DEFAULT_ESCAPES


def test_slice3_a_session_that_runs_out_of_budget_is_a_limit(repo):
    """The real CLI exits 1 with subtype error_max_budget_usd and an empty result (tracer run 2026-11-23)."""
    run(repo, "run", TASK, mode="budget")
    state = task_file(repo, "STATE.md")
    assert re.search(r"Blocked: limit build_usd \$10 reached in a session: Reached maximum budget \(\$0\.01\)\. "
                     r"Spent \$0\.13 in build", state)


# --- slice 4: approval gates ---------------------------------------------------------------------


def mark_t2_for_approval(repo):
    design = repo / "docs" / "tasks" / TASK / "DESIGN.md"
    design.write_text(design.read_text().replace("- T2: Widen it.", "- T2: Widen it (approval)."))
    git(repo, "commit", "-qam", "mark T2")


def test_slice4_task_graph_reads_approval_marks():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    graph = afk.task_graph("- T1: a. Done: `x` exits 0.\n- T2: b (approval). after: T1. Done: `y` exits 0.\n")
    assert [t.approval for t in graph] == [False, True]


def test_slice4_approval(repo):
    """D10: build stops before a marked slice; approve records the line and the next run builds it."""
    mark_t2_for_approval(repo)
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("build", "blocked")
    assert re.search(r"\[build\] Blocked: T2 is marked \(approval\)", state)
    assert not any("T2" in p for p in calls(repo)), "no session runs for T2 before the approval"
    result = run(repo, "approve", TASK, "--slice", "T2", "--words", "Migration is fine")
    assert result.returncode == 0, result.stdout
    assert re.search(r'^Approval T2: Eval User, \d{4}-\d\d-\d\dT[\d:]+Z, "Migration is fine"$', task_file(repo, "BUILD.md"),
                     re.M)
    assert front(task_file(repo, "STATE.md"), "status") == "in-progress"
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked")


def test_slice4_approve_a_slice_needs_a_marked_slice(repo):
    run(repo, "run", TASK)
    result = run(repo, "approve", TASK, "--slice", "T9", "--words", "ok")
    assert result.returncode == 1 and "T9" in result.stdout


def test_slice4_backstop(repo):
    """D10: a changed path that matches approval: with no approval blocks before the next stage."""
    set_afk(repo, f"approval:\n  - '**/feature_t2.py'\ngates:\n  testing: {GOOD_GATE}\n")
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert re.search(r"\[gates\] Blocked: approval: `feature_t2.py` matches `\*\*/feature_t2.py` in feat\(T2\)", state)
    assert not any("REVIEW.md" in p for p in calls(repo))
    assert run(repo, "approve", TASK, "--slice", "T2", "--words", "ok").returncode == 0
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked")


def test_slice4_path_patterns():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    assert afk.path_matches("db/migrations/001.sql", "**/migrations/**")
    assert afk.path_matches("migrations/001.sql", "**/migrations/**")
    assert not afk.path_matches("src/app.py", "**/migrations/**")


def test_slice4_design_marks_approval_slices():
    steps = (PLUGIN / "stages" / "DESIGN.md").read_text().split("## Steps", 1)[1].split("\n## ", 1)[0]
    assert "(approval)" in steps and "approval:" in steps


# --- slice 5: the full gate chain ---------------------------------------------------------------

SIX = ("testing", "contract", "accessibility", "performance", "observability", "security")


def gate_rows(repo):
    return [[c.strip() for c in line.strip("|").split("|")] for line in task_file(repo, "GATES.md").splitlines()
            if line.startswith("| ") and not line.startswith("| Gate")]


def test_slice5_gates(repo):
    """D9: gates run in order; the exit code decides; an empty command is `not set`, never a pass."""
    set_afk(repo, f"gates:\n  testing: {GOOD_GATE}\n  contract:\n  accessibility:\n  performance: true\n"
                  "  observability:\n  security: true\n")
    assert run(repo, "run", TASK).returncode == 0
    rows = gate_rows(repo)
    assert [r[0] for r in rows] == list(SIX)
    assert [r[1] for r in rows] == ["pass", "not set", "not set", "pass", "not set", "pass"]
    assert front(task_file(repo, "STATE.md"), "stage") == "review"
    assert re.search(r"\[gates\] 3 pass, 3 not set: contract, accessibility, observability\.", task_file(repo, "STATE.md"))


def test_slice5_security_runs_last(repo):
    set_afk(repo, f"gates:\n  testing: {GOOD_GATE}\n  security: true\n  performance: true\n")
    assert run(repo, "run", TASK).returncode == 0
    assert re.search(r"Blocked: readiness: the security gate must be last", task_file(repo, "STATE.md"))
    assert calls(repo) == []


def test_slice5_ai_check_runs_after_its_command(repo):
    """D9: an AI check runs inside a gate only after the gate's command passes, read-only."""
    set_afk(repo, f"gates:\n  testing: {GOOD_GATE}\n  observability: true\n  security:\n"
                  "checks:\n  observability: Each new code path writes a log line.\n  security: No secret in the diff.\n")
    assert run(repo, "run", TASK).returncode == 0
    checks = [p for p in calls(repo) if "gate check" in p]
    assert len(checks) == 1 and "Each new code path writes a log line." in checks[0], "no check for a not set gate"
    args = [a for a, p in zip(args_log(repo), calls(repo)) if "gate check" in p][0]
    assert "--disallowedTools" in args
    assert gate_rows(repo)[1][:4] == ["observability", "pass", "0", "check: pass"]


def test_slice5_a_failed_ai_check_fails_the_gate(repo):
    set_afk(repo, f"gates:\n  testing: {GOOD_GATE}\n  observability: true\n"
                  "checks:\n  observability: Each new code path writes a log line.\n")
    assert run(repo, "run", TASK, mode="gate_fail").returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert re.search(r"Blocked: gate observability check failed: no log line for the new path", state)
    assert gate_rows(repo)[1][:4] == ["observability", "fail", "0", "check: no log line for the new path"]


# --- slice 6: push, pull request, merge, install -------------------------------------------------

GH = ROOT / "tests" / "stubs" / "gh"


def with_remote(repo):
    remote = repo.parent / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "main")
    return remote


def run_gh(repo, *args, mode="good", gh_mode=""):
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "KAIRYN_GH": str(GH), "STUB_LOG": str(repo.parent / "stub.log"),
           "STUB_MODE": mode, "GH_LOG": str(repo.parent / "gh.log"), "GH_MODE": gh_mode}
    return subprocess.run([sys.executable, str(AFK), *args, "--root", str(repo)], capture_output=True, text=True,
                          env=env)


def gh_calls(repo):
    log = repo.parent / "gh.log"
    return log.read_text().splitlines() if log.exists() else []


def test_slice6_gh(repo):
    """D11: build ends with a push and one pull request; review posts REVIEW.md; approve merges."""
    remote = with_remote(repo)
    assert run_gh(repo, "run", TASK).returncode == 0
    calls_ = gh_calls(repo)
    assert any(c.startswith(f"pr create --base main --head kairyn/{TASK}") for c in calls_)
    assert sum(c.startswith("pr create") for c in calls_) == 1
    assert any(c.startswith(f"pr comment kairyn/{TASK} --body-file ") and c.endswith("REVIEW.md") for c in calls_)
    branch_tip = subprocess.run(["git", "-C", str(remote), "rev-parse", f"kairyn/{TASK}"], capture_output=True,
                                text=True).stdout.strip()
    assert branch_tip == git(worktree(repo), "rev-parse", "HEAD").strip(), "the pushed branch has the review commit"
    assert "https://github.com/example/repo/pull/1" in task_file(repo, "STATE.md")
    result = run_gh(repo, "approve", TASK, "--words", "Ship it")
    assert result.returncode == 0, result.stdout + result.stderr
    assert gh_calls(repo)[-1] == f"pr merge kairyn/{TASK} --merge"
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "done")


def test_slice6_merge_failure_blocks(repo):
    with_remote(repo)
    run_gh(repo, "run", TASK)
    result = run_gh(repo, "approve", TASK, "--words", "Ship it", gh_mode="merge_fail")
    assert result.returncode == 1 and "base branch policy" in result.stdout
    state = task_file(repo, "STATE.md")
    assert front(state, "status") == "blocked"
    assert re.search(r'^Decision: Eval User, .*"Ship it"$', task_file(repo, "REVIEW.md"), re.M)
    assert re.search(r"\[review\] Blocked: gh pr merge failed: .*base branch policy", state)


def test_slice6_no_remote(repo):
    """D11: with no remote, nothing is pushed and approve only records the decision."""
    assert run_gh(repo, "run", TASK).returncode == 0
    assert gh_calls(repo) == []
    assert re.search(r"\[build\] No remote: no push and no pull request\.", task_file(repo, "STATE.md"))
    assert run_gh(repo, "approve", TASK, "--words", "Ship it").returncode == 0
    assert gh_calls(repo) == [] and front(task_file(repo, "STATE.md"), "status") == "done"


def test_slice6_no_gh(repo):
    with_remote(repo)
    env = {**os.environ, "KAIRYN_CLAUDE": str(STUB), "KAIRYN_GH": str(repo.parent / "missing-gh"),
           "STUB_LOG": str(repo.parent / "stub.log")}
    subprocess.run([sys.executable, str(AFK), "run", TASK, "--root", str(repo)], env=env, capture_output=True)
    state = task_file(repo, "STATE.md")
    assert re.search(r"\[build\] Pushed kairyn/2026-01-05-feature\. No gh: no pull request\.", state)
    assert front(state, "stage") == "review"


def test_slice6_init(tmp_path):
    """R16: init creates .kairyn/afk.yml from the template; afk.py creates it in a repo set up before."""
    from helpers import make_good_repo
    repo = make_good_repo(tmp_path / "fresh")
    assert (repo / ".kairyn" / "afk.yml").read_text() == (PLUGIN / "templates" / "afk.yml").read_text()


def test_slice6_init_keeps_an_edited_afk_yml(tmp_path):
    from helpers import make_good_repo
    repo = make_good_repo(tmp_path / "fresh")
    (repo / ".kairyn" / "afk.yml").write_text("gates:\n  testing: make test\n")
    subprocess.run(["bash", str(PLUGIN / "scripts" / "init.sh"), str(repo)], check=True, capture_output=True)
    assert (repo / ".kairyn" / "afk.yml").read_text() == "gates:\n  testing: make test\n"


def test_slice6_afk_creates_a_missing_afk_yml(repo):
    """An upgraded repo has the template but no .kairyn/afk.yml: the run creates it and stops before a worktree."""
    (repo / ".kairyn" / "afk.yml").unlink()
    (repo / ".kairyn" / "templates").mkdir()
    (repo / ".kairyn" / "templates" / "afk.yml").write_text((PLUGIN / "templates" / "afk.yml").read_text())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "upgraded repo")
    result = run(repo, "run", TASK)
    assert result.returncode == 1 and "Created .kairyn/afk.yml" in result.stdout
    assert (repo / ".kairyn" / "afk.yml").is_file() and not worktree(repo).exists()


# --- slice 8: review fixes from the real reviewer run (2026-11-23) --------------------------------


def test_slice8_reviewer_gets_the_diff_in_its_prompt(repo):
    """A PreToolUse hook (rtk) rewrote `git diff`, so the read-only reviewer could not run it. afk.py passes the diff."""
    run(repo, "run", TASK)
    prompt = reviewer_calls(repo)[0]
    assert "+VALUE = 1" in prompt and "check_t1.py" in prompt
    assert "docs/tasks/" not in prompt.split("Diff:", 1)[1], "the task's own files are not part of the diff"


def test_slice8_gate_check_gets_the_diff_in_its_prompt(repo):
    set_afk(repo, f"gates:\n  testing: {GOOD_GATE}\n  observability: true\n"
                  "checks:\n  observability: Each new code path writes a log line.\n")
    run(repo, "run", TASK)
    check = next(p for p in calls(repo) if "gate check" in p)
    assert "+VALUE = 1" in check


def test_slice8_second_review_treats_fixes_as_in_scope(repo):
    run(repo, "run", TASK, mode="review_fixable")
    second = reviewer_calls(repo)[1]
    assert "feature_t1.VALUE has no test for 0." in second and "in scope" in second


def test_slice8_adding_to_a_test_file_is_not_a_test_edit(repo):
    run(repo, "run", TASK, mode="add_test")
    assert "test edit" not in task_file(repo, "BUILD.md")


def test_slice8_diff_is_cut_when_long():
    sys.path.insert(0, str(PLUGIN / "scripts"))
    import afk
    text = afk.clip_diff("x" * 100, limit=40, stat=" a.py | 2 +-")
    assert len(text) < 200 and "a.py" in text and "cut" in text


# --- first-mate hub T1: afk.py mirrors STATE.md log lines to the milestone log ------------------


def test_afk_update_mirrors_state_log_line(repo):
    (repo / ".kairyn" / "milestones.yml").write_text("write:\n  log: .session/milestones.log\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "milestones on")
    assert run(repo, "run", TASK).returncode == 0
    log = (repo / ".session" / "milestones.log").read_text().splitlines()
    state = task_file(repo, "STATE.md")
    assert re.search(rf"^\S+Z \[{TASK}\] build: Build started\.$", log[0]), log
    for line in log:
        stamp, _, rest = line.partition(f" [{TASK}] ")
        stage, _, text = rest.partition(": ")
        assert f"{stamp} [{stage}] {text}" in state, line
    assert len(log) == len(re.findall(r"^\S+Z \[(?:build|gates|review)\] ", state, re.M)), "one milestone per afk.py log line"


def test_afk_writes_no_milestones_without_settings(repo):
    assert run(repo, "run", TASK).returncode == 0
    assert not (repo / ".session").exists()
