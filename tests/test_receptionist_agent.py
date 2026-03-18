from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent_framework import Agent

from src.agents.receptionist import (
    ManagedFoundryResponsesClient,
    create_receptionist_agent,
    load_azure_ai_model_config,
    load_receptionist_definition,
)


def test_load_receptionist_definition_reads_prompt_from_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Front desk triage
    instructions: |
      Welcome callers and route them.
  - name: support
    description: Tech support
    instructions: |
      Fix things.
""".strip()
    )

    definition = load_receptionist_definition(config_path)

    assert definition.name == "receptionist"
    assert definition.description == "Front desk triage"
    assert definition.instructions == "Welcome callers and route them.\n"


def test_load_receptionist_definition_raises_when_missing(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("agents: []")

    with pytest.raises(ValueError, match="receptionist"):
        load_receptionist_definition(config_path)


def test_load_azure_ai_model_config_reads_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "AZURE_AI_PROJECT_ENDPOINT=https://env-example.cognitiveservices.azure.com/",
                "AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-53-chat-env",
            ]
        )
    )

    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", raising=False)

    model_config = load_azure_ai_model_config(env_path=env_path)

    assert model_config.project_endpoint == "https://env-example.cognitiveservices.azure.com/"
    assert model_config.model_deployment_name == "gpt-53-chat-env"


def test_load_azure_ai_model_config_accepts_legacy_openai_env_names(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "AZURE_OPENAI_ENDPOINT=https://legacy-example.cognitiveservices.azure.com/",
                "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-53-chat-legacy",
            ]
        )
    )

    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", raising=False)

    model_config = load_azure_ai_model_config(
        env_path=env_path,
    )

    assert model_config.project_endpoint == "https://legacy-example.cognitiveservices.azure.com/"
    assert model_config.model_deployment_name == "gpt-53-chat-legacy"


def test_load_azure_ai_model_config_raises_when_env_is_incomplete(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("AZURE_AI_PROJECT_ENDPOINT=https://env-example.cognitiveservices.azure.com/")

    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", raising=False)

    with pytest.raises(ValueError, match="environment configuration"):
        load_azure_ai_model_config(env_path=env_path)


@patch("src.agents.receptionist.ManagedFoundryResponsesClient")
@patch("src.agents.receptionist.AIProjectClient")
@patch("src.agents.receptionist.DefaultAzureCredential")
def test_create_receptionist_agent_uses_env_file_values(
    default_credential_mock,
    ai_project_client_mock,
    chat_client_mock,
    tmp_path,
    monkeypatch,
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Front desk triage
    instructions: |
      Welcome callers and route them.
""".strip()
    )

    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "AZURE_AI_PROJECT_ENDPOINT=https://env-example.cognitiveservices.azure.com/",
                "AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-53-chat-env",
            ]
        )
    )

    credential = MagicMock()
    project_client = MagicMock()
    async_openai_client = MagicMock()
    client = MagicMock()
    default_credential_mock.return_value = credential
    ai_project_client_mock.return_value = project_client
    project_client.get_openai_client.return_value = async_openai_client
    chat_client_mock.return_value = client
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", raising=False)

    agent = create_receptionist_agent(
        config_path=config_path,
        env_path=env_path,
    )

    assert isinstance(agent, Agent)
    assert agent.name == "receptionist"
    assert agent.description == "Front desk triage"
    assert agent.client is client
    assert agent.default_options["instructions"] == "Welcome callers and route them."
    ai_project_client_mock.assert_called_once_with(
        endpoint="https://env-example.cognitiveservices.azure.com/",
        credential=credential,
    )
    project_client.get_openai_client.assert_called_once_with()
    chat_client_mock.assert_called_once_with(
        project_client=project_client,
        credential=credential,
        owns_credential=True,
        model_id="gpt-53-chat-env",
        async_client=async_openai_client,
    )


@pytest.mark.anyio
async def test_managed_foundry_responses_client_closes_owned_resources() -> None:
    async_openai_client = AsyncMock()
    project_client = AsyncMock()
    credential = AsyncMock()
    client = ManagedFoundryResponsesClient(
        project_client=project_client,
        credential=credential,
        owns_credential=True,
        model_id="gpt-4.1",
        async_client=async_openai_client,
    )

    async with client:
        pass

    async_openai_client.close.assert_awaited_once()
    project_client.close.assert_awaited_once()
    credential.close.assert_awaited_once()
