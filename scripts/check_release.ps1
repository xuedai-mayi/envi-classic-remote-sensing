$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    & (Join-Path $PSScriptRoot "setup.ps1") -Dev
}

& $pythonPath -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed."
}

$forbiddenPatterns = @(
    ("C:" + "\\" + "Users" + "\\"),
    ("1624" + "0110"),
    ([string][char]0x675C + [string][char]0x660A),
    ([string][char]0x65E5 + [string][char]0x5E38 + [string][char]0x5B9E + [string][char]0x9A8C),
    ("eval-" + "workspace"),
    ("eval-" + "review")
)

$trackedCandidates = Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch "[\\/]\.venv[\\/]" -and
    $_.FullName -notmatch "[\\/]\.git[\\/]" -and
    $_.FullName -notmatch "[\\/]__pycache__[\\/]"
}

$matches = $trackedCandidates | Select-String -Pattern $forbiddenPatterns -CaseSensitive:$false
if ($matches) {
    $matches | ForEach-Object { Write-Error "$($_.Path):$($_.LineNumber): $($_.Line)" }
    throw "Release check found a private path or personal identifier."
}

Write-Output "Release check passed."
