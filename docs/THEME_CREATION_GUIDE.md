# Hướng dẫn tạo theme cho MCW Launcher

Tài liệu này hướng dẫn tạo một theme PNG ngoài EXE cho MCW Launcher Beta 10.

## 1. Tạo thư mục theme

```text
themes/
└── my-theme/
    └── theme.json
```

`my-theme` là ID thư mục. Nên dùng chữ thường, số và dấu gạch ngang.

## 2. Tạo manifest

```json
{
  "schema_version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "author": "Artist name",
  "description": "A custom MCW Launcher theme.",
  "assets": {}
}
```

Các field `id`, `name`, `author` chỉ là metadata hiển thị. `assets` ánh xạ key launcher tới đường dẫn PNG tương đối bên trong theme.

## 3. Bắt đầu từ một asset nhỏ

Theme không cần đủ toàn bộ file. Ví dụ chỉ thay background và logo:

```text
themes/my-theme/
├── theme.json
├── backgrounds/
│   └── window.png
└── logos/
    └── main.png
```

```json
{
  "schema_version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "author": "Artist name",
  "assets": {
    "background.window": "backgrounds/window.png",
    "logo.main": "logos/main.png"
  }
}
```

Mọi widget khác tiếp tục dùng CSS mặc định.

## 4. Asset cho Beta 9

Các màn hình mới có asset riêng:

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

Khai báo:

```json
{
  "assets": {
    "surface.microsoft_card": "surfaces/cards/microsoft.png",
    "surface.java_card": "surfaces/cards/java.png",
    "surface.lifecycle_card": "surfaces/cards/lifecycle.png",
    "badge.locked": "surfaces/badges/locked.png",
    "icon.action.microsoft": "icons/actions/microsoft.png",
    "icon.action.java": "icons/actions/java.png",
    "icon.action.backup": "icons/actions/backup.png",
    "icon.action.restore": "icons/actions/restore.png"
  }
}
```

Canvas chính xác được liệt kê trong [`THEME_ASSET_GUIDE.md`](THEME_ASSET_GUIDE.md).

## 5. Asset bảo mật Beta 10

```text
surfaces/cards/security.png       480 × 260
icons/actions/shield.png          24 × 24
icons/actions/reprotect.png       24 × 24
```

Khai báo:

```json
{
  "assets": {
    "surface.security_card": "surfaces/cards/security.png",
    "icon.action.shield": "icons/actions/shield.png",
    "icon.action.reprotect": "icons/actions/reprotect.png"
  }
}
```

Card security chứa nội dung động như số account protected/legacy/invalid, vì vậy không nên vẽ sẵn các con số hoặc trạng thái vào PNG.

## 6. PNG có chữ sẵn

Chỉ dùng cho chữ cố định. Ví dụ nút Launch đã vẽ chữ `LAUNCH`:

```json
{
  "assets": {
    "button.launch": "controls/buttons/launch/default.png"
  },
  "text_assets": {
    "control.launch": "button.launch"
  }
}
```

Người dùng có thể tắt **Show static text over themed controls**. Launcher chỉ ẩn chữ khi PNG hợp lệ đã được load; thiếu ảnh thì chữ tự quay lại.

Không vẽ sẵn nội dung thay đổi theo thời gian như username, tên instance, version, trạng thái tải hoặc error message.

## 7. Trạng thái button

Một nút nên có đủ state khi có thể:

```text
controls/buttons/launch/
├── default.png
├── hover.png
├── pressed.png
└── disabled.png
```

Các state thiếu sẽ fallback về style mặc định hoặc state gần nhất do stylesheet xử lý.

## 8. Background và vùng an toàn

- `background.window`: 1600 × 900.
- Sidebar: 220 × 900.
- Right panel: 400 × 900.
- Center/page: 980 px chiều rộng.
- Không đặt chữ quan trọng sát mép vì cửa sổ có thể scale hoặc resize.
- Kiểm tra theme trên 1366 × 768 và 1600 × 900.

## 9. Kiểm tra theme

1. Đặt folder cạnh source hoặc cạnh EXE:

```text
MCW Launcher.exe
themes/
└── my-theme/
```

2. Mở **Launcher Settings → Appearance**.
3. Chọn theme.
4. Nhấn **Reload and preview theme**.
5. Kiểm tra Accounts, Instances, Launcher Settings, Mod Manager, Modrinth Browser và các dialog.

Nếu theme không xuất hiện:

- kiểm tra `theme.json` là JSON hợp lệ;
- kiểm tra `id` không rỗng;
- kiểm tra path dùng `/` hoặc path tương đối hợp lệ;
- kiểm tra file thật sự là PNG;
- không dùng `..`, drive letter hoặc path tuyệt đối.

## 10. Fallback và theme chưa hoàn chỉnh

Theme có thể được phát hành khi mới có vài PNG. Launcher không crash vì:

- file thiếu;
- PNG hỏng;
- canvas khác khuyến nghị;
- key lạ;
- asset không đọc được.

Asset lỗi bị bỏ qua riêng lẻ. Tuy vậy, nên test console/log để phát hiện typo trong manifest.

## 11. Đóng gói cùng release

Công cụ release tự copy toàn bộ `themes/`:

```powershell
python tools/build_release_zip.py --exe ".\dist\MCW Launcher.exe" --version "0.5.0-beta.10"
```

Người dùng cũng có thể thêm theme mới vào folder `themes/` mà không cần rebuild EXE.

## Checklist cho theme author

```text
[ ] theme.json hợp lệ
[ ] ID theme duy nhất
[ ] Không có path tuyệt đối hoặc ..
[ ] PNG có alpha đúng
[ ] Background được test ở nhiều độ phân giải
[ ] Button có hover/pressed khi cần
[ ] PNG có chữ được khai báo trong text_assets
[ ] Nội dung động không bị vẽ cứng vào PNG
[ ] Thiếu asset vẫn fallback dễ đọc
[ ] Theme xuất hiện sau Reload and preview theme
```
