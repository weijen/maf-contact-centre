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

**Routing**
`wrong_specialist` · `should_have_stayed_at_receptionist` · `missed_specialist_route`

**Handoff**
`missed_handoff` · `unnecessary_handoff` · `looping_handoff`

**Response**
`intent_not_addressed` · `escalation_request_not_addressed` · `generic_redirection` · `incomplete_answer` · `insufficient_empathy` · `unhelpful_response` · `off_tone`

**Policy / boundary**
`unsupported_domain_handling` · `policy_not_followed` · `boundary_handling_issue`

**Tool**
`tool_not_used` · `tool_used_incorrectly` · `tool_result_ignored`

**Evaluation**
`ambiguous_gold_label` · `judge_mismatch` · `insufficient_context`

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

### 2 Priority `policy_failure` 

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

### 5 Priority `handoff_failure` 

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
Is the defect in the test data or labels?          → evaluation_issue
Does the agent violate a policy or boundary rule?  → policy_failure
Is the core defect about tool use?                 → tool_failure
Is the route wrong?  (route_correct = 0)           → routing_failure
Is the route OK but handoff wrong?                 → handoff_failure
Is routing/handoff OK but response quality poor?   → response_failure
No meaningful defect found?                        → no_failure
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
