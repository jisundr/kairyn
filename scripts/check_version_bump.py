#!/usr/bin/env python3
"""Fail when plugin/ changed since a base commit but plugin.json's version is not newer.

Without a bump, consumers' version checks never see the change, so it never reaches them.
CI runs it on pull requests into main.

Usage (inside the repo): python scripts/check_version_bump.py <base-ref>
"""
import json
import subprocess
import sys
from pathlib import Path

PLUGIN_JSON = "plugin/.claude-plugin/plugin.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def _parts(version: str) -> tuple:
    return tuple(int(p) for p in version.split("."))


def problems(repo: Path, base: str) -> list[str]:
    changed = _git(repo, "diff", "--name-only", f"{base}...HEAD", "--", "plugin").split()
    if not changed:
        return []
    old = json.loads(_git(repo, "show", f"{base}:{PLUGIN_JSON}"))["version"]
    new = json.loads((repo / PLUGIN_JSON).read_text())["version"]
    if _parts(new) > _parts(old):
        return []
    return [f"{len(changed)} file(s) under plugin/ changed, but {PLUGIN_JSON} is still {new} "
            f"(base has {old}). Bump the version and regenerate plugin/release-hashes.json."]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.split("Usage")[1].strip(), file=sys.stderr)
        return 2
    found = problems(Path.cwd(), argv[0])
    for p in found:
        print(f"FAIL: {p}")
    if not found:
        print("OK: plugin version bumped, or plugin/ unchanged")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
