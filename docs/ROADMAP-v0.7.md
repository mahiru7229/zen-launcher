# MCW Launcher 0.7 Roadmap

## v0.7.0-beta.1 — CurseForge Gateway and provider cache

Status: **implemented, awaiting public beta testing**.

- [x] CurseForge Gateway integration without an embedded API key
- [x] CurseForge mod search
- [x] Compatible file/version selection for Fabric and Forge
- [x] Automatic download when third-party distribution is permitted
- [x] Manual mod download and SHA-1 verification fallback
- [x] Local JSON cache
- [x] 10 MiB cache limit with LRU eviction
- [x] Last-refreshed timestamp and cache source display
- [x] Refresh cooldown, failure backoff and request deduplication
- [x] Stale-cache fallback when the gateway is temporarily unavailable
- [x] Batch project/file metadata requests

## v0.7.0-beta.2 — MCW Modpack Catalog

- Full `.mcwpack`
- Thin `.mcwpack`
- SHA-256 verification
- Catalog metadata and version history
- GitHub Releases storage
- Download then import through the existing progress system

## v0.7.0-beta.3 — Storage and mirror providers

- Multiple download mirrors
- Cloudflare R2
- MCW server provider
- Automatic fallback
- Content-addressed cache
- Provider health and priority selection
