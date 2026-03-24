"""Tests for src.core.patches — monkey-patch for agent-framework#3983."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.core.patches import _get_event_type, apply_devui_executor_patch


class TestGetEventType:
    """Unit tests for the _get_event_type helper."""

    def test_returns_type_from_object(self) -> None:
        event = MagicMock()
        event.type = "request_info"
        assert _get_event_type(event) == "request_info"

    def test_returns_type_from_dict(self) -> None:
        event = {"type": "error", "message": "something failed"}
        assert _get_event_type(event) == "error"

    def test_returns_none_for_dict_without_type(self) -> None:
        event = {"message": "no type key"}
        assert _get_event_type(event) is None

    def test_returns_none_for_object_without_type(self) -> None:
        event = object()
        assert _get_event_type(event) is None


class TestApplyDevuiExecutorPatch:
    """Integration tests for the monkey-patch."""

    def test_patch_is_idempotent(self) -> None:
        import src.core.patches as patches_mod

        with patch.object(patches_mod, "_PATCHED", False):
            # First call should proceed and set _PATCHED.
            with patch.object(patches_mod, "_patch_execute_entity"):
                with patch.object(patches_mod, "_patch_execute_workflow"):
                    apply_devui_executor_patch()

            assert patches_mod._PATCHED is True

    def test_skips_when_upstream_fix_present(self) -> None:
        import src.core.patches as patches_mod

        executor_mod = MagicMock()
        executor_mod._get_event_type = MagicMock()

        with patch.object(patches_mod, "_PATCHED", False):
            with patch.dict("sys.modules", {"agent_framework_devui._executor": executor_mod}):
                apply_devui_executor_patch()
            assert patches_mod._PATCHED is True

    def test_dict_event_wrapped_by_patched_execute_workflow(self) -> None:
        """Simulate the error path: _execute_workflow yields a raw dict.

        After patching, the dict must be wrapped so that ``event.type``
        works without raising ``AttributeError``.
        """
        import agent_framework_devui._executor as executor_mod

        from src.core.patches import _patch_execute_workflow

        cls = getattr(executor_mod, "AgentFrameworkExecutor", None)
        if cls is None:
            pytest.skip("AgentFrameworkExecutor not available in installed version")

        original_method = getattr(cls, "_execute_workflow", None)
        if original_method is None:
            pytest.skip("_execute_workflow not found on AgentFrameworkExecutor")

        # Create a fake _execute_workflow that yields a raw dict (the bug trigger).
        async def _fake_execute_workflow(self, *args, **kwargs):
            yield {"type": "error", "message": "generator didn't stop after throw()"}

        try:
            cls._execute_workflow = _fake_execute_workflow

            # Apply only the workflow patch directly.
            _patch_execute_workflow(executor_mod)

            # Now the patched version should wrap the dict.
            instance = MagicMock()

            async def _collect() -> list[object]:
                events = []
                async for event in cls._execute_workflow(instance):
                    events.append(event)
                return events

            events = asyncio.new_event_loop().run_until_complete(_collect())

            assert len(events) == 1
            event = events[0]
            # The critical assertion: accessing .type must NOT raise.
            assert event.type == "error"
            assert event.message == "generator didn't stop after throw()"
            # Must still pass isinstance(event, dict) for downstream consumers.
            assert isinstance(event, dict)
            assert event["type"] == "error"
        finally:
            # Restore original to avoid polluting other tests.
            if original_method is not None:
                cls._execute_workflow = original_method
