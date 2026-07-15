# MCW Launcher v0.5.0 Beta 8

> Mod Management Update — compatible mod updates, version locks, dependency diagnostics, and managed Modrinth modpack files.

---

## Tiếng Việt

### Mod Manager mới

- Thêm **Check updates**, **Update selected** và **Update all**.
- Chỉ kiểm tra phiên bản phù hợp với Minecraft, Fabric và kênh Release/Beta/Alpha đang bật.
- Hiển thị nguồn `Local` hoặc `Modrinth` cho từng mod.
- Hiển thị phiên bản đang cài và phiên bản mới nhất được phép.
- Cho phép **khóa phiên bản** từng mod Modrinth.
- Update All tự bỏ qua mod đã khóa.
- Cài dependency bắt buộc khi cập nhật.

### Phân tích tương thích Fabric

- Phát hiện mod ID bị trùng.
- Phát hiện dependency bắt buộc bị thiếu hoặc đang bị disable.
- Kiểm tra một số constraint phiên bản an toàn.
- Hiển thị mod server-only đang được bật.
- Phát hiện khai báo `conflicts` và `breaks`.
- Cảnh báo Fabric API thông qua dependency `fabric-api` thực tế của mod.

### Quản lý file modpack

- `.mrpack` mới lưu danh sách file được pack quản lý.
- Ghi lại SHA-1, SHA-512, kích thước và layer nguồn.
- Có thể phát hiện file pack bị thiếu hoặc đã được người dùng chỉnh sửa.
- Beta 8 chưa tự ghi đè file đã chỉnh sửa; đây là nền móng cho update modpack an toàn ở bản sau.

### Lưu ý

- Chỉ mod được cài từ Modrinth mới có update và version lock.
- Mod JAR thêm thủ công vẫn được quản lý như mod cục bộ.
- Đóng Minecraft trước khi cập nhật, xóa, bật/tắt hoặc khóa mod.
- Forge, NeoForge và Quilt chưa được hỗ trợ.

---

## English

### New Mod Manager workflow

- Added **Check updates**, **Update selected**, and **Update all**.
- Only versions compatible with the instance Minecraft version, Fabric, and enabled Release/Beta/Alpha channels are considered.
- Shows `Local` or `Modrinth` provenance for each mod.
- Shows the installed and latest allowed versions.
- Added per-project **version locks**.
- Update All skips locked mods.
- Required dependencies remain enabled during updates.

### Fabric compatibility analysis

- Detects duplicate mod IDs.
- Detects missing or disabled required dependencies.
- Evaluates safe version constraints when possible.
- Reports enabled server-only mods.
- Detects declared `conflicts` and `breaks` relationships.
- Fabric API warnings come from the mod's real `fabric-api` dependency declaration.

### Managed modpack files

- New `.mrpack` installations record managed files.
- Stores SHA-1, SHA-512, size, and source layer.
- Can detect missing or locally modified pack files.
- Beta 8 does not automatically overwrite modified files; this metadata prepares a safe future modpack updater.

### Notes

- Update and version-lock controls apply only to Modrinth-installed mods.
- Manually added JARs remain local mods.
- Close Minecraft before changing or updating mods.
- Forge, NeoForge, and Quilt are not supported.

---

## Release information

```text
Version: v0.5.0-beta.8
Channel: Beta / Pre-release
Platform: Windows x64
License: MIT
```

Suggested asset:

```text
MCW-Launcher-v0.5.0-beta.8-windows-x64.zip
```
