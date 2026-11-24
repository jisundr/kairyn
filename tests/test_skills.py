"""Stage skills: one per built-in stage, each names its model and defers to the repo's stage file."""
import re

import pytest
import yaml

from helpers import PLUGIN, split_front_matter

STAGE_SKILLS = {"requirements": "REQUIREMENTS", "design": "DESIGN", "grill": "GRILL", "model-routing": "MODEL-ROUTING", "close": "CLOSE",
                "retro": "RETRO"}
MODELS = {"haiku", "sonnet", "opus", "inherit"}
SCRIPT_COMMANDS = ("init", "check", "upgrade", "release")


def skill(name):
    return PLUGIN / "skills" / name / "SKILL.md"


def front(path):
    fm, body = split_front_matter(path.read_text())
    return yaml.safe_load(fm), body


def stage_steps(stage):
    """The numbered lines under a stage's ## Steps heading."""
    text = (PLUGIN / "stages" / f"{stage}.md").read_text()
    section = text.split("## Steps", 1)[1].split("\n## ", 1)[0]
    return [line.strip() for line in section.splitlines() if re.match(r"\s*\d+\.", line)]


def test_each_built_in_stage_has_a_skill():
    assert {p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md")} >= set(STAGE_SKILLS)


@pytest.mark.parametrize("name", STAGE_SKILLS)
def test_skill_front_matter_names_a_model(name):
    data, _ = front(skill(name))
    assert data["name"] == name
    assert data["model"] in MODELS
    assert "Use when" in data["description"], "description must say when, not only what"


@pytest.mark.parametrize("name,stage", STAGE_SKILLS.items())
def test_skill_defers_to_the_repo_stage_file(name, stage):
    _, body = front(skill(name))
    assert f".kairyn/stages/{stage}.md" in body
    assert "/kairyn:upgrade" in body, "a missing stage file must point at /kairyn:upgrade"
    copied = [step for step in stage_steps(stage) if step in body]
    assert not copied, f"skill copies stage steps: {copied}"


def test_grill_is_a_skill_not_a_command():
    """Same name as a command and a skill would register /kairyn:grill twice."""
    assert not (PLUGIN / "commands" / "grill.md").exists()


@pytest.mark.parametrize("name", SCRIPT_COMMANDS)
def test_script_only_commands_name_a_model(name):
    data, _ = front(PLUGIN / "commands" / f"{name}.md")
    assert data.get("model") in MODELS


def test_design_skill_runs_on_opus():
    """D6: design needs the most judgment; Sonnet only after a 10-run eval pass."""
    assert front(skill("design"))[0]["model"] == "opus"


def test_retro_is_optional_and_runs_its_script():
    """D1, D6: an optional stage like close; its size checks run in retro.py, so the skill may call python3."""
    stage, _ = front(PLUGIN / "stages" / "RETRO.md")
    assert stage["optional"] is True
    data, body = front(skill("retro"))
    assert "Bash(python3:*)" in data["allowed-tools"]
    assert "scripts/retro.py" in body


def test_close_skill_can_run_retro():
    """Option A: close follows RETRO.md in the same turn, so it names the retro script too."""
    assert "scripts/retro.py" in front(skill("close"))[1]


def test_close_skill_runs_the_close_script():
    assert "scripts/close.py" in front(skill("close"))[1]


@pytest.mark.parametrize("path", ["skills/exit", "stages/EXIT.md", "scripts/exit.py"])
def test_no_exit_name_is_shipped(path):
    """R1-R3: a bare /exit is the Claude Code built-in, so the stage is close."""
    assert not (PLUGIN / path).exists()


@pytest.mark.parametrize("name,command", [("build", "run"), ("review", "approve")])
def test_afk_skills_run_the_script(name, command):
    """D7, D11: the script runs the loop and records the decision; the skill only calls it."""
    data, body = front(skill(name))
    assert data["name"] == name and data["model"] in MODELS and "Use when" in data["description"]
    assert "Bash(python3:*)" in data["allowed-tools"]
    assert f"scripts/afk.py {command}" in body
    assert "/kairyn:upgrade" in body


def test_build_skill_approves_a_slice():
    """D10: `/kairyn:build <task> approve T<n>` records the approval, then resumes."""
    assert "afk.py approve <task> --slice T<n>" in front(skill("build"))[1]
