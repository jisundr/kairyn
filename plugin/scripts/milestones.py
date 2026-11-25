#!/usr/bin/env python3
"""Milestone messages for the first mate: one log that writers append to and a watcher streams.

    python3 milestones.py write --tag <run tag> <text>   # append one line (afk.py imports write())
    python3 milestones.py hook                           # PostToolUse, PostToolUseFailure, Stop: hook JSON on stdin
    python3 milestones.py watch [--interval <s>]         # print each new log line; run it with Monitor
    python3 milestones.py catchup                        # SessionStart: missed lines, then how to start watch

All take --root (default: the current directory). Settings: .kairyn/milestones.yml, optional:
    write:
      log: .session/milestones.log      # writer repo: where lines go. No log: write nothing.
      patterns:                         # optional: <label>: <regex on the Bash command>; replaces the defaults
        tests: '\bpytest\b'
    watch:
      host: dev-server                               # optional: read the log over ssh
      log: ~/Projects/home/.session/milestones.log   # first mate repo: the log to read
A line is `<UTC timestamp> [<run tag>] <text>`, the text cut to 200 characters. A new `.session/`
folder gets a `.gitignore` that ignores all its files. `watch` stores the number of the last line it
printed in `.session/watch.json` of its repo; with no stored number it starts at the log's end, and a
log shorter than the stored number starts from line 1. `catchup` prints the lines after the stored number,
stores the new number, and tells the first mate to start `watch` with the Monitor tool.
With a host, both read with `ssh <host> tail -n +<n>`. When ssh fails, `watch` prints one
`server unreachable since <time>`, stores the time, and retries quietly: --retry seconds (15), doubling
to 5 minutes. KAIRYN_SSH overrides the ssh binary (tests use a stub).
`hook` writes the label and the exit code of a Bash command that matches a pattern (never the command text) and
the first line of the last assistant message at Stop. Its run tag is `<tmux session>:<window> <repo folder>`,
or the repo folder outside tmux. KAIRYN_MILESTONES=off (afk.py sessions) makes it write nothing.
KAIRYN_TMUX overrides the tmux binary (tests use a stub). A hook never fails the turn: errors exit 0.

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(".kairyn") / "milestones.yml"
SESSION = ".session"
MAX_TEXT = 200
MAX_RETRY = 300
DEFAULT_PATTERNS = {
    "tests": r"\b(pytest|(npm|pnpm|yarn|bun)( run)? test|go test|cargo test|jest|vitest|rspec|phpunit)\b",
    "lint": r"\b(ruff|eslint|flake8|pylint|mypy|golangci-lint|(npm|pnpm|yarn|bun) run lint)\b",
    "push": r"\bgit push\b",
    "comment": r"\b(gh pr (comment|review)|gh api \S*/comments|glab mr note)\b",
}


def _value(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def parse_settings(text: str) -> dict:
    """Nested `key: value` maps by indent. Full-line `#` comments and blank lines are skipped."""
    root: dict = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key, sep, rest = raw.strip().partition(":")
        if not sep:
            raise ValueError(f"milestones.yml: expected `key: value`, got {raw!r}")
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if rest.strip():
            parent[key.strip()] = _value(rest)
        else:
            parent[key.strip()] = child = {}
            stack.append((indent, child))
    return root


def settings(root: Path) -> dict:
    path = root / SETTINGS
    return parse_settings(path.read_text()) if path.is_file() else {}


def _path(root: Path, raw: str) -> Path:
    path = Path(os.path.expanduser(raw))
    return path if path.is_absolute() else root / path


def session_dir(folder: Path) -> Path:
    """Create the folder, with a `.gitignore` that ignores all its files, if it is missing (R7)."""
    if not folder.is_dir():
        folder.mkdir(parents=True)
        (folder / ".gitignore").write_text("*\n")
    return folder


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(root: Path, tag: str, text: str, when: str = ""):
    """Append one milestone line. Returns the log path, or None when no log is set (R6)."""
    conf = settings(root).get("write")
    raw = conf.get("log") if isinstance(conf, dict) else None
    if not raw:
        return None
    log = _path(root, raw)
    session_dir(log.parent)
    first = (text.strip().splitlines() or [""])[0]
    with log.open("a") as f:
        f.write(f"{when or stamp()} [{tag}] {first[:MAX_TEXT]}\n")
    return log


def _read_lines(log: Path) -> list:
    return log.read_text().splitlines() if log.is_file() else []


def match(patterns: dict, command: str):
    """The label of the first pattern that matches the command, or None."""
    for label, pattern in patterns.items():
        if re.search(pattern, command):
            return label
    return None


def run_tag(root: Path) -> str:
    """`<tmux session>:<window> <repo folder>` in tmux, else the repo folder (R5)."""
    pane = os.environ.get("TMUX_PANE")
    if pane:
        try:
            out = subprocess.run([os.environ.get("KAIRYN_TMUX", "tmux"), "display-message", "-p", "-t", pane,
                                  "#S:#I"], capture_output=True, text=True, timeout=0.8)
            where = out.stdout.strip()
            if out.returncode == 0 and where:
                return f"{where} {root.name}"
        except (OSError, subprocess.SubprocessError):
            pass
    return root.name


def return_code(event: dict) -> int:
    response = event.get("tool_response")
    if isinstance(response, dict):
        for key in ("exitCode", "returnCode", "code"):
            if isinstance(response.get(key), int):
                return response[key]
    found = re.search(r"[Ee]xit code (\d+)", str(event.get("error") or ""))
    if found:
        return int(found.group(1))
    return 1 if event.get("hook_event_name") == "PostToolUseFailure" else 0


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content
                         if isinstance(part, dict) and part.get("type") == "text").strip()
    return ""


def last_message(transcript: str) -> str:
    """The text of the last assistant message with text, read from the end of a transcript JSONL."""
    path = Path(transcript)
    if not path.is_file():
        return ""
    with path.open("rb") as f:
        f.seek(max(0, path.stat().st_size - 2_000_000))
        rows = f.read().decode("utf-8", "replace").splitlines()
    for row in reversed(rows):
        try:
            data = json.loads(row)
        except ValueError:
            continue
        message = data.get("message") if isinstance(data, dict) else None
        if data.get("type") == "assistant" and isinstance(message, dict):
            text = _text(message.get("content"))
            if text:
                return text
    return ""


def hook(root: Path, raw: str) -> None:
    """Write the milestone for one hook event, if any (R1, R2)."""
    if os.environ.get("KAIRYN_MILESTONES", "").lower() == "off":
        return
    conf = settings(root).get("write")
    if not isinstance(conf, dict) or not conf.get("log"):
        return
    event = json.loads(raw)
    name = event.get("hook_event_name")
    if name in ("PostToolUse", "PostToolUseFailure"):
        command = (event.get("tool_input") or {}).get("command") or ""
        patterns = conf.get("patterns")
        label = match(patterns if isinstance(patterns, dict) and patterns else DEFAULT_PATTERNS, command)
        text = f"{label} exit {return_code(event)}" if label else ""
    elif name == "Stop":
        text = event.get("last_assistant_message") or last_message(event.get("transcript_path") or "")
    else:
        return
    if text.strip():
        write(root, run_tag(root), text)


class Unreachable(Exception):
    pass


def watch_source(root: Path):
    """(host or None, log) from the watch settings, or None when no log is set."""
    conf = settings(root).get("watch")
    raw = conf.get("log") if isinstance(conf, dict) else None
    if not raw:
        return None
    host = conf.get("host") or None
    return host, (raw if host else _path(root, raw))


def _remote(path: str) -> str:
    return '"$HOME"/' + shlex.quote(path[2:]) if path.startswith("~/") else shlex.quote(path)


def fetch(source, after: int):
    """(line count, the lines after line `after`) of the log, local or over ssh. Raises Unreachable."""
    host, log = source
    if not host:
        lines = _read_lines(log)
        return len(lines), lines[after:]
    q = _remote(str(log))
    script = f"[ -f {q} ] || {{ echo 0; exit 0; }}; wc -l < {q}; tail -n +{after + 1} {q}"
    try:
        out = subprocess.run([os.environ.get("KAIRYN_SSH", "ssh"), "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                              host, script], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as err:
        raise Unreachable(str(err))
    rows = out.stdout.splitlines()
    if out.returncode != 0 or not rows or not rows[0].strip().isdigit():
        raise Unreachable(out.stderr.strip())
    return int(rows[0]), rows[1:]


def retry_delays(start: float):
    """start, doubling, at most MAX_RETRY seconds (R11)."""
    delay = start
    while True:
        yield min(delay, MAX_RETRY)
        delay = min(delay * 2, MAX_RETRY)


def stored_line(state: Path):
    try:
        return int(json.loads(state.read_text())["line"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def stored_since(state: Path) -> str:
    try:
        return str(json.loads(state.read_text()).get("unreachable") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def store(state: Path, line: int, since: str = "") -> None:
    data = {"line": line, **({"unreachable": since} if since else {})}
    state.write_text(json.dumps(data) + "\n")


def catchup(root: Path) -> None:
    """Print the lines after the stored number and the watcher instruction (R10, R13)."""
    if os.environ.get("KAIRYN_MILESTONES", "").lower() == "off":
        return
    source = watch_source(root)
    if not source:
        return
    state = session_dir(root / SESSION) / "watch.json"
    done = stored_line(state)
    try:
        count, missed = fetch(source, done or 0)
        if done is None:
            done, missed = count, []
        elif done > count:
            count, missed = fetch(source, 0)
        if missed:
            print(f"Milestones since the last session ({len(missed)}):")
            for line in missed:
                print(line)
        store(state, count)
    except Unreachable:
        print(f"Milestones: server {source[0]} unreachable since {stored_since(state) or stamp()}; "
              "watch catches up when it answers.")
    script = Path(__file__).resolve()
    print(f'Start the milestone watcher now with the Monitor tool: python3 "{script}" watch --root "{root}". '
          "Each line it prints is one milestone; tell the user. When Monitor stops, start it again.")


def watch(root: Path, interval: float, retry: float = 15.0) -> int:
    source = watch_source(root)
    if not source:
        print("milestones: no watch log set in .kairyn/milestones.yml", file=sys.stderr)
        return 2
    state = session_dir(root / SESSION) / "watch.json"
    done = stored_line(state)
    since = stored_since(state)
    delays = None
    while True:
        try:
            count, new = fetch(source, done or 0)
        except Unreachable:   # tell once, retry quietly with a growing delay (R11)
            if not since:
                since = stamp()
                print(f"server unreachable since {since}", flush=True)
                store(state, done or 0, since)
            delays = delays or retry_delays(retry)
            time.sleep(next(delays))
            continue
        delays = None
        if done is None:
            done, new = count, []
        if count < done:   # a shorter log: cleanup removed it, start from line 1 (R13)
            done = 0
            continue
        for line in new:
            print(line, flush=True)
        if new or since:   # back online: the missed lines are out, clear the notice (R12)
            done, since = done + len(new), ""
            store(state, done)
        elif not state.exists():
            store(state, done)
        time.sleep(interval)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("write")
    w.add_argument("--tag", required=True)
    w.add_argument("text")
    v = sub.add_parser("watch")
    v.add_argument("--interval", type=float, default=5.0)
    v.add_argument("--retry", type=float, default=15.0)
    h = sub.add_parser("hook")
    c = sub.add_parser("catchup")
    for p in (w, v, h, c):
        p.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "write":
        write(root, args.tag, args.text)
        return 0
    if args.command == "hook":
        try:
            hook(root, sys.stdin.read())
        except Exception as err:   # a milestone must never fail the user's turn
            print(f"milestones: {err}", file=sys.stderr)
        return 0
    if args.command == "catchup":
        try:
            catchup(root)
        except Exception as err:   # a session start must never fail
            print(f"milestones: {err}", file=sys.stderr)
        return 0
    return watch(root, args.interval, args.retry)


if __name__ == "__main__":
    sys.exit(main())
