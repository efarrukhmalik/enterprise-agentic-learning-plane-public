# Build status

| Area | Implemented | Verification | Limitations |
|---|---|---|---|
| Foundation | Package, CLI, contracts, SQLite, tests | Ruff check and format passed; 11 tests passed | Hashed runtime, development, and cloud dependency locks are checked in |
| Lab 1 | Typed requests, LangGraph graph, dispatcher, specialists, tools, approval, idempotency, tenant checks | All-labs demo reported LangGraph; approval paused then completed | Deterministic provider; no remote model call |
| Lab 2 | Local spans, 96-case dataset, deterministic harness, simulated judge metadata, RCA | Baseline 0.50, candidate 1.00, zero candidate critical violations | No live OTLP/Phoenix/LangSmith backend |
| Lab 3 | Hashed variant, comparison, hard gates, approval, canary, rollback, gaming scenario | Gaming candidate blocked; rollback restored baseline-v1 | No RL/DPO weight update executed |
| Lab 4 | Local event pipeline, analytical sink, Docker, CI, Terraform mapping | Event processed once; repeat produced no duplicate; cloud_deployed=false | Docker installed but daemon not running; Terraform unavailable; no GCP deployment |
| Integration | All-labs CLI, FastAPI, dashboard, documentation | All-labs demo exited 0; API tested through ASGI | Dashboard is intentionally lightweight |

## Commands executed on October 13 2026

    ruff check .
    ruff format --check .
    python -m pytest -q
    python -m learning_plane.cli demo all --evidence-dir evidence
    docker info --format '{{.ServerVersion}}'

The first four commands passed. Docker reported that the Docker Desktop Linux engine was not running. Terraform was not installed, so terraform formatting and validation were not executed.

