# Engineering decisions

| ID | Decision | Reason |
|---|---|---|
| D-001 | Use one deterministic Northstar Connect domain across all labs. | Evidence and versions remain traceable end to end. |
| D-002 | Use LangGraph when installed, with an explicit manual fallback. | The packaged demo remains inspectable if installation is unavailable, without mislabeling the fallback. |
| D-003 | Store local state in SQLite and traces in SQLite plus JSONL. | Durable, dependency-light, and easy to inspect. |
| D-004 | Bind approval to a digest of exact write parameters. | Prevents reusing approval after amount, account, or reason changes. |
| D-005 | Split the synthetic dataset by incident families. | Reduces leakage compared with a naive random-row split. |
| D-006 | Treat policy, safety, and authorization failures as vetoes. | Average quality cannot compensate for critical violations. |
| D-007 | Make live cloud adapters fail explicitly. | Avoids implying that local simulation is a deployed integration. |
| D-008 | Keep source workbooks outside Git. | Protects private source material and repository size. |

