# MCW Launcher — Instance Run Lock

## Mục tiêu

Ngăn cùng một instance Minecraft được chạy lần thứ hai khi instance đó đang chuẩn bị khởi động hoặc vẫn còn tiến trình game hoạt động.

## Cách hoạt động

- Lock được lấy ngay đầu `MinecraftExecutor.run()` để chặn cả double-click và hai request đồng thời.
- Mỗi lock lưu PID launcher khi đang chuẩn bị và PID Minecraft sau khi `JavaRuntime.run()` thành công.
- Một thread daemon chờ Minecraft thoát rồi tự động nhả lock.
- Nếu launcher bị crash, lock cũ được nhận diện bằng PID và tự dọn ở lần chạy tiếp theo.
- Lock được lưu tại `instances/.runtime/locks`, không nằm trong folder game nên không bị clone/export cùng instance.
- Token ownership ngăn một watcher cũ xóa nhầm lock của lần chạy mới.
- Hai instance khác nhau vẫn có thể chạy đồng thời ở tầng core.

## File thay đổi

- `src/core/fs/paths.py`
- `src/core/instance/errors.py` (mới)
- `src/core/instance/instance_run_lock.py` (mới)
- `src/core/minecraft/minecraft_executor.py`
- `src/gui/presenters/launch_error_presenter.py`
- `test/core/instance/test_instance_run_lock.py` (mới)
- `test/core/minecraft/test_minecraft_executor.py`
- `test/gui/presenters/test_launch_error_presenter.py`

## Kiểm thử

- `429 passed`
- `3 xfailed` (các test đã được đánh dấu xfail từ trước)
- Đã test thêm bằng tiến trình subprocess thật: lần chạy thứ hai bị chặn và lock tự biến mất khi tiến trình kết thúc.

## Commit đề xuất

```bash
git add src/core/fs/paths.py src/core/instance/errors.py src/core/instance/instance_run_lock.py src/core/minecraft/minecraft_executor.py src/gui/presenters/launch_error_presenter.py test/core/instance/test_instance_run_lock.py test/core/minecraft/test_minecraft_executor.py test/gui/presenters/test_launch_error_presenter.py

git commit -m "feat: prevent duplicate instance launches"
```
