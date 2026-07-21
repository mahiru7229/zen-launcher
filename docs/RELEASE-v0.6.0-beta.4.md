# MCW Launcher v0.6.0 Beta 4

> Beta 4 completes the Modrinth workflow for both Fabric and Forge. Mods and modpacks now use an explicit loader filter while preserving the existing deferred-download, retry, progress, pause/resume, and update behavior.

---

## Tiếng Việt

### Bộ lọc loader trong Modrinth

Cả hai cửa sổ hiện có bộ lọc riêng:

```text
Browse Modrinth Mods
Loader: Fabric | Forge
```

```text
Browse Modrinth Modpacks
Loader: Fabric | Forge
```

- Khi mở Browse Mods từ một instance, bộ lọc mặc định khớp với loader của instance đó.
- Có thể đổi bộ lọc để xem dự án của loader khác, nhưng launcher không cho cài mod sai loader vào instance đang mở.
- Kết quả tìm kiếm hoặc danh sách phiên bản từ loader cũ được bỏ qua nếu người dùng đã đổi bộ lọc trong lúc request đang chạy.
- Release vẫn luôn được bật; Beta và Alpha tiếp tục là tùy chọn riêng.

### Mod Forge từ Modrinth

Mod Forge được cài bằng cùng flow đã dùng cho Fabric:

```text
Chọn mod
→ Chọn phiên bản Forge tương thích
→ Resolve dependency bắt buộc theo Forge
→ Tải vào cache
→ Kiểm tra JAR
→ Copy an toàn qua .part
→ Ghi registry Modrinth
```

- Dependency được tìm theo đúng Minecraft version và loader `forge`.
- Mod đã tải đúng hash chỉ được check, không tải lại.
- Registry ghi lại loader của từng mod để hỗ trợ update và diagnostics.
- Update check, update hàng loạt và version lock hoạt động cho cả Fabric lẫn Forge.
- Mod sai loader bị từ chối trước khi thay đổi thư mục `mods/`.

### Modpack Forge từ Modrinth

Browse Modpacks vẫn giữ giao diện và nút cũ, nhưng có thêm bộ lọc Fabric/Forge.

Flow cài Forge modpack:

```text
Tìm Forge modpack
→ Chọn version .mrpack
→ Đọc modrinth.index.json
→ Xác định Minecraft + Forge version
→ Chuẩn bị Forge runtime
→ Tạo instance Forge
→ Giải nén overrides an toàn
→ Ghi registry file
→ Chờ nhấn Launch để tải các file quản lý
```

Khi Launch:

```text
Check toàn bộ file
→ Tải toàn bộ file thiếu
→ Check lại
→ Retry tối đa 3 vòng
→ Launch hoặc báo lỗi
```

- Tải tối đa 8 file song song.
- Hiển thị tốc độ, số file còn lại và phần trăm.
- Pause/Resume giữ file `.part`.
- Tôn trọng giới hạn băng thông.
- File đúng hash không bị tải lại.
- `overrides/` và `client-overrides/` tiếp tục được giải nén an toàn.
- NeoForge và Quilt được từ chối rõ ràng, không bị hiểu nhầm là Forge.
- Nếu manifest không khớp bộ lọc đang chọn, launcher dừng trước khi tạo instance.

### Update modpack

- Modpack Forge được check update bằng filter `forge`.
- Runtime Forge đích được chuẩn bị và verify trước khi áp dụng update.
- Update không được tự đổi family loader giữa Fabric và Forge.
- Backup, preserved files và rollback vẫn hoạt động như trước.
- Registry cũ chưa có trường loader tiếp tục được hiểu là Fabric để giữ backward compatibility.

### Version

```python
VERSION = "v0.6.0 Beta 4"
VERSION_ID = "0.6.0-beta.4"
UPDATE_CHANNEL = "beta"
```

---

## English

### Loader filters for Modrinth

Both Modrinth browsers now provide an explicit loader filter:

```text
Fabric | Forge
```

- Browse Mods defaults to the selected instance loader.
- Browse Modpacks remains the same entry point and can switch freely between Fabric and Forge.
- Stale asynchronous results are ignored after the loader filter changes.
- A mod cannot be installed when the selected filter does not match the current instance loader.

### Forge mods from Modrinth

Forge mod installation now uses the same transactional workflow as Fabric:

- select a compatible Forge version;
- resolve required dependencies using the Forge loader filter;
- download and verify artifacts;
- install through the safe manual mod manager path;
- record Modrinth provenance and loader metadata;
- check and install updates without re-downloading valid files.

### Forge modpacks from Modrinth

Forge `.mrpack` files are now supported:

- parse the declared Minecraft and Forge versions;
- prepare the Forge runtime before instance creation;
- safely extract overrides;
- defer managed-file downloads until Launch;
- check all files before downloading;
- retry missing files for up to three rounds;
- reuse progress, pause/resume, bandwidth limiting, concurrent downloads, and manual fallback.

NeoForge and Quilt packs remain unsupported and are rejected explicitly.

### Compatibility

- Existing Fabric Modrinth workflows remain supported.
- Existing pack registries without a loader field default to Fabric.
- Managed pack updates cannot silently switch between Fabric and Forge.
- CurseForge integration remains outside the public `0.6.x` scope while API-key distribution requirements are being clarified.

---

## GitHub Release

```text
Tag: v0.6.0-beta.4
Title: MCW Launcher v0.6.0 Beta 4
Pre-release: enabled
```

Upload only:

```text
MCW-Launcher-v0.6.0-beta.4-windows-x64.zip
MCW-Launcher-v0.6.0-beta.4-windows-x64.zip.sha256
```
