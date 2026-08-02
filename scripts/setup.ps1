param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$pluginRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $pluginRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $candidatePython = $null

    if ($env:ENVI_MCP_PYTHON -and (Test-Path -LiteralPath $env:ENVI_MCP_PYTHON)) {
        $candidatePython = $env:ENVI_MCP_PYTHON
    }

    if (-not $candidatePython) {
        $codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        if (Test-Path -LiteralPath $codexPython) {
            $candidatePython = $codexPython
        }
    }

    if (-not $candidatePython) {
        $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($pyLauncher) {
            & $pyLauncher.Source -3.12 -m venv (Join-Path $pluginRoot ".venv")
        } else {
            $python = Get-Command python.exe -ErrorAction SilentlyContinue
            if (-not $python) {
                throw "未找到 Python 3.11+。请安装 Python，或通过 ENVI_MCP_PYTHON 指定 python.exe。"
            }
            & $python.Source -m venv (Join-Path $pluginRoot ".venv")
        }
    } else {
        & $candidatePython -m venv (Join-Path $pluginRoot ".venv")
    }
}

$installTarget = if ($Dev) { "$($pluginRoot)[dev]" } else { $pluginRoot }
& $venvPython -m pip install --disable-pip-version-check -e $installTarget
if ($LASTEXITCODE -ne 0) {
    throw "ENVI Classic MCP 依赖安装失败。"
}

Write-Output "ENVI Classic MCP 环境已就绪：$venvPython"
