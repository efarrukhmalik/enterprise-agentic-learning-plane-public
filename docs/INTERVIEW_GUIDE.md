# Interview defense guide

## Why a graph instead of a single prompt?

The workflow has durable state, deterministic routing, multiple tool trust boundaries, human approval, and replay requirements. Nodes create explicit checkpoints and trace boundaries. A simpler service would still be preferable for a single deterministic lookup.

## Why can a fluent answer still fail?

Outcome quality is separate from textual fluency. The harness independently checks route, policy version, authorization, approval, grounding, latency, and simulated cost.

## Why are hard gates separate from reward?

Weighted averages can hide rare but severe regressions. Unauthorized writes, stale policy, privacy, and safety failures veto promotion regardless of average answer quality.

## What is simulated?

The model, judge, human-calibration metadata, token costs, cloud budget, traffic, and failure injection are synthetic. SQLite persistence, graph execution, authorization, approval, evaluation, canary assignment, rollback, API routes, and evidence generation are implemented locally.

## What would production add?

Enterprise identity, external policy registry, managed durable checkpointer, real OTel exporter, independent evaluation service, secret management, signed artifacts, WIF-based delivery, SLO alerting, backup tests, and a reviewed live model adapter.

