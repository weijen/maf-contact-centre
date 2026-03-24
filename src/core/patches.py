"""Monkey-patches for upstream bugs in agent-framework-devui.

Tracks:
  - https://github.com/microsoft/agent-framework/issues/3983
    Fixed upstream in PR #4294 (agent-framework-devui >= 1.0.0b260304).
    Remove this module once agent-framework is upgraded past 1.0.0b260212.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_PATCHED = False


def _get_event_type(event: object) -> str | None:
    """Safely read the type of a workflow event.

    The upstream ``_executor.py`` accesses ``event.type`` directly, but error
    paths yield plain *dicts* which don't have a ``.type`` attribute.  This
    helper mirrors the fix in PR #4294.
    """
    if isinstance(event, dict):
        return event.get("type")
    return getattr(event, "type", None)


def apply_devui_executor_patch() -> None:
    """Patch ``agent_framework_devui._executor`` to handle dict events safely.

    Idempotent — calling this more than once is a no-op.
    """
    global _PATCHED  # noqa: PLW0603
    if _PATCHED:
        return

    try:
        import agent_framework_devui._executor as executor_mod
    except ImportError:
        logger.debug("agent_framework_devui not installed; skipping executor patch")
        return

    # If the upstream fix is already present we don't need to patch.
    if hasattr(executor_mod, "_get_event_type"):
        logger.debug("Upstream _get_event_type already present; skipping patch")
        _PATCHED = True
        return

    executor_mod._get_event_type = _get_event_type

    # Patch every method that contains bare ``event.type`` accesses.
    _patch_execute_entity(executor_mod)
    _patch_execute_workflow(executor_mod)

    _PATCHED = True
    logger.info(
        "Applied monkey-patch for microsoft/agent-framework#3983 "
        "(devui _executor.py event.type -> _get_event_type)"
    )


def _patch_execute_entity(mod: object) -> None:
    """Wrap ``AgentFrameworkExecutor.execute_entity`` to guard ``event.type``."""
    cls = getattr(mod, "AgentFrameworkExecutor", None)
    if cls is None:
        return

    original = cls.execute_entity

    async def _patched_execute_entity(self, entity_id, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        async for event in original(self, entity_id, request, *args, **kwargs):
            yield event

    # We don't actually need to replace the whole generator — the root cause is
    # a bare ``event.type`` inside the method body.  Instead of rewriting the
    # generator we inject ``_get_event_type`` into the module namespace so that
    # any *new* code using it will work.  But the **existing** bytecode still
    # references the attribute directly.  The simplest safe approach is to make
    # dict events behave like objects by giving them a ``.type`` property via a
    # thin wrapper emitted from the generator.
    #
    # However, the cleanest minimal fix is to patch the *source* of the problem:
    # the error-path ``yield`` statements that emit raw dicts.  We wrap
    # ``_execute_workflow`` instead (see below).


def _patch_execute_workflow(mod: object) -> None:
    """Wrap ``AgentFrameworkExecutor._execute_workflow`` to make dict events safe."""
    cls = getattr(mod, "AgentFrameworkExecutor", None)
    if cls is None:
        return

    original_execute_workflow = getattr(cls, "_execute_workflow", None)
    if original_execute_workflow is None:
        return

    class _DictEvent(dict):
        """Dict subclass so dicts emitted on error paths expose ``.type`` as an attribute.

        Inheriting from ``dict`` ensures ``isinstance(event, dict)`` still
        returns ``True``, keeping downstream consumers happy.
        """

        def __getattr__(self, name: str) -> object:
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name) from None

        def __repr__(self) -> str:
            return f"_DictEvent({dict.__repr__(self)})"

    async def _patched_execute_workflow(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        async for event in original_execute_workflow(self, *args, **kwargs):
            if isinstance(event, dict):
                yield _DictEvent(event)
            else:
                yield event

    cls._execute_workflow = _patched_execute_workflow
