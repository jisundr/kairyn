"""milestones.py: the milestone log and its watcher (task 2026-11-25-first-mate-hub).

Writers (hooks, afk.py) append `<UTC timestamp> [<run tag>] <text>` lines to one log. The first mate
runs `watch` through the Monitor tool: each stdout line is one chat message.
"""
import json
from pathlib import Path
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


def test_store_replaces_watch_json_atomically(tmp_path, monkeypatch):
    """store() writes a temp file in the same folder, then os.replace: a reader never sees watch.json empty.
    CI run 45548893428 read it between write_text's truncate and its write (JSONDecodeError)."""
    import milestones
    state = tmp_path / "watch.json"
    milestones.store(state, 1)
    seen = []
    real_replace = milestones.os.replace

    def spy(src, dst):
        seen.append((Path(src), Path(dst), json.loads(Path(dst).read_text())))   # the reader's view mid-write
        real_replace(src, dst)

    monkeypatch.setattr(milestones.os, "replace", spy)
    milestones.store(state, 2, "2026-11-25T00:00:00Z")
    assert len(seen) == 1, "store() must write through os.replace"
    src, dst, during = seen[0]
    assert dst == state and src.parent == state.parent and src != state
    assert during == {"line": 1}
    assert json.loads(state.read_text()) == {"line": 2, "unreachable": "2026-11-25T00:00:00Z"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["watch.json"], "no temp file left behind"


def test_store_leaves_no_temp_file_when_the_write_fails(tmp_path, monkeypatch):
    import milestones
    state = tmp_path / "watch.json"
    milestones.store(state, 1)

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(milestones.os, "replace", boom)
    try:
        milestones.store(state, 2)
    except OSError:
        pass
    else:
        raise AssertionError("the error must reach the caller")
    assert json.loads(state.read_text()) == {"line": 1}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["watch.json"]


def test_reader_never_sees_watch_json_empty_while_store_runs(tmp_path):
    """A second process polls watch.json (the test above, catchup in a new session) while watch stores."""
    import milestones
    state = tmp_path / "watch.json"
    milestones.store(state, 0)
    bad, stop = [], threading.Event()

    def reader():
        while not stop.is_set():
            try:
                json.loads(state.read_text())
            except ValueError as e:
                bad.append(repr(e))

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        for n in range(3000):
            milestones.store(state, n)
    finally:
        stop.set()
        t.join(timeout=5)
    assert not bad, f"{len(bad)} reads saw a partial file, first: {bad[0]}"


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


# --- T2: hooks write milestones ----------------------------------------------------------------


def hook(repo, payload, env=None, cwd=None):
    """Run `milestones.py hook` the way hooks.json does: the hook JSON on stdin, --root the project."""
    base = {k: v for k, v in __import__("os").environ.items() if k not in ("TMUX_PANE", "KAIRYN_MILESTONES")}
    return subprocess.run([sys.executable, str(SCRIPT), "hook", "--root", str(repo)], input=json.dumps(payload),
                          capture_output=True, text=True, env={**base, **(env or {})}, cwd=cwd or repo)


HOOK_FIXTURES = Path(__file__).parent / "fixtures" / "hooks"   # real Claude Code payloads, ids and paths blanked


def real_event(name):
    return json.loads((HOOK_FIXTURES / f"{name}.json").read_text())


def bash_event(command, code, event=None):
    """A real Bash hook payload for `command`. Claude Code sends a success as PostToolUse with no return code field,
    and a nonzero return code as PostToolUseFailure with `error: "Exit code N\n<output>"`."""
    payload = real_event("post_tool_use" if code == 0 else "post_tool_use_failure")
    payload["tool_input"]["command"] = command
    if code:
        payload["error"] = f"Exit code {code}\nFAILED tests/test_x.py"
    return payload


def test_real_hook_payloads_give_label_and_exit(tmp_path):
    """F2: the recorded payloads, unchanged except for the command, give the right exit code and message."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".kairyn").mkdir()
    (repo / ".kairyn" / "milestones.yml").write_text("write:\n  log: .session/milestones.log\n")
    ok, failed = real_event("post_tool_use"), real_event("post_tool_use_failure")
    assert "exitCode" not in ok["tool_response"] and failed["error"].startswith("Exit code 3")
    ok["tool_input"]["command"] = failed["tool_input"]["command"] = "uv run pytest"
    for payload in (ok, failed, real_event("stop")):
        assert hook(repo, payload).returncode == 0
    texts = [line.split("] ", 1)[1] for line in log_lines(repo)]
    assert texts == ["tests exit 0", "tests exit 3", "done"], texts


def log_lines(repo):
    log = repo / ".session" / "milestones.log"
    return log.read_text().splitlines() if log.exists() else []


def writer(tmp_path, extra=""):
    repo = git_repo(tmp_path / "cerna-home")
    settings(repo, "write:\n  log: .session/milestones.log\n" + extra)
    return repo


def test_post_tool_use_writes_label_and_exit_only_on_match(tmp_path):
    repo = writer(tmp_path)
    secret = "uv run pytest -k token=s3cr3t"
    assert hook(repo, bash_event(secret, 1, "PostToolUseFailure")).returncode == 0
    assert hook(repo, bash_event("ls -la", 0)).returncode == 0
    lines = log_lines(repo)
    assert len(lines) == 1, lines
    m = LINE.match(lines[0])
    assert m and m.group("text") == "tests exit 1", lines
    assert "s3cr3t" not in lines[0] and "pytest" not in lines[0]
    assert hook(repo, bash_event("git push -u origin main", 0)).returncode == 0
    assert LINE.match(log_lines(repo)[-1]).group("text") == "push exit 0"


def test_custom_patterns_replace_the_defaults(tmp_path):
    repo = writer(tmp_path, "  patterns:\n    deploy: '^make deploy'\n")
    hook(repo, bash_event("make deploy prod", 2, "PostToolUseFailure"))
    hook(repo, bash_event("uv run pytest", 0))
    assert [LINE.match(x).group("text") for x in log_lines(repo)] == ["deploy exit 2"]


def test_stop_writes_first_line_cut_to_200(tmp_path):
    repo = writer(tmp_path)
    message = "A" * 250 + "\nSecond line.\nThird line."
    assert hook(repo, {"hook_event_name": "Stop", "last_assistant_message": message}).returncode == 0
    lines = log_lines(repo)
    assert len(lines) == 1 and LINE.match(lines[0]).group("text") == "A" * 200


def test_stop_reads_the_transcript_when_no_message_is_given(tmp_path):
    repo = writer(tmp_path)
    transcript = tmp_path / "t.jsonl"
    rows = [{"type": "user", "message": {"role": "user", "content": "go"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Old."}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Pushed the branch.\nDetails follow."}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash"}]}}]
    transcript.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    hook(repo, {"hook_event_name": "Stop", "transcript_path": str(transcript)})
    assert [LINE.match(x).group("text") for x in log_lines(repo)] == ["Pushed the branch."]


def test_run_tag_from_tmux_pane_or_repo_folder(tmp_path):
    repo = writer(tmp_path)
    tmux = tmp_path / "tmux"
    tmux.write_text("#!/bin/sh\necho \"$@\" > \"$(dirname \"$0\")/tmux.args\"\necho 'server:2'\n")
    tmux.chmod(0o755)
    hook(repo, bash_event("npm test", 0))
    hook(repo, bash_event("npm test", 0), env={"TMUX_PANE": "%7", "KAIRYN_TMUX": str(tmux)})
    tags = [LINE.match(x).group("tag") for x in log_lines(repo)]
    assert tags == ["cerna-home", "server:2 cerna-home"], tags
    assert "%7" in (tmp_path / "tmux.args").read_text()


def test_hook_writes_nothing_when_off_or_unset(tmp_path):
    repo = writer(tmp_path)
    assert hook(repo, bash_event("npm test", 1, "PostToolUseFailure"), env={"KAIRYN_MILESTONES": "off"}).returncode == 0
    assert log_lines(repo) == []
    bare = git_repo(tmp_path / "bare")
    assert hook(bare, bash_event("npm test", 0)).returncode == 0
    assert not (bare / ".session").exists()
    assert hook(repo, {"hook_event_name": "Stop"}, cwd=repo).returncode == 0   # bad input never fails a turn
    assert subprocess.run([sys.executable, str(SCRIPT), "hook", "--root", str(repo)], input="not json",
                          capture_output=True, text=True).returncode == 0


def test_default_patterns_match_common_commands():
    import milestones
    expected = {"uv run pytest": "tests", "npm test": "tests", "git push": "push", "gh pr comment 12 -b hi": "comment",
                "ruff check .": "lint"}
    for command, label in expected.items():
        assert milestones.match(milestones.DEFAULT_PATTERNS, command) == label, command
    assert milestones.match(milestones.DEFAULT_PATTERNS, "ls -la") is None


def test_hooks_finish_within_one_second(tmp_path):
    repo = writer(tmp_path)
    (repo / ".session").mkdir()
    (repo / ".session" / ".gitignore").write_text("*\n")
    (repo / ".session" / "milestones.log").write_text("2026-11-25T00:00:00Z [x] old\n" * 10000)
    for payload in (bash_event("uv run pytest", 0), {"hook_event_name": "Stop", "last_assistant_message": "Done."}):
        start = time.monotonic()
        assert hook(repo, payload).returncode == 0
        assert time.monotonic() - start < 1.0
    assert len(log_lines(repo)) == 10002


def test_plugin_registers_the_milestone_hooks():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    for event in ("PostToolUse", "PostToolUseFailure", "Stop"):
        commands = [h["command"] for group in hooks[event] for h in group["hooks"]]
        assert any("scripts/milestones.py\" hook" in c and "CLAUDE_PROJECT_DIR" in c for c in commands), event
    for event in ("PostToolUse", "PostToolUseFailure"):
        assert all(group.get("matcher") == "Bash" for group in hooks[event]
                   if any("milestones.py" in h["command"] for h in group["hooks"]))


# --- T3: restart catch-up ----------------------------------------------------------------------


def first_mate(tmp_path, count, stored):
    """A home log of `count` lines and a first mate repo whose watch.json holds `stored`."""
    home = git_repo(tmp_path / "home")
    log = home / ".session" / "milestones.log"
    log.parent.mkdir(parents=True)
    log.write_text("".join(f"2026-11-25T00:00:0{n}Z [home] line {n}\n" for n in range(1, count + 1)))
    mate = git_repo(tmp_path / "mate")
    settings(mate, f"watch:\n  log: {log}\n")
    (mate / ".session").mkdir()
    (mate / ".session" / ".gitignore").write_text("*\n")
    (mate / ".session" / "watch.json").write_text(json.dumps({"line": stored}) + "\n")
    return home, mate


def catchup(repo, env=None):
    base = {k: v for k, v in __import__("os").environ.items() if k != "KAIRYN_MILESTONES"}
    return subprocess.run([sys.executable, str(SCRIPT), "catchup", "--root", str(repo)], capture_output=True,
                          text=True, env={**base, **(env or {})})


def printed_lines(out):
    return [LINE.match(x).group("text") for x in out.splitlines() if LINE.match(x)]


def test_catchup_prints_missed_lines_and_instruction(tmp_path):
    _, mate = first_mate(tmp_path, 5, 2)
    result = catchup(mate)
    assert result.returncode == 0, result.stderr
    assert printed_lines(result.stdout) == ["line 3", "line 4", "line 5"]
    assert "Monitor" in result.stdout
    assert re.search(r"milestones\.py\"? watch --root \"?" + re.escape(str(mate)), result.stdout), result.stdout
    assert json.loads((mate / ".session" / "watch.json").read_text())["line"] == 5
    again = catchup(mate)
    assert printed_lines(again.stdout) == [] and "Monitor" in again.stdout


def test_shorter_log_starts_from_line_one(tmp_path):
    _, mate = first_mate(tmp_path, 3, 10)
    assert printed_lines(catchup(mate).stdout) == ["line 1", "line 2", "line 3"]
    _, mate = first_mate(tmp_path / "w", 3, 10)
    proc = subprocess.Popen([sys.executable, "-u", str(SCRIPT), "watch", "--root", str(mate), "--interval", "0.2"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    got = []
    reader = threading.Thread(target=lambda: got.extend(proc.stdout.readline() for _ in range(3)), daemon=True)
    try:
        reader.start()
        reader.join(timeout=30)
        assert printed_lines("".join(got)) == ["line 1", "line 2", "line 3"]
    finally:
        proc.kill()
        proc.wait()


def test_catchup_is_silent_without_watch_settings_or_when_off(tmp_path):
    bare = git_repo(tmp_path / "bare")
    result = catchup(bare)
    assert result.returncode == 0 and result.stdout == ""
    assert not (bare / ".session").exists()
    _, mate = first_mate(tmp_path, 5, 2)
    off = catchup(mate, env={"KAIRYN_MILESTONES": "off"})
    assert off.returncode == 0 and off.stdout == ""


def test_plugin_registers_the_catchup_hook():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    commands = [h["command"] for group in hooks["SessionStart"] for h in group["hooks"]]
    assert any("scripts/milestones.py\" catchup" in c and "CLAUDE_PROJECT_DIR" in c for c in commands)


# --- T4: watch over ssh ------------------------------------------------------------------------


def ssh_stub(tmp_path, fails):
    """An ssh that fails its first `fails` calls with 255, then runs its last argument locally."""
    stub = tmp_path / "ssh"
    stub.write_text("#!/bin/sh\n"
                    "dir=$(dirname \"$0\")\n"
                    "echo \"$@\" >> \"$dir/ssh.calls\"\n"
                    "n=$(wc -l < \"$dir/ssh.calls\")\n"
                    f"[ \"$n\" -le {fails} ] && {{ echo 'ssh: connect: refused' >&2; exit 255; }}\n"
                    "for a; do last=$a; done\n"
                    "exec sh -c \"$last\"\n")
    stub.chmod(0o755)
    return stub


def host_mate(tmp_path, count, stored, fails):
    home, mate = first_mate(tmp_path, count, stored)
    settings(mate, f"watch:\n  host: dev-server\n  log: {home / '.session' / 'milestones.log'}\n")
    env = {k: v for k, v in __import__("os").environ.items() if k != "KAIRYN_MILESTONES"}
    return mate, {**env, "KAIRYN_SSH": str(ssh_stub(tmp_path, fails))}


def test_retry_delays_double_from_15_seconds_to_5_minutes():
    import milestones
    delays = milestones.retry_delays(15)
    assert [next(delays) for _ in range(8)] == [15, 30, 60, 120, 240, 300, 300, 300]


def test_watch_host_unreachable_once_then_catches_up(tmp_path):
    mate, env = host_mate(tmp_path, 5, 2, fails=3)
    proc = subprocess.Popen([sys.executable, "-u", str(SCRIPT), "watch", "--root", str(mate), "--interval", "0.1",
                             "--retry", "0.05"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    got = []
    reader = threading.Thread(target=lambda: got.extend(proc.stdout.readline() for _ in range(4)), daemon=True)
    try:
        reader.start()
        reader.join(timeout=30)
        assert len(got) == 4, got
        assert re.match(r"^server unreachable since \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", got[0]), got
        assert printed_lines("".join(got[1:])) == ["line 3", "line 4", "line 5"], got
        calls = (tmp_path / "ssh.calls").read_text().splitlines()
        assert len(calls) >= 4 and all("dev-server" in c and "tail -n +3" in c for c in calls[:4]), calls
        stored = json.loads((mate / ".session" / "watch.json").read_text())
        assert stored["line"] == 5 and not stored.get("unreachable"), stored
    finally:
        proc.kill()
        proc.wait()


def test_watch_host_failure_is_stored_and_not_repeated(tmp_path):
    mate, env = host_mate(tmp_path, 5, 2, fails=1000)
    proc = subprocess.Popen([sys.executable, "-u", str(SCRIPT), "watch", "--root", str(mate), "--interval", "0.1",
                             "--retry", "0.05"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        deadline = time.monotonic() + 10
        state = mate / ".session" / "watch.json"
        while time.monotonic() < deadline and not json.loads(state.read_text()).get("unreachable"):
            time.sleep(0.1)
        time.sleep(0.5)
    finally:
        proc.kill()
        out = proc.communicate()[0]
    assert out.count("server unreachable since") == 1, out
    stored = json.loads(state.read_text())
    assert stored["line"] == 2 and re.match(r"^\d{4}-\d\d-\d\dT", stored["unreachable"]), stored
    assert len((tmp_path / "ssh.calls").read_text().splitlines()) >= 3


def test_catchup_reads_the_host_log(tmp_path):
    mate, env = host_mate(tmp_path, 5, 2, fails=0)
    result = subprocess.run([sys.executable, str(SCRIPT), "catchup", "--root", str(mate)], capture_output=True,
                            text=True, env=env)
    assert printed_lines(result.stdout) == ["line 3", "line 4", "line 5"] and "Monitor" in result.stdout
    assert json.loads((mate / ".session" / "watch.json").read_text())["line"] == 5
    down, env = host_mate(tmp_path / "down", 5, 2, fails=1000)
    result = subprocess.run([sys.executable, str(SCRIPT), "catchup", "--root", str(down)], capture_output=True,
                            text=True, env=env)
    assert result.returncode == 0 and "server unreachable" in result.stdout and "Monitor" in result.stdout
    assert json.loads((down / ".session" / "watch.json").read_text())["line"] == 2


# --- T5: docs and eval ----------------------------------------------------------------------------------

MILESTONE_DOCS = ("plugin/harness/.harness/workflows/milestones.md", ".harness/workflows/milestones.md")   # this repo installs the shipped doc


def _asserts():
    import importlib.util
    from helpers import ROOT
    spec = importlib.util.spec_from_file_location("kairyn_asserts", ROOT / "evals" / "promptfoo" / "asserts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_milestone_docs_have_valid_headers():
    from harness_docs import doc_problems, read_meta
    from helpers import ROOT
    for rel in MILESTONE_DOCS:
        path = ROOT / rel
        assert path.is_file(), rel
        assert doc_problems(path, read_meta(path)) == [], rel
        assert "milestones.yml" in path.read_text(), rel


def test_shipped_milestone_doc_is_installed_and_indexed():
    from kairyn_files import owner_of
    assert owner_of(".harness/workflows/milestones.md") == "plugin"
    for index in (PLUGIN / "harness" / "CLAUDE.block.md", PLUGIN / "harness" / ".harness" / "README.md"):
        assert "workflows/milestones.md" in index.read_text(), index


def test_milestones_eval_names_its_dependencies_scenario_and_asserts():
    import yaml
    from helpers import ROOT
    config_path = ROOT / "evals" / "promptfoo" / "milestones.yaml"
    text = config_path.read_text()
    depends = text.splitlines()[0]
    for dep in ("plugin/scripts/milestones.py", "plugin/hooks/hooks.json"):
        assert dep in depends
    config = yaml.safe_load(text)
    provider = (ROOT / "evals" / "promptfoo" / "provider.py").read_text()
    asserts = _asserts()
    for test in config["tests"]:
        scenario = test["vars"]["scenario"]
        assert f"def {scenario}(" in provider and re.search(rf"\b{scenario}\b", provider.split("SCENARIOS = ")[1])
        for check in test["assert"]:
            assert callable(getattr(asserts, check["value"].split(":")[-1]))
            assert check["metric"] in test["metadata"]["min_pass_rate"]


def test_starts_monitor_passes_only_for_a_monitor_on_milestones_watch():
    asserts = _asserts()
    watch = {"name": "Monitor", "input": {"command": 'python3 "/p/scripts/milestones.py" watch --root "/r"'}}
    assert asserts.starts_monitor(json.dumps({"tools": [watch]}), {})["pass"]
    bash = {"name": "Bash", "input": {"command": 'python3 "/p/scripts/milestones.py" watch --root "/r"'}}
    assert not asserts.starts_monitor(json.dumps({"tools": [bash]}), {})["pass"]
    other = {"name": "Monitor", "input": {"command": "tail -f app.log"}}
    assert not asserts.starts_monitor(json.dumps({"tools": [other]}), {})["pass"]
    assert not asserts.starts_monitor(json.dumps({"tools": []}), {})["pass"]


def test_reports_missed_passes_only_when_the_reply_names_each_missed_milestone():
    asserts = _asserts()
    evidence = {"missed": ["tests exit 0", "push exit 0"]}
    assert asserts.reports_missed(json.dumps({**evidence, "reply": "Missed: tests exit 0, push exit 0."}), {})["pass"]
    assert not asserts.reports_missed(json.dumps({**evidence, "reply": "Missed: tests exit 0."}), {})["pass"]
