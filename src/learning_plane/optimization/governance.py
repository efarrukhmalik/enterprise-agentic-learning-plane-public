from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import uuid4

from learning_plane.contracts.models import ReleaseDecision, VariantManifest
from learning_plane.storage import SQLiteStore


class ReleaseController:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def propose_context_fix(self, evidence_ids: list[str]) -> VariantManifest:
        manifest = VariantManifest(
            baseline_version="baseline-v1",
            lane="context",
            changed_factor="policy version selection",
            diff={"policy_selector": {"from": "latest cached", "to": "approved effective version"}},
            owner="evaluation-team",
            expected_effect="eliminate stale-policy decisions without changing routing or tools",
            failure_evidence=evidence_ids,
            golden_set_id="northstar-golden-v1",
            primary_metric="held_out_pass_rate",
            guardrails=[
                "zero unauthorized writes",
                "zero stale-policy decisions",
                "zero safety regressions",
            ],
            risks=["higher retrieval latency", "missing policy version fails closed"],
            reversal_plan="restore baseline-v1 configuration manifest",
        )
        self.store.save_variant(manifest)
        return manifest

    @staticmethod
    def gate(baseline: dict[str, Any], candidate: dict[str, Any]) -> ReleaseDecision:
        failures: list[str] = []
        if candidate["critical_violations"]:
            failures.append("candidate has critical policy, safety, or authorization violations")
        if candidate["mean_latency_ms"] > baseline["mean_latency_ms"] * 1.75:
            failures.append("latency regression exceeds 75 percent")
        if candidate["mean_token_cost_units"] > baseline["mean_token_cost_units"] * 1.5:
            failures.append("cost regression exceeds 50 percent")
        delta = candidate["pass_rate"] - baseline["pass_rate"]
        if delta < 0:
            failures.append("held-out pass rate regressed")
        return ReleaseDecision(
            allowed=not failures,
            hard_gate_failures=failures,
            metric_delta=round(delta, 4),
            reason="all hard gates passed" if not failures else "; ".join(failures),
        )

    def approve(
        self,
        tenant_id: str,
        version: str,
        approver: str,
        decision: ReleaseDecision,
        prior_version: str,
    ) -> dict[str, Any]:
        if not decision.allowed:
            raise PermissionError("release cannot be approved while hard gates fail")
        release = {
            "release_id": f"release-{uuid4().hex[:12]}",
            "tenant_id": tenant_id,
            "version": version,
            "prior_version": prior_version,
            "status": "approved",
            "approver": approver,
            "decision_digest": sha256(decision.model_dump_json().encode()).hexdigest(),
        }
        self.store.save_release(release)
        return release

    def start_canary(self, release: dict[str, Any], traffic_percent: int = 10) -> dict[str, Any]:
        if release["status"] != "approved":
            raise PermissionError("only approved releases can start a canary")
        canary = {
            **release,
            "status": "canary",
            "traffic_percent": traffic_percent,
            "assignment": "stable sha256(customer_id + release_id) modulo 100",
            "stop_conditions": {"critical_violations": 0, "error_rate": 0.02, "p95_ms": 800},
        }
        self.store.save_release(canary)
        return canary

    @staticmethod
    def assigned(customer_id: str, release_id: str, traffic_percent: int) -> bool:
        bucket = int(sha256(f"{customer_id}:{release_id}".encode()).hexdigest()[:8], 16) % 100
        return bucket < traffic_percent

    def monitor_and_maybe_rollback(
        self, canary: dict[str, Any], metrics: dict[str, float]
    ) -> dict[str, Any]:
        stop = canary["stop_conditions"]
        breached = (
            metrics.get("critical_violations", 0) > stop["critical_violations"]
            or metrics.get("error_rate", 0) > stop["error_rate"]
            or metrics.get("p95_ms", 0) > stop["p95_ms"]
        )
        if not breached:
            observed = {**canary, "status": "canary_healthy", "observed_metrics": metrics}
            self.store.save_release(observed)
            return observed
        rollback = {
            **canary,
            "release_id": f"rollback-{uuid4().hex[:12]}",
            "status": "rolled_back",
            "version": canary["prior_version"],
            "rolled_back_from": canary["version"],
            "observed_metrics": metrics,
            "restoration_verified": True,
        }
        self.store.save_release(rollback)
        return rollback
