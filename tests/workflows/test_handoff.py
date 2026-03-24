from unittest.mock import MagicMock, patch

import pytest

from src.workflows.handoff_workflow import HandoffRule, build_handoff_workflow, load_handoff_policy


def test_load_handoff_policy_reads_all_rules(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Receptionist
    instructions: Greet callers.
  - name: billing
    description: Billing
    instructions: Handle billing.
  - name: support
    description: Support
    instructions: Handle support.
handoffs:
  - from: receptionist
    to: billing
    description: Transfer to billing
  - from: receptionist
    to: support
    description: Transfer to support
""".strip()
    )

    rules = load_handoff_policy(config_path)

    assert len(rules) == 2
    assert rules[0] == HandoffRule(from_agent="receptionist", to_agent="billing", description="Transfer to billing")
    assert rules[1] == HandoffRule(from_agent="receptionist", to_agent="support", description="Transfer to support")


def test_load_handoff_policy_returns_empty_when_no_handoffs(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("agents: []")

    rules = load_handoff_policy(config_path)

    assert rules == []


@patch("src.workflows.handoff_workflow.HandoffBuilder")
@patch("src.workflows.handoff_workflow.create_agent")
def test_build_handoff_workflow_creates_workflow_with_agents_and_handoffs(
    create_agent_mock, handoff_builder_cls, tmp_path
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Receptionist
    instructions: Greet callers.
  - name: billing
    description: Billing
    instructions: Handle billing.
  - name: support
    description: Support
    instructions: Handle support.
handoffs:
  - from: receptionist
    to: billing
    description: Transfer to billing
  - from: receptionist
    to: support
    description: Transfer to support
""".strip()
    )

    receptionist = MagicMock(name="receptionist_agent")
    receptionist.name = "receptionist"
    billing = MagicMock(name="billing_agent")
    billing.name = "billing"
    support = MagicMock(name="support_agent")
    support.name = "support"

    def fake_create_agent(agent_name, **kwargs):
        return {"receptionist": receptionist, "billing": billing, "support": support}[agent_name]

    create_agent_mock.side_effect = fake_create_agent
    builder_instance = handoff_builder_cls.return_value
    builder_instance.add_handoff.return_value = builder_instance
    client = MagicMock()

    workflow = build_handoff_workflow(config_path=config_path, client=client)

    assert create_agent_mock.call_count == 3
    called_names = sorted(c.args[0] for c in create_agent_mock.call_args_list)
    assert called_names == ["billing", "receptionist", "support"]

    handoff_builder_cls.assert_called_once()
    participants = handoff_builder_cls.call_args[1]["participants"]
    assert set(participants) == {receptionist, billing, support}

    assert builder_instance.add_handoff.call_count == 2
    builder_instance.add_handoff.assert_any_call(receptionist, [billing], description="Transfer to billing")
    builder_instance.add_handoff.assert_any_call(receptionist, [support], description="Transfer to support")

    builder_instance.build.assert_called_once()
    assert workflow is builder_instance.build.return_value


@patch("src.workflows.handoff_workflow.HandoffBuilder")
@patch("src.workflows.handoff_workflow.create_agent")
def test_build_handoff_workflow_only_creates_agents_involved_in_handoffs(
    create_agent_mock, handoff_builder_cls, tmp_path
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Receptionist
    instructions: Greet callers.
  - name: billing
    description: Billing
    instructions: Handle billing.
  - name: support
    description: Support
    instructions: Handle support.
handoffs:
  - from: receptionist
    to: billing
    description: Transfer to billing
""".strip()
    )

    receptionist = MagicMock(name="receptionist_agent")
    receptionist.name = "receptionist"
    billing = MagicMock(name="billing_agent")
    billing.name = "billing"

    def fake_create_agent(agent_name, **kwargs):
        return {"receptionist": receptionist, "billing": billing}[agent_name]

    create_agent_mock.side_effect = fake_create_agent
    builder_instance = handoff_builder_cls.return_value
    builder_instance.add_handoff.return_value = builder_instance
    client = MagicMock()

    workflow = build_handoff_workflow(config_path=config_path, client=client)

    called_names = sorted(c.args[0] for c in create_agent_mock.call_args_list)
    assert called_names == ["billing", "receptionist"]

    builder_instance.build.assert_called_once()
    assert workflow is builder_instance.build.return_value


@patch("src.workflows.handoff_workflow.HandoffBuilder")
@patch("src.workflows.handoff_workflow.create_agent")
def test_build_handoff_workflow_reuses_provided_agents(
    create_agent_mock, handoff_builder_cls, tmp_path
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
agents:
  - name: receptionist
    description: Receptionist
    instructions: Greet callers.
  - name: billing
    description: Billing
    instructions: Handle billing.
handoffs:
  - from: receptionist
    to: billing
    description: Transfer to billing
""".strip()
    )

    receptionist = MagicMock(name="receptionist_agent")
    receptionist.name = "receptionist"
    billing = MagicMock(name="billing_agent")
    billing.name = "billing"
    provided_agents = {
        "receptionist": receptionist,
        "billing": billing,
    }
    builder_instance = handoff_builder_cls.return_value

    workflow = build_handoff_workflow(config_path=config_path, agents=provided_agents)

    create_agent_mock.assert_not_called()
    handoff_builder_cls.assert_called_once_with(participants=[receptionist, billing])
    builder_instance.with_start_agent.assert_called_once_with(receptionist)
    builder_instance.add_handoff.assert_called_once_with(receptionist, [billing], description="Transfer to billing")
    assert workflow is builder_instance.build.return_value
