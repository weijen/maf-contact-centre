import pytest

from agent_framework import FunctionTool

from src.tools import PLUGIN_REGISTRY, load_plugins
from src.tools.billing_tools import BillingTools
from src.tools.receptionist_tools import ReceptionistTools
from src.tools.support_tools import SupportPlugin


class TestPluginRegistry:
    def test_contains_billing_tools(self):
        assert PLUGIN_REGISTRY["billing_tools"] is BillingTools

    def test_contains_receptionist_tools(self):
        assert PLUGIN_REGISTRY["receptionist_tools"] is ReceptionistTools

    def test_contains_support_tools(self):
        assert PLUGIN_REGISTRY["support_tools"] is SupportPlugin

    def test_has_exactly_three_entries(self):
        assert len(PLUGIN_REGISTRY) == 3


class TestLoadPlugins:
    def test_loads_single_plugin(self):
        plugins = load_plugins(["billing_tools"])

        assert len(plugins) == 4
        assert all(isinstance(p, FunctionTool) for p in plugins)

    def test_loads_multiple_plugins(self):
        plugins = load_plugins(["billing_tools", "support_tools"])

        assert len(plugins) == 8
        assert all(isinstance(p, FunctionTool) for p in plugins)

    def test_loads_all_plugins(self):
        plugins = load_plugins(["billing_tools", "receptionist_tools", "support_tools"])

        assert len(plugins) == 10

    def test_returns_empty_list_for_no_plugins(self):
        plugins = load_plugins([])

        assert plugins == []

    def test_raises_value_error_for_unknown_plugin(self):
        with pytest.raises(ValueError, match="Unknown plugin 'nonexistent'"):
            load_plugins(["nonexistent"])

    def test_error_message_lists_available_plugins(self):
        with pytest.raises(ValueError, match="Available plugins"):
            load_plugins(["bad_name"])

    def test_each_call_returns_new_instances(self):
        plugins1 = load_plugins(["billing_tools"])
        plugins2 = load_plugins(["billing_tools"])

        assert plugins1[0] is not plugins2[0]
