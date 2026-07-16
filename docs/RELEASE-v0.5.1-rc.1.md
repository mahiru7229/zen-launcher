# MCW Launcher v0.5.1 RC 1

> Release Candidate đầu tiên của dòng `v0.5.1`, tập trung vào kiểm định độ ổn định, phục hồi dữ liệu lỗi và gia cố các đường dẫn có thể làm launcher crash.

---

## Tiếng Việt

### Các lỗi đã sửa trước RC

- Sửa crash khi không thể tải version manifest và cache hiện có phải được dùng để chạy offline.
- Manifest tải mới được xác thực và ghi nguyên tử; response lỗi không còn ghi đè cache tốt.
- Settings instance bị hỏng hoặc sai kiểu dữ liệu không còn làm Launch crash.
- Settings lỗi JSON được sao lưu thành `settings.json.broken` trước khi tạo lại cấu hình an toàn.
- Một `instance.json` hỏng không còn làm toàn bộ danh sách instance biến mất.
- Tên instance không hợp lệ hoặc trùng tên thiết bị Windows như `CON`, `NUL`, `COM1` được từ chối sớm.
- Import `.mcwpack` và giải nén native JAR được bảo vệ khỏi path traversal, symlink và file độc hại.
- SQLite account connections được đóng đúng cách để tránh tích tụ handle hoặc `database is locked` trên Windows.
- File log Minecraft được đóng ở tiến trình launcher ngay sau khi Java khởi động, trong khi tiến trình game vẫn tiếp tục ghi log bình thường.
- Sửa `tools/build_release_zip.py` để chạy trực tiếp bằng đúng lệnh release từ bất kỳ working directory nào.
- Công cụ build ZIP từ chối version không khớp với `src/config.py`.
- Thông báo lỗi OAuth giữ lại mô tả lỗi do Microsoft trả về.

### Progress Import/Export instance

- Import và export `.mcwpack` giờ hiển thị trực tiếp trên thanh progress chung của launcher.
- Progress hiển thị file đang xử lý, dung lượng đã hoàn thành, dung lượng còn lại và phần trăm tổng.
- File lớn được cập nhật theo từng chunk thay vì chỉ nhảy từ `0%` lên `100%`.
- Export sử dụng file `.part` tạm và chỉ thay thế file đích sau khi ZIP hoàn tất, tránh để lại package hỏng khi tác vụ thất bại.
- Import kiểm tra toàn bộ entry trước khi ghi file, nên package có đường dẫn độc hại không thể để lại dữ liệu được giải nén một phần.

### Gia cố bảo mật và tính toàn vẹn

- Package ZIP từ chối đường dẫn tuyệt đối, `..`, symlink, tên Windows không hợp lệ và tên file trùng không phân biệt hoa thường.
- Native extraction không cho phép ghi file ra ngoài thư mục natives hoặc giả mạo marker `.extracted`.
- Giới hạn số file và tổng dung lượng giải nén để giảm rủi ro package bất thường.
- MD5/SHA-1 dùng cho UUID offline và metadata Mojang/Modrinth được đánh dấu rõ là hash tương thích giao thức, không phải hash bảo mật.

### Version

```text
Display version: v0.5.1 RC 1
Version ID: 0.5.1-rc.1
Update channel: beta
```

### Kiểm thử

```text
704 passed
0 failed
0 errors
0 skipped
0 xfailed
```

Các kiểm tra bổ sung:

- Full GUI suite với PySide6 ở chế độ offscreen.
- Toàn bộ `ResourceWarning` được nâng thành lỗi.
- Compile toàn bộ `src`, `test`, `tools` và `launcher.py`.
- Ruff kiểm tra syntax và undefined names.
- Bandit không còn cảnh báo mức Medium hoặc High.
- Smoke test cấu trúc release ZIP và `mcw-update.json`.
- Chạy trực tiếp `python tools/build_release_zip.py` từ working directory bên ngoài repo.

---

## English

### Fixes included before RC

- Fixed a crash when the online version manifest was unavailable and an existing cache should have been used offline.
- Downloaded manifests are validated and written atomically; invalid responses no longer replace a valid cache.
- Corrupted or incorrectly typed instance settings no longer crash Launch.
- Invalid JSON settings are backed up as `settings.json.broken` before safe defaults are recreated.
- One damaged `instance.json` no longer prevents all valid instances from being listed.
- Invalid instance names and reserved Windows device names such as `CON`, `NUL`, and `COM1` are rejected early.
- `.mcwpack` imports and native JAR extraction are protected from path traversal, symlinks, and malicious entries.
- SQLite account connections are closed reliably to avoid accumulated handles and possible `database is locked` failures on Windows.
- The launcher's Minecraft log handle is closed immediately after Java starts while the game process continues writing normally.
- Fixed `tools/build_release_zip.py` so the documented direct command works from any working directory.
- Release packaging rejects versions that do not match `src/config.py`.
- Microsoft OAuth errors retain the description returned by the provider.

### Instance import/export progress

- `.mcwpack` imports and exports now use the launcher's shared progress bar.
- Progress includes the current file, completed size, remaining size, and overall percentage.
- Large files update in chunks instead of jumping directly from `0%` to `100%`.
- Exports are written to a temporary `.part` file and only replace the destination after the ZIP completes, preventing corrupted packages after failures.
- Imports validate every archive entry before writing files, so a malicious path cannot leave partially extracted data behind.

### Security and integrity hardening

- Package archives reject absolute paths, `..`, symlinks, invalid Windows names, and case-insensitive duplicate entries.
- Native extraction cannot write outside the natives directory or spoof the `.extracted` marker.
- Archive file-count and extracted-size limits reduce risk from abnormal packages.
- MD5/SHA-1 uses required for offline UUIDs and Mojang/Modrinth metadata are explicitly marked as protocol compatibility hashes rather than security hashes.

### Version

```text
Display version: v0.5.1 RC 1
Version ID: 0.5.1-rc.1
Update channel: beta
```

### Testing

```text
704 passed
0 failed
0 errors
0 skipped
0 xfailed
```

Additional validation:

- Full PySide6 GUI suite in offscreen mode.
- All `ResourceWarning` messages promoted to errors.
- Full compilation of `src`, `test`, `tools`, and `launcher.py`.
- Ruff syntax and undefined-name checks.
- No Medium or High Bandit findings.
- Release ZIP and `mcw-update.json` structure smoke test.
- Direct execution of `python tools/build_release_zip.py` from outside the repository.

---

## Installation

1. Download the Windows x64 ZIP package.
2. Extract the entire archive into a new folder or over the previous installation.
3. Run `MCW Launcher.exe`.
4. Do not run the executable directly from inside the ZIP archive.

Recommended short path:

```text
C:\MCW
```

## GitHub Release

```text
Tag: v0.5.1-rc.1
Title: MCW Launcher v0.5.1 RC 1
Pre-release: enabled
```

Upload only:

```text
MCW-Launcher-v0.5.1-rc.1-windows-x64.zip
MCW-Launcher-v0.5.1-rc.1-windows-x64.zip.sha256
```
