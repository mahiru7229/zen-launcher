# MCW Launcher v0.5.0 Beta 9

> Accounts, Java, Modpack Lifecycle & Backup Update

Beta 9 gộp hai mốc roadmap Accounts/Java và Modpack/Backup thành một bản cập nhật lớn. Microsoft Authentication đã được chuẩn bị nhưng vẫn bị khóa cho đến khi ứng dụng được Mojang/Microsoft chấp thuận.

---

## Tiếng Việt

### Microsoft Authentication — prepared but locked

- Chuẩn bị đầy đủ luồng:
  - OAuth PKCE;
  - refresh token;
  - Xbox Live;
  - XSTS;
  - Minecraft Services;
  - kiểm tra entitlement;
  - lấy Minecraft profile;
  - tạo và lưu account.
- Nút **Add Microsoft account** vẫn xuất hiện và click được.
- Khi chưa được chấp thuận, launcher dừng tại approval gate:
  - không mở browser;
  - không gửi OAuth request;
  - không lưu account;
  - hiển thị thông báo đang chờ approval.
- Sau này chỉ cần bật feature flag và cung cấp `client_id` đã được chấp thuận để bắt đầu kiểm thử live flow.

### Java diagnostics

- Quét Java từ:
  - `JAVA_HOME`;
  - PATH;
  - Program Files;
  - Windows Registry;
  - managed runtimes.
- Chạy executable để xác minh Java thực sự hoạt động.
- Hiển thị:
  - major version;
  - vendor;
  - architecture;
  - source;
  - executable path.
- Thêm nút mở thư mục Java đã chọn.

### Backup và Restore

- Thêm định dạng `.mcwbackup`.
- Hỗ trợ:
  - **Full instance data**;
  - **Worlds only**.
- Backup được lưu riêng tại:

```text
backups/<instance-id>/
```

- Restore hoạt động theo transaction.
- Tự tạo safety backup trước khi thay dữ liệu hiện tại.
- Chặn path traversal, symbolic link và archive vượt giới hạn an toàn.
- Không đưa runtime lock, launcher metadata nội bộ, log hoặc crash report vào backup thường.

### Modrinth modpack update

- Kiểm tra phiên bản modpack mới theo channel Release/Beta/Alpha đã chọn.
- Tải và xác minh `.mrpack` mới.
- Tạo full safety backup trước khi cập nhật.
- So sánh managed files bằng checksum.
- Giữ lại:
  - file người dùng đã chỉnh sửa;
  - file unmanaged trùng đường dẫn với pack mới.
- Chỉ xóa file pack cũ khi file đó chưa bị người dùng sửa.
- Cập nhật Minecraft version và Fabric Loader profile của instance.
- Rollback file, profile và registry nếu cập nhật thất bại.
- Registry modpack được nâng lên schema 3, lưu `preservedFiles` và `lastBackup`.

### Theme update

Thêm các asset key:

```text
surface.microsoft_card
surface.java_card
surface.lifecycle_card
badge.locked
icon.action.microsoft
icon.action.java
icon.action.backup
icon.action.restore
```

Tài liệu mới:

```text
docs/THEME_CREATION_GUIDE.md
docs/THEME_ASSET_GUIDE.md
```

Mọi PNG vẫn optional và fallback an toàn khi thiếu hoặc lỗi.

### Giới hạn hiện tại

- Microsoft sign-in chưa thể sử dụng cho đến khi application được chấp thuận.
- Modpack updater tự giữ file conflict nhưng chưa có UI chọn hành động riêng cho từng file.
- Backup browser và retention policy chi tiết chưa có.
- Forge, NeoForge và Quilt chưa được hỗ trợ.
- Đây vẫn là bản Beta; hãy backup world quan trọng trước khi thử nghiệm.

---

## English

### Microsoft Authentication — prepared but locked

- Prepared the complete authentication pipeline:
  - OAuth PKCE;
  - token refresh;
  - Xbox Live;
  - XSTS;
  - Minecraft Services;
  - entitlement verification;
  - Minecraft profile retrieval;
  - account creation and persistence.
- The **Add Microsoft account** button remains visible and clickable.
- Until application approval is granted, the approval gate stops the flow before:
  - opening a browser;
  - sending an OAuth request;
  - saving an account.
- A single feature flag can enable the prepared pipeline after an approved `client_id` is available and live verification is completed.

### Java diagnostics

- Scan Java from:
  - `JAVA_HOME`;
  - PATH;
  - Program Files;
  - Windows Registry;
  - managed runtimes.
- Execute candidates to verify they work.
- Display major version, vendor, architecture, source, and executable path.
- Open the selected Java installation folder.

### Backup and restore

- Added the `.mcwbackup` format.
- Supports full-instance and worlds-only scopes.
- Stores archives under `backups/<instance-id>/`.
- Uses transactional restore staging.
- Creates a safety backup before replacing current data.
- Rejects unsafe paths, symbolic links, and oversized archives.
- Excludes runtime locks, internal launcher metadata, logs, and crash reports from normal backup payloads.

### Modrinth modpack updates

- Check newer pack versions using the enabled Release/Beta/Alpha channels.
- Download and validate the target `.mrpack`.
- Create a full safety backup before applying changes.
- Compare managed files using checksums.
- Preserve user-modified files and unmanaged path conflicts.
- Remove old managed files only when they remain unmodified.
- Update the instance Minecraft/Fabric runtime profile.
- Roll back files, profile, and registry metadata when installation fails.
- Upgraded the pack registry to schema 3 with `preservedFiles` and `lastBackup`.

### Theme update

Added dedicated Microsoft, Java, lifecycle, locked-status, backup, and restore assets. Theme creation and canvas documentation were expanded. All PNG assets remain optional and fall back safely.

### Current limitations

- Microsoft sign-in remains unavailable until the launcher application is approved.
- Modpack conflicts are preserved automatically, but per-file conflict choices are not yet exposed in the GUI.
- A dedicated backup browser and retention policy are not included yet.
- Forge, NeoForge, and Quilt are not supported.
- This is still a Beta release. Back up important worlds before testing.

---

## Release information

```text
Version: v0.5.0-beta.9
Channel: Beta / Pre-release
Platform: Windows x64
License: MIT
```

Suggested tag:

```text
v0.5.0-beta.9
```

Suggested asset:

```text
MCW-Launcher-v0.5.0-beta.9-windows-x64.zip
MCW-Launcher-v0.5.0-beta.9-windows-x64.zip.sha256
```

> Extract the entire ZIP before running the launcher. Do not run the executable directly from inside the archive.
