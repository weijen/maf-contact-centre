import asyncio
from unittest.mock import AsyncMock, patch

from agent_framework import WorkflowEvent


def _setup_workflow_mock(build_wf_mock, events: list) -> None:
    workflow_mock = AsyncMock()
    run_result_mock = AsyncMock()
    run_result_mock.__aiter__.return_value = iter(events)
    workflow_mock.run.return_value = run_result_mock
    build_wf_mock.return_value = workflow_mock


@patch("scripts.run_eval.build_handoff_workflow")
def test_run_workflow_async_returns_response_and_route(build_wf_mock):
    """Output events should be captured as response text with correct route."""
    events = [
        WorkflowEvent(
            type="output",
            data="I can help with billing questions.",
            executor_id="receptionist",
        ),
    ]
    _setup_workflow_mock(build_wf_mock, events)

    from scripts.run_eval import _run_workflow_async

    result = asyncio.run(_run_workflow_async("I have a billing question"))

    assert result["response"] == "I can help with billing questions."
    assert result["actual_route"] == "receptionist"
    assert result["actual_handoff"] == "False"


@patch("scripts.run_eval.build_handoff_workflow")
def test_run_workflow_async_detects_handoff(build_wf_mock):
    """Handoff events should set actual_handoff to True."""
    events = [
        WorkflowEvent(type="handoff_sent", data=None),
        WorkflowEvent(
            type="output",
            data="The balance for ACC-1002 is $1320.00.",
            executor_id="billing",
        ),
    ]
    _setup_workflow_mock(build_wf_mock, events)

    from scripts.run_eval import _run_workflow_async

    result = asyncio.run(_run_workflow_async("Check balance for ACC-1002"))

    assert result["actual_route"] == "billing"
    assert result["actual_handoff"] == "True"
    assert result["response"] == "The balance for ACC-1002 is $1320.00."
