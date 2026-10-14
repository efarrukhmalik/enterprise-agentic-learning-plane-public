from __future__ import annotations

from learning_plane.evals import EvaluationHarness, build_golden_dataset


def test_golden_dataset_is_large_and_family_split():
    cases = build_golden_dataset()
    assert len(cases) >= 80
    assert {case.split for case in cases} == {"development", "calibration", "held_out"}
    families = {}
    for case in cases:
        families.setdefault(case.incident_family, set()).add(case.split)
    assert all(splits == {"development", "calibration", "held_out"} for splits in families.values())


def test_corrected_candidate_improves_without_critical_violations():
    cases = build_golden_dataset()
    harness = EvaluationHarness()
    baseline = harness.evaluate(cases, "baseline-v1")
    candidate = harness.evaluate(cases, "context-fix-v2")
    comparison = harness.compare(baseline, candidate)
    assert candidate["pass_rate"] > baseline["pass_rate"]
    assert candidate["critical_violations"] == 0
    assert comparison["new_critical_violations"] == 0
