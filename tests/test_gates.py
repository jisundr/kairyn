"""scripts/gates.py: the review gates of this repo's .kairyn/afk.yml, run on tiny git repos."""
import json
import subprocess
import sys
from pathlib import Path

from helpers import ROOT
from selector import deps_hash

GATES = ROOT / "scripts" / "gates.py"
TASK = "2026-11-25-demo"
DESIGN = f"""# Design

## Tasks
- T1: Files: `app.py`, `tests/test_app.py`, `tests/fixtures/` . Done: `sh check.sh` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 Adds | T1 | `test_adds` |
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, message: str, files: dict) -> str:
    for name, text in files.items():
        path = repo / name
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "--short", "HEAD")


def make_repo(tmp_path: Path, design: str = DESIGN) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")
    commit(repo, "base", {"app.py": "x = 1\n", "check.sh": "grep -q good app.py\n"})
    git(repo, "checkout", "-q", "-b", f"kairyn/{TASK}")
    commit(repo, f"kairyn({TASK}): design", {f"docs/tasks/{TASK}/DESIGN.md": design})
    return repo


def gate(repo: Path, check: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATES), check, *args], cwd=repo, capture_output=True, text=True)


def test_every_gate_passes_with_no_code_commits(tmp_path):
    repo = make_repo(tmp_path, DESIGN + "| AC2 Real | T1 | Manual: one real session |\n")
    for check in ("design", "commits", "evals", "sessions"):
        result = gate(repo, check)
        assert result.returncode == 0, (check, result.stdout)


def test_gates_skip_outside_a_kairyn_branch(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")
    assert gate(repo, "design").returncode == 0


# design: changed files and hook events must be in DESIGN.md
def test_design_passes_when_each_changed_file_is_named(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n", "tests/fixtures/a.json": "{}\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    result = gate(repo, "design")
    assert result.returncode == 0, result.stdout


def test_design_fails_on_a_file_outside_design(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "feat(T1): adds", {"app.py": "good\n", "other.py": "y\n"})
    result = gate(repo, "design")
    assert result.returncode == 1
    assert "`other.py`" in result.stdout and "app.py" not in result.stdout


def test_design_allow_skips_a_file(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "feat(T1): adds", {"app.py": "good\n", ".kairyn/learnings.md": "- x\n"})
    assert gate(repo, "design", "--allow", ".kairyn/*.md").returncode == 0


def test_design_fails_on_a_hook_event_outside_design(tmp_path):
    hooks = {"hooks": {"PostToolUse": []}}
    repo = make_repo(tmp_path, DESIGN.replace("`app.py`", "`app.py`, `hooks.json` (PostToolUse)"))
    git(repo, "checkout", "-q", "main")
    commit(repo, "hooks", {"hooks.json": json.dumps(hooks)})
    git(repo, "checkout", "-q", f"kairyn/{TASK}")
    git(repo, "rebase", "-q", "main")
    hooks["hooks"]["PostToolUseFailure"] = []
    hooks["hooks"]["Stop"] = []
    commit(repo, "feat(T1): hooks", {"hooks.json": json.dumps(hooks)})
    result = gate(repo, "design")
    assert result.returncode == 1
    assert "PostToolUseFailure" in result.stdout and "`Stop`" in result.stdout
    assert "`PostToolUse`" not in result.stdout


# commits: no test change in a feat commit; a fix-round test edit needs a new red run
def test_commits_fail_when_a_feat_commit_changes_a_test_or_fixture(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    sha = commit(repo, "feat(T1): adds", {"app.py": "good\n", "tests/fixtures/a.json": "{}\n"})
    result = gate(repo, "commits")
    assert result.returncode == 1
    assert sha in result.stdout and "tests/fixtures/a.json" in result.stdout


def test_commits_pass_on_a_clean_red_green_pair(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    result = gate(repo, "commits", "--run", "sh check.sh")
    assert result.returncode == 0, result.stdout


def test_commits_fail_when_a_fix_commit_edits_a_test(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    sha = commit(repo, "fix: finding", {"tests/test_app.py": "weaker\n"})
    result = gate(repo, "commits", "--run", "sh check.sh")
    assert result.returncode == 1
    assert sha in result.stdout and "tests/test_app.py" in result.stdout


def test_commits_allow_a_fix_commit_that_only_adds_test_lines(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    commit(repo, "fix: finding", {"tests/test_app.py": "t\nmore\n"})
    assert gate(repo, "commits", "--run", "sh check.sh").returncode == 0


def test_commits_fail_when_a_fix_round_test_edit_is_not_red(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    sha = commit(repo, "test(review): reword", {"tests/test_app.py": "t2\n"})
    result = gate(repo, "commits", "--run", "sh check.sh")
    assert result.returncode == 1
    assert sha in result.stdout and "not red" in result.stdout


def test_commits_pass_when_a_fix_round_test_edit_is_red(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "test(T1): adds", {"tests/test_app.py": "t\n"})
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    commit(repo, "test(review): stricter", {"tests/test_app.py": "t2\n", "check.sh": "grep -q better app.py\n"})
    commit(repo, "fix(review): stricter", {"app.py": "good better\n"})
    result = gate(repo, "commits", "--run", "sh check.sh")
    assert result.returncode == 0, result.stdout


# evals: a plugin/ change needs a recorded eval pass at the current hash
def eval_repo(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")
    commit(repo, "evals", {"evals/promptfoo/init.yaml": "# depends: plugin/stages/*.md\n",
                           "evals/promptfoo/close.yaml": "# depends: plugin/scripts/close.py\n",
                           "plugin/stages/A.md": "a\n", ".gitignore": "evals/results/\n"})
    git(repo, "checkout", "-q", f"kairyn/{TASK}")
    git(repo, "rebase", "-q", "main")
    commit(repo, "feat(T1): stage", {"plugin/stages/A.md": "b\n"})
    return repo


def test_evals_fail_without_a_pass_for_a_changed_dependency(tmp_path):
    repo = eval_repo(tmp_path)
    result = gate(repo, "evals")
    assert result.returncode == 1
    assert "`init`" in result.stdout and "close" not in result.stdout


def test_evals_pass_with_a_pass_at_the_current_hash(tmp_path):
    repo = eval_repo(tmp_path)
    record = repo / "evals" / "results" / "passed.json"
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({"init": deps_hash(repo, ["plugin/stages/*.md"])}))
    result = gate(repo, "evals")
    assert result.returncode == 0, result.stdout


def test_evals_fail_when_a_fix_round_edits_stage_text_after_the_eval_pass(tmp_path):
    """flag-fix-round-stage-edits: a fix round can change stage text that no eval ran on."""
    repo = eval_repo(tmp_path)
    record = repo / "evals" / "results" / "passed.json"
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({"init": deps_hash(repo, ["plugin/stages/*.md"])}))
    commit(repo, "fix: shorter step", {"plugin/stages/A.md": "c\n"})
    result = gate(repo, "evals")
    assert result.returncode == 1 and "`init`" in result.stdout, result.stdout


def test_evals_read_the_record_of_the_main_checkout_from_a_worktree(tmp_path):
    repo = eval_repo(tmp_path)
    wt = tmp_path / "wt"
    git(repo, "checkout", "-q", "main")
    git(repo, "worktree", "add", "-q", str(wt), f"kairyn/{TASK}")
    record = repo / "evals" / "results" / "passed.json"
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({"init": deps_hash(wt, ["plugin/stages/*.md"])}))
    result = gate(wt, "evals")
    assert result.returncode == 0, result.stdout


def test_evals_pass_when_no_plugin_file_changed(tmp_path):
    repo = make_repo(tmp_path)
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    assert gate(repo, "evals").returncode == 0


# sessions: a Manual test plan row needs a `Run AC<n>:` line in the task folder
def test_sessions_fail_on_a_manual_row_with_no_run(tmp_path):
    repo = make_repo(tmp_path, DESIGN + "| AC2 Real session | T1 | Manual: one real session after merge |\n")
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    result = gate(repo, "sessions")
    assert result.returncode == 1
    assert "AC2" in result.stdout and "AC1" not in result.stdout


def test_sessions_pass_when_the_run_is_recorded(tmp_path):
    repo = make_repo(tmp_path, DESIGN + "| AC2 Real session | T1 | Manual: one real session |\n")
    commit(repo, "feat(T1): adds", {"app.py": "good\n"})
    commit(repo, f"kairyn({TASK}): run", {f"docs/tasks/{TASK}/BUILD.md":
                                           '# Build\n\nRun AC2: T, 2026-11-25T05:00:00Z, "0 status asks"\n'})
    result = gate(repo, "sessions")
    assert result.returncode == 0, result.stdout
