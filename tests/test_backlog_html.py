"""plugin/scripts/backlog_html.py and /kairyn:backlog: a view-only page of every idea in docs/backlog/."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

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


# ---------- T2: fields, detail view, markdown ----------

def test_lists_each_idea_with_its_fields(tmp_path):
    root = make_repo(tmp_path, {
        "20261125053013-a.md": idea(title="Idea A", appetite="big batch", date="2026-11-25", problem="Problem A."),
        "20261124053013-b.md": idea(title="Idea B", appetite="small batch", date="2026-11-24", problem="Problem `B`."),
        "20261123053013-c.md": idea(title="Idea C", appetite="", date="2026-11-23", problem="See [A](20261125053013-a.md)."),
    })
    data = page_data(render_html(root))
    rows = [(d["title"], d["appetite"], d["date"], d["problem"]) for d in data]
    assert rows == [("Idea A", "big batch", "2026-11-25", "Problem A."),
                    ("Idea B", "small batch", "2026-11-24", "Problem B."),
                    ("Idea C", "", "2026-11-23", "See A.")]


def test_detail_view_has_front_matter_text_and_log(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-ship-gates.md": idea(
        extra="**Notes:** Needs evals.", log="- 2026-11-25T05:30:13Z [capture] Created.\n2026-11-25T05:38:06Z [triage] Kept.")})
    d = page_data(render_html(root))[0]
    assert (d["requester"], d["review_by"], d["file"]) == ("Jo", "", "20261125053013-ship-gates.md")
    assert "<strong>Notes:</strong> Needs evals." in d["body_html"]
    assert "# Log" not in d["body_html"] and "Created." not in d["body_html"]
    assert d["log_html"].count("<li>") == 2


def test_links_between_ideas_open_the_linked_idea(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(extra="See [B](20261124053013-b.md)."),
                                "20261124053013-b.md": idea(title="B")})
    assert '<a href="#b">B</a>' in page_data(render_html(root))[0]["body_html"]


def test_markdown_blocks_render():
    from backlog_html import render_markdown
    html = render_markdown("## Next\n\n- one\n- two\n\n1. a\n2. b\n\n> quoted\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n*it* `x<y`")
    assert "<h4>Next</h4>" in html
    assert "<ul><li>one</li><li>two</li></ul>" in html and "<ol><li>a</li><li>b</li></ol>" in html
    assert "<blockquote><p>quoted</p></blockquote>" in html
    assert "<th>A</th>" in html and "<td>2</td>" in html
    assert "<em>it</em>" in html and "<code>x&lt;y</code>" in html


def test_idea_text_cannot_run_script(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-x.md": idea(
        extra="A <b>x</b> and [bad](javascript:alert(1)) and [ok](https://e.com).\n\n</script><script>alert(1)</script>")})
    html = render_html(root)
    d = page_data(html)[0]
    assert "&lt;b&gt;x&lt;/b&gt;" in d["body_html"] and "<b>x</b>" not in d["body_html"]
    assert "javascript:" not in d["body_html"] and '<a href="#">bad</a>' in d["body_html"]
    assert '<a href="https://e.com">ok</a>' in d["body_html"]
    assert html[html.index("<script>"):].count("</script>") == 1


# ---------- T3: the page's controls, notes, themes; no status, no network ----------

TRIAGE = """# Triage

Intro text.

## Next

ship-gates first.

## Parked

Reviewed by 2027-02-23: other.

## Later

Not shown.
"""
STATUSES = ["committed", "shaped", "shaping", "triaged", "inbox", "parked", "dropped"]


def test_page_loads_nothing_from_the_network(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea()}, triage=TRIAGE)
    html = render_html(root).lower()
    for marker in ("<link", "src=", "@import", "url(", "fonts.googleapis", "http://", "https://"):
        assert marker not in html, marker


def test_page_shows_no_status(tmp_path):
    ideas = {f"2026112505301{n}-s{n}.md": idea(title=f"Idea {n}", status=s) for n, s in enumerate(STATUSES)}
    html = render_html(make_repo(tmp_path, ideas)).lower()
    for word in STATUSES + ["status"]:
        assert word not in html, word


def test_triage_notes_keep_next_and_parked_only(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}, triage=TRIAGE))
    details = re.search(r"<details.*?</details>", html, re.S).group(0)
    assert "ship-gates first." in details and "Reviewed by 2027-02-23: other." in details
    assert "<details open" not in html
    assert "Intro text" not in html and "Not shown." not in html


def test_no_triage_file_means_no_notes(tmp_path):
    assert "<details" not in render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}))


def test_page_has_search_and_an_appetite_filter(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(appetite="big batch"),
                                "20261124053013-b.md": idea(appetite="small batch"),
                                "20261123053013-c.md": idea(appetite="")})
    html = render_html(root)
    assert re.search(r'<input id="q" type="search"', html)
    options = re.findall(r'<option value="([^"]*)">([^<]*)</option>', html)
    assert options == [("", "Any appetite"), ("big batch", "Big batch"), ("small batch", "Small batch"), ("none", "Not set")]


def test_page_has_no_edit_controls(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}, triage=TRIAGE))
    assert len(re.findall(r"<input\b", html)) == 1 and len(re.findall(r"<select\b", html)) == 1
    assert set(re.findall(r'<button class="(\w+)"', html)) == {"row", "close"}
    assert len(re.findall(r"<button\b", html)) == 2
    for marker in ("<textarea", "<form", "contenteditable", "localstorage", "fetch("):
        assert marker not in html.lower(), marker


def test_page_follows_the_system_theme_and_fits_a_phone(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}))
    assert "@media (prefers-color-scheme: dark)" in html
    assert 'name="viewport" content="width=device-width' in html
    assert "@media (max-width:560px)" in html


def test_relative_links_resolve_from_the_page_in_kairyn(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(extra="[Task](../tasks/2026-11-25-x/) and [T](TRIAGE.md#next).")})
    body = page_data(render_html(root))[0]["body_html"]
    assert '<a href="../docs/backlog/../tasks/2026-11-25-x/">Task</a>' in body
    assert '<a href="../docs/backlog/TRIAGE.md#next">T</a>' in body


# ---------- T4: .gitignore and the error exits ----------

@pytest.mark.parametrize("before", [None, "node_modules/\n", "node_modules/", "node_modules/\n.kairyn/backlog.html\n"])
def test_gitignore_gets_one_line(tmp_path, before):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea()})
    if before is not None:
        (root / ".gitignore").write_text(before)
    for _ in range(2):
        assert run(root).returncode == 0
    lines = (root / ".gitignore").read_text().splitlines()
    assert lines.count(".kairyn/backlog.html") == 1
    if before:
        assert lines[0] == "node_modules/"


def test_no_ideas_writes_nothing(tmp_path):
    root = make_repo(tmp_path, {"README.md": "# Backlog\n"}, triage="# Triage\n")
    r = run(root)
    assert r.returncode == 1 and len((r.stdout + r.stderr).strip().splitlines()) == 1
    assert "docs/backlog" in r.stdout + r.stderr
    assert not (root / ".kairyn" / "backlog.html").exists() and not (root / ".gitignore").exists()


def test_no_backlog_folder_writes_nothing(tmp_path):
    (tmp_path / ".kairyn").mkdir()
    r = run(tmp_path)
    assert r.returncode == 1 and not (tmp_path / ".kairyn" / "backlog.html").exists()


def test_no_kairyn_folder_writes_nothing(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea()}, kairyn=False)
    r = run(root)
    assert r.returncode == 1 and len((r.stdout + r.stderr).strip().splitlines()) == 1
    assert "/kairyn:init" in r.stdout + r.stderr
    assert not (root / ".kairyn").exists() and not (root / ".gitignore").exists()
