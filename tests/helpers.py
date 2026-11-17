import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
VERIFY = PLUGIN / "scripts" / "verify-init.sh"


def make_good_repo(dest: Path) -> Path:
    """What a correct /kairyn:init produces: run the real init script on an empty repo."""
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["bash", str(PLUGIN / "scripts" / "init.sh"), str(dest)], check=True, capture_output=True)
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
