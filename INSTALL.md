# Prometheus CLI - Quick Installation Guide

**One-command installation** for Windows, macOS, and Linux.

## Windows (PowerShell)

```powershell
# Clone or pull the latest code
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus

# Run the installation script
.\install.ps1
```

**Done!** The script:

- ✅ Creates a Python virtual environment
- ✅ Installs all dependencies  
- ✅ Sets up Prometheus CLI in editable mode
- ✅ Verifies everything works
- ✅ Shows next steps

### Options

```powershell
# Use custom virtual environment name
.\install.ps1 -VenvPath my-env

# Use specific Python version
.\install.ps1 -Python python3.10

# Both options
.\install.ps1 -VenvPath my-env -Python python3.10
```

## Linux / macOS (Bash)

```bash
# Clone or pull the latest code
git clone https://github.com/PiliAlessio/Prometheus.git
cd Prometheus

# Run the installation script
chmod +x install.sh
./install.sh
```

**Done!** Same as PowerShell - automated setup.

### Options

```bash
# Use custom virtual environment name
./install.sh --venv my-env

# Use specific Python version
./install.sh --python python3.10

# Both options
./install.sh --venv my-env --python python3.10
```

## After Installation

1. **Activate the virtual environment** (if not already active)

   *Windows:*

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   *Linux/macOS:*

   ```bash
   source .venv/bin/activate
   ```

2. **Verify installation**

   ```bash
   prometheus version
   ```

3. **Start using the CLI**

   ```bash
   prometheus help
   prometheus init
   ```

## To Update

Just run the installation script again - it will update everything:

*Windows:*

```powershell
.\install.ps1
```

*Linux/macOS:*

```bash
./install.sh
```

## Troubleshooting

### "Python not found"

- **Windows**: Install Python 3.9+ from python.org, ensure it's in PATH
- **Linux/macOS**: Install Python: `brew install python3` (macOS) or `apt install python3` (Linux)

### "Command not found: prometheus"

- Ensure virtual environment is activated (see "After Installation" section)
- Run `pip show prometheus-cli` to verify installation

### "Permission denied" (Linux/macOS)

```bash
chmod +x install.sh
./install.sh
```

### "Virtual environment already exists"

- The script detects and reuses existing environments
- To start fresh: `rm -rf .venv` then run the script

## What Gets Installed

```
Prometheus CLI:
├── click (8.1.7)        ← CLI framework
├── pyyaml (6.0.1)       ← YAML config parsing
└── requests (2.28+)     ← HTTP client

Development tools (dev):
├── pytest (7.0+)        ← Testing framework
├── pytest-cov (4.0+)    ← Code coverage
├── pytest-mock (3.12+)  ← Mocking library
├── black (23.0+)        ← Code formatter
├── flake8 (5.0+)        ← Linter
└── mypy (0.990+)        ← Type checker
```

## Installation Size

- **Total**: ~150 MB (includes venv + all dependencies)
- **CLI only**: ~10 MB
- **Installation time**: 30-60 seconds (first run), 5-10 seconds (updates)

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows 10+ | ✅ Fully supported | PowerShell 5.0+ required |
| macOS 10.14+ | ✅ Fully supported | Intel and Apple Silicon (M1/M2) |
| Linux | ✅ Fully supported | Any Linux distribution |

## Requirements

- **Python**: 3.9 or later
- **git**: For cloning the repository
- **Disk space**: ~500 MB (including workspace)
- **Internet**: For downloading dependencies

## For Corporate Deployment

If you need to distribute this to your team:

1. **Create a shared directory** on your network or artifact repository
2. **Run the install script** to create a central Python environment
3. **Create a shortcut/alias** for easy access
4. **Share installation guide** with team members

Example for team setup:

```powershell
# Shared network path
\\company\tools\prometheus\install.ps1
```

---

**Questions?** Check the main README.md for detailed documentation.
