
# `test/` Directory

This directory contains unit tests and integration tests for the `components/` and `bases/` of the LIF system, following the Polylith architectural pattern. All tests are written in pure Python, using standard testing libraries like `unittest` or `pytest`.

## Purpose

The `test/` directory is designed to:
- Ensure correctness of reusable components (`components/`)
- Validate the orchestration logic in deployable services (`bases/`)
- Enable fast feedback during development and CI/CD
- Promote a clean separation between logic and test code

## Example Structure

The directory layout mirrors the source tree of `components/` and `bases/`:

<pre lang="markdown"> <code> 
test/  
├── components/  
│ └── lif/  
│ ├── query_cache_service/  
│ │ └── test_core.py  
│ └── openapi_to_graphql/  
│ └── test_core.py  
│ ...  
├── bases/  
│ └── lif/  
│ ├── api_graphql/  
│ │ └── test_core.py  
│ └── advisor_restapi/  
│ └── test_core.py
</code> </pre>

Each module typically contains:
- `test_core.py` — tests for the corresponding `core.py`
- `__init__.py` — marks the directory as a Python package (required for pytest-asyncio to work correctly)

## Prerequisites

### Required

- **Python 3.13+** with dependencies installed via `uv sync`

### Optional (for integration tests)

- **PostgreSQL** - Required for MDR integration tests (`test/bases/lif/mdr_restapi/`)
  ```bash
  # macOS
  brew install postgresql
  ```
  If PostgreSQL is not installed, these tests will be skipped automatically.

### Environment Variables

Export `LIF_ADAPTER__LIF_TO_LIF__GRAPHQL_API_URL` before running tests:

```bash
export LIF_ADAPTER__LIF_TO_LIF__GRAPHQL_API_URL="http://localhost:8000"
```

## Running Tests

Run all tests from the repository root:

```bash
uv run pytest
```

Run a specific test file:

```bash
uv run pytest test/components/lif/query_cache_service/test_core.py
```

Run a specific test:

```bash
uv run pytest test/components/lif/query_cache_service/test_core.py::test_function_name -v
```

Run with verbose output:

```bash
uv run pytest -v
```

## Async Tests

Tests use `pytest-asyncio` with `asyncio_mode = auto` (configured in `pyproject.toml`). Async test functions are automatically detected and run - no `@pytest.mark.asyncio` decorator needed.

## Guidelines

-   Mirror the structure of the source directories (`components/` and `bases/`)
-   Keep test cases focused and descriptive
-   Use test doubles (e.g., mocks or fixtures) to isolate logic
-   Group related tests into classes or logical sections
-   Prefer small, fast, and deterministic tests

## Related Directories

-   `components/`: Reusable feature modules tested here
-   `bases/`: Deployment contexts tested here
-   `development/`: May contain mock data or helper scripts used during testing

## Recommended Tools

-   pytest
-   [unittest](https://docs.python.org/3/library/unittest.html)
-   [coverage.py](https://coverage.readthedocs.io/) — for test coverage reporting
