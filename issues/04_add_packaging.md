# Issue: Add project packaging (requirements.txt and/or pyproject.toml)

## Objective
Add standard Python packaging metadata so the project can be installed and dependencies tracked.

## Requirements

1. **`requirements.txt`**
   - List runtime dependencies with minimum viable versions:
     ```
     pydantic>=2.0
     litellm>=1.0
     typer>=0.12
     pandas>=2.0
     pyyaml>=6.0
     ```

2. **`pyproject.toml`** (recommended over setup.py)
   - `[build-system]` using `setuptools`
   - `[project]` section:
     - name: `minpriv`
     - version: `0.1.0`
     - description: brief summary
     - requires-python: `>=3.11`
     - dependencies: same list as `requirements.txt`
   - `[project.optional-dependencies]`:
     - `dev`: `pytest>=8.0`, `mypy`, `ruff`
   - `[tool.setuptools.packages.find]` to include `minpriv/`

## Acceptance Criteria
- `pip install -e .` installs the package successfully
- `python -c "import minpriv"` works after installation
- Optional dev dependencies install with `pip install -e ".[dev]"`

## Files to Create
- `requirements.txt`
- `pyproject.toml`
