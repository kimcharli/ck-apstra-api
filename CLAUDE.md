# CK-APSTRA-API Development Guidelines

## Build & Test Commands
- Setup: `uv init`
- Install dependencies: `uv sync`
- Run CLI: `uv run ck-cli`
- Run pytest (all tests): `pytest`
- Run single test: `pytest tests/test_file.py::test_function_name -v`
- Run tests with tox: `tox`
- Build package: `uv build`
- Publish package: `python -m twine upload dist/*`

## Style Guidelines
- Python 3.11+ compatible code
- Use type hints consistently (Optional, Result types)
- Import ordering: standard lib → third-party → local modules
- Class names: PascalCase (e.g., CkApstraSession)
- Constants/Enums: UPPER_SNAKE_CASE
- Functions/variables: snake_case
- Use Result types (Ok/Err) for error handling
- Log errors with appropriate severity
- Use docstrings for classes and public methods
- Prefer explicit error handling over exceptions