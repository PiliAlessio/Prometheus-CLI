# Copilot Instructions for Prometheus CLI

## Repository Overview

**Prometheus CLI** is a Python 3.9+ command-line tool for repository initialization, configuration management, and GitHub integration. The project is organized around:

- **CLI Tool** (`tools/cli/`) - Main Python package for command execution
- **Installation Scripts** - PowerShell (Windows) and Bash (Unix-like) scripts for setup
- **Documentation** - Comprehensive guides in `docs/` directory

This is a polyglot repository containing both shell scripts and Python code.

## Build, Test, and Lint Commands

All commands below should be run from the `tools/cli/` directory. A virtual environment is recommended.

### Setup

```bash
# Navigate to CLI directory
cd tools/cli

# Create virtual environment
python -m venv venv

# Activate (choose one based on OS)
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows CMD
venv\Scripts\Activate.ps1       # Windows PowerShell
```

### Install Dependencies

```bash
# Install the package in development mode with dev dependencies
pip install -e ".[dev]"

# Or manually install all dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src/prometheus

# Run specific test file
pytest tests/test_init.py

# Run specific test function
pytest tests/test_init.py::test_init_interactive

# Run tests with markers (unit, integration, slow, github, cli)
pytest -m unit
pytest -m "not slow"

# Run tests in verbose mode with HTML coverage report
pytest tests/ -v --cov=src/prometheus --cov-report=html
# View report: open htmlcov/index.html
```

### Code Quality

```bash
# Linting (flake8)
flake8 src/ tests/

# Type checking (mypy)
mypy src/

# Code formatting check (black)
black --check src/ tests/

# Auto-format code (black)
black src/ tests/

# Run all checks in order
flake8 src/ && mypy src/ && pytest tests/
```

### Building

```bash
# Build package for distribution
python -m build

# Outputs: dist/prometheus-cli-0.1.0.tar.gz and .whl

# Install from built wheel (for testing)
pip install dist/prometheus-cli-0.1.0-py3-none-any.whl
prometheus version
```

## Architecture

### High-Level Structure

```
tools/cli/
├── src/prometheus/
│   ├── main.py                 # Entry point
│   ├── cli/commands.py         # Click CLI command definitions
│   ├── version.py              # Version info (semantic versioning)
│   ├── context.py              # Global application context
│   ├── init/workflow.py        # Repository initialization workflow
│   ├── language/detection.py   # Language detection logic
│   ├── github/api.py           # GitHub API client wrapper
│   ├── config/config.py        # Configuration file parsing
│   ├── validate/validate.py    # Configuration validation
│   ├── symlink/symlink.py      # Symlink management
│   ├── submodule/detection.py  # Git submodule detection
│   ├── push.py                 # Push changes workflow
│   └── update.py               # Update workflow
├── tests/                      # Pytest test suite
└── pyproject.toml             # Package metadata & build config
```

### Core Workflows

1. **Initialize** (`InitWorkflow`) - Main CLI workflow for setting up repositories
   - Language detection
   - Configuration discovery
   - User interaction (interactive/non-interactive modes)
   - GitHub API integration

2. **Push** - Pushes changes to both app repo and prometheus-core submodule
3. **Update** - Pulls and applies updates from upstream
4. **Validate** - Validates configuration files and repository state

### Dependencies

**Runtime:**
- `click` (8.0+) - CLI framework with commands and options
- `pyyaml` (6.0+) - YAML configuration parsing
- `requests` (2.28+) - HTTP client for GitHub API

**Development:**
- `pytest` (7.0+) - Test framework
- `pytest-cov` (4.0+) - Coverage reporting
- `pytest-mock` (3.12+) - Mocking utilities
- `black` (23.0+) - Code formatter
- `flake8` (5.0+) - Linter
- `mypy` (0.990+) - Type checker

## Key Conventions

### Module Organization

- **Click Commands** live in `src/prometheus/cli/commands.py`
  - Use Click decorators: `@click.command()`, `@click.option()`, `@click.argument()`
  - Wrap RuntimeError exceptions as ClickException for clean error messages
  - Include docstrings with Examples section

- **Workflows** are classes in dedicated modules (e.g., `InitWorkflow` in `init/workflow.py`)
  - Constructor takes `Path` for working directory
  - Main entry method is typically `execute()` or named action method
  - Raise `RuntimeError` with descriptive messages for error handling

- **Utilities** are functions in focused modules (e.g., `language/detection.py`, `github/api.py`)
  - Single responsibility principle per module
  - Type hints for all function signatures (checked by mypy)

### Type Hints

- **All functions require type hints** - Checked during linting with `mypy`
- Use `from __future__ import annotations` at file top for forward references
- Use `Path` from `pathlib` for file system operations (not strings)
- Return types must be explicit: `-> None`, `-> bool`, `-> dict[str, Any]`, etc.

### Testing

- **Test file naming**: `test_*.py` or `*_test.py`
- **Test organization**: One test class per module under test
- **Test markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
- **Fixtures**: Common fixtures in `conftest.py` (e.g., mock GitHub tokens)
- **Mocking**: Use `pytest-mock` for mocking external dependencies (GitHub API, file system)

### Error Handling

- Raise `RuntimeError` with descriptive messages from workflows/utilities
- In Click commands, catch `RuntimeError` and re-raise as `click.ClickException`
- Never suppress exceptions silently - always provide context

### Code Style

- **Line length**: 100 characters (enforced by black)
- **String format**: Use f-strings for all string formatting
- **Imports**: Group standard library, third-party, local in that order
- **Docstrings**: Include when a function/class purpose isn't obvious from context

### Configuration

- YAML files use conventional keys (lowercase, underscores)
- Configuration discovery order: CLI flag > environment variable > local file > home directory > defaults
- Validate all config values early in workflow initialization

## CI/CD

**Workflow**: `.github/workflows/python-build.yml`

- Runs on: `main` and `develop` branches (push and PR)
- Triggers on changes in: `tools/cli/**` or the workflow file itself
- Test matrix: Python 3.9, 3.10, 3.11, 3.12
- Steps: Install deps → Run tests with coverage → Build → Upload coverage

Run the same test/lint sequence locally before pushing:

```bash
cd tools/cli
pip install -e ".[dev]"
pytest tests/ --cov=src/prometheus
flake8 src/
mypy src/
```

## Environment Variables

- **GITHUB_TOKEN** - Required for GitHub API operations (PAT with repo access)
- **PROMETHEUS_CONFIG** - Override default config file location
- **PROMETHEUS_DEBUG** - Enable debug output (set to `1` or `true`)
- **NO_COLOR** - Disable colored output (set to `1` or `true`)

## Common Tasks

### Adding a New Command

1. Add command function in `src/prometheus/cli/commands.py` with Click decorators
2. Include docstring with example usage
3. Handle errors by catching RuntimeError and raising ClickException
4. Add test file(s) in `tests/test_*.py`

### Adding a New Feature Module

1. Create module under `src/prometheus/[feature]/`
2. Add `__init__.py` (can be empty)
3. Implement functions with full type hints
4. Import in parent `__init__.py` if needed for public API
5. Add corresponding test file

### Testing External APIs

- Use `responses` library to mock HTTP requests (already in dev dependencies)
- Fixture in `conftest.py` for common mocks (GitHub tokens, API responses)
- Mark GitHub API tests with `@pytest.mark.github`

### Running a Single Test During Development

```bash
pytest tests/test_init.py::TestInitWorkflow::test_execute -v -s
```

The `-s` flag shows print statements for debugging.

## Documentation

- `README.md` - Quick start and feature overview
- `tools/cli/BUILD_PYTHON.md` - Detailed build, test, release guide
- `tools/cli/README.md` - CLI usage, commands, configuration
- `tools/cli/PYTHON_MIGRATION.md` - Migration notes from Go version
- `docs/` - High-level documentation

## Troubleshooting

### "ModuleNotFoundError: No module named 'prometheus'"

Install in editable mode: `pip install -e .`

### Tests fail with import errors

Ensure you're in `tools/cli/` directory and have activated the virtual environment:
```bash
cd tools/cli
source venv/bin/activate
pip install -e ".[dev]"
```

### Type checking errors

Run `mypy src/` to see all type issues. Fix by adding explicit type hints.

### Flake8 line length warnings

Use black to auto-format: `black src/ tests/`

## Version Management

- Version stored in `src/prometheus/version.py` as `__version__ = "X.Y.Z"`
- Follows semantic versioning (major.minor.patch)
- Update before releases and commit with tag
