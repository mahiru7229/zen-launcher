# MCW Launcher v0.6.0-beta.5 — Memory slider and numeric input setting

## Tiếng Việt

Bản vá này thay đổi phần cấp phát RAM Java trong **Instance Settings → Java and memory**.

### Thay đổi

- Mỗi mức RAM có cả **thanh trượt** và **ô nhập số MB**; có thể kéo nhanh hoặc nhập chính xác.
- Thanh trượt dùng bước 256 MB; ô nhập cho phép đặt chính xác từng MB và giá trị vẫn được hiển thị đồng thời theo GB/MB.
- Giới hạn trên của RAM tối thiểu luôn bằng RAM tối đa đang chọn.
- Khi hạ RAM tối đa xuống dưới RAM tối thiểu, RAM tối thiểu tự động hạ theo.
- RAM tối đa không thể vượt quá RAM vật lý được hệ điều hành báo cáo.
- Launcher kiểm tra giới hạn ở cả GUI, controller và `SettingsManager`.
- Cấu hình cũ vượt RAM vật lý được clamp an toàn khi load hoặc save.
- Không thay đổi schema `settings.json`; các trường `min_memory` và `max_memory` vẫn giữ nguyên.
- Bổ sung giao diện thanh trượt, ô nhập số đồng bộ và bản dịch tiếng Việt/Anh.

### Fallback

Nếu launcher không thể đọc RAM vật lý, giới hạn an toàn tạm thời là 4096 MB. Thông báo trong giao diện sẽ nói rõ launcher đang dùng fallback thay vì giả định đó là RAM thật.

### Kiểm thử

```text
737 passed
33 skipped
0 failed
0 errors
```

Các test bị skip là nhóm GUI phụ thuộc PySide6, không có trong môi trường regression hiện tại. Test lõi cho phát hiện RAM, clamp, validation, lưu/load settings và language pack đều đã chạy thành công.

---

## English

This patch changes Java RAM allocation under **Instance Settings → Java and memory**.

### Changes

- Each RAM value now has both a **slider** and an editable **MB numeric field**, allowing quick dragging or exact entry.
- Sliders use 256 MB steps; numeric fields accept exact MB values and the selected amount remains visible in both GB and MB.
- The minimum-memory slider's upper bound always follows the selected maximum memory.
- Lowering maximum memory below minimum memory automatically lowers the minimum.
- Maximum Java memory cannot exceed physical RAM reported by the operating system.
- The limit is enforced by the GUI, controller, and `SettingsManager`.
- Existing configurations above physical RAM are safely clamped during load or save.
- The `settings.json` schema remains compatible; `min_memory` and `max_memory` are unchanged.
- Adds synchronized slider/numeric input UI and complete Vietnamese/English translations.

### Fallback

When physical RAM cannot be detected, the launcher uses a temporary safe limit of 4096 MB. The UI explicitly identifies this as a fallback rather than reporting it as detected RAM.

### Regression

```text
737 passed
33 skipped
0 failed
0 errors
```

Skipped tests are GUI tests that require PySide6, which was unavailable in the regression environment. Core tests for RAM detection, clamping, validation, settings persistence, and language packs passed.
