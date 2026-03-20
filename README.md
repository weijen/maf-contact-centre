# Customer Service Multi-Agent Prototype

A multi-agent contact centre built with the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) featuring intelligent handoffs, automated evaluation, and OpenTelemetry tracing.

## Agents

All conversations start with the **receptionist**, which triages and hands off as needed:

| Agent | Role |
|---|---|
| **Receptionist** | Greeting, office hours, triage; routes to billing or support |
| **Billing** | Account balance, payment status, invoices, payment arrangements. Verifies account ID before revealing sensitive data; asks for missing identifiers before acting. |
| **Support** | Password reset, technical troubleshooting, ticket creation. Asks for user ID before sensitive actions; creates a ticket if the issue cannot be resolved quickly. |

Handoffs are bidirectional between all three agents (configured in `config.yaml`).

## Project structure

```
main.py                         # entry point — interactive conversation
config.yaml                     # agent definitions, system prompts, handoff rules
src/
  agents/                       # agent factories (receptionist, billing, support)
  core/                         # shared config loading, telemetry
  tools/
    mock_data.py                # stable mock data (users, accounts, payments, tickets)
    billing_tools.py            # billing agent tools (backed by mock_data)
    support_tools.py            # support agent tools (backed by mock_data)
    receptionist_tools.py       # receptionist agent tools
  workflows/                    # HandoffBuilder-based multi-agent workflow
scripts/
  run_manual_tests.py           # automated evaluation runner
data/
  manual_test_cases_v1.json     # 9 routing test cases
infra/                          # Terraform (Azure AI Foundry, App Insights, etc.)
tests/                          # pytest unit tests
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Azure credentials available to `DefaultAzureCredential`

## Local setup

1. Copy `.env.example` to `.env` and fill in the Azure AI Foundry connection values.
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Run the entry point:
   ```bash
   uv run python main.py
   ```

## Evaluation

Run the automated routing evaluation against all 9 test cases:

```bash
uv run python scripts/run_manual_tests.py
```

This uses the [azure-ai-evaluation](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/develop/evaluate-sdk) SDK with four evaluators:

| Evaluator | Type | Description |
|---|---|---|
| `routing_correctness` | Deterministic | Checks handler and handoff match expected values |
| `CoherenceEvaluator` | LLM-judged | Response coherence (1–5) |
| `RelevanceEvaluator` | LLM-judged | Response relevance to query (1–5) |

Results are written to `data/manual_test_results_v1.json`.

## Tracing

OpenTelemetry traces are exported to Azure Application Insights and visible in the AI Foundry portal's **Tracing** tab.

`setup_telemetry()` in `src/core/telemetry.py` is called at startup. It is a no-op if `APPLICATIONINSIGHTS_CONNECTION_STRING` is not set. `flush_telemetry()` is called before process exit to ensure buffered spans are exported.

## Infrastructure

All Azure resources are managed with Terraform in `infra/`:

- AI Foundry account + project
- GPT model deployment (`gpt-53-chat`)
- Evaluator model deployment (`gpt-4o` — required for LLM-judged evaluators)
- Application Insights + Log Analytics
- App Insights connection (enables Tracing in AI Foundry portal)
- Storage account, Key Vault, RBAC role assignments

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # fill in values
terraform init
terraform plan -out=main.tfplan
terraform apply main.tfplan
```

## Environment variables

Required:

```dotenv
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com/
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-53-chat
```

For evaluation (LLM-judged evaluators):

```dotenv
AZURE_EVAL_ENDPOINT=https://your-project.cognitiveservices.azure.com/
AZURE_EVAL_DEPLOYMENT_NAME=gpt-4o
AZURE_EVAL_API_VERSION=2024-06-01
```

Optional:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

Notes:

- `.env` is ignored by git
- Process environment variables override values from `.env`

## Out of scope (V1)

- Real authentication
- Real database / payment processing (tools return stable mock data from `src/tools/mock_data.py`)
- Production-grade UI

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
