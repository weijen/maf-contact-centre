from unittest.mock import AsyncMock
from unittest.mock import patch

from main import main


@patch("main.create_receptionist_agent")
def test_main_defaults_to_status_command(create_receptionist_agent_mock, capsys):
    agent = AsyncMock()
    agent.name = "receptionist"
    agent.client.model_id = "gpt-53-chat"
    agent.__aenter__.return_value = agent
    agent.__aexit__.return_value = None
    create_receptionist_agent_mock.return_value = agent

    main()

    captured = capsys.readouterr()
    assert captured.out == "Loaded receptionist agent using deployment gpt-53-chat.\n"
    agent.__aenter__.assert_awaited_once()
    agent.__aexit__.assert_awaited_once()


@patch("main.serve_devui")
def test_main_runs_devui_subcommand_with_auto_open_enabled_by_default(serve_devui_mock):
    main(["devui", "--port", "8081", "--mode", "user"])

    serve_devui_mock.assert_called_once_with(
        host="127.0.0.1",
        port=8081,
        auto_open=True,
        instrumentation_enabled=False,
        mode="user",
    )


@patch("main.serve_devui")
def test_main_allows_disabling_devui_auto_open(serve_devui_mock):
    main(["devui", "--no-auto-open"])

    serve_devui_mock.assert_called_once_with(
        host="127.0.0.1",
        port=8080,
        auto_open=False,
        instrumentation_enabled=False,
        mode="developer",
    )
