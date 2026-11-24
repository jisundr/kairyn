"""Shipped scripts run on Python 3.9, the python3 macOS ships at /usr/bin/python3."""
import subprocess
from pathlib import Path

import pytest

from helpers import PLUGIN, ROOT, make_good_repo

SCRIPTS = PLUGIN / "scripts"


def find_python39() -> str | None:
    try:
        found = subprocess.run(
            ["uv", "python", "find", "--no-project", "3.9"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return None
    path = found.stdout.strip()
    return path if found.returncode == 0 and path else None


PY39 = find_python39()
pytestmark = pytest.mark.skipif(PY39 is None, reason="no Python 3.9 interpreter installed")


def run39(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY39, *args], capture_output=True, text=True)


def test_interpreter_is_3_9():
    assert run39("-c", "import sys; print(sys.version_info[:2])").stdout.strip() == "(3, 9)"


@pytest.mark.parametrize("script", ["budgets.py", "harness_docs.py"])
def test_checkers_run_on_a_fresh_repo(tmp_path, script):
    repo = make_good_repo(tmp_path / "repo")
    result = run39(str(SCRIPTS / script), "--root", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", ["budgets.py", "harness_docs.py"])
def test_checkers_run_on_this_repo(script):
    result = run39(str(SCRIPTS / script), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr


def test_budgets_html_runs(tmp_path):
    out = tmp_path / "budgets.html"
    result = run39(str(SCRIPTS / "budgets_html.py"), "--root", str(ROOT), "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    assert out.exists()


def test_every_script_imports():
    for script in sorted(SCRIPTS.glob("*.py")):
        code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import {script.stem}"
        result = run39("-c", code)
        assert result.returncode == 0, f"{script.name}: {result.stderr}"


def test_close_script_runs(tmp_path):
    repo = make_good_repo(tmp_path / "repo")
    assert run39(str(SCRIPTS / "close.py"), "adr-path", "first", "--root", str(repo)).stdout.strip() == "docs/adr/0001-first.md"
    assert run39(str(SCRIPTS / "close.py"), "check", "none", "--root", str(repo)).stdout.startswith("FAIL:")


def test_retro_script_runs(tmp_path):
    repo = make_good_repo(tmp_path / "repo")
    assert run39(str(SCRIPTS / "retro.py"), "size", "--root", str(repo)).stdout.startswith("learnings.md ")
    out = run39(str(SCRIPTS / "retro.py"), "fits", "CLAUDE.md", "--add", "rule", "--root", str(repo)).stdout.strip()
    assert out == "FITS"
