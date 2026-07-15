# MCW Launcher themes

Mỗi theme nằm trong `themes/<theme-id>/` và phải có `theme.json`.

- Mọi PNG đều tùy chọn.
- Thiếu hoặc hỏng một file chỉ làm thành phần đó fallback về CSS mặc định.
- Launcher không dừng khởi động vì theme không hoàn chỉnh.
- Có thể reload/preview theme trong **Launcher Settings → Appearance**.
- Xem danh sách tên file, đường dẫn và canvas tại [`docs/THEME_ASSET_GUIDE.md`](../docs/THEME_ASSET_GUIDE.md).

Theme `mcw-default` khai báo sẵn toàn bộ key, nhưng không bắt buộc phải chứa toàn bộ PNG. Họa sĩ có thể thêm dần từng file theo đúng đường dẫn trong manifest.

Theme `mcw-legacy-assets` giữ tương thích với logo và nút Launch PNG cũ trong `themes/Default Theme/`.
