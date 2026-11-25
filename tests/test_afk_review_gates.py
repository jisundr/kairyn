"""afk.py review gates `design` and `commits` (backlog idea ship-review-gates, first slice).

Each test builds kairyn/<task> by hand with STATE.md at `stage: gates`, then runs afk.py against
tests/stubs/claude. The gates stage runs the review gates first, then the afk.yml `gates:`.
"""
import importlib
import re
import sys

import test_afk as base
from helpers import PLUGIN
from test_afk import TASK, front, git, run, task_file

sys.path.insert(0, str(PLUGIN / "scripts"))
afk = importlib.import_module("afk")
repo = base.repo   # the repo fixture of test_afk.py

NAMED = "- T1: Files: `app.py`, `tests/test_app.py`, `tests/fixtures/` . Done: `python3 check_t1.py` exits 0.\n"


def branch(repo, commits, design=NAMED):
    """kairyn/<task> with DESIGN.md naming `design`, the commits (message, {path: text}) and STATE.md at gates."""
    folder = repo / "docs" / "tasks" / TASK
    git(repo, "checkout", "-q", "-b", f"kairyn/{TASK}")
    text = (folder / "DESIGN.md").read_text()
    (folder / "DESIGN.md").write_text(re.sub(r"## Tasks\n(- T.*\n)+", "## Tasks\n" + design, text))
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
    (folder / "BUILD.md").write_text("# Build\n")
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
    assert names[:3] == ["design", "commits", "testing"], names
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


def test_commits_gate_allows_a_red_test_commit_in_the_fix_round(repo):
    """A fix-round test edit is fine in a test(...) commit where the testing gate fails."""
    commits = PAIR + [("test(review): stricter", {"tests/test_app.py": "def test_x(): assert 0\n",
                                                  "check_t1.py": "import sys; sys.exit(1)\n"}),
                      ("fix: pass it", {"check_t1.py": "pass\n"})]
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
