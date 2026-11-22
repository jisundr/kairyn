#!/usr/bin/env python3
"""Warn when this plugin is newer than the kairyn files installed in a repo.

Prints one line naming /kairyn:upgrade when the plugin is newer, and nothing otherwise
(no .kairyn/, versions match, or the repo is newer). Always exits 0 and writes no file.
Runs in /kairyn:check, verify-init.sh and the SessionStart hook, so it stays small and fast.

Usage: python3 version_check.py [--root DIR] [--plugin DIR]
"""
from __future__ import annotations   # macOS ships python3 3.9

import json
import sys
from pathlib import Path


def _parts(version: str) -> tuple:
    try:
        return tuple(int(p) for p in version.split("."))
    except (AttributeError, ValueError):
        return ()


def newer(a: str, b: str) -> bool:
    return _parts(a) > _parts(b)


def message(repo: Path, plugin: Path) -> str | None:
    if not (repo / ".kairyn").is_dir():
        return None
    current = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["version"]
    try:
        installed = json.loads((repo / ".kairyn" / "manifest.json").read_text())["version"]
    except (OSError, ValueError, KeyError):
        installed = "0.1.0"   # no manifest: set up before 0.2.0
    if not newer(current, installed):
        return None
    return f"kairyn {current} is installed, but this repo's kairyn files are {installed}: run /kairyn:upgrade"


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path.cwd()
    plugin = Path(argv[argv.index("--plugin") + 1]) if "--plugin" in argv else Path(__file__).resolve().parent.parent
    try:
        line = message(root, plugin)
    except (OSError, ValueError, KeyError):
        line = None   # a warning tool: never break a session or a check
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
