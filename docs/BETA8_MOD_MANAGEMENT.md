# MCW Launcher Beta 8 — Mod Management

Beta 8 turns the Fabric Mod Manager from a file list into a managed update and compatibility workflow.

## Modrinth update tracking

Mods installed from Modrinth are tracked in:

```text
<instance>/.mcw/modrinth.json
```

Registry schema 2 stores:

- Modrinth project and version IDs;
- installed version number and release channel;
- installed filename and SHA-1;
- project title and source;
- version-lock state;
- publication/update timestamps when available.

Registry schema 1 is migrated in memory and written back as schema 2 on the next change.

## Check and install updates

The Mod Manager can:

- check all tracked mods for versions compatible with the instance Minecraft version and Fabric;
- respect the enabled Release/Beta/Alpha preferences;
- update selected mods;
- update all unlocked mods;
- keep dependency installation enabled;
- avoid downgrading a newer prerelease to an older stable release when publication data is available.

A manually added or replaced JAR is treated as a local mod and removes stale Modrinth provenance for that filename.

## Version locks

A tracked Modrinth mod can be locked. Locked mods are skipped by Update All and are not automatically replaced when another Modrinth mod resolves that project as a dependency.

Version locking does not prevent an explicit manual install from the Modrinth browser.

## Compatibility analysis

The offline compatibility scanner reads `fabric.mod.json` and reports:

- duplicate enabled mod IDs;
- broken or non-Fabric JARs;
- enabled server-only mods;
- missing required dependencies;
- required dependencies that are disabled;
- confidently detected version-constraint mismatches;
- missing recommended dependencies;
- declared `conflicts` and `breaks` relationships.

Minecraft and Fabric Loader are included as built-in dependency versions. A missing `fabric-api` requirement is therefore shown as a normal missing dependency instead of a special hard-coded guess.

The scanner is intentionally conservative: a complex version expression that cannot be evaluated safely is not reported as a false incompatibility.

## Managed modpack files

New Modrinth modpack installs write schema 2 metadata to:

```text
<instance>/.mcw/modrinth-pack.json
```

The metadata contains the final path, SHA-1, SHA-512, size, and source layer for every downloaded or overridden managed file. `client-overrides` correctly replaces earlier entries for the same path.

`ModrinthPackRegistry.scan(instance)` can report managed files that are:

- missing;
- modified locally.

Beta 8 records this information as the safety foundation for a later modpack update workflow. It does not overwrite modified pack files automatically.

## Safety rules

- Mod changes and updates are blocked while the instance is running.
- Registry and pack metadata use atomic writes.
- Tracked paths are restricted to the instance.
- Manual user files remain outside managed-file ownership.
- Update All skips locked projects.
- Modpack managed-file scanning is read-only.
