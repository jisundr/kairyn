"""Pure checks for the model-routing stage output (evals/checks.py)."""
from datetime import datetime, timedelta, timezone

from checks import TS_FORMAT, next_routing_stage, open_decisions, routing_problems

TASK = "2026-11-22-cut-reply-cost"
NOW = datetime.now(timezone.utc).replace(microsecond=0)

GOOD_DOC = f"""---
task: {TASK}
stage: model-routing
summary: "Plan stage 0 logging for the support-reply feature."
---

# Model routing

## Call sites
| File | Model | Purpose |
|---|---|---|
| app.py | claude-opus | support replies |

## Next stage
Stage 0: logging and a baseline. No request logs exist.

## Decisions
- D1 quality bar: open
- D2 cost and latency goals: open

## Build plan
Add a flag `ROUTING_LOG`.

## Gates
1. Every route meets the quality bar.
"""


def _state(ts: str, status="blocked", routing="in-progress") -> str:
    return f"""---
task: {TASK}
title: Cut reply cost
stage: model-routing
status: {status}
stages:
  requirements: done
  model-routing: {routing}
created: {ts}
updated: {ts}
---

# Log

{ts} [requirements] Task created.
{ts} [model-routing] Planned stage 0; waiting on D1, D2.
"""


def _run(tmp_path, doc=GOOD_DOC, **state):
    task = tmp_path / TASK
    task.mkdir()
    (task / "STATE.md").write_text(_state(NOW.strftime(TS_FORMAT), **state))
    (task / "REQUIREMENTS.md").write_text("req")
    if doc is not None:
        (task / "MODEL-ROUTING.md").write_text(doc)
    return {"task": task, "start": NOW - timedelta(seconds=30), "end": NOW + timedelta(seconds=30)}


def test_good_output_has_no_problems(tmp_path):
    assert routing_problems(_run(tmp_path)) == []


def test_missing_output(tmp_path):
    assert "MODEL-ROUTING.md missing" in routing_problems(_run(tmp_path, doc=None))


def test_stage_not_recorded_in_state(tmp_path):
    problems = routing_problems(_run(tmp_path, routing="pending"))
    assert any("model-routing" in p for p in problems)


def test_missing_section(tmp_path):
    problems = routing_problems(_run(tmp_path, doc=GOOD_DOC.replace("## Gates", "## Checks")))
    assert any("gates" in p for p in problems)


def test_wrong_header_stage(tmp_path):
    problems = routing_problems(_run(tmp_path, doc=GOOD_DOC.replace("stage: model-routing", "stage: routing")))
    assert any("front matter stage" in p for p in problems)


def test_next_routing_stage():
    assert next_routing_stage(GOOD_DOC) == 0
    assert next_routing_stage(GOOD_DOC.replace("Stage 0:", "**Stage 3**:")) == 3
    assert next_routing_stage("## Next stage\nAdd a cache.\n") is None


def test_open_decisions():
    assert open_decisions(GOOD_DOC) == ["D1", "D2"]
    answered = GOOD_DOC.replace("D1 quality bar: open", "D1 quality bar: score 4 of 5 (user)")
    assert open_decisions(answered) == ["D2"]
