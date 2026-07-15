# MCW Launcher Beta 10 — Microsoft Account Security

Beta 10 tập trung vào bảo vệ token Microsoft, tính toàn vẹn của account database và ngăn dữ liệu nhạy cảm xuất hiện trong log hoặc diagnostic report.

## Phạm vi bảo vệ

### DPAPI v2

Refresh token Microsoft được bảo vệ bằng Windows DPAPI theo user hiện tại. Định dạng mới có prefix:

```text
mcw-dpapi:v2:<base64>
```

Beta 10 bổ sung optional entropy được tạo từ application identity, account ID và loại token. Vì vậy ciphertext của refresh token không thể bị đổi sang account khác hoặc đổi sang field khác rồi giải mã bình thường.

Token Beta 9 dùng DPAPI cũ được tự phát hiện và mã hóa lại khi launcher khởi động.

### Không lưu Minecraft access token dài hạn

Minecraft access token có thời gian sống ngắn và chỉ được giữ trong memory của phiên launcher hiện tại. Database chỉ lưu Microsoft refresh token đã được DPAPI bảo vệ. Khi launch sau khi mở lại launcher, token Minecraft mới được tạo bằng refresh flow.

### Record integrity

Mỗi account record có HMAC-SHA256 trên profile fields và encrypted credential fields. HMAC key được tạo ngẫu nhiên và chính nó được DPAPI bảo vệ. Launcher từ chối record bị thay đổi ngoài transaction hợp lệ.

Đây là lớp phát hiện corruption/tampering, không phải biện pháp chống malware đang chạy dưới cùng Windows user.

### SQLite hardening

Account database bật:

```text
PRAGMA quick_check
PRAGMA secure_delete = ON
PRAGMA trusted_schema = OFF
PRAGMA temp_store = MEMORY
PRAGMA synchronous = FULL
```

Khi xóa account, token fields được xóa trước, record được delete và database được compact bằng `VACUUM`.

### Log redaction

Các nguồn sau được scrub trước khi hiển thị hoặc export:

- GUI error dialogs;
- launcher activity log;
- diagnostic report;
- OAuth error response.

Bộ redactor che `Bearer` token, access token, refresh token, authorization code, code verifier, client secret, password và JWT-like value.

### OAuth callback hardening

Local callback response thêm:

```text
Cache-Control: no-store
Pragma: no-cache
Content-Security-Policy: default-src 'none'
Referrer-Policy: no-referrer
X-Content-Type-Options: nosniff
```

Authorization code, state và error state được xóa khỏi static handler memory sau mỗi callback.

## Accounts → Security

Accounts page có thêm card **Account security**:

- **Verify security**: kiểm tra SQLite, DPAPI format và record integrity;
- **Re-protect credentials**: tạo integrity key mới, mã hóa lại refresh token và compact database.

Trạng thái hiển thị:

```text
Protected Microsoft accounts: 2/2 • Legacy: 0 • Invalid: 0
```

Account Microsoft không còn refresh token hoặc có ciphertext không mở được sẽ được đánh dấu invalid và cần đăng nhập lại.

## Migration

Khi nâng từ Beta 9:

1. schema database tăng từ 1 lên 2;
2. token DPAPI cũ được giải mã bằng legacy path;
3. access token không được lưu lại;
4. refresh token được mã hóa bằng DPAPI v2;
5. integrity signature được tạo;
6. database được compact.

Migration không gửi token ra mạng và không thay đổi account UUID hoặc username.

## Threat model và giới hạn

Beta 10 bảo vệ tốt hơn trước:

- copy file database sang Windows user/máy khác;
- đọc token trực tiếp từ SQLite;
- đổi ciphertext giữa account/field;
- corruption hoặc chỉnh sửa record;
- token bị in vào log/diagnostics;
- dữ liệu token còn trong page SQLite đã delete.

Beta 10 không thể bảo vệ token trước malware hoặc process có quyền chạy dưới chính Windows user đang đăng nhập. DPAPI cũng không thay thế Windows account password, BitLocker, antivirus hoặc code signing.
