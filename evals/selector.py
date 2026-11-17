"""Decide which evals need to run: only those whose dependencies changed.

A feature file declares what it exercises with a header comment:
    # depends: plugin/stages/REQUIREMENTS.md, plugin/scripts/*
The hash of those files is recorded when the feature last passed. If the hash
is unchanged, the (slow, costly) eval is skipped.
"""
import hashlib
import json
import re
from pathlib import Path

DEPENDS_RE = re.compile(r"^#\s*depends:\s*(.+)$", re.M)


def parse_depends(feature_text: str) -> list[str]:
    match = DEPENDS_RE.search(feature_text)
    if not match:
        return []
    return [p.strip() for p in match.group(1).split(",") if p.strip()]


def deps_hash(root: Path, patterns: list[str]) -> str:
    """Hash the content of every file matching the patterns.

    A pattern that matches nothing contributes a marker, so deleting a
    dependency changes the hash.
    """
    h = hashlib.sha256()
    for pattern in sorted(patterns):
        matches = sorted(p for p in root.glob(pattern) if p.is_file())
        if not matches:
            h.update(f"missing:{pattern}\n".encode())
        for path in matches:
            h.update(f"file:{path.relative_to(root)}\n".encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def needs_run(name: str, current_hash: str, record: dict, force: bool = False) -> bool:
    return force or record.get(name) != current_hash


def record_pass(record: dict, name: str, current_hash: str) -> dict:
    return {**record, name: current_hash}


def load_record(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
