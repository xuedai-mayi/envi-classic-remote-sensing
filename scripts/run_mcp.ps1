$ErrorActionPreference = "Stop"
$pluginRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $pluginRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    & (Join-Path $PSScriptRoot "setup.ps1") | Out-Null
}

& $venvPython -m envi_classic_mcp.server
exit $LASTEXITCODE
