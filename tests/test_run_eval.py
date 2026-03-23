import asyncio
import json
from unittest.mock import AsyncMock, patch

from agent_framework import AgentResponseUpdate, Content, WorkflowEvent

_FAKE_INSTRUCTIONS = {
    "receptionist": "You are a receptionist.",
    "billing": "You are a billing agent.",
    "support": "You are a support agent.",
}

_FAKE_PLUGINS = {
    "receptionist": ["receptionist_tools"],
    "billing": ["billing_tools"],
    "support": ["support_tools"],
}

_FAKE_AVAILABLE_TOOLS = {
    "receptionist": ["get_current_time", "get_office_hours"],
    "billing": ["get_account_balance", "check_payment_status"],
    "support": ["reset_password", "create_support_ticket"],
}


def _make_data_events(contents_list: list[list[Content]], *, executor_id: str = "billing") -> list:
    """Build data WorkflowEvents from lists of Content items."""
    events = []
    for contents in contents_list:
        update = AgentResponseUpdate(contents=contents, role="assistant")
        events.append(WorkflowEvent(type="data", data=update, executor_id=executor_id))
    return events


def _setup_workflow_mock(build_wf_mock, events: list) -> None:
    workflow_mock = AsyncMock()
    run_result_mock = AsyncMock()
    run_result_mock.__aiter__.return_value = iter(events)
    workflow_mock.run.return_value = run_result_mock
    build_wf_mock.return_value = workflow_mock


@patch("scripts.run_eval._AGENT_INSTRUCTIONS", _FAKE_INSTRUCTIONS)
@patch("scripts.run_eval._AGENT_PLUGINS", _FAKE_PLUGINS)
@patch("scripts.run_eval._AGENT_AVAILABLE_TOOLS", _FAKE_AVAILABLE_TOOLS)
@patch("scripts.run_eval.build_handoff_workflow")
def test_run_workflow_async_captures_tool_calls(build_wf_mock):
    """Tool call and tool result events should appear in conversation_response."""
    events = [
        WorkflowEvent(type="handoff_sent", data=None),
        *_make_data_events([
            [Content.from_function_call(
                call_id="call_1",
                name="get_account_balance",
                arguments={"account_id": "ACC-1002"},
            )],
        ]),
        *_make_data_events([
            [Content.from_function_result(
                call_id="call_1",
                result='{"balance": 1320.00}',
            )],
        ]),
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
    assert json.loads(result["agent_plugins"]) == ["billing_tools"]
    assert json.loads(result["agent_available_tools"]) == ["get_account_balance", "check_payment_status"]

    response_msgs = json.loads(result["conversation_response"])

    # Should have 3 messages: tool_call, tool_result, final text
    assert len(response_msgs) == 3

    # First: tool call
    assert response_msgs[0]["role"] == "assistant"
    tool_call = response_msgs[0]["content"][0]
    assert tool_call["type"] == "tool_call"
    assert tool_call["tool_call"]["function"]["name"] == "get_account_balance"
    assert tool_call["tool_call"]["function"]["arguments"] == {"account_id": "ACC-1002"}
    assert tool_call["tool_call"]["id"] == "call_1"

    # Second: tool result
    assert response_msgs[1]["role"] == "tool"
    assert response_msgs[1]["tool_call_id"] == "call_1"
    tool_result = response_msgs[1]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert "1320" in tool_result["tool_result"]

    # Third: final assistant text
    assert response_msgs[2]["role"] == "assistant"
    assert response_msgs[2]["content"][0]["type"] == "text"
    assert "1320" in response_msgs[2]["content"][0]["text"]


@patch("scripts.run_eval._AGENT_INSTRUCTIONS", _FAKE_INSTRUCTIONS)
@patch("scripts.run_eval._AGENT_PLUGINS", _FAKE_PLUGINS)
@patch("scripts.run_eval._AGENT_AVAILABLE_TOOLS", _FAKE_AVAILABLE_TOOLS)
@patch("scripts.run_eval.build_handoff_workflow")
def test_run_workflow_async_no_tool_calls(build_wf_mock):
    """When no tools are called, conversation_response has only the text message."""
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

    assert json.loads(result["agent_plugins"]) == ["receptionist_tools"]
    assert json.loads(result["agent_available_tools"]) == ["get_current_time", "get_office_hours"]

    response_msgs = json.loads(result["conversation_response"])
    assert len(response_msgs) == 1
    assert response_msgs[0]["role"] == "assistant"
    assert response_msgs[0]["content"][0]["type"] == "text"


@patch("scripts.run_eval._AGENT_INSTRUCTIONS", _FAKE_INSTRUCTIONS)
@patch("scripts.run_eval._AGENT_PLUGINS", _FAKE_PLUGINS)
@patch("scripts.run_eval._AGENT_AVAILABLE_TOOLS", _FAKE_AVAILABLE_TOOLS)
@patch("scripts.run_eval.build_handoff_workflow")
def test_run_workflow_async_multiple_tool_calls(build_wf_mock):
    """Multiple tool calls should all appear in the response."""
    events = [
        WorkflowEvent(type="handoff_sent", data=None),
        *_make_data_events([
            [Content.from_function_call(
                call_id="call_1",
                name="get_account_balance",
                arguments={"account_id": "ACC-1001"},
            )],
        ]),
        *_make_data_events([
            [Content.from_function_result(
                call_id="call_1",
                result='{"balance": 245.50}',
            )],
        ]),
        *_make_data_events([
            [Content.from_function_call(
                call_id="call_2",
                name="check_payment_status",
                arguments={"account_id": "ACC-1001", "payment_id": "PAY-2001"},
            )],
        ]),
        *_make_data_events([
            [Content.from_function_result(
                call_id="call_2",
                result='{"status": "completed"}',
            )],
        ]),
        WorkflowEvent(
            type="output",
            data="Balance is $245.50, payment PAY-2001 is completed.",
            executor_id="billing",
        ),
    ]
    _setup_workflow_mock(build_wf_mock, events)

    from scripts.run_eval import _run_workflow_async

    result = asyncio.run(_run_workflow_async("Check balance and payment status"))

    response_msgs = json.loads(result["conversation_response"])
    # 2 tool calls + 2 tool results + 1 final text = 5 messages
    assert len(response_msgs) == 5

    tool_call_msgs = [m for m in response_msgs if m["role"] == "assistant" and m["content"][0]["type"] == "tool_call"]
    tool_result_msgs = [m for m in response_msgs if m["role"] == "tool"]
    assert len(tool_call_msgs) == 2
    assert len(tool_result_msgs) == 2
