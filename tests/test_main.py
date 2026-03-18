from unittest.mock import AsyncMock
from unittest.mock import patch

from main import main


@patch("main.create_receptionist_agent")
def test_main(create_receptionist_agent_mock, capsys):
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
