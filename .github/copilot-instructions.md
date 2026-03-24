# Copilot Instructions

## Language & Runtime

- We use **Python** as the primary programming language.

## Package Management

- We use **uv** to manage packages and virtual environments.
- Use `uv add` to add dependencies and `uv run` to execute scripts.
- Always run Python from the `.venv` virtual environment.

## Development Practices

- Follow **Test-Driven Development (TDD)**:
  1. Write a failing test first.
  2. Write the minimal code to make the test pass.
  3. Refactor while keeping tests green.
- Use `pytest` as the test framework.
- Run tests with `uv run pytest`.

## Monkey-patches

- `src/core/patches.py` patches `agent_framework_devui._executor` at runtime to fix [microsoft/agent-framework#3983](https://github.com/microsoft/agent-framework/issues/3983).
- The patch is applied in `src/devui.py` at startup via `apply_devui_executor_patch()`.
- Remove the patch once `agent-framework-devui` is upgraded past `1.0.0b260212`.

## Prompt-level workarounds

- Every agent prompt (`src/prompts/*.md`) has a **Transfer rules** section that forbids the model from calling a tool and transferring in the same response.
- This works around [microsoft/agent-framework#4053](https://github.com/microsoft/agent-framework/issues/4053) where HandoffBuilder doesn't flush pending tool calls before switching agents, causing a `"No tool output found for function call"` 400 error.
- Remove the section once `agent-framework` fixes #4053.
