# CurseForge Gateway integration

MCW Launcher `v0.7.0-beta.1` introduces the first public CurseForge integration without embedding a CurseForge API key in the desktop application.

## Architecture

```text
MCW Launcher
    │ HTTPS JSON
    ▼
MCW CurseForge Gateway (Vercel)
    │ x-api-key stored only on the server
    ▼
CurseForge API
```

The launcher stores only the gateway URL. Mod files are not proxied through Vercel: the gateway returns metadata/download URLs and MCW Launcher's normal downloader fetches the file directly, reports progress, retries, and verifies SHA-1.

Default gateway:

```text
https://mcw-curseforge-gateway.vercel.app/api/curseforge
```

Local overrides are optional:

```json
{
  "schema_version": 2,
  "gateway_url": "https://example.vercel.app/api/curseforge",
  "client_token": ""
}
```

Save this as `config/curseforge.json`, or set:

```text
MCW_CURSEFORGE_GATEWAY_URL
MCW_CURSEFORGE_CLIENT_TOKEN
```

The client token is only a gateway access hint; a token distributed inside a desktop launcher must not be treated as a secret.

## Supported Beta 1 workflow

- Search CurseForge projects through the gateway.
- Filter compatible files by Minecraft version, Fabric/Forge loader, and release channel.
- Fetch project/file metadata in batches where possible.
- Install required CurseForge mod dependencies.
- Download automatically when `downloadUrl` is available and third-party distribution is permitted.
- If automatic distribution is unavailable, open the official project page and allow the user to select the downloaded `.jar`.
- Validate manually selected files by expected byte size and SHA-1 before adding them to the instance.
- Track installed and pending files in the CurseForge registry.

The manual-download flow is implemented for mods in Beta 1. CurseForge modpack handling remains experimental and should be tested on copied instances.

## Local JSON cache

CurseForge responses are stored under the launcher cache directory:

```text
cache/content/curseforge/api-v2/
├── index.json
└── entries/
```

Policy:

- Maximum disk size: `10 MiB`.
- Cleanup target: `8 MiB`.
- Eviction: least recently used entries first.
- Search TTL: 30 minutes.
- File lists: 1 hour.
- Project metadata: 12 hours.
- File metadata: 24 hours.
- Download URLs are resolved at install time and are not retained as permanent download authority.
- Cache writes use temporary files and atomic replacement.
- Invalid cache schema/data is discarded safely.

The browser displays:

- last successful refresh time;
- live/cached/stale source;
- current cache size and limit;
- latest refresh failure;
- manual-refresh cooldown.

If the gateway is temporarily unavailable, stale cached data may remain visible instead of clearing the page.

## Request control

Beta 1 reduces API traffic with:

- one in-flight request per normalized cache key;
- shared results for identical concurrent requests;
- manual refresh cooldown;
- increasing retry backoff after failures;
- support for the gateway's `Retry-After` response;
- batch project/file metadata requests;
- no empty-query search requests.

These client controls improve UX but do not replace server-side validation and rate limiting.

## Security and privacy

The cache must never contain:

- CurseForge API keys;
- Microsoft access or refresh tokens;
- account databases;
- authorization headers;
- private worlds or instance saves.

Only public project/file metadata is cached. The server's CurseForge API key stays in Vercel environment variables and is never returned to the launcher.
