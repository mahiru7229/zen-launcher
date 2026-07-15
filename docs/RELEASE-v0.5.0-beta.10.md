# MCW Launcher v0.5.0 Beta 10

> Microsoft Account Security & Privacy Hardening

---

## Tiếng Việt

### Điểm nổi bật

- Nâng token storage lên **DPAPI v2** với context riêng theo account và loại token.
- Tự migrate token Microsoft từ Beta 9.
- Không lưu Minecraft access token dài hạn trong database.
- Thêm HMAC integrity cho từng account record.
- Account database tự chạy `quick_check` và bật `secure_delete`.
- Xóa account sẽ scrub token fields và compact database.
- Redact token khỏi log, error dialog và diagnostic report.
- Gia cố localhost OAuth callback bằng security headers và dọn state sau phiên.
- Thêm card **Account security** để verify hoặc re-protect credential.
- Cập nhật PNG theme assets cho security card và action icons.

### Migration

Beta 10 tự nâng `accounts.db` schema 1 lên schema 2. Profile, UUID, selected account và refresh token hợp lệ được giữ lại. Microsoft account có dữ liệu không giải mã được sẽ giữ profile nhưng xóa credential và yêu cầu đăng nhập lại.

### Lưu ý

- `client_id` là public application identifier và vẫn được nhúng trong EXE.
- Launcher không chứa `client_secret`; desktop OAuth dùng Authorization Code + PKCE.
- DPAPI ràng buộc credential với Windows user hiện tại.
- Đây vẫn là bản Beta. Hãy giữ backup của worlds và instance quan trọng.

---

## English

### Highlights

- Upgraded token storage to **DPAPI v2** with per-account and per-token context.
- Automatically migrates Beta 9 Microsoft credentials.
- Minecraft access tokens are no longer persisted long-term.
- Added HMAC integrity validation for account records.
- Account database now runs `quick_check` and enables `secure_delete`.
- Removing an account scrubs credential fields and compacts the database.
- Tokens are redacted from logs, error dialogs, and diagnostic reports.
- Hardened the localhost OAuth callback with security headers and state cleanup.
- Added an **Account security** card for verification and credential re-protection.
- Added PNG theme assets for the security card and actions.

### Migration

Beta 10 upgrades `accounts.db` from schema 1 to schema 2 automatically. Valid profiles, UUIDs, selected-account state, and refresh tokens are preserved. If stored credentials cannot be decrypted, the profile is retained but its credentials are cleared and interactive sign-in is required again.

### Notes

- The embedded `client_id` is a public application identifier.
- No `client_secret` is embedded; the desktop application uses Authorization Code with PKCE.
- DPAPI binds stored credentials to the current Windows user.
- This remains a Beta release. Keep backups of important worlds and instances.

---

## Release information

```text
Version: v0.5.0-beta.10
Channel: Beta / Pre-release
Platform: Windows x64
License: MIT
```

Suggested asset:

```text
MCW-Launcher-v0.5.0-beta.10-windows-x64.zip
MCW-Launcher-v0.5.0-beta.10-windows-x64.zip.sha256
```
