#!/usr/bin/env python3
"""Build plugin/release-hashes.json: {version: {repo path: [sha256, ...]}}.

For each version it records the hash of every installed file in every commit whose
plugin.json had that version, plus the working tree under the current version. A version
can span several commits (0.1.0 changed in #5 to #7 without a bump), so all of them count.
Upgrade uses the file to recognize unedited files in repos that have no manifest.

Needs the full git history (not a shallow clone).

Usage (from the repo root):
    python scripts/release_hashes.py           # print the JSON
    python scripts/release_hashes.py --write   # write plugin/release-hashes.json
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "scripts"))
from kairyn_files import BLOCK, block_text, comparable_block, sha256  # noqa: E402

OUT = "plugin/release-hashes.json"
SHIPPED = ("plugin/stages", "plugin/templates", "plugin/harness")
PLUGIN_JSON = "plugin/.claude-plugin/plugin.json"


def repo_path(source: str) -> str | None:
    """Where init installs a shipped plugin file, or None if init does not install it."""
    for prefix, dest in (("plugin/stages/", ".kairyn/stages/"), ("plugin/templates/", ".kairyn/templates/"),
                         ("plugin/harness/.harness/", ".harness/")):
        if source.startswith(prefix):
            return dest + source[len(prefix):]
    return BLOCK if source == "plugin/harness/CLAUDE.block.md" else None


def _hash(path: str, data: bytes) -> str:
    if path == BLOCK:
        block = block_text(data.decode())
        data = comparable_block(block if block is not None else data.decode()).encode()
    return sha256(data)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def collect(root: Path) -> dict:
    found = defaultdict(lambda: defaultdict(set))
    for commit in _git(root, "rev-list", "HEAD", "--", "plugin").decode().split():
        try:
            version = json.loads(_git(root, "show", f"{commit}:{PLUGIN_JSON}"))["version"]
        except subprocess.CalledProcessError:
            continue   # before plugin.json existed
        for source in _git(root, "ls-tree", "-r", "--name-only", commit, "--", *SHIPPED).decode().splitlines():
            path = repo_path(source)
            if path:
                found[version][path].add(_hash(path, _git(root, "show", f"{commit}:{source}")))
    version = json.loads((root / PLUGIN_JSON).read_text())["version"]
    for top in SHIPPED:
        for file in sorted(p for p in (root / top).rglob("*") if p.is_file()):
            path = repo_path(file.relative_to(root).as_posix())
            if path:
                found[version][path].add(_hash(path, file.read_bytes()))
    return {v: {p: sorted(h) for p, h in sorted(files.items())} for v, files in sorted(found.items())}


def main(argv: list[str]) -> int:
    text = json.dumps(collect(ROOT), indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        (ROOT / OUT).write_text(text)
        print(f"wrote {OUT}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
