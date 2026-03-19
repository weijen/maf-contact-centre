from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_framework import Agent, Workflow
from agent_framework.openai import OpenAIResponsesClient
from agent_framework.orchestrations import HandoffBuilder

from src.agents.common import DEFAULT_CONFIG_PATH, create_agent, load_yaml


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
) -> Workflow:
    rules = load_handoff_policy(config_path)

    agent_names = _unique_agent_names(rules)
    agents: dict[str, Agent] = {
        name: create_agent(name, config_path=config_path, client=client)
        for name in agent_names
    }

    builder = HandoffBuilder(participants=list(agents.values()))

    for rule in rules:
        source = agents[rule.from_agent]
        target = agents[rule.to_agent]
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
