"""scripts/evals_gate.py: this repo's `evals:` command for afk.py's evals review gate, run on tiny git repos.
It passes when each eval that depends on a changed plugin/ file has a pass at the current hash."""
import json
import os
import subprocess
import sys
from pathlib import Path

from helpers import ROOT
from selector import deps_hash

SCRIPT = ROOT / "scripts" / "evals_gate.py"
TASK = "2026-11-25-demo"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, message: str, files: dict) -> str:
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def eval_repo(tmp_path: Path) -> Path:
    """main with two evals and a stage file; kairyn/<task> changes the stage file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")
    commit(repo, "base", {"evals/promptfoo/init.yaml": "# depends: plugin/stages/*.md\n",
                          "evals/promptfoo/close.yaml": "# depends: plugin/scripts/close.py\n",
                          "plugin/stages/A.md": "a\n", "app.py": "x = 1\n", ".gitignore": "evals/results/\n"})
    git(repo, "checkout", "-q", "-b", f"kairyn/{TASK}")
    commit(repo, "feat(T1): stage", {"plugin/stages/A.md": "b\n"})
    return repo


def gate(repo: Path, base: str = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "KAIRYN_BASE"}
    if base:
        env["KAIRYN_BASE"] = base
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=repo, capture_output=True, text=True, env=env)


def record(root: Path, wt: Path = None) -> None:
    path = root / "evals" / "results" / "passed.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"init": deps_hash(wt or root, ["plugin/stages/*.md"])}))


def test_fails_without_a_pass_for_a_changed_dependency(tmp_path):
    repo = eval_repo(tmp_path)
    result = gate(repo)
    assert result.returncode == 1
    assert "`init`" in result.stdout and "close" not in result.stdout and "/run-evals init" in result.stdout


def test_passes_with_a_pass_at_the_current_hash(tmp_path):
    repo = eval_repo(tmp_path)
    record(repo)
    result = gate(repo)
    assert result.returncode == 0, result.stdout


def test_fails_when_a_fix_round_edits_stage_text_after_the_eval_pass(tmp_path):
    """flag-fix-round-stage-edits: a fix round can change stage text that no eval ran on."""
    repo = eval_repo(tmp_path)
    record(repo)
    commit(repo, "fix: shorter step", {"plugin/stages/A.md": "c\n"})
    result = gate(repo)
    assert result.returncode == 1 and "`init`" in result.stdout, result.stdout


def test_reads_the_record_of_the_main_checkout_from_a_worktree(tmp_path):
    repo = eval_repo(tmp_path)
    wt = tmp_path / "wt"
    git(repo, "checkout", "-q", "main")
    git(repo, "worktree", "add", "-q", str(wt), f"kairyn/{TASK}")
    record(repo, wt)
    result = gate(wt)
    assert result.returncode == 0, result.stdout


def test_passes_when_no_plugin_file_changed(tmp_path):
    repo = eval_repo(tmp_path)
    stage = git(repo, "rev-parse", "HEAD")
    commit(repo, "fix: app", {"app.py": "x = 2\n"})
    assert gate(repo, base=stage).returncode == 0


def test_takes_the_base_from_kairyn_base(tmp_path):
    """afk.py sets KAIRYN_BASE; with it at HEAD nothing changed, so the gate passes."""
    repo = eval_repo(tmp_path)
    assert gate(repo, base=git(repo, "rev-parse", "HEAD")).returncode == 0
    assert gate(repo, base=git(repo, "rev-parse", "main")).returncode == 1


def test_this_repo_afk_yml_sets_the_evals_gate():
    sys.path.insert(0, str(ROOT / "plugin" / "scripts"))
    import afk
    data = afk.parse_afk((ROOT / ".kairyn" / "afk.yml").read_text())
    assert data["evals"] == {"command": "python3 scripts/evals_gate.py", "paths": ["plugin/**"]}
    assert "evals" not in data["gates"]
    assert not (ROOT / "scripts" / "gates.py").exists() and not (ROOT / "tests" / "test_gates.py").exists()
