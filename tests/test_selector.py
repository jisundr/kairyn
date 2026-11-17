"""The eval selector: run an eval only when the files it depends on changed."""
import json

import pytest

from selector import deps_hash, load_record, needs_run, parse_depends, record_pass, save_record


# --- parse_depends -----------------------------------------------------------

def test_parse_depends_reads_comma_separated_paths():
    text = "# depends: plugin/a.md, plugin/scripts/*\nFeature: x\n"
    assert parse_depends(text) == ["plugin/a.md", "plugin/scripts/*"]


def test_parse_depends_without_header_is_empty():
    assert parse_depends("Feature: x\n") == []


def test_parse_depends_ignores_other_comments():
    text = "# just a comment\n# depends: a.md\nFeature: x\n"
    assert parse_depends(text) == ["a.md"]


# --- deps_hash ---------------------------------------------------------------

@pytest.fixture
def tree(tmp_path):
    (tmp_path / "plugin" / "scripts").mkdir(parents=True)
    (tmp_path / "plugin" / "a.md").write_text("a")
    (tmp_path / "plugin" / "b.md").write_text("b")
    (tmp_path / "plugin" / "scripts" / "x.sh").write_text("x")
    return tmp_path


def test_hash_is_stable(tree):
    assert deps_hash(tree, ["plugin/a.md"]) == deps_hash(tree, ["plugin/a.md"])


def test_hash_changes_when_dependency_changes(tree):
    before = deps_hash(tree, ["plugin/a.md"])
    (tree / "plugin" / "a.md").write_text("changed")
    assert deps_hash(tree, ["plugin/a.md"]) != before


def test_hash_ignores_unrelated_files(tree):
    before = deps_hash(tree, ["plugin/a.md"])
    (tree / "plugin" / "b.md").write_text("changed")
    assert deps_hash(tree, ["plugin/a.md"]) == before


def test_hash_expands_globs(tree):
    before = deps_hash(tree, ["plugin/scripts/*"])
    (tree / "plugin" / "scripts" / "y.sh").write_text("new file")
    assert deps_hash(tree, ["plugin/scripts/*"]) != before


def test_hash_changes_when_dependency_is_deleted(tree):
    before = deps_hash(tree, ["plugin/a.md"])
    (tree / "plugin" / "a.md").unlink()
    assert deps_hash(tree, ["plugin/a.md"]) != before


def test_hash_does_not_depend_on_pattern_order(tree):
    assert deps_hash(tree, ["plugin/a.md", "plugin/b.md"]) == deps_hash(tree, ["plugin/b.md", "plugin/a.md"])


# --- needs_run / record_pass -------------------------------------------------

def test_never_run_needs_run():
    assert needs_run("init", "h1", {}) is True


def test_unchanged_since_last_pass_is_skipped():
    assert needs_run("init", "h1", {"init": "h1"}) is False


def test_changed_since_last_pass_needs_run():
    assert needs_run("init", "h2", {"init": "h1"}) is True


def test_force_always_runs():
    assert needs_run("init", "h1", {"init": "h1"}, force=True) is True


def test_record_pass_stores_hash_without_mutating_input():
    original = {"other": "h0"}
    updated = record_pass(original, "init", "h1")
    assert updated == {"other": "h0", "init": "h1"}
    assert original == {"other": "h0"}


# --- load_record / save_record -----------------------------------------------

def test_load_missing_record_is_empty(tmp_path):
    assert load_record(tmp_path / "nope.json") == {}


def test_load_corrupt_record_is_empty(tmp_path):
    path = tmp_path / "passed.json"
    path.write_text("{not json")
    assert load_record(path) == {}


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "sub" / "passed.json"
    save_record(path, {"init": "h1"})
    assert load_record(path) == {"init": "h1"}
    assert json.loads(path.read_text()) == {"init": "h1"}
