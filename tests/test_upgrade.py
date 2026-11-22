"""upgrade.py: bring an installed repo up to the plugin's version without losing the user's edits."""
import json
import shutil
import subprocess

import pytest

from helpers import PLUGIN, ROOT, make_good_repo
from kairyn_files import BLOCK, manifest_problems, read_manifest, sha256

UPGRADE = PLUGIN / "scripts" / "upgrade.py"
FIXTURE = ROOT / "tests" / "fixtures" / "consumer-v0.1.0"
STAGE = ".kairyn/stages/REQUIREMENTS.md"
TEMPLATE = ".kairyn/templates/STATE.md"


def new_plugin(tmp_path, version="9.9.9", edit=None, add=None):
    """A copy of the plugin at a new version, with some shipped files changed or added."""
    plugin = tmp_path / "plugin-new"
    shutil.copytree(PLUGIN, plugin)
    meta = plugin / ".claude-plugin" / "plugin.json"
    meta.write_text(json.dumps({**json.loads(meta.read_text()), "version": version}))
    for rel, fn in (edit or {}).items():
        (plugin / rel).write_text(fn((plugin / rel).read_text()))
    for rel, text in (add or {}).items():
        (plugin / rel).write_text(text)
    return plugin


def upgrade(repo, plugin):
    result = subprocess.run(["python3", str(UPGRADE), "--root", str(repo), "--plugin", str(plugin)],
                            capture_output=True, text=True)
    lines = dict(reversed(line.split(" ", 1)) for line in result.stdout.splitlines() if " " in line)
    return result, lines


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def lines_of(text):
    return text.splitlines(keepends=True)


@pytest.fixture
def repo(tmp_path):
    return make_good_repo(tmp_path / "repo")


# --- plugin-owned files ----------------------------------------------------------

def test_plugin_owned_file_is_replaced(tmp_path, repo):
    plugin = new_plugin(tmp_path, edit={"templates/STATE.md": lambda t: t + "\nnew line\n"})
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 0, result.stdout
    assert lines[TEMPLATE] == "REPLACED"
    assert (repo / TEMPLATE).read_text().endswith("new line\n")


def test_edited_plugin_owned_file_is_replaced_and_the_edit_saved_aside(tmp_path, repo):
    (repo / TEMPLATE).write_text("my template\n")
    plugin = new_plugin(tmp_path, edit={"templates/STATE.md": lambda t: t + "\nnew line\n"})
    _, lines = upgrade(repo, plugin)
    assert lines[TEMPLATE] == "REPLACED"
    assert (repo / (TEMPLATE + ".kairyn-old")).read_text() == "my template\n"


def test_only_the_kairyn_block_of_claude_md_is_replaced(tmp_path, repo):
    claude = repo / "CLAUDE.md"
    claude.write_text("# Mine\n\nkeep this\n\n" + claude.read_text() + "\nand this\n")
    plugin = new_plugin(tmp_path, edit={"harness/CLAUDE.block.md": lambda t: t.replace("## kairyn", "## kairyn (new)")})
    _, lines = upgrade(repo, plugin)
    text = claude.read_text()
    assert lines[BLOCK] == "REPLACED"
    assert text.startswith("# Mine\n\nkeep this\n") and text.endswith("\nand this\n") and "## kairyn (new)" in text


def test_a_refreshed_doc_index_does_not_count_as_an_edit(tmp_path, repo):
    claude = repo / "CLAUDE.md"
    claude.write_text(claude.read_text().replace("<!-- harness-docs:end -->", "| extra | row |\n<!-- harness-docs:end -->"))
    _, lines = upgrade(repo, new_plugin(tmp_path))
    assert lines[BLOCK] == "KEPT" and "| extra | row |" in claude.read_text()


# --- repo-owned files: three-way merge -------------------------------------------

def test_merge_unchanged_locally_takes_the_new_version(tmp_path, repo):
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t + "\nplugin line\n"})
    _, lines = upgrade(repo, plugin)
    assert lines[STAGE] == "REPLACED" and (repo / STAGE).read_text().endswith("plugin line\n")


def test_merge_clean_keeps_the_users_edit_and_the_plugins_change(tmp_path, repo):
    stage = repo / STAGE
    stage.write_text(stage.read_text().replace("# Stage: requirements", "# Stage: requirements (ours)"))
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t + "\nplugin line\n"})
    result, lines = upgrade(repo, plugin)
    text = stage.read_text()
    assert result.returncode == 0 and lines[STAGE] == "MERGED"
    assert "(ours)" in text and text.endswith("plugin line\n")


def test_merge_conflict_keeps_the_local_file_and_writes_kairyn_new(tmp_path, repo):
    stage = repo / STAGE
    stage.write_text(stage.read_text().replace("# Stage: requirements", "# Stage: ours"))
    local = stage.read_text()
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t.replace("# Stage: requirements", "# Stage: theirs")})
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 1 and lines[STAGE] == "CONFLICT"
    assert stage.read_text() == local and "<<<<<<<" not in local
    new = (repo / (STAGE + ".kairyn-new")).read_text()
    assert "<<<<<<<" in new and "# Stage: ours" in new and "# Stage: theirs" in new
    assert read_manifest(repo)["version"] != "9.9.9"   # not up to date while a conflict is open


def test_deleting_kairyn_new_resolves_the_conflict(tmp_path, repo):
    stage = repo / STAGE
    stage.write_text(stage.read_text().replace("# Stage: requirements", "# Stage: ours"))
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t.replace("# Stage: requirements", "# Stage: theirs")})
    upgrade(repo, plugin)
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 1 and lines[STAGE] == "CONFLICT"     # still open
    (repo / (STAGE + ".kairyn-new")).unlink()                         # the user merged what they wanted
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 0 and lines[STAGE] == "KEPT"
    assert "# Stage: ours" in stage.read_text()
    assert read_manifest(repo)["version"] == "9.9.9" and manifest_problems(repo) == []


# --- scope, report, idempotence ------------------------------------------------

def test_new_files_are_added_and_unowned_files_never_touched(tmp_path, repo):
    (repo / ".kairyn" / "learnings.md").write_text("# Learnings\n\nmine\n")
    task = repo / "docs" / "tasks" / "2026-01-01-x"
    task.mkdir()
    (task / "STATE.md").write_text("task\n")
    (repo / ".harness" / "workflows" / "mine.md").write_text("my doc\n")
    untouched = {k: v for k, v in tree(repo).items() if k.startswith(("docs/", ".kairyn/learnings", ".harness/workflows/mine"))}
    plugin = new_plugin(tmp_path, add={"stages/NEW-STAGE.md": "---\nname: new-stage\n---\n"})
    _, lines = upgrade(repo, plugin)
    assert lines[".kairyn/stages/NEW-STAGE.md"] == "ADDED"
    assert (repo / ".kairyn/stages/NEW-STAGE.md").read_text() == "---\nname: new-stage\n---\n"
    after = tree(repo)
    assert all(after[k] == v for k, v in untouched.items())


def test_a_harness_file_the_user_had_before_init_stays_theirs(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".harness").mkdir(parents=True)
    (repo / ".harness" / "README.md").write_text("my own readme\n")
    make_good_repo(repo)
    plugin = new_plugin(tmp_path, edit={"harness/.harness/README.md": lambda t: t + "\nnew\n"})
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 0
    assert (repo / ".harness" / "README.md").read_text() == "my own readme\n"
    assert ".harness/README.md" not in lines or lines[".harness/README.md"].startswith("KEPT")


def test_report_has_one_known_result_per_file_and_updates_the_record(tmp_path, repo):
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t + "\nplugin line\n"})
    result, lines = upgrade(repo, plugin)
    assert set(lines.values()) <= {"REPLACED", "MERGED", "ADDED", "CONFLICT", "KEPT"}
    manifest = read_manifest(repo)
    assert manifest["version"] == "9.9.9"
    assert manifest["files"][STAGE]["sha256"] == sha256((plugin / "stages" / "REQUIREMENTS.md").read_bytes())
    assert (repo / ".kairyn" / ".base" / STAGE).read_bytes() == (plugin / "stages" / "REQUIREMENTS.md").read_bytes()
    assert manifest_problems(repo) == []


def test_a_second_upgrade_changes_nothing(tmp_path, repo):
    stage = repo / STAGE
    stage.write_text(stage.read_text().replace("# Stage: requirements", "# Stage: requirements (ours)"))
    plugin = new_plugin(tmp_path, edit={"stages/REQUIREMENTS.md": lambda t: t + "\nplugin line\n",
                                         "harness/CLAUDE.block.md": lambda t: t.replace("## kairyn", "## kairyn (new)")})
    upgrade(repo, plugin)
    before = tree(repo)
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 0 and set(lines.values()) == {"KEPT"}
    assert tree(repo) == before


def test_upgrade_needs_an_initialized_repo(tmp_path):
    result, _ = upgrade(tmp_path, PLUGIN)
    assert result.returncode == 2 and "/kairyn:init" in result.stdout + result.stderr


# --- repos from before the manifest (v0.1.0) ------------------------------------

def test_pre_manifest_files_that_match_a_release_are_replaced(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    result, lines = upgrade(repo, PLUGIN)
    assert lines[STAGE] == "REPLACED" and lines[".kairyn/stages/_template.md"] == "REPLACED"
    assert lines[".kairyn/stages/MODEL-ROUTING.md"] == "ADDED"
    assert (repo / STAGE).read_bytes() == (PLUGIN / "stages" / "REQUIREMENTS.md").read_bytes()


def test_pre_manifest_file_that_matches_no_release_takes_the_conflict_path(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    (repo / TEMPLATE).write_text("hand-made template\n")
    result, lines = upgrade(repo, PLUGIN)
    assert result.returncode == 1 and lines[TEMPLATE] == "CONFLICT"
    assert (repo / TEMPLATE).read_text() == "hand-made template\n"
    assert (repo / (TEMPLATE + ".kairyn-new")).read_bytes() == (PLUGIN / "templates" / "STATE.md").read_bytes()


def test_the_v0_1_0_fixture_upgrades_and_verifies(tmp_path):
    from helpers import run_verify
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    learnings = (repo / ".kairyn" / "learnings.md").read_bytes()
    result, lines = upgrade(repo, PLUGIN)
    assert result.returncode == 0, result.stdout
    assert "CONFLICT" not in lines.values()
    assert run_verify(repo).returncode == 0, run_verify(repo).stdout
    assert (repo / ".kairyn" / "learnings.md").read_bytes() == learnings
    assert any((repo / "docs" / "tasks").iterdir())


def test_this_repos_v0_1_0_stages_upgrade_without_conflict(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    for name in ("REQUIREMENTS.md", "_template.md"):
        shutil.copy(ROOT / ".kairyn" / "stages" / name, repo / ".kairyn" / "stages" / name)
    _, lines = upgrade(repo, PLUGIN)
    assert lines[STAGE] in ("REPLACED", "KEPT") and lines[".kairyn/stages/_template.md"] in ("REPLACED", "KEPT")


def test_a_plugin_owned_file_kept_by_resolving_its_conflict_stays_the_users(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    (repo / TEMPLATE).write_text("hand-made template\n")
    upgrade(repo, PLUGIN)
    (repo / (TEMPLATE + ".kairyn-new")).unlink()            # resolved: keep mine
    result, lines = upgrade(repo, PLUGIN)
    assert result.returncode == 0 and lines[TEMPLATE] == "KEPT"
    plugin = new_plugin(tmp_path, edit={"templates/STATE.md": lambda t: t + "\nnew line\n"})
    result, lines = upgrade(repo, plugin)
    assert (repo / TEMPLATE).read_text() == "hand-made template\n"
    assert not (repo / (TEMPLATE + ".kairyn-old")).exists()


def test_a_pre_manifest_repo_owned_file_kept_by_resolving_stays_the_users(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    readme = repo / ".harness" / "README.md"
    readme.write_text("our own dev readme\n")
    upgrade(repo, PLUGIN)
    (repo / ".harness" / "README.md.kairyn-new").unlink()
    upgrade(repo, PLUGIN)
    plugin = new_plugin(tmp_path, edit={"harness/.harness/README.md": lambda t: t + "\nnew line\n"})
    result, lines = upgrade(repo, plugin)
    assert result.returncode == 0 and readme.read_text() == "our own dev readme\n"
    assert not (repo / ".harness" / "README.md.kairyn-new").exists()
