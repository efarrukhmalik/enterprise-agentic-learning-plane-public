from __future__ import annotations

import pytest
from pydantic import ValidationError

from learning_plane.contracts import RunRequest, VariantManifest


def test_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RunRequest(
            tenant_id="northstar",
            principal_id="tester",
            correlation_id="corr-1",
            customer_id="cust-001",
            message="hello",
            surprise=True,
        )


def test_variant_is_content_hashed():
    variant = VariantManifest(
        baseline_version="v1",
        lane="routing",
        changed_factor="router rule",
        diff={"rule": "billing-first"},
        owner="team",
        expected_effect="route billing correctly",
        failure_evidence=["trace-1"],
        golden_set_id="golden-v1",
        primary_metric="route_accuracy",
        guardrails=["no authorization regression"],
        risks=["over-routing"],
        reversal_plan="restore v1",
    )
    assert len(variant.content_hash) == 64
