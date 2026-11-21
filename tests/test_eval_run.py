

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
