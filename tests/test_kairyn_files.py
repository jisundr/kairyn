"""kairyn_files.py: the table of installed files, the manifest and the .base/ copies."""
import hashlib
import json
import subprocess

import pytest

from helpers import PLUGIN, make_good_repo
from kairyn_files import (
    BLOCK, block_text, comparable_block, installed_files, manifest_problems, owner_of, plugin_version, read_manifest,
)

INIT = PLUGIN / "scripts" / "init.sh"
KF = PLUGIN / "scripts" / "kairyn_files.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# --- the file table ------------------------------------------------------------

@pytest.mark.parametrize("path,owner", [
    (".kairyn/stages/REQUIREMENTS.md", "repo"),
    (".kairyn/stages/MODEL-ROUTING.md", "repo"),
    (".kairyn/templates/STATE.md", "plugin"),
    (".harness/README.md", "repo"),
    (".harness/budgets.yml", "repo"),
    (".harness/workflows/running-stages.md", "plugin"),
    (".harness/workflows/task-lifecycle.md", "plugin"),
    (".harness/workflows/keeping-docs-lean.md", "plugin"),
    (BLOCK, "plugin"),
])
def test_owner_follows_the_requirements_split(path, owner):
    assert owner_of(path) == owner


def test_never_touched_files_have_no_owner():
    for path in (".kairyn/learnings.md", "docs/tasks/2026-01-01-x/STATE.md", ".harness/workflows/mine.md", "CLAUDE.md"):
        assert owner_of(path) is None, path


def test_every_shipped_file_has_an_owner():
    assert [e.path for e in installed_files(PLUGIN) if e.owner not in ("plugin", "repo")] == []


def test_installed_files_map_every_shipped_file_to_its_repo_path():
    table = {e.path: e.source for e in installed_files(PLUGIN)}
    assert table[".kairyn/stages/REQUIREMENTS.md"] == PLUGIN / "stages" / "REQUIREMENTS.md"
    assert table[".harness/workflows/task-lifecycle.md"] == PLUGIN / "harness" / ".harness" / "workflows" / "task-lifecycle.md"
    assert table[BLOCK] == PLUGIN / "harness" / "CLAUDE.block.md"
    shipped = len(list((PLUGIN / "stages").iterdir())) + len(list((PLUGIN / "templates").iterdir()))
    shipped += sum(1 for p in (PLUGIN / "harness" / ".harness").rglob("*") if p.is_file()) + 1
    assert len(table) == shipped


def test_block_text_is_the_marked_region_inclusive():
    text = "mine\n<!-- kairyn:start -->\nbody\n<!-- kairyn:end -->\nafter\n"
    assert block_text(text) == "<!-- kairyn:start -->\nbody\n<!-- kairyn:end -->\n"
    assert block_text("no block\n") is None


def test_plugin_version_reads_plugin_json():
    assert plugin_version(PLUGIN) == json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]


# --- init writes the manifest and .base/ ---------------------------------------

def test_init_writes_a_manifest_with_version_hash_and_owner(good_repo):
    manifest = read_manifest(good_repo)
    assert manifest["version"] == plugin_version(PLUGIN)
    stage = manifest["files"][".kairyn/stages/REQUIREMENTS.md"]
    assert stage == {"sha256": sha((good_repo / ".kairyn/stages/REQUIREMENTS.md").read_bytes()), "owner": "repo"}
    assert manifest["files"][".kairyn/templates/STATE.md"]["owner"] == "plugin"
    assert ".kairyn/learnings.md" not in manifest["files"]


def test_init_records_every_installed_file_and_the_claude_block(good_repo):
    assert set(read_manifest(good_repo)["files"]) == {e.path for e in installed_files(PLUGIN)}
    block = block_text((good_repo / "CLAUDE.md").read_text())
    assert read_manifest(good_repo)["files"][BLOCK]["sha256"] == sha(comparable_block(block).encode())


def test_comparable_block_empties_the_doc_index():
    block = "<!-- kairyn:start -->\na\n<!-- harness-docs:start -->\n| row |\n<!-- harness-docs:end -->\n<!-- kairyn:end -->\n"
    assert comparable_block(block) == "<!-- kairyn:start -->\na\n<!-- harness-docs:start -->\n<!-- harness-docs:end -->\n<!-- kairyn:end -->\n"


def test_base_holds_an_exact_copy_of_each_recorded_file(good_repo):
    for path, entry in read_manifest(good_repo)["files"].items():
        base = good_repo / ".kairyn" / ".base" / path
        assert base.is_file(), path
        assert sha(base.read_bytes()) == entry["sha256"], path


def test_init_does_not_record_files_the_user_already_had(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".harness").mkdir(parents=True)
    (repo / ".harness" / "README.md").write_text("my own readme\n")
    (repo / "CLAUDE.md").write_text("mine\n<!-- kairyn:start -->\nold\n<!-- kairyn:end -->\n")
    make_good_repo(repo)
    files = read_manifest(repo)["files"]
    assert ".harness/README.md" not in files and BLOCK not in files
    assert not (repo / ".kairyn" / ".base" / ".harness" / "README.md").exists()


def test_a_second_init_changes_nothing(good_repo):
    before = tree(good_repo)
    subprocess.run(["bash", str(INIT), str(good_repo)], check=True, capture_output=True)
    assert tree(good_repo) == before


# --- manifest_problems: what verify-init.sh reports ----------------------------

def test_a_fresh_install_has_no_manifest_problems(good_repo):
    assert manifest_problems(good_repo) == []


def test_missing_manifest_names_upgrade(good_repo):
    (good_repo / ".kairyn" / "manifest.json").unlink()
    problems = manifest_problems(good_repo)
    assert len(problems) == 1 and "manifest.json missing" in problems[0] and "/kairyn:upgrade" in problems[0]


def test_invalid_manifest_is_a_problem(good_repo):
    (good_repo / ".kairyn" / "manifest.json").write_text("{not json")
    assert any("manifest.json" in p for p in manifest_problems(good_repo))


def test_base_copy_that_does_not_match_the_manifest_is_a_problem(good_repo):
    base = good_repo / ".kairyn" / ".base" / ".kairyn" / "stages" / "REQUIREMENTS.md"
    base.write_text("changed\n")
    assert any(".base/.kairyn/stages/REQUIREMENTS.md" in p for p in manifest_problems(good_repo))


def test_an_edited_repo_file_is_not_a_manifest_problem(good_repo):
    (good_repo / ".kairyn" / "stages" / "REQUIREMENTS.md").write_text("user edit\n")
    assert manifest_problems(good_repo) == []


def test_cli_check_exits_one_on_problems(good_repo):
    (good_repo / ".kairyn" / "manifest.json").unlink()
    result = subprocess.run(["python3", str(KF), "check", str(good_repo)], capture_output=True, text=True)
    assert result.returncode == 1 and result.stdout.startswith("FAIL:")
