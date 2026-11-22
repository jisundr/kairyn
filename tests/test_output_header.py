"""Front matter on stage outputs: fixed identity only, no task state."""
from checks import output_header_problems

TASK = "2026-11-22-dry-run-flag"


def doc(front: str) -> str:
    return f"---\n{front}---\n\n# Requirements\n"


GOOD = doc(f"task: {TASK}\nstage: requirements\nsummary: \"Add a --dry-run flag that prints planned file changes.\"\n")


def test_good_header_passes():
    assert output_header_problems(GOOD, TASK, "requirements") == []


def test_missing_front_matter():
    assert output_header_problems("# Requirements\n", TASK, "requirements") == ["no front matter"]


def test_wrong_task_and_stage():
    text = doc("task: 2026-01-01-other\nstage: design\nsummary: ok\n")
    problems = output_header_problems(text, TASK, "requirements")
    assert any("task" in p for p in problems) and any("stage" in p for p in problems)


def test_summary_required_and_short():
    assert any("summary" in p for p in output_header_problems(doc(f"task: {TASK}\nstage: requirements\n"), TASK, "requirements"))
    long = "x" * 161
    assert any("summary" in p for p in output_header_problems(doc(f"task: {TASK}\nstage: requirements\nsummary: {long}\n"), TASK, "requirements"))


def test_state_fields_not_allowed():
    text = doc(f"task: {TASK}\nstage: requirements\nsummary: ok\nstatus: done\n")
    assert any("status" in p for p in output_header_problems(text, TASK, "requirements"))


def test_invalid_yaml():
    assert any("invalid" in p for p in output_header_problems("---\ntask: [\n---\n", TASK, "requirements"))
