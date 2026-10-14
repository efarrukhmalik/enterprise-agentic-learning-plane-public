# Enterprise Agentic Learning Plane

An offline-first portfolio system that demonstrates four integrated engineering labs for the synthetic company **Northstar Connect**:

1. Governed multi-agent runtime with a real LangGraph `StateGraph` path.
2. Structured trace evidence, deterministic evaluation, and root-cause analysis.
3. One-factor optimization, hard release gates, approval, canary, and rollback.
4. Local event processing plus a Cloud Run, Pub/Sub, BigQuery, and Vertex AI deployment mapping.

The default model, judge, data, costs, and cloud behavior are deterministic simulations. No API key, cloud account, or paid service is required.

## Quick start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python -m learning_plane.cli demo all
.\.venv\Scripts\pytest -q
```

Linux and macOS use `.venv/bin/python` in the same commands.

Generated artifacts are written to `evidence/` and intentionally ignored by Git. The demo uses a stable seed and is safe to rerun.

The checked-in lock files make runtime, development, and optional cloud environments reproducible. Regenerate them with `pip-tools` after changing `pyproject.toml`:

```powershell
python -m pip install "pip-tools==7.6.2" "hatchling>=1.27" "packaging>=24"
python -m piptools compile --no-build-isolation --all-build-deps --strip-extras --generate-hashes --output-file requirements.lock pyproject.toml
python -m piptools compile --no-build-isolation --all-build-deps --extra dev --strip-extras --generate-hashes --output-file requirements-dev.lock pyproject.toml
python -m piptools compile --no-build-isolation --all-build-deps --extra cloud --strip-extras --generate-hashes --output-file requirements-cloud.lock pyproject.toml
```

## Run one lab

```powershell
.\.venv\Scripts\python -m learning_plane.cli demo lab1
.\.venv\Scripts\python -m learning_plane.cli demo lab2
.\.venv\Scripts\python -m learning_plane.cli demo lab3
.\.venv\Scripts\python -m learning_plane.cli demo lab4
```

## API and dashboard

```powershell
.\.venv\Scripts\uvicorn learning_plane.api.app:app --reload
```

Open <http://127.0.0.1:8000/>. Useful routes include `/health`, `/api/run`, `/api/runs/{run_id}`, `/api/evaluate`, and `/api/releases`.

## Demonstrated scenarios

- Cross-domain billing and connectivity request with policy provenance.
- High-risk refund paused for human approval and resumed with an audit record.
- Stale-policy and routing faults reconstructed from trace evidence.
- Baseline versus corrected variant evaluated on a held-out family split.
- Reward gaming blocked by non-negotiable policy and authorization gates.
- Versioned canary stopped and rolled back to the prior approved release.
- Local event queue processed into an analytical sink, with an explicit GCP mapping.

See [the demo script](docs/DEMO_SCRIPT.md), [architecture](docs/ARCHITECTURE.md), and [build status](docs/BUILD_STATUS.md).

The original workbook documents and generated evidence are deliberately excluded from this public repository. The canonical engineering specification is [docs/MASTER_BUILD_SPEC.md](docs/MASTER_BUILD_SPEC.md).

## Safety and honesty

- Synthetic data only.
- Tool writes require explicit scope and approval where policy requires it.
- Raw tool arguments are never written to traces; a salted digest and allow-listed metadata are stored instead.
- Cloud adapters fail clearly when dependencies or credentials are absent.
- Terraform is configuration only. Nothing deploys automatically.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and responsible reporting guidance. CI uses immutable action revisions and audits every locked dependency set.

## License

Licensed under the [Apache License 2.0](LICENSE).

