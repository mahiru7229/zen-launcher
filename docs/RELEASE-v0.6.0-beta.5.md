# MCW Launcher v0.6.0 Beta 5

> Beta 5 completes the managed Modrinth modpack lifecycle with repair, safer update tracking, and faster repeated verification.

## Tiếng Việt

### Modpack Repair

- Thêm nút **Repair modpack** trong trang Instances.
- Tải lại manifest `.mrpack` của phiên bản hiện tại và xác minh bắt buộc toàn bộ file được quản lý.
- Khôi phục file bị thiếu hoặc sai checksum, bao gồm file download, `overrides` và `client-overrides`.
- Tạo full backup trước khi thay thế file đầu tiên.
- Tự rollback file instance, runtime profile và registry nếu repair thất bại.
- Không xóa world hoặc file không do modpack quản lý.

### Modpack Update

- Bỏ qua download khi file đích đã đúng với manifest phiên bản mới.
- Bỏ qua copy khi file trong instance đã có checksum mục tiêu.
- File người dùng chỉnh sửa vẫn được giữ nguyên khi update, nhưng tiếp tục nằm trong registry để scan/repair nhận biết về sau.
- Registry mới được tạo lại verification cache sau update thành công.

### Tối ưu hiệu năng

- Nâng schema `modrinth-pack.json` lên **4**.
- Lưu verification cache theo path, size, `mtime_ns` và checksum mong đợi.
- Scan và kiểm tra trước launch không băm lại file nếu metadata không đổi.
- Size sai sẽ bị phát hiện ngay mà không cần đọc toàn bộ file.
- Modpack mới cài, update hoặc repair thành công được seed cache ngay, giảm chi phí ở lần launch kế tiếp.

### An toàn

- Repair dùng copy tạm rồi replace nguyên tử cho từng file.
- Download vẫn dùng checksum, HTTPS host policy, retry, pause/resume, bandwidth limit và progress chung.
- Update/repair bị chặn khi instance đang chạy.

## English

### Modpack Repair

- Added **Repair modpack** to the Instances page.
- Downloads the current `.mrpack` manifest and force-verifies every managed file.
- Restores missing or checksum-mismatched downloads, `overrides`, and `client-overrides` files.
- Creates a full backup before replacing the first instance file.
- Automatically rolls back instance data, runtime profile, and registry metadata when repair fails.
- Does not remove worlds or unmanaged files.

### Modpack Update

- Skips downloads when an existing instance file already matches the target manifest.
- Skips disk copies for already-correct target files.
- User-modified files remain preserved during update while staying tracked for later scan/repair actions.
- Rebuilds the verification cache after a successful update.

### Performance

- Upgraded `modrinth-pack.json` to schema **4**.
- Stores a verification cache using path, size, `mtime_ns`, and expected checksums.
- Repeated scans and pre-launch checks avoid hashing unchanged files.
- Size mismatches are rejected before reading full file contents.
- Fresh installs, updates, and repairs seed the cache immediately for a faster next launch.

### Safety

- Repair copies through a temporary file and atomically replaces each target.
- Downloads retain checksum verification, HTTPS host restrictions, retry, pause/resume, bandwidth limiting, and unified progress.
- Update and repair are blocked while the instance is running.

## Release metadata

```python
VERSION = "v0.6.0 Beta 5"
VERSION_ID = "0.6.0-beta.5"
UPDATE_CHANNEL = "beta"
```

```text
Tag: v0.6.0-beta.5
Title: MCW Launcher v0.6.0 Beta 5
Asset: MCW-Launcher-v0.6.0-beta.5-windows-x64.zip
```
