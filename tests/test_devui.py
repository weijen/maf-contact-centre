from unittest.mock import MagicMock, patch

from src.devui import build_devui_entities, serve_devui


@patch("src.devui.build_handoff_workflow")
@patch("src.devui.create_support_agent")
@patch("src.devui.create_billing_agent")
@patch("src.devui.create_receptionist_agent")
def test_build_devui_entities_reuses_shared_client(
    create_receptionist_agent_mock,
    create_billing_agent_mock,
    create_support_agent_mock,
    build_handoff_workflow_mock,
):
    client = MagicMock()
    receptionist = MagicMock(name="receptionist")
    billing = MagicMock(name="billing")
    support = MagicMock(name="support")
    workflow = MagicMock(name="workflow")

    create_receptionist_agent_mock.return_value = receptionist
    create_billing_agent_mock.return_value = billing
    create_support_agent_mock.return_value = support
    build_handoff_workflow_mock.return_value = workflow

    entities = build_devui_entities(client=client)

    assert entities == [receptionist, billing, support, workflow]
    create_receptionist_agent_mock.assert_called_once_with(
        config_path=create_receptionist_agent_mock.call_args.kwargs["config_path"],
        env_path=create_receptionist_agent_mock.call_args.kwargs["env_path"],
        client=client,
    )
    create_billing_agent_mock.assert_called_once_with(
        config_path=create_billing_agent_mock.call_args.kwargs["config_path"],
        env_path=create_billing_agent_mock.call_args.kwargs["env_path"],
        client=client,
    )
    create_support_agent_mock.assert_called_once_with(
        config_path=create_support_agent_mock.call_args.kwargs["config_path"],
        env_path=create_support_agent_mock.call_args.kwargs["env_path"],
        client=client,
    )
    build_handoff_workflow_mock.assert_called_once_with(
        config_path=build_handoff_workflow_mock.call_args.kwargs["config_path"],
        client=client,
        agents={
            "receptionist": receptionist,
            "billing": billing,
            "support": support,
        },
    )


@patch("src.devui.flush_telemetry")
@patch("src.devui.devui_serve")
@patch("src.devui.register_cleanup")
@patch("src.devui.build_devui_entities")
@patch("src.devui.build_chat_client")
@patch("src.devui.setup_telemetry")
def test_serve_devui_registers_cleanup_for_owned_client(
    setup_telemetry_mock,
    build_chat_client_mock,
    build_devui_entities_mock,
    register_cleanup_mock,
    devui_serve_mock,
    flush_telemetry_mock,
):
    client = MagicMock()
    workflow = MagicMock(name="workflow")
    build_chat_client_mock.return_value = client
    build_devui_entities_mock.return_value = [MagicMock(), MagicMock(), MagicMock(), workflow]

    serve_devui(port=9000, auto_open=True, instrumentation_enabled=True)

    setup_telemetry_mock.assert_called_once_with()
    build_chat_client_mock.assert_called_once()
    build_devui_entities_mock.assert_called_once_with(
        config_path=build_devui_entities_mock.call_args.kwargs["config_path"],
        env_path=build_devui_entities_mock.call_args.kwargs["env_path"],
        client=client,
    )
    register_cleanup_mock.assert_called_once_with(workflow, client.close)
    devui_serve_mock.assert_called_once_with(
        entities=build_devui_entities_mock.return_value,
        host="127.0.0.1",
        port=9000,
        auto_open=True,
        instrumentation_enabled=True,
        mode="developer",
    )
    flush_telemetry_mock.assert_called_once_with()


@patch("src.devui.flush_telemetry")
@patch("src.devui.devui_serve")
@patch("src.devui.register_cleanup")
@patch("src.devui.build_devui_entities")
@patch("src.devui.build_chat_client")
def test_serve_devui_does_not_create_or_register_cleanup_for_external_client(
    build_chat_client_mock,
    build_devui_entities_mock,
    register_cleanup_mock,
    devui_serve_mock,
    flush_telemetry_mock,
):
    external_client = MagicMock()
    build_devui_entities_mock.return_value = [MagicMock()]

    serve_devui(client=external_client)

    build_chat_client_mock.assert_not_called()
    register_cleanup_mock.assert_not_called()
    devui_serve_mock.assert_called_once()
    flush_telemetry_mock.assert_called_once_with()