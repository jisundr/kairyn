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
