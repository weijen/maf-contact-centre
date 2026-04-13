"""Run multi-turn conversation scenarios through the handoff workflow.

Supports same-session multi-turn input: each scenario is a sequence of user
messages processed by a single Workflow instance.  The script records per-turn
output, responding agent, handoff chain, clarification detection, and tool
calls, then writes a JSON report to ``data/``.

Usage:
    uv run python scripts/manual_multiturn_runner.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


def _setup() -> None:
    """Load env vars and initialise telemetry (call once before running scenarios)."""
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    from src.core.telemetry import setup_telemetry

    setup_telemetry()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Billing → Support cross-handoff",
        "turns": [
            {
                "user_message": "Hi, can you check the account balance for ACC-1002?",
                "expect_agent": "billing",
                "expect_handoff": True,
            },
            {
                "user_message": (
                    "Thanks for that. I also have a technical issue — my product "
                    "PRD-3001 keeps crashing when I open it. Can someone help?"
                ),
                "expect_agent": "support",
                "expect_handoff": True,
            },
        ],
    },
    {
        "id": 2,
        "name": "Clarification needed then billing",
        "turns": [
            {
                "user_message": "I need help.",
                "expect_agent": "receptionist",
                "expect_handoff": False,
            },
            {
                "user_message": "It's about my bill — I want to check payment status for ACC-1001.",
                "expect_agent": "billing",
                "expect_handoff": True,
            },
        ],
    },
    {
        "id": 3,
        "name": "Support with follow-up",
        "turns": [
            {
                "user_message": "I'm having a problem with product PRD-3002, it won't start.",
                "expect_agent": "support",
                "expect_handoff": True,
            },
            {
                "user_message": "I tried restarting but it still doesn't work. What else can I try?",
                "expect_agent": "support",
                "expect_handoff": False,
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_context_message(history: list[dict[str, str]], current_message: str) -> str:
    """Combine prior conversation history with the current user message.

    For the first turn ``history`` is empty and the raw message is returned.
    For subsequent turns the prior exchanges are prepended so the LLM has
    context from earlier turns.
    """
    if not history:
        return current_message

    parts: list[str] = ["[Previous conversation]"]
    for entry in history:
        parts.append(f"User: {entry['user']}")
        parts.append(f"Agent: {entry['agent']}")
    parts.append("")
    parts.append("[Current message]")
    parts.append(current_message)
    return "\n".join(parts)


def detect_clarification(response: str, handoff_occurred: bool) -> bool:
    """Heuristic: the agent asked a question and did not hand off."""
    if handoff_occurred:
        return False
    return "?" in response


# ---------------------------------------------------------------------------
# Single-turn execution
# ---------------------------------------------------------------------------


async def _run_turn(
    workflow: Any,
    message: str,
) -> dict[str, Any]:
    """Send *message* to *workflow* and collect streaming events."""
    from agent_framework import AgentResponseUpdate

    run_result = await workflow.run(message, stream=True)

    output_parts: list[str] = []
    last_executor = ""
    handoff_occurred = False
    handoff_chain: list[str] = []
    tool_calls: list[dict[str, str]] = []

    async for event in run_result:
        etype = event.type

        if etype == "handoff_sent":
            handoff_occurred = True

        if etype == "executor_invoked" and event.executor_id:
            if event.executor_id not in handoff_chain:
                handoff_chain.append(event.executor_id)

        if etype == "data" and event.data is not None and isinstance(event.data, AgentResponseUpdate):
            for content in event.data.contents:
                if content.type == "function_call":
                    tool_calls.append({"name": content.name, "arguments": content.arguments})

        if etype == "output" and event.data is not None:
            output_parts.append(str(event.data))
            if event.executor_id:
                last_executor = event.executor_id

    response_text = "".join(output_parts).strip()

    return {
        "response": response_text,
        "responding_agent": last_executor,
        "handoff_occurred": handoff_occurred,
        "handoff_chain": handoff_chain,
        "is_clarification": detect_clarification(response_text, handoff_occurred),
        "tool_calls": tool_calls,
    }


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BASE_DELAY = 5.0


async def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Execute all turns of a single scenario and return the results."""
    from src.core.config import DEFAULT_CONFIG_PATH
    from src.workflows.handoff_workflow import build_handoff_workflow

    workflow = build_handoff_workflow(config_path=DEFAULT_CONFIG_PATH)
    history: list[dict[str, str]] = []
    turn_results: list[dict[str, Any]] = []

    for idx, turn in enumerate(scenario["turns"], start=1):
        user_msg = turn["user_message"]
        context_msg = build_context_message(history, user_msg)

        for attempt in range(_MAX_RETRIES + 1):
            try:
                result = await _run_turn(workflow, context_msg)
                break
            except Exception as exc:
                if attempt < _MAX_RETRIES:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Scenario %d turn %d attempt %d failed, retrying in %.0fs: %s",
                        scenario["id"],
                        idx,
                        attempt + 1,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Scenario %d turn %d failed after retries: %s", scenario["id"], idx, exc)
                    result = {
                        "response": f"[ERROR] {exc}",
                        "responding_agent": "",
                        "handoff_occurred": False,
                        "handoff_chain": [],
                        "is_clarification": False,
                        "tool_calls": [],
                    }

        history.append({"user": user_msg, "agent": result["response"]})

        turn_results.append(
            {
                "turn": idx,
                "user_message": user_msg,
                "expect_agent": turn.get("expect_agent", ""),
                "expect_handoff": turn.get("expect_handoff"),
                **result,
            }
        )

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "turns": turn_results,
    }


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------


def print_summary(results: list[dict[str, Any]]) -> None:
    """Print a human-readable summary to the console."""
    for scenario in results:
        print(f"\n{'='*72}")
        print(f"Scenario {scenario['scenario_id']}: {scenario['scenario_name']}")
        print(f"{'='*72}")
        for turn in scenario["turns"]:
            agent_match = turn["responding_agent"] == turn["expect_agent"]
            handoff_match = turn["handoff_occurred"] == turn.get("expect_handoff")
            status = "PASS" if (agent_match and handoff_match) else "FAIL"

            print(f"\n  Turn {turn['turn']} [{status}]")
            print(f"    User     : {turn['user_message'][:80]}")
            print(f"    Agent    : {turn['responding_agent']} (expected: {turn['expect_agent']})")
            print(f"    Handoff  : {turn['handoff_occurred']} (expected: {turn.get('expect_handoff')})")
            print(f"    Chain    : {' → '.join(turn['handoff_chain']) if turn['handoff_chain'] else '(none)'}")
            print(f"    Clarify  : {turn['is_clarification']}")
            if turn["tool_calls"]:
                print(f"    Tools    : {', '.join(tc['name'] for tc in turn['tool_calls'])}")
            response_preview = turn["response"][:120].replace("\n", " ")
            print(f"    Response : {response_preview}...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def async_main() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        print(f"\nRunning scenario {scenario['id']}: {scenario['name']} ...")
        result = await run_scenario(scenario)
        results.append(result)
    return results


def main() -> None:
    _setup()
    results = asyncio.run(async_main())

    # Write results
    timestamp = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    output_path = PROJECT_ROOT / "data" / f"multiturn_results_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to {output_path}")
    print_summary(results)


if __name__ == "__main__":
    main()
