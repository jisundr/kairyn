"""Stage skills: one per built-in stage, each names its model and defers to the repo's stage file."""
import re

import pytest
import yaml

from helpers import PLUGIN, split_front_matter

STAGE_SKILLS = {"requirements": "REQUIREMENTS", "grill": "GRILL", "model-routing": "MODEL-ROUTING"}
MODELS = {"haiku", "sonnet", "opus", "inherit"}
SCRIPT_COMMANDS = ("init", "check", "upgrade")


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
