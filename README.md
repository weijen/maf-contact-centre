# Customer Service Multi-Agent Prototype

## Goal

Build a Microsoft Agent Framework contact centre prototype with three agents:

- receptionist
- billing
- support

All conversations start with the receptionist. The receptionist prompt is defined in `config.yaml`, and the model connection is loaded from `.env`.

## Current status

- `receptionist` is implemented as an `agent_framework.Agent`
- the receptionist system prompt is loaded from `config.yaml`
- the Azure AI Foundry project endpoint and model deployment name are loaded from `.env`
- `billing`, `support`, and handoff workflow files are still scaffolded

## User flow

All users start with receptionist.

Receptionist either:

- answers simple general questions
- hands off to billing
- hands off to support

## V1 scope

- billing: account balance, payment status
- support: password reset, create support ticket
- receptionist: greeting, office hours, triage

## Out of scope

- real authentication
- real database
- real payment processing
- production-grade UI

## Requirements

- Python 3.13+
- `uv`
- Azure credentials available to `DefaultAzureCredential`

## Local setup

1. Create or update `.env` from `.env.example`.
2. Fill in the Azure AI Foundry connection values.
3. Install dependencies with `uv sync`.
4. Run the entry point with `uv run python main.py`.

## Recommended usage

Use the receptionist agent as an async context manager so the underlying Azure and OpenAI clients are closed cleanly after each run.

```python
import asyncio

from src.agents.receptionist import create_receptionist_agent


async def main() -> None:
	async with create_receptionist_agent() as agent:
		response = await agent.run("Hello, what can you help me with?")
		print(response.messages[0].text)


asyncio.run(main())
```

Notes:

- this avoids unclosed client session warnings
- `main.py` remains a minimal smoke-test entry point

## Environment variables

Required:

```dotenv
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com/
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-53-chat
```

Optional:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

Notes:

- `.env` is ignored by git
- process environment variables override values from `.env`
- prefer `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- legacy `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` are still accepted as fallback names
- both endpoint and deployment values must be present in `.env`

## Run

Run the current prototype:

```bash
uv run python main.py
```

Current behavior:

- loads the receptionist definition from `config.yaml`
- creates the Azure AI Foundry client
- prints the selected agent name and deployment
- for real conversations, prefer the async context-manager example above

## Test

Run the test suite:

```bash
uv run pytest
```

Run only the receptionist-focused tests:

```bash
uv run pytest tests/test_receptionist_agent.py tests/test_main.py
```

## Configuration sources

The receptionist agent currently reads configuration from these sources:

1. `config.yaml` for agent description and system prompt
2. `.env` for Azure AI project endpoint and model deployment name
