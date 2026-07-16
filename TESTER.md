# MCW Launcher v0.5.1 RC 1 — Tester Checklist

> Mục tiêu của RC1: xác nhận launcher đủ ổn định để phát hành `v0.5.1` Stable.  
> Tester nên dùng bản build ZIP chính thức, không chạy từ source và không chạy EXE trực tiếp bên trong ZIP.

---

## 1. Thông tin môi trường

Tester ghi lại trước khi bắt đầu:

- Windows: 10 hoặc 11
- CPU:
- RAM:
- Ổ cài launcher: HDD / SSD
- Đường dẫn launcher:
- Có antivirus bên thứ ba hay không:
- Java đã cài sẵn:
- Tài khoản dùng để test: Offline / Microsoft
- Instance hoặc modpack được dùng:
- Tốc độ mạng ước tính:

---

# A. Test bắt buộc — P0

Nếu bất kỳ mục P0 nào thất bại, chưa nên phát hành Stable.

## A1. Cài đặt và khởi động

- [ ] Tải ZIP từ GitHub Release.
- [ ] Giải nén toàn bộ ZIP vào thư mục mới.
- [ ] Có đủ:
  - [ ] `MCW Launcher.exe`
  - [ ] `mcw-update.json`
  - [ ] `lang/`
  - [ ] `themes/`
  - [ ] `docs/`
  - [ ] `README.md`
  - [ ] `LICENSE`
- [ ] Launcher mở được.
- [ ] Không có cửa sổ CMD bật lên.
- [ ] Không crash ngay khi mở.
- [ ] Theme mặc định tải đúng.
- [ ] Ngôn ngữ tải đúng.
- [ ] Đóng launcher và mở lại bình thường.

## A2. Update channel migration

Dùng settings từ bản Beta cũ trước khi mở RC1.

- [ ] Người đang ở Beta được chuyển sang Stable trong lần mở đầu tiên.
- [ ] Người đang ở Stable vẫn giữ Stable.
- [ ] Channel lỗi hoặc thiếu được sửa thành Stable.
- [ ] Đóng và mở lại launcher không chạy migration lần hai.
- [ ] Sau migration, tự chọn Beta trong Settings.
- [ ] Đóng và mở lại launcher: Beta vẫn được giữ.
- [ ] Reset Settings: channel trở về Stable.

## A3. Offline account

- [ ] Tạo tài khoản Offline.
- [ ] Username hợp lệ được lưu.
- [ ] Chọn tài khoản Offline.
- [ ] Đóng/mở launcher: tài khoản vẫn còn.
- [ ] Launch Minecraft bằng tài khoản Offline.
- [ ] Xóa tài khoản Offline.
- [ ] Launcher tự chọn tài khoản khác nếu còn.

## A4. Microsoft account

- [ ] Đăng nhập Microsoft thành công.
- [ ] Đóng cửa sổ đăng nhập giữa chừng không làm launcher treo.
- [ ] Thêm nhiều tài khoản Microsoft.
- [ ] Mỗi tài khoản hiển thị đúng username.
- [ ] Đóng/mở launcher: tài khoản vẫn còn.
- [ ] Token được refresh khi cần.
- [ ] Launch server premium không báo invalid session.
- [ ] Xóa một tài khoản không làm hỏng database.
- [ ] Không xuất hiện lỗi `database is locked`.

## A5. Vanilla launch

Test ít nhất:

- [ ] Một phiên bản mới dùng Java 17/21.
- [ ] Một phiên bản cũ dùng Java 8.
- [ ] Một instance đã tải đủ file.
- [ ] Một instance chưa có client/libraries/assets.

Kiểm tra:

- [ ] Launcher chọn đúng Java.
- [ ] Client được tải và hiện progress.
- [ ] Libraries được tải và hiện progress.
- [ ] Assets được tải và hiện progress.
- [ ] Tốc độ mạng chỉ hiện khi đang tải.
- [ ] Số file hoặc dung lượng còn lại đúng hướng.
- [ ] Minecraft mở thành công.
- [ ] Launcher không block UI.
- [ ] Launch lần hai không tải lại file đã hợp lệ.
- [ ] Không có CMD popup.

## A6. Modrinth mod

- [ ] Thêm một mod tương thích.
- [ ] Launch instance.
- [ ] Launcher check toàn bộ trước khi tải.
- [ ] Sau check mới bắt đầu tải.
- [ ] Mod tải thành công.
- [ ] Launch lại: mod chỉ được check, không tải lại.
- [ ] Xóa file mod thủ công rồi Launch lại.
- [ ] Launcher phát hiện thiếu và tải lại.
- [ ] File sai hash bị từ chối và tải lại.
- [ ] Dependency bắt buộc được xử lý đúng.

## A7. Modrinth modpack

- [ ] Add modpack không tải toàn bộ mod ngay.
- [ ] Nhấn Launch mới bắt đầu check và tải.
- [ ] Progress hiển thị số file còn lại.
- [ ] File đúng hash được bỏ qua.
- [ ] File lỗi được retry theo tối đa 3 vòng.
- [ ] Sau mỗi vòng tải có bước check lại.
- [ ] Nếu vẫn thiếu sau 3 vòng, launcher báo lỗi ngay.
- [ ] Thông báo chỉ rõ nơi tắt tùy chọn chặn Launch.
- [ ] Tắt `Stop launch when required Modrinth files are missing`.
- [ ] Launch lại: launcher vẫn retry đủ 3 vòng.
- [ ] Nếu vẫn lỗi, Minecraft được phép tiếp tục Launch.
- [ ] Log ghi đúng đường dẫn file cần tải thủ công.
- [ ] Lần Launch sau vẫn thử tải lại file còn thiếu.

## A8. Pause và Resume

Thực hiện với một file đủ lớn để kịp thao tác.

- [ ] Trong lúc tải, nút Launch chuyển thành Cancel.
- [ ] Nhấn Cancel làm tác vụ dừng.
- [ ] Launcher không hiển thị lỗi download.
- [ ] File `.part` vẫn còn.
- [ ] Nút trở lại Launch.
- [ ] Nhấn Launch lại.
- [ ] Download tiếp tục từ `.part`.
- [ ] Progress không quay về trạng thái sai.
- [ ] File hoàn tất đúng hash.
- [ ] Minecraft Launch thành công sau resume.

Lặp lại với:

- [ ] Minecraft client.
- [ ] Libraries/assets.
- [ ] Java runtime.
- [ ] Modrinth mod/modpack.

## A9. Giới hạn tốc độ

- [ ] Đặt giới hạn `1 MB/s`.
- [ ] Tải một file lớn.
- [ ] Tốc độ thực tế không vượt giới hạn quá xa trong thời gian dài.
- [ ] Tải nhiều file song song.
- [ ] Tổng tốc độ được giới hạn, không phải mỗi file một giới hạn riêng.
- [ ] Đặt `0 MB/s`.
- [ ] Download trở lại không giới hạn.
- [ ] Tắt tùy chọn và mở lại launcher: cấu hình được lưu đúng.

## A10. Import instance

- [ ] Import một `.mcwpack` hợp lệ.
- [ ] Thanh progress hiển thị file đang xử lý.
- [ ] Hiển thị dung lượng đã xử lý, tổng dung lượng, còn lại và phần trăm.
- [ ] Progress tăng dần, không chỉ nhảy 0% → 100%.
- [ ] Instance import xong xuất hiện trong danh sách.
- [ ] Instance Launch được.
- [ ] Import package không có save.
- [ ] Import package có save.
- [ ] Import package trùng tên tạo tên an toàn.
- [ ] Cancel/đóng launcher giữa import không để lại instance hoàn chỉnh giả.

## A11. Export instance

- [ ] Export không gồm save.
- [ ] Export gồm save.
- [ ] Progress tăng theo dung lượng.
- [ ] File `.part` được dùng trong quá trình export.
- [ ] Khi hoàn tất chỉ còn `.mcwpack` hợp lệ.
- [ ] Package export có thể import lại.
- [ ] Lưu `.mcwpack` bên trong thư mục instance không làm package tự chứa chính nó.
- [ ] Nếu export lỗi, package cũ không bị ghi đè bởi ZIP hỏng.

## A12. Launcher update

- [ ] Check Update hoạt động.
- [ ] Update download hiển thị trên progress.
- [ ] Có tốc độ và dung lượng còn lại khi đang tải.
- [ ] Giới hạn tốc độ áp dụng cho update.
- [ ] ZIP update có `mcw-update.json`.
- [ ] Update không làm mất settings, accounts hoặc instances.
- [ ] Launcher restart đúng sau update.
- [ ] Không để lại update `.part` hỏng làm lần sau thất bại.

---

# B. Test quan trọng — P1

## B1. Theme

- [ ] Theme mặc định hiển thị Launch PNG.
- [ ] Trong lúc tải hiển thị Cancel PNG.
- [ ] Hover, pressed và disabled hoạt động.
- [ ] Theme tùy chỉnh thiếu `cancel.png` dùng fallback mặc định.
- [ ] Theme không có một số asset khác không làm launcher crash.
- [ ] Đổi theme rồi mở lại launcher vẫn đúng.

## B2. Language

- [ ] Chuyển English ↔ Vietnamese.
- [ ] Các thông báo Modrinth mới được dịch.
- [ ] Pause/Resume status được dịch.
- [ ] Import/Export status được dịch.
- [ ] Không hiện key thô như `download.pause.status`.
- [ ] Mở lại launcher vẫn giữ ngôn ngữ.

## B3. Instance settings

- [ ] RAM min/max được lưu.
- [ ] Resolution được lưu.
- [ ] Fullscreen được lưu.
- [ ] Java path tùy chỉnh hoạt động.
- [ ] JVM arguments được lưu.
- [ ] Settings cũ thiếu field mới vẫn load.
- [ ] `settings.json` lỗi được backup thành `.broken`.
- [ ] Launcher tự tạo settings mặc định và vẫn Launch.

## B4. Instance manager

- [ ] Create.
- [ ] Rename.
- [ ] Clone/Duplicate.
- [ ] Delete.
- [ ] Một `instance.json` hỏng không làm mất các instance còn lại.
- [ ] Tên instance dài vẫn được xử lý hợp lý.
- [ ] Tên instance có ký tự Windows không hợp lệ bị từ chối rõ ràng.

## B5. Java

- [ ] Tự tìm Java trong PATH.
- [ ] Tìm Java trong Program Files/Registry nếu có.
- [ ] Chọn đúng major version.
- [ ] Java thiếu được tự tải nếu thuộc major được hỗ trợ.
- [ ] Java download có progress.
- [ ] Java download pause/resume được.
- [ ] Java lỗi hiển thị thông báo dễ hiểu.

## B6. WinError 206

Test với:

- Đường dẫn launcher dài.
- Instance có nhiều libraries.
- Modpack lớn.

Kiểm tra:

- [ ] Launcher không báo `WinError 206`.
- [ ] Classpath manifest JAR được tạo trong `.mcw/launch/`.
- [ ] Minecraft vẫn mở.
- [ ] Nếu đường dẫn thật sự quá dài, thông báo khuyên dùng đường dẫn ngắn như `C:\MCW`.

---

# C. Stress và edge case — P2

## C1. Mạng không ổn định

- [ ] Tắt mạng giữa lúc tải.
- [ ] Bật mạng lại và Launch.
- [ ] Resume hoạt động.
- [ ] Mô phỏng mạng rất chậm.
- [ ] Đổi Wi-Fi giữa lúc tải.
- [ ] VPN bật/tắt giữa lúc tải.
- [ ] Server trả `403`.
- [ ] Server trả `404`.
- [ ] Server trả `416`.
- [ ] Server trả `429`.
- [ ] Server trả lỗi `5xx`.
- [ ] URL đầu lỗi nhưng URL dự phòng hoạt động.

## C2. Thao tác liên tục

- [ ] Nhấn Launch nhiều lần nhanh.
- [ ] Pause/Resume nhiều lần.
- [ ] Đổi page trong lúc tải.
- [ ] Đóng launcher trong lúc tải.
- [ ] Mở lại launcher ngay sau khi đóng.
- [ ] Launch hai instance khác nhau.
- [ ] Không Launch trùng cùng một instance.

## C3. Dung lượng và quyền truy cập

- [ ] Ổ đĩa gần hết dung lượng.
- [ ] Thư mục launcher chỉ đọc.
- [ ] Antivirus khóa một file `.jar`.
- [ ] File đang bị chương trình khác sử dụng.
- [ ] Launcher hiển thị lỗi rõ và không để file đích hỏng.

## C4. ZIP độc hại

Chỉ tester kỹ thuật thực hiện bằng package test riêng.

- [ ] Entry `../../outside.txt` bị chặn.
- [ ] Absolute path bị chặn.
- [ ] Symlink entry bị chặn.
- [ ] Hai entry trùng tên không phân biệt hoa thường bị chặn.
- [ ] Package quá nhiều file bị chặn.
- [ ] Package vượt giới hạn dung lượng bị chặn.
- [ ] Không có file nào được ghi ra ngoài thư mục instance.

---

# D. Test nâng cấp từ phiên bản cũ

Tester nên giữ bản sao dữ liệu trước khi thử.

## Từ Beta 1/Beta 2/Beta 3

- [ ] Cài RC1 đè lên thư mục cũ.
- [ ] Accounts vẫn còn.
- [ ] Selected account vẫn đúng.
- [ ] Instances vẫn còn.
- [ ] Instance settings vẫn giữ.
- [ ] Theme/language vẫn giữ.
- [ ] Channel được migration sang Stable đúng một lần.
- [ ] Các mod đã tải không bị tải lại.
- [ ] File `.part` cũ có thể resume hoặc tự phục hồi.
- [ ] Database không báo lỗi table hoặc lock.

## Clean install

- [ ] Cài RC1 vào thư mục hoàn toàn mới.
- [ ] First-run settings được tạo đúng.
- [ ] Stable là channel mặc định.
- [ ] Tạo account, instance và Launch từ đầu thành công.

---

# E. Điều kiện đạt RC

RC1 có thể lên Stable khi:

- Không có lỗi P0 chưa xử lý.
- Không có crash hoặc freeze có thể tái hiện.
- Không mất account, instance, world hoặc settings.
- Không có file được ghi ra ngoài thư mục dự kiến.
- Update hoạt động trên ít nhất hai máy Windows khác nhau.
- Offline và Microsoft Launch đều thành công.
- Vanilla và ít nhất một Modrinth modpack Launch thành công.
- Pause/Resume và Import/Export hoạt động trên build EXE.
- Stable channel migration chạy đúng một lần.

---

# F. Mẫu báo lỗi cho tester

## Tiêu đề

```text
[RC1][Khu vực] Mô tả lỗi ngắn
```

Ví dụ:

```text
[RC1][Modrinth] Pause xong không resume file mod
```

## Nội dung

```text
Phiên bản:
MCW Launcher v0.5.1 RC 1

Mức độ:
P0 / P1 / P2

Windows:
Windows 10/11 + build nếu biết

Đường dẫn launcher:
C:\...

Instance:
Tên instance + Minecraft version + loader

Các bước tái hiện:
1.
2.
3.

Kết quả mong đợi:

Kết quả thực tế:

Lỗi có xảy ra lại không:
Luôn luôn / thỉnh thoảng / một lần

Ảnh hoặc video:

Log:
Dán đoạn log liên quan hoặc đính kèm file log

Thông tin thêm:
Antivirus, VPN, giới hạn tốc độ, theme, language...
```

## Phân loại mức độ

- **P0 — Blocker:** crash, freeze, mất dữ liệu, không Launch được, update hỏng.
- **P1 — Major:** feature chính sai nhưng có cách tạm xử lý.
- **P2 — Minor:** lỗi giao diện, wording, progress chưa đẹp, không chặn sử dụng.

---

# G. Bộ test tối thiểu cho mỗi tester

Nếu tester không có nhiều thời gian, yêu cầu họ hoàn thành ít nhất:

1. Clean install.
2. Kiểm tra Stable channel.
3. Login Offline hoặc Microsoft.
4. Launch một bản Vanilla.
5. Add và Launch một Modrinth modpack.
6. Pause rồi Resume một download.
7. Đặt giới hạn tốc độ.
8. Export rồi Import lại một instance.
9. Đổi theme và language.
10. Gửi log nếu có lỗi.