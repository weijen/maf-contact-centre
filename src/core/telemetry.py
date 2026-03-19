"""OpenTelemetry setup for Azure AI Foundry tracing.

Call ``setup_telemetry()`` once at application startup, **before** any agent or
workflow code runs.  Traces, logs, and metrics are exported to Application
Insights and visible in the AI Foundry portal's Tracing tab.
"""

from __future__ import annotations

import os


def setup_telemetry() -> None:
    """Configure Azure Monitor export and enable Agent Framework instrumentation.

    Reads ``APPLICATIONINSIGHTS_CONNECTION_STRING`` from the environment.  If
    the variable is not set the function is a no-op so local development still
    works without Azure Monitor.
    """
    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        return

    from azure.monitor.opentelemetry import configure_azure_monitor
    from agent_framework.observability import enable_instrumentation

    configure_azure_monitor(connection_string=connection_string)
    enable_instrumentation(enable_sensitive_data=True)
