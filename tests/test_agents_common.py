from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent_framework import Agent

from src.agents.common import (
    ManagedFoundryResponsesClient,
    create_agent,
    load_agent_definition,
    load_azure_ai_model_config,
)


@pytest.mark.parametrize(
    ("agent_name", "description", "instructions"),
    [
        ("receptionist", "Front desk triage", "Welcome callers and route them.\n"),
        ("billing", "Billing desk", "Help with payments.\n"),
        ("support", "Support desk", "Fix product issues.\n"),
    ],
)
def test_load_agent_definition_reads_inline_instructions(tmp_path, agent_name, description, instructions):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Front desk triage
    instructions: |
      Welcome callers and route them.
  - name: billing
    description: Billing desk
    instructions: |
      Help with payments.
  - name: support
    description: Support desk
    instructions: |
      Fix product issues.
""".strip()
    )

    definition = load_agent_definition(agent_name, config_path)

    assert definition.name == agent_name
    assert definition.description == description
    assert definition.instructions == instructions


def test_load_agent_definition_reads_instructions_file(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_file = prompts_dir / "greeter.md"
    prompt_file.write_text("You are a greeter.\n", encoding="utf-8")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: greeter
    description: A greeter
    instructions_file: "prompts/greeter.md"
""".strip()
    )

    definition = load_agent_definition("greeter", config_path)

    assert definition.name == "greeter"
    assert definition.instructions == "You are a greeter.\n"


def test_load_agent_definition_raises_when_both_instructions_and_file(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: bad
    description: Ambiguous
    instructions: "inline text"
    instructions_file: "some/file.md"
""".strip()
    )

    with pytest.raises(ValueError, match="both"):
        load_agent_definition("bad", config_path)


def test_load_agent_definition_raises_when_no_instructions(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: empty
    description: No instructions
""".strip()
    )

    with pytest.raises(ValueError, match="must define"):
        load_agent_definition("empty", config_path)


def test_load_agent_definition_raises_when_file_not_found(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: ghost
    description: Missing file
    instructions_file: "does_not_exist.md"
""".strip()
    )

    with pytest.raises(FileNotFoundError, match="does_not_exist.md"):
        load_agent_definition("ghost", config_path)


def test_load_agent_definition_raises_when_missing(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("agents: []")

    with pytest.raises(ValueError, match="receptionist"):
        load_agent_definition("receptionist", config_path)


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

    model_config = load_azure_ai_model_config(env_path=env_path)

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


@patch("src.agents.common.ManagedFoundryResponsesClient")
@patch("src.agents.common.AIProjectClient")
@patch("src.agents.common.DefaultAzureCredential")
def test_create_agent_uses_env_file_values(
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
  - name: billing
    description: Billing desk
    instructions: |
      Help with payments.
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

    agent = create_agent(
        "billing",
        config_path=config_path,
        env_path=env_path,
    )

    assert isinstance(agent, Agent)
    assert agent.name == "billing"
    assert agent.description == "Billing desk"
    assert agent.client is client
    assert agent.default_options["instructions"] == "Help with payments."
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


@patch("src.agents.common.build_chat_client")
def test_create_agent_uses_injected_client(build_chat_client_mock, tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: support
    description: Support desk
    instructions: |
      Fix product issues.
""".strip()
    )

    client = MagicMock()

    agent = create_agent(
        "support",
        config_path=config_path,
        client=client,
    )

    assert isinstance(agent, Agent)
    assert agent.name == "support"
    assert agent.client is client
    build_chat_client_mock.assert_not_called()


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


@pytest.mark.anyio
async def test_managed_foundry_responses_client_does_not_close_external_credential() -> None:
    async_openai_client = AsyncMock()
    project_client = AsyncMock()
    credential = AsyncMock()
    client = ManagedFoundryResponsesClient(
        project_client=project_client,
        credential=credential,
        owns_credential=False,
        model_id="gpt-4.1",
        async_client=async_openai_client,
    )

    async with client:
        pass

    async_openai_client.close.assert_awaited_once()
    project_client.close.assert_awaited_once()
    credential.close.assert_not_awaited()