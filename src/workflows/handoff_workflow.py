from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_framework import Agent, Workflow
from agent_framework.openai import OpenAIResponsesClient
from agent_framework.orchestrations import HandoffBuilder

from src.agents.common import create_agent
from src.core.config import DEFAULT_CONFIG_PATH, load_yaml


@dataclass(frozen=True)
class HandoffRule:
    from_agent: str
    to_agent: str
    description: str


def load_handoff_policy(config_path: Path = DEFAULT_CONFIG_PATH) -> list[HandoffRule]:
    config = load_yaml(config_path)
    handoffs = config.get("handoffs", [])
    return [
        HandoffRule(
            from_agent=h["from"],
            to_agent=h["to"],
            description=h["description"],
        )
        for h in handoffs
    ]


def build_handoff_workflow(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    client: OpenAIResponsesClient | None = None,
    agents: dict[str, Agent] | None = None,
) -> Workflow:
    rules = load_handoff_policy(config_path)

    agent_names = _unique_agent_names(rules)
    resolved_agents = agents or {
        name: create_agent(name, config_path=config_path, client=client)
        for name in agent_names
    }

    missing_agent_names = [name for name in agent_names if name not in resolved_agents]
    if missing_agent_names:
        raise ValueError(f"Missing agents for handoff workflow: {missing_agent_names}")

    participants = [resolved_agents[name] for name in agent_names]
    builder = HandoffBuilder(participants=participants)
    builder.with_start_agent(resolved_agents[agent_names[0]])

    for rule in rules:
        source = resolved_agents[rule.from_agent]
        target = resolved_agents[rule.to_agent]
        builder.add_handoff(source, [target], description=rule.description)

    return builder.build()


def _unique_agent_names(rules: list[HandoffRule]) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for rule in rules:
        for name in (rule.from_agent, rule.to_agent):
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names
