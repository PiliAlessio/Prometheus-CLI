<#
.SYNOPSIS
    Wrapper script to run Prometheus CLI commands with automatic venv activation

.DESCRIPTION
    Automatically activates the virtual environment and runs prometheus commands.
    No need to manually activate the venv - just use this wrapper.

.EXAMPLE
    .\prometheus init
    .\prometheus pull
    .\prometheus sync
    .\prometheus help

.NOTES
    Make sure install.ps1 has been run first to set up the environment.
#>

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$VenvPath = ".venv"
$activate_script = Join-Path $VenvPath "Scripts\Activate.ps1"

# Check if venv exists
if (-not (Test-Path $activate_script)) {
    Write-Host "Error: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Run .\install.ps1 first to set up the environment" -ForegroundColor Yellow
    exit 1
}

# Activate venv and run command
& $activate_script
& prometheus @Arguments
