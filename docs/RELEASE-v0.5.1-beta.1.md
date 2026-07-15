# MCW Launcher v0.5.1 Beta 1

## Download progress telemetry

- Download progress now shows the current network speed using automatic B/s, KB/s, MB/s, GB/s, or TB/s formatting.
- Byte-based downloads show the remaining transfer size.
- File-based progress shows how many files remain.
- The telemetry applies to Minecraft files, Modrinth content, Java runtime downloads, and launcher updates.

## Per-instance Modrinth failure policy

- Added a per-instance option under **Instance Settings > Modrinth downloads**.
- The option is enabled by default and blocks launch when required Modrinth files remain missing after three complete check/download rounds.
- The blocking error now explains where the option can be disabled.
- When disabled, the launcher continues starting Minecraft, keeps the failed download records, and shows the exact files and instance paths that must be filled manually.
- Existing instance settings remain compatible; instances without the new field use the safe default (`true`).

## Version

- Display version: `v0.5.1 Beta 1`
- Version ID: `0.5.1-beta.1`
- Update channel: `beta`
