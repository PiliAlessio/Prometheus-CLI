# Prometheus CLI - Installation Guide

This guide covers multiple ways to install the Prometheus Python-based CLI tool. Choose the method that best fits your workflow.

## Quick Start

The fastest way to get started:

```bash
pip install prometheus-cli
```

Then verify installation:
```bash
prometheus version
```

Expected output:
```
Prometheus v0.1.0 (built: 2026-07-19, commit: abc1234)
```

## Installation Methods

### 1. Using PyPI (Recommended)

Install from Python Package Index using pip:

**Linux/macOS/Windows:**
```bash
pip install prometheus-cli
```

**Or with python -m:**
```bash
python -m pip install prometheus-cli
```

**For a specific version:**
```bash
pip install prometheus-cli==0.1.0
```

**Upgrade to latest version:**
```bash
pip install --upgrade prometheus-cli
```

**Verify installation:**
```bash
prometheus version
```

### 2. Build from Source

For developers or those who prefer building locally.

#### Prerequisites
- Python 3.9 or later ([install Python](https://www.python.org/downloads/))
- Git
- pip

#### Installation

**Clone and install:**
```bash
# Clone the repository
git clone https://github.com/AlessioPili-KT/Prometheus.git
cd Prometheus/tools/cli

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify
prometheus version
```

**Or install directly from git:**
```bash
pip install git+https://github.com/AlessioPili-KT/Prometheus.git@main#egg=prometheus-cli&subdirectory=tools/cli
```

**For development (with test dependencies):**
```bash
git clone https://github.com/AlessioPili-KT/Prometheus.git
cd Prometheus/tools/cli

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e ".[dev]"

# Run tests
pytest tests/
```

### 3. Using Docker (Optional)

If you prefer containerized tools:

**Using Docker image:**
```bash
docker run --rm ghcr.io/AlessioPili-KT/prometheus:latest version
```

**Or build from Dockerfile:**
```dockerfile
FROM python:3.11-slim

RUN pip install prometheus-cli

ENTRYPOINT ["prometheus"]
```

Build and run:
```bash
docker build -t prometheus .
docker run --rm prometheus version
```

## Verifying Installation

### Check version:
```bash
prometheus version
```

Output:
```
Prometheus v0.1.0 (built: 2026-07-19, commit: abc1234)
```

### Check help:
```bash
prometheus help
# or
prometheus --help
```

### Test basic functionality:
```bash
prometheus init --help
prometheus version
```

## Platform-Specific Instructions

### macOS

Use pip on any Mac (Intel or Apple Silicon):

```bash
# Install
pip install prometheus-cli

# Verify
prometheus version
```

### Linux (All distributions)

Use pip on any Linux distribution:

```bash
# Install
pip install prometheus-cli

# Verify
prometheus version
```

For ARM64 (Raspberry Pi, etc.):
```bash
pip install prometheus-cli
```

### Windows (All architectures)

```powershell
# Install
pip install prometheus-cli

# Verify
prometheus version
```

Or using Command Prompt:
```cmd
pip install prometheus-cli
prometheus version
```

### Windows WSL2

Use Linux installation in Windows Subsystem for Linux:

```bash
pip install prometheus-cli
prometheus version
```

## Verifying Python Version

Prometheus CLI requires Python 3.9 or later. Check your Python version:

```bash
python --version
# or
python3 --version
```

If you have multiple Python versions, specify Python 3.9+:

```bash
python3.11 -m pip install prometheus-cli
prometheus version
```

## Troubleshooting

### "prometheus: command not found"

The executable is not in your PATH. Try:

**Option 1: Use full path**
```bash
python -m prometheus version
```

**Option 2: Add Python's bin to PATH**

Find where pip installed the command:
```bash
# Linux/macOS
python -m site --user-base

# Add {output}/bin to your PATH
# For example, add to ~/.bashrc or ~/.zshrc:
export PATH="$PATH:$HOME/.local/bin"
```

**Option 3: Install with --user flag**
```bash
pip install --user prometheus-cli
```

### "Permission denied"

This may occur on macOS/Linux with system Python:

```bash
# Solution: Use --user flag
pip install --user prometheus-cli

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install prometheus-cli
```

### "ModuleNotFoundError" or import errors

This means the package is not properly installed. Try:

```bash
# Verify installation
pip show prometheus-cli

# Reinstall
pip install --force-reinstall prometheus-cli

# Or in a virtual environment
python -m venv venv
source venv/bin/activate
pip install prometheus-cli
```

### "No module named pip"

Install pip first:

```bash
# macOS/Linux
python -m ensurepip --upgrade

# Windows
python -m ensurepip --upgrade
```

### "Python 3.9+ required"

You have an older Python version. Install Python 3.9 or later:

- **macOS**: https://www.python.org/downloads/ or `brew install python@3.11`
- **Linux**: `apt-get install python3.11` (Ubuntu/Debian)
- **Windows**: https://www.python.org/downloads/

Verify:
```bash
python3.11 --version
python3.11 -m pip install prometheus-cli
```

### "Version shows 'unknown' commit"

This is normal for released packages. The version information is:
- `v0.1.0` - Semantic version
- `built: 2026-07-19` - Build date
- `commit: abc1234` - Git commit hash

Unbuilt versions will show `dev` or `unknown`. This doesn't affect functionality.

### Installing fails with network error

- Check your internet connection
- Try a different PyPI mirror: `pip install -i https://pypi.org/simple/ prometheus-cli`
- Upgrade pip: `pip install --upgrade pip`
- Check PyPI status: https://status.pypi.org/

### Still having issues?

Open an issue on [GitHub](https://github.com/AlessioPili-KT/Prometheus/issues) with:
1. Output of `prometheus version`
2. Output of `python --version`
3. Output of `pip --version`
4. Your operating system and architecture
5. Steps you followed
6. Full error message

## Next Steps

After installation:

1. **Quick Start**: See [CLI_GUIDE.md](CLI_GUIDE.md) for basic usage
2. **Full Documentation**: Read [tools/cli/README.md](../tools/cli/README.md)
3. **First Use**: Run `prometheus init --help` to see initialization options

## Updating

To update to a new version:

```bash
# Update pip first (recommended)
pip install --upgrade pip

# Upgrade prometheus-cli
pip install --upgrade prometheus-cli

# Verify
prometheus version
```

Check for updates at: https://github.com/AlessioPili-KT/Prometheus/releases

## Uninstalling

```bash
# Uninstall
pip uninstall prometheus-cli

# Verify it's removed
prometheus version
# Should show: command not found
```

## Getting Help

- **Documentation**: https://github.com/AlessioPili-KT/Prometheus/blob/main/docs/
- **Issues**: https://github.com/AlessioPili-KT/Prometheus/issues
- **Releases**: https://github.com/AlessioPili-KT/Prometheus/releases
- **CLI Help**: `prometheus help`
- **PyPI Package**: https://pypi.org/project/prometheus-cli/

## License

Prometheus CLI is licensed under the MIT License. See [LICENSE](https://github.com/AlessioPili-KT/Prometheus/blob/main/LICENSE) for details.

