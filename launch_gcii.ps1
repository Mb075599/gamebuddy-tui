$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "gcii_tui.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $scriptPath @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $scriptPath @args
    exit $LASTEXITCODE
}

Write-Error "Python was not found in PATH. Install Python 3 and try again."
