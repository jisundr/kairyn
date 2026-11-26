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


def idea(title="Ship the gates", status="triaged", effort="medium", impact="high", date="2026-11-25",
         problem="The gates are repo-only.", extra="", log="- 2026-11-25T05:30:13Z [capture] Created."):
    return f"""---
title: {title}
status: {status}
requester: Jo
date: {date}
effort: {effort}
impact: {impact}
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
        "20261125053013-a.md": idea(title="Idea A", effort="low", impact="high", date="2026-11-25", problem="Problem A."),
        "20261124053013-b.md": idea(title="Idea B", effort="High", impact="medium", date="2026-11-24", problem="Problem `B`."),
        "20261123053013-c.md": idea(title="Idea C", effort="", impact="", date="2026-11-23", problem="See [A](20261125053013-a.md)."),
    })
    data = page_data(render_html(root))
    rows = [(d["title"], d["effort"], d["effort_level"], d["impact"], d["impact_level"], d["date"], d["problem"]) for d in data]
    assert rows == [("Idea A", "low", "low", "high", "high", "2026-11-25", "Problem A."),
                    ("Idea B", "High", "high", "medium", "medium", "2026-11-24", "Problem B."),
                    ("Idea C", "", "", "", "", "2026-11-23", "See A.")]
    assert all("appetite" not in d for d in data)


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


def test_page_has_search_and_effort_and_impact_filters(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(effort="big batch", impact="")})
    html = render_html(root)
    assert re.search(r'<input id="q" type="search"', html)
    selects = re.findall(r'<select id="(\w+)" aria-label="([^"]+)">(.*?)</select>', html)
    assert [(i, label) for i, label, _ in selects] == [("imp", "Impact"), ("eff", "Effort")]
    for (_, label, body) in selects:
        assert re.findall(r'<option value="([^"]*)">([^<]*)</option>', body) == [
            ("", "Any " + label.lower()), ("low", "Low"), ("medium", "Medium"), ("high", "High"), ("none", "Not set")]
    assert "appetite" not in html.lower()


def test_page_has_no_edit_controls(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}, triage=TRIAGE))
    assert len(re.findall(r"<input\b", html)) == 1 and len(re.findall(r"<select\b", html)) == 2
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


# ---------- T4: .gitignore, and nothing to build ----------

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


# ---------- T5: the eval and the docs ----------

def _asserts():
    import importlib.util
    from helpers import ROOT
    spec = importlib.util.spec_from_file_location("kairyn_asserts", ROOT / "evals" / "promptfoo" / "asserts.py")
    asserts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asserts)
    return asserts


@pytest.mark.parametrize("evidence, ok", [
    ({"reply": "Built: .kairyn/backlog.html", "page_exists": True, "ignored": True}, True),
    ({"reply": "Done.", "page_exists": True, "ignored": True}, False),
    ({"reply": ".kairyn/backlog.html", "page_exists": False, "ignored": True}, False),
    ({"reply": ".kairyn/backlog.html", "page_exists": True, "ignored": False}, False),
])
def test_backlog_eval_assert(evidence, ok):
    assert _asserts().backlog_page_built(json.dumps(evidence), {})["pass"] is ok


def test_backlog_eval_runs_the_command_and_depends_on_its_files():
    from helpers import ROOT
    config = (ROOT / "evals" / "promptfoo" / "backlog.yaml").read_text()
    assert config.startswith("# depends: plugin/commands/backlog.md, plugin/scripts/backlog_html.py")
    assert "scenario: backlog_page" in config and "asserts.py:backlog_page_built" in config


def test_readme_names_the_command():
    from helpers import ROOT
    assert "/kairyn:backlog" in (ROOT / "README.md").read_text()


# ---------- T6: readability (owner's pick, 2026-11-25) ----------

ODD = "Big (proposed by the steward; owner to confirm)"


def test_problem_line_is_the_first_sentence(tmp_path):
    root = make_repo(tmp_path, {
        "20261125053013-a.md": idea(title="A", problem="Version 1.2 is out. Then more text follows here."),
        "20261124053013-b.md": idea(title="B", problem="No full stop at all"),
    })
    assert [d["problem"] for d in page_data(render_html(root))] == ["Version 1.2 is out.", "No full stop at all"]


@pytest.mark.parametrize("value, level", [
    ("low", "low"), ("Medium", "medium"), ("HIGH", "high"), ("high (owner to confirm)", "high"),
    ("", ""), ("big batch", ""), (ODD, ""), ("lowest", ""),
])
def test_effort_and_impact_get_a_level_and_keep_the_raw_value(tmp_path, value, level):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(effort=value, impact=value)})
    d = page_data(render_html(root))[0]
    assert (d["effort"], d["effort_level"], d["impact"], d["impact_level"]) == (value, level, value, level)


@pytest.mark.parametrize("value, label", [("2026-11-25", "Nov 25"), ("2026-01-03", "Jan 3"), ("", "—"), ("soon", "soon")])
def test_dates_show_as_month_and_day(tmp_path, value, label):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(date=value)})
    assert page_data(render_html(root))[0]["date_label"] == label


def test_detail_view_leads_with_the_problem(tmp_path):
    root = make_repo(tmp_path, {"20261125053013-a.md": idea(problem="The `gates` are repo-only.", extra="**Notes:** n.")})
    d = page_data(render_html(root))[0]
    assert d["problem_html"].startswith("<strong>Problem (confirmed by Jo, 2026-11-25):</strong> The <code>gates</code>")
    assert "Problem (confirmed" not in d["body_html"]
    assert "<strong>Raw request:</strong>" in d["body_html"] and "<strong>Notes:</strong> n." in d["body_html"]


def test_no_problem_means_no_lead(tmp_path):
    text = idea().replace("**Problem (confirmed by Jo, 2026-11-25):** The gates are repo-only.\nSecond line of the problem.\n", "**Learning:** x\n")
    d = page_data(render_html(make_repo(tmp_path, {"20261125053013-a.md": text})))[0]
    assert d["problem"] == "" and d["problem_html"] == ""
    assert "<strong>Learning:</strong> x" in d["body_html"]


def test_log_is_a_timeline_of_time_tag_and_text(tmp_path):
    log = ("- 2026-11-25T05:30:13Z [capture] Created <b>now</b>.\n"
           "2026-11-25T10:18:25Z [slice] Slice 2: `afk.py`\n  runs it.\n"
           "A line with no time.")
    d = page_data(render_html(make_repo(tmp_path, {"20261125053013-a.md": idea(log=log)})))[0]
    items = re.findall(r"<li>(.*?)</li>", d["log_html"])
    assert d["log_html"].startswith('<ol class="tl">') and len(items) == 3
    assert '<time datetime="2026-11-25T05:30:13Z">Nov 25 05:30</time>' in items[0]
    assert '<span class="tag">capture</span> Created &lt;b&gt;now&lt;/b&gt;.' in items[0]
    assert '<span class="tag">slice</span> Slice 2: <code>afk.py</code> runs it.' in items[1]
    assert "<time></time>" in items[2] and "A line with no time." in items[2]


def test_page_has_search_feedback_and_a_compact_list(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}))
    assert 'id="count"' in html and "<mark>" in html and 'e.key==="/"' in html
    assert "No problem statement" in html
    assert 'class="list"' in html and "text-overflow:ellipsis" in html


# ---------- T6: measured in a real browser ----------

def _chrome():
    import os
    import shutil
    for name in (os.environ.get("CHROME", ""), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if name and shutil.which(name):
            return shutil.which(name)
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if Path(mac).exists() else None


def in_browser(tmp_path, page: str, width: int, js: str) -> dict:
    """Load page in a width-px iframe (headless windows have a minimum width), run js with d and w, return its JSON."""
    import html as html_mod
    chrome = _chrome()
    if not chrome:
        pytest.skip("no Chrome or Chromium on this machine")
    outer = (f'<!doctype html><body><iframe id="f" style="width:{width}px;height:900px;border:0" '
             f'srcdoc="{html_mod.escape(page, quote=True)}"></iframe><script>f.onload=()=>setTimeout(()=>{{'
             f'const d=f.contentDocument,w=f.contentWindow;const o=document.createElement("output");o.id="r";'
             f'o.textContent=JSON.stringify((()=>{{{js}}})());document.body.append(o)}},100)</script></body>')
    probe = tmp_path / "probe.html"
    probe.write_text(outer)
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--window-size=1400,1000",
                        "--virtual-time-budget=3000", "--dump-dom", probe.as_uri()],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r'<output id="r">(.*?)</output>', r.stdout, re.S)
    assert m, r.stderr[-500:]
    return json.loads(html_mod.unescape(m.group(1)))


def browser_repo(tmp_path):
    return make_repo(tmp_path / "repo", {
        "20261125053013-a.md": idea(title="An idea with a fairly long title that wraps on a phone", effort=ODD,
                                    problem="A long problem sentence " + "that goes on and on " * 12 + "."),
        "20261124053013-b.md": idea(title="Second", effort="low", impact="medium", extra="Unbroken: " + "x" * 120),
        "20261123053013-c.md": idea(title="Third", effort="", impact="").replace("**Problem (confirmed by Jo, 2026-11-25):**", "**Learning:**"),
    })


@pytest.mark.parametrize("width", [360, 390])
def test_phone_width_has_no_sideways_scroll(tmp_path, width):
    page = render_html(browser_repo(tmp_path))
    js = ("const list=d.documentElement.scrollWidth;w.openPane('a');const a=d.getElementById('pane').scrollWidth;"
          "w.openPane('b');return {list, a, b:d.getElementById('pane').scrollWidth, iw:w.innerWidth}")
    got = in_browser(tmp_path, page, width, js)
    assert got["iw"] == width
    assert got["list"] <= width and got["a"] <= width and got["b"] <= width, got


def test_desktop_rows_are_one_line_summaries_with_aligned_dates(tmp_path):
    page = render_html(browser_repo(tmp_path))
    js = ("const s=[...d.querySelectorAll('.row .s')].map(e=>e.getBoundingClientRect().height);"
          "const lh=parseFloat(w.getComputedStyle(d.querySelector('.row .s')).lineHeight);"
          "const x=[...d.querySelectorAll('.row .date')].map(e=>Math.round(e.getBoundingClientRect().right));"
          "const tip=d.querySelector('.row .lv.effort').title;"
          "const none=d.querySelectorAll('.row')[2].querySelector('.s').textContent;"
          "return {s, lh, x, tip, none, sw:d.documentElement.scrollWidth}")
    got = in_browser(tmp_path, page, 1280, js)
    assert all(h <= got["lh"] * 1.2 for h in got["s"]), got
    assert len(set(got["x"])) == 1, got
    assert got["tip"] == "Effort: " + ODD and got["none"] == "No problem statement" and got["sw"] <= 1280


def test_search_shows_a_count_and_highlights_matches(tmp_path):
    page = render_html(browser_repo(tmp_path))
    js = ("d.dispatchEvent(new w.KeyboardEvent('keydown',{key:'/'}));const focused=d.activeElement.id;"
          "const q=d.getElementById('q');q.value='third';q.dispatchEvent(new w.Event('input'));"
          "return {focused, count:d.getElementById('count').textContent, rows:d.querySelectorAll('.row').length,"
          "mark:d.querySelector('.row mark')&&d.querySelector('.row mark').textContent}")
    got = in_browser(tmp_path, page, 1280, js)
    assert got == {"focused": "q", "count": "1 of 3", "rows": 1, "mark": "Third"}, got


# ---------- effort and impact (2026-11-26-effort-and-impact) ----------

def test_rows_and_pane_show_effort_and_impact(tmp_path):
    page = render_html(browser_repo(tmp_path))
    js = ("const rows=[...d.querySelectorAll('.row')].map(r=>[...r.querySelectorAll('.lv')].map(e=>e.textContent));"
          "w.openPane('a');const facts=d.querySelector('#pane .facts').textContent;"
          "return {rows, facts}")
    got = in_browser(tmp_path, page, 1280, js)
    assert got["rows"] == [["Impact High", "Effort Not set"], ["Impact Medium", "Effort Low"],
                           ["Impact Not set", "Effort Not set"]], got
    assert "Impact high" in got["facts"] and "Effort " + ODD in got["facts"], got


def test_filters_pick_ideas_by_level(tmp_path):
    page = render_html(browser_repo(tmp_path))
    js = ("const pick=(id,v)=>{const s=d.getElementById(id);s.value=v;s.dispatchEvent(new w.Event('change'))};"
          "const titles=()=>[...d.querySelectorAll('.row .t')].map(e=>e.textContent);"
          "pick('imp','medium');const medium=titles();pick('imp','');pick('eff','none');const unset=titles();"
          "pick('imp','high');const both=titles();pick('imp','low');"
          "return {medium, unset, both, empty:d.querySelector('.empty').textContent}")
    got = in_browser(tmp_path, page, 1280, js)
    assert got["medium"] == ["Second"], got
    assert got["unset"] == ["An idea with a fairly long title that wraps on a phone", "Third"], got
    assert got["both"] == ["An idea with a fairly long title that wraps on a phone"], got
    assert "filters" in got["empty"] and "appetite" not in got["empty"], got


def test_ideas_sort_by_impact_then_effort_then_newest(tmp_path):
    spec = [  # file time, impact, effort
        ("20261120000000", "high", "high"), ("20261121000000", "low", "low"), ("20261122000000", "", "low"),
        ("20261123000000", "high", "low"), ("20261124000000", "medium", ""), ("20261125000000", "medium", "medium"),
        ("20261126000000", "High", "Low"), ("20261127000000", "big", "medium"), ("20261128000000", "medium", "medium"),
    ]
    ideas = {f"{t}-i{n}.md": idea(title=f"I{n}", impact=i, effort=e) for n, (t, i, e) in enumerate(spec)}
    data = page_data(render_html(make_repo(tmp_path, ideas)))
    assert [d["title"] for d in data] == ["I6", "I3", "I0", "I8", "I5", "I4", "I1", "I2", "I7"]


def test_header_names_the_order(tmp_path):
    html = render_html(make_repo(tmp_path, {"20261125053013-a.md": idea()}))
    assert "by impact (high first), then effort (low first), then newest" in html
    assert "newest first." not in html
