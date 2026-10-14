<#
.SYNOPSIS
    Build, verify, and run the completed Enterprise Agentic Learning Plane locally.
#>
[CmdletBinding()]
param(
    [switch] $SkipInstall,
    [switch] $SkipTests,
    [string] $Python = 'python'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoPath '.venv\Scripts\python.exe'

if (-not $SkipInstall) {
    & $Python -m venv (Join-Path $RepoPath '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    & $VenvPython -m pip install --require-hashes -r (Join-Path $RepoPath 'requirements-dev.lock')
    if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
    Push-Location $RepoPath
    try {
        & $VenvPython -m pip install --no-deps --no-build-isolation -e .
        if ($LASTEXITCODE -ne 0) { throw 'Editable package installation failed.' }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Missing local environment. Run without -SkipInstall first."
}

Push-Location $RepoPath
try {
    if (-not $SkipTests) {
        & $VenvPython -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    }
    & $VenvPython -m learning_plane.cli demo all
    if ($LASTEXITCODE -ne 0) { throw 'Demo failed.' }
} finally {
    Pop-Location
}

Write-Host 'Local build, tests, and all-labs demo completed.' -ForegroundColor Green
