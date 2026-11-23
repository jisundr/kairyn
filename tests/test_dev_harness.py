"""This repo's own dev harness in .claude/: evals run in a forked agent that can run and read, never edit."""
import re

import yaml

from helpers import ROOT, split_front_matter

SKILL = ROOT / ".claude" / "skills" / "run-evals" / "SKILL.md"
AGENT = ROOT / ".claude" / "agents" / "eval-runner.md"


def front(path):
    return yaml.safe_load(split_front_matter(path.read_text())[0])


def tool_names(value):
    items = value if isinstance(value, list) else str(value).split(",")
    return {re.sub(r"\(.*\)", "", t).strip() for t in items if t.strip()}


def test_run_evals_skill_forks_into_the_eval_runner():
    fm = front(SKILL)
    assert fm["name"] == "run-evals"
    assert fm["context"] == "fork"
    assert fm["agent"] == "eval-runner"
    assert fm.get("background", True) is True, "a foreground fork blocks the main session"


def test_eval_runner_can_run_and_read_but_not_edit():
    fm = front(AGENT)
    assert fm["name"] == "eval-runner"
    tools = tool_names(fm["tools"])
    assert {"Bash", "Read"} <= tools
    assert not tools & {"Edit", "Write", "NotebookEdit"}, tools


def test_skill_passes_arguments_to_the_fork():
    assert "$ARGUMENTS" in SKILL.read_text()


def test_eval_runner_starts_detached_and_waits_in_the_foreground():
    """A background Bash job dies with the fork when it ends early; evals/bg.py runs the evals in their own session."""
    text = AGENT.read_text()
    assert "evals/bg.py start" in text and "evals/bg.py wait" in text
    assert "run_in_background" not in text and "Monitor" not in text
    assert "Monitor" not in tool_names(front(AGENT)["tools"])
