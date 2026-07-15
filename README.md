# MCW Launcher

<p align="center">
  <strong>A modular, instance-based Minecraft launcher written in Python.</strong>
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml">
    <img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4" alt="Windows">
  <img src="https://img.shields.io/badge/Status-Beta-orange" alt="Beta">
</p>

> [!WARNING]
> MCW Launcher is under active beta development. Back up important worlds before testing new builds.

---

## Overview

MCW Launcher is an open-source Minecraft launcher focused on isolated instances, a modular core, visible launch progress, and a GUI that remains separate from launcher logic.

The project is currently developed primarily for Windows and uses PySide6 for its graphical interface.

## Features

### Minecraft launching

- Launch Vanilla Minecraft across modern and legacy version formats.
- Download and verify the client, libraries, assets, and native files.
- Build modern and legacy launch arguments.
- Select a compatible Java runtime automatically.
- Download and manage compatible Java runtimes when required.
- Display structured progress while preparing and launching the game.
- Track the Minecraft process until exit, including PID, exit code, session duration, latest game log, and crash report detection.

### Instance management

Each instance has its own game directory, metadata, settings, saves, mods, and runtime state.

- Create, rename, clone, and delete instances.
- Import and export instances using the `.mcwpack` format.
- Include or exclude saves while cloning or exporting.
- Configure memory, resolution, fullscreen mode, Java path, JVM arguments, and game arguments per instance.
- Prevent the same instance from being launched more than once at the same time.
- Show instances that are currently preparing or running.
- Fully repair an instance without touching worlds, mods, resource packs, screenshots, or instance settings.
- Record `last_played`, accumulated play time, last exit code, and crash state in instance metadata.

### Fabric and mods

- Create Vanilla or Fabric instances.
- Automatically select a recommended stable Fabric Loader version.
- Change or repair the Fabric Loader version from instance management.
- Cache Fabric metadata and reuse it when possible.
- Manage Fabric mods in a dedicated window.
- Add, remove, enable, or disable mod files.
- Read metadata from `fabric.mod.json`.
- Drag and drop supported mod JAR files into the Mod Manager.
- Analyze duplicate mod IDs, missing/disabled dependencies, version constraints, and declared Fabric conflicts.
- Check, install, and bulk-install compatible Modrinth mod updates.
- Lock individual Modrinth mods to prevent automatic dependency or bulk updates.

> Fabric API is a separate mod and is not installed automatically by the Fabric Loader itself.

### Modrinth

- Search and install Fabric mods from Modrinth.
- Install required Modrinth dependencies automatically.
- Search `.mrpack` modpacks and create isolated instances automatically.
- Filter versions by Release, Beta, and Alpha channels. Release remains enabled by default; Beta and Alpha require explicit opt-in.
- Persist channel preferences in `config/launcher_settings.json`.
- Verify downloaded files and protect modpack extraction paths.
- Track Modrinth mod provenance, installed versions, update locks, and managed modpack files.
- Detect missing or locally modified files that originally came from an installed `.mrpack`.
- Check and install newer modpack versions.
- Create a full safety backup before changing a managed modpack.
- Preserve user-modified and unmanaged conflicting files instead of overwriting them silently.
- Roll back instance files, runtime profile, and registry metadata when an update fails.

### PNG themes

- Load themes from `themes/<theme-id>/theme.json`.
- Replace launcher backgrounds, page backgrounds, dialogs, cards, buttons, inputs, progress bars, scrollbars, badges, logos, navigation icons, action icons, and state icons with PNG assets.
- Reload and preview themes from Launcher Settings.
- Fall back per component to the built-in CSS interface when a PNG is missing, invalid, or unreadable.
- Ship external themes beside the EXE so visual assets can be updated without rebuilding the launcher.

See [`docs/THEME_ASSET_GUIDE.md`](docs/THEME_ASSET_GUIDE.md) for every filename, path, and recommended canvas size.

### Accounts

- Offline account support.
- SQLite account storage.
- Windows DPAPI v2 protection for Microsoft refresh tokens, scoped per account and credential type.
- Microsoft OAuth PKCE, Xbox Live, XSTS, Minecraft Services, entitlement verification, profile retrieval, and token refresh.
- Add and store multiple Microsoft accounts, identified by Minecraft UUID.
- Microsoft sign-in runs in a background task and can be cancelled from the Accounts page without freezing the launcher.
- Minecraft access tokens remain in memory only; account records include integrity validation and security audit/re-protection controls.
- Logs, error dialogs, and diagnostic exports automatically redact OAuth credentials and bearer tokens.

### Java diagnostics

- Scan `JAVA_HOME`, PATH, Program Files, the Windows Registry, and managed runtime folders.
- Verify that discovered Java executables can run.
- Display Java major version, vendor, architecture, source, and executable path.
- Open the folder of a selected Java installation from Launcher Settings.

### Backup and restore

- Create full-instance or worlds-only `.mcwbackup` archives.
- Store backups separately under `backups/<instance-id>/`.
- Restore through a transactional staging directory.
- Create a safety backup before replacing current data.
- Reject unsafe archive paths and symbolic links.
- Keep launcher metadata, runtime locks, logs, and crash reports outside normal backup payloads.

### Language packs

Built-in language packs:

- `en-US.json` — English - US
- `vi-VN.json` — Tiếng Việt - Việt Nam

Language packs use semantic keys such as:

```text
instance.create.success
mod_manager.add_files
launcher_settings.language.label
```

A new language can be added by placing another compatible JSON file inside the `lang` directory. Missing translations fall back to `en-US`.

See [`docs/LANGUAGE_PACKS.md`](docs/LANGUAGE_PACKS.md) for the pack format.

### Reliability and development

- Shared HTTP client and reusable download pipeline.
- SHA-1 verification for Minecraft files.
- Atomic writes for important cache and metadata files.
- SQLite schema initialization and migration.
- Runtime instance locks with stale-lock recovery.
- Automated tests through GitHub Actions.
- Modular managers, models, controllers, pages, and presenters.

---

## Project structure

```text
mcw-launcher/
├── launcher.py
├── mcw_launcher.spec
├── lang/
│   ├── en-US.json
│   └── vi-VN.json
├── src/
│   ├── core/
│   │   ├── account/
│   │   ├── auth/
│   │   ├── backup/
│   │   ├── instance/
│   │   ├── java/
│   │   ├── language/
│   │   ├── minecraft/
│   │   ├── mod/
│   │   ├── modloader/
│   │   ├── modrinth/
│   │   ├── runtime/
│   │   ├── theme/
│   │   ├── network/
│   │   └── package/
│   ├── gui/
│   └── models/
├── docs/
├── test/
└── themes/
```

The GUI calls the public launcher core instead of implementing Minecraft logic directly.

---

## Requirements

### Running a packaged build

- Windows 10 or Windows 11, 64-bit.
- Internet access for the first download of a Minecraft version.
- Enough free storage for Minecraft assets, libraries, Java runtimes, instances, and mods.

Java can be detected or provisioned by the launcher.

### Running from source

- Python 3.12 is recommended.
- Git is optional but recommended.

Create a virtual environment:

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install PySide6 requests httpx cryptography
```

Start the launcher:

```powershell
python launcher.py
```

---

## Testing

Install test dependencies:

```powershell
python -m pip install pytest pytest-cov
```

Run the full test suite:

```powershell
python -m pytest test -v
```

GitHub Actions also runs the tests on pushes and pull requests targeting `main`.

---

## Build a Windows executable

Install PyInstaller:

```powershell
python -m pip install pyinstaller
```

Build using the project specification:

```powershell
python -m PyInstaller --clean mcw_launcher.spec
```

The specification creates a windowed executable and bundles the built-in language packs.

Windows SmartScreen may warn about unsigned beta builds. Code signing is not currently included.

---

## Runtime data

When running from source, runtime data is created beside the project. In a packaged build, it is created beside the executable.

```text
accounts/       Account database
backups/        Instance and world backup archives
cache/          Minecraft and mod-loader cache
config/         Launcher configuration
instances/      Instance directories and metadata
lang/           External language packs
runtimes/       Managed Java runtimes
themes/         Theme assets
```

Do not commit runtime data, downloaded Minecraft files, account databases, or personal worlds.

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Core architecture |
| [`docs/INSTANCE_SYSTEM.md`](docs/INSTANCE_SYSTEM.md) | Instance metadata and lifecycle |
| [`docs/PACKAGE_FORMAT.md`](docs/PACKAGE_FORMAT.md) | `.mcwpack` package format |
| [`docs/LANGUAGE_PACKS.md`](docs/LANGUAGE_PACKS.md) | Creating language packs |
| [`docs/THEME_ASSET_GUIDE.md`](docs/THEME_ASSET_GUIDE.md) | PNG theme filenames, paths, and canvas sizes |
| [`docs/THEME_CREATION_GUIDE.md`](docs/THEME_CREATION_GUIDE.md) | Step-by-step theme creation guide |
| [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md) | Building updater-compatible release ZIPs |
| [`docs/BETA7_RUNTIME_REPAIR.md`](docs/BETA7_RUNTIME_REPAIR.md) | Runtime monitoring, crash detection, and full instance repair |
| [`docs/BETA8_MOD_MANAGEMENT.md`](docs/BETA8_MOD_MANAGEMENT.md) | Mod updates, version locks, compatibility analysis, and managed modpack files |
| [`docs/BETA9_ACCOUNTS_JAVA_MODPACK_BACKUP.md`](docs/BETA9_ACCOUNTS_JAVA_MODPACK_BACKUP.md) | Microsoft authentication, Java diagnostics, backups, and safe modpack updates |
| [`docs/BETA10_ACCOUNT_SECURITY.md`](docs/BETA10_ACCOUNT_SECURITY.md) | DPAPI v2, account integrity, SQLite hardening, and privacy protections |
| [`docs/gui-api.en.md`](docs/gui-api.en.md) | GUI integration API in English |
| [`docs/gui-api.vi.md`](docs/gui-api.vi.md) | GUI integration API in Vietnamese |

---

## Current status

| Component | Status |
|---|---|
| Vanilla launch pipeline | Available |
| Instance system | Available |
| Offline accounts | Available |
| Automatic Java handling | Available |
| Java diagnostics and multi-source scanning | Beta |
| PySide6 GUI | Beta |
| Fabric Loader | Beta |
| Fabric Mod Manager | Beta — update, lock, and compatibility analysis available |
| Modrinth mods and Fabric modpacks | Beta — safe pack update and conflict preservation available |
| Release/Beta/Alpha Modrinth channels | Available |
| English and Vietnamese language packs | Available |
| Microsoft authentication | Beta — multi-account, cancellable sign-in, DPAPI v2 and integrity protection |
| Forge / NeoForge / Quilt | Not currently supported |
| Optional PNG theme system | Beta |
| Game lifecycle and crash detection | Beta |
| Full instance repair | Beta |
| Instance/world backup and transactional restore | Beta |

---

## Roadmap

Near-term priorities:

- Harden Microsoft token storage, revocation, session lifecycle, and account security for Beta 10.
- Add interactive per-file conflict resolution for modpack updates.
- Add backup retention rules, backup size previews, and a dedicated backup browser.
- Improve crash diagnostics and runtime history presentation.
- Continue replacing hard-coded GUI text with semantic translation keys.
- Improve packaged-build testing and release automation.
- Test community PNG themes across multiple DPI and screen sizes.

Other mod loaders should be developed and tested on separate branches before being included in stable beta releases.

---

## Contributing

Bug reports and focused pull requests are welcome.

When reporting a bug, include:

- MCW Launcher version.
- Windows version.
- Minecraft version.
- Selected Java and mod-loader version.
- Reproduction steps.
- Relevant logs or screenshots.

Please avoid committing downloaded game files, account data, tokens, worlds, build output, or local cache directories.

---

## License

MCW Launcher is released under the [MIT License](LICENSE).

Copyright © mahiru7229.