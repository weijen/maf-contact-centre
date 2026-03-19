"""Run the 9 manual test cases through the handoff workflow using azure-ai-evaluation.

Usage:
    uv run python scripts/run_manual_tests.py

Output:
    - Console summary with pass/fail per case
    - data/manual_test_results_v1.json with full details including evaluation metrics
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.core.telemetry import setup_telemetry  # noqa: E402

setup_telemetry()

from azure.ai.evaluation import (  # noqa: E402
    CoherenceEvaluator,
    RelevanceEvaluator,
    ToolCallAccuracyEvaluator,
    evaluate,
)
from dotenv import dotenv_values

from src.core.config import DEFAULT_CONFIG_PATH, load_yaml
from src.workflows.handoff_workflow import build_handoff_workflow

TEST_CASES_PATH = PROJECT_ROOT / "data" / "manual_test_cases_v1.json"
RESULTS_PATH = PROJECT_ROOT / "data" / "manual_test_results_v1.json"


# ---------------------------------------------------------------------------
# Handoff tool definitions built from config.yaml
# ---------------------------------------------------------------------------

def _build_handoff_tool_definitions(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict[str, Any]]:
    """Build tool definitions matching the framework's handoff tools from config."""
    config = load_yaml(config_path)
    seen: set[str] = set()
    definitions: list[dict[str, Any]] = []

    for handoff in config.get("handoffs", []):
        target = handoff["to"]
        tool_name = f"handoff_to_{target}"
        if tool_name in seen:
            continue
        seen.add(tool_name)
        definitions.append({
            "name": tool_name,
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Optional context about the handoff reason.",
                    },
                },
                "required": [],
            },
        })
    return definitions


HANDOFF_TOOL_DEFINITIONS = _build_handoff_tool_definitions()


# ---------------------------------------------------------------------------
# Target function: runs a single query through the handoff workflow
# ---------------------------------------------------------------------------

def run_workflow_target(query: str) -> dict[str, Any]:
    """Target callable for azure-ai-evaluation.

    Returns response text, routing metadata, and tool call data for
    ToolCallAccuracyEvaluator.
    """
    return asyncio.run(_run_workflow_async(query))


async def _run_workflow_async(query: str) -> dict[str, Any]:
    workflow = build_handoff_workflow(config_path=DEFAULT_CONFIG_PATH)
    run_result = await workflow.run(query, stream=True)

    last_output_executor = ""
    handoff_occurred = False
    output_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    call_counter = 0

    async for event in run_result:
        etype = event.type

        if etype == "handoff_sent":
            handoff_occurred = True
            data = event.data
            target = data.target if hasattr(data, "target") else str(data)
            call_counter += 1
            tool_calls.append({
                "type": "function_call",
                "name": f"handoff_to_{target}",
                "arguments": {},
                "tool_call_id": f"call_{call_counter}",
            })

        if etype == "output" and event.data is not None:
            output_parts.append(str(event.data))
            if event.executor_id:
                last_output_executor = event.executor_id

    result: dict[str, Any] = {
        "response": " ".join(output_parts),
        "actual_handler": last_output_executor,
        "actual_handoff": str(handoff_occurred),
        "tool_calls": json.dumps(tool_calls),
        "tool_definitions": json.dumps(HANDOFF_TOOL_DEFINITIONS),
    }
    return result


# ---------------------------------------------------------------------------
# Custom evaluator: routing correctness (deterministic pass/fail)
# ---------------------------------------------------------------------------

def routing_correctness(
    *,
    actual_handler: str,
    actual_handoff: str,
    expected_handler: str,
    expected_handoff: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Deterministic evaluator that checks whether routing matched expectations."""
    handler_match = actual_handler == expected_handler
    handoff_match = actual_handoff == expected_handoff
    passed = handler_match and handoff_match

    observation = "OK"
    if not handler_match:
        observation = f"Expected {expected_handler}, got {actual_handler}"
    elif not handoff_match:
        observation = f"Handoff expected={expected_handoff}, actual={actual_handoff}"

    return {
        "routing_correct": 1.0 if passed else 0.0,
        "handler_correct": 1.0 if handler_match else 0.0,
        "handoff_correct": 1.0 if handoff_match else 0.0,
        "observation": observation,
    }


# ---------------------------------------------------------------------------
# Prepare dataset for evaluate()
# ---------------------------------------------------------------------------

def prepare_dataset(cases_path: Path = TEST_CASES_PATH) -> Path:
    """Convert test cases JSON to a JSONL file that evaluate() can consume."""
    with open(cases_path) as f:
        cases = json.load(f)

    jsonl_path = cases_path.parent / "manual_test_cases_v1.jsonl"
    with open(jsonl_path, "w") as f:
        for case in cases:
            row = {
                "query": case["input"],
                "expected_handler": case["expected_handler"],
                "expected_handoff": str(case["expected_handoff"]),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return jsonl_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    env_path = PROJECT_ROOT / ".env"
    env_values = dotenv_values(env_path)

    eval_endpoint = env_values.get("AZURE_EVAL_ENDPOINT", "")
    eval_deployment = env_values.get("AZURE_EVAL_DEPLOYMENT_NAME", "")
    eval_api_version = env_values.get("AZURE_EVAL_API_VERSION", "2024-06-01")

    model_config = {
        "azure_endpoint": eval_endpoint,
        "azure_deployment": eval_deployment,
        "api_version": eval_api_version,
    }

    jsonl_path = prepare_dataset()
    print(f"Prepared {jsonl_path}\n")

    result = evaluate(
        data=str(jsonl_path),
        target=run_workflow_target,
        evaluators={
            "routing": routing_correctness,
            "tool_accuracy": ToolCallAccuracyEvaluator(model_config=model_config),
            "coherence": CoherenceEvaluator(model_config=model_config),
            "relevance": RelevanceEvaluator(model_config=model_config),
        },
        evaluator_config={
            "routing": {
                "column_mapping": {
                    "actual_handler": "${target.actual_handler}",
                    "actual_handoff": "${target.actual_handoff}",
                    "expected_handler": "${data.expected_handler}",
                    "expected_handoff": "${data.expected_handoff}",
                },
            },
            "tool_accuracy": {
                "column_mapping": {
                    "query": "${data.query}",
                    "tool_calls": "${target.tool_calls}",
                    "tool_definitions": "${target.tool_definitions}",
                },
            },
            "coherence": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${target.response}",
                },
            },
            "relevance": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${target.response}",
                },
            },
        },
        output_path=str(RESULTS_PATH),
        evaluation_name="manual_test_v1",
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("-" * 60)
    metrics = result.get("metrics", {})
    for key, value in sorted(metrics.items()):
        print(f"  {key}: {value}")
    print("=" * 60)

    rows = result.get("rows", [])
    if rows:
        print(f"\nDetailed results saved to {RESULTS_PATH}")

    # Check routing pass rate
    routing_score = metrics.get("routing.routing_correct", 0)
    if isinstance(routing_score, (int, float)) and routing_score < 1.0:
        print("\nSome routing tests FAILED.")
        sys.exit(1)
    else:
        print("\nAll routing tests PASSED.")


if __name__ == "__main__":
    main()
