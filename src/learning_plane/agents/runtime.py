from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

from learning_plane.agents.tools import AuthorizationError, GovernedTools, ToolContext
from learning_plane.contracts import ApprovalDecision, RunRequest, RunResult
from learning_plane.contracts.models import Domain
from learning_plane.storage import SQLiteStore
from learning_plane.telemetry import LocalTracer


class GraphState(TypedDict, total=False):
    request: RunRequest
    trace_id: str
    root_span_id: str
    route: list[Domain]
    evidence: list[dict[str, Any]]
    answer: str
    status: str
    approval_id: str


class AgentRuntime:
    def __init__(self, store: SQLiteStore, evidence_dir: str | Path) -> None:
        self.store = store
        self.tools = GovernedTools(store)
        self.tracer = LocalTracer(store, Path(evidence_dir) / "traces.jsonl")
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return None

        builder = StateGraph(GraphState)
        builder.add_node("route", self._route_node)
        builder.add_node("specialists", self._specialist_node)
        builder.add_node("policy", self._policy_node)
        builder.add_node("compose", self._compose_node)
        builder.add_edge(START, "route")
        builder.add_edge("route", "specialists")
        builder.add_edge("specialists", "policy")
        builder.add_conditional_edges(
            "policy",
            lambda state: "compose" if state.get("status") == "completed" else "end",
            {"compose": "compose", "end": END},
        )
        builder.add_edge("compose", END)
        return builder.compile()

    @staticmethod
    def _ctx(request: RunRequest) -> ToolContext:
        return ToolContext(
            tenant_id=request.tenant_id,
            principal_id=request.principal_id,
            correlation_id=request.correlation_id,
            scopes=request.scopes,
        )

    def _route_node(self, state: GraphState) -> dict[str, Any]:
        request = state["request"]
        message = request.message.lower()
        route: list[Domain] = []
        if any(word in message for word in ("bill", "charge", "fee", "refund", "waiver")):
            route.append(Domain.BILLING)
        if any(word in message for word in ("outage", "service", "internet", "connect")):
            route.append(Domain.CONNECTIVITY)
        if any(word in message for word in ("account", "address", "plan")):
            route.append(Domain.ACCOUNT)
        if "policy" in message or "compliance" in message:
            route.append(Domain.POLICY)
        if not route:
            route = [Domain.ACCOUNT]
        if request.inject_fault == "wrong_route":
            route = [Domain.ACCOUNT]
        return {"route": list(dict.fromkeys(route))}

    def _specialist_node(self, state: GraphState) -> dict[str, Any]:
        request = state["request"]
        ctx = self._ctx(request)
        evidence: list[dict[str, Any]] = []
        parent = state["root_span_id"]
        for domain in state["route"]:
            with self.tracer.span(
                f"agent.{domain.value}",
                tenant_id=request.tenant_id,
                trace_id=state["trace_id"],
                parent_span_id=parent,
                attributes={"route": domain.value, "configuration_version": "runtime-v1"},
            ) as span:
                if domain is Domain.BILLING:
                    value = self.tools.get_bill(request.customer_id, ctx)
                elif domain is Domain.CONNECTIVITY:
                    value = self.tools.get_service_status(request.customer_id, ctx)
                else:
                    value = self.tools.get_customer_profile(request.customer_id, ctx)
                evidence.append({"domain": domain.value, "value": value})
                span["attributes"]["tool_result_digest"] = self.tracer.digest(value)
        return {"evidence": evidence}

    @staticmethod
    def _refund_parameters(request: RunRequest, amount: float) -> dict[str, Any]:
        return {
            "customer_id": request.customer_id,
            "amount": round(amount, 2),
            "reason": "fee waiver",
        }

    def _policy_node(self, state: GraphState) -> dict[str, Any]:
        request = state["request"]
        ctx = self._ctx(request)
        version = (
            "policy-2026-04" if request.inject_fault == "stale_policy" else request.policy_version
        )
        with self.tracer.span(
            "policy.validate",
            tenant_id=request.tenant_id,
            trace_id=state["trace_id"],
            parent_span_id=state["root_span_id"],
            attributes={"policy_version": version},
        ) as span:
            policy = self.tools.retrieve_policy(version, ctx)
            span["attributes"]["source"] = policy["source"]
            wants_refund = any(
                word in request.message.lower() for word in ("refund", "waive", "waiver")
            )
            amount = 15.0
            if wants_refund and policy["requires_approval"] and amount > policy["refund_threshold"]:
                params = self._refund_parameters(request, amount)
                expected = sha256(str(sorted(params.items())).encode()).hexdigest()
                if request.approval_id:
                    decision = self.store.get_approval(request.tenant_id, request.approval_id)
                    if (
                        decision
                        and decision["approved"]
                        and decision["exact_parameters_hash"] == expected
                    ):
                        return {"status": "completed", "approval_id": request.approval_id}
                approval_id = request.approval_id or f"approval-{uuid4().hex[:12]}"
                return {
                    "status": "approval_required",
                    "approval_id": approval_id,
                    "answer": (
                        "A $15.00 fee waiver requires authorized human approval under "
                        f"{version}. No write was performed."
                    ),
                }
        return {"status": "completed"}

    def _compose_node(self, state: GraphState) -> dict[str, Any]:
        request = state["request"]
        facts = []
        for item in state.get("evidence", []):
            if item["domain"] == "billing":
                facts.append(f"current balance ${item['value']['balance']:.2f}")
            if item["domain"] == "connectivity":
                facts.append(f"service status {item['value']['status']}")
        answer = "Northstar Connect verified " + " and ".join(facts or ["the customer profile"])
        if state.get("approval_id"):
            ctx = self._ctx(request)
            result = self.tools.submit_refund_request(
                request.customer_id,
                15.0,
                "fee waiver",
                state["approval_id"],
                f"{request.correlation_id}:refund:15",
                ctx,
            )
            answer += f". Approved refund request {result['request_id']} was submitted idempotently"
        answer += f" using policy {request.policy_version}."
        return {"answer": answer, "status": "completed"}

    def run(self, request: RunRequest) -> RunResult:
        trace_id = uuid4().hex
        with self.tracer.span(
            "agent.run",
            tenant_id=request.tenant_id,
            trace_id=trace_id,
            attributes={
                "principal_id": request.principal_id,
                "correlation_id": request.correlation_id,
                "message_digest": self.tracer.digest(request.message),
                "policy_version": request.policy_version,
            },
        ) as root:
            state: GraphState = {
                "request": request,
                "trace_id": trace_id,
                "root_span_id": root["span_id"],
                "evidence": [],
            }
            try:
                if self.graph:
                    state = self.graph.invoke(state)
                else:
                    state.update(self._route_node(state))
                    state.update(self._specialist_node(state))
                    state.update(self._policy_node(state))
                    if state.get("status") == "completed":
                        state.update(self._compose_node(state))
                result = RunResult(
                    status=state.get("status", "failed"),
                    route=state.get("route", []),
                    answer=state.get("answer", "Execution failed before response composition."),
                    policy_version=(
                        "policy-2026-04"
                        if request.inject_fault == "stale_policy"
                        else request.policy_version
                    ),
                    approval_id=state.get("approval_id"),
                    trace_id=trace_id,
                    tool_results=state.get("evidence", []),
                )
            except (AuthorizationError, LookupError) as exc:
                result = RunResult(
                    status="denied",
                    route=state.get("route", []),
                    answer=f"Request denied safely: {exc}",
                    policy_version=request.policy_version,
                    trace_id=trace_id,
                    tool_results=state.get("evidence", []),
                )
        self.store.save_run(request, result)
        return result

    def decide_approval(
        self,
        request: RunRequest,
        approval_id: str,
        approved: bool,
        approver: str,
        role: str = "refund-approver",
    ) -> ApprovalDecision:
        params = self._refund_parameters(request, 15.0)
        decision = ApprovalDecision(
            approval_id=approval_id,
            tenant_id=request.tenant_id,
            principal_id=approver,
            role=role,
            approved=approved,
            exact_parameters_hash=sha256(str(sorted(params.items())).encode()).hexdigest(),
        )
        self.store.save_approval(decision)
        return decision
