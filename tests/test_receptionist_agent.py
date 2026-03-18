from unittest.mock import MagicMock, patch

from agent_framework import Agent

from src.agents.receptionist import (
    create_receptionist_agent,
    load_azure_ai_model_config,
    load_receptionist_definition,
)


@patch("src.agents.receptionist.load_agent_definition")
def test_load_receptionist_definition_delegates_to_shared_loader(load_agent_definition_mock):
    definition = MagicMock()
    load_agent_definition_mock.return_value = definition

    result = load_receptionist_definition()

    assert result is definition
    load_agent_definition_mock.assert_called_once()
    assert load_agent_definition_mock.call_args.args[0] == "receptionist"


@patch("src.agents.receptionist.load_shared_azure_ai_model_config")
def test_load_azure_ai_model_config_delegates_to_shared_loader(load_model_config_mock, tmp_path):
    env_path = tmp_path / ".env"
    model_config = MagicMock()
    load_model_config_mock.return_value = model_config

    result = load_azure_ai_model_config(env_path=env_path)

    assert result is model_config
    load_model_config_mock.assert_called_once_with(env_path)


@patch("src.agents.receptionist.create_agent")
def test_create_receptionist_agent_delegates_to_shared_factory(create_agent_mock, tmp_path):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    client = MagicMock()
    credential = MagicMock()
    agent = MagicMock(spec=Agent)
    create_agent_mock.return_value = agent

    result = create_receptionist_agent(
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )

    assert result is agent
    create_agent_mock.assert_called_once_with(
        "receptionist",
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )
