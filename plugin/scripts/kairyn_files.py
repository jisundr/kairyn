#!/usr/bin/env python3
"""The files kairyn installs in a repo, who owns each one, and the record of what was installed.

Owners decide what an upgrade may do:
    plugin  replaced on upgrade (the user's edits are saved aside)
    repo    merged on upgrade: base, local file and new file in three ways
Files with no owner (learnings.md, docs/tasks/, the user's own docs, CLAUDE.md outside the
kairyn block) are never touched.

The record:
    .kairyn/manifest.json  {"version": "<plugin version>", "files": {"<repo path>": {"sha256", "owner"}}}
    .kairyn/.base/<repo path>  an exact copy of each recorded file, the merge base for upgrades
The kairyn block in CLAUDE.md is recorded as the path "CLAUDE.md#kairyn". Its doc index
(the harness-docs region) is left out of its hash, because /kairyn:check write refreshes it.
An entry with "pending": true is an open upgrade conflict: <file>.kairyn-new waits for the user.
"no_base": true marks a conflict that had nothing to merge from (a repo set up before the manifest).

Standard library only: consumers run this with a plain python3.

Usage:
    python3 kairyn_files.py manifest <repo> <repo path>...   # record these just-installed files
    python3 kairyn_files.py check <repo>                     # exit 1 if the record is missing or broken
"""
from __future__ import annotations   # init runs this; macOS ships python3 3.9

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

BLOCK = "CLAUDE.md#kairyn"
MANIFEST = ".kairyn/manifest.json"
BASE = ".kairyn/.base"
_BLOCK_RE = re.compile(r"<!-- kairyn:start -->.*?<!-- kairyn:end -->\n?", re.S)
_INDEX_RE = re.compile(r"(<!-- harness-docs:start -->).*?(<!-- harness-docs:end -->)", re.S)

# Files under .harness/ the plugin ships but the repo owns. Other shipped harness files are plugin-owned.
REPO_OWNED_HARNESS = {".harness/README.md", ".harness/budgets.yml"}


class Entry(NamedTuple):
    path: str      # repo path, or BLOCK
    source: Path   # the shipped file in the plugin
    owner: str     # "plugin" or "repo"


def installed_files(plugin: Path) -> list[Entry]:
    """Every file init installs, as shipped in this plugin."""
    entries = []
    for kind in ("stages", "templates"):
        for src in sorted((plugin / kind).iterdir()):
            if src.is_file():
                path = f".kairyn/{kind}/{src.name}"
                entries.append(Entry(path, src, owner_of(path)))
    harness = plugin / "harness" / ".harness"
    for src in sorted(p for p in harness.rglob("*") if p.is_file()):
        path = ".harness/" + src.relative_to(harness).as_posix()
        entries.append(Entry(path, src, owner_of(path)))
    entries.append(Entry(BLOCK, plugin / "harness" / "CLAUDE.block.md", "plugin"))
    return entries


# A new shipped harness doc must be added here, or init cannot record it (a test checks).
_KAIRYN_HARNESS_DOCS = {".harness/workflows/running-stages.md", ".harness/workflows/task-lifecycle.md",
                        ".harness/workflows/keeping-docs-lean.md", ".harness/workflows/afk-run.md"}


def owner_of(path: str) -> str | None:
    if path.startswith(".kairyn/stages/") or path in REPO_OWNED_HARNESS:
        return "repo"
    if path.startswith(".kairyn/templates/") or path in _KAIRYN_HARNESS_DOCS or path == BLOCK:
        return "plugin"
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def block_text(claude_md: str) -> str | None:
    """The kairyn block in CLAUDE.md, markers included, or None."""
    m = _BLOCK_RE.search(claude_md)
    return m.group() if m else None


def comparable_block(block: str) -> str:
    """The block as recorded and compared: its doc index emptied."""
    return _INDEX_RE.sub(lambda m: f"{m.group(1)}\n{m.group(2)}", block)


def shipped_bytes(entry: Entry) -> bytes:
    """A shipped file as recorded and compared (the block: marked region, index emptied)."""
    if entry.path == BLOCK:
        return comparable_block(block_text(entry.source.read_text()) or entry.source.read_text()).encode()
    return entry.source.read_bytes()


def current_bytes(repo: Path, path: str) -> bytes | None:
    """What the repo holds for a recorded path now, as recorded and compared, or None if it is gone."""
    if path == BLOCK:
        claude = repo / "CLAUDE.md"
        block = block_text(claude.read_text()) if claude.is_file() else None
        return comparable_block(block).encode() if block is not None else None
    target = repo / path
    return target.read_bytes() if target.is_file() else None


def plugin_version(plugin: Path) -> str:
    return json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["version"]


def read_manifest(repo: Path) -> dict:
    return json.loads((repo / MANIFEST).read_text())


class Record(NamedTuple):
    data: bytes            # the merge base: the shipped version this repo last took
    owner: str
    pending: bool = False  # an open conflict
    no_base: bool = False  # that conflict had no merge base


def write_record(repo: Path, version: str, records: dict) -> None:
    """Write .kairyn/manifest.json and .kairyn/.base/ for {path: Record}. Paths not given are dropped."""
    files = {}
    for path, rec in sorted(records.items()):
        base = repo / BASE / path
        base.parent.mkdir(parents=True, exist_ok=True)
        base.write_bytes(rec.data)
        flags = {"pending": True, **({"no_base": True} if rec.no_base else {})} if rec.pending else {}
        files[path] = {"sha256": sha256(rec.data), "owner": rec.owner, **flags}
    (repo / MANIFEST).write_text(json.dumps({"version": version, "files": files}, indent=2, sort_keys=True) + "\n")


def write_manifest(repo: Path, plugin: Path, paths: list[str]) -> None:
    """Record just-installed files: hash each one into the manifest and copy it to .base/."""
    records = {}
    for path in paths:
        owner, data = owner_of(path), current_bytes(repo, path)
        if owner is None or data is None:
            raise ValueError(f"cannot record {path!r}: no owner or not installed")
        records[path] = Record(data, owner)
    write_record(repo, plugin_version(plugin), records)


def manifest_problems(repo: Path) -> list[str]:
    """The record is present and consistent. Edits to installed files are not problems."""
    if not (repo / MANIFEST).is_file():
        return [f"{MANIFEST} missing (set up before kairyn recorded versions: run /kairyn:upgrade)"]
    try:
        manifest = read_manifest(repo)
        version, files = manifest["version"], manifest["files"]
        if not isinstance(version, str) or not isinstance(files, dict):
            raise TypeError("version must be a string and files a mapping")
    except (ValueError, KeyError, TypeError) as e:
        return [f"{MANIFEST} invalid: {e}"]
    problems = []
    for path, entry in sorted(files.items()):
        if (not isinstance(entry, dict) or entry.get("owner") not in ("plugin", "repo") or not entry.get("sha256")
                or not isinstance(entry.get("pending", False), bool)):
            problems.append(f"{MANIFEST}: bad entry for {path}")
            continue
        base = repo / BASE / path
        if not base.is_file():
            problems.append(f"{BASE}/{path} missing")
        elif sha256(base.read_bytes()) != entry["sha256"]:
            problems.append(f"{BASE}/{path} does not match {MANIFEST}")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "manifest":
        repo = Path(argv[1])
        write_manifest(repo, Path(__file__).resolve().parent.parent, argv[2:])
        return 0
    if len(argv) == 2 and argv[0] == "check":
        problems = manifest_problems(Path(argv[1]))
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1 if problems else 0
    print(__doc__.split("Usage:")[1].rstrip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
