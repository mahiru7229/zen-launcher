# Forge and CurseForge — MCW Launcher v0.6.0 Beta 1

## Scope

This beta adds Minecraft Forge as a first-class instance loader and adds CurseForge browsing for Forge mods and Forge modpacks. Vanilla, Fabric, and Modrinth behavior remain available.

## CurseForge API key

CurseForge API requests require an API key. MCW Launcher does not store a public key in the repository.

Use either:

```powershell
$env:MCW_CURSEFORGE_API_KEY="your-api-key"
.\dist\MCW Launcher.exe
```

or create a local file that is excluded by `.gitignore`:

```json
{
  "api_key": "your-api-key"
}
```

Save it as:

```text
config/curseforge.json
```

Never commit or publish this file.

## Forge workflow

```text
Create/Manage Instance
→ Select Forge
→ Load compatible Forge versions
→ Download the official installer
→ Run the installer outside the GUI thread
→ Import generated Forge libraries/profile
→ Launch through the normal Minecraft pipeline
```

Forge downloads use the shared progress reporter, pause/resume controller, bandwidth limiter, retry behavior, and file verification.

## CurseForge mod workflow

```text
Open a Forge instance
→ Manage Mods
→ Browse CurseForge
→ Select project and compatible file
→ Install required dependencies
→ Verify and copy JAR files into mods/
→ Save CurseForge provenance in .mcw/curseforge.json
```

## CurseForge modpack workflow

```text
Browse CurseForge Modpacks
→ Select pack file and instance name
→ Download and validate manifest.json
→ Resolve Minecraft + Forge versions
→ Create Forge instance
→ Safely extract overrides
→ Save managed-file registry
→ Download managed files when Launch is pressed
```

Managed files follow this launch flow:

```text
Check every file
→ Download all missing files
→ Check again
→ Retry up to 3 rounds
→ Launch or show the missing-file error
```

Files already present with the expected size/hash are checked and skipped, not downloaded again.

## Third-party distribution restrictions

Some CurseForge files are not available to third-party launchers. When the API marks a file unavailable or returns no permitted download URL, MCW Launcher records a clear manual-install error instead of treating the whole package as corrupted.

The existing per-instance managed-file policy controls whether missing required files block Launch after all retry rounds.

## Beta 1 limitations

- CurseForge browsing is Forge-focused.
- NeoForge modpacks are not supported in this beta.
- CurseForge requires developer/user API-key configuration.
- Forge installation must be manually verified on Windows before release because the CI/container environment cannot run the packaged Windows EXE.
