from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learning_plane.agents import AgentRuntime
from learning_plane.contracts import RunRequest
from learning_plane.deploy import LocalEventPipeline
from learning_plane.evals import EvaluationHarness, build_golden_dataset
from learning_plane.optimization import ReleaseController
from learning_plane.storage import SQLiteStore


class DemoEnvironment:
    def __init__(self, root: str | Path = "evidence") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = SQLiteStore(self.root / "learning_plane.db")
        self.runtime = AgentRuntime(self.store, self.root)
        self.harness = EvaluationHarness()
        self.releases = ReleaseController(self.store)
        self.events = LocalEventPipeline(self.store)

    def _write(self, name: str, payload: Any) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path

    @staticmethod
    def request(**overrides: Any) -> RunRequest:
        values: dict[str, Any] = {
            "tenant_id": "northstar",
            "principal_id": "demo-agent",
            "correlation_id": "corr-demo-001",
            "customer_id": "cust-001",
            "message": "Please waive the fee because my internet service is down",
            "scopes": {
                "customer:read",
                "billing:read",
                "service:read",
                "policy:read",
                "refund:write",
                "case:write",
            },
        }
        values.update(overrides)
        return RunRequest(**values)

    def lab1(self) -> dict[str, Any]:
        request = self.request()
        paused = self.runtime.run(request)
        if paused.status != "approval_required" or not paused.approval_id:
            raise RuntimeError("expected approval checkpoint")
        decision = self.runtime.decide_approval(
            request, paused.approval_id, True, approver="human-manager"
        )
        resumed = self.runtime.run(request.model_copy(update={"approval_id": paused.approval_id}))
        replay = self.runtime.run(request.model_copy(update={"approval_id": paused.approval_id}))
        stale = self.runtime.run(
            self.request(
                correlation_id="corr-stale-001",
                message="Explain the refund policy",
                inject_fault="stale_policy",
            )
        )
        payload = {
            "lab": 1,
            "framework": "LangGraph"
            if self.runtime.graph
            else "manual fallback (LangGraph unavailable)",
            "paused": paused.model_dump(mode="json"),
            "approval": decision.model_dump(mode="json"),
            "resumed": resumed.model_dump(mode="json"),
            "idempotent_replay": replay.model_dump(mode="json"),
            "stale_policy_fault": stale.model_dump(mode="json"),
        }
        self._write("lab1_runtime.json", payload)
        return payload

    def lab2(self) -> dict[str, Any]:
        cases = build_golden_dataset(self.root / "golden_dataset.jsonl")
        baseline = self.harness.evaluate(cases, "baseline-v1")
        candidate = self.harness.evaluate(cases, "context-fix-v2")
        stale = self.runtime.run(
            self.request(
                correlation_id="corr-rca-001",
                message="Explain the refund policy",
                inject_fault="stale_policy",
            )
        )
        rca = self.harness.root_cause(
            self.runtime.tracer.trace_tree("northstar", stale.trace_id),
            "agent used a stale refund policy",
        )
        payload = {
            "lab": 2,
            "dataset_cases": len(cases),
            "baseline": baseline,
            "candidate": candidate,
            "comparison": self.harness.compare(baseline, candidate),
            "root_cause": rca,
        }
        self._write("lab2_evaluation.json", payload)
        return payload

    def lab3(self) -> dict[str, Any]:
        cases = build_golden_dataset()
        baseline = self.harness.evaluate(cases, "baseline-v1")
        candidate = self.harness.evaluate(cases, "context-fix-v2")
        gaming = self.harness.evaluate(cases, "reward-gaming-v3")
        variant = self.releases.propose_context_fix(["corr-rca-001"])
        decision = self.releases.gate(baseline, candidate)
        gaming_decision = self.releases.gate(baseline, gaming)
        release = self.releases.approve(
            "northstar", "context-fix-v2", "release-manager", decision, "baseline-v1"
        )
        canary = self.releases.start_canary(release, 10)
        rollback = self.releases.monitor_and_maybe_rollback(
            canary,
            {"critical_violations": 1, "error_rate": 0.03, "p95_ms": 850},
        )
        payload = {
            "lab": 3,
            "variant": variant.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json"),
            "optimizer_gaming_blocked": not gaming_decision.allowed,
            "gaming_decision": gaming_decision.model_dump(mode="json"),
            "canary": canary,
            "rollback": rollback,
            "terminology": (
                "offline scorecard and rule-based optimizer; no RL weight update executed"
            ),
        }
        self._write("lab3_optimization.json", payload)
        return payload

    def lab4(self) -> dict[str, Any]:
        event_id = self.events.publish(
            "northstar",
            {
                "kind": "agent_run_completed",
                "run_id": "demo-run-001",
                "latency_ms": 243,
                "token_cost_units": 123,
                "error": False,
            },
        )
        processed = self.events.process("northstar")
        second_pass = self.events.process("northstar")
        payload = {
            "lab": 4,
            "published_event_id": event_id,
            "processed": processed,
            "idempotent_second_pass": second_pass,
            "analytics": self.store.analytics("northstar"),
            "cloud_deployed": False,
            "cloud_mapping": {
                "api": "Cloud Run",
                "events": "Pub/Sub",
                "analytics": "BigQuery",
                "model": "Vertex AI optional adapter",
                "secrets": "Secret Manager references",
            },
        }
        self._write("lab4_cloud_readiness.json", payload)
        return payload

    def all(self) -> dict[str, Any]:
        result = {
            "lab1": self.lab1(),
            "lab2": self.lab2(),
            "lab3": self.lab3(),
            "lab4": self.lab4(),
        }
        self._write("demo_all.json", result)
        return result
