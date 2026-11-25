"""scripts/backlog_html.py: the backlog page is built from docs/backlog/*.md and TRIAGE.md."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from backlog_html import (  # noqa: E402
    load_ideas, parse_idea, render_html, render_log, render_markdown, triage_notes, write_html,
)

NOW = datetime(2026, 11, 25, 12, 0, 0, tzinfo=timezone.utc)

IDEA = """---
title: Ship the gates
status: triaged
requester: Jo
date: 2026-11-25
appetite: big batch
review_by: 2027-02-23
---

# Ship the gates

**Problem (confirmed by Jo, 2026-11-25):** The `gates` are repo-only. See [other](20261122080759-other.md).

**Notes:** Needs evals.

# Log

- 2026-11-25T05:30:13Z [capture] Created.
2026-11-25T05:38:06Z [triage] Kept.
"""

OTHER = """---
title: Other idea
status: parked
date: 2026-11-22
---

# Other idea

Body.
"""

TRIAGE = """# Triage

Intro text.

## Next

ship-gates first.

## Parked

Reviewed by 2027-02-23: other.

## Later

Not shown.
"""


def backlog(tmp_path: Path, files: dict) -> Path:
    d = tmp_path / "docs" / "backlog"
    d.mkdir(parents=True)
    for name, text in files.items():
        (d / name).write_text(text)
    return tmp_path


def page_data(html: str) -> list:
    m = re.search(r"const DATA=(.*?);\nconst ORDER", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_reads_front_matter_body_and_log(tmp_path):
    root = backlog(tmp_path, {"20261125053013-ship-gates.md": IDEA})
    idea = parse_idea(root / "docs/backlog/20261125053013-ship-gates.md")
    assert idea["slug"] == "ship-gates"
    assert (idea["title"], idea["status"], idea["appetite"]) == ("Ship the gates", "triaged", "big batch")
    assert (idea["date"], idea["review_by"], idea["requester"]) == ("2026-11-25", "2027-02-23", "Jo")
    assert idea["summary"] == "The gates are repo-only. See other."
    assert idea["body"].startswith("**Problem") and "# Log" not in idea["body"]
    assert idea["log"].startswith("- 2026-11-25T05:30:13Z")


def test_missing_fields_are_empty_and_title_falls_back_to_the_file(tmp_path):
    root = backlog(tmp_path, {"20261122080759-bare.md": "Just text.\n"})
    idea = parse_idea(root / "docs/backlog/20261122080759-bare.md")
    assert idea["title"] == "20261122080759-bare"
    assert idea["status"] == idea["log"] == idea["summary"] == ""


def test_only_idea_files_are_loaded(tmp_path):
    root = backlog(tmp_path, {"README.md": "# Backlog\n", "TRIAGE.md": TRIAGE,
                              "20261125053013-ship-gates.md": IDEA, "20261122080759-other.md": OTHER})
    assert [i["slug"] for i in load_ideas(root / "docs/backlog")] == ["other", "ship-gates"]


def test_triage_notes_keep_next_and_parked_only():
    notes = triage_notes(TRIAGE)
    assert notes.startswith("## Next") and "## Parked" in notes
    assert "Intro text" not in notes and "Later" not in notes


def test_markdown_escapes_html_and_renders_inline_marks():
    html = render_markdown("A <b>tag</b> and **bold**, `x<y`, *it* and [l](https://e.com).")
    assert "&lt;b&gt;tag&lt;/b&gt;" in html and "<b>" not in html
    assert "<strong>bold</strong>" in html and "<code>x&lt;y</code>" in html
    assert "<em>it</em>" in html and '<a href="https://e.com">l</a>' in html


def test_markdown_lists_quotes_headings_and_tables():
    html = render_markdown("## Next\n\n- one\n- two\n\n1. a\n2. b\n\n> quoted\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
    assert "<h4>Next</h4>" in html
    assert "<ul><li>one</li><li>two</li></ul>" in html and "<ol><li>a</li><li>b</li></ol>" in html
    assert "<blockquote><p>quoted</p></blockquote>" in html
    assert "<th>A</th>" in html and "<td>2</td>" in html


def test_links_between_ideas_open_the_linked_idea():
    html = render_markdown("See [other](20261122080759-other.md).", {"20261122080759-other.md": "#other"})
    assert '<a href="#other">other</a>' in html


def test_unsafe_link_targets_are_dropped():
    assert 'href="#"' in render_markdown("[x](javascript:alert(1))")


def test_log_lines_without_a_dash_are_list_items():
    html = render_log("- 2026-11-25T05:30:13Z one\n2026-11-25T05:38:06Z two", {})
    assert html.count("<li>") == 2


def test_page_embeds_every_idea_and_the_triage_notes(tmp_path):
    root = backlog(tmp_path, {"TRIAGE.md": TRIAGE, "20261125053013-ship-gates.md": IDEA,
                              "20261122080759-other.md": OTHER})
    html = render_html(root, NOW, commit="abc1234")
    assert html.startswith("<!doctype html>") and "</html>" in html
    assert "abc1234" in html and "2026-11-25 12:00 UTC" in html
    assert "ship-gates first." in html and "Not shown." not in html
    data = page_data(html)
    assert [d["slug"] for d in data] == ["other", "ship-gates"]
    assert '<a href="#other">other</a>' in data[1]["body_html"]
    assert data[1]["log_html"].count("<li>") == 2


def test_page_filters_by_status_appetite_and_text_and_supports_themes(tmp_path):
    root = backlog(tmp_path, {"20261125053013-ship-gates.md": IDEA})
    html = render_html(root, NOW, commit="")
    order = json.loads(re.search(r"const ORDER=(.*?);", html).group(1))
    assert order[:7] == ["committed", "shaped", "shaping", "triaged", "inbox", "parked", "dropped"]
    assert '<option value="big batch">' in html and 'id="q"' in html
    assert "prefers-color-scheme: dark" in html and 'data-theme="dark"' in html
    assert 'name="viewport"' in html


def test_unknown_status_still_gets_a_group(tmp_path):
    root = backlog(tmp_path, {"20261125053013-odd.md": IDEA.replace("status: triaged", "status: someday")})
    order = json.loads(re.search(r"const ORDER=(.*?);", render_html(root, NOW, commit="")).group(1))
    assert order[-1] == "someday"


def test_script_close_tags_in_ideas_cannot_end_the_script(tmp_path):
    root = backlog(tmp_path, {"20261125053013-x.md": IDEA.replace("Needs evals.", "</script><script>alert(1)")})
    html = render_html(root, NOW, commit="")
    script = html[html.index("<script>"):]
    assert script.count("</script>") == 1


def test_write_html_creates_the_file(tmp_path):
    root = backlog(tmp_path, {"20261125053013-ship-gates.md": IDEA})
    out = tmp_path / "out" / "page.html"
    write_html(root, out, NOW)
    assert "Ship the gates" in out.read_text()


def test_cli_builds_this_repos_backlog(tmp_path):
    out = tmp_path / "backlog.html"
    r = subprocess.run([sys.executable, str(ROOT / "scripts/backlog_html.py"), "--root", str(ROOT), "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    ideas = sorted(p.name for p in (ROOT / "docs/backlog").glob("[0-9]*.md"))
    assert [d["file"] for d in page_data(out.read_text())] == ideas


def test_default_page_is_git_ignored():
    r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "docs/backlog/backlog.html"])
    assert r.returncode == 0
