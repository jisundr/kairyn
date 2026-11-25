"""atomic_write.py: one shared write that a reader never sees empty (backlog atomic-state-md).

milestones.store() (watch.json) and afk.py Run.update() (STATE.md) write through it.
"""
import os
import threading
from pathlib import Path

import pytest

from helpers import PLUGIN

STATE = """---
task: 2026-01-05-feature
stage: build
status: in-progress
stages:
  build: pending
updated: 2026-01-05T09:20:00Z
---

# Log

2026-01-05T09:20:00Z [design] Approved.
"""


def test_write_text_replaces_through_a_temp_file_in_the_same_folder(tmp_path, monkeypatch):
    import atomic_write
    path = tmp_path / "STATE.md"
    path.write_text("old\n")
    seen = []
    real_replace = os.replace

    def spy(src, dst):
        seen.append((Path(src), Path(dst), Path(dst).read_text()))   # the reader's view mid-write
        real_replace(src, dst)

    monkeypatch.setattr(atomic_write.os, "replace", spy)
    atomic_write.write_text(path, "new\n")
    assert len(seen) == 1, "write_text must write through os.replace"
    src, dst, during = seen[0]
    assert dst == path and src.parent == path.parent and src != path
    assert during == "old\n"
    assert path.read_text() == "new\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["STATE.md"], "no temp file left behind"


def test_write_text_leaves_no_temp_file_when_the_write_fails(tmp_path, monkeypatch):
    import atomic_write
    path = tmp_path / "STATE.md"
    path.write_text("old\n")

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(atomic_write.os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write.write_text(path, "new\n")
    assert path.read_text() == "old\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["STATE.md"]


def test_milestones_store_writes_through_the_shared_helper(tmp_path, monkeypatch):
    import atomic_write
    import milestones
    calls = []
    monkeypatch.setattr(atomic_write, "write_text", lambda path, text: calls.append((path, text)))
    milestones.store(tmp_path / "watch.json", 3)
    assert calls == [(tmp_path / "watch.json", '{"line": 3}\n')]


def bare_run(tmp_path):
    """A Run whose task folder is a plain folder: update() needs no git."""
    import afk
    r = afk.Run.__new__(afk.Run)
    r.root, r.task, r.wt = tmp_path, "2026-01-05-feature", tmp_path / "wt"
    r.folder.mkdir(parents=True)
    (r.folder / "STATE.md").write_text(STATE)
    return r


def test_afk_update_writes_state_md_through_the_shared_helper(tmp_path, monkeypatch):
    import atomic_write
    r = bare_run(tmp_path)
    calls = []
    real = atomic_write.write_text
    monkeypatch.setattr(atomic_write, "write_text", lambda path, text: (calls.append(path), real(path, text)))
    r.update("build", "Build started.", status="in-progress", stage_status="in-progress")
    assert calls == [r.folder / "STATE.md"]
    assert "[build] Build started." in r.state()


def test_reader_never_sees_state_md_empty_while_afk_updates_it(tmp_path):
    """A second process (afk.py run or approve, close.py, a first mate) reads STATE.md while update() writes it.
    On an empty read, front() returns None: a blocked run does not resume, close says `status None`."""
    r = bare_run(tmp_path)
    state = r.folder / "STATE.md"
    bad, stop = [], threading.Event()

    def reader():
        while not stop.is_set():
            text = state.read_text()
            if "status: in-progress" not in text.partition("\n---\n")[0]:
                bad.append(len(text))

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        for n in range(1500):
            r.update("build", f"line {n}")
    finally:
        stop.set()
        t.join(timeout=5)
    assert not bad, f"{len(bad)} reads saw an empty or partial STATE.md, first length: {bad[0]}"
    assert state.read_text().count("[build] line ") == 1500


def test_helper_ships_in_plugin_scripts():
    assert (PLUGIN / "scripts" / "atomic_write.py").is_file()


def test_write_text_keeps_the_file_mode(tmp_path):
    """mkstemp makes the temp file 0600; STATE.md keeps the mode it had."""
    import atomic_write
    path = tmp_path / "STATE.md"
    path.write_text("old\n")
    path.chmod(0o644)
    atomic_write.write_text(path, "new\n")
    assert path.stat().st_mode & 0o777 == 0o644
