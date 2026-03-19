from __future__ import annotations

from typing import Any

from src.tools.billing_tools import BillingTools
from src.tools.receptionist_tools import ReceptionistTools
from src.tools.support_tools import SupportPlugin

# Maps plugin names used in config.yaml to their tool classes.
PLUGIN_REGISTRY: dict[str, type] = {
    "billing_tools": BillingTools,
    "receptionist_tools": ReceptionistTools,
    "support_tools": SupportPlugin,
}


def load_plugins(plugin_names: list[str]) -> list[Any]:
    """Extract bound FunctionTool objects from plugin classes for the given config names."""
    from agent_framework import FunctionTool

    tools: list[Any] = []
    for name in plugin_names:
        cls = PLUGIN_REGISTRY.get(name)
        if cls is None:
            raise ValueError(
                f"Unknown plugin '{name}'. Available plugins: {sorted(PLUGIN_REGISTRY)}"
            )
        instance = cls()
        for attr_name in vars(type(instance)):
            attr = getattr(instance, attr_name)
            if isinstance(attr, FunctionTool):
                tools.append(attr)
    return tools
