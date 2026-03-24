from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Any

from agent_framework.openai import OpenAIResponsesClient
from agent_framework_devui import register_cleanup, serve as devui_serve

from src.agents.billing import create_billing_agent
from src.agents.common import ManagedFoundryResponsesClient, build_chat_client
from src.agents.receptionist import create_receptionist_agent
from src.agents.support import create_support_agent
from src.core.config import DEFAULT_CONFIG_PATH, DEFAULT_ENV_PATH
from src.core.patches import apply_devui_executor_patch
from src.core.telemetry import flush_telemetry, setup_telemetry
from src.workflows.handoff_workflow import build_handoff_workflow


def build_devui_entities(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
    client: ManagedFoundryResponsesClient | OpenAIResponsesClient | None = None,
) -> list[Any]:
    resolved_client = client or build_chat_client(env_path=env_path)

    receptionist = create_receptionist_agent(
        config_path=config_path,
        env_path=env_path,
        client=resolved_client,
    )
    billing = create_billing_agent(
        config_path=config_path,
        env_path=env_path,
        client=resolved_client,
    )
    support = create_support_agent(
        config_path=config_path,
        env_path=env_path,
        client=resolved_client,
    )
    agents = {
        "receptionist": receptionist,
        "billing": billing,
        "support": support,
    }
    handoff_workflow = build_handoff_workflow(
        config_path=config_path,
        client=resolved_client,
        agents=agents,
    )

    return [receptionist, billing, support, handoff_workflow]


def serve_devui(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
    host: str = "127.0.0.1",
    port: int = 8080,
    auto_open: bool = True,
    instrumentation_enabled: bool = False,
    mode: str = "developer",
    client: ManagedFoundryResponsesClient | OpenAIResponsesClient | None = None,
) -> None:
    setup_telemetry()
    apply_devui_executor_patch()

    owns_client = client is None
    resolved_client = client or build_chat_client(env_path=env_path)
    cleanup_registered = False

    try:
        entities = build_devui_entities(
            config_path=config_path,
            env_path=env_path,
            client=resolved_client,
        )

        if owns_client:
            register_cleanup(entities[-1], resolved_client.close)
            cleanup_registered = True

        devui_serve(
            entities=entities,
            host=host,
            port=port,
            auto_open=auto_open,
            instrumentation_enabled=instrumentation_enabled,
            mode=mode,
        )
    finally:
        if owns_client and not cleanup_registered:
            _run_cleanup(resolved_client.close)
        flush_telemetry()


def _run_cleanup(cleanup_hook: Any) -> None:
    result = cleanup_hook()
    if inspect.isawaitable(result):
        asyncio.run(result)