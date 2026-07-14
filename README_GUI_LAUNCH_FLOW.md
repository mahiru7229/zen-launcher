# MCW Launcher — GUI launch flow patch

Patch này chỉ nâng lớp trình bày GUI, không thay đổi contract của Minecraft Core.

## Thành phần

- `ProgressPresenter`: chuyển `ProgressEvent` thành dữ liệu hiển thị.
- `LaunchErrorPresenter`: chuyển exception thành dialog thân thiện nhưng vẫn giữ technical detail.
- `LaunchControlWidget`: hiển thị stage, progress byte/file, trạng thái Java và trạng thái launch.
- `ProgressStage`: bổ sung `DOWNLOADING_JAVA` và `INSTALLING_JAVA`.
- `MainWindow`: đưa lỗi launch vào launch bar mà không phá signal/controller hiện tại.

## Áp dụng

Chép các thư mục `src` và `test` đè vào thư mục gốc repository.

PowerShell:

```powershell
Copy-Item ".\src\*" "D:\LAUNCHER\zen-launcher\src" -Recurse -Force
Copy-Item ".\test\*" "D:\LAUNCHER\zen-launcher\test" -Recurse -Force
```

## Test

```powershell
python -m pytest test/gui/presenters -q
python -m pytest -q
python launcher.py
```

## Manual checklist

1. Xóa `runtimes/java-8`, chọn instance Minecraft cần Java 8 và launch.
2. Launch bar phải hiện `JAVA CHECK`, `JAVA DOWNLOAD`, `JAVA INSTALL`.
3. Download phải hiển thị MiB và phần trăm.
4. Khi cài đặt, progress bar chạy indeterminate.
5. Khi game mở, badge chuyển sang `RUNNING`.
6. Ngắt mạng để xác nhận dialog `Network error`.
7. Lần launch tiếp theo phải bỏ qua download Java nếu runtime đã tồn tại.
