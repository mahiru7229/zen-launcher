# MCW Launcher v0.5.1 Beta 2

> Final beta for the v0.5.1 line

## Unified download progress

- All launcher-managed downloads report through the shared progress system, including launcher updates, Minecraft client files, libraries, assets, managed Java runtimes, Fabric artifacts, Modrinth mods, and Modrinth modpacks.
- Byte downloads show transferred size, remaining size, percentage, and current network speed using automatic B/KB/MB/GB/TB units.
- Multi-file downloads show completed files, remaining files, percentage, and aggregate network speed only while data is actively being transferred.
- Cached or verification-only work does not display a misleading network speed.

## Global bandwidth limit

- Added an optional global download limit in **Launcher Settings > Download bandwidth**.
- The value is configured in MB/s. A value of `0` means unlimited.
- Concurrent downloads share one global limit instead of each worker receiving the full limit independently.
- Existing launcher settings remain compatible and default to unlimited speed.

## Resilient downloader

- Interrupted downloads retain `.part` files and resume using HTTP Range when supported.
- Invalid or rejected ranges are discarded and restarted as full downloads in the same attempt.
- `206 Content-Range` responses are validated before appending data.
- Transient HTTP errors such as `408`, `425`, `429`, and server errors can be retried with `Retry-After` support.
- Permanent failures such as unusable `403` or `404` responses move to fallback URLs or fail clearly without wasteful retries.
- File size, SHA-1, SHA-256, and SHA-512 verification remain enforced where metadata is available.

## Pause and resume launch downloads

- While a launch task is preparing or downloading files, the Launch button changes to **Cancel** and remains clickable.
- Pressing Cancel pauses the active download cooperatively instead of terminating worker threads or corrupting destination files.
- Existing `.part` files are preserved. Pressing Launch again starts a fresh launch task and resumes supported downloads with HTTP Range.
- Pause is checked during Modrinth verification, Minecraft client/library/asset downloads, Fabric artifacts, managed Java downloads, retry delays, and bandwidth-limit waits.
- The paused state is shown as a warning rather than a launch failure, and no error dialog is displayed.
- Themes may provide `button.cancel*` assets and `control.cancel`. Missing Cancel artwork falls back to the bundled MCW PNG set.

## Modrinth check and retry flow

Each launch now follows a deterministic flow:

1. Check every managed Modrinth file.
2. Download all missing files.
3. Check the complete set again.
4. Repeat for up to three download rounds.
5. Perform a final check and either continue or report the remaining required files immediately.

Files that already match their expected hash are checked only and are never downloaded again. Failed files remain recorded and are retried during the same launch and again on later launches.

## Per-instance manual fallback

- Added **Instance Settings > Modrinth downloads > Stop launch when required Modrinth files are missing**.
- The option is enabled by default. Missing required files stop launch after three failed rounds and the error points to the setting.
- When disabled explicitly, the launcher continues after warning the user and records the exact relative paths that must be filled manually.
- This policy is stored independently for every instance and older settings use the safe enabled default.

## Release packaging

- `tools/build_release_zip.py` now writes its default output to `release/`, matching the documented beta release flow.
- The generated archive contains the wrapper directory, `MCW Launcher.exe`, `mcw-update.json`, language packs, themes, docs, README, and LICENSE.
- A matching SHA-256 file is generated beside the ZIP.

## Version

- Display version: `v0.5.1 Beta 2`
- Version ID: `0.5.1-beta.2`
- Update channel: `beta`

This is the final beta planned for v0.5.1. A stable release must still pass the complete release flow, including a clean Windows build and manual EXE verification.
