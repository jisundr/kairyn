"""scripts/check_version_bump.py: a change under plugin/ needs a newer plugin.json version (A2)."""
import json
import subprocess
import sys

import pytest

from helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from check_version_bump import problems  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def commit(repo, version, files):
    for rel, text in {**files, "plugin/.claude-plugin/plugin.json": json.dumps({"version": version})}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    commit(tmp_path, "0.1.0", {"plugin/stages/A.md": "a\n", "README.md": "r\n"})
    return tmp_path


def test_plugin_change_without_a_bump_fails(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "0.1.0", {"plugin/stages/A.md": "changed\n"})
    out = problems(repo, base)
    assert len(out) == 1 and "0.1.0" in out[0] and "plugin.json" in out[0]


def test_plugin_change_with_a_bump_passes(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "0.2.0", {"plugin/stages/A.md": "changed\n"})
    assert problems(repo, base) == []


def test_a_lower_version_fails(repo):
    base = commit(repo, "0.3.0", {})
    commit(repo, "0.2.0", {"plugin/stages/A.md": "changed\n"})
    assert problems(repo, base)


def test_changes_outside_plugin_need_no_bump(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "0.1.0", {"README.md": "changed\n"})
    assert problems(repo, base) == []


def test_cli_exits_one_on_a_missing_bump(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "0.1.0", {"plugin/stages/A.md": "changed\n"})
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_version_bump.py"), base],
                            cwd=repo, capture_output=True, text=True)
    assert result.returncode == 1 and result.stdout.startswith("FAIL:")
