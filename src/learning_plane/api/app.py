from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from learning_plane.contracts import RunRequest
from learning_plane.demo import DemoEnvironment
from learning_plane.evals import build_golden_dataset

app = FastAPI(title="Enterprise Agentic Learning Plane", version="0.1.0")
environment = DemoEnvironment(Path(os.getenv("LEARNING_PLANE_EVIDENCE", "evidence")))


class ApprovalInput(BaseModel):
    approved: bool
    approver: str


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return """<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Enterprise Agentic Learning Plane</title>
<style>body{font-family:system-ui;margin:3rem;max-width:1000px;background:#071529;color:#eef6ff}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem}
.card{background:#10284a;border:1px solid #2c6bb2;border-radius:14px;padding:1rem}
code{color:#6de1ff}a{color:#8fd9ff}</style></head><body>
<h1>Enterprise Agentic Learning Plane</h1>
<p>Offline synthetic evidence; no live cloud or paid model calls.</p>
<div class='grid'><div class='card'><h2>Lab 1</h2><p>Governed runtime and approvals</p></div>
<div class='card'><h2>Lab 2</h2><p>Traces, evaluation, and RCA</p></div>
<div class='card'><h2>Lab 3</h2><p>Hard gates, canary, rollback</p></div>
<div class='card'><h2>Lab 4</h2><p>Local events and GCP mapping</p></div></div>
<p><a href='/docs'>Interactive API documentation</a> ·
<a href='/health'>Health</a></p></body></html>"""


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "offline": True,
        "langgraph_available": environment.runtime.graph is not None,
        "cloud_deployed": False,
    }


@app.post("/api/run")
async def run(request: RunRequest) -> dict[str, Any]:
    return environment.runtime.run(request).model_dump(mode="json")


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str, x_tenant_id: str = Header(...)) -> dict[str, Any]:
    result = environment.store.get_run(x_tenant_id, run_id)
    if not result:
        raise HTTPException(404, "run not found for tenant")
    return result


@app.post("/api/runs/{run_id}/approvals/{approval_id}")
async def approve(
    run_id: str,
    approval_id: str,
    body: ApprovalInput,
    x_tenant_id: str = Header(...),
) -> dict[str, Any]:
    stored = environment.store.get_run(x_tenant_id, run_id)
    if not stored:
        raise HTTPException(404, "run not found for tenant")
    request = DemoEnvironment.request(tenant_id=x_tenant_id, approval_id=approval_id)
    return environment.runtime.decide_approval(
        request, approval_id, body.approved, body.approver
    ).model_dump(mode="json")


@app.post("/api/evaluate")
async def evaluate(configuration: str = "context-fix-v2") -> dict[str, Any]:
    return environment.harness.evaluate(build_golden_dataset(), configuration)


@app.get("/api/releases")
async def releases(x_tenant_id: str = Header(...)) -> list[dict[str, Any]]:
    return environment.store.releases(x_tenant_id)
