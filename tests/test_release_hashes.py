"""plugin/release-hashes.json: the sha256 of every installed file in every release.

Upgrade uses it to recognize an unedited file in a repo that has no manifest (set up before 0.2.0).
Regenerate with: uv run python scripts/release_hashes.py --write
"""
import json
import subprocess
import sys

import pytest

from helpers import PLUGIN, ROOT
from kairyn_files import BLOCK, comparable_block, installed_files, plugin_version, sha256, shipped_bytes

sys.path.insert(0, str(ROOT / "scripts"))
from release_hashes import collect, repo_path  # noqa: E402

HASHES = PLUGIN / "release-hashes.json"


def load():
    return json.loads(HASHES.read_text())


def shipped_hash(entry) -> str:
    return sha256(shipped_bytes(entry))


# --- the shipped file ----------------------------------------------------------

def test_every_installed_file_of_the_current_version_is_recorded():
    """Fails when a plugin file changes and the hashes are not regenerated (or the version not bumped)."""
    recorded = load().get(plugin_version(PLUGIN), {})
    missing = [e.path for e in installed_files(PLUGIN) if shipped_hash(e) not in recorded.get(e.path, [])]
    assert missing == [], f"regenerate: uv run python scripts/release_hashes.py --write ({missing})"


def test_format_is_version_to_path_to_sorted_hashes():
    data = load()
    for version, files in data.items():
        assert version.count(".") == 2, version
        for path, hashes in files.items():
            assert hashes == sorted(set(hashes)) and all(len(h) == 64 for h in hashes), (version, path)


def _has_commit(commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", commit], cwd=ROOT, capture_output=True).returncode == 0


@pytest.mark.parametrize("commit", ["0563d9f", "a31ad4d"])
def test_stages_from_every_0_1_0_commit_are_recorded(commit):
    if not _has_commit(commit):
        pytest.skip(f"{commit} not in this clone (shallow checkout)")
    text = subprocess.run(["git", "show", f"{commit}:plugin/stages/REQUIREMENTS.md"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
    assert sha256(text.encode()) in load()["0.1.0"][".kairyn/stages/REQUIREMENTS.md"]


# --- the generator -------------------------------------------------------------

@pytest.mark.parametrize("source,expected", [
    ("plugin/stages/REQUIREMENTS.md", ".kairyn/stages/REQUIREMENTS.md"),
    ("plugin/templates/STATE.md", ".kairyn/templates/STATE.md"),
    ("plugin/harness/.harness/workflows/task-lifecycle.md", ".harness/workflows/task-lifecycle.md"),
    ("plugin/harness/CLAUDE.block.md", BLOCK),
    ("plugin/scripts/init.sh", None),
    ("plugin/commands/init.md", None),
])
def test_repo_path_maps_shipped_files_only(source, expected):
    assert repo_path(source) == expected


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def commit(repo, files: dict, version: str):
    for rel, text in {**files, "plugin/.claude-plugin/plugin.json": json.dumps({"version": version})}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", version)


def test_collect_keeps_every_commit_of_a_version_and_the_working_tree(tmp_path):
    git(tmp_path, "init", "-q")
    stage = "plugin/stages/REQUIREMENTS.md"
    commit(tmp_path, {stage: "one\n"}, "0.1.0")
    commit(tmp_path, {stage: "two\n"}, "0.1.0")          # changed without a bump
    commit(tmp_path, {stage: "three\n"}, "0.2.0")
    (tmp_path / stage).write_text("four\n")               # not committed yet
    data = collect(tmp_path)
    path = ".kairyn/stages/REQUIREMENTS.md"
    assert data["0.1.0"][path] == sorted(sha256(t.encode()) for t in ("one\n", "two\n"))
    assert data["0.2.0"][path] == sorted(sha256(t.encode()) for t in ("three\n", "four\n"))


def test_collect_hashes_only_the_marked_block_of_claude_block_md(tmp_path):
    git(tmp_path, "init", "-q")
    block = "<!-- kairyn:start -->\nx\n<!-- harness-docs:start -->\n| index |\n<!-- harness-docs:end -->\n<!-- kairyn:end -->\n"
    commit(tmp_path, {"plugin/harness/CLAUDE.block.md": "before\n" + block}, "0.1.0")
    assert collect(tmp_path)["0.1.0"][BLOCK] == [sha256(comparable_block(block).encode())]
