from __future__ import annotations

import pytest

from learning_plane.demo import DemoEnvironment
from learning_plane.evals import build_golden_dataset


def test_optimizer_gaming_is_blocked(tmp_path):
    env = DemoEnvironment(tmp_path / "evidence")
    cases = build_golden_dataset()
    baseline = env.harness.evaluate(cases, "baseline-v1")
    gaming = env.harness.evaluate(cases, "reward-gaming-v3")
    decision = env.releases.gate(baseline, gaming)
    assert not decision.allowed
    assert decision.hard_gate_failures
    with pytest.raises(PermissionError):
        env.releases.approve("northstar", "reward-gaming-v3", "manager", decision, "baseline-v1")


def test_approval_is_bound_to_exact_parameters(tmp_path):
    env = DemoEnvironment(tmp_path / "evidence")
    request = env.request()
    paused = env.runtime.run(request)
    decision = env.runtime.decide_approval(request, paused.approval_id, True, "manager")
    decision.exact_parameters_hash = "wrong"
    env.store.save_approval(decision)
    resumed = env.runtime.run(request.model_copy(update={"approval_id": paused.approval_id}))
    assert resumed.status == "approval_required"
