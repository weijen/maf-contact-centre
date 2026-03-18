from __future__ import annotations

from pathlib import Path

from agent_framework import Agent
from agent_framework.openai import OpenAIResponsesClient
from azure.core.credentials_async import AsyncTokenCredential

from src.agents.common import AgentDefinition, DEFAULT_CONFIG_PATH, DEFAULT_ENV_PATH, ManagedFoundryResponsesClient
from src.agents.common import create_agent, load_agent_definition


def load_support_definition(config_path: Path = DEFAULT_CONFIG_PATH) -> AgentDefinition:
    return load_agent_definition("support", config_path)


def create_support_agent(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
    credential: AsyncTokenCredential | None = None,
    client: ManagedFoundryResponsesClient | OpenAIResponsesClient | None = None,
) -> Agent:
    return create_agent(
        "support",
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )