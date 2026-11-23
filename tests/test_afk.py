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
GOOD_GATE = 'python3 -c "import feature_t1"'

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
    (repo / ".kairyn" / "afk.yml").write_text("gates:\n  testing: python3 -c 'raise SystemExit(3)'\n")
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
    assert sum("fix round" in p for p in calls(repo)) == 1 and len(reviewer_calls(repo)) == 2
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked"), "the run reached review"
    assert "fix: cover VALUE 0" in git(worktree(repo), "log", "--format=%s")
    assert "feature_t1.VALUE has no test for 0." in task_file(repo, "BUILD.md")


def test_slice2_escalates(repo):
    """D3: one fix round only. A finding that stays blocks the run with the finding."""
    assert run(repo, "run", TASK, mode="review_stuck").returncode == 0
    assert sum("fix round" in p for p in calls(repo)) == 1 and len(reviewer_calls(repo)) == 2
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
