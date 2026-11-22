"""version_check.py: one line naming /kairyn:upgrade when the plugin is newer than the repo's kairyn files."""
import json
import shutil
import subprocess
import time

import pytest

from helpers import PLUGIN, ROOT, make_good_repo, run_verify
from version_check import message, newer

CHECK = PLUGIN / "scripts" / "version_check.py"
FIXTURE = ROOT / "tests" / "fixtures" / "consumer-v0.1.0"


def run(repo, *extra):
    return subprocess.run(["python3", str(CHECK), "--root", str(repo), *extra], capture_output=True, text=True)


def set_manifest_version(repo, version):
    path = repo / ".kairyn" / "manifest.json"
    path.write_text(json.dumps({**json.loads(path.read_text()), "version": version}))


@pytest.mark.parametrize("a,b,expected", [
    ("0.2.0", "0.1.0", True), ("0.10.0", "0.9.0", True), ("1.0.0", "1.0.0", False), ("0.1.0", "0.2.0", False),
])
def test_newer_compares_numerically(a, b, expected):
    assert newer(a, b) is expected


def test_silent_without_kairyn(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""


def test_silent_when_versions_match(tmp_path):
    result = run(make_good_repo(tmp_path / "repo"))
    assert result.returncode == 0 and result.stdout == ""


def test_one_line_naming_upgrade_when_the_plugin_is_newer(tmp_path):
    repo = make_good_repo(tmp_path / "repo")
    set_manifest_version(repo, "0.0.1")
    result = run(repo)
    assert result.returncode == 0
    assert len(result.stdout.splitlines()) == 1 and "/kairyn:upgrade" in result.stdout and "0.0.1" in result.stdout


def test_a_repo_without_a_manifest_is_older(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    assert "/kairyn:upgrade" in run(repo).stdout


def test_writes_no_file_and_runs_in_under_a_second(tmp_path):
    repo = make_good_repo(tmp_path / "repo")
    set_manifest_version(repo, "0.0.1")
    before = sorted(p for p in repo.rglob("*"))
    start = time.perf_counter()
    run(repo)
    assert time.perf_counter() - start < 1.0
    assert sorted(p for p in repo.rglob("*")) == before


def test_message_is_none_when_up_to_date(tmp_path):
    assert message(make_good_repo(tmp_path / "repo"), PLUGIN) is None


# --- where it runs ------------------------------------------------------------

def test_verify_init_reports_an_older_version_without_failing(tmp_path):
    repo = make_good_repo(tmp_path / "repo")
    set_manifest_version(repo, "0.0.1")
    result = run_verify(repo)
    assert result.returncode == 0 and "/kairyn:upgrade" in result.stdout


def test_verify_init_says_nothing_about_versions_when_they_match(tmp_path):
    assert "/kairyn:upgrade" not in run_verify(make_good_repo(tmp_path / "repo")).stdout


def test_check_command_runs_the_version_check():
    assert "scripts/version_check.py" in (PLUGIN / "commands" / "check.md").read_text()


def test_plugin_ships_a_session_start_hook_that_runs_the_check():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]["SessionStart"]
    commands = [h["command"] for group in hooks for h in group["hooks"]]
    assert any("scripts/version_check.py" in c and "CLAUDE_PROJECT_DIR" in c for c in commands)
