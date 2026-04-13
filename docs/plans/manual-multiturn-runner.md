# Plan: `scripts/manual_multiturn_runner.py`

## Goal

Build a script that runs **multi-turn conversation scenarios** through the
handoff workflow, recording every turn's output, which agent handled it, and
whether a handoff or clarification occurred.

## Background

The existing runners (`run_manual_tests.py`, `run_eval.py`) are **single-turn**:
each query builds a fresh `Workflow`, sends one message, collects results, and
tears down. They cannot test behaviour across multiple user messages in the same
session (e.g. "check my billing" → follow-up "actually I have a support issue
too").

## Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Multi-turn state | Rebuild workflow per turn, pass prior conversation context in the message | Calling `workflow.run(message)` resets internal context (`reset_for_new_run`). Checkpoint/resume requires `request_info` events the HandoffBuilder workflow does not emit. Prepending conversation history in the prompt is the simplest correct approach. |
| Scenario format | Python dicts in-script | Only 3 scenarios are needed. Avoids JSON plumbing for a manual tool. |
| Output | JSON file under `data/` | Machine-readable, consistent with existing `eval_results` files. |
| Console output | Rich summary per turn (agent, handoff, response preview) | Quick visual feedback when running manually. |

## Scenarios (3)

1. **Billing → Support cross-handoff**
   - Turn 1: User asks about account balance → expect handoff to billing
   - Turn 2: User says they also have a technical issue → expect handoff to
     support (or back to receptionist then support)

2. **Clarification needed**
   - Turn 1: User sends vague "I need help" → expect receptionist to ask for
     clarification (no handoff)
   - Turn 2: User clarifies "It's about my bill" → expect handoff to billing

3. **Support with follow-up**
   - Turn 1: User reports a product issue → expect handoff to support
   - Turn 2: User asks a follow-up question about the same issue → expect
     support agent to continue handling

## Data captured per turn

| Field | Type | Description |
|-------|------|-------------|
| `turn` | int | 1-based index within the scenario |
| `user_message` | str | What the user said |
| `response` | str | Agent's full text reply |
| `responding_agent` | str | `executor_id` from the last `output` event |
| `handoff_occurred` | bool | True if `handoff_sent` event seen this turn |
| `handoff_chain` | list[str] | Ordered agent names from `handoff_sent` events |
| `is_clarification` | bool | Heuristic: agent asked a question, no handoff |
| `tool_calls` | list[dict] | Tool invocations (function name + args) |

## Output file

`data/multiturn_results_DD-MM-YYYY.json`

```json
[
  {
    "scenario_id": 1,
    "scenario_name": "Billing → Support cross-handoff",
    "turns": [
      {
        "turn": 1,
        "user_message": "...",
        "response": "...",
        "responding_agent": "billing",
        "handoff_occurred": true,
        "handoff_chain": ["receptionist", "billing"],
        "is_clarification": false,
        "tool_calls": [...]
      }
    ]
  }
]
```

## Implementation steps

1. Create `scripts/manual_multiturn_runner.py`.
2. Define 3 scenario dicts with `id`, `name`, `turns` (list of user messages
   and expectations).
3. For each scenario:
   a. Build a fresh `Workflow` via `build_handoff_workflow()`.
   b. Initialise an empty conversation history list.
   c. For each turn:
      - Construct a combined message: prior history + current user input.
      - Call `workflow.run(message, stream=True)`.
      - Stream events, record output text, handoffs, tool calls.
      - Append user message and agent response to the history for the next
        turn's context.
   d. Append scenario results to the output list.
4. Write results JSON to `data/`.
5. Print console summary.

## Testing

- `tests/test_manual_multiturn_runner.py` — unit tests for helper functions
  (`build_context_message`, `detect_clarification`, scenario structure
  validation). Workflow invocation is mocked.

## Open questions

- If checkpoint-based resumption is needed later (true server-side session
  state), the `Workflow.run(checkpoint_id=..., responses=...)` path can be
  explored once HandoffBuilder supports `request_info` events.
