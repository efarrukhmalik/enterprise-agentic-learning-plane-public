from __future__ import annotations

import httpx
import pytest

from learning_plane.api.app import app


@pytest.mark.anyio
async def test_health_and_run_routes():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        response = await client.post(
            "/api/run",
            json={
                "tenant_id": "northstar",
                "principal_id": "api-test",
                "correlation_id": "corr-api-test",
                "customer_id": "cust-001",
                "message": "Explain my latest bill",
                "scopes": [
                    "customer:read",
                    "billing:read",
                    "policy:read",
                    "service:read",
                ],
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["route"] == ["billing"]
