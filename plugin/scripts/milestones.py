#!/usr/bin/env python3
"""Milestone messages for the first mate: one log that writers append to and a watcher streams.

    python3 milestones.py write --tag <run tag> <text>   # append one line (afk.py imports write())
    python3 milestones.py watch [--interval <s>]         # print each new log line; run it with Monitor

All take --root (default: the current directory). Settings: .kairyn/milestones.yml, optional:
    write:
      log: .session/milestones.log      # writer repo: where lines go. No log: write nothing.
    watch:
      log: ~/Projects/home/.session/milestones.log   # first mate repo: the log to read
A line is `<UTC timestamp> [<run tag>] <text>`, the text cut to 200 characters. A new `.session/`
folder gets a `.gitignore` that ignores all its files. `watch` stores the number of the last line it
printed in `.session/watch.json` of its repo; with no stored number it starts at the log's end.

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(".kairyn") / "milestones.yml"
SESSION = ".session"
MAX_TEXT = 200


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


def watch(root: Path, interval: float) -> int:
    conf = settings(root).get("watch")
    raw = conf.get("log") if isinstance(conf, dict) else None
    if not raw:
        print("milestones: no watch log set in .kairyn/milestones.yml", file=sys.stderr)
        return 2
    log = _path(root, raw)
    state = session_dir(root / SESSION) / "watch.json"
    try:
        done = int(json.loads(state.read_text())["line"])
    except (OSError, ValueError, KeyError, TypeError):
        done = len(_read_lines(log))
        state.write_text(json.dumps({"line": done}) + "\n")
    while True:
        lines = _read_lines(log)
        if len(lines) > done:
            for line in lines[done:]:
                print(line, flush=True)
            done = len(lines)
            state.write_text(json.dumps({"line": done}) + "\n")
        time.sleep(interval)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("write")
    w.add_argument("--tag", required=True)
    w.add_argument("text")
    v = sub.add_parser("watch")
    v.add_argument("--interval", type=float, default=5.0)
    for p in (w, v):
        p.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "write":
        write(root, args.tag, args.text)
        return 0
    return watch(root, args.interval)


if __name__ == "__main__":
    sys.exit(main())
