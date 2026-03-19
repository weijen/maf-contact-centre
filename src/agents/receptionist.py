from __future__ import annotations

from pathlib import Path

from agent_framework import Agent
from agent_framework.openai import OpenAIResponsesClient
from azure.core.credentials_async import AsyncTokenCredential

from src.agents.common import AgentDefinition, AzureAIModelConfig, ManagedFoundryResponsesClient
from src.agents.common import create_agent, load_agent_definition
from src.core.config import DEFAULT_CONFIG_PATH, DEFAULT_ENV_PATH
from src.agents.common import load_azure_ai_model_config as load_shared_azure_ai_model_config


def load_receptionist_definition(config_path: Path = DEFAULT_CONFIG_PATH) -> AgentDefinition:
    return load_agent_definition("receptionist", config_path)


def load_azure_ai_model_config(
    env_path: Path = DEFAULT_ENV_PATH,
) -> AzureAIModelConfig:
    return load_shared_azure_ai_model_config(env_path)


def create_receptionist_agent(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
    credential: AsyncTokenCredential | None = None,
    client: ManagedFoundryResponsesClient | OpenAIResponsesClient | None = None,
) -> Agent:
    return create_agent(
        "receptionist",
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )
