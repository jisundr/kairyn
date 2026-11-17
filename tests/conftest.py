import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
VERIFY = PLUGIN / "scripts" / "verify-init.sh"


def make_good_repo(dest: Path) -> Path:
    """Reference layout: what a correct /kairyn:init produces."""
    (dest / "docs" / "tasks").mkdir(parents=True)
    shutil.copytree(PLUGIN / "stages", dest / ".kairyn" / "stages")
    shutil.copytree(PLUGIN / "templates", dest / ".kairyn" / "templates")
    (dest / ".kairyn" / "learnings.md").write_text("# Learnings\n\nStages append here.\n")
    return dest


def run_verify(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(VERIFY), str(repo), str(PLUGIN)], capture_output=True, text=True
    )


def split_front_matter(text: str):
    """Return (front_matter_text, body) for a file that starts with ---."""
    assert text.startswith("---\n"), "file does not start with front matter"
    _, fm, body = text.split("---\n", 2)
    return fm, body


@pytest.fixture
def good_repo(tmp_path):
    return make_good_repo(tmp_path / "repo")
