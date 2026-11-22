

def test_score_gate_applies_mean_and_floor(tmp_path):
    from run import score_gate
    cfg = {"mean": 4, "floor": 3, "min_gradable": 0.9}

    def runs(rows):
        for i, row in enumerate(rows):
            d = tmp_path / "s" / f"run-{i}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "judge.json").write_text(__import__("json").dumps(row))

    good = {"verifiable": 5, "scope": 4, "no_invention": 3}   # the old eval's passing shape: 3s allowed
    runs([good] * 3)
    assert score_gate(tmp_path, "s", 3, cfg)[0].startswith("PASS")
    runs([good, good, {"verifiable": 5, "scope": 5, "no_invention": 2}])
    assert any("below 3" in line for line in score_gate(tmp_path, "s", 3, cfg))
    assert any("gradable" in line for line in score_gate(tmp_path, "s", 5, cfg))
    runs([{"verifiable": 3, "scope": 3, "no_invention": 3}] * 3)
    assert any("mean 3.00" in line for line in score_gate(tmp_path, "s", 3, cfg))


def test_score_gate_applies_per_criterion_mean(tmp_path):
    import json
    from run import score_gate
    for i, row in enumerate([{"verifiable": 5, "scope": 5, "no_invention": 3}] * 3):
        d = tmp_path / "s" / f"run-{i}"
        d.mkdir(parents=True)
        (d / "judge.json").write_text(json.dumps(row))
    loose = {"mean": 4, "floor": 3, "min_gradable": 0.9}
    assert score_gate(tmp_path, "s", 3, loose)[0].startswith("PASS")   # overall mean 4.33 hides it
    strict = {**loose, "criteria": {"no_invention": 4}}
    lines = score_gate(tmp_path, "s", 3, strict)
    assert lines[0].startswith("FAIL") and any("no_invention mean 3.00 < 4" in l for l in lines)


def test_score_gates_count_runs_per_test():
    """A config with two tests: each score gate counts only its own test's runs."""
    from run import score_gates
    case = lambda scenario, gate=None: {"testCase": {"description": scenario, "vars": {"scenario": scenario},
                                                     "metadata": {"score_gate": gate} if gate else {}}}
    gate = {"mean": 4, "floor": 3, "min_gradable": 0.9}
    data = {"results": {"results": [case("requirements", gate)] * 10 + [case("requirements_with_concept")] * 10}}
    assert score_gates(data) == [("requirements", 10, gate)]


def test_eval_modules_import():
    """promptfoo loads these by path; a syntax error there only shows up as a failed eval run."""
    import importlib.util
    from helpers import ROOT
    for name in ("asserts", "provider"):
        path = ROOT / "evals" / "promptfoo" / f"{name}.py"
        spec = importlib.util.spec_from_file_location(f"kairyn_{name}", path)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))


def test_cost_of_reads_total_cost_from_json_output():
    from runner import cost_of
    assert cost_of('{"result": "hi", "total_cost_usd": 0.25}') == 0.25
    assert cost_of("plain text, not json") is None
    assert cost_of('{"result": "no cost"}') is None


def test_record_cost_appends_one_line_per_call(tmp_path):
    import json
    from runner import record_cost
    record_cost(tmp_path / "s" / "run-1", "run", 0.5)
    record_cost(tmp_path / "s" / "run-1", "judge", 0.1)
    record_cost(tmp_path / "s" / "run-1", "run", None)   # unknown cost is not recorded
    lines = (tmp_path / "s" / "run-1" / "cost.jsonl").read_text().splitlines()
    assert [json.loads(l) for l in lines] == [{"role": "run", "usd": 0.5}, {"role": "judge", "usd": 0.1}]


def test_session_cost_is_the_last_turn_only(tmp_path, monkeypatch):
    """On --resume, total_cost_usd is the conversation total so far: summing turns would count turn 1 twice."""
    import json
    import runner
    replies = iter([{"session_id": "s1", "result": "a", "total_cost_usd": 0.10},
                    {"session_id": "s1", "result": "b", "total_cost_usd": 0.25}])

    class Done:
        def __init__(self, out): self.stdout = out
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: Done(json.dumps(next(replies))))
    runner.set_cost_dir(tmp_path)
    try:
        runner.claude_session(["one", "two"], tmp_path)
    finally:
        runner.set_cost_dir(None)
    assert [json.loads(l)["usd"] for l in (tmp_path / "cost.jsonl").read_text().splitlines()] == [0.25]


def test_cost_lines_sum_per_scenario_and_total(tmp_path):
    from run import cost_lines
    from runner import record_cost
    record_cost(tmp_path / "requirements" / "run-1", "run", 0.50)
    record_cost(tmp_path / "requirements" / "run-1", "judge", 0.05)
    record_cost(tmp_path / "requirements" / "run-2", "run", 0.70)
    record_cost(tmp_path / "grill" / "run-1", "run", 1.00)
    lines = cost_lines(tmp_path)
    assert "cost  grill: $1.00 over 1 run (judge $0.00)" in lines
    assert "cost  requirements: $1.25 over 2 runs (judge $0.05)" in lines
    assert lines[-1] == "cost  total: $2.25"
    assert cost_lines(tmp_path / "empty") == []
