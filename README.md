# Prometheus CLI

The command-line interface and installation scripts for the Prometheus ecosystem.

## Overview

This repository contains:
- **CLI Tool**: The Prometheus command-line interface for project initialization and management
- **Installation Scripts**: Automated setup for Windows (PowerShell) and Unix-like systems (Bash)

## Quick Start

### Windows (PowerShell)

```powershell
git clone https://github.com/PiliAlessio/Prometheus-CLI.git
cd Prometheus-CLI
.\install.ps1
```

### Linux / macOS

```bash
git clone https://github.com/PiliAlessio/Prometheus-CLI.git
cd Prometheus-CLI
chmod +x install.sh
./install.sh
```

## Documentation

- [Installation Guide](./INSTALL.md) - Detailed installation instructions and troubleshooting
- [CLI Tool Documentation](./tools/cli/README.md) - Usage and commands
- [Prometheus Core](https://github.com/PiliAlessio/Prometheus) - Core instructions and workflows

## Structure

```
Prometheus-CLI/
├── tools/
│   └── cli/              # Python CLI implementation
│       ├── src/          # CLI source code
│       ├── tests/        # Test suite
│       └── pyproject.toml
├── install.ps1           # Windows installation script
├── install.sh            # Unix/Linux installation script
└── INSTALL.md            # Installation guide
```

## Requirements

- **Python**: 3.9 or later
- **Git**: For cloning repositories
- **Disk space**: ~500 MB (including dependencies)
- **Internet**: For downloading dependencies

## License

Same as Prometheus Core

---

For more information, see [Prometheus Core](https://github.com/PiliAlessio/Prometheus).
