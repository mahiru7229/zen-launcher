# MCW Launcher v0.6.0 RC 2

> RC2 is a focused stability update for the dedicated Mods installation flow and startup reliability fixes introduced after RC1.

---

## Tiếng Việt

### Sửa lỗi cài mod

- Sửa thông báo giả **“Select an instance first.”** xuất hiện sau khi cài mod thành công.
- Khi chọn hoặc tạo instance từ trang Mods, launcher gắn instance đó làm target của Mod Manager trước khi bắt đầu cài đặt.
- Việc quét thư mục mod ban đầu được trì hoãn cho đến khi task cài mod hoàn tất, tránh quét trạng thái chưa hoàn chỉnh.
- Sau khi cài xong, Mod Manager refresh đúng instance và hiển thị mod vừa cài.
- Giữ lại bản sửa race condition của RC1: launcher chỉ cài mod sau khi task tạo instance và loader đã được giải phóng hoàn toàn.

### Startup

- Giữ startup worker, timeout và báo lỗi theo stage từ bản sửa RC1.
- Splash screen không còn che dialog lỗi startup.
- Chi tiết lỗi tiếp tục được lưu tại `logs/startup-error.log`.

### Phiên bản

```text
VERSION = v0.6.0 RC 2
VERSION_ID = 0.6.0-rc.2
UPDATE_CHANNEL = beta
```

---

## English

### Mod installation fixes

- Fixed the false **“Select an instance first.”** message shown after a successful mod installation.
- When an instance is selected or created from the Mods page, it is assigned as the Mod Manager target before installation starts.
- The initial mod-folder scan is deferred until installation completes, avoiding scans of an incomplete state.
- After installation, Mod Manager refreshes the correct instance and displays the newly installed mod.
- Retains the RC1 race-condition fix: installation starts only after instance creation and loader preparation have fully settled.

### Startup

- Retains the startup worker, stage timeout and detailed error reporting introduced after RC1.
- The splash screen no longer hides startup error dialogs.
- Full details continue to be written to `logs/startup-error.log`.

### Version

```text
VERSION = v0.6.0 RC 2
VERSION_ID = 0.6.0-rc.2
UPDATE_CHANNEL = beta
```
