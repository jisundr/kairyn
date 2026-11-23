"""Checks on the files under .github/ that outsiders and GitHub read."""
import re

import pytest

from helpers import ROOT

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?P<rest>.*)$")
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"^\s+#\s*v\d+(\.\d+)*\s*$")


def unpinned(text):
    """Return each `uses:` line that has no 40-character SHA or no version comment."""
    bad = []
    for line in text.splitlines():
        m = USES.match(line)
        if not m:
            continue
        ref = m.group("ref")
        if ref.startswith("./"):
            continue
        if not PINNED.match(ref) or not VERSION_COMMENT.match(m.group("rest")):
            bad.append(line.strip())
    return bad


SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.mark.parametrize("line", [
    "      - uses: actions/checkout@v7",
    f"      - uses: actions/checkout@{SHA}",
    f"      - uses: actions/checkout@{SHA[:7]} # v7",
    "      - uses: actions/checkout@main # v7",
    f"        uses: actions/checkout@{SHA} # latest",
])
def test_unpinned_flags_bad_lines(line):
    assert unpinned(line) == [line.strip()]


@pytest.mark.parametrize("line", [
    f"      - uses: actions/checkout@{SHA} # v7",
    f"        uses: astral-sh/setup-uv@{SHA} # v10.3.3",
    "      - uses: ./.github/actions/local",
])
def test_unpinned_accepts_good_lines(line):
    assert unpinned(line) == []


def test_workflows_exist():
    assert WORKFLOWS


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_actions_pinned_by_sha(workflow):
    assert unpinned(workflow.read_text()) == []


DEPENDABOT = ROOT / ".github" / "dependabot.yml"


@pytest.mark.parametrize("ecosystem", ["github-actions", "uv"])
def test_dependabot_weekly_version_updates(ecosystem):
    import yaml

    config = yaml.safe_load(DEPENDABOT.read_text())
    assert config["version"] == 2
    entries = [u for u in config["updates"] if u["package-ecosystem"] == ecosystem]
    assert len(entries) == 1
    assert entries[0]["directory"] == "/"
    assert entries[0]["schedule"]["interval"] == "weekly"


# --- outsider files (R9 to R13, R15) -----------------------------------------

SECURITY = ROOT / "SECURITY.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
PR_TEMPLATE = ROOT / ".github" / "pull_request_template.md"
BUG_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
ISSUE_CONFIG = ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"
REPO_URL = "https://github.com/jisundr/kairyn"


def test_security_md_points_to_private_reporting():
    text = SECURITY.read_text()
    assert f"{REPO_URL}/security/advisories/new" in text
    assert "public issue" in text.lower()
    assert "latest" in text.lower()


def test_bug_report_form_asks_for_the_five_fields():
    import yaml

    form = yaml.safe_load(BUG_FORM.read_text())
    assert form["name"] and form["description"]
    ids = {item.get("id") for item in form["body"] if item["type"] != "markdown"}
    assert {"kairyn-version", "claude-code-version", "os", "steps", "output"} <= ids
    for item in form["body"]:
        if item.get("id") in ids:
            assert item["validations"]["required"] is True


def test_issue_chooser_has_no_blank_issues():
    import yaml

    assert yaml.safe_load(ISSUE_CONFIG.read_text())["blank_issues_enabled"] is False


def test_contributing_md_states_the_three_rules():
    text = CONTRIBUTING.read_text()
    lower = text.lower()
    assert "open an issue" in lower and "before" in lower
    assert "uv run pytest" in text
    assert "maintainer" in lower and "evals" in lower


def test_pull_request_template_has_the_checklist():
    items = [line for line in PR_TEMPLATE.read_text().splitlines() if line.startswith("- [ ]")]
    assert len(items) == 3
    text = "\n".join(items)
    assert "uv run pytest" in text
    assert "issue" in text.lower()
    assert "plugin/" in text and "version" in text.lower()


@pytest.mark.parametrize("path", [SECURITY, CONTRIBUTING, PR_TEMPLATE], ids=lambda p: p.name)
def test_new_markdown_has_its_own_budget(path):
    from budgets import load_budgets

    rel = path.relative_to(ROOT).as_posix()
    patterns = [b.pattern for b in load_budgets(ROOT / ".harness" / "budgets.yml")]
    assert rel in patterns
