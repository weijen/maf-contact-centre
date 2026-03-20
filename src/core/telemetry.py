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


def flush_telemetry() -> None:
    """Force-flush all OpenTelemetry providers so pending spans/metrics/logs are exported."""
    from opentelemetry import trace, metrics
    from opentelemetry._logs import get_logger_provider

    tp = trace.get_tracer_provider()
    if hasattr(tp, "force_flush"):
        tp.force_flush()

    mp = metrics.get_meter_provider()
    if hasattr(mp, "force_flush"):
        mp.force_flush()

    lp = get_logger_provider()
    if hasattr(lp, "force_flush"):
        lp.force_flush()
