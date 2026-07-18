# MCW Launcher v0.6.0 Beta 1

> First experimental release in the `0.6.x` line. Stable users only receive it after joining the Tester Program.

## Tiếng Việt

### Forge Loader

- Thêm Forge như một loader ngang hàng với Vanilla và Fabric.
- Tải danh sách phiên bản từ Forge Maven chính thức.
- Tự chọn bản Forge mới nhất tương thích khi dùng Auto.
- Tải và chạy Forge installer ngoài GUI thread.
- Import profile và libraries do Forge tạo ra vào cache launcher.
- Hỗ trợ đổi phiên bản và Repair Forge trong trang quản lý instance.
- Toàn bộ tiến trình tải/cài Forge xuất hiện trên thanh progress.

### CurseForge Mods

- Thêm trình duyệt CurseForge dành cho instance Forge.
- Tìm kiếm, lọc Minecraft version và chọn Release/Beta/Alpha.
- Cài file mod và dependency bắt buộc.
- Lưu project ID, file ID, hash và trạng thái tải để kiểm tra lại khi Launch.
- Mod hợp lệ đã có chỉ được check, không tải lại.

### CurseForge Modpacks

- Tìm kiếm và cài modpack CurseForge tương tự Modrinth.
- Đọc `manifest.json`, tạo instance Forge và giải nén `overrides` an toàn.
- Chỉ tải các file quản lý khi người dùng nhấn Launch.
- Check toàn bộ → tải toàn bộ file thiếu → check lại, tối đa 3 vòng.
- Hỗ trợ progress, pause/resume, giới hạn tốc độ và tải nhiều file song song.
- File bị giới hạn phân phối được báo để người chơi tải thủ công.

### API key

CurseForge yêu cầu API key. Launcher đọc key từ:

```text
MCW_CURSEFORGE_API_KEY
```

hoặc file local:

```text
config/curseforge.json
```

File local đã được thêm vào `.gitignore` và không được commit.

### Version

```python
VERSION = "v0.6.0 Beta 1"
VERSION_ID = "0.6.0-beta.1"
UPDATE_CHANNEL = "beta"
```

## English

### Forge Loader

- Added Forge as a first-class loader alongside Vanilla and Fabric.
- Loads compatible versions from the official Forge Maven repository.
- Downloads and runs the Forge installer outside the GUI thread.
- Imports generated profiles/libraries and supports Forge repair/change workflows.
- Forge installation progress uses the launcher-wide progress system.

### CurseForge Mods and Modpacks

- Added CurseForge browsing for Forge mods and Forge modpacks.
- Supports release-channel filters, required dependencies, safe override extraction, deferred downloads, three download rounds, pause/resume, bandwidth limiting, and concurrent workers.
- Existing valid files are verified and skipped.
- Files unavailable for third-party distribution receive manual-install guidance.

### Tester channel

This is an experimental update. Stable users must explicitly enable the Tester Program to receive `0.6.x` beta releases.

## Release files

```text
MCW-Launcher-v0.6.0-beta.1-windows-x64.zip
MCW-Launcher-v0.6.0-beta.1-windows-x64.zip.sha256
```

Mark the GitHub release as **Pre-release**.
