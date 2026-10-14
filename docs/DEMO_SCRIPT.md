# 15 minute demonstration

## 1. Start with the architecture

Open `docs/ARCHITECTURE.md`. Explain that the system separates execution, evidence, optimization, and release authority.

## 2. Run all labs

```powershell
python -m learning_plane.cli demo all
```

Expected: exit code 0 and JSON showing `status: completed`. Open `evidence/demo_all.json`.

## 3. Show governed execution

Open `evidence/lab1_runtime.json`. Point to the first run stopping at `approval_required`, the bound approval record, the resumed write, and the identical idempotent replay result. Show the multi-domain route.

## 4. Show evidence and root cause

Open `evidence/traces.jsonl` and `evidence/lab2_evaluation.json`. Explain trace and span IDs, policy version evidence, the 96-case family split, denominator, confidence interval, and the difference between observed facts and hypotheses.

## 5. Show optimization authority boundaries

Open `evidence/lab3_optimization.json`. Show the content-hashed one-factor variant, hard release gates, explicit approval, canary limits, and verified rollback. Emphasize that the reward-gaming candidate was vetoed and no RL training occurred.

## 6. Show cloud readiness honestly

Open `evidence/lab4_cloud_readiness.json`, `compose.yaml`, and `infra/gcp/terraform/main.tf`. Explain the local event-to-analytics path and its GCP mapping. State clearly that no cloud deployment was performed.

## 7. Close with verification

```powershell
pytest -q
ruff check .
ruff format --check .
```

Open the local dashboard with `uvicorn learning_plane.api.app:app --reload` if time permits.

