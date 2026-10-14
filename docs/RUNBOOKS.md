# Operational runbooks

## Local setup

Create a Python 3.11 or newer environment, install the development extras, run the checks, and then run the all-labs demo. Keep remote model access disabled unless a reviewed adapter is deliberately configured.

## Incident severity

- SEV 1: unauthorized write, cross-tenant disclosure, or safety failure. Stop traffic and preserve evidence.
- SEV 2: policy-version mismatch, widespread incorrect routing, or failed rollback.
- SEV 3: elevated latency, cost, or retry rate without incorrect customer outcome.

## Rollback

Stop the canary when a hard threshold is breached. Restore the exact prior version from the persisted release record, verify the version, and retain the failed candidate and trace evidence.

## Backup and restore

Stop writers, copy the SQLite database and JSONL evidence, record checksums, and restart. Restore into an isolated directory first, run a SQLite integrity check, and replay a read-only demo before reopening writes. The project has no automated remote backup.

## Disaster recovery limits

SQLite and local files are single-host teaching components. They do not provide multi-region recovery, managed encryption keys, or continuous point-in-time recovery.

## Cost shutdown

The local demo has no paid API calls. For an operator-deployed cloud environment, stop Cloud Run traffic, subscriptions, model endpoints, and scheduled work; inspect retained BigQuery, Pub/Sub, and Artifact Registry data before deletion.
