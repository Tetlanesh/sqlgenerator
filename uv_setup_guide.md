# UV Environment Setup — Quick Reference

## Prerequisites

- **uv** installed: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Default install location: `%USERPROFILE%\.local\bin\uv.exe`
- If `uv` isn't on PATH in a new terminal: `$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"` (`set PATH=%USERPROFILE%\.local\bin;%PATH%` for cmd terminal)

## Project Setup (from scratch)

### 1. Create `pyproject.toml`

```toml
[project]
name = "your-project"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"

dependencies = [
    "pandas",
    "some-package",
]
```

### 2. Create the venv + install dependencies

```bash
uv sync
```

This does everything in one command:
- Finds or downloads the required Python version
- Creates `.venv/` in the project directory
- Installs all dependencies
- Generates `uv.lock` lockfile

### 3. Verify installation

```bash
uv run python -c "import pandas; print('OK')"
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `uv sync` | Create/update venv from `pyproject.toml` |
| `uv add <package>` | Add a dependency (updates `pyproject.toml` + installs) |
| `uv remove <package>` | Remove a dependency |
| `uv run <command>` | Run a command using the project's venv |
| `uv run python script.py` | Run a Python script in the venv |
| `uv lock` | Regenerate lockfile without installing |
| `uv pip list` | List installed packages in the venv |
| `uv python list` | List available Python versions |
| `uv python install 3.12` | Install a specific Python version |

## VS Code Integration

- Select interpreter: `.venv\Scripts\python.exe` in the workspace root
- VS Code usually auto-detects the `.venv` folder

## Notes

- `uv sync` is idempotent — safe to re-run anytime
- `.venv/` should be in `.gitignore`; `uv.lock` should be committed
- `uv run` auto-activates the venv — no need to manually activate
- If hardlink warnings appear, set `UV_LINK_MODE=copy` or pass `--link-mode=copy`
