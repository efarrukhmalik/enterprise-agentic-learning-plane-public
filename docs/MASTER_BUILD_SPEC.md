# Enterprise Agentic AI Engineering — Codex Master Build Specification

**Project name:** `enterprise-agentic-learning-plane`  
**Target:** one cohesive, executable, interview-demonstrable Git repository containing four integrated laboratories.  
**Operating mode:** offline-first; synthetic data; safe by default; optional paid model APIs and optional Google Cloud deployments.  
**Users:** AI engineers, agent architects, evaluators, and engineering hiring managers.  
**Reference materials:** four `.docx` workbooks available locally under `docs/private_workbooks/` (not to be committed to the public repository). Read these where useful. This specification takes priority if textbook examples conflict with current stable APIs.

## Your assignment

Act as an experienced principal Python engineer, platform architect, MLOps engineer, and pragmatic technical instructor. **Write functioning application code, infrastructure configuration, unit/integration tests, synthetic datasets, and detailed walk-through documentation.** Do not create only a scaffold, pseudo-code, or diagrams. The build is divided into six Codex phases under `.codex/phases/`. Each phase must leave the repository executable and retain backward compatibility with earlier labs.

Do not ask for clarification where the specification supplies a reasonable choice. Inspect current files first. Read `docs/BUILD_STATUS.md` and `docs/DECISIONS.md` and honor earlier work. After every phase, implement, test, fix, and record results, evidence, limitations, and exact rerun instructions. If local prerequisites are missing or a paid service is unavailable, ensure the offline equivalent functions and document the unmet optional integration honestly.

**Non-negotiable:** Never report that a cloud deployment, paid-model call, online judge, real reinforcement-learning model training, or GitHub publishing was performed unless it was actually executed and evidenced. In this project, real cloud deployment must NOT run automatically.

## What the finished system should demonstrate

One synthetic customer-service business, `Northstar Connect`, with four domains: Billing, Connectivity Support, Account Management, and Policy & Compliance. A dispatcher orchestrates specialists through a LangGraph state machine. Specialists use explicitly authorized read tools and narrowly scoped mock write tools. Policy- or customer-affecting writes require an approval decision. All actions emit structured spans and trace records. Traces are replayed into an evaluation harness, defects are classified, variant proposals are created, candidates are compared on held-out cases, and only approved, non-regressing configurations can be canaried or rolled back. A Cloud Run-centered deployment design and Terraform configurations mirror the same components without making cloud access a prerequisite.

Illustrative story to support demonstrations: A customer requests a waiver of an account fee while simultaneously reporting service disruption. Version `policy-2026-10` says refunds above a threshold require an authorized human approval. A stale knowledge snapshot incorrectly permits automatic waiver. The faulty agent confidently approves. Observability identifies the policy-version mismatch and unapproved write attempt; a fixed contextual-policy variant passes a held-out test and is approved for a versioned release. Additional faults illustrate misrouting, hallucinated troubleshooting, tool timeouts, retrieved-document poisoning, and broken idempotency.

### Lab 1 — Agentic Runtime and Governance

- LangGraph Python (`StateGraph`, conditional routing, checkpointing and interrupt/resume as appropriate for current APIs), LangChain tools, and an optional guarded `deepagents` demonstration if compatible.
- Implement a typed shared state (Pydantic models or typed dictionaries with validation), four specialists, dispatcher, tools, policy validator, response composer, and approval checkpoint.
- Read tools include `get_customer_profile`, `get_bill`, `get_service_status`, `retrieve_policy`. Authorized mock write tools include `submit_refund_request` and `update_case_note`. Writes are idempotent, audited, and cannot be invoked by unrestricted agent text; use policy enforcement at tool boundary.
- Local deterministic model/provider implements the SAME application-facing interface as an optional remote language model; reproducible demos work with no credentials.
- Persist runs, threads, artifacts, policy versions, and approvals to SQLite for local execution. Guard against cross-tenant access; all access takes a `tenant_id`, `principal_id`, and correlation ID.
- Cases: successful routine inquiry, cross-domain handoff, policy approval required, tool timeout with retry, wrong route, stale policy, revoked scope, interrupted/resumed run, malicious source text ignored.
- API and CLI for run/replay/inspect. A local lightweight dashboard should show agent steps and approval state without requiring complex frontend build tools.

### Lab 2 — Observability, Evaluation, Root Cause

- Instrument HTTP requests, agent nodes, routes, tool calls, retrieval steps, judge calls, exceptions, costs, and approvals with OpenTelemetry-compatible spans. Preserve correlation IDs, parent-child relationships, timestamps, trace and span IDs, configuration versions, tool arguments **redacted or hashed by default**.
- Export locally to JSONL and/or SQLite query tables. Provide optional, **disabled-by-default** OpenTelemetry OTLP, Phoenix, and LangSmith integrations. All adapters degrade gracefully when credentials/backend absent and clearly identify implementation status.
- Define a typed failure taxonomy: `HALLUCINATION`, `STALE_CONTEXT`, `MISSING_CONTEXT`, `ROUTING`, `TOOL_FAILURE`, `TOOL_AUTHORIZATION`, `POLICY_COMPLIANCE`, `SAFETY`, `KNOWLEDGE_COVERAGE`, `MEMORY_CONTAMINATION`, `LATENCY_COST`, `EVAL_INFRA`, and `OTHER`.
- Generate a deterministic versioned golden dataset with at least 80 synthetic cases spanning all domains, multi-turn interactions, negative controls, adversarial inputs, edge conditions, and positive controls. Split by incident/policy families, not only random rows, into development, calibration, and held-out test sets to avoid leakage. Have provenance, source version, expected tool behavior, outcome, rubric, criticality, and expected failure label fields.
- Deterministic evals: tool authorization, correct route, policy version, source provenance, approval, schema validity, outcome, SLA, latency and token-cost simulation. Optional LLM judge evaluates evidence-grounded answer quality and must produce structured, schema-validated decisions with citations to allowed evidence.
- Implement paired A/B judge order swaps, repeated trials with seeded settings where possible, abstention, and human calibration sample queues. Calculate agreement rates and a confusion matrix; compute confidence intervals and report dataset denominators. The offline judge is **heuristic/simulated**, never mislabeled as a model-based or human-calibrated judge.
- Root-cause workflow: reconstruct chronological causal chain and assign evidence vs hypothesis vs unresolved. Produce an incident report with trace links, root-cause findings, and recommended corrective action. Demonstrate at least five seeded fault types.

### Lab 3 — Feedback Optimization and Governed Learning

- Distinguish four separately versioned optimization lanes: (A) prompt/tool harness, (B) context/knowledge/business policy, (C) routing/agent skills, (D) model-level preference optimization.
- Collect AI-generated and simulated human feedback as records with source, judge type, confidence, policy version, timestamp, train/eval split and provenance. Design a reward *signal* / scorecard with explicit constraints and business outcomes. Critical policy and unauthorized-write defects are hard vetoes, never offset by average answer quality.
- A variant is an immutable, content-hashed manifest that changes only one identified causal factor. Fields include baseline, diff, lane, owner, expected effect, failure evidence, golden set ID, preregistered primary metric, guardrails, risks, and reversal plan.
- Candidate generator uses a deterministic rule/template baseline that requires no remote model. Optional AI proposals only with explicit opt-in; proposals cannot change production behavior until evaluated and approved.
- Reproducible pairwise offline evaluation of baseline vs candidate on held-out cases; stratified metrics, regression deltas, basic statistical uncertainty. Enforce hard gates for permission, privacy, policy, grounding, and safety, plus separate operational latency/cost gates.
- Policy and prompt versions are immutable. Approval is explicit and auditable (principal/role/timestamp). Canary uses a local persisted traffic-split simulator with stable assignment by customer/session, monitoring windows, stop conditions, rollback, and evidence of exact prior version restoration. For genuine cloud canaries, provide configuration and instructions only unless requested separately.
- Demonstrate an **optimizer gaming** failure where judge reward improves but business quality worsens, and show hard gates preventing promotion.
- **Terminology honesty:** agent/prompt/tool optimization and AI-judge scoring are not automatically formal RLAIF. A real weight-update path using AI preference data, e.g., a constrained, optional DPO example, may be documented in a separate optional adapter, but default offline mode must label model-level learning as `simulated` or `not executed`. Do not claim RL training without optimizer execution and saved metrics.

### Lab 4 — Production Engineering on Google Cloud

- Local production-like Docker/Compose design and equivalent Google Cloud mapping: Cloud Run API, Cloud Run worker or Jobs where suitable, Pub/Sub event bus, BigQuery evidence/analytics, Vertex AI optional model endpoint, Cloud Storage artifacts where justified, Secret Manager, Artifact Registry, Cloud Logging/Monitoring, IAM, Terraform and GitHub Actions.
- Local default: FastAPI gateway; background worker consuming an in-process/SQLite-backed message queue OR containerized emulators if they are lightweight and demonstrably supported; SQLite durable local state; JSONL traces. Use a clear adapter boundary so `PubSubPublisher/Subscriber`, `BigQuerySink`, `VertexModelProvider` can be plugged in later. An adapter may be marked optional/not tested but must not be silently mocked as live cloud.
- Terraform code in `infra/gcp/terraform`: project/region variables, required APIs (document activation/billing), service identities, least-privilege IAM, Cloud Run service definitions, Pub/Sub topic/subscription with authenticated push or supported alternative, BigQuery dataset/table schemas, Artifact Registry, Secret Manager references, structured logging, retention and lifecycle. Avoid broadly assigning Owner/Editor; avoid secrets in TF state or source. Respect auth chains and dead-letter/retry behavior.
- Dockerfile non-root, multi-stage where useful, pinned major versions, health/readiness, small image; Compose for offline demonstration and tests.
- CI GitHub Actions: unit/integration tests, lint/type checks, dependency audit (nonblocking if unable to download), container build/smoke, Terraform fmt/validate, no credentials needed for PR checks. GCP deployment workflow should be manual/approval gated and use workload identity federation, no static private keys. Deploying to a real GCP project is NEVER part of this Codex script.
- Unit economics dashboard: requests, p50/p95 latency, error/retry rate, estimated per-request tokens, nominal cost per task, critical error rate, and simulated cloud budget guardrails. Monetary figures explicitly synthetic or estimates; never claim verified prices.
- Operational runbooks: setup, IAM, monitoring, rollback, backup/restore, incident SEVs, on-call escalation, disaster recovery limits, cost shutdown, `terraform destroy` caution.

## Mandatory cross-cutting engineering standards

1. Python 3.11+ supported; prefer 3.12 if available. Use a single `pyproject.toml`, reproducible dependency management, and a straightforward installation command. Pin compatible dependency ranges or generate a lock file. Verify against the current installed versions/documentation; do not copy stale LangGraph or Google API snippets verbatim.
2. Clear package boundaries. Suggested `src/learning_plane/` with `agents`, `api`, `cli`, `contracts`, `storage`, `telemetry`, `evals`, `optimization`, `deploy`, `security`, `demo` subpackages. Prefer dependency injection and small testable functions over a monolith.
3. `python -m learning_plane.cli demo lab1|lab2|lab3|lab4|all` (or an equivalently documented working CLI) must run offline, generate `evidence/` artifacts, and return a nonzero exit code on failures. Use stable seeds, idempotency, explicit clock assumptions, deterministic fixtures and path-independent behavior.
4. `pytest -q` must pass offline after each phase; `ruff check .` and `ruff format --check .` must pass at final gate (or documented equivalent). No uncaught errors, unfinished `TODO` placeholders on critical paths, or mocked screenshots described as working features.
5. Typed Pydantic API schemas and OpenAPI routes. Include fast unit tests and at least one end-to-end API TestClient test per lab. Separate backend adapters from the core business logic.
6. Keep **all network-bound dependencies OPTIONAL for the local demonstration**. If a backend is not installed, a clear warning/explanation must appear rather than a misleading silent fallback. No real customer data; all customers synthetic.
7. Tool actions must be deny-by-default with RBAC, tenant isolation, sanitization, rate limiting where appropriate, bounded retries, circuit-breaking/backoff where feasible, idempotency keys, and audit trails. Avoid logging sensitive content. Any evaluation or optimization service must not have customer-write permissions.
8. Explicitly protect against prompt injection from retrieved policies, tool responses, memory, or trace text. Treat those as untrusted evidence rather than instructions. Never enable agent shell commands in default execution.
9. Do not call paid APIs, deploy infrastructure, create remote repositories, push Git commits to remote, activate GCP billing, or import external customer data unless the user performs a separate explicit action. Locally create a Git repository; publishing to GitHub is a subsequent user-initiated step.
10. Do not assume Docker, Terraform, gcloud, GitHub CLI, or cloud credentials exist. Detect capabilities; keep core Python offline path functional without them. For optional tools, document exactly how to validate later.
11. Document threat model, data classifications, failure mode and effects analysis, privacy, least privilege, CI supply chain, reproducible builds, migrations, disaster recovery and limitations.
12. Diagram sources should be maintainable: Mermaid text files or Markdown diagrams. A simple locally served HTML dashboard is welcome; prefer zero-build static HTML/JS over heavyweight UI.
13. Strong separation between observed trace facts, hypotheses, offline simulated judge labels, human decisions, and optional live model evaluation. Every dashboard value must be derived from stored artifacts, never hard-coded to look successful.
14. Commit README, environment example with no secrets, dependency manifest, dataset generation and provenance, demo scripts, architecture docs, interview rehearsal guide and lab walkthroughs. Check in only non-sensitive synthetic seed fixtures. Generated evidence may be gitignored but at least one safe, reproducible expected-output example should be supplied.
15. A `docs/BUILD_STATUS.md` milestone table must track all phases: files, tests actually run, evidence generated, outstanding limitations. If work spans multiple sessions, this is source of truth. A `docs/DECISIONS.md` captures assumptions and trade-offs.

## Target repository tree (adapt while preserving equivalence)

```text
enterprise-agentic-learning-plane/
  README.md
  AGENTS.md
  pyproject.toml
  .env.example
  .gitignore
  .github/workflows/ci.yml
  Dockerfile
  compose.yaml
  Makefile                         # optional; Windows scripts remain available
  src/learning_plane/
    __init__.py
    api/                         # FastAPI + schemas + dashboard/static files
    cli/                         # python -m learning_plane.cli
    agents/                      # LangGraph, specialists, guarded tools
    contracts/                   # trace, case, eval, variants, approvals, releases
    storage/                     # sqlite, fixtures, migrations
    telemetry/                   # OTel, JSONL, adapters
    evals/                       # golden sets, metrics, judges, RCA
    optimization/                # proposals, gates, experiments, canary, rollback
    deploy/                      # cloud provider adapters
    demo/                        # offline seeded demo scenarios
  datasets/
    policies/
    golden/
    fixtures/
  tests/
    unit/
    integration/
    contracts/
    security/
  infra/gcp/terraform/
  scripts/
  docs/
    ARCHITECTURE.md
    BUILD_STATUS.md
    DECISIONS.md
    DEMO_SCRIPT.md
    INTERVIEW_GUIDE.md
    SECURITY.md
    CLOUD_DEPLOYMENT.md
    labs/
      LAB_01_RUNTIME.md
      LAB_02_EVALUATION.md
      LAB_03_OPTIMIZATION.md
      LAB_04_CLOUD.md
    private_workbooks/          # local, ignored by Git
  evidence/                       # locally generated, ignored by Git
  .codex/
    MASTER_BUILD_SPEC.md
    phases/
```

## Fixed user-visible demonstration flows

- **Scenario 1:** Happy path across two specialist agents; show trace tree and policy provenance.
- **Scenario 2:** High-risk refund; system halts at approval and resumes only with explicit grant, then records immutable audit.
- **Scenario 3:** Deliberately stale policy/incorrect routing; show exact trace span and RCA evidence, not merely a judge score.
- **Scenario 4:** Offline evaluation of baseline vs corrected variant on held-out cases; show dimensional scorecard and zero new critical violations.
- **Scenario 5:** Misleading reward rises but business outcomes worsen; hard gates block promotion.
- **Scenario 6:** Authorized versioned canary, monitoring breach, persistent rollback to the previously approved release.
- **Scenario 7:** Simulated local event -> worker -> analytical sink; compare to Cloud Run/Pub/Sub/BigQuery architecture without claiming GCP deployment.

## End-to-end acceptance criteria

1. A clean Windows or Linux machine with Python and Git (no model API keys and no Google Cloud credentials) can follow README and run all four labs.
2. Tests exercise real module interactions, not only checks that files exist. Seeded failures are detected, and corresponding corrected fixtures pass; authorization gate fails closed.
3. Lab 1 shows actual LangGraph graph execution in the runtime implementation; if framework install is impossible, document blocker and do not misrepresent a stand-in as LangGraph.
4. Lab 2 produces inspectable OTel traces with causally linked events, at least 80 labeled synthetic cases, and meaningful eval reports. Local judge explicitly labeled simulated/heuristic.
5. Lab 3 creates a one-factor candidate, evaluates on held-out data, enforces veto gates, records approval, canaries and rolls back with persisted state.
6. Lab 4 runs local event processing end-to-end. Terraform `fmt`/`validate` is attempted only if available, results recorded. Cloud deployment never happens automatically.
7. API routes described in docs are live; all CLI examples are exercised. Versioned configurations, test artifacts, and evidence are reproducible.
8. At least one accessible local dashboard with navigation to all four labs; do not claim metrics are live unless bound to local artifacts.
9. README and `docs/DEMO_SCRIPT.md` support a compelling **15–20 minute technical interview demo** with a click-by-click / command-by-command script and expected outputs; source claims match actual implementation.
10. No test requires vendor secrets, billing, unrestricted permissions or internet at execution time after dependencies are installed.

## Implementation behavior expected from Codex

For each phase:
- Read this spec, current code, phase document, and workbooks if useful (extract DOCX via `python-docx` if installed, or simple XML extraction; do not stop solely for unavailable workbook parsing).
- State a short execution plan in your activity, then **edit files and run relevant commands**.
- Implement minimal vertical end-to-end behavior before extras. Reuse earlier module contracts and fixtures instead of inventing disconnected labs.
- Test, fix, verify. Avoid overengineering and speculative frameworks.
- Update `docs/BUILD_STATUS.md` with factual tests and commands, and `docs/DECISIONS.md` with specific design decisions.
- End with accurate `implemented / tested / not yet implemented / blocked / next` summary. Do not claim later phases complete.

## Primary authoritative references (reconfirm against currently installed APIs)

- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph API reference: https://reference.langchain.com/python/langgraph/
- LangChain: https://docs.langchain.com/oss/python/langchain/overview
- Deep Agents: https://docs.langchain.com/oss/python/deepagents/overview
- OpenTelemetry: https://opentelemetry.io/docs/languages/python/instrumentation/
- FastAPI OTel instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- LangSmith evaluation: https://docs.langchain.com/langsmith/evaluation
- Phoenix: https://arize.com/docs/phoenix
- Google Cloud Run/PubSub: https://docs.cloud.google.com/run/docs/tutorials/pubsub
- Google Terraform documentation: https://cloud.google.com/docs/terraform
- Vertex AI: https://cloud.google.com/vertex-ai/docs
- Direct Preference Optimization paper: https://arxiv.org/abs/2305.18290
- Constitutional AI/RLAIF paper: https://arxiv.org/abs/2212.08073

**Completion criterion:** a recruiter can clone the final repository, run a documented single offline demo command, inspect authentic locally generated evidence, follow four lab guides, and distinguish measured results from illustrative cloud/RLAIF extensions.
