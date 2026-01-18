# Poetry Guide - Python Dependency Management

This project uses **Poetry** for modern Python dependency management with TOML-based configuration.

## Why Poetry?

- **Modern Dependency Management**: Better than pip + requirements.txt
- **Dependency Resolution**: Automatically resolves conflicts
- **Lock File**: `poetry.lock` ensures reproducible builds
- **Virtual Environment Management**: Integrated venv handling
- **Dev Dependencies**: Separate production and development dependencies
- **Build System**: Standardized Python package building

---

## Installation

### 1. Install Poetry

**Windows (PowerShell)**:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**macOS/Linux**:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Alternative (via pip)**:
```bash
pip install poetry
```

### 2. Verify Installation
```bash
poetry --version
# Should output: Poetry (version 1.7.0)
```

### 3. Configure Poetry (Recommended)
```bash
# Create virtual environments inside the project directory
poetry config virtualenvs.in-project true

# Use Python 3.11+
poetry env use python3.11
```

---

## Quick Start

### Initial Setup

```bash
cd backend

# Install all dependencies (production + dev + test)
poetry install

# Install only production dependencies
poetry install --only main

# Install without dev dependencies
poetry install --no-dev
```

This will:
- Create a virtual environment
- Install all dependencies
- Generate a `poetry.lock` file (commit this!)

### Activate Virtual Environment

```bash
# Option 1: Spawn a shell within the virtual environment
poetry shell

# Option 2: Run commands with poetry run
poetry run python -m uvicorn src.api.main:app --reload
poetry run pytest
```

---

## Common Commands

### Dependency Management

```bash
# Add a new dependency
poetry add fastapi

# Add a development dependency
poetry add --group dev black

# Add a test dependency
poetry add --group test pytest

# Add with version constraint
poetry add "fastapi>=0.104.0,<0.105.0"

# Remove a dependency
poetry remove pandas

# Update all dependencies
poetry update

# Update specific package
poetry update fastapi

# Show installed packages
poetry show

# Show outdated packages
poetry show --outdated

# Show dependency tree
poetry show --tree
```

### Virtual Environment

```bash
# Show virtual environment info
poetry env info

# List all virtual environments
poetry env list

# Remove virtual environment
poetry env remove python3.11

# Activate shell in virtual environment
poetry shell

# Exit poetry shell
exit
```

### Lock File

```bash
# Update lock file without installing
poetry lock --no-update

# Install from lock file (CI/CD)
poetry install --no-root

# Export to requirements.txt (for compatibility)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Running Scripts

```bash
# Run Python scripts
poetry run python scripts/seed_data.py
poetry run python scripts/run_evals.py

# Run uvicorn server
poetry run uvicorn src.api.main:app --reload

# Run tests
poetry run pytest
poetry run pytest --cov=src --cov-report=html

# Run linting
poetry run ruff check src/
poetry run black src/
poetry run mypy src/
```

---

## Project Structure

```
backend/
├── pyproject.toml          # Poetry configuration & dependencies
├── poetry.lock             # Lock file (COMMIT THIS!)
├── .venv/                  # Virtual environment (if using in-project)
├── src/                    # Source code
└── tests/                  # Test code
```

---

## Development Workflow

### 1. Setting Up a New Developer

```bash
cd backend
poetry install          # Installs everything from poetry.lock
poetry shell           # Activate environment
```

### 2. Adding a New Dependency

```bash
# Add the package
poetry add langchain-anthropic

# The pyproject.toml and poetry.lock are automatically updated
# Commit both files
git add pyproject.toml poetry.lock
git commit -m "Add langchain-anthropic dependency"
```

### 3. Updating Dependencies

```bash
# Check for outdated packages
poetry show --outdated

# Update a specific package
poetry update openai

# Update all packages
poetry update

# Commit the updated lock file
git add poetry.lock
git commit -m "Update dependencies"
```

### 4. CI/CD Integration

```bash
# Install dependencies (fast, uses lock file)
poetry install --no-root --no-dev

# Or export to requirements.txt for Docker
poetry export -f requirements.txt --output requirements.txt --without-hashes
pip install -r requirements.txt
```

---

## Dependency Groups

This project organizes dependencies into groups:

### Main Dependencies (Production)
```bash
poetry add <package>           # Adds to main dependencies
poetry install --only main     # Install only production deps
```

### Development Dependencies
```bash
poetry add --group dev <package>    # Linters, formatters
poetry install --with dev           # Include dev deps
```

### Test Dependencies
```bash
poetry add --group test <package>   # Testing tools
poetry install --with test          # Include test deps
```

---

## Integration with Modal

When deploying to Modal, you have two options:

### Option 1: Use pyproject.toml directly
```python
# modal_app.py
import modal

image = modal.Image.debian_slim(python_version="3.11").poetry_install_from_file(
    "pyproject.toml"
)
```

### Option 2: Export to requirements.txt
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev,test
```

Then in Modal:
```python
image = modal.Image.debian_slim(python_version="3.11").pip_install_from_requirements(
    "requirements.txt"
)
```

---

## Troubleshooting

### Poetry not found after installation
Add Poetry to PATH:
```bash
# Windows
$env:Path += ";$env:APPDATA\Python\Scripts"

# macOS/Linux
export PATH="$HOME/.local/bin:$PATH"
```

### Lock file conflicts
```bash
# Regenerate lock file
poetry lock --no-update
```

### Virtual environment issues
```bash
# Remove and recreate
poetry env remove python3.11
poetry install
```

### Dependency conflicts
```bash
# Show why a package is required
poetry show --tree | grep <package-name>

# Update lock file with latest compatible versions
poetry update
```

### Convert existing requirements.txt
```bash
# If you have an old requirements.txt, manually add to pyproject.toml
# Then:
poetry lock
poetry install
```

---

## Best Practices

1. **Always commit `poetry.lock`**: Ensures reproducible builds
2. **Use version constraints**: `^` for compatible versions, `~` for minor updates
3. **Separate dependency groups**: Keep dev/test separate from production
4. **Update regularly**: Check for security updates with `poetry update`
5. **Use `poetry shell`**: Better than manual venv activation
6. **Export for Docker**: Use `poetry export` for containerization

---

## Cheat Sheet

```bash
# Install
poetry install                  # Install all dependencies
poetry install --no-dev        # Production only

# Add/Remove
poetry add <package>           # Add dependency
poetry remove <package>        # Remove dependency

# Run
poetry shell                   # Activate venv
poetry run <command>           # Run command in venv

# Update
poetry update                  # Update all
poetry update <package>        # Update specific

# Info
poetry show                    # List packages
poetry show --tree             # Dependency tree
poetry env info                # Environment info

# Export
poetry export -f requirements.txt --output requirements.txt
```

---

## Migration from pip

If migrating from `requirements.txt`:

1. **Install Poetry** (see above)
2. **Review `pyproject.toml`** (already configured)
3. **Generate lock file**:
   ```bash
   poetry lock
   ```
4. **Install dependencies**:
   ```bash
   poetry install
   ```
5. **Update scripts** to use `poetry run`
6. **(Optional) Keep requirements.txt** for backward compatibility:
   ```bash
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

---

## Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Commands](https://python-poetry.org/docs/cli/)
- [Dependency Specification](https://python-poetry.org/docs/dependency-specification/)
- [pyproject.toml Spec](https://peps.python.org/pep-0621/)
