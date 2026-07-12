# Tài liệu tham chiếu Public API của MCW Launcher Core

> Phiên bản mục tiêu: **MCW Launcher v0.4.x**
>
> Đối tượng sử dụng: lập trình viên GUI, CLI và các frontend khác.
>
> Tài liệu này mô tả các Public API mà frontend được phép gọi. Nội dung không phụ thuộc vào framework giao diện cụ thể.
>
> Tài liệu này được tạo bằng ChatGPT 5.2
---

## 1. Phạm vi

Frontend được phép:

- Lấy thông tin version.
- Tạo và quản lý instance.
- Load và save instance settings.
- Quản lý account.
- Xác thực account offline.
- Khởi chạy Minecraft.
- Nhận progress event có cấu trúc.

Frontend không nên:

- Đọc hoặc ghi trực tiếp file JSON của launcher.
- Truy cập trực tiếp database account.
- Tự download file Minecraft.
- Tự build classpath hoặc Java command.
- Tự chọn Java runtime.
- Tự giải nén native library.
- Gọi method có tên bắt đầu bằng `_`.

---

## 2. Tổng quan Public API

| API | Mục đích | Khuyến nghị về luồng |
|---|---|---|
| `VersionManifestManager.get()` | Load Minecraft version manifest | Nên chạy worker |
| `VersionManifestManager.latest_version()` | Lấy ID release hoặc snapshot mới nhất | Nên chạy worker |
| `VersionManager.load()` | Download và parse đầy đủ metadata version | Nên chạy worker |
| `InstanceManager.list_instances()` | Trả về danh sách instance | Thường nhanh |
| `InstanceManager.create()` | Tạo instance mới | Nên chạy worker |
| `InstanceManager.load()` | Load một instance | Thường nhanh |
| `InstanceManager.rename()` | Đổi tên instance | Nên chạy worker |
| `InstanceManager.clone()` | Clone instance | Bắt buộc worker nếu dữ liệu lớn |
| `InstanceManager.delete_instance()` | Xóa instance | Nên chạy worker |
| `InstanceManager.export()` | Export `.mcwpack` | Bắt buộc worker |
| `InstanceManager.import_instance()` | Import `.mcwpack` | Bắt buộc worker |
| `SettingsManager.load()` | Load instance settings | Thường nhanh |
| `SettingsManager.save()` | Save instance settings | Thường nhanh |
| `AccountManager.*` | Lưu và chọn account | Thường nhanh |
| `OfflineAuthentication.uuid_generator()` | Tạo offline UUID | An toàn trên UI thread |
| `OfflineAuthentication.authenticate()` | Tạo dữ liệu xác thực offline | An toàn trên UI thread |
| `MinecraftExecutor.run()` | Chạy toàn bộ launch pipeline | Bắt buộc worker |
| `ProgressEvent` | Dữ liệu progress có cấu trúc | Dữ liệu callback |

---

# 3. Version Manifest API

## 3.1. `VersionManifestManager.get()`

### Chữ ký

```python
VersionManifestManager.get() -> list[VersionManifest]
```

### Mục đích

Load Minecraft version manifest.

### Trả về

Danh sách model `VersionManifest`.

### Field thường dùng

```python
version.id
version.type
version.url
version.release_time
```

### Ví dụ

```python
versions = VersionManifestManager.get()

release_ids = [
    version.id
    for version in versions
    if version.type == "release"
]
```

### Luồng

Có thể thực hiện network request. Nên chạy ngoài GUI thread.

### Lưu ý

- Danh sách có thể chứa release, snapshot, old alpha và old beta.
- Frontend có thể lọc bằng `version.type`.
- Không tự download manifest bằng code frontend.

---

## 3.2. `VersionManifestManager.latest_version()`

### Chữ ký

```python
VersionManifestManager.latest_version(is_snapshot: bool = False) -> str
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `is_snapshot` | `bool` | `False` để lấy release mới nhất, `True` để lấy snapshot mới nhất |

### Trả về

ID của version mới nhất.

### Ví dụ

```python
latest_release = VersionManifestManager.latest_version()
latest_snapshot = VersionManifestManager.latest_version(is_snapshot=True)
```

### Luồng

Có thể phụ thuộc vào việc load manifest và nên được xem là thao tác có thể block.

### Lưu ý

Implementation hiện tại có thể trả chuỗi rỗng khi manifest không khả dụng.

---

# 4. Version Metadata API

## 4.1. `VersionManager.load()`

### Chữ ký

```python
VersionManager.load(id: str = VersionManifestManager.latest_version()) -> Version
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `id` | `str` | ID version Minecraft |

### Trả về

Model `Version`.

### Ví dụ

```python
version = VersionManager.load("1.20.1")
```

### Luồng

Có network và filesystem I/O. Nên chạy worker thread.

### Có thể lỗi khi

- Không tìm thấy version ID.
- Manifest không khả dụng.
- Download metadata thất bại.
- Metadata thiếu hoặc không hợp lệ.

### Lưu ý frontend

Dùng API này khi:

- Tạo instance mới.
- Hiển thị thông tin chi tiết version.
- Hiển thị Java major version yêu cầu.

Không gọi private method như `_parse_version()` từ frontend.

---

## 4.2. Model `Version`

### Field thường dùng

```python
version.id
version.type
version.path
version.main_class
version.java_version
version.assets
version.asset_index
version.arguments
version.minecraft_arguments
version.libraries
version.downloads
version.raw_json
```

### Ý nghĩa field

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | `str` | ID version Minecraft |
| `type` | `str` | Loại như `release`, `snapshot`, `old_alpha`, `old_beta` |
| `path` | `Path` | Path metadata đã cache |
| `main_class` | `str` | Java main class |
| `java_version` | `dict` | Metadata Java yêu cầu |
| `assets` | `str` | Tên asset index |
| `asset_index` | `dict` | Metadata download asset index |
| `arguments` | `dict \| None` | JVM/game arguments hiện đại |
| `minecraft_arguments` | `str \| None` | Chuỗi launch argument legacy |
| `libraries` | `list[dict]` | Metadata library |
| `downloads` | `dict` | Metadata client/server |
| `raw_json` | `dict` | Metadata đầy đủ đã parse |

### Lưu ý tương thích

Version hiện đại thường dùng:

```text
arguments.jvm
arguments.game
```

Version legacy có thể dùng:

```text
minecraftArguments
```

Frontend không được tự parse hoặc lựa chọn giữa hai định dạng. Launch pipeline sẽ tự xử lý.

---

# 5. Instance API

## 5.1. `InstanceManager.list_instances()`

### Chữ ký

```python
InstanceManager.list_instances() -> list[Instance]
```

### Mục đích

Trả về toàn bộ instance đã đăng ký.

### Trả về

Danh sách model `Instance`.

### Luồng

Thường nhanh. Có thể chạy trên GUI thread, nhưng worker an toàn hơn nếu số instance lớn.

### Ví dụ

```python
instances = InstanceManager.list_instances()

for instance in instances:
    print(instance.name, instance.version_id)
```

### Lưu ý frontend

Refresh danh sách sau:

- Create.
- Rename.
- Clone.
- Delete.
- Import.

---

## 5.2. `InstanceManager.create()`

### Chữ ký

```python
InstanceManager.create(name: str, version: Version, mod_loader: tuple[str, str] = ("vanilla", "-1")) -> Instance
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `name` | `str` | Tên instance mới |
| `version` | `Version` | Model version Minecraft đã load |
| `mod_loader` | `tuple[str, str]` | Tên và version mod loader |

### Trả về

`Instance` vừa tạo.

### Ví dụ

```python
version = VersionManager.load("1.20.1")
instance = InstanceManager.create(name="My Instance", version=version)
```

### Luồng

Có ghi filesystem. Nên chạy worker.

### Có thể lỗi khi

- Tên instance đã tồn tại.
- Tên không hợp lệ với filesystem.
- Không tạo được thư mục.
- Không ghi được metadata.

### Lưu ý frontend

Sau khi thành công:

- Refresh danh sách.
- Chọn instance mới.
- Load settings của nó nếu cần.

---

## 5.3. `InstanceManager.load()`

### Chữ ký

```python
InstanceManager.load(name: str) -> Instance
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `name` | `str` | Tên instance đã tồn tại |

### Trả về

Model `Instance`.

### Ví dụ

```python
instance = InstanceManager.load("My Instance")
```

### Luồng

Thường nhanh.

### Có thể lỗi khi

- Instance không tồn tại.
- Metadata instance không hợp lệ.
- Không đọc được filesystem.

### Lưu ý frontend

Không đọc `instance.json` trực tiếp.

---

## 5.4. `InstanceManager.is_instance_exist()`

### Chữ ký

```python
InstanceManager.is_instance_exist(name: str) -> bool
```

### Trả về

`True` nếu instance tồn tại, ngược lại là `False`.

### Ví dụ

```python
if InstanceManager.is_instance_exist("My Instance"):
    ...
```

### Lưu ý

Dùng method này thay vì chỉ kiểm tra directory vì manager có thể còn xử lý registry hoặc metadata legacy.

---

## 5.5. `InstanceManager.rename()`

### Chữ ký

```python
InstanceManager.rename(instance_name: str, new_name: str) -> Path
```

### Trả về

Path thư mục instance sau khi đổi tên.

### Luồng

Nên chạy worker.

### Có thể lỗi khi

- Instance nguồn không tồn tại.
- Tên đích đã tồn tại.
- Filesystem rename thất bại.

### Lưu ý frontend

Sau khi thành công:

- Refresh danh sách instance.
- Cập nhật selection.
- Cập nhật path đang hiển thị.

---

## 5.6. `InstanceManager.clone()`

### Chữ ký

```python
InstanceManager.clone(source_name: str, new_name: str, include_saves: bool = False) -> Instance
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `source_name` | `str` | Tên instance nguồn |
| `new_name` | `str` | Tên clone |
| `include_saves` | `bool` | Có copy world hay không |

### Trả về

`Instance` đã clone.

### Luồng

Chạy worker. World lớn có thể tốn nhiều thời gian.

### Lưu ý

Khi `include_saves=False`, các thư mục lớn hoặc không cần thiết có thể bị loại trừ:

- `saves`
- `logs`
- `crash-reports`

### Lưu ý frontend

Nên có lựa chọn rõ ràng trước khi copy saves vì world có thể rất lớn.

---

## 5.7. `InstanceManager.delete_instance()`

### Chữ ký

```python
InstanceManager.delete_instance(name: str) -> bool
```

### Trả về

Boolean cho biết xóa thành công hay không.

### Luồng

Nên chạy worker.

### Lưu ý frontend

Luôn yêu cầu xác nhận. Thao tác này xóa thư mục instance.

---

## 5.8. `InstanceManager.export()`

### Chữ ký

```python
InstanceManager.export(instance_name: str, output_path: Path, include_saves: bool = False) -> Path
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `instance_name` | `str` | Instance cần export |
| `output_path` | `Path` | Path `.mcwpack` đích |
| `include_saves` | `bool` | Có bao gồm world hay không |

### Trả về

Path package cuối cùng.

### Luồng

Chạy worker.

### Có thể lỗi khi

- Thiếu `instance.json`.
- Output path không hợp lệ.
- Không có quyền ghi.
- Không tạo được archive.

### Lưu ý frontend

Chọn destination path trước khi bắt đầu worker task.

---

## 5.9. `InstanceManager.import_instance()`

### Chữ ký

```python
InstanceManager.import_instance(package_path: Path) -> Instance
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `package_path` | `Path` | Path `.mcwpack` hoặc package được hỗ trợ |

### Trả về

`Instance` đã import.

### Luồng

Chạy worker.

### Có thể lỗi khi

- Package không hợp lệ.
- Thiếu `instance.json`.
- Có nhiều `instance.json`.
- Instance cùng tên đã tồn tại.
- Extract archive thất bại.

### Lưu ý frontend

Sau khi thành công:

- Refresh danh sách instance.
- Chọn instance vừa import.

---

## 5.10. Model `Instance`

### Field thường dùng

```python
instance.instance_id
instance.name
instance.version_id
instance.mod_loader
instance.instance_dir
```

Metadata bổ sung có thể bao gồm:

```python
instance.created_at
instance.updated_at
instance.last_played
instance.icon
instance.notes
instance.launcher_version
instance.metadata_version
```

Field chính xác phụ thuộc vào phiên bản model hiện tại.

---

# 6. Instance Settings API

## 6.1. `SettingsManager.load()`

### Chữ ký

```python
SettingsManager.load(instance: Instance) -> InstanceSettings
```

### Trả về

Model `InstanceSettings`.

### Luồng

Thường nhanh.

### Ví dụ

```python
settings = SettingsManager.load(instance)
```

---

## 6.2. `SettingsManager.save()`

### Chữ ký

```python
SettingsManager.save(instance: Instance, settings: InstanceSettings) -> None
```

### Mục đích

Lưu toàn bộ model settings.

### Luồng

Thường nhanh nhưng có ghi filesystem.

### Ví dụ

```python
settings = SettingsManager.load(instance)
settings.min_memory = 1024
settings.max_memory = 4096
SettingsManager.save(instance, settings)
```

### Validation frontend

Trước khi save:

- `min_memory > 0`
- `max_memory >= min_memory`
- `width > 0`
- `height > 0`
- Custom Java path tồn tại nếu được đặt

---

## 6.3. Các update method bổ sung

Tùy implementation hiện tại, manager có thể expose:

```python
SettingsManager.save_default(...)
SettingsManager.update_memory(...)
SettingsManager.update_java_path(...)
SettingsManager.update_window(...)
SettingsManager.update_jvm_arguments(...)
SettingsManager.update_game_arguments(...)
```

Chỉ dùng khi chúng tồn tại trong public implementation hiện tại. Workflow `load()` rồi `save()` vẫn là cách ổn định và đơn giản nhất.

---

## 6.4. Model `InstanceSettings`

### Field thường dùng

```python
settings.java_path
settings.min_memory
settings.max_memory
settings.width
settings.height
settings.fullscreen
settings.jvm_arguments
settings.game_arguments
settings.offline_multiplayer_enabled
```

### Ý nghĩa

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `java_path` | `Path \| None` | Custom Java path tùy chọn |
| `min_memory` | `int` | Heap ban đầu theo MB |
| `max_memory` | `int` | Heap tối đa theo MB |
| `width` | `int` | Chiều rộng cửa sổ |
| `height` | `int` | Chiều cao cửa sổ |
| `fullscreen` | `bool` | Chế độ fullscreen |
| `jvm_arguments` | `list[str]` | JVM argument do người dùng thêm |
| `game_arguments` | `list[str]` | Game argument do người dùng thêm |
| `offline_multiplayer_enabled` | `bool` | Bật workaround offline multiplayer |

---

# 7. Account API

## 7.1. `AccountManager.create_offline_account()`

### Chữ ký

```python
AccountManager.create_offline_account(username: str) -> Account
```

### Mục đích

Tạo và lưu account offline.

### Trả về

`Account` vừa tạo.

### Luồng

Thường nhanh.

### Có thể lỗi khi

- Username không hợp lệ.
- Account trùng.
- Không ghi được database.

---

## 7.2. `AccountManager.list_accounts()`

### Chữ ký

```python
AccountManager.list_accounts() -> list[Account]
```

### Trả về

Toàn bộ account đã lưu.

### Luồng

Thường nhanh.

---

## 7.3. `AccountManager.get_account()`

### Chữ ký

```python
AccountManager.get_account(account_id: str) -> Account | None
```

### Trả về

Account phù hợp hoặc `None`.

---

## 7.4. `AccountManager.get_selected_account()`

### Chữ ký

```python
AccountManager.get_selected_account() -> Account | None
```

### Trả về

Account đang được chọn hoặc `None`.

### Lưu ý frontend

Khi khởi động:

1. Load selected account.
2. Nếu không có, yêu cầu người dùng tạo hoặc chọn account.

---

## 7.5. `AccountManager.set_selected_account()`

### Chữ ký

```python
AccountManager.set_selected_account(account_id: str) -> None
```

### Mục đích

Lưu ID account đang được chọn.

### Có thể lỗi khi

Account không tồn tại hoặc database không cập nhật được.

---

## 7.6. `AccountManager.remove_account()`

### Chữ ký

```python
AccountManager.remove_account(account_id: str) -> bool
```

### Trả về

Account có được xóa hay không.

### Lưu ý frontend

Refresh danh sách sau khi xóa. Manager có thể tự chọn account khác nếu cần.

---

## 7.7. `AccountManager.is_account_exist()`

### Chữ ký

```python
AccountManager.is_account_exist(username: str) -> bool
```

### Trả về

Username đã tồn tại trong account storage hay chưa.

---

## 7.8. Model `Account`

### Field thường dùng

```python
account.account_id
account.account_type
account.username
account.uuid
account.access_token
account.refresh_token
account.token_expires_at
```

Một số token field có thể không tồn tại hoặc là `None` với account offline.

### Loại account

```python
AccountSource.OFFLINE
AccountSource.MICROSOFT
```

Microsoft authentication vẫn đang phát triển trong v0.4.x.

---

# 8. Offline Authentication API

## 8.1. `OfflineAuthentication.uuid_generator()`

### Chữ ký

```python
OfflineAuthentication.uuid_generator(username: str) -> str
```

### Mục đích

Tạo Minecraft offline UUID ổn định.

### Luồng

An toàn trên GUI thread.

### Ví dụ

```python
player_uuid = OfflineAuthentication.uuid_generator("Steve")
```

### Lưu ý

Kết quả:

- Ổn định với cùng username.
- Phân biệt chữ hoa và chữ thường.
- Tương thích với hành vi offline UUID của Minecraft.

---

## 8.2. `OfflineAuthentication.authenticate()`

### Chữ ký

```python
OfflineAuthentication.authenticate(account: Account) -> Authentication
```

### Trả về

Model `Authentication` sẵn sàng truyền vào `MinecraftExecutor.run()`.

### Luồng

An toàn trên GUI thread.

### Ví dụ

```python
authentication = OfflineAuthentication.authenticate(account)
```

---

## 8.3. Ví dụ account offline tạm thời

Frontend có thể tạo account trong memory cho session tạm:

```python
import uuid

account = Account(
    account_id=str(uuid.uuid4()),
    account_type=AccountSource.OFFLINE,
    username="Steve",
    uuid=OfflineAuthentication.uuid_generator("Steve"),
)

authentication = OfflineAuthentication.authenticate(account)
```

Với account screen đầy đủ, nên dùng account được lưu qua `AccountManager`.

---

## 8.4. Model `Authentication`

### Field thường dùng

```python
authentication.player_name
authentication.uuid
authentication.access_token
authentication.xuid
authentication.client_id
authentication.user_type
```

Một số giá trị có thể là `None` với account offline.

---

# 9. Launch API

## 9.1. `MinecraftExecutor.run()`

### Chữ ký

```python
MinecraftExecutor.run(
    instance: Instance,
    authentication: Authentication,
    account: Account,
    on_progress: ProgressCallback | None = None,
    debug_mode: bool = False,
) -> dict
```

### Tham số

| Tên | Kiểu | Mô tả |
|---|---|---|
| `instance` | `Instance` | Instance cần launch |
| `authentication` | `Authentication` | Dữ liệu xác thực |
| `account` | `Account` | Model account |
| `on_progress` | `Callable[[ProgressEvent], None] \| None` | Progress callback |
| `debug_mode` | `bool` | Bật hành vi debug bổ sung |

### Trả về

Implementation hiện tại trả:

```python
{
    "javaPath": Path,
    "minecraftJavaMajorVersion": int,
    "minecraftVersion": str,
}
```

### Luồng

Bắt buộc chạy worker thread.

### Ví dụ

```python
result = MinecraftExecutor.run(
    instance=instance,
    authentication=authentication,
    account=account,
    on_progress=on_progress,
)
```

### Trách nhiệm nội bộ

Executor sở hữu toàn bộ launch pipeline:

```text
Load version metadata
Download client
Download libraries
Download asset index
Download assets
Load settings
Build context
Build arguments
Build command
Select Java
Launch Minecraft
```

Frontend không được gọi riêng từng bước nội bộ này.

### Tương thích

Executor tự xử lý:

- Structured arguments hiện đại.
- `minecraftArguments` legacy.

Frontend không cần logic launch riêng theo version.

---

# 10. Progress API

## 10.1. Progress callback

### Chữ ký

```python
def on_progress(event: ProgressEvent) -> None:
    ...
```

Callback có thể được gọi từ worker thread đang chạy executor.

---

## 10.2. Model `ProgressEvent`

### Field thường dùng

```python
event.stage
event.message
event.current
event.total
event.unit
event.fraction
event.percentage
event.is_determinate
```

### Ý nghĩa

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `stage` | `ProgressStage` | Stage hiện tại của pipeline |
| `message` | `str` | Status cho người dùng |
| `current` | `int \| None` | Giá trị hiện tại |
| `total` | `int \| None` | Tổng giá trị |
| `unit` | `str \| None` | Đơn vị như files hoặc bytes |
| `fraction` | `float \| None` | Giá trị từ 0.0 đến 1.0 |
| `percentage` | `float \| None` | Giá trị từ 0 đến 100 |
| `is_determinate` | `bool` | Có biết tổng progress hay không |

### Hành vi frontend

Nếu `is_determinate` là true:

- Hiển thị phần trăm.
- Hiển thị current và total.
- Dùng progress bar determinate.

Nếu false:

- Hiển thị message và stage.
- Dùng progress indicator indeterminate.

---

## 10.3. `ProgressStage`

Các stage hiện tại:

```python
ProgressStage.PREPARING
ProgressStage.LOADING_VERSION
ProgressStage.DOWNLOADING_CLIENT
ProgressStage.DOWNLOADING_LIBRARIES
ProgressStage.DOWNLOADING_ASSET_INDEX
ProgressStage.DOWNLOADING_ASSETS
ProgressStage.BUILDING_CONTEXT
ProgressStage.BUILDING_COMMAND
ProgressStage.SELECTING_JAVA
ProgressStage.LAUNCHING
ProgressStage.FINISHED
```

| Stage | Ý nghĩa |
|---|---|
| `PREPARING` | Khởi tạo pipeline |
| `LOADING_VERSION` | Load và parse metadata version |
| `DOWNLOADING_CLIENT` | Verify hoặc download client JAR |
| `DOWNLOADING_LIBRARIES` | Verify hoặc download libraries |
| `DOWNLOADING_ASSET_INDEX` | Download metadata asset index |
| `DOWNLOADING_ASSETS` | Verify hoặc download asset objects |
| `BUILDING_CONTEXT` | Build placeholder context |
| `BUILDING_COMMAND` | Build command cuối |
| `SELECTING_JAVA` | Chọn Java runtime |
| `LAUNCHING` | Tạo Java process |
| `FINISHED` | Tạo process hoàn tất |

`FINISHED` nghĩa là process Minecraft đã được tạo, không phải game đã thoát.

---

# 11. Luồng frontend được đề xuất

## 11.1. Khởi động

```text
Load instance list
Load selected account
Load version manifest trên worker
Populate selector
```

## 11.2. Tạo instance

```text
Validate tên
Load Version
Create Instance
Refresh danh sách
Chọn instance mới
```

## 11.3. Launch instance

```text
Load Instance
Load/Create Account
Authenticate
Disable control xung đột
Chạy MinecraftExecutor trên worker
Render ProgressEvent
Hiển thị Java/version được trả về
Bật lại control
```

## 11.4. Import/export

```text
Chọn file path trên frontend thread
Chạy import/export trên worker
Refresh danh sách sau import
Hiển thị package path sau export
```

---

# 12. Tham chiếu về luồng

| API | Khuyến nghị |
|---|---|
| `VersionManifestManager.get()` | Worker |
| `VersionManifestManager.latest_version()` | Worker |
| `VersionManager.load()` | Worker |
| `InstanceManager.list_instances()` | UI-safe nếu project nhỏ |
| `InstanceManager.load()` | Thường UI-safe |
| `InstanceManager.create()` | Worker |
| `InstanceManager.rename()` | Worker |
| `InstanceManager.clone()` | Worker |
| `InstanceManager.delete_instance()` | Worker |
| `InstanceManager.import_instance()` | Worker |
| `InstanceManager.export()` | Worker |
| `SettingsManager.load()` | Thường UI-safe |
| `SettingsManager.save()` | Thường UI-safe |
| `AccountManager.*` | Thường UI-safe |
| `OfflineAuthentication.*` | UI-safe |
| `MinecraftExecutor.run()` | Bắt buộc worker |

Frontend framework chịu trách nhiệm đưa progress và kết quả trở lại main UI thread.

---

# 13. Error Contract

Public API hiện tại thường raise standard Python exception hoặc `RuntimeError`.

Nhóm lỗi có thể gồm:

- `RuntimeError`
- `FileNotFoundError`
- `PermissionError`
- `OSError`
- Network request error
- Package hoặc metadata không hợp lệ

Yêu cầu frontend:

- Catch lỗi tại Public API boundary.
- Hiển thị message ngắn gọn cho người dùng.
- Lưu chi tiết kỹ thuật vào activity/debug log.
- Không được nuốt exception bất ngờ.

---

# 14. Internal API

Các API sau là internal và frontend không nên gọi trực tiếp:

```text
HttpDownloader
DownloadClientManager
DownloadLibraryManager
AssetIndexManager
AssetManager
ClasspathBuilder
ContextBuilder
ArgumentBuilder
LauncherManager
JavaManager
JavaSelector
JavaRuntime
```

Private method bắt đầu bằng `_` cũng là internal.

Các component này có thể thay đổi mà không giữ frontend compatibility.

---

# 15. Độ ổn định API

| API | Trạng thái trong v0.4.x |
|---|---|
| `MinecraftExecutor.run()` | Public |
| `ProgressEvent` / `ProgressStage` | Public |
| `InstanceManager` | Public |
| `VersionManifestManager` | Public |
| `VersionManager` | Public |
| `SettingsManager.load/save` | Public |
| `OfflineAuthentication` | Public |
| `AccountManager` | Public, đang phát triển |
| Microsoft authentication | Experimental |
| Mod loader API | Chưa public |
| Internal builder/manager | Internal |

---

# 16. Checklist cho frontend

- [ ] Chỉ dùng Public Core API.
- [ ] Không đọc JSON hoặc SQLite trực tiếp.
- [ ] Chạy network và launch task ngoài UI thread.
- [ ] Hiển thị `ProgressEvent` thay vì parse log.
- [ ] Refresh instance sau create, rename, clone, delete hoặc import.
- [ ] Xác nhận thao tác phá hủy dữ liệu.
- [ ] Validate input trước khi gọi Core.
- [ ] Ngăn launch task bị lặp.
- [ ] Hiển thị lỗi rõ ràng.
- [ ] Không chứa logic launch riêng theo version.

---

## Nguyên tắc cuối cùng

```text
Frontend quyết định thông tin được hiển thị thế nào.
Core quyết định Minecraft hoạt động thế nào.
```