"""Run the eval dataset through the handoff workflow using azure-ai-evaluation.

Usage:
    uv run python scripts/run_eval.py [--dataset data/eval_dataset_v1.jsonl]

Output:
    - Console summary with pass/fail per case
    - data/eval_results_v1.json with full details including evaluation metrics
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import threading
import time
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
    TaskAdherenceEvaluator,
    evaluate,
)
from dotenv import dotenv_values  # noqa: E402

from src.agents.common import load_agent_definition  # noqa: E402
from src.core.config import DEFAULT_CONFIG_PATH  # noqa: E402
from src.workflows.handoff_workflow import build_handoff_workflow  # noqa: E402

# Load the receptionist system prompt so TaskAdherenceEvaluator knows the agent's role
_RECEPTIONIST_INSTRUCTIONS = load_agent_definition("receptionist").instructions

DEFAULT_DATASET = PROJECT_ROOT / "data" / "eval_dataset_v1.jsonl"

# Limit concurrent workflow executions to avoid Azure OpenAI rate limits
_CONCURRENCY_LIMIT = threading.Semaphore(3)
_MAX_RETRIES = 4
_BASE_DELAY = 5.0

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Target function: runs a single query through the handoff workflow
# ---------------------------------------------------------------------------


def run_workflow_target(query: str) -> dict[str, Any]:
    """Target callable for azure-ai-evaluation (with throttling + retry)."""
    for attempt in range(_MAX_RETRIES + 1):
        with _CONCURRENCY_LIMIT:
            try:
                return asyncio.run(_run_workflow_async(query))
            except Exception as exc:
                if "Too Many Requests" in str(exc) or "429" in str(exc) or "rate" in str(exc).lower():
                    if attempt < _MAX_RETRIES:
                        delay = _BASE_DELAY * (2 ** attempt)
                        logger.warning("Rate limited (attempt %d/%d), retrying in %.0fs", attempt + 1, _MAX_RETRIES, delay)
                        time.sleep(delay)
                        continue
                raise
    return {"response": "", "actual_route": "", "actual_handoff": "False"}


async def _run_workflow_async(query: str) -> dict[str, Any]:
    workflow = build_handoff_workflow(config_path=DEFAULT_CONFIG_PATH)
    run_result = await workflow.run(query, stream=True)

    last_output_executor = ""
    handoff_occurred = False
    output_parts: list[str] = []

    async for event in run_result:
        etype = event.type

        if etype == "handoff_sent":
            handoff_occurred = True

        if etype == "output" and event.data is not None:
            output_parts.append(str(event.data))
            if event.executor_id:
                last_output_executor = event.executor_id

    return {
        "response": "".join(output_parts).strip(),
        "actual_route": last_output_executor,
        "actual_handoff": str(handoff_occurred),
        "conversation_query": json.dumps(
            [
                {"role": "system", "content": _RECEPTIONIST_INSTRUCTIONS},
                {"role": "user", "content": query},
            ]
        ),
        "conversation_response": json.dumps(
            [{"role": "assistant", "content": [{"type": "text", "text": "".join(output_parts).strip()}]}]
        ),
    }


# ---------------------------------------------------------------------------
# Custom evaluator: routing correctness (deterministic)
# ---------------------------------------------------------------------------


def routing_correctness(
    *,
    actual_route: str,
    expected_route: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Check whether the query was routed to an acceptable agent.

    For mixed-intent cases, acceptable_routes / acceptable_handoff define
    a set of valid outcomes (e.g. clarify_or_triage).  For all other cases
    we fall back to exact expected_route matching.
    """
    # Parse flexible-match lists (serialised as JSON strings by prepare_dataset)
    raw_routes = kwargs.get("acceptable_routes", "[]")
    acceptable_routes: list[str] = json.loads(raw_routes) if raw_routes else []
    raw_handoff = kwargs.get("acceptable_handoff", "[]")
    acceptable_handoff: list[bool] = json.loads(raw_handoff) if raw_handoff else []

    actual_handoff = kwargs.get("actual_handoff", "False") == "True"

    if acceptable_routes:
        # Flexible matching for mixed-intent / triage cases
        route_match = actual_route in acceptable_routes
        handoff_match = actual_handoff in acceptable_handoff if acceptable_handoff else True
    else:
        # Strict matching for single-intent cases
        route_match = actual_route == expected_route
        expected_handoff = expected_route != "receptionist"
        handoff_match = actual_handoff == expected_handoff

    observation = "OK"
    if not route_match:
        label = acceptable_routes if acceptable_routes else [expected_route]
        observation = f"Expected route in {label}, got {actual_route}"
    elif not handoff_match:
        observation = f"Handoff actual={actual_handoff}, acceptable={acceptable_handoff}"

    return {
        "routing_correct": 1.0 if (route_match and handoff_match) else 0.0,
        "route_correct": 1.0 if route_match else 0.0,
        "handoff_correct": 1.0 if handoff_match else 0.0,
        "observation": observation,
    }


# ---------------------------------------------------------------------------
# Prepare JSONL for evaluate()
# ---------------------------------------------------------------------------


def prepare_dataset(dataset_path: Path) -> Path:
    """Read the eval JSONL and emit a evaluate()-ready JSONL with flat columns."""
    ready_path = dataset_path.parent / (dataset_path.stem + "_ready.jsonl")
    with open(dataset_path) as fin, open(ready_path, "w") as fout:
        for line in fin:
            case = json.loads(line)
            row = {
                "query": case["query"],
                "expected_route": case["expected_route"],
                "category": case.get("category", ""),
                "id": case.get("id", ""),
                "acceptable_routes": json.dumps(case.get("acceptable_routes", [])),
                "acceptable_handoff": json.dumps(case.get("acceptable_handoff", [])),
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
    return ready_path


# ---------------------------------------------------------------------------
# Pretty-print results
# ---------------------------------------------------------------------------


def pretty_print_results(results_path: Path) -> None:
    """Re-write the results JSON with indentation."""
    with open(results_path) as f:
        data = json.load(f)
    with open(results_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval dataset")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to eval JSONL dataset")
    args = parser.parse_args()

    dataset_path: Path = args.dataset
    results_path = dataset_path.parent / dataset_path.name.replace("eval_dataset", "eval_results").replace(
        ".jsonl", ".json"
    )

    env_path = PROJECT_ROOT / ".env"
    env_values = dotenv_values(env_path)

    model_config = {
        "azure_endpoint": env_values.get("AZURE_EVAL_ENDPOINT", ""),
        "azure_deployment": env_values.get("AZURE_EVAL_DEPLOYMENT_NAME", ""),
        "api_version": env_values.get("AZURE_EVAL_API_VERSION", "2024-06-01"),
    }

    # Newer models (e.g. gpt-5.3-chat) require max_completion_tokens instead of max_tokens
    deployment = model_config["azure_deployment"]
    is_reasoning = "gpt-5" in deployment or "o1" in deployment or "o3" in deployment

    jsonl_path = prepare_dataset(dataset_path)
    print(f"Prepared {jsonl_path}\n")

    result = evaluate(
        data=str(jsonl_path),
        target=run_workflow_target,
        evaluators={
            "routing": routing_correctness,
            "coherence": CoherenceEvaluator(model_config=model_config, is_reasoning_model=is_reasoning),
            "relevance": RelevanceEvaluator(model_config=model_config, is_reasoning_model=is_reasoning),
            "task_adherence": TaskAdherenceEvaluator(model_config=model_config, is_reasoning_model=is_reasoning),
        },
        evaluator_config={
            "routing": {
                "column_mapping": {
                    "actual_route": "${target.actual_route}",
                    "actual_handoff": "${target.actual_handoff}",
                    "expected_route": "${data.expected_route}",
                    "acceptable_routes": "${data.acceptable_routes}",
                    "acceptable_handoff": "${data.acceptable_handoff}",
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
            "task_adherence": {
                "column_mapping": {
                    "query": "${target.conversation_query}",
                    "response": "${target.conversation_response}",
                },
            },
        },
        output_path=str(results_path),
        evaluation_name="eval_v1",
    )

    pretty_print_results(results_path)

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
        print(f"\nDetailed results saved to {results_path}")

    # Per-category breakdown
    categories: dict[str, list[float]] = {}
    for row in rows:
        cat = row.get("inputs.category", "unknown")
        score = row.get("outputs.routing.routing_correct", 0.0)
        categories.setdefault(cat, []).append(score)

    if categories:
        print("\n--- Routing by Category ---")
        for cat, scores in sorted(categories.items()):
            avg = sum(scores) / len(scores) if scores else 0.0
            print(f"  {cat}: {avg:.2f} ({len(scores)} cases)")

    # Check routing pass rate
    routing_score = metrics.get("routing.routing_correct", 0)
    if isinstance(routing_score, (int, float)) and routing_score < 1.0:
        print("\nSome routing tests FAILED.")
        sys.exit(1)
    else:
        print("\nAll routing tests PASSED.")

    from src.core.telemetry import flush_telemetry

    flush_telemetry()


if __name__ == "__main__":
    main()
