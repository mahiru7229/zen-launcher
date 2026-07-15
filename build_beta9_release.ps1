param(
    [string]$Version = "0.5.0-beta.9",
    [string]$ExeName = "MCW Launcher.exe",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Checking repository state"

if (-not (Test-Path ".\mcw_launcher.spec")) {
    throw "mcw_launcher.spec was not found. Run this script from the project root."
}

if (-not (Test-Path ".\tools\build_release_zip.py")) {
    throw "tools/build_release_zip.py was not found."
}

$gitStatus = git status --porcelain
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read Git status."
}

if ($gitStatus) {
    Write-Host $gitStatus
    throw "Working tree is not clean. Commit or restore changes before building the release."
}

if (-not $SkipTests) {
    Write-Step "Running tests"
    python -m pytest test -q
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed. Release build stopped."
    }
}

Write-Step "Removing old build output"
Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\dist" -Recurse -Force -ErrorAction SilentlyContinue

Write-Step "Building windowed EXE with PyInstaller"
python -m PyInstaller --clean mcw_launcher.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$exePath = Join-Path ".\dist" $ExeName
if (-not (Test-Path $exePath)) {
    throw "Expected EXE was not created: $exePath"
}

Write-Step "Creating updater-compatible release ZIP"
python .\tools\build_release_zip.py --exe $exePath --version $Version
if ($LASTEXITCODE -ne 0) {
    throw "Release ZIP creation failed."
}

$zipName = "MCW-Launcher-v$Version-windows-x64.zip"
$zipPath = Join-Path ".\release" $zipName
$shaPath = "$zipPath.sha256"

if (-not (Test-Path $zipPath)) {
    throw "Expected release ZIP was not created: $zipPath"
}

Write-Step "Calculating final hashes"
$exeHash = (Get-FileHash $exePath -Algorithm SHA256).Hash.ToLower()
$zipHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()

Write-Host ""
Write-Host "Release build completed successfully." -ForegroundColor Green
Write-Host ""
Write-Host "EXE:"
Write-Host "  $exePath"
Write-Host "  SHA-256: $exeHash"
Write-Host ""
Write-Host "Release ZIP:"
Write-Host "  $zipPath"
Write-Host "  SHA-256: $zipHash"

if (Test-Path $shaPath) {
    Write-Host ""
    Write-Host "Checksum file:"
    Write-Host "  $shaPath"
}

Write-Host ""
Write-Host "Git tag:"
Write-Host "  v$Version"