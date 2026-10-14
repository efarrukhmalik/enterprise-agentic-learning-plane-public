from __future__ import annotations

from learning_plane.demo import DemoEnvironment


def test_approval_pause_resume_and_idempotency(tmp_path):
    env = DemoEnvironment(tmp_path / "evidence")
    request = env.request()
    paused = env.runtime.run(request)
    assert paused.status == "approval_required"
    assert paused.approval_id

    env.runtime.decide_approval(request, paused.approval_id, True, "manager")
    approved = request.model_copy(update={"approval_id": paused.approval_id})
    first = env.runtime.run(approved)
    replay = env.runtime.run(approved)

    assert first.status == "completed"
    assert replay.status == "completed"
    assert first.answer == replay.answer
    assert "refund-" in first.answer


def test_revoked_scope_fails_closed(tmp_path):
    env = DemoEnvironment(tmp_path / "evidence")
    request = env.request(scopes={"customer:read", "policy:read"})
    result = env.runtime.run(request)
    assert result.status == "denied"
    assert "scope" in result.answer


def test_tenant_isolation(tmp_path):
    env = DemoEnvironment(tmp_path / "evidence")
    result = env.runtime.run(env.request())
    assert env.store.get_run("northstar", result.run_id)
    assert env.store.get_run("other-tenant", result.run_id) is None
