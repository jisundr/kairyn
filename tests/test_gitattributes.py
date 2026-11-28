"""learnings.md merges with scripts/merge_learnings.py: parallel appends keep both lines, and a
branch from before a retro does not restore the lines the retro removed (union did)."""
import subprocess
import sys

import pytest

from helpers import ROOT

DRIVER = ROOT / "scripts" / "merge_learnings.py"
HEAD = "# Learnings\n\nStages append here.\n"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def make_repo(tmp_path, *, driver=True, body=""):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")
    (repo / ".gitattributes").write_text((ROOT / ".gitattributes").read_text())
    (repo / "scripts").mkdir()
    (repo / "scripts" / "merge_learnings.py").write_text(DRIVER.read_text())
    if driver:
        git(repo, "config", "merge.learnings.driver", f"{sys.executable} scripts/merge_learnings.py %O %A %B")
    learnings = repo / ".kairyn" / "learnings.md"
    learnings.parent.mkdir()
    learnings.write_text(HEAD + body)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    return repo, learnings


def commit(repo, learnings, text, message):
    learnings.write_text(text)
    git(repo, "commit", "-qam", message)


OLD = "- 2026-11-20 [build] old one\n- 2026-11-20 [build] old two\n- 2026-11-20 [build] old three\n"


def retro_case(tmp_path, *, driver):
    """main runs a retro that removes OLD; branch t, made before it, appends one line and rebases."""
    repo, learnings = make_repo(tmp_path, driver=driver, body=OLD)
    git(repo, "checkout", "-q", "-b", "t")
    commit(repo, learnings, HEAD + OLD + "- 2026-11-21 [build] new\n", "append")
    git(repo, "checkout", "-q", "main")
    commit(repo, learnings, HEAD + "- 2026-11-21 [close] kept\n", "retro")
    git(repo, "checkout", "-q", "t")
    return repo, learnings, git(repo, "rebase", "main")


def test_learnings_md_merges_by_the_driver():
    out = git(ROOT, "check-attr", "merge", ".kairyn/learnings.md").stdout.strip()
    assert out.endswith(": merge: learnings"), out


def test_rebase_after_a_retro_keeps_its_removals(tmp_path):
    repo, learnings, rebase = retro_case(tmp_path, driver=True)
    assert rebase.returncode == 0, rebase.stdout + rebase.stderr
    assert learnings.read_text() == HEAD + "- 2026-11-21 [close] kept\n- 2026-11-21 [build] new\n"


def test_two_branches_that_each_add_a_learning_merge_cleanly(tmp_path):
    repo, learnings = make_repo(tmp_path)
    for branch, line in (("a", "- 2026-11-25 [build] one\n"), ("b", "- 2026-11-25 [design] two\n")):
        git(repo, "checkout", "-q", "-b", branch, "main")
        commit(repo, learnings, HEAD + line, branch)
    git(repo, "checkout", "-q", "a")
    assert git(repo, "merge", "-q", "--no-edit", "b").returncode == 0
    text = learnings.read_text()
    assert "one" in text and "two" in text and "<<<<<<<" not in text


def test_driver_keeps_current_order_then_new_lines(tmp_path):
    base, ours, theirs = (tmp_path / n for n in ("o", "a", "b"))
    base.write_text("h\nx\ny\n")
    ours.write_text("h\ny\nx\nours\n")
    theirs.write_text("h\nx\ntheirs1\ntheirs2\n")
    result = subprocess.run([sys.executable, str(DRIVER), str(base), str(ours), str(theirs)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert ours.read_text() == "h\nx\nours\ntheirs1\ntheirs2\n"


def test_install_is_idempotent(tmp_path):
    repo, _ = make_repo(tmp_path, driver=False)
    for _ in range(2):
        result = subprocess.run([sys.executable, "scripts/merge_learnings.py", "--install"],
                                cwd=repo, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert "merge.learnings.driver" in result.stdout
    entries = git(repo, "config", "--get-all", "merge.learnings.driver").stdout.splitlines()
    assert entries == ["python3 scripts/merge_learnings.py %O %A %B"]
    assert git(repo, "config", "--get", "merge.learnings.name").returncode == 0


def test_without_driver_config_a_retro_case_conflicts(tmp_path):
    repo, learnings, rebase = retro_case(tmp_path, driver=False)
    assert rebase.returncode != 0
    assert "<<<<<<<" in learnings.read_text()


def test_driver_runs_on_python39(tmp_path):
    from test_python39 import PY39
    if PY39 is None:
        pytest.skip("no Python 3.9 interpreter installed")
    base, ours, theirs = (tmp_path / n for n in ("o", "a", "b"))
    base.write_text("h\nold\n")
    ours.write_text("h\n")
    theirs.write_text("h\nold\nnew\n")
    result = subprocess.run([PY39, str(DRIVER), str(base), str(ours), str(theirs)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert ours.read_text() == "h\nnew\n"
