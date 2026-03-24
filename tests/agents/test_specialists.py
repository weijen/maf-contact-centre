from unittest.mock import MagicMock, patch

from agent_framework import Agent

from src.agents.billing import create_billing_agent, load_billing_definition
from src.agents.support import create_support_agent, load_support_definition


@patch("src.agents.billing.load_agent_definition")
def test_load_billing_definition_delegates_to_shared_loader(load_agent_definition_mock):
    definition = MagicMock()
    load_agent_definition_mock.return_value = definition

    result = load_billing_definition()

    assert result is definition
    load_agent_definition_mock.assert_called_once()
    assert load_agent_definition_mock.call_args.args[0] == "billing"


@patch("src.agents.support.load_agent_definition")
def test_load_support_definition_delegates_to_shared_loader(load_agent_definition_mock):
    definition = MagicMock()
    load_agent_definition_mock.return_value = definition

    result = load_support_definition()

    assert result is definition
    load_agent_definition_mock.assert_called_once()
    assert load_agent_definition_mock.call_args.args[0] == "support"


@patch("src.agents.billing.create_agent")
def test_create_billing_agent_delegates_to_shared_factory(create_agent_mock, tmp_path):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    client = MagicMock()
    credential = MagicMock()
    agent = MagicMock(spec=Agent)
    create_agent_mock.return_value = agent

    result = create_billing_agent(
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )

    assert result is agent
    create_agent_mock.assert_called_once_with(
        "billing",
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )


@patch("src.agents.support.create_agent")
def test_create_support_agent_delegates_to_shared_factory(create_agent_mock, tmp_path):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    client = MagicMock()
    credential = MagicMock()
    agent = MagicMock(spec=Agent)
    create_agent_mock.return_value = agent

    result = create_support_agent(
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )

    assert result is agent
    create_agent_mock.assert_called_once_with(
        "support",
        config_path=config_path,
        env_path=env_path,
        credential=credential,
        client=client,
    )