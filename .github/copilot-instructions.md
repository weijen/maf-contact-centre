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
