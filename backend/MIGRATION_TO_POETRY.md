# Migration Guide: pip → Poetry

This guide helps you migrate from the old `pip + requirements.txt` setup to the new `Poetry + pyproject.toml` setup.

## Why Migrate?

✅ **Better Dependency Resolution**: Automatic conflict detection  
✅ **Lock File**: Reproducible builds across all environments  
✅ **Dependency Groups**: Separate dev/test/prod dependencies  
✅ **Modern Standard**: TOML-based configuration (PEP 621)  
✅ **Integrated Virtual Environments**: No manual venv management  

---

## Quick Migration (5 minutes)

### 1. Install Poetry

**Windows (PowerShell)**:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**macOS/Linux/WSL**:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify installation:
```bash
poetry --version
```

### 2. Remove Old Virtual Environment

```bash
cd backend

# Deactivate if active
deactivate  # or: conda deactivate

# Remove old venv
rm -rf venv/  # or: rmdir /s venv (Windows)
```

### 3. Install Dependencies with Poetry

```bash
# Install all dependencies from pyproject.toml
poetry install

# This will:
# - Create a new virtual environment
# - Install all production dependencies
# - Install all dev dependencies (black, ruff, mypy)
# - Install all test dependencies (pytest, pytest-cov)
# - Generate poetry.lock file
```

### 4. Update Your Workflow

**Before (pip)**:
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m uvicorn src.api.main:app --reload
pytest
```

**After (Poetry)**:
```bash
# Option 1: Use poetry shell
poetry shell
uvicorn src.api.main:app --reload
pytest

# Option 2: Use poetry run (no activation needed)
poetry run uvicorn src.api.main:app --reload
poetry run pytest
```

### 5. Commit Changes

```bash
git add pyproject.toml poetry.lock
git commit -m "Migrate to Poetry for dependency management"
```

---

## Detailed Changes

### What Changed?

| Aspect | Before (pip) | After (Poetry) |
|--------|-------------|----------------|
| **Dependencies** | `requirements.txt` | `pyproject.toml` + `poetry.lock` |
| **Install** | `pip install -r requirements.txt` | `poetry install` |
| **Add Package** | Manual edit + `pip install` | `poetry add <package>` |
| **Virtual Env** | `python -m venv venv` | Automatic with `poetry install` |
| **Activate** | `source venv/bin/activate` | `poetry shell` or `poetry run` |
| **Dev Deps** | Mixed with prod deps | Separate `[tool.poetry.group.dev]` |

### File Changes

**New Files**:
- ✅ `backend/pyproject.toml` - Now includes all dependencies
- ✅ `backend/poetry.lock` - Lock file (commit this!)
- ✅ `backend/POETRY_GUIDE.md` - Complete Poetry documentation
- ✅ `backend/MIGRATION_TO_POETRY.md` - This file

**Modified Files**:
- 📝 `backend/requirements.txt` - Kept for compatibility (with deprecation note)
- 📝 `README.md` - Updated setup instructions
- 📝 `docs/deployment_guide.md` - Updated CI/CD workflows
- 📝 `docs/plan.md` - Updated dependency management section
- 📝 `.gitignore` - Added Poetry cache directories

---

## Common Migration Scenarios

### Scenario 1: Local Development

```bash
cd backend

# Old way
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.api.main:app --reload

# New way
poetry install
poetry run uvicorn src.api.main:app --reload
```

### Scenario 2: Running Tests

```bash
# Old way
source venv/bin/activate
pytest
pytest --cov=src

# New way
poetry run pytest
poetry run pytest --cov=src
```

### Scenario 3: Adding a New Package

```bash
# Old way
pip install langchain-anthropic
pip freeze > requirements.txt  # Manual!

# New way
poetry add langchain-anthropic  # Automatic!
# poetry.lock and pyproject.toml are automatically updated
```

### Scenario 4: CI/CD Pipeline

**Before (GitHub Actions)**:
```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install pytest
```

**After (GitHub Actions)**:
```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Install Poetry
  run: |
    curl -sSL https://install.python-poetry.org | python3 -
    echo "$HOME/.local/bin" >> $GITHUB_PATH

- name: Install dependencies
  run: |
    poetry install
```

### Scenario 5: Modal Deployment

**Before**:
```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
)
```

**After**:
```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .poetry_install_from_file("pyproject.toml")
)
```

---

## FAQ

### Q: Do I need to delete requirements.txt?

**A**: No! We're keeping it for backward compatibility. However, it now has a deprecation notice. If you want to keep it in sync:

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Q: Where is my virtual environment?

**A**: Poetry creates it automatically. Find it with:

```bash
poetry env info

# Or list all Poetry envs
poetry env list

# Path is usually: ~/.cache/pypoetry/virtualenvs/
# Or in-project: backend/.venv/ (if configured)
```

To use in-project virtual environments:
```bash
poetry config virtualenvs.in-project true
poetry install
# Creates: backend/.venv/
```

### Q: How do I activate the virtual environment?

**A**: Two options:

```bash
# Option 1: Spawn a new shell
poetry shell
# Now run commands normally: pytest, uvicorn, etc.
exit  # to exit poetry shell

# Option 2: Run commands with poetry run (no activation)
poetry run pytest
poetry run uvicorn src.api.main:app --reload
```

### Q: Can I still use pip?

**A**: Yes, but not recommended. If you must:

```bash
poetry shell  # Activate the Poetry env
pip install <package>  # Works but won't update poetry.lock!
```

Better approach:
```bash
poetry add <package>  # Properly tracked
```

### Q: How do I update packages?

```bash
# Check for outdated packages
poetry show --outdated

# Update specific package
poetry update openai

# Update all packages
poetry update

# Update and regenerate lock file
poetry lock
```

### Q: What about Modal deployment?

Modal supports Poetry natively:

```python
# backend/modal_app.py (already updated)
image = modal.Image.debian_slim(python_version="3.11").poetry_install_from_file("pyproject.toml")
```

### Q: My IDE doesn't recognize the environment

**Configure your IDE to use Poetry's virtual environment**:

1. Get the environment path:
   ```bash
   poetry env info --path
   ```

2. **VSCode**: 
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose the path from step 1

3. **PyCharm**:
   - Settings → Project → Python Interpreter
   - Add → Existing Environment → Select Poetry env

### Q: How do I revert to pip if needed?

```bash
# Export current dependencies
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create traditional venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Troubleshooting

### Error: "poetry: command not found"

**Solution**: Add Poetry to PATH:

```bash
# Windows PowerShell
$env:Path += ";$env:APPDATA\Python\Scripts"

# macOS/Linux
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Error: "The Poetry configuration is invalid"

**Solution**: Validate and fix:

```bash
cd backend
poetry check
poetry lock --no-update
```

### Error: "SolverProblemError: dependency conflicts"

**Solution**: Update lock file with latest compatible versions:

```bash
poetry update
# or
poetry lock --no-update
```

If still failing, check conflicting packages:
```bash
poetry show --tree
```

### Virtual environment in wrong location

**Solution**: Configure in-project:

```bash
poetry config virtualenvs.in-project true
poetry env remove python3.11  # Remove old env
poetry install  # Creates new env in backend/.venv/
```

---

## Next Steps

1. ✅ Install Poetry
2. ✅ Run `poetry install`
3. ✅ Update your editor/IDE interpreter
4. ✅ Use `poetry run` or `poetry shell` for commands
5. ✅ Read `POETRY_GUIDE.md` for advanced usage
6. ✅ Update any local scripts or aliases
7. ✅ Inform your team about the migration

---

## Resources

- 📖 [POETRY_GUIDE.md](./POETRY_GUIDE.md) - Complete Poetry documentation
- 🌐 [Poetry Official Docs](https://python-poetry.org/docs/)
- 🔧 [Poetry CLI Reference](https://python-poetry.org/docs/cli/)
- 📋 [pyproject.toml Spec (PEP 621)](https://peps.python.org/pep-0621/)

---

## Getting Help

If you encounter issues:

1. Check `POETRY_GUIDE.md` troubleshooting section
2. Run `poetry check` to validate configuration
3. Run `poetry env info` to debug environment issues
4. Check Poetry docs: https://python-poetry.org/docs/
5. Ask the team in Slack/Discord

**Welcome to modern Python dependency management! 🚀**
