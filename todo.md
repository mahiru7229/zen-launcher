# Zen Launcher v0.3.0-alpha

## Giới thiệu

Zen Launcher là một Minecraft Launcher đang trong giai đoạn phát triển, được thiết kế theo hướng:

- Quản lý nhiều Instance
- Đơn giản
- Hiện đại
- Dễ mở rộng
- Tập trung vào trải nghiệm người dùng

Hiện tại launcher đã có backend khá hoàn chỉnh, vì vậy có thể bắt đầu thiết kế giao diện.

---

# Những tính năng đã hoàn thành

## 1. Instance System

Đây là trung tâm của launcher.

Mỗi Instance là một môi trường Minecraft độc lập.

Hiện tại hỗ trợ:

- Tạo Instance
- Đổi tên Instance
- Xóa Instance
- Clone Instance
- Export Instance
- Import Instance
- Chỉnh sửa thông tin Instance

---

## 2. Package System

Launcher sử dụng định dạng package riêng:

```
.mcwpack
```

Package hỗ trợ:

- Export Instance
- Import Instance
- Metadata riêng
- Có thể lựa chọn:
  - Bao gồm Save
  - Không bao gồm Save

---

## 3. Settings

Mỗi Instance có Settings riêng.

Ví dụ:

- Java Path
- RAM tối thiểu
- RAM tối đa
- Java Arguments
- Game Arguments
- Độ phân giải
- Fullscreen

---

## 4. Account System

Đã hoàn thành Offline Account.

Hiện tại hỗ trợ:

- Tạo Offline Account
- Xóa Account
- Danh sách Account
- Chọn Account mặc định
- Luôn đảm bảo có Selected Account hợp lệ

Trong tương lai sẽ hỗ trợ:

- Microsoft Account

---

## 5. Launch System

Launcher đã có thể:

- Chọn Java
- Chuẩn bị Launch Context
- Khởi chạy Minecraft
- Đọc Settings của từng Instance
- Đọc Account đang được chọn

---

## 6. Download System

Đã hỗ trợ:

- Download Version
- Download Libraries
- Download Assets
- Download Client

Đã tối ưu tốc độ download.

---

# Những gì chưa có

Hiện tại chưa có GUI.

Mọi thao tác vẫn thực hiện bằng code.

Đây là lý do bắt đầu thiết kế giao diện.

---

# Định hướng UI

Launcher hướng tới:

- Modern
- Minimal
- Pixel Art
- Dễ sử dụng

Không hướng tới giao diện quá nhiều nút.

---

# Điều quan trọng

Launcher lấy **Instance** làm trung tâm.

Không phải Version.

Luồng sử dụng mong muốn:

```
Mở Launcher

↓

Chọn Instance

↓

Launch
```

---

# Những màn hình dự kiến

## Trang chủ

Hiển thị danh sách Instance.

Mỗi Instance có:

- Tên
- Phiên bản Minecraft
- Mod Loader
- Nút Launch

---

## Chi tiết Instance

Cho phép chỉnh:

- Tên
- Java
- RAM
- Resolution
- Fullscreen
- Launch Arguments

---

## Account

Danh sách Account.

Có thể:

- Thêm Account
- Chọn Account
- Xóa Account

Trong tương lai sẽ thêm Microsoft Login.

---

## Settings

Cài đặt chung của Launcher.

---

## Package

Import / Export Package.

---

## Download

Hiển thị tiến trình download.

---

## Log

Hiển thị log launcher.

---

# Phong cách thiết kế

Launcher hướng tới phong cách:

- Pixel Art
- Màu tối
- Card UI
- Icon Pixel
- Animation nhẹ

Ví dụ:

- Mascot Pixel
- Animation đào đá khi Download
- Animation chạy khi Launch
- Animation thành công / thất bại

---

# Điều mong muốn

Không cần thiết kế giống:

- PCL2
- HMCL
- Prism Launcher

Có thể sáng tạo theo phong cách riêng.

Launcher mong muốn có bản sắc riêng và dễ nhận diện.

---

# Mục tiêu

Thiết kế một launcher:

- Hiện đại
- Gọn gàng
- Dễ sử dụng
- Có cảm giác "vui" khi sử dụng nhờ Pixel Art
- Đủ chuyên nghiệp để sử dụng hằng ngày