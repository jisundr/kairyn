"""milestones.py: the milestone log and its watcher (task 2026-11-25-first-mate-hub).

Writers (hooks, afk.py) append `<UTC timestamp> [<run tag>] <text>` lines to one log. The first mate
runs `watch` through the Monitor tool: each stdout line is one chat message.
"""
import json
import re
import subprocess
import sys
import threading
import time

from helpers import PLUGIN

SCRIPT = PLUGIN / "scripts" / "milestones.py"
sys.path.insert(0, str(PLUGIN / "scripts"))
LINE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \[(?P<tag>[^\]]+)\] (?P<text>.*)$")


def git_repo(path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    return path


def settings(repo, text):
    (repo / ".kairyn").mkdir(parents=True, exist_ok=True)
    (repo / ".kairyn" / "milestones.yml").write_text(text)


def test_no_settings_writes_nothing(tmp_path):
    import milestones
    repo = git_repo(tmp_path / "repo")
    assert milestones.write(repo, "tag", "Tests passed.") is None
    assert not (repo / ".session").exists()
    result = subprocess.run([sys.executable, str(SCRIPT), "write", "--root", str(repo), "--tag", "t", "hi"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert list(repo.rglob("*.log")) == [] and not (repo / ".session").exists()


def test_session_folder_gets_gitignore(tmp_path):
    import milestones
    repo = git_repo(tmp_path / "repo")
    settings(repo, "write:\n  log: .session/milestones.log\n")
    log = milestones.write(repo, "cerna-home", "x" * 300)
    assert log == repo / ".session" / "milestones.log"
    assert (repo / ".session" / ".gitignore").read_text().strip() == "*"
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    m = LINE.match(lines[0])
    assert m and m.group("tag") == "cerna-home" and m.group("text") == "x" * 200
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"],
                            capture_output=True, text=True, check=True).stdout
    assert ".session" not in status, status


def test_watch_local_prints_new_line_and_stores_number(tmp_path):
    import milestones
    home = git_repo(tmp_path / "home")
    settings(home, "write:\n  log: .session/milestones.log\n")
    milestones.write(home, "old", "Before the watcher started.")
    mate = git_repo(tmp_path / "mate")
    settings(mate, f"watch:\n  log: {home / '.session' / 'milestones.log'}\n")
    proc = subprocess.Popen([sys.executable, "-u", str(SCRIPT), "watch", "--root", str(mate), "--interval", "0.2"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    got = []
    reader = threading.Thread(target=lambda: got.append(proc.stdout.readline()), daemon=True)
    try:
        time.sleep(0.5)
        start = time.monotonic()
        milestones.write(home, "cerna-home", "Tests passed.")
        reader.start()
        reader.join(timeout=60)
        assert got and got[0].strip(), "the watcher printed nothing within 60 s"
        assert time.monotonic() - start < 60
        m = LINE.match(got[0].strip())
        assert m and m.group("tag") == "cerna-home" and m.group("text") == "Tests passed."
        stored = mate / ".session" / "watch.json"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not (stored.exists() and json.loads(stored.read_text()).get("line") == 2):
            time.sleep(0.1)
        assert json.loads(stored.read_text())["line"] == 2
        assert (mate / ".session" / ".gitignore").exists()
    finally:
        proc.kill()
        proc.wait()
