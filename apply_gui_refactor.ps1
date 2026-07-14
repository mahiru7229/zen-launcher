param(
    [Parameter(Mandatory = $false)]
    [string]$RepoPath = "."
)

$ErrorActionPreference = "Stop"
$RepoPath = (Resolve-Path $RepoPath).Path
$SourceRoot = $PSScriptRoot
$SourceGui = Join-Path $SourceRoot "src\gui"
$DestinationGui = Join-Path $RepoPath "src\gui"

if (-not (Test-Path (Join-Path $RepoPath "src"))) {
    throw "Repo path does not contain a src folder: $RepoPath"
}

New-Item -ItemType Directory -Force -Path $DestinationGui | Out-Null
Copy-Item (Join-Path $SourceGui "*") $DestinationGui -Recurse -Force
Copy-Item (Join-Path $SourceRoot "launcher.py") (Join-Path $RepoPath "launcher.py") -Force

Write-Host "MCW Launcher GUI refactor copied to: $RepoPath"
Write-Host "Run: python launcher.py"
