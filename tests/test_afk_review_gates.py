"""afk.py review gates `design`, `commits`, `sessions` and `evals` (backlog idea ship-review-gates, slices 1-3).

Each test builds kairyn/<task> by hand with STATE.md at `stage: gates`, then runs afk.py against
tests/stubs/claude. The gates stage runs the review gates first, then the afk.yml `gates:`.
"""
import importlib
import re
import sys

import pytest

import test_afk as base
from helpers import PLUGIN
from test_afk import TASK, front, git, run, task_file

sys.path.insert(0, str(PLUGIN / "scripts"))
afk = importlib.import_module("afk")
repo = base.repo   # the repo fixture of test_afk.py

NAMED = "- T1: Files: `app.py`, `tests/test_app.py`, `tests/fixtures/` . Done: `python3 check_t1.py` exits 0.\n"


def branch(repo, commits, design=NAMED, plan="", build="# Build\n"):
    """kairyn/<task> with DESIGN.md naming `design` (plus a test `plan`), the commits (message, {path: text}),
    BUILD.md text `build` and STATE.md at gates."""
    folder = repo / "docs" / "tasks" / TASK
    git(repo, "checkout", "-q", "-b", f"kairyn/{TASK}")
    text = (folder / "DESIGN.md").read_text()
    (folder / "DESIGN.md").write_text(re.sub(r"## Tasks\n(- T.*\n)+", "## Tasks\n" + design, text) + plan)
    git(repo, "commit", "-qam", f"kairyn({TASK}): design")
    for message, files in commits:
        for name, body in files.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)
    state = (folder / "STATE.md").read_text().replace("stage: build", "stage: gates").replace(
        "  build: pending", "  build: done")
    (folder / "STATE.md").write_text(state)
    (folder / "BUILD.md").write_text(build)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"kairyn({TASK}): build")
    git(repo, "checkout", "-q", "main")


def rows(repo):
    return {line.split("|")[1].strip(): line for line in task_file(repo, "GATES.md").splitlines()
            if line.startswith("| ") and not line.startswith("| Gate")}


PAIR = [("test(T1): add a test", {"tests/test_app.py": "def test_x(): pass\n"}),
        ("feat(T1): add app", {"app.py": "x = 1\n"})]


def test_review_gates_pass_and_come_first(repo):
    branch(repo, PAIR + [("learn", {".kairyn/learnings.md": "- a\n"})])
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert front(state, "stage") == "review", state
    names = list(rows(repo))
    assert names[:5] == ["design", "commits", "sessions", "evals", "testing"], names
    assert "| pass |" in rows(repo)["design"] and "| pass |" in rows(repo)["commits"]


def test_design_gate_blocks_a_file_outside_design(repo):
    branch(repo, PAIR + [("fix: more", {"other.py": "y = 2\n"})])
    run(repo, "run", TASK)
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert re.search(r"\[gates\] Blocked: gate design failed: `other\.py` changed, but DESIGN\.md does not name it",
                     state)
    assert "app.py" not in state.splitlines()[-1]
    assert "| fail |" in rows(repo)["design"] and "testing" not in rows(repo)


def test_design_gate_blocks_a_new_hook_event_outside_design(repo):
    design = NAMED.replace("`app.py`", "`app.py`, `hooks.json` (PostToolUse)")
    branch(repo, PAIR + [("feat(T1): hooks", {"hooks.json": '{"hooks": {"PostToolUse": [], "Stop": []}}'})],
           design=design)
    run(repo, "run", TASK)
    last = task_file(repo, "STATE.md").splitlines()[-1]
    assert "hook event `Stop` added to `hooks.json`" in last and "`PostToolUse`" not in last


def test_commits_gate_blocks_a_test_change_in_a_feat_commit(repo):
    commits = PAIR[:1] + [("feat(T1): add app", {"app.py": "x = 1\n", "tests/fixtures/a.json": "{}\n"})]
    branch(repo, commits)
    run(repo, "run", TASK)
    state = task_file(repo, "STATE.md")
    assert front(state, "status") == "blocked"
    assert re.search(r"Blocked: gate commits failed: \w+ feat\(T1\) changes the test file `tests/fixtures/a\.json`",
                     state)


def test_commits_gate_counts_a_file_from_a_test_commit_as_a_test(repo):
    """The stub's tests are check_t<n>.py: a test(T<n>) commit makes a file a test file, whatever its name."""
    commits = [("test(T1): add check", {"check_t1.py": "import app\n"}),
               ("feat(T1): add app", {"app.py": "x = 1\n"}),
               ("fix: weaken", {"check_t1.py": "pass\n"})]
    branch(repo, commits, design=NAMED.replace("`app.py`", "`app.py`, `check_t1.py`"))
    run(repo, "run", TASK)
    last = task_file(repo, "STATE.md").splitlines()[-1]
    assert "fix edits the test file `check_t1.py` in the fix round" in last


def test_commits_gate_allows_a_fix_commit_that_only_adds_test_lines(repo):
    branch(repo, PAIR + [("fix: finding", {"tests/test_app.py": "def test_x(): pass\ndef test_y(): pass\n"})])
    run(repo, "run", TASK)
    assert front(task_file(repo, "STATE.md"), "stage") == "review", task_file(repo, "STATE.md")


def test_commits_gate_allows_a_red_test_commit_in_the_fix_round(repo):
    """A fix-round test edit is fine in a test(...) commit where the testing gate fails."""
    commits = PAIR + [("test(review): stricter", {"check_t1.py": "import app\nassert app.x == 2\n"}),
                      ("fix: pass it", {"app.py": "x = 2\n"})]
    (repo / ".kairyn" / "afk.yml").write_text("gates:\n  testing: python3 check_t1.py\n")
    (repo / "check_t1.py").write_text("pass\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "testing gate")
    branch(repo, commits, design=NAMED.replace("`app.py`", "`app.py`, `check_t1.py`"))
    run(repo, "run", TASK)
    assert front(task_file(repo, "STATE.md"), "stage") == "review", task_file(repo, "STATE.md")


def test_commits_gate_blocks_a_fix_round_test_commit_that_is_not_red(repo):
    commits = PAIR + [("test(review): stricter", {"tests/test_app.py": "def test_x(): assert 1\n"})]
    branch(repo, commits)
    run(repo, "run", TASK)
    last = task_file(repo, "STATE.md").splitlines()[-1]
    assert re.search(r"\w+ test\(review\) edits `tests/test_app\.py` but is not red", last), last


def test_is_test_knows_test_and_fixture_paths():
    assert afk.is_test("tests/fixtures/a.json") and afk.is_test("src/app.spec.ts") and afk.is_test("test_x.py")
    assert not afk.is_test("app.py") and not afk.is_test("docs/testing.md")


# --- sessions: each Manual row of the test plan has a `Run AC<n>:` line in a task file (slice 2) ----------
PLAN = """
## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 the app adds | T1 | `tests/test_app.py` |
| AC2 the page shows the sum | T1 | Manual: open the page |
"""


def test_sessions_gate_blocks_a_manual_row_with_no_run_line(repo):
    branch(repo, PAIR, plan=PLAN)
    run(repo, "run", TASK)
    state = task_file(repo, "STATE.md")
    assert front(state, "status") == "blocked"
    last = state.splitlines()[-1]
    assert "gate sessions failed: AC2 needs a person to run" in last and "AC1" not in last, last
    assert "| fail |" in rows(repo)["sessions"] and "testing" not in rows(repo)


def test_sessions_gate_block_says_what_to_run_how_to_record_it_and_how_to_resume(repo):
    branch(repo, PAIR, plan=PLAN)
    out = run(repo, "run", TASK).stdout
    assert "| AC2 the page shows the sum | T1 | Manual: open the page |" in out, out
    assert 'Run AC<n>: <who>, <time>, "<what it showed>"' in out
    assert f"/kairyn:build {TASK}" in out and f"docs/tasks/{TASK}/BUILD.md" in out


GOOD_RUN = 'Run AC2: Ana Cruz, 2026-01-05T10:00:00Z, "the page shows 3"'


def test_sessions_gate_passes_with_a_run_line(repo):
    branch(repo, PAIR, plan=PLAN, build=f"# Build\n\n{GOOD_RUN}\n")
    assert run(repo, "run", TASK).returncode == 0
    assert front(task_file(repo, "STATE.md"), "stage") == "review"
    assert "| pass |" in rows(repo)["sessions"]


@pytest.mark.parametrize("line", [
    'Run AC2: 2026-01-05T10:00:00Z, "the page shows 3"',          # no who
    'Run AC2: Ana Cruz, yesterday, "the page shows 3"',           # no time
    "Run AC2: Ana Cruz, 2026-01-05T10:00:00Z, the page shows 3",  # not quoted
    'Run AC2: Ana Cruz, 2026-01-05T10:00:00Z, ""',                # empty
])
def test_has_run_line_needs_who_time_and_quoted_text(line):
    assert not afk.has_run_line(line, "AC2")
    assert afk.has_run_line(GOOD_RUN, "AC2") and not afk.has_run_line(GOOD_RUN, "AC1")


def test_sessions_gate_reads_any_task_file_but_design(repo):
    """A Run line in DESIGN.md does not count; one in another task file does."""
    branch(repo, PAIR, plan=PLAN + f"\n{GOOD_RUN}\n")
    run(repo, "run", TASK)
    assert "gate sessions failed" in task_file(repo, "STATE.md")


def test_manual_criteria_reads_the_test_plan():
    text = PLAN + "| AC3 x | T2 | manual check |\n| AC4 y | T2 | not Manual |\n"
    assert afk.manual_criteria(text) == {"AC2": "| AC2 the page shows the sum | T1 | Manual: open the page |",
                                         "AC3": "| AC3 x | T2 | manual check |"}


# --- evals: a command and paths from .kairyn/afk.yml (slice 3) ----------------------------------


def set_evals(repo, evals):
    """Commit a .kairyn/afk.yml on main with the testing gate and the `evals:` section text."""
    (repo / ".kairyn" / "afk.yml").write_text(f"gates:\n  testing: {base.GOOD_GATE}\n" + evals)
    git(repo, "commit", "-qam", "afk.yml")


def marker_command(repo):
    """A command that records KAIRYN_BASE in a file outside the repo, so a test sees that it ran."""
    marker = repo.parent / "evals_ran"
    return marker, f"printf %s \"$KAIRYN_BASE\" > {marker}"


def test_evals_gate_runs_the_command_on_a_guarded_change(repo):
    marker, command = marker_command(repo)
    set_evals(repo, f"evals:\n  command: {command}\n  paths:\n    - 'app.py'\n")
    branch(repo, PAIR)
    assert run(repo, "run", TASK).returncode == 0
    assert front(task_file(repo, "STATE.md"), "stage") == "review"
    assert "| pass | 0 |" in rows(repo)["evals"], rows(repo)["evals"]
    assert re.fullmatch(r"[0-9a-f]{7,40}", marker.read_text()), "the command gets KAIRYN_BASE"


def test_evals_gate_blocks_on_a_failing_command(repo):
    set_evals(repo, "evals:\n  command: exit 3\n  paths:\n    - 'app.py'\n")
    branch(repo, PAIR)
    run(repo, "run", TASK)
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert "gate evals failed: `exit 3` exited 3" in state.splitlines()[-1], state
    assert "| fail | 3 |" in rows(repo)["evals"] and "testing" not in rows(repo)

