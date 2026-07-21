# Prometheus CLI - Python Build and Development Guide

## Overview

This document describes how to build, test, and release the Prometheus Python CLI tool.

## Prerequisites

### Required
- **Python 3.9+** - Download from [python.org](https://www.python.org/downloads/)
- **pip** - Python package manager (included with Python)
- **git** - For version information
- **venv** - Python virtual environments (included with Python 3.3+)

### Optional
- **pytest** - For running tests
- **flake8** - For code linting
- **mypy** - For type checking
- **black** - For code formatting

## Development Setup

### Initial Setup

#### 1. Clone the repository
```bash
git clone https://github.com/AlessioPili-KT/Prometheus.git
cd Prometheus/tools/cli
```

#### 2. Create a virtual environment (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate      # On Linux/macOS
# or
venv\Scripts\activate          # On Windows Command Prompt
# or
venv\Scripts\Activate.ps1      # On Windows PowerShell
```

#### 3. Install dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install the package in development mode with dev dependencies
pip install -e ".[dev]"
```

### Development Workflow

#### Run the CLI locally
```bash
# Directly
prometheus version
prometheus init --help

# Or through Python
python -m prometheus version
```

#### Run tests
```bash
pytest tests/

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_init.py

# Verbose output
pytest -v tests/
```

#### Run linting
```bash
# Check code style
flake8 src/

# Type checking
mypy src/

# Auto-format code
black src/ tests/
```

#### Run all checks
```bash
# Use a combined script (if available)
pip install pre-commit
pre-commit install
pre-commit run --all-files

# Or manually
flake8 src/
mypy src/
pytest tests/
```

## Building for Distribution

### Build the package

```bash
# Install build tools
pip install build

# Build source distribution and wheel
python -m build

# Outputs:
# dist/prometheus-cli-0.1.0.tar.gz  (source distribution)
# dist/prometheus-cli-0.1.0-py3-none-any.whl  (wheel)
```

### Verify the build

```bash
# List contents of wheel
unzip -l dist/prometheus-cli-0.1.0-py3-none-any.whl

# Test installation from wheel
pip install dist/prometheus-cli-0.1.0-py3-none-any.whl
prometheus version

# Uninstall
pip uninstall prometheus-cli
```

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_init.py           # Tests for init command
├── test_version.py        # Tests for version command
├── test_config.py         # Tests for configuration
├── conftest.py            # Pytest fixtures
└── fixtures/              # Test data
    ├── sample_config.yml
    └── sample_project/
```

### Running Tests

#### All tests
```bash
pytest tests/
```

#### Specific test file
```bash
pytest tests/test_init.py
```

#### Specific test function
```bash
pytest tests/test_init.py::test_init_interactive
```

#### With coverage report
```bash
pytest --cov=src --cov-report=html tests/

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

#### With verbose output
```bash
pytest -v tests/
```

### Test Dependencies

Tests use:
- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities
- **responses** - HTTP request mocking (for GitHub API tests)

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock responses
```

## Code Quality

### Linting

#### Check code style with flake8
```bash
flake8 src/

# Specific file
flake8 src/prometheus/cli.py

# Show statistics
flake8 --statistics src/
```

#### Configuration (.flake8)
```ini
[flake8]
max-line-length = 100
exclude = venv,build,dist
ignore = E203, W503
```

### Type Checking

#### Check types with mypy
```bash
mypy src/

# Specific file
mypy src/prometheus/cli.py

# Strict mode
mypy --strict src/
```

#### Configuration (mypy.ini)
```ini
[mypy]
python_version = 3.9
disallow_untyped_defs = True
disallow_incomplete_defs = True
```

### Code Formatting

#### Format code with black
```bash
# Format in place
black src/ tests/

# Check without changes
black --check src/ tests/
```

#### Configuration (pyproject.toml)
```toml
[tool.black]
line-length = 100
target-version = ['py39']
```

## Dependency Management

### Dependencies (from setup.py or pyproject.toml)

**Runtime dependencies:**
- Click (7.1+) - CLI framework
- PyYAML (6.0+) - YAML parsing
- requests (2.28+) - HTTP client

**Development dependencies:**
- pytest (7.0+) - Testing
- pytest-cov (3.0+) - Coverage
- pytest-mock (3.0+) - Mocking
- responses (0.20+) - HTTP mocking
- flake8 (4.0+) - Linting
- mypy (0.950+) - Type checking
- black (22.0+) - Formatting

### Update dependencies

```bash
# List outdated packages
pip list --outdated

# Upgrade all packages
pip install --upgrade -r requirements-dev.txt

# Update specific package
pip install --upgrade Click

# Generate requirements file (if needed)
pip freeze > requirements-dev.txt
```

## Versioning

### Version file location

The version is stored in: `src/prometheus/version.py`

```python
__version__ = "0.1.0"
__build_time__ = "2026-07-19"
__git_commit__ = "abc1234"
```

### Update version

1. Edit `src/prometheus/version.py`
2. Update `setup.py` or `pyproject.toml` version field
3. Update `CHANGELOG.md`
4. Tag in git: `git tag -a v0.1.0 -m "Release v0.1.0"`
5. Push: `git push && git push --tags`

## Releasing

### Pre-release Checklist

- [ ] Update version in `src/prometheus/version.py`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Run tests: `pytest tests/`
- [ ] Run linting: `flake8 src/`
- [ ] Run type checking: `mypy src/`
- [ ] Build package: `python -m build`
- [ ] Test installation: `pip install dist/*.whl`
- [ ] Commit changes: `git commit -am "Release v0.X.Y"`
- [ ] Create tag: `git tag -a v0.X.Y -m "Release v0.X.Y"`

### Create Release

#### 1. Publish to PyPI

```bash
# Install tools
pip install twine

# Verify package
twine check dist/*

# Upload to PyPI
twine upload dist/prometheus-cli-0.1.0.*
```

#### 2. Create GitHub Release

```bash
# Using GitHub CLI
gh release create v0.1.0 \
  --title "Release 0.1.0" \
  --notes "See CHANGELOG.md for details" \
  dist/prometheus-cli-0.1.0.*

# Or manually on GitHub website
```

#### 3. Verify Release

```bash
# Install from PyPI
pip install prometheus-cli==0.1.0

# Test
prometheus version
```

### Manual Release Process

If you prefer manual steps:

```bash
# Build
python -m build

# Verify
twine check dist/*

# Upload to PyPI
twine upload dist/prometheus-cli-0.1.0.*

# Tag in git
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Docker Builds (Optional)

### Build Docker image

#### Dockerfile example
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Verify
RUN prometheus version

ENTRYPOINT ["prometheus"]
```

#### Build image
```bash
docker build -t prometheus-cli:0.1.0 .

# Tag for registry
docker tag prometheus-cli:0.1.0 ghcr.io/AlessioPili-KT/prometheus:0.1.0

# Push to registry (requires authentication)
docker push ghcr.io/AlessioPili-KT/prometheus:0.1.0
```

#### Test image
```bash
docker run --rm prometheus-cli:0.1.0 version
docker run --rm prometheus-cli:0.1.0 --help
```

## Troubleshooting

### "Python not found"

Install Python from [python.org](https://www.python.org/downloads/)

Verify:
```bash
python --version
python3 --version
```

### "venv module not found"

On some systems, venv is a separate package:

```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# Fedora
sudo dnf install python3-venv

# macOS (with Homebrew)
brew install python
```

### "pip: command not found"

```bash
# Reinstall pip
python -m ensurepip --upgrade

# Or upgrade pip
python -m pip install --upgrade pip
```

### Tests fail with "module not found"

```bash
# Install package in editable mode
pip install -e .

# Or install all dev dependencies
pip install -e ".[dev]"
```

### Type checking errors in strict mode

```bash
# Run mypy without strict mode
mypy src/

# Or fix type hints in the code
```

### Flake8 complains about line length

```bash
# Configure in .flake8 or pyproject.toml
# max-line-length = 100
```

## Performance

Build times (approximate):
- **Local install**: 5-10 seconds
- **Tests**: 5-15 seconds
- **Linting**: 2-5 seconds
- **Type checking**: 3-8 seconds
- **Full build**: 10-30 seconds

## Next Steps

- Read [INSTALLATION.md](../../docs/INSTALLATION.md) for installation instructions
- Check [README.md](README.md) for usage guide
- Review [PYTHON_MIGRATION.md](PYTHON_MIGRATION.md) for migration from Go
- Check [tools/cli/src/](src/) for source code structure

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Click Documentation](https://click.palletsprojects.com/)
- [PyYAML Documentation](https://pyyaml.org/)
- [Semantic Versioning](https://semver.org/)
