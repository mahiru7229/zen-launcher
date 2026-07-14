from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

from src.models.update.update_info import PreparedUpdate


class AutomaticUpdateUnsupportedError(RuntimeError):
    pass


class WindowsUpdateInstaller:
    @staticmethod
    def is_supported() -> bool:
        return os.name == "nt" and bool(getattr(sys, "frozen", False))

    @classmethod
    def launch(cls, prepared: PreparedUpdate, install_directory: Path | None = None, executable_path: Path | None = None, parent_pid: int | None = None) -> Path:
        if not cls.is_supported():
            raise AutomaticUpdateUnsupportedError("Automatic installation is only available in the packaged Windows launcher.")

        executable = Path(executable_path) if executable_path is not None else Path(sys.executable)
        destination = Path(install_directory) if install_directory is not None else executable.resolve().parent
        source = prepared.content_directory.resolve()
        destination = destination.resolve()
        executable = executable.resolve()

        if not source.is_dir():
            raise FileNotFoundError(f"Prepared update directory does not exist: {source}")
        if not destination.is_dir():
            raise FileNotFoundError(f"Launcher directory does not exist: {destination}")
        if executable.parent != destination:
            raise RuntimeError("The launcher executable must be inside the installation directory.")
        if not (source / executable.name).is_file():
            raise RuntimeError(f"The update ZIP does not contain the expected executable: {executable.name}")

        updater_directory = Path(tempfile.gettempdir()) / f"mcw-launcher-updater-{uuid.uuid4().hex}"
        updater_directory.mkdir(parents=True, exist_ok=False)
        script_path = updater_directory / "update.ps1"
        script_path.write_text(cls._script_text(), encoding="utf-8-sig")

        command = [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-ParentPid",
            str(parent_pid if parent_pid is not None else os.getpid()),
            "-SourceDirectory",
            str(source),
            "-DestinationDirectory",
            str(destination),
            "-ExecutableName",
            executable.name,
            "-UpdaterDirectory",
            str(updater_directory),
            "-StagingDirectory",
            str(prepared.staging_directory.resolve()),
        ]
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        subprocess.Popen(command, cwd=str(destination), close_fds=True, creationflags=creation_flags)
        return script_path

    @staticmethod
    def _script_text() -> str:
        return r"""param(
    [Parameter(Mandatory=$true)][int]$ParentPid,
    [Parameter(Mandatory=$true)][string]$SourceDirectory,
    [Parameter(Mandatory=$true)][string]$DestinationDirectory,
    [Parameter(Mandatory=$true)][string]$ExecutableName,
    [Parameter(Mandatory=$true)][string]$UpdaterDirectory,
    [Parameter(Mandatory=$true)][string]$StagingDirectory
)

$ErrorActionPreference = "Stop"
$logPath = Join-Path $UpdaterDirectory "update.log"
$backupDirectory = Join-Path $UpdaterDirectory "backup"
$newFiles = New-Object System.Collections.Generic.List[string]
$completed = $false

function Write-UpdateLog([string]$Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $logPath -Value "[$timestamp] $Message" -Encoding UTF8
}

function Invoke-Robocopy([string]$Source, [string]$Destination) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    & robocopy.exe $Source $Destination /E /COPY:DAT /DCOPY:DAT /R:3 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -ge 8) {
        throw "Robocopy failed with exit code $exitCode"
    }
}

function Backup-ExistingFiles {
    Write-UpdateLog "Creating rollback backup"
    Get-ChildItem -LiteralPath $SourceDirectory -File -Recurse -Force | ForEach-Object {
        $relativePath = $_.FullName.Substring($SourceDirectory.Length).TrimStart([char]'\')
        $destinationPath = Join-Path $DestinationDirectory $relativePath
        if (Test-Path -LiteralPath $destinationPath -PathType Leaf) {
            $backupPath = Join-Path $backupDirectory $relativePath
            $backupParent = Split-Path -Parent $backupPath
            New-Item -ItemType Directory -Path $backupParent -Force | Out-Null
            Copy-Item -LiteralPath $destinationPath -Destination $backupPath -Force
        }
        elseif (-not (Test-Path -LiteralPath $destinationPath)) {
            $newFiles.Add($destinationPath)
        }
    }
}

function Restore-Backup {
    Write-UpdateLog "Restoring files after update failure"
    foreach ($path in $newFiles) {
        Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $backupDirectory -PathType Container) {
        Invoke-Robocopy $backupDirectory $DestinationDirectory
    }
}

try {
    Write-UpdateLog "Waiting for launcher process $ParentPid"
    Wait-Process -Id $ParentPid -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 700

    Backup-ExistingFiles
    Write-UpdateLog "Copying update from $SourceDirectory to $DestinationDirectory"
    Invoke-Robocopy $SourceDirectory $DestinationDirectory

    $updatedExecutable = Join-Path $DestinationDirectory $ExecutableName
    if (-not (Test-Path -LiteralPath $updatedExecutable -PathType Leaf)) {
        throw "Updated executable was not found: $updatedExecutable"
    }

    Write-UpdateLog "Starting updated launcher"
    Start-Process -FilePath $updatedExecutable -WorkingDirectory $DestinationDirectory
    $completed = $true
    Remove-Item -LiteralPath $StagingDirectory -Recurse -Force -ErrorAction SilentlyContinue
    Write-UpdateLog "Update completed"
}
catch {
    Write-UpdateLog "Update failed: $($_.Exception.Message)"
    try {
        Restore-Backup
    }
    catch {
        Write-UpdateLog "Rollback failed: $($_.Exception.Message)"
    }
    Add-Type -AssemblyName PresentationFramework -ErrorAction SilentlyContinue
    [System.Windows.MessageBox]::Show(
        "MCW Launcher could not finish the update.`n`n$($_.Exception.Message)`n`nLog: $logPath",
        "MCW Launcher Update",
        "OK",
        "Error"
    ) | Out-Null
}
finally {
    if ($completed) {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "timeout /t 2 /nobreak >nul & rmdir /s /q `"$UpdaterDirectory`"" -WindowStyle Hidden
    }
}
"""
