---
name: open-devui
description: "Launch the Agent Framework DevUI web interface for the maf-contact-centre project. Use when the user asks to open, start, run, or launch DevUI."
argument-hint: "Optional flags like --port, --no-auto-open, or --mode user"
user-invocable: true
---

# Open DevUI

Use this skill when the user asks to open, start, run, or launch DevUI.

## Prerequisites

- The `.env` file must exist at the project root with valid Azure AI Foundry credentials (`PROJECT_CONNECTION_STRING`).
- Dependencies must be installed (`uv sync`).

## Default command

```bash
uv run python main.py devui
```

This starts the DevUI server on `127.0.0.1:8080` and opens the browser automatically.

## Available flags

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Host interface for the DevUI server |
| `--port` | `8080` | Port for the DevUI server |
| `--no-auto-open` | off | Do not open the browser after DevUI starts |
| `--instrumentation-enabled` | off | Enable DevUI OpenTelemetry instrumentation |
| `--mode` | `developer` | Run DevUI in `developer` or `user` mode |

## Workflow

1. Confirm the `.env` file exists at the project root. If it does not, tell the user to create one from `infra/terraform.tfvars.example` or set `PROJECT_CONNECTION_STRING` manually.

2. Build the command from the user's request:
   - Start with `uv run python main.py devui`.
   - Append any flags the user specified (e.g. `--port 9000`, `--no-auto-open`, `--mode user`).
   - If the user did not specify a port but the default port `8080` is in use, pick the next free port.

3. Run the command in a **background terminal** so the DevUI server stays alive.

4. After launching, briefly confirm:
   - The command that was run.
   - The URL where DevUI is available (e.g. `http://127.0.0.1:8080`).

## Troubleshooting

- **Port already in use**: Re-run with a different `--port` value, or find and stop the process occupying the port with `lsof -i :<port>`.
- **Missing credentials**: Ensure `.env` contains a valid `PROJECT_CONNECTION_STRING`. Run `cat .env | grep PROJECT_CONNECTION_STRING` to verify.
- **Import errors**: Run `uv sync` to install all dependencies.

## Completion criteria

- The DevUI server process is running in a background terminal.
- The user has been told the URL to access it.
