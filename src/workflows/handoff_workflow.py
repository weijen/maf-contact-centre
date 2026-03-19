from __future__ import annotations

from pathlib import Path

from agent_framework import Agent, Workflow
from agent_framework.openai import OpenAIResponsesClient
from agent_framework.orchestrations import HandoffBuilder

from src.agents.common import DEFAULT_CONFIG_PATH, HandoffRule, create_agent, load_handoff_policy


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
