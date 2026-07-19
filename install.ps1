#Requires -Version 5.0
<#
.SYNOPSIS
    One-command Prometheus CLI installation script for Windows (PowerShell)

.DESCRIPTION
    Automatically handles:
    - Python environment setup (checks/creates venv)
    - Dependency installation
    - Prometheus CLI setup in editable mode
    - Verification that everything works

.PARAMETER VenvPath
    Virtual environment directory (default: .venv)

.PARAMETER Python
    Python executable to use (default: python from PATH)

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -VenvPath my-env

.NOTES
    Run from the Prometheus repository root directory
#>
param(
    [string]$VenvPath = ".venv",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

# Color output
$green = "`e[32m"
$red = "`e[31m"
$yellow = "`e[33m"
$reset = "`e[0m"

function Write-Success {
    Write-Host "$green✓ $args$reset"
}

function Write-Error {
    Write-Host "$red✗ $args$reset" -ForegroundColor Red
    exit 1
}

function Write-Info {
    Write-Host "$yellow→ $args$reset"
}

# 1. Check repository structure
Write-Info "Verifying Prometheus-CLI repository structure..."
$required_paths = @("tools/cli", ".git")
foreach ($path in $required_paths) {
    if (-not (Test-Path $path)) {
        Write-Error "Missing $path - run this script from Prometheus-CLI root directory"
    }
}
Write-Success "Repository structure verified"

# 2. Check Python installation
Write-Info "Checking Python installation..."
try {
    $python_version = & $Python --version 2>&1
    Write-Success "Found $python_version"
} catch {
    Write-Error "Python not found in PATH. Install Python 3.9+ or specify with -Python parameter"
}

# 3. Create virtual environment if needed
if (-not (Test-Path $VenvPath)) {
    Write-Info "Creating virtual environment at $VenvPath..."
    & $Python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
    }
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment already exists at $VenvPath"
}

# 4. Activate virtual environment
Write-Info "Activating virtual environment..."
$activate_script = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activate_script)) {
    Write-Error "Activation script not found at $activate_script"
}
& $activate_script
Write-Success "Virtual environment activated"

# 5. Upgrade pip
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip"
}
Write-Success "pip upgraded"

# 6. Install development dependencies
Write-Info "Installing development dependencies..."
cd tools/cli
pip install -e ".[dev]" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Prometheus CLI with development dependencies"
}
cd ../..
Write-Success "Prometheus CLI installed with dev dependencies"

# 7. Verify installation
Write-Info "Verifying installation..."
prometheus version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Prometheus CLI verification failed"
}
Write-Success "Installation verified"

Write-Host ""
Write-Success "Prometheus CLI installation complete!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. ${yellow}Activate the environment:${reset} .\$VenvPath\Scripts\Activate.ps1"
Write-Host "  2. ${yellow}Verify commands:${reset} prometheus help"
Write-Host "  3. ${yellow}Start using:${reset} prometheus init"
Write-Host ""
Write-Host "To update in the future, just run: ${green}.\install.ps1${reset}"
