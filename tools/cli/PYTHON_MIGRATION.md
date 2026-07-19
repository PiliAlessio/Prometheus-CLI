# Prometheus CLI - Go to Python Migration Guide

## Overview

This document explains the migration of Prometheus CLI from Go to Python, including what changed, how to migrate, and frequently asked questions.

## What Changed?

### Language Migration

| Aspect | Go Version | Python Version |
|--------|-----------|-----------------|
| **Language** | Go 1.22+ | Python 3.9+ |
| **Build Tool** | go build, make | pip, setup.py |
| **Package Manager** | None (binaries) | PyPI |
| **Framework** | Custom | Click (CLI framework) |
| **Distribution** | Binary cross-compilation | Python wheels + source |
| **Installation** | Binary download or `go install` | `pip install` |
| **Runtime** | Single binary | Python interpreter |
| **Dependencies** | Built-in | Click, PyYAML, requests |

### Architecture Changes

**Go Version:**
```
tools/cli/
├── cmd/
│   └── prometheus/
│       └── main.go
├── pkg/
│   ├── init/
│   ├── version/
│   └── config/
├── Makefile
├── go.mod
├── go.sum
└── .goreleaser.yml
```

**Python Version:**
```
tools/cli/
├── src/
│   └── prometheus/
│       ├── __init__.py
│       ├── cli.py        # Main CLI entry point
│       ├── commands/
│       ├── config/
│       └── utils/
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── conftest.py
├── setup.py
├── pyproject.toml
└── requirements-dev.txt
```

### Installation Methods

**Go Version:**
```bash
# Method 1: go install
go install github.com/PiliAlessio/Prometheus/tools/cli/cmd/prometheus@latest

# Method 2: Binary download
curl -O https://github.com/.../prometheus-linux-amd64.tar.gz
tar xzf prometheus-linux-amd64.tar.gz
cp prometheus-linux-amd64 /usr/local/bin/

# Method 3: Build from source
make build
cp build/prometheus-linux-amd64 /usr/local/bin/
```

**Python Version:**
```bash
# Method 1: pip install (recommended)
pip install prometheus-cli

# Method 2: From source
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus/tools/cli
pip install -e .

# Method 3: Docker
docker run ghcr.io/piliAlessio/prometheus:latest version
```

## Why Python?

### Advantages

1. **Easier Development** - Python is more readable and easier to maintain
2. **Larger Ecosystem** - More libraries available (PyYAML, Click, requests)
3. **Better for Scripting** - Natural fit for DevOps and automation tools
4. **Cross-Platform** - Python interpreter handles all platform differences
5. **Faster Iteration** - No compilation step needed
6. **Community** - Python has a larger community for CLI tools
7. **Lower Learning Curve** - Easier for contributors to get involved
8. **Better Testing** - Python has mature testing frameworks (pytest)

### Trade-offs

| Aspect | Impact |
|--------|--------|
| **Binary Size** | Python versions larger (~30-50MB with interpreter) |
| **Startup Time** | Python slightly slower (~500ms vs <100ms) |
| **Runtime Dependency** | Requires Python installed (but increasingly standard) |
| **Performance** | Python slower for CPU-intensive tasks (not relevant for CLI) |

## Migration Guide for Users

### For End Users

#### Before (Go)
```bash
# Installation
go install github.com/PiliAlessio/Prometheus/tools/cli/cmd/prometheus@latest
# or
curl -O https://github.com/.../prometheus-linux-amd64.tar.gz
tar xzf prometheus-linux-amd64.tar.gz
cp prometheus-linux-amd64 /usr/local/bin/

# Verification
prometheus version
```

#### After (Python)
```bash
# Installation
pip install prometheus-cli
# or
pip install --upgrade pip && pip install prometheus-cli

# Verification
prometheus version
```

**All commands remain the same!** - No changes needed to workflows.

### For Contributors

#### Before (Go)
```bash
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus/tools/cli

go mod download
make build
make test
```

#### After (Python)
```bash
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus/tools/cli

python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

See [BUILD_PYTHON.md](BUILD_PYTHON.md) for detailed development setup.

## Removed Files

The following Go-related files have been removed:

```
DELETED: cmd/                          # Go command packages
DELETED: pkg/                          # Go package modules
DELETED: go.mod                        # Go module definition
DELETED: go.sum                        # Go dependency checksums
DELETED: Makefile                      # Go build targets
DELETED: BUILD.md                      # Go build guide (replaced)
DELETED: VERSION_STRATEGY.md           # Go versioning (replaced)
DELETED: .goreleaser.yml               # Go release automation
DELETED: .github/workflows/go-build.yml
DELETED: .github/workflows/go-lint.yml
DELETED: .github/workflows/go-test.yml
```

## New Files

```
CREATED: src/                          # Python source code
CREATED: tests/                        # Python tests
CREATED: setup.py                      # Python package setup
CREATED: pyproject.toml                # Python project config
CREATED: requirements-dev.txt          # Development dependencies
CREATED: BUILD_PYTHON.md               # Python build guide
CREATED: PYTHON_MIGRATION.md           # This file
```

## Compatibility

### Command Interface

✅ **Fully compatible** - All commands work exactly the same:

```bash
prometheus version           # Same output
prometheus init --help       # Same interface
prometheus init -y           # Same flags
```

### Configuration Files

✅ **Fully compatible** - YAML configuration unchanged:

```yaml
language:
  primary: python
  fallback: javascript
github:
  api_endpoint: https://api.github.com
```

### Environment Variables

✅ **Fully compatible** - All env vars work the same:

```bash
export GITHUB_TOKEN=your-token
prometheus init
```

### GitHub Integration

✅ **Fully compatible** - GitHub API integration unchanged

### Platform Support

| Platform | Go | Python |
|----------|-----|--------|
| Linux (x86_64) | ✅ | ✅ |
| Linux (ARM64) | ✅ | ✅ |
| macOS (Intel) | ✅ | ✅ |
| macOS (Apple Silicon) | ✅ | ✅ |
| Windows | ✅ | ✅ |
| FreeBSD | ✅ | ❌ (not tested) |

## FAQ

### Q: Do I need to change my workflow?

**A:** No! All commands and interfaces remain identical. Installation method changes, but usage stays the same.

### Q: Does Python need to be installed?

**A:** Yes, Python 3.9+ is required. However:
- Most modern systems have Python pre-installed
- It can be installed via package manager (apt, brew, choco)
- Many other tools require Python anyway

### Q: Will the CLI work exactly the same?

**A:** Yes! The behavior, output, and functionality are identical. All your scripts and workflows will continue to work.

### Q: Is this version faster or slower?

**A:** Slightly slower startup (~500ms vs <100ms), but:
- Typical init operation takes 1-5 seconds (difference is negligible)
- No impact on functionality
- Trade-off for better development experience and maintainability

### Q: Can I still use the Go version?

**A:** Not from this repository. The Go version has been completely removed. However:
- You can keep old binaries installed
- You can use the `git` version you prefer by checking out an older tag
- Functionality is identical, so upgrading is recommended

### Q: How do I upgrade from Go to Python version?

**A:** Simply install the new version:

```bash
pip install --upgrade prometheus-cli
prometheus version
```

That's it! No configuration changes needed.

### Q: What about the Makefile and Go-specific tools?

**A:** Removed. Use Python-based tools instead:

| Go | Python |
|----|--------|
| `make build` | `python -m build` |
| `make test` | `pytest tests/` |
| `go vet` | `flake8 src/` and `mypy src/` |
| `go fmt` | `black src/` |

### Q: Can I contribute to the Python version?

**A:** Yes! See [BUILD_PYTHON.md](BUILD_PYTHON.md) for setup instructions.

### Q: Where are the Go module examples?

**A:** Kept in `docs/examples/` for reference. See [docs/examples/](../../docs/examples/) directory.

### Q: How do I report issues with the Python version?

**A:** Same as before - open an issue on [GitHub](https://github.com/PiliAlessio/Prometheus/issues) with:
1. Output of `prometheus version`
2. Output of `python --version`
3. Steps to reproduce
4. Error message

## Version Information

### Current Versions

- **Python CLI Version**: 0.1.0
- **Python Requirement**: 3.9+
- **Release Date**: July 2026

### Version History

- **0.1.0** - Initial Python release (migrated from Go)

## Support

### Need Help?

- **Installation Issues**: See [INSTALLATION.md](../../docs/INSTALLATION.md)
- **Usage Questions**: See [CLI Guide](../../docs/CLI_GUIDE.md)
- **Development Setup**: See [BUILD_PYTHON.md](BUILD_PYTHON.md)
- **Report Bugs**: [GitHub Issues](https://github.com/PiliAlessio/Prometheus/issues)

### Roadmap

Future Python version features:
- [ ] Plugin system for extensibility
- [ ] Advanced configuration validation
- [ ] Performance optimizations
- [ ] Additional language templates
- [ ] GUI tool (optional)

## References

- [Installation Guide](../../docs/INSTALLATION.md)
- [CLI Guide](../../docs/CLI_GUIDE.md)
- [Build Guide](BUILD_PYTHON.md)
- [README](README.md)
- [Changelog](../../CHANGELOG.md)

---

**Migration Date**: July 2026  
**Python CLI Version**: 0.1.0  
**Status**: Active Development

For questions or feedback, please open an issue on [GitHub](https://github.com/PiliAlessio/Prometheus/issues).
