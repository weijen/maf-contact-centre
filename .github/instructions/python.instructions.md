---
applyTo: "**/*.py"
---

# Python Coding Instructions

## Formatting & Style

- Use Ruff as the formatter and linter. Run `task lint` and `task format` before committing.
- Maximum line length is **120 characters** (configured in `pyproject.toml`).
- Use 4 spaces for indentation. Never use tabs.
- Use `snake_case` for functions, methods, variables, and module names.
- Use `PascalCase` for class names.
- Use `UPPER_SNAKE_CASE` for constants.
- Prefer double quotes (`"`) for strings.

## Imports

- Place all imports at the top of the file. Avoid inline imports inside functions, methods, or test cases.
- Do not create barrel/re-export modules that exist only to re-export symbols from other modules. Import directly from the owning module instead.
- Order imports in three groups separated by a blank line: standard library, third-party packages, local/project modules. Ruff's `isort` rules (`extend-select = ["I"]`) enforce this automatically.
- Use absolute imports for project modules (e.g., `from ai_contact_centre_solution_accelerator.config import ...`).

## Type Hints

- Add type hints to all function signatures (parameters and return types).
- Use built-in generic types (`list`, `dict`, `tuple`, `set`) instead of `typing.List`, `typing.Dict`, etc. (Python 3.12+).
- Use `X | None` instead of `Optional[X]`.
- Use `X | Y` instead of `Union[X, Y]`.

## Functions & Methods

- Keep functions short and focused — each function should do one thing.
- Use `async def` for I/O-bound operations; avoid blocking calls inside async functions.
- Prefer keyword arguments for functions with more than two parameters.
- Use `*args` and `**kwargs` sparingly; prefer explicit parameters.

## Classes & Data Models

- Use `dataclasses` or Pydantic `BaseModel` for data structures instead of plain dicts.
- Prefer composition over inheritance.
- Keep `__init__` methods simple — avoid heavy logic or I/O in constructors.

## Error Handling

- Catch specific exceptions, never bare `except:` or `except Exception:` without re-raising.
- Let unexpected exceptions propagate — don't swallow errors silently.
- Use `raise ... from err` to preserve exception chains.

## Naming Conventions

- Boolean variables and functions should read as questions: `is_valid`, `has_permission`, `can_retry`.
- Private attributes and methods start with a single underscore: `_internal_method`.
- Avoid abbreviations; prefer clarity: `customer_name` over `cust_nm`.

## Testing

- Use `pytest` with `pytest-asyncio` (auto mode is configured).
- Name test files `test_<module>.py` and test functions `test_<behaviour>`.
- Follow Arrange-Act-Assert (AAA) structure in tests.
- Use `unittest.mock.patch` or `MagicMock`/`AsyncMock` for mocking; prefer patching at the call site.
- Write tests first (TDD) — verify they fail before writing implementation.

## Docstrings & Comments

- Don't add docstrings or comments to code you didn't write or modify.
- When needed, use Google-style docstrings.
- Prefer self-documenting code over comments. Add comments only when *why* isn't obvious from the code.

## Async & Concurrency

- Use `asyncio` for concurrent I/O. Do not use threads for I/O-bound work.
- Never call `asyncio.run()` inside an already-running event loop.
- Use `async with` for async context managers (HTTP clients, DB connections, etc.).

## Dependencies

- Target Python **3.12+** — use modern syntax and stdlib features.
- Use `uv` for dependency management. Add dependencies to `pyproject.toml`, not `requirements.txt`.
