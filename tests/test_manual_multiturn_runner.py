"""Tests for scripts/manual_multiturn_runner.py helper functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.manual_multiturn_runner import (
    SCENARIOS,
    build_context_message,
    detect_clarification,
    run_scenario,
)


# ---------------------------------------------------------------------------
# build_context_message
# ---------------------------------------------------------------------------


class TestBuildContextMessage:
    def test_first_turn_returns_raw_message(self) -> None:
        assert build_context_message([], "Hello") == "Hello"

    def test_second_turn_prepends_history(self) -> None:
        history = [{"user": "Hi", "agent": "Hello! How can I help?"}]
        result = build_context_message(history, "Check my bill")
        assert "[Previous conversation]" in result
        assert "User: Hi" in result
        assert "Agent: Hello! How can I help?" in result
        assert "[Current message]" in result
        assert result.endswith("Check my bill")

    def test_multiple_turns_include_all_history(self) -> None:
        history = [
            {"user": "Hi", "agent": "Hello!"},
            {"user": "Billing please", "agent": "Connecting you."},
        ]
        result = build_context_message(history, "Thanks")
        assert result.count("User:") == 2
        assert result.count("Agent:") == 2


# ---------------------------------------------------------------------------
# detect_clarification
# ---------------------------------------------------------------------------


class TestDetectClarification:
    def test_question_without_handoff_is_clarification(self) -> None:
        assert detect_clarification("What is your account number?", False) is True

    def test_question_with_handoff_is_not_clarification(self) -> None:
        assert detect_clarification("Let me transfer you. OK?", True) is False

    def test_no_question_is_not_clarification(self) -> None:
        assert detect_clarification("Here is your balance.", False) is False


# ---------------------------------------------------------------------------
# Scenario structure validation
# ---------------------------------------------------------------------------


class TestScenarioStructure:
    def test_has_three_scenarios(self) -> None:
        assert len(SCENARIOS) == 3

    def test_each_scenario_has_required_keys(self) -> None:
        for s in SCENARIOS:
            assert "id" in s
            assert "name" in s
            assert "turns" in s
            assert len(s["turns"]) >= 2, f"Scenario {s['id']} needs at least 2 turns"

    def test_each_turn_has_required_keys(self) -> None:
        for s in SCENARIOS:
            for t in s["turns"]:
                assert "user_message" in t
                assert "expect_agent" in t
                assert "expect_handoff" in t


# ---------------------------------------------------------------------------
# run_scenario (mocked workflow)
# ---------------------------------------------------------------------------


def _make_event(etype: str, data: object = None, executor_id: str | None = None) -> MagicMock:
    event = MagicMock()
    event.type = etype
    event.data = data
    event.executor_id = executor_id
    return event


class TestRunScenario:
    def test_records_two_turns(self) -> None:
        """Mocked workflow returns canned events for each turn."""
        events_per_turn = [
            # Turn 1: handoff to billing
            [
                _make_event("executor_invoked", executor_id="receptionist"),
                _make_event("handoff_sent"),
                _make_event("executor_invoked", executor_id="billing"),
                _make_event("output", data="Your balance is $100.", executor_id="billing"),
            ],
            # Turn 2: handoff to support
            [
                _make_event("executor_invoked", executor_id="billing"),
                _make_event("handoff_sent"),
                _make_event("executor_invoked", executor_id="support"),
                _make_event("output", data="Let me help with that.", executor_id="support"),
            ],
        ]

        call_count = 0

        async def mock_run(message: str, stream: bool = False) -> AsyncMock:
            nonlocal call_count
            events = events_per_turn[call_count]
            call_count += 1

            async def _aiter():
                for e in events:
                    yield e

            return _aiter()

        mock_workflow = MagicMock()
        mock_workflow.run = mock_run

        scenario = SCENARIOS[0]  # Billing → Support cross-handoff

        async def _run() -> dict:
            with patch("src.workflows.handoff_workflow.build_handoff_workflow", return_value=mock_workflow):
                return await run_scenario(scenario)

        import asyncio

        result = asyncio.run(_run())

        assert result["scenario_id"] == 1
        assert len(result["turns"]) == 2

        t1 = result["turns"][0]
        assert t1["responding_agent"] == "billing"
        assert t1["handoff_occurred"] is True
        assert "receptionist" in t1["handoff_chain"]
        assert "billing" in t1["handoff_chain"]

        t2 = result["turns"][1]
        assert t2["responding_agent"] == "support"
        assert t2["handoff_occurred"] is True
