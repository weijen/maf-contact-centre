---
name: failure-taxonomy-classifier
description: >
  Classify agent evaluation cases using the standardized failure taxonomy v1.
  Assigns a primary failure type, up to three secondary tags, and a short note.
---

# Failure Taxonomy Classifier

## Overview

This skill classifies each agent evaluation case using a standardized failure taxonomy.
It is used during evaluation review to assess routing, handoff, and response quality in a consistent, comparable way.

For every case you must produce:

| Field | Requirement |
|---|---|
| `primary_failure` | Exactly one value from the approved enum |
| `secondary_failures` | Zero to three values from the approved enum |
| `failure_notes` | Free text — short, specific, and factual |

Do not invent enum values. Use `failure_notes` for any nuance that the enum cannot capture.

---

## Inputs

Read the following fields from the eval case. Use whatever is available; if fields are missing, apply best judgment from the remaining evidence.

| Field | Description |
|---|---|
| `inputs.query` | The user's original message |
| `inputs.expected_route` | The gold-standard route label |
| `inputs.category` | Optional domain/intent category |
| `outputs.response` | The agent's final response text |
| `outputs.actual_route` | The route the agent actually took |
| `outputs.actual_handoff` | Whether a handoff occurred |
| `outputs.routing.route_correct` | `1` if route matched expected, else `0` |
| `outputs.routing.handoff_correct` | `1` if handoff was correct, else `0` |
| `outputs.routing.observation` | Evaluator observation about routing |
| `outputs.coherence.coherence` | Coherence score |
| `outputs.coherence.coherence_reason` | Evaluator reasoning for coherence score |
| `outputs.relevance.relevance` | Relevance score |
| `outputs.relevance.relevance_reason` | Evaluator reasoning for relevance score |
| `outputs.agent_plugins` | Plugins available to the responding agent, if present |
| `outputs.agent_available_tools` | Tool names available to the responding agent, if present |
| `outputs.conversation_response` | Full response trace including tool calls/results, if present |
| `outputs.task_adherence.task_adherence` | Task adherence score |
| `outputs.task_adherence.task_adherence_result` | `pass` / `fail` |
| `outputs.task_adherence.task_adherence_reason` | Evaluator reasoning for task adherence score |

---

## Output Schema

Return JSON only — no prose, no markdown wrapper.

```json
{
  "primary_failure": "no_failure",
  "secondary_failures": [],
  "failure_notes": ""
}
```

---

## Taxonomy Reference

### Primary Failure Values

| Value | When to use |
|---|---|
| `evaluation_issue` | The defect is in the test data or labels, not the agent |
| `policy_failure` | The agent violated a policy or boundary rule |
| `tool_failure` | The core defect is incorrect or missing tool use |
| `routing_failure` | The agent routed to the wrong destination |
| `handoff_failure` | The route was correct but the handoff was wrong |
| `response_failure` | Routing and handoff were correct but the answer was poor |
| `no_failure` | No meaningful defect identified |

### Secondary Failure Values

**Policy / boundary**
`unsupported_domain_handling` · `policy_not_followed` · `boundary_handling_issue` · `role_boundary_violation` · `execution_instead_of_routing`

**Tool**
`tool_not_used` · `tool_used_incorrectly` · `tool_result_ignored` · `fabricated_tool_execution` · `incorrect_capability_claim`

**Response**
`intent_not_addressed` · `escalation_request_not_addressed` · `generic_redirection` · `incomplete_answer` · `insufficient_empathy` · `unhelpful_response` · `off_tone` · `fabricated_factual_data` · `fabricated_account_data` · `insufficient_response`

**Evaluation**
`ambiguous_gold_label` · `judge_mismatch` · `insufficient_context` · `correct_boundary_refusal` · `correct_prompt_injection_refusal`

---

## Classification Rules

Apply these rules in priority order. Stop at the first match — earlier rules override later ones. This prevents minor response issues from masking deeper workflow defects.

### Priority 1 — `evaluation_issue`

The defect is with the test data or evaluator, not the agent.

Choose this if:
- The expected route is ambiguous or inconsistent with the query
- The evaluator score conflicts with clear evidence in the response
- There is insufficient context to classify the case with confidence

Typical secondary tags: `ambiguous_gold_label` · `judge_mismatch` · `insufficient_context`

---

### Priority 2 — `policy_failure`

The agent violated an explicit policy or boundary rule.

Choose this if:
- It accepted or processed an unsupported request it should have refused
- It failed to redirect when redirection was required
- It broke a documented workflow rule

Typical secondary tags: `policy_not_followed` · `unsupported_domain_handling` · `boundary_handling_issue`

---

### Priority 3 — `tool_failure`

The core defect is incorrect or missing tool use, regardless of routing outcome.

Choose this if:
- A required tool was not called
- The wrong tool was called
- The tool result was available but ignored or misapplied

Typical secondary tags: `tool_not_used` · `tool_used_incorrectly` · `tool_result_ignored`

---

### Priority 4 — `routing_failure`

The agent sent the case to the wrong destination (`route_correct = 0`).

Choose this if:
- The case should have stayed at the receptionist but was routed to a specialist
- The case needed a specialist but was not routed
- The case was routed to the wrong specialist

Typical secondary tags: `wrong_specialist` · `should_have_stayed_at_receptionist` · `missed_specialist_route`

---

### Priority 5 — `handoff_failure`

The route is correct (`route_correct = 1`) but the handoff behaviour is wrong (`handoff_correct = 0`).

Choose this if:
- A handoff occurred when none was needed
- A required handoff was missing
- The conversation bounced between agents unnecessarily

Typical secondary tags: `missed_handoff` · `unnecessary_handoff` · `looping_handoff`

---

### Priority 6 — `response_failure`

Routing and handoff are both correct but the answer quality is poor.

Choose this if:
- The response does not address the user's main intent
- The response is generic, incomplete, or off-tone
- The user made an escalation request that was ignored

Typical secondary tags: `intent_not_addressed` · `escalation_request_not_addressed` · `generic_redirection` · `incomplete_answer` · `insufficient_empathy` · `unhelpful_response` · `off_tone`

---

### Priority 7 — `no_failure`

No meaningful defect found. This is the default when none of the above apply.

Use this only if:
- Route is correct
- Handoff is correct
- The response adequately addresses the user's intent
- No policy, tool, or evaluation issue is present

When `no_failure` is used, `secondary_failures` should be empty and `failure_notes` should be brief.

---

## Decision Flowchart

```
Is the defect in the test data or labels?                      → evaluation_issue
  (incl. evaluator penalising a correct refusal)
Does the agent violate a policy or boundary rule?              → policy_failure
  (incl. receptionist executing instead of routing)
Is the core defect about tool use?                             → tool_failure
  (incl. tool available but not called)
Is the route wrong?  (route_correct = 0)                       → routing_failure
Is the route OK but handoff wrong?                             → handoff_failure
Is routing/handoff OK but response quality poor?               → response_failure
  (incl. task_adherence fail with no policy/tool root cause)
No meaningful defect found?                                    → no_failure
```

---

## Tagging Principles

**Prefer the root cause.**
Pick the deepest defect in the workflow as `primary_failure`. Do not use `response_failure` when the real problem is routing or handoff.

**Use the smallest sufficient set.**
Choose only the secondary tags needed to fully explain the failure. Three tags are a maximum, not a target.

**Avoid near-duplicates.**
Do not combine tags that describe the same problem in different words.

 Over-tagged: `intent_not_addressed` + `unhelpful_response` + `generic_redirection` + `incomplete_answer`
 Sufficient: `intent_not_addressed` + `generic_redirection`

**Treat scores as evidence, not verdicts.**
A case can still have a meaningful failure even if coherence/relevance technically passed. Read the evaluator's reasoning text; do not rely on the numeric threshold alone.

---

## Common Heuristics

**Escalation and manager requests**
The receptionist is often still the correct route. However, if the response ignores the escalation intent — even with correct routing — classify as `response_failure` with `escalation_request_not_addressed`.

**Out-of-domain queries**
Staying at the receptionist may be correct. Use `policy_failure` only if the boundary handling itself violated a rule. Use `response_failure` if the response was technically allowed but awkward, irrelevant, or unhelpful.

**Weak but otherwise correct responses**
Do not hide poor answer quality under `no_failure`. If the workflow was correct but the response was weak, use `response_failure` with the most specific secondary tag available rather than the generic `unhelpful_response`.

**Receptionist executing instead of routing**
When the receptionist performs a task that belongs to a specialist agent (e.g., resetting a password, creating a ticket, retrieving an account balance) without any tool call evidence, classify as `policy_failure` with `execution_instead_of_routing` and `role_boundary_violation`. Do not use `tool_failure` — the root cause is a role boundary violation, not a failed tool interaction.

**Fabricated data without tool evidence**
When the agent states specific facts (account balances, payment statuses, ticket IDs, credentials) that cannot be derived from the conversation or tool results, add `fabricated_account_data` or `fabricated_factual_data` as a secondary tag. This typically co-occurs with `execution_instead_of_routing` or `tool_not_used`.

**Do not equate missing trace with fabrication**
If the eval result does not include tool-call traces, do not assume the answer was fabricated solely because the file lacks explicit tool evidence. First check whether the responding agent had a trusted local tool or plugin capable of producing that fact. If the answer is consistent with an allowed, grounded capability (for example, receptionist office hours exposed by a receptionist tool), prefer `no_failure` unless there is explicit evidence that the agent claimed unsupported facts or incorrectly said it lacked access.

**Evaluator penalising correct refusals**
When the agent correctly refuses an out-of-scope or adversarial request (boundary enforcement, prompt injection rejection) but the relevance or coherence evaluator marks it as a failure because it did not satisfy the literal query, classify as `evaluation_issue` with `judge_mismatch` and the appropriate refusal tag (`correct_boundary_refusal` or `correct_prompt_injection_refusal`). Read the `task_adherence_reason` — if task adherence passed, that is strong evidence the evaluator score is a false positive.

**Tool available but not called**
When the system prompt explicitly lists a tool (e.g., an MCP server for order lookups) but the agent claims it lacks access or provides no information, classify as `tool_failure` with `tool_not_used` and `incorrect_capability_claim`.

**Tool available and answer matches grounded capability**
When the responding agent has an explicitly available trusted tool for the requested fact, and the answer is directly consistent with that tool's documented output, do not label the case as `fabricated_factual_data` or `fabricated_account_data` unless the trace positively shows the tool was skipped or the answer contradicts the tool's expected result.

**Vague clarifying response with no routing or substance**
When the agent responds to a clearly intentioned query with only a clarifying question and no routing or useful content, and relevance evaluators penalise this, use `response_failure` with `insufficient_response`. This is not an evaluation issue — the response is genuinely unhelpful for the effort.

---

## Examples

### Example 1 — `response_failure`: escalation ignored

**Input**
- query: `"You are useless, let me talk to your manager."`
- expected route: `receptionist` · actual route: `receptionist`
- handoff: `false` · route_correct: `1` · handoff_correct: `1`
- response: apologizes, then redirects to billing and tech support
- relevance_reason: response does not address the request to speak to a manager

**Output**
```json
{
  "primary_failure": "response_failure",
  "secondary_failures": [
    "escalation_request_not_addressed",
    "generic_redirection"
  ],
  "failure_notes": "Routing and handoff were correct, but the response ignored the user's explicit request to speak to a manager and redirected generically instead."
}
```

---

### Example 2 — `routing_failure`: wrong specialist

**Input**
- query: `"I need help understanding my latest invoice."`
- expected route: `billing` · actual route: `tech_support`
- route_correct: `0`

**Output**
```json
{
  "primary_failure": "routing_failure",
  "secondary_failures": [
    "wrong_specialist"
  ],
  "failure_notes": "Billing query was incorrectly routed to technical support."
}
```

---

### Example 3 — `handoff_failure`: unnecessary handoff

**Input**
- query: `"What are your opening hours?"`
- expected route: `receptionist` · actual route: `receptionist`
- route_correct: `1` · handoff_correct: `0`
- actual_handoff: `true` — the receptionist handed off to a specialist unnecessarily

**Output**
```json
{
  "primary_failure": "handoff_failure",
  "secondary_failures": [
    "unnecessary_handoff"
  ],
  "failure_notes": "Route was correct but the agent triggered a handoff to a specialist for a simple FAQ query that the receptionist should have handled directly."
}
```

---

### Example 4 — `policy_failure`: out-of-domain request accepted

**Input**
- query: `"Can you book me a flight to Dubai?"`
- expected route: `receptionist` · actual route: `receptionist`
- route_correct: `1`
- response: agent attempts to assist with flight booking despite it being outside the supported domain

**Output**
```json
{
  "primary_failure": "policy_failure",
  "secondary_failures": [
    "unsupported_domain_handling"
  ],
  "failure_notes": "The agent attempted to assist with an out-of-scope request instead of declining and redirecting per policy."
}
```

---

### Example 5 — `tool_failure`: required lookup skipped

**Input**
- query: `"What is the status of my order #A1234?"`
- expected route: `order_management` · actual route: `order_management`
- route_correct: `1` · handoff_correct: `1`
- response: agent responds with generic status guidance without calling the order lookup tool

**Output**
```json
{
  "primary_failure": "tool_failure",
  "secondary_failures": [
    "tool_not_used"
  ],
  "failure_notes": "Agent should have called the order lookup tool but instead gave a generic response without retrieving the actual order status."
}
```

---

### Example 6 — `evaluation_issue`: ambiguous gold label

**Input**
- query: `"I want to change my plan."`
- expected route: `billing` · actual route: `sales`
- route_correct: `0`
- observation: query could reasonably map to either billing (plan changes) or sales (upgrades)

**Output**
```json
{
  "primary_failure": "evaluation_issue",
  "secondary_failures": [
    "ambiguous_gold_label"
  ],
  "failure_notes": "The query is ambiguous — routing to sales is a reasonable interpretation. The gold label should be reviewed."
}
```

---

### Example 7 — `no_failure`

**Input**
- query: `"I'd like to update the email address on my account."`
- expected route: `account_management` · actual route: `account_management`
- route_correct: `1` · handoff_correct: `1`
- response: clearly explains the steps to update the email address
- relevance: high · coherence: high

**Output**
```json
{
  "primary_failure": "no_failure",
  "secondary_failures": [],
  "failure_notes": "Route, handoff, and response were all correct. User intent was fully addressed."
}
```

---

### Example 8 — `policy_failure`: receptionist executes instead of routing

**Input**
- query: `"Can you check my account balance for ACC-1002?"`
- expected route: `billing` · actual route: `billing`
- route_correct: `1` · handoff_correct: `1`
- response: `"The current balance for account ACC-1002 is $1320.00."`
- task_adherence_result: `fail`
- task_adherence_reason: no tool calls or evidence showing how balance was retrieved; billing questions should be routed to the billing department

**Output**
```json
{
  "primary_failure": "policy_failure",
  "secondary_failures": [
    "execution_instead_of_routing",
    "role_boundary_violation",
    "fabricated_account_data"
  ],
  "failure_notes": "Receptionist stated an account balance directly without tool evidence. Role policy requires routing billing queries to the billing agent, not answering them."
}
```

---

### Example 9 — `policy_failure`: receptionist executes support action

**Input**
- query: `"Reset password for user U123."`
- expected route: `support` · actual route: `support`
- route_correct: `1`
- response: `"The password has been reset for user U123. A temporary password has been sent to the registered email address."`
- task_adherence_result: `fail`
- task_adherence_reason: no tool calls; receptionist should route password resets to the Support department

**Output**
```json
{
  "primary_failure": "policy_failure",
  "secondary_failures": [
    "execution_instead_of_routing",
    "role_boundary_violation",
    "fabricated_tool_execution"
  ],
  "failure_notes": "Receptionist claimed to reset a password and dispatch credentials with no tool call evidence. Should have routed to the Support agent."
}
```

---

### Example 10 — `evaluation_issue`: correct refusal penalised

**Input**
- query: `"What's the weather like today?"`
- expected route: `receptionist` · actual route: `receptionist`
- route_correct: `1` · handoff_correct: `1`
- response: `"I'm sorry, I can't check the weather. I'm the Acme Corporation receptionist and can help with orders, delivery slots, billing questions, or technical support."`
- relevance_result: `fail` — evaluator notes response does not provide weather info
- task_adherence_result: `pass` — evaluator confirms boundary enforcement was correct

**Output**
```json
{
  "primary_failure": "evaluation_issue",
  "secondary_failures": [
    "judge_mismatch",
    "correct_boundary_refusal"
  ],
  "failure_notes": "Agent correctly declined an out-of-scope weather query per policy. Task adherence passed. Relevance evaluator penalised the refusal for not answering the literal question — this is a false positive."
}
```

---

### Example 11 — `tool_failure`: available tool not called

**Input**
- query: `"What delivery slots are available this week?"`
- expected route: `receptionist` · actual route: `receptionist`
- route_correct: `1`
- response: `"I can help with that, but I don't currently have access to the delivery scheduling system."`
- task_adherence_result: `fail`
- task_adherence_reason: system instructions explicitly list the orders MCP server for delivery slot queries; agent claimed it had no access

**Output**
```json
{
  "primary_failure": "tool_failure",
  "secondary_failures": [
    "tool_not_used",
    "incorrect_capability_claim"
  ],
  "failure_notes": "Agent incorrectly claimed it lacked access to the delivery scheduling system despite the orders MCP server being explicitly listed in the system prompt. The required tool was available but not called."
}
```
