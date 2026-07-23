# MCW Launcher v0.7.0 Beta 1

> The first beta of the 0.7 line introduces the CurseForge Gateway, provider caching, API request controls, and manual-distribution fallback.

---

## Tiếng Việt

### CurseForge Gateway

- Launcher không còn cần hoặc chứa CurseForge API key.
- Mọi request metadata đi qua **MCW CurseForge Gateway** trên Vercel bằng HTTPS.
- API key thật chỉ tồn tại trong environment variables phía server.
- File mod được tải trực tiếp bởi downloader của launcher; dữ liệu lớn không đi xuyên qua Vercel.
- Có thể override gateway bằng `config/curseforge.json` hoặc environment variables dành cho development.

### Tìm kiếm và cài CurseForge mods

- Trang Mods dùng một catalog chung ngay tại chỗ cho cả Modrinth và CurseForge.
- Chọn `Nguồn mod` (Modrinth/CurseForge) và `Mod loader` (Fabric/Forge) rồi tìm kiếm trong cùng một bảng, không mở thêm cửa sổ CurseForge.
- Manage Mods vẫn có trình duyệt CurseForge riêng cho instance đang được quản lý.
- Lọc theo Minecraft version, Fabric/Forge và Release/Beta/Alpha.
- Chọn chính xác file/version trước khi cài.
- Kiểm tra file có tương thích với version và loader của instance.
- Cài dependency bắt buộc và dùng batch metadata để giảm số request.
- Download, retry, checksum và tiến trình vẫn dùng hệ thống downloader thống nhất của MCW Launcher.

### Tải thủ công an toàn

Khi tác giả tắt phân phối qua bên thứ ba hoặc CurseForge không cung cấp `downloadUrl`:

- launcher không cố đoán hoặc scrape URL;
- hiển thị file cần tải và mở trang CurseForge chính thức;
- người dùng chọn file `.jar` đã tải;
- launcher xác minh kích thước và SHA-1;
- file chỉ được thêm vào instance khi xác minh thành công;
- registry giữ trạng thái `pendingDownload` cho đến khi hoàn tất.

Fallback tải thủ công trong Beta 1 áp dụng cho mods. Luồng CurseForge modpack vẫn ở mức thử nghiệm.

### Cache JSON 10 MB

- Cache CurseForge được lưu cục bộ theo từng entry JSON.
- Giới hạn tối đa `10 MiB`, dọn xuống khoảng `8 MiB` bằng LRU khi vượt ngưỡng.
- Không preload toàn bộ cache khi launcher startup.
- Ghi cache bằng file tạm và atomic replace để giảm nguy cơ hỏng dữ liệu.
- TTL:
  - search: 30 phút;
  - file list: 1 giờ;
  - project: 12 giờ;
  - file metadata: 24 giờ.
- Khi gateway lỗi, launcher có thể tiếp tục hiển thị cache cũ và ghi rõ dữ liệu đang stale.

### Thời gian cập nhật và giới hạn request

Giao diện CurseForge hiển thị:

- lần refresh thành công gần nhất;
- dữ liệu live/cached/stale;
- dung lượng cache hiện tại;
- lỗi refresh gần nhất;
- thời gian chờ trước lần refresh thủ công tiếp theo.

Để tránh gọi API quá nhiều:

- không gửi search rỗng;
- một cache key chỉ có tối đa một request đang chạy;
- request trùng đồng thời dùng chung kết quả;
- refresh thủ công có cooldown 60 giây;
- lỗi liên tiếp dùng backoff `10/30/60/120/300` giây;
- launcher tôn trọng `Retry-After` từ gateway;
- metadata nhiều project/file được lấy bằng batch tối đa 50 ID.

### Phiên bản

```text
VERSION = v0.7.0 Beta 1
VERSION_ID = 0.7.0-beta.1
UPDATE_CHANNEL = beta
```

### Kiểm thử

```text
762 passed
46 skipped
0 failed
0 errors
```

Các test bị skip là nhóm GUI/PySide6 không khả dụng trong môi trường regression. Toàn bộ core CurseForge, cache, downloader, manual fallback và regression hiện có đều hoàn tất không có lỗi.

### Lưu ý tester

- Đây là bản Beta dành cho tester, không phải Stable.
- Hãy thử trên bản sao instance trước khi dùng với world quan trọng.
- Kiểm tra cả Fabric và Forge.
- Thử một mod cho phép tải tự động và một mod yêu cầu tải thủ công.
- Khi báo lỗi, gửi Logs nhưng không gửi account database hoặc token.

---

## English

### CurseForge Gateway

- The launcher no longer requires or embeds a CurseForge API key.
- Metadata requests use the HTTPS **MCW CurseForge Gateway** hosted on Vercel.
- The real API key remains only in server-side environment variables.
- Mod files are downloaded directly by MCW Launcher's downloader rather than proxied through Vercel.
- Developers may override the gateway through `config/curseforge.json` or environment variables.

### CurseForge mod browsing and installation

- The standalone Mods page now uses one inline catalog for both Modrinth and CurseForge.
- Select the `Mod provider` (Modrinth/CurseForge) and `Mod loader` (Fabric/Forge), then search in the same table without opening another CurseForge window.
- Manage Mods keeps its instance-scoped CurseForge browser for quick management actions.
- Filter by Minecraft version, Fabric/Forge, and Release/Beta/Alpha.
- Select an exact compatible file before installation.
- Validate Minecraft-version and loader compatibility.
- Install required dependencies and use batch metadata requests to reduce traffic.
- Downloads continue to use MCW Launcher's unified progress, retry, and checksum pipeline.

### Safe manual distribution fallback

When an author disables third-party distribution or CurseForge returns no `downloadUrl`:

- the launcher does not scrape or guess a CDN URL;
- it opens the official CurseForge project page;
- the user selects the downloaded `.jar`;
- byte size and SHA-1 are verified;
- the mod is added only after verification succeeds;
- the registry keeps a `pendingDownload` state until completion.

Beta 1 manual fallback applies to mods. CurseForge modpack handling remains experimental.

### 10 MB local JSON cache

- CurseForge responses are stored as separate JSON entries.
- The disk cache is capped at `10 MiB` and evicts toward `8 MiB` using LRU.
- Startup does not parse the complete cache.
- Atomic replacement protects cache writes.
- TTL policy:
  - search: 30 minutes;
  - file lists: 1 hour;
  - project metadata: 12 hours;
  - file metadata: 24 hours.
- Stale cache may remain visible when the gateway is unavailable.

### Refresh information and request limits

The CurseForge browser displays:

- last successful refresh;
- live/cached/stale source;
- cache size;
- latest refresh error;
- remaining manual-refresh cooldown.

Traffic controls include:

- no empty searches;
- one in-flight request per cache key;
- concurrent identical requests share one result;
- a 60-second manual refresh cooldown;
- `10/30/60/120/300` second failure backoff;
- gateway `Retry-After` support;
- batch metadata requests of up to 50 IDs.

### Version

```text
VERSION = v0.7.0 Beta 1
VERSION_ID = 0.7.0-beta.1
UPDATE_CHANNEL = beta
```

### Tests

```text
762 passed
46 skipped
0 failed
0 errors
```

Skipped tests are GUI/PySide6-dependent tests unavailable in the regression environment. The CurseForge core, cache, downloader, manual fallback, and the existing regression suite completed without failures.

### Tester notes

- This is an opt-in Beta, not a Stable build.
- Test on copied instances before using important worlds.
- Verify both Fabric and Forge flows.
- Test one automatically distributable mod and one manual-download case.
- Include Logs in bug reports, but never share account databases or tokens.
