from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from learning_plane.storage import SQLiteStore


class AuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class ToolContext:
    tenant_id: str
    principal_id: str
    correlation_id: str
    scopes: set[str]


CUSTOMERS = {
    "cust-001": {"name": "Avery Chen", "plan": "Northstar Fiber", "tenant_id": "northstar"},
    "cust-002": {"name": "Jordan Rivera", "plan": "Northstar Mobile", "tenant_id": "northstar"},
}
BILLS = {
    "cust-001": {"balance": 135.0, "last_charge": 120.0, "fee": 15.0},
    "cust-002": {"balance": 80.0, "last_charge": 80.0, "fee": 0.0},
}
SERVICE = {
    "cust-001": {"status": "degraded", "incident": "inc-2026-10-13", "eta_minutes": 45},
    "cust-002": {"status": "operational", "incident": None, "eta_minutes": 0},
}
POLICIES = {
    "policy-2026-10": {
        "refund_threshold": 10.0,
        "requires_approval": True,
        "effective": "2026-10-01",
    },
    "policy-2026-04": {
        "refund_threshold": 100.0,
        "requires_approval": False,
        "effective": "2026-04-01",
    },
}


class GovernedTools:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    @staticmethod
    def _require(ctx: ToolContext, scope: str) -> None:
        if scope not in ctx.scopes:
            raise AuthorizationError(f"missing required scope: {scope}")

    @staticmethod
    def _customer(customer_id: str, ctx: ToolContext) -> dict[str, Any]:
        customer = CUSTOMERS.get(customer_id)
        if not customer or customer["tenant_id"] != ctx.tenant_id:
            raise AuthorizationError("customer is unavailable in this tenant")
        return customer

    def get_customer_profile(self, customer_id: str, ctx: ToolContext) -> dict[str, Any]:
        self._require(ctx, "customer:read")
        return dict(self._customer(customer_id, ctx))

    def get_bill(self, customer_id: str, ctx: ToolContext) -> dict[str, Any]:
        self._require(ctx, "billing:read")
        self._customer(customer_id, ctx)
        return dict(BILLS[customer_id])

    def get_service_status(self, customer_id: str, ctx: ToolContext) -> dict[str, Any]:
        self._require(ctx, "service:read")
        self._customer(customer_id, ctx)
        return dict(SERVICE[customer_id])

    def retrieve_policy(self, version: str, ctx: ToolContext) -> dict[str, Any]:
        self._require(ctx, "policy:read")
        policy = POLICIES.get(version)
        if not policy:
            raise LookupError(f"unknown immutable policy version: {version}")
        return {"version": version, **policy, "source": f"policy://{version}"}

    def submit_refund_request(
        self,
        customer_id: str,
        amount: float,
        reason: str,
        approval_id: str,
        idempotency_key: str,
        ctx: ToolContext,
    ) -> dict[str, Any]:
        self._require(ctx, "refund:write")
        self._customer(customer_id, ctx)
        params = {
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "reason": reason,
        }
        expected = sha256(str(sorted(params.items())).encode()).hexdigest()
        decision = self.store.get_approval(ctx.tenant_id, approval_id)
        if (
            not decision
            or not decision["approved"]
            or decision["exact_parameters_hash"] != expected
        ):
            raise AuthorizationError(
                "approval is missing, denied, cross-tenant, or bound to other parameters"
            )
        result = {
            "request_id": f"refund-{idempotency_key[:12]}",
            "status": "submitted",
            "amount": amount,
            "approval_id": approval_id,
        }
        return self.store.put_idempotent(ctx.tenant_id, idempotency_key, result)

    def update_case_note(
        self, customer_id: str, note: str, idempotency_key: str, ctx: ToolContext
    ) -> dict[str, Any]:
        self._require(ctx, "case:write")
        self._customer(customer_id, ctx)
        result = {"status": "recorded", "note_digest": sha256(note.encode()).hexdigest()}
        return self.store.put_idempotent(ctx.tenant_id, idempotency_key, result)
