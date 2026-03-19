from __future__ import annotations

from contextlib import suppress
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_framework import Agent
from agent_framework.openai import OpenAIResponsesClient
from azure.ai.projects.aio import AIProjectClient
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import DefaultAzureCredential
from dotenv import dotenv_values
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    instructions: str


@dataclass(frozen=True)
class AzureAIModelConfig:
    project_endpoint: str
    model_deployment_name: str


class ManagedFoundryResponsesClient(OpenAIResponsesClient):
    def __init__(
        self,
        *,
        project_client: AIProjectClient,
        credential: AsyncTokenCredential,
        owns_credential: bool,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._project_client = project_client
        self._credential = credential
        self._owns_credential = owns_credential

    async def __aenter__(self) -> "ManagedFoundryResponsesClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if hasattr(self.client, "close"):
            with suppress(Exception):
                await self.client.close()
        with suppress(Exception):
            await self._project_client.close()
        if self._owns_credential and hasattr(self._credential, "close"):
            with suppress(Exception):
                await self._credential.close()


def load_agent_definition(agent_name: str, config_path: Path = DEFAULT_CONFIG_PATH) -> AgentDefinition:
    config = load_yaml(config_path)
    agents = config.get("agents", [])

    for agent in agents:
        if agent.get("name") != agent_name:
            continue

        instructions = agent["instructions"]
        if not instructions.endswith("\n"):
            instructions = f"{instructions}\n"

        return AgentDefinition(
            name=agent["name"],
            description=agent["description"],
            instructions=instructions,
        )

    raise ValueError(f"Could not find an agent definition for {agent_name} in {config_path}.")


def load_yaml(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file_handle:
        loaded = yaml.safe_load(file_handle)

    if not isinstance(loaded, dict):
        raise ValueError(f"Expected {config_path} to contain a mapping at the top level.")

    return loaded


def load_azure_ai_model_config(env_path: Path = DEFAULT_ENV_PATH) -> AzureAIModelConfig:
    env_config = _load_azure_ai_env_config(env_path)
    project_endpoint = env_config.get("project_endpoint")
    model_deployment_name = env_config.get("model_deployment_name")

    if project_endpoint is None:
        raise ValueError(f"Could not resolve an Azure AI project endpoint from {env_path}.")
    if model_deployment_name is None:
        raise ValueError(
            "Could not resolve the Azure AI model deployment name from environment configuration. "
            f"Checked {env_path}."
        )

    return AzureAIModelConfig(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
    )


def build_chat_client(
    *,
    credential: AsyncTokenCredential | None = None,
    env_path: Path = DEFAULT_ENV_PATH,
) -> OpenAIResponsesClient:
    model_config = load_azure_ai_model_config(env_path=env_path)
    owns_credential = credential is None
    resolved_credential = credential or DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=model_config.project_endpoint,
        credential=resolved_credential,
    )
    async_openai_client = project_client.get_openai_client()

    return ManagedFoundryResponsesClient(
        project_client=project_client,
        credential=resolved_credential,
        owns_credential=owns_credential,
        model_id=model_config.model_deployment_name,
        async_client=async_openai_client,
    )


def create_agent(
    agent_name: str,
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    env_path: Path = DEFAULT_ENV_PATH,
    credential: AsyncTokenCredential | None = None,
    client: ManagedFoundryResponsesClient | OpenAIResponsesClient | None = None,
) -> Agent:
    definition = load_agent_definition(agent_name, config_path)
    resolved_client = client or build_chat_client(
        credential=credential,
        env_path=env_path,
    )

    return Agent(
        client=resolved_client,
        name=definition.name,
        description=definition.description,
        instructions=definition.instructions.rstrip("\n"),
    )


def _load_azure_ai_env_config(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return _read_azure_ai_environment(os.environ)

    env_values = {
        key: value
        for key, value in dotenv_values(env_path).items()
        if isinstance(value, str) and value.strip()
    }
    process_values = {key: value for key, value in os.environ.items() if value.strip()}
    merged_values = {**env_values, **process_values}
    return _read_azure_ai_environment(merged_values)


def _read_azure_ai_environment(values: Mapping[str, str]) -> dict[str, str]:
    project_endpoint = values.get("AZURE_AI_PROJECT_ENDPOINT") or values.get("AZURE_OPENAI_ENDPOINT")
    model_deployment_name = values.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or values.get(
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
    )

    config: dict[str, str] = {}
    if project_endpoint:
        config["project_endpoint"] = project_endpoint
    if model_deployment_name:
        config["model_deployment_name"] = model_deployment_name

    return config