# MCW Launcher update packages

Automatic updates use a GitHub Release ZIP. The ZIP must contain the packaged launcher executable and may contain any other file or directory that should overwrite the current installation.

## Build Beta 3

After building the EXE with PyInstaller:

```powershell
python tools/build_release_zip.py --exe ".\dist\MCW Launcher.exe" --version "0.5.0-beta.3"
```

The command creates:

```text
MCW-Launcher-v0.5.0-beta.3-windows-x64.zip
MCW-Launcher-v0.5.0-beta.3-windows-x64.zip.sha256
```

The package contains a single wrapper directory:

```text
MCW-Launcher-v0.5.0-beta.3-windows-x64/
├── MCW Launcher.exe
├── mcw-update.json
├── lang/
├── README.md
└── LICENSE
```

`mcw-update.json` lets Beta 3 and later verify that the downloaded package matches the selected GitHub release before replacing files.

## Test the Beta 2 → Beta 3 updater

1. Build and publish the Beta 3 ZIP as an asset of a GitHub pre-release tagged `v0.5.0-beta.3`.
2. The asset name should contain `MCW`, `windows`, and `x64`.
3. Start the packaged Beta 2 launcher.
4. Use **Launcher Settings → Check for updates** if the automatic check has already run recently.
5. Confirm the update prompt, release notes, package size, backup, overwrite, restart, and `logs/updater.log`.
6. Confirm `config`, `instances`, `accounts`, and other user data remain intact.

The updater copies and overwrites files present in the ZIP. It does not delete unrelated files from the installation directory.
