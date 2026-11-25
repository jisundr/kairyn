"""plugin/scripts/backlog_html.py and /kairyn:backlog: a view-only page of every idea in docs/backlog/."""
import json
import re
import subprocess
import sys
from pathlib import Path

from helpers import PLUGIN

from backlog_html import PAGE_PATH, render_html

SCRIPT = PLUGIN / "scripts" / "backlog_html.py"


def idea(title="Ship the gates", status="triaged", appetite="big batch", date="2026-11-25",
         problem="The gates are repo-only.", extra="", log="- 2026-11-25T05:30:13Z [capture] Created."):
    return f"""---
title: {title}
status: {status}
requester: Jo
date: {date}
appetite: {appetite}
review_by:
---

# {title}

**Raw request:** "add it" (Jo)

**Problem (confirmed by Jo, 2026-11-25):** {problem}
Second line of the problem.

{extra}

# Log

{log}
"""


def make_repo(root: Path, ideas: dict, kairyn: bool = True, triage: str = None) -> Path:
    backlog = root / "docs" / "backlog"
    backlog.mkdir(parents=True)
    if kairyn:
        (root / ".kairyn").mkdir()
    for name, text in ideas.items():
        (backlog / name).write_text(text)
    if triage is not None:
        (backlog / "TRIAGE.md").write_text(triage)
    return root


def run(root: Path, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True)


def page_data(html: str) -> list:
    return json.loads(re.search(r"const DATA=(.*?);\n", html).group(1).replace("<\\/", "</"))


# ---------- T1: the page and the command ----------

def test_script_writes_the_page_and_prints_its_path(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-ship-gates.md": idea()})
    r = run(root)
    assert r.returncode == 0, r.stderr
    page = root / ".kairyn" / "backlog.html"
    assert page.exists() and PAGE_PATH == ".kairyn/backlog.html"
    assert r.stdout.strip() == str(page)
    assert "Ship the gates" in page.read_text()


def test_page_is_one_inline_file(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-ship-gates.md": idea(),
                                "20261122080759-other.md": idea(title="Other idea")})
    html = render_html(root)
    assert html.startswith("<!doctype html>") and html.rstrip().endswith("</html>")
    assert html.count("<style>") == 1 and html.count("<script>") == 1
    assert "<script src" not in html
    assert [d["title"] for d in page_data(html)] == ["Ship the gates", "Other idea"]


def test_command_runs_the_script_and_reports_the_path():
    text = (PLUGIN / "commands" / "backlog.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/backlog_html.py --root ." in text
    assert "model: haiku" in text and "path" in text
