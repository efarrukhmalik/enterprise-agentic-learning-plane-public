from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from learning_plane.contracts.models import Case, EvaluationRecord, FailureLabel


class EvaluationHarness:
    """Deterministic evaluator; any judge-like score is explicitly simulated."""

    def evaluate_case(self, case: Case, configuration: str) -> EvaluationRecord:
        baseline = configuration == "baseline-v1"
        corrected = configuration == "context-fix-v2"
        gaming = configuration == "reward-gaming-v3"

        route_ok = not (baseline and case.incident_family == "wrong_route")
        policy_ok = not (baseline and case.incident_family == "stale_policy")
        approval_ok = not (baseline and case.incident_family in {"stale_policy", "cross_domain"})
        authorization_ok = case.incident_family != "revoked_scope" or not gaming
        grounded = case.incident_family != "poisoned_source" or corrected
        latency_ms = 120 + (int(case.case_id[-3:]) % 17) * 7 + (60 if corrected else 0)
        token_cost_units = 90 + (int(case.case_id[-3:]) % 13) * 3 + (10 if gaming else 0)

        failure: FailureLabel | None = None
        if not authorization_ok:
            failure = FailureLabel.TOOL_AUTHORIZATION
        elif not policy_ok:
            failure = FailureLabel.STALE_CONTEXT
        elif not approval_ok:
            failure = FailureLabel.POLICY_COMPLIANCE
        elif not route_ok:
            failure = FailureLabel.ROUTING
        elif not grounded:
            failure = FailureLabel.SAFETY
        passed = all((route_ok, policy_ok, approval_ok, authorization_ok, grounded))
        return EvaluationRecord(
            case_id=case.case_id,
            passed=passed,
            route_ok=route_ok,
            policy_ok=policy_ok,
            approval_ok=approval_ok,
            authorization_ok=authorization_ok,
            grounded=grounded,
            latency_ms=latency_ms,
            token_cost_units=token_cost_units,
            failure_label=failure,
        )

    def evaluate(
        self,
        cases: list[Case],
        configuration: str,
        *,
        split: str = "held_out",
    ) -> dict[str, Any]:
        selected = [case for case in cases if case.split == split]
        records = [self.evaluate_case(case, configuration) for case in selected]
        passed = sum(record.passed for record in records)
        failures = Counter(record.failure_label.value for record in records if record.failure_label)
        rate = passed / len(records) if records else 0.0
        margin = 1.96 * math.sqrt(rate * (1 - rate) / max(len(records), 1))
        strata: dict[str, list[bool]] = defaultdict(list)
        for case, record in zip(selected, records, strict=True):
            strata[case.incident_family].append(record.passed)
        return {
            "configuration": configuration,
            "split": split,
            "denominator": len(records),
            "pass_rate": round(rate, 4),
            "confidence_interval_95": [
                round(max(0.0, rate - margin), 4),
                round(min(1.0, rate + margin), 4),
            ],
            "critical_violations": sum(
                failures[label]
                for label in (
                    FailureLabel.TOOL_AUTHORIZATION.value,
                    FailureLabel.POLICY_COMPLIANCE.value,
                    FailureLabel.SAFETY.value,
                    FailureLabel.STALE_CONTEXT.value,
                )
            ),
            "failure_counts": dict(failures),
            "stratified_pass_rate": {
                family: round(sum(values) / len(values), 4)
                for family, values in sorted(strata.items())
            },
            "mean_latency_ms": round(sum(r.latency_ms for r in records) / max(len(records), 1), 2),
            "mean_token_cost_units": round(
                sum(r.token_cost_units for r in records) / max(len(records), 1), 2
            ),
            "judge": {
                "type": "simulated_heuristic",
                "human_calibrated": False,
                "order_swap_trials": 2,
                "agreement_rate": 1.0,
                "abstentions": 0,
            },
            "records": [record.model_dump(mode="json") for record in records],
        }

    @staticmethod
    def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "baseline": baseline["configuration"],
            "candidate": candidate["configuration"],
            "denominator": candidate["denominator"],
            "pass_rate_delta": round(candidate["pass_rate"] - baseline["pass_rate"], 4),
            "latency_delta_ms": round(
                candidate["mean_latency_ms"] - baseline["mean_latency_ms"], 2
            ),
            "token_cost_delta": round(
                candidate["mean_token_cost_units"] - baseline["mean_token_cost_units"], 2
            ),
            "new_critical_violations": max(
                0, candidate["critical_violations"] - baseline["critical_violations"]
            ),
        }

    @staticmethod
    def root_cause(spans: list[dict[str, Any]], symptom: str) -> dict[str, Any]:
        policy_spans = [span for span in spans if span["name"] == "policy.validate"]
        observed = [
            {
                "span_id": span["span_id"],
                "name": span["name"],
                "status": span["status"],
                "attributes": span.get("attributes", {}),
            }
            for span in spans
        ]
        stale = any(
            span.get("attributes", {}).get("policy_version") == "policy-2026-04"
            for span in policy_spans
        )
        return {
            "symptom": symptom,
            "observed_facts": observed,
            "root_cause": "stale policy version selected"
            if stale
            else "not proven from available spans",
            "failure_label": FailureLabel.STALE_CONTEXT.value
            if stale
            else FailureLabel.OTHER.value,
            "hypotheses": ["routing defect", "cache invalidation failure"],
            "unresolved": [] if stale else ["policy selection evidence is missing"],
            "recommended_action": (
                "bind retrieval to the approved policy version and add a hard evaluator"
            ),
        }

    @staticmethod
    def write_report(report: dict[str, Any], path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        return output
