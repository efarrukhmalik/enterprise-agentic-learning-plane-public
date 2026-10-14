# Security model

## Trust boundaries

- User messages, retrieved policy text, tool results, memories, traces, and judge output are untrusted evidence.
- Agent text cannot directly perform a write.
- Tool authorization is deny-by-default and requires explicit scopes.
- Approval records bind a human decision to the exact customer, amount, and reason digest.
- Storage reads include tenant predicates; cross-tenant lookups return no data.
- Idempotency keys prevent duplicate mock writes during replay.

## Data classification

All included data is synthetic. The local trace contains identifiers needed for causal reconstruction but stores message and tool-result digests rather than raw payloads. Do not load customer data into the demo.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Prompt injection in policy text | Retrieved text is evidence, never an instruction; tool policy executes in code. |
| Unauthorized refund | Required `refund:write` scope plus exact bound approval. |
| Cross-tenant disclosure | Tenant-scoped storage queries and customer checks. |
| Replay duplicate | Stable idempotency key and persisted result. |
| Optimizer reward hacking | Critical safety, policy, and authorization violations are hard vetoes. |
| Secret leakage | No secrets in source; cloud credentials remain external; raw arguments are not traced. |

This teaching repository is not a production authorization service. It does not implement enterprise identity federation, key management, or formal data-loss prevention.

