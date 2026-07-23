# MCW Launcher v0.6.0 RC 1

> Release Candidate đầu tiên của dòng `0.6`, tập trung đóng các lỗi giao diện cuối, ngăn cài mod nhầm instance và bảo vệ thay đổi cài đặt chưa được lưu trước giai đoạn compatibility matrix.

---

## Tiếng Việt

### Sửa luồng tạo instance rồi cài mod

- Tác vụ cài mod không còn được khởi chạy khi tác vụ tạo instance vẫn chưa giải phóng trạng thái blocking.
- Thêm tín hiệu `task_settled`, chỉ chạy bước cài mod sau khi task loader đã được dọn dẹp hoàn toàn.
- Xác minh lại tên instance và loader thực tế trước khi tiếp tục cài mod.
- Các request tải danh sách Fabric/Forge version trùng nhau được bỏ qua im lặng, không còn hiện thông báo `Task ... is already running`.
- Nếu bước cài mod tiếp theo không thể bắt đầu, launcher báo rõ rằng instance đã tạo nhưng mod chưa được cài.

### Sửa startup splash bị đứng

- Các bước bootstrap có I/O được chạy ngoài Qt GUI thread, giúp splash tiếp tục phản hồi khi database hoặc bảo mật tài khoản mất nhiều thời gian.
- Startup có timeout 45 giây và báo chính xác bước đang bị kẹt.
- Báo cáo `startup-error.log` giờ ghi thêm startup stage và giữ nguyên traceback từ worker thread.
- Hộp thoại lỗi được đặt làm con của splash, tránh bị splash luôn-on-top che phía sau.

### Progress mod loader kết thúc đúng trạng thái

- Sau khi tạo instance có Fabric/Forge, thay loader, repair loader hoặc khôi phục Forge trước đó, thanh progress chuyển sang `100%` và badge `READY`.
- Các progress event mod loader đến muộn từ worker thread không còn ghi đè trạng thái hoàn tất.
- Khi thao tác loader thất bại, progress giữ trạng thái lỗi ngắn gọn; chi tiết kỹ thuật vẫn nằm trong Logs.

### Dialog tương thích nhiều cấu hình Windows hơn

- Chữ trong `QMessageBox` dùng màu xám trung tính `#767676`, có độ tương phản đọc được trên cả nền trắng và nền đen.
- Palette được áp trực tiếp cho label, detailed text và button do Windows tạo, thay vì chỉ dựa vào style kế thừa.
- Vẫn giữ Fusion style và nền dialog riêng làm lớp bảo vệ chính.

### Trang Cài mod độc lập

- Thêm mục **Mods** vào sidebar.
- Có thể tìm mod Modrinth theo Fabric/Forge, sắp xếp kết quả và chọn Release/Beta/Alpha.
- Danh sách version hiển thị rõ các phiên bản Minecraft được hỗ trợ.
- Nhấn **Chọn instance và cài đặt** sẽ mở danh sách chỉ gồm instance khớp đồng thời:
  - Minecraft version của file mod;
  - Fabric hoặc Forge đã chọn.
- Instance đang chạy được đánh dấu và không thể cài cho tới khi Minecraft được đóng.
- Luồng Browse Modrinth trong Manage Mods vẫn được giữ để thao tác nhanh trên instance hiện tại.

### Tạo instance ngay trong hộp chọn instance

- Hộp thoại chọn instance tương thích có thêm nút **Tạo instance mới**.
- Chỉ các phiên bản Minecraft mà file mod đang chọn hỗ trợ mới xuất hiện trong hộp tạo.
- Loader được khóa theo mod đang cài để tránh tạo nhầm Fabric/Forge.
- Tên instance được gợi ý tự động và xử lý trùng tên bằng quy tắc hiện có của launcher.
- Sau khi loader của instance mới chuẩn bị xong, launcher tự tiếp tục cài đúng mod đã chọn.

### Checkbox phản hồi ngay trước khi tải lại dữ liệu

- Checkbox Release/Beta/Alpha trong trang Mods, Modrinth browser và CurseForge browser đổi hình trước khi bắt đầu lọc hoặc tải file mới.
- Checkbox hiển thị snapshot trong trang Instances cũng cập nhật trực quan trước khi dựng lại danh sách version.
- Theme preview sau khi bật/tắt chữ trên nút được hoãn một nhịp giao diện, tránh cảm giác click không nhận và nhấn hai lần.

### Cảnh báo cài đặt chưa lưu

- Instance Settings và Launcher Settings theo dõi trạng thái thay đổi so với dữ liệu đã lưu.
- Khi có thay đổi:
  - nút Save được làm nổi bật và có dấu trạng thái;
  - mục tương ứng trên sidebar được làm nổi bật;
  - banner nhắc lưu xuất hiện trong trang.
- Khi rời trang, đổi instance, launch game hoặc đóng launcher, hộp thoại cho phép **Save**, **Discard** hoặc **Cancel**.
- Nếu lưu thất bại, launcher giữ nguyên trạng thái chưa lưu và không tiếp tục thao tác có thể làm mất dữ liệu.
- Các cập nhật cài đặt từ tác vụ nền không ghi đè phần người dùng đang chỉnh sửa.

### Màn hình khởi động

- Thêm splash screen xuất hiện trước cửa sổ chính để người dùng biết launcher vẫn đang khởi tạo.
- Hiển thị tiến trình khi chuẩn bị thư mục, settings, hệ thống tải, database tài khoản, bảo mật và giao diện.
- Splash dùng ngôn ngữ đã lưu ngay khi launcher settings được đọc xong.
- Khi startup thất bại, splash chuyển sang trạng thái lỗi và launcher lưu `logs/startup-error.log` hoặc bản dự phòng trong thư mục tạm.
- Cửa sổ chính chỉ được đưa lên trước sau khi giao diện đã dựng xong; splash có thời gian hiển thị tối thiểu ngắn để tránh nhấp nháy.

### Kiểm thử

```text
749 passed
44 skipped
0 failed
0 errors
```

Các test GUI cần PySide6 bị skip trong môi trường regression hiện tại; toàn bộ test core và kiểm tra compile đều thành công.

### Phiên bản

```python
VERSION = "v0.6.0 RC 1"
VERSION_ID = "0.6.0-rc.1"
UPDATE_CHANNEL = "beta"
```

---

## English

### Fixed create-instance-then-install flow

- Mod installation no longer starts while the instance creation task still owns the blocking task state.
- Added a `task_settled` signal so the selected mod is installed only after loader task cleanup has completed.
- The created instance name and actual loader are verified before continuing.
- Duplicate Fabric/Forge version-list requests are ignored silently instead of showing `Task ... is already running`.
- If the follow-up install cannot start, the launcher clearly reports that the instance exists but the mod was not installed.

### Fixed startup splash stalls

- I/O-heavy bootstrap steps now run outside the Qt GUI thread, keeping the splash responsive while account data or security checks are busy.
- Startup now has a 45-second timeout and reports the exact stage where it stopped.
- `startup-error.log` includes the startup stage and preserves worker-thread tracebacks.
- The startup error dialog is parented to the splash so the always-on-top splash cannot hide it.

### Terminal mod-loader progress

- Creating a Fabric/Forge instance, changing a loader, repairing it, or restoring the previous Forge installation now ends at `100%` with a `READY` badge.
- Late worker-thread loader events can no longer overwrite the terminal success state.
- Failed loader operations keep a compact error state while technical details remain in Logs.

### More resilient dialogs

- `QMessageBox` text now uses neutral gray `#767676`, remaining readable when a broken Windows theme produces either a white or black background.
- The palette is applied directly to native-created labels, detailed text widgets, and buttons.
- Fusion style and the explicit dialog background remain the primary compatibility layer.

### Standalone Install Mods page

- Added a **Mods** sidebar page.
- Browse Modrinth mods by Fabric/Forge, sorting mode, and Release/Beta/Alpha channel.
- Version choices show their supported Minecraft versions.
- **Choose instance and install** lists only instances matching both the selected Minecraft version and loader.
- Running instances are marked and cannot be modified until Minecraft is closed.
- The existing Manage Mods browser remains available for quick instance-specific installation.

### Create an instance from the compatibility chooser

- The compatible-instance dialog now includes a **Create new instance** action.
- Only Minecraft versions supported by the selected mod file are offered.
- The loader is fixed to the selected mod's loader, preventing accidental Fabric/Forge mismatches.
- Instance names are suggested automatically and use the launcher's existing duplicate-name policy.
- Once the new instance and its loader are ready, installation of the originally selected mod resumes automatically.

### Immediate checkbox feedback

- Release/Beta/Alpha checkboxes on the Mods page and in the Modrinth and CurseForge browsers paint their new state before filtering or loading new data.
- The snapshot checkbox on the Instances page also updates visually before rebuilding the version list.
- Button-text theme preview is deferred by one UI turn so the toggle visibly responds before the theme reload begins.

### Unsaved-settings protection

- Instance Settings and Launcher Settings now track changes against their last saved state.
- While changes are pending:
  - the Save button is highlighted and marked;
  - the matching sidebar entry is highlighted;
  - an unsaved-changes banner is shown on the page.
- Leaving the page, switching instances, launching Minecraft, or closing the launcher prompts for **Save**, **Discard**, or **Cancel**.
- A failed save keeps the page dirty and blocks the destructive navigation action.
- Background settings updates no longer overwrite a form the user is actively editing.

### Startup screen

- Added a splash screen before the main window so users can see that the launcher is still initializing.
- Reports progress while preparing folders, settings, downloads, the account database, security migration, and the interface.
- The splash switches to the saved launcher language as soon as settings are available.
- Startup failures change the splash to an error state and write `logs/startup-error.log`, with a temporary-directory fallback.
- The main window is raised only after construction completes, while a short minimum splash duration prevents distracting flicker.

### Regression

```text
749 passed
44 skipped
0 failed
0 errors
```

GUI tests requiring PySide6 were skipped in the current regression environment; all core tests and compile checks succeeded.

### Release metadata

```python
VERSION = "v0.6.0 RC 1"
VERSION_ID = "0.6.0-rc.1"
UPDATE_CHANNEL = "beta"
```

This release remains a GitHub prerelease and is intended for the tester channel before `v0.6.0` Stable.
