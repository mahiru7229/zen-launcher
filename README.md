# MCW Launcher

<p align="center">
  <strong>Trình khởi chạy Minecraft theo từng instance, được viết bằng Python và PySide6.</strong><br>
  <em>An instance-first Minecraft launcher built with Python and PySide6.</em>
</p>

<p align="center">
  <a href="https://github.com/mahiru7229/mcw-launcher/releases/latest">
    <img src="https://img.shields.io/badge/Current-v0.6.0--rc.1-blue" alt="Current version">
  </a>
  <a href="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml">
    <img src="https://github.com/mahiru7229/mcw-launcher/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4" alt="Windows">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
</p>

<p align="center">
  <a href="#tiếng-việt">Tiếng Việt</a> ·
  <a href="#english">English</a> ·
  <a href="docs/RELEASE-v0.6.0-rc.2.md">RC 2 release notes</a>
</p>

> [!WARNING]
> `v0.6.0-rc.2` là Release Candidate thứ hai của dòng 0.6 và vẫn dành cho tester trước khi lên Stable. Hãy sao lưu world quan trọng trước khi cập nhật modpack, sửa chữa instance hoặc thử Forge trên các phiên bản Minecraft cũ.

---

## Tiếng Việt

### MCW Launcher là gì?

MCW Launcher là launcher Minecraft mã nguồn mở, ưu tiên **instance độc lập**, tiến trình tải rõ ràng, khả năng sửa chữa an toàn và kiến trúc tách biệt giữa GUI với launcher core.

Mỗi instance có thư mục game, phiên bản Minecraft, mod loader, mods, saves, cấu hình Java, RAM và trạng thái runtime riêng. Launcher hiện tập trung cho Windows 10/11 64-bit.

### Điểm nổi bật của dòng 0.6

- Tạo và chạy instance **Vanilla, Fabric hoặc Forge**.
- Cài đặt, thay đổi và repair Fabric Loader hoặc Minecraft Forge.
- Tìm, cài và cập nhật mod từ **Modrinth** với bộ lọc loader/version/channel.
- Trang **Cài mod** độc lập chỉ hiển thị instance khớp chính xác Minecraft version và loader trước khi cài.
- Cài modpack `.mrpack`, kiểm tra update và **repair file modpack bị thiếu hoặc bị sửa**.
- Backup an toàn trước update/repair và rollback khi thao tác thất bại.
- Cache kết quả xác minh để không hash lại file modpack không đổi ở mỗi lần launch.
- Quản lý RAM bằng **slider + ô nhập MB chính xác**, với ràng buộc `Min ≤ Max ≤ RAM vật lý`.
- Hiển thị màn hình khởi động với tiến trình rõ ràng trong khi launcher chuẩn bị settings, database, tài khoản và giao diện.
- Tự chọn bố cục theo màn hình:
  - `1920×1080` trở lên → cửa sổ `1600×900`.
  - `1366×768` → cửa sổ gọn `1280×720`.
  - Màn hình nhỏ hơn → profile an toàn theo vùng hiển thị khả dụng.
- Dialog dùng màu chữ xám trung tính có thể đọc trên cả nền sáng lẫn nền tối khi Windows theme hiển thị sai.
- Sau khi cài hoặc repair loader, progress chuyển rõ ràng sang `100% / READY` thay vì mắc ở trạng thái đang tải.
- Khi launch thất bại, progress chỉ hiện thông báo ngắn; lỗi kỹ thuật đầy đủ nằm trong **Logs**.
- Microsoft OAuth PKCE, nhiều tài khoản Microsoft, SQLite và bảo vệ refresh token bằng Windows DPAPI.
- Theo dõi process Minecraft, thời gian chơi, exit code, game log và crash report.
- Hỗ trợ ngôn ngữ Việt/Anh và theme PNG ngoài EXE.

### Tải và chạy

Bản đóng gói dành cho Windows được phát hành tại trang **Releases**:

- [Mở trang phát hành](https://github.com/mahiru7229/mcw-launcher/releases)
- Stable dành cho người dùng thông thường vẫn thuộc dòng `0.5.1`.
- Dòng `0.6.x` sử dụng kênh `beta` và dành cho người chủ động tham gia tester program.

Yêu cầu cơ bản:

- Windows 10 hoặc Windows 11, 64-bit.
- Kết nối Internet khi tải phiên bản Minecraft, Java, mod loader, mods hoặc modpack lần đầu.
- Đủ dung lượng trống cho assets, libraries, Java runtimes, instances, backups và mods.

Java tương thích có thể được launcher tự phát hiện hoặc tải khi cần.

### Chạy từ source

Python `3.12` được khuyến nghị.

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
git switch beta/0.6

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python launcher.py
```

### Kiểm thử

```powershell
python -m pytest test -q
```

Quy tắc release của dự án: chỉ build khi test không có `failed` hoặc `error`.

### Build EXE và gói updater

```powershell
python -m PyInstaller --clean mcw_launcher.spec
python tools/build_release_zip.py --exe ".\dist\MCW Launcher.exe" --version "0.6.0-rc.2"
```

Kết quả updater package:

```text
MCW-Launcher-v0.6.0-rc.2-windows-x64.zip
MCW-Launcher-v0.6.0-rc.2-windows-x64.zip.sha256
```

Xem thêm [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md).

---

## English

### What is MCW Launcher?

MCW Launcher is an open-source Minecraft launcher centered around **isolated instances**, visible download progress, safe repair workflows, and a GUI that remains separate from launcher logic.

Each instance owns its game directory, Minecraft version, mod loader, mods, saves, Java configuration, memory allocation, and runtime state. The project currently targets 64-bit Windows 10 and Windows 11.

### v0.6 highlights

- Create and launch **Vanilla, Fabric, and Forge** instances.
- Install, change, and repair Fabric Loader or Minecraft Forge.
- Search, install, and update **Modrinth** mods with loader, version, and release-channel filtering.
- A standalone **Install Mods** page only offers instances matching the selected Minecraft version and loader.
- Install `.mrpack` modpacks, check for updates, and **repair missing or locally modified managed files**.
- Create safety backups before update/repair operations and roll back failed changes.
- Cache successful file verification so unchanged pack files are not hashed on every launch.
- Configure Java memory with a **slider and exact MB input**, enforcing `Min ≤ Max ≤ detected physical RAM`.
- Show a startup screen with clear progress while settings, databases, accounts, and the main interface are prepared.
- Select a responsive display profile automatically:
  - `1920×1080` or larger → `1600×900` window.
  - `1366×768` → compact `1280×720` window.
  - Smaller displays → a safe size based on available screen geometry.
- Apply a high-contrast compatibility palette to message dialogs to avoid white-on-white rendering issues.
- Keep launch-progress failures short while preserving complete technical details in **Logs**.
- Support Microsoft OAuth PKCE, multiple Microsoft accounts, SQLite storage, and Windows DPAPI protection for refresh tokens.
- Track the Minecraft process, play time, exit status, latest game log, and detected crash reports.
- Support English/Vietnamese language packs and external PNG themes.

### Download and run

Packaged Windows builds are published on the **Releases** page:

- [Open releases](https://github.com/mahiru7229/mcw-launcher/releases)
- The regular-user stable channel remains on the `0.5.1` line.
- `0.6.x` uses the opt-in `beta` tester channel.

Requirements:

- 64-bit Windows 10 or Windows 11.
- Internet access for first-time Minecraft, Java, loader, mod, and modpack downloads.
- Enough storage for assets, libraries, runtimes, instances, backups, and mods.

A compatible Java runtime can be detected or provisioned automatically.

### Run from source

Python `3.12` is recommended.

```powershell
git clone https://github.com/mahiru7229/mcw-launcher.git
cd mcw-launcher
git switch beta/0.6

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python launcher.py
```

### Test

```powershell
python -m pytest test -q
```

The release flow requires zero failed tests and zero collection/runtime errors before packaging.

### Build the EXE and updater package

```powershell
python -m PyInstaller --clean mcw_launcher.spec
python tools/build_release_zip.py --exe ".\dist\MCW Launcher.exe" --version "0.6.0-rc.2"
```

Expected updater assets:

```text
MCW-Launcher-v0.6.0-rc.2-windows-x64.zip
MCW-Launcher-v0.6.0-rc.2-windows-x64.zip.sha256
```

See [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md).

---

## Core capabilities

### Instances and runtime

- Per-instance metadata and settings.
- Create, rename, clone, delete, import, and export.
- `.mcwpack` packages and `.mcwbackup` backups.
- Runtime locks that prevent duplicate launches.
- Transactional restore and full-instance repair without deleting personal content.
- Configurable resolution, fullscreen, JVM/game arguments, Java path, and memory.

### Minecraft and Java

- Modern and legacy Minecraft argument formats.
- Client, library, asset, native, and logging downloads with checksum verification.
- Java scanning through `JAVA_HOME`, PATH, Program Files, Windows Registry, and managed runtimes.
- Compatible Java selection based on Minecraft metadata.
- Automatic runtime provisioning for supported Java majors.

### Mods and modpacks

- Fabric and Forge mod metadata parsing.
- Enable/disable, drag-and-drop, dependency analysis, duplicate-ID detection, and loader mismatch checks.
- Modrinth dependency installation, update checks, update locks, retry/resume, and fallback URLs.
- Managed modpack registry with update, repair, conflict preservation, backup, rollback, and verification cache.

### Accounts and privacy

- Offline and Microsoft accounts.
- Microsoft PKCE/Xbox/XSTS/Minecraft Services flow.
- Windows DPAPI protection for persisted refresh tokens.
- Access tokens kept in memory only.
- Credential and bearer-token redaction in logs and diagnostics.

### Interface

- PySide6 GUI with full and compact display profiles.
- Unified progress for launcher updates, Minecraft files, Java, mods, modpacks, imports, exports, and repairs.
- English and Vietnamese language packs.
- External PNG theme system with per-asset fallback.

---

## Project structure

```text
mcw-launcher/
├── launcher.py
├── mcw_launcher.spec
├── config/
├── docs/
├── lang/
├── src/
│   ├── core/
│   │   ├── account/
│   │   ├── auth/
│   │   ├── backup/
│   │   ├── instance/
│   │   ├── java/
│   │   ├── minecraft/
│   │   ├── mod/
│   │   ├── modloader/
│   │   ├── modrinth/
│   │   ├── network/
│   │   ├── progress/
│   │   ├── runtime/
│   │   ├── security/
│   │   ├── system/
│   │   ├── theme/
│   │   └── update/
│   ├── gui/
│   └── models/
├── test/
├── themes/
└── tools/
```

The GUI calls public core services instead of implementing Minecraft behavior directly.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/RELEASE-v0.6.0-rc.2.md`](docs/RELEASE-v0.6.0-rc.2.md) | Complete RC 2 release notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Core architecture |
| [`docs/INSTANCE_SYSTEM.md`](docs/INSTANCE_SYSTEM.md) | Instance metadata and lifecycle |
| [`docs/MODRINTH_INTEGRATION.md`](docs/MODRINTH_INTEGRATION.md) | Modrinth integration |
| [`docs/FORGE_MODRINTH.md`](docs/FORGE_MODRINTH.md) | Forge and Modrinth behavior |
| [`docs/PACKAGE_FORMAT.md`](docs/PACKAGE_FORMAT.md) | `.mcwpack` format |
| [`docs/UPDATE_PACKAGES.md`](docs/UPDATE_PACKAGES.md) | Updater-compatible release ZIPs |
| [`docs/LANGUAGE_PACKS.md`](docs/LANGUAGE_PACKS.md) | Language pack format |
| [`docs/THEME_ASSET_GUIDE.md`](docs/THEME_ASSET_GUIDE.md) | PNG theme assets and sizes |
| [`docs/gui-api.en.md`](docs/gui-api.en.md) / [`docs/gui-api.vi.md`](docs/gui-api.vi.md) | GUI integration API |

## Support status

| Component | Status in v0.6.0-rc.2 |
|---|---|
| Vanilla instances | Available |
| Fabric Loader and mods | Available |
| Forge Loader and mods | Beta |
| Modrinth mods and `.mrpack` modpacks | Beta — update and repair available |
| Microsoft accounts | Beta |
| Offline accounts | Available |
| English / Vietnamese | Available |
| PNG themes | Beta |
| NeoForge / Quilt | Not supported |
| CurseForge public integration | Deferred to `0.7.x` |

## Contributing and bug reports

Focused issues and pull requests are welcome. A useful bug report includes:

- MCW Launcher version.
- Windows and screen resolution/DPI.
- Minecraft, Java, and mod-loader versions.
- Reproduction steps.
- Relevant launcher/game logs and screenshots.

Never publish account databases, access/refresh tokens, private worlds, or other personal runtime data.

## License

MCW Launcher is released under the [MIT License](LICENSE).

Copyright © mahiru7229.
