#!/usr/bin/env python3
"""One atomic file write: a reader in another process never sees the file empty or partial.

    import atomic_write
    atomic_write.write_text(path, text)

It writes a temp file in the same folder, then os.replace()s it over the file. The temp file
keeps the old file's permission bits. If the write fails, the temp file is deleted, the old
file stays as it was, and the error goes to the caller.
Used by milestones.store() (.session/watch.json) and afk.py Run.update() (STATE.md).

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        if path.exists():
            os.chmod(tmp, stat.S_IMODE(path.stat().st_mode))
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
