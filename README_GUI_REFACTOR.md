# MCW Launcher GUI Refactor

Bộ file này thay thế GUI thử nghiệm bằng cấu trúc PySide6 tách trách nhiệm rõ ràng.

## Cách áp dụng

1. Sao lưu branch hiện tại.
2. Chép `launcher.py` và thư mục `src/gui/` trong gói này vào root repo, cho phép ghi đè file cũ.
3. Cài PySide6 nếu môi trường chưa có:

```bash
pip install PySide6
```

4. Chạy:

```bash
python launcher.py
```

## Kiến trúc

- `main_window_2.py`: lắp ráp shell, route signal, không gọi Core trực tiếp.
- `controllers/`: validate dữ liệu và gọi Public Core API.
- `pages/`: hiển thị từng màn hình và phát intent signal.
- `widget/`: component tái sử dụng.
- `task_runner.py`: quản lý toàn bộ vòng đời `QThread`.
- `style.py`: stylesheet tập trung.
- `config.py`: tên launcher, kích thước và resource path.

## Các màn hình đã có

- Home
- Accounts
- Instances
- Instance Settings
- Launcher Settings
- Logs
- About

## Core được nối

- Version manifest
- Offline account CRUD/select
- Instance CRUD/import/export
- Instance settings load/save
- Minecraft launch + structured progress

Microsoft authentication vẫn hiển thị là tính năng đang phát triển vì Core hiện tại chưa hoàn tất luồng đó.

## Áp dụng nhanh trên Windows

Mở PowerShell trong thư mục đã giải nén và chạy:

```powershell
.\apply_gui_refactor.ps1 -RepoPath "D:\path\to\mcw-launcher"
```

Nên tạo branch mới trước khi ghi đè GUI:

```bash
git switch -c feat/gui-srp-refactor
```
