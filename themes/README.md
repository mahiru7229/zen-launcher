# MCW Launcher themes

Mỗi theme nằm trong `themes/<theme-id>/` và có một `theme.json`.

- Mọi PNG đều tùy chọn.
- Thiếu hoặc hỏng một file chỉ làm đúng thành phần đó fallback về CSS mặc định.
- Launcher không dừng khởi động vì theme chưa hoàn chỉnh.
- Có thể reload/preview trong **Launcher Settings → Appearance**.
- Theme ngoài EXE có thể được thêm hoặc cập nhật mà không cần build lại launcher.

Tài liệu:

- [`docs/THEME_CREATION_GUIDE.md`](../docs/THEME_CREATION_GUIDE.md) — hướng dẫn tạo theme từng bước.
- [`docs/THEME_ASSET_GUIDE.md`](../docs/THEME_ASSET_GUIDE.md) — toàn bộ key, đường dẫn và canvas PNG.

## Asset mới của Beta 9

```text
surfaces/cards/microsoft.png
surfaces/cards/java.png
surfaces/cards/lifecycle.png
surfaces/badges/locked.png
icons/actions/microsoft.png
icons/actions/java.png
icons/actions/backup.png
icons/actions/restore.png
```

Các asset này tương ứng với card Microsoft approval, Java diagnostics, Backup/Modpack lifecycle và các nút hành động mới.

## PNG đã chứa chữ

Khi một PNG đã vẽ sẵn nội dung cố định, khai báo role tương ứng:

```json
{
  "text_assets": {
    "control.launch": "button.launch"
  }
}
```

Người dùng có thể tắt **Show static text over themed controls**. Launcher chỉ ẩn chữ khi asset được khai báo tồn tại và là PNG hợp lệ; thiếu hoặc lỗi file thì chữ fallback vẫn xuất hiện.

Không nên vẽ cứng nội dung động như tên instance, username, version, progress hoặc error message lên PNG.
