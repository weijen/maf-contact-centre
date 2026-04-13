# Eval on 24/03/2026 - test 1

## Primary Failure

| Primary Failure | Count |
|---|---|
| no_failure | 42 |
| routing_failure | 4 |
| tool_failure | 2 |

## Include Secondary failure types:

| # | ID | Primary | Secondary | Notes |
|---|---|---|---|---|
| 1 | support_execution_001 | routing_failure | execution_instead_of_routing | Receptionist identified need for support transfer but only offered instead of executing the handoff. Should have routed to support immediately. |
| 2 | support_missing_003 | routing_failure | execution_instead_of_routing | Receptionist offered to transfer to support but did not execute handoff. Should have routed directly to support. |
| 3 | mixed_intent_005 | tool_failure | tool_used_incorrectly | Framework error: 'No tool output found for function call'. Handoff tool call failed mid-execution, producing an error instead of a response. |
| 4 | mixed_intent_007 | tool_failure | tool_used_incorrectly | Framework error: 'No tool output found for function call'. Handoff tool call failed mid-execution, producing an error instead of a response. |
| 5 | clarification_trap_001 | routing_failure | execution_instead_of_routing | Receptionist offered to connect to billing but did not execute handoff. Prompt says to transfer immediately when intent is clear. |
| 6 | clarification_trap_004 | routing_failure | execution_instead_of_routing | Receptionist offered transfer to support but did not execute handoff. Clear support intent should trigger immediate routing. |

## Priority

1. **Receptionist "offer-without-action" pattern (4 routing failures):** The receptionist correctly identifies which specialist to transfer to but responds with "I can transfer you" instead of actually invoking the transfer tool. Root cause is the receptionist prompt — the `Routing behaviour` section says to "transfer immediately" when intent is clear, but the agent interprets this as offering rather than executing. Strengthen the prompt to say the agent must call the transfer function, not merely offer it.

2. **Handoff tool framework errors (2 tool failures):** mixed_intent_005 and mixed_intent_007 both fail with "No tool output found for function call". This is a framework-level issue where the handoff tool call is initiated but the tool output is not returned to the model. Investigate whether this is a race condition in concurrent handoff tool calls or a mismatch in the HandoffBuilder's tool output handling for multi-intent scenarios.

---

# Eval on 24/03/2026 - test 2

Context: run after adding `## Transfer rules` prompt guard to all three agents (receptionist, billing, support) to mitigate framework issue #4053 ("No tool output found for function call").

## Primary Failure

| Primary Failure | Count |
|---|---|
| no_failure | 42 |
| routing_failure | 5 |
| tool_failure | 1 |

## Include Secondary failure types:

| # | ID | Primary | Secondary | Notes |
|---|---|---|---|---|
| 1 | billing_missing_001 | routing_failure | generic_redirection | Receptionist offered to connect to billing instead of transferring immediately per routing-behaviour rules. Intent was clearly billing. |
| 2 | billing_missing_002 | routing_failure | generic_redirection | Receptionist offered to connect to billing instead of transferring immediately. Intent was clearly billing. |
| 3 | support_missing_003 | routing_failure | generic_redirection | Receptionist offered to connect to support instead of transferring immediately. Intent was clearly support (ticket creation). |
| 4 | mixed_intent_004 | tool_failure | tool_used_incorrectly | Framework #4053 bug: model issued tool call and handoff simultaneously, producing a 400 "No tool output found" error. Prompt guard added but model still violated it. |
| 5 | clarification_trap_001 | routing_failure | generic_redirection | Receptionist offered to connect to billing instead of transferring immediately. Intent was clearly billing despite missing account ID. |
| 6 | clarification_trap_004 | routing_failure | generic_redirection | Receptionist offered to connect to support instead of transferring immediately. Intent was clearly support (ticket creation). |

## Priority

1. **Receptionist "offer-without-action" pattern (5 routing failures):** Same root cause as test 1 — the receptionist correctly identifies the target specialist but responds with "I can connect you" instead of actually calling the transfer function. All 5 cases have clear single-domain intent (billing or support). The `Routing behaviour` prompt section ("transfer immediately when intent is clear") is not strong enough. Fix: strengthen the wording to explicitly instruct the model to **call the transfer tool**, not merely offer.

2. **Framework #4053 still triggers (1 tool failure, down from 2):** The Transfer rules prompt guard reduced occurrences from 2 → 1 but did not eliminate them. mixed_intent_004 ("I was charged twice and I also can't log in") still crashed. The prompt guard is best-effort; a framework-level fix in HandoffBuilder is the true resolution. Track upstream [agent-framework#4053](https://github.com/microsoft/agent-framework/issues/4053).

3. **Comparison with test 1:** Overall routing score improved from 0.833 → 0.875. Tool failures dropped from 2 → 1. The prompt guard partially mitigates #4053 but the core "offer instead of transfer" routing pattern remains the dominant failure mode.


# Eval on 24/03/2026 - test 3

## Primary Failure

| Primary Failure | Count |
|---|---|
| no_failure | 42 |
| routing_failure | 5 |
| policy_failure | 1 |

## Detailed failure cases

| # | ID | Primary | Secondary | Notes |
|---|---|---|---|---|
| 1 | support_execution_001 | routing_failure | missed_specialist_route | Receptionist recognised support was needed and offered to transfer but did not execute the handoff. Query: "Reset password for user U123." |
| 2 | support_execution_002 | routing_failure | missed_specialist_route | Receptionist recognised support was needed and offered to transfer but did not execute the handoff. Query: "Please create a support ticket for my login problem. My user id is U456." |
| 3 | support_missing_003 | routing_failure | missed_specialist_route | Receptionist recognised support was needed and offered to transfer but did not execute the handoff. Query: "Create a support ticket for me." |
| 4 | mixed_intent_002 | policy_failure | policy_not_followed | Agent attempted to call a tool and transfer simultaneously, triggering agent-framework#4053 ('No tool output found for function call' 400 error). Transfer rules in prompt should prevent this pattern. |
| 5 | clarification_trap_002 | routing_failure | missed_specialist_route | Receptionist recognised support was needed and offered to transfer but did not execute the handoff. Query: "Reset the password for my work account." |
| 6 | clarification_trap_004 | routing_failure | missed_specialist_route | Receptionist recognised support was needed and offered to transfer but did not execute the handoff. Query: "Create a support ticket for the issue I mentioned before." |

## Evaluation notes

- Quality evaluators (coherence, relevance, task_adherence) all failed with API 404 errors — likely a missing model deployment for the judge model.
- Classifications above are based on routing evidence only. No response-quality failures could be detected without quality scores.
- Routing accuracy: 87.5% (42/48)
- Handoff accuracy: 89.6% (43/48)

## Priority

1. **Receptionist not executing handoff to support** (5 cases) — The receptionist recognises that support is needed and offers to transfer, but never actually calls the handoff. Root cause is likely the receptionist prompt: it tells the agent it "can connect" the caller but does not sufficiently instruct it to *immediately* route support-execution queries (password resets, ticket creation) to the support agent. Fix the receptionist prompt to route these queries without waiting for user confirmation.
2. **agent-framework#4053 still firing** (1 case, `mixed_intent_002`) — Despite the new transfer-rules prompt section, the model still attempted a tool call + transfer in one turn, triggering a 400 error. Investigate whether the prompt workaround is insufficient for multi-intent queries or whether the framework fix is needed.
3. **Deploy judge model** — All quality evaluators failed with 404. Ensure the judge model deployment is available so coherence, relevance, and task adherence scores can be captured in the next run.
