"""parallel-learnings: two task branches that each append a learning merge with no conflict."""
import subprocess

from helpers import ROOT


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def test_learnings_md_merges_by_union():
    assert git(ROOT, "check-attr", "merge", ".kairyn/learnings.md").stdout.strip().endswith(": merge: union")


def test_two_branches_that_each_add_a_learning_merge_cleanly(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")
    (repo / ".gitattributes").write_text((ROOT / ".gitattributes").read_text())
    learnings = repo / ".kairyn" / "learnings.md"
    learnings.parent.mkdir()
    learnings.write_text("# Learnings\n\nStages append here.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    for branch, line in (("a", "- 2026-11-25 [build] one\n"), ("b", "- 2026-11-25 [design] two\n")):
        git(repo, "checkout", "-q", "-b", branch, "main")
        learnings.write_text(learnings.read_text() + line)
        git(repo, "commit", "-qam", branch)
    git(repo, "checkout", "-q", "a")
    assert git(repo, "merge", "-q", "--no-edit", "b").returncode == 0
    text = learnings.read_text()
    assert "one" in text and "two" in text and "<<<<<<<" not in text
