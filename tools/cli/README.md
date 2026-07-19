# Prometheus CLI

A powerful command-line interface for repository initialization, management, and configuration discovery.

**Version**: 0.1.0  
**Repository**: [PiliAlessio/Prometheus](https://github.com/PiliAlessio/Prometheus)  
**License**: MIT  
**Language**: Python 3.9+

## Quick Start

### Installation

```bash
pip install prometheus-cli
```

**Or build from source:**
```bash
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus/tools/cli
pip install -e .
```

**Using Docker:**
```bash
docker run --rm ghcr.io/piliAlessio/prometheus:latest version
```

See [Installation Guide](../../docs/INSTALLATION.md) for detailed instructions.

### Verify Installation

```bash
prometheus version
```

Expected output:
```
Prometheus v0.1.0 (built: 2026-07-19, commit: abc1234)
```

## Requirements

- **Python**: 3.9 or later
- **pip**: Latest recommended
- **Dependencies**:
  - Click (7.1+) - Command-line interface framework
  - PyYAML (6.0+) - YAML configuration parsing
  - requests (2.28+) - HTTP client library

## Features

- **Repository Initialization** - Initialize new repositories with Prometheus configuration
- **Multi-Language Support** - Detect and configure projects in Go, Python, TypeScript, Java, and more
- **Configuration Discovery** - Automatically discover and validate project configurations
- **GitHub Integration** - Integrate with GitHub for repository management
- **Flexible Output** - Structured output for scripting and automation
- **Cross-Platform** - Works on Linux, macOS, and Windows

## Basic Usage

### Initialize a Repository

```bash
prometheus init
```

This will guide you through setting up Prometheus for your project.

**With GitHub token:**
```bash
GITHUB_TOKEN=your_token prometheus init
```

**In non-interactive mode:**
```bash
prometheus init --non-interactive
prometheus init -y
```

### Get Help

```bash
# Global help
prometheus help
prometheus --help
prometheus -h

# Help for specific command
prometheus init --help
prometheus version --help
```

### Check Version

```bash
prometheus version
```

Shows:
- Semantic version (e.g., 0.1.0)
- Build timestamp
- Git commit hash

## Commands Reference

### Available Commands

```
prometheus [command] [flags]
```

#### init

Initialize Prometheus configuration in a repository.

```bash
prometheus init [flags]
```

**Flags:**
- `-y, --yes` - Non-interactive mode (assume yes to all prompts)
- `--language <lang>` - Specify project language
- `--config <path>` - Path to configuration file
- `--template <name>` - Use a configuration template

**Examples:**
```bash
# Interactive initialization
prometheus init

# Non-interactive mode
prometheus init -y

# Specify language
prometheus init --language python

# Use custom config
prometheus init --config ./custom-config.yml
```

#### help

Display help information.

```bash
prometheus help [command]
```

**Examples:**
```bash
# Show global help
prometheus help

# Show help for specific command
prometheus help init
prometheus help version
```

#### version

Show version information.

```bash
prometheus version
```

**Output format:**
```
Prometheus v0.1.0 (built: 2026-07-19, commit: abc1234)
```

## Flags Reference

### Global Flags

These flags work with any command:

- `-h, --help` - Show help information
- `-v, --verbose` - Enable verbose output (for debugging)
- `--debug` - Enable debug mode
- `--config <file>` - Use specific configuration file
- `--no-color` - Disable colored output

### Command-Specific Flags

See command help for details:
```bash
prometheus [command] --help
```

## Environment Variables

### Required

- **GITHUB_TOKEN** - GitHub API token for repository operations
  ```bash
  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  prometheus init
  ```

### Optional

- **PROMETHEUS_CONFIG** - Path to configuration file (overrides `--config`)
- **PROMETHEUS_DEBUG** - Enable debug output (set to `1` or `true`)
- **NO_COLOR** - Disable colored output (set to `1` or `true`)

### Setting Environment Variables

**Linux/macOS:**
```bash
export GITHUB_TOKEN="your-token"
prometheus init
```

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN = "your-token"
prometheus init
```

**Windows (Command Prompt):**
```cmd
set GITHUB_TOKEN=your-token
prometheus init
```

## Configuration

Prometheus uses configuration files to customize behavior.

### Configuration File Location

Prometheus looks for configuration in this order:
1. `--config` flag value
2. `PROMETHEUS_CONFIG` environment variable
3. `.prometheus.yml` (current directory)
4. `~/.prometheus/config.yml` (home directory)
5. Built-in defaults

### Configuration Format

YAML format with sections:

```yaml
# Language detection
language:
  primary: python
  fallback: javascript

# GitHub settings
github:
  api_endpoint: https://api.github.com
  verify_ssl: true

# Initialization options
init:
  template: default
  interactive: true

# Output settings
output:
  format: text
  color: true
```

## Basic Usage

### Initialize a Repository

```bash
prometheus init
```

This will guide you through setting up Prometheus for your project.

**With GitHub token:**
```bash
GITHUB_TOKEN=your_token prometheus init
```

**In non-interactive mode:**
```bash
prometheus init --non-interactive
prometheus init -y
```

### Get Help

```bash
# Global help
prometheus help
prometheus --help
prometheus -h

# Help for specific command
prometheus init --help
prometheus version --help
```

### Check Version

```bash
prometheus version
```

Shows:
- Semantic version (e.g., 0.1.0)
- Build timestamp
- Git commit hash

## Commands Reference

### Available Commands

```
prometheus [command] [flags]
```

#### init

Initialize Prometheus configuration in a repository.

```bash
prometheus init [flags]
```

**Flags:**
- `-y, --yes` - Non-interactive mode (assume yes to all prompts)
- `--language <lang>` - Specify project language
- `--config <path>` - Path to configuration file
- `--template <name>` - Use a configuration template

**Examples:**
```bash
# Interactive initialization
prometheus init

# Non-interactive mode
prometheus init -y

# Specify language
prometheus init --language python

# Use custom config
prometheus init --config ./custom-config.yml
```

#### help

Display help information.

```bash
prometheus help [command]
```

**Examples:**
```bash
# Show global help
prometheus help

# Show help for specific command
prometheus help init
prometheus help version
```

#### version

Show version information.

```bash
prometheus version
```

**Output format:**
```
Prometheus v0.1.0 (built: 2026-07-19, commit: abc1234)
```

## Flags Reference

### Global Flags

These flags work with any command:

- `-h, --help` - Show help information
- `-v, --verbose` - Enable verbose output (for debugging)
- `--debug` - Enable debug mode
- `--config <file>` - Use specific configuration file
- `--no-color` - Disable colored output

### Command-Specific Flags

See command help for details:
```bash
prometheus [command] --help
```

## Environment Variables

### Required

- **GITHUB_TOKEN** - GitHub API token for repository operations
  ```bash
  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  prometheus init
  ```

### Optional

- **PROMETHEUS_CONFIG** - Path to configuration file (overrides `--config`)
- **PROMETHEUS_DEBUG** - Enable debug output (set to `1` or `true`)
- **NO_COLOR** - Disable colored output (set to `1` or `true`)

### Setting Environment Variables

**Linux/macOS:**
```bash
export GITHUB_TOKEN="your-token"
prometheus init
```

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN = "your-token"
prometheus init
```

**Windows (Command Prompt):**
```cmd
set GITHUB_TOKEN=your-token
prometheus init
```

## Configuration

Prometheus uses configuration files to customize behavior.

### Configuration File Location

Prometheus looks for configuration in this order:
1. `--config` flag value
2. `PROMETHEUS_CONFIG` environment variable
3. `.prometheus.yml` (current directory)
4. `~/.prometheus/config.yml` (home directory)
5. Built-in defaults

### Configuration Format

YAML format with sections:

```yaml
# Language detection
language:
  primary: python
  fallback: javascript

# GitHub settings
github:
  api_endpoint: https://api.github.com
  verify_ssl: true

# Initialization options
init:
  template: default
  interactive: true

# Output settings
output:
  format: text
  color: true
```

## Examples

### Initialize Python Project

```bash
prometheus init --language python
```

### Initialize Go Project with Non-Interactive Mode

```bash
prometheus init --language go -y
```

### Use Custom Configuration

```bash
prometheus init --config ./my-config.yml
```

### Check Version Information

```bash
prometheus version
```

### Get Help for Init Command

```bash
prometheus init --help
```

## Troubleshooting

### Command not found

```
bash: prometheus: command not found
```

**Solution**: The CLI is not installed or not in PATH.
1. Check installation: `pip show prometheus-cli`
2. Install: `pip install prometheus-cli`
3. See [Installation Guide](../../docs/INSTALLATION.md)

### Permission denied

This shouldn't occur with pip-based installation, but if it does:

```bash
pip install --force-reinstall prometheus-cli
```

### GitHub API errors

```
Error: Failed to authenticate with GitHub
```

**Solution**: Set GITHUB_TOKEN environment variable.
```bash
export GITHUB_TOKEN="your-github-token"
```

### Module import errors

```
ModuleNotFoundError: No module named 'prometheus'
```

**Solution**: Reinstall the package.
```bash
pip install --force-reinstall prometheus-cli
```

Or in a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install prometheus-cli
```

## Development Setup

For developers contributing to Prometheus CLI:

### Prerequisites
- Python 3.9+
- git

### Setup

```bash
# Clone the repository
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus/tools/cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
flake8 src/

# Run type checking
mypy src/
```

## Performance

- **Install size**: ~10 MB (with dependencies)
- **Startup time**: <500ms
- **Typical init command**: 1-5 seconds

## Platform Support

### Supported Operating Systems

- ✅ Linux (all distributions, all architectures)
- ✅ macOS (Intel and Apple Silicon)
- ✅ Windows (64-bit and 32-bit)

### Supported Architectures

- ✅ x86_64 (amd64)
- ✅ ARM64 (Apple Silicon, Raspberry Pi, etc.)
- ✅ All other Python-supported platforms

## Updating

Check for updates:
```bash
# Check PyPI for latest version
pip index versions prometheus-cli

# Or visit
https://github.com/PiliAlessio/Prometheus/releases
```

To update:
```bash
pip install --upgrade prometheus-cli
prometheus version
```

## Contributing

We welcome contributions! 

### Reporting Issues
- Check existing [issues](https://github.com/PiliAlessio/Prometheus/issues)
- Provide version info: `prometheus version`
- Include reproduction steps

### Contributing Code
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run: `pytest tests/` and `flake8 src/`
6. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

## License

Prometheus CLI is licensed under the MIT License. See [LICENSE](../../LICENSE) for details.

## Related Documentation

- **[Installation Guide](../../docs/INSTALLATION.md)** - Detailed installation instructions
- **[CLI Guide](../../docs/CLI_GUIDE.md)** - Comprehensive usage guide
- **[Build Guide](BUILD.md)** - Building and developing from source
- **[Migration Guide](PYTHON_MIGRATION.md)** - Python migration from Go
- **[Main Repository](https://github.com/PiliAlessio/Prometheus)** - Project documentation

## Support

- **GitHub Issues**: [PiliAlessio/Prometheus/issues](https://github.com/PiliAlessio/Prometheus/issues)
- **Releases**: [PiliAlessio/Prometheus/releases](https://github.com/PiliAlessio/Prometheus/releases)
- **Documentation**: [docs/INSTALLATION.md](../../docs/INSTALLATION.md)
- **PyPI Package**: [prometheus-cli](https://pypi.org/project/prometheus-cli/)

## Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for version history.

---

**Last Updated**: July 2026  
**Current Version**: 0.1.0  
**Status**: Active Development  
**Language**: Python 3.9+
