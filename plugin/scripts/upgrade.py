#!/usr/bin/env python3
"""/kairyn:upgrade: bring a repo's installed kairyn files up to this plugin's version.

One line per shipped file: REPLACED, MERGED, ADDED, CONFLICT or KEPT, then the path.
    missing                                   ADDED     (written)
    same as the new version                   KEPT
    plugin-owned, recorded or released        REPLACED  (an edited copy is saved as <file>.kairyn-old)
    repo-owned, unedited                      REPLACED  (unedited: matches .base/ or a released version)
    repo-owned, edited, with a base           git merge-file: MERGED, or CONFLICT
    edited and nothing to merge from          CONFLICT  (a repo without a manifest, or no git)
On CONFLICT the local file stays as it is and the merge goes to <file>.kairyn-new. The user
takes what they want from it and deletes it; the next upgrade records the file as resolved. If the
conflict had nothing to merge from and they kept their version, the file is theirs from then on.
A recorded file the plugin no longer ships:
    missing, or unedited (matches .base/ or a released version)   REMOVED  (file, .base/ copy and entry)
    edited                                                         CONFLICT (kept; the user moves the edits
                                                                   and deletes it; the next upgrade removes it)
The manifest takes the new version only when no conflict is open. Exit 1 on any conflict.
Files kairyn does not own (learnings, tasks, the user's own docs) are never touched.

Usage: python3 upgrade.py [--root DIR] [--plugin DIR]
"""
from __future__ import annotations   # macOS ships python3 3.9

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from kairyn_files import (
    BASE, BLOCK, MANIFEST, Record, block_text, current_bytes, installed_files, plugin_version, read_manifest,
    sha256, shipped_bytes, write_record,
)

NEW, OLD = ".kairyn-new", ".kairyn-old"


def _file(repo: Path, path: str) -> Path:
    """Where a path's side files go; the block's go next to CLAUDE.md."""
    return repo / ("CLAUDE.md" if path == BLOCK else path)


def _write(repo: Path, path: str, source: Path) -> None:
    if path == BLOCK:
        new_block = block_text(source.read_text()) or source.read_text()
        claude = repo / "CLAUDE.md"
        if not claude.is_file():
            claude.write_text(new_block)
            return
        text = claude.read_text()
        old = block_text(text)
        claude.write_text(text.replace(old, new_block, 1) if old else text.rstrip("\n") + "\n\n" + new_block)
        return
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _merge(local: bytes, base: bytes, new: bytes) -> tuple[int, bytes] | None:
    """git merge-file: (conflict count, merged text), or None if git cannot run."""
    with tempfile.TemporaryDirectory(prefix="kairyn-merge-") as tmp:
        paths = []
        for name, data in (("local", local), ("base", base), ("new", new)):
            (Path(tmp) / name).write_bytes(data)
            paths.append(str(Path(tmp) / name))
        try:
            result = subprocess.run(["git", "merge-file", "-p", "-L", "yours", "-L", "base", "-L", "kairyn", *paths],
                                    capture_output=True)
        except OSError:
            return None
    return (result.returncode, result.stdout) if 0 <= result.returncode < 128 else None


def _remove_unshipped(repo: Path, manifest: dict, shipped: set, records: dict, releases: dict) -> list:
    """Recorded files this plugin no longer ships: REMOVED if missing or unedited, else CONFLICT."""
    lines = []
    for path in sorted(set(manifest["files"]) - shipped):
        old, local = records.get(path), current_bytes(repo, path)
        released = local is not None and any(sha256(local) in files.get(path, []) for files in releases.values())
        if local is None or released or (old is not None and local == old.data):
            if local is not None:
                (repo / path).unlink()
            (repo / BASE / path).unlink(missing_ok=True)
            records.pop(path, None)
            lines.append(("REMOVED", path))
        else:
            records[path] = Record(old.data if old else local, manifest["files"][path]["owner"], True)
            lines.append(("CONFLICT", path))
    return lines


def upgrade(repo: Path, plugin: Path) -> tuple[list[tuple[str, str]], bool]:
    has_manifest = (repo / MANIFEST).is_file()
    manifest = read_manifest(repo) if has_manifest else {"version": "0.0.0", "files": {}}
    releases = json.loads((plugin / "release-hashes.json").read_text())
    records = {p: Record((repo / BASE / p).read_bytes(), e["owner"], e.get("pending", False), e.get("no_base", False))
               for p, e in manifest["files"].items() if (repo / BASE / p).is_file()}
    lines, block_written = [], False

    for entry in installed_files(plugin):
        path, new = entry.path, shipped_bytes(entry)
        local, old = current_bytes(repo, path), records.get(path)
        side = _file(repo, path)
        new_side = side.with_name(side.name + NEW)

        if old and old.pending:
            if new_side.exists():
                lines.append(("CONFLICT", path))
                continue
            # The user deleted <file>.kairyn-new: resolved. With no merge base, keeping their
            # version means the file is theirs (their own doc at a kairyn path): never touch it again.
            if old.no_base and local is not None and local != new:
                del records[path]
                lines.append(("KEPT", path))
                continue
            old = Record(old.data, old.owner)
            if local is not None and old.data == new:
                records[path] = Record(new, entry.owner)
                lines.append(("KEPT", path))
                continue

        if local is None:
            _write(repo, path, entry.source)
            block_written |= path == BLOCK
            records[path], result = Record(new, entry.owner), "ADDED"
        elif has_manifest and old is None:
            lines.append(("KEPT", path))   # the user had this file before init: theirs
            continue
        elif local == new:
            records[path], result = Record(new, entry.owner), "KEPT"
        else:
            released = any(sha256(local) in files.get(path, []) for files in releases.values())
            unedited = (old is not None and local == old.data) or released
            if entry.owner == "plugin" and (has_manifest or unedited):
                if not unedited:
                    side.with_name(side.name + OLD).write_bytes(local if path != BLOCK else
                                                               (block_text(side.read_text()) or "").encode())
                _write(repo, path, entry.source)
                block_written |= path == BLOCK
                records[path], result = Record(new, entry.owner), "REPLACED"
            elif unedited:
                _write(repo, path, entry.source)
                records[path], result = Record(new, entry.owner), "REPLACED"
            else:
                merged = _merge(local, old.data, new) if old is not None else None
                if merged is not None and merged[0] == 0:
                    if merged[1] != local:
                        (repo / path).write_bytes(merged[1])
                    records[path], result = Record(new, entry.owner), "MERGED" if merged[1] != local else "KEPT"
                else:
                    if path == BLOCK:
                        conflict = (block_text(entry.source.read_text()) or "").encode()
                    else:
                        conflict = merged[1] if merged is not None else entry.source.read_bytes()
                    new_side.write_bytes(conflict)
                    records[path], result = Record(new, entry.owner, True, no_base=old is None), "CONFLICT"
        lines.append((result, path))

    lines += _remove_unshipped(repo, manifest, {e.path for e in installed_files(plugin)}, records, releases)

    if block_written and (repo / ".harness").is_dir():
        try:
            import harness_docs
            harness_docs.sync(repo)
        except (OSError, ValueError):
            pass   # no index markers to refresh
    conflicts = any(r.pending for r in records.values())
    write_record(repo, manifest["version"] if conflicts else plugin_version(plugin), records)
    return lines, conflicts


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path.cwd()
    plugin = Path(argv[argv.index("--plugin") + 1]) if "--plugin" in argv else Path(__file__).resolve().parent.parent
    if not (root / ".kairyn").is_dir():
        print("FAIL: no .kairyn/ here: run /kairyn:init first")
        return 2
    lines, conflicts = upgrade(root.resolve(), plugin.resolve())
    shipped = {e.path for e in installed_files(plugin.resolve())}
    for result, path in lines:
        print(f"{result} {path}")
    for result, path in lines:
        if result == "CONFLICT" and path not in shipped:
            print(f"{path}: kairyn no longer ships this file: move your edits into its new file, "
                  "delete it, then run /kairyn:upgrade again.")
    if any(result == "CONFLICT" and path in shipped for result, path in lines):
        print(f"Open conflicts: take what you want from each <file>{NEW}, delete it, then run /kairyn:upgrade again.")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
