# TỪ ĐIỂN DỮ LIỆU — TỔ CHỨC · TÀI KHOẢN · HẠ TẦNG HỆ THỐNG

Bản 1.0 — 28/08/2026. Nguồn sự thật là model.py; tệp này chép Ý NGHĨA, không thay mã.

---

Mọi bảng trong cụm này kế thừa `AuditMixin`, tức đều có 5 cột chung:

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT PK | Khóa chính, tự tăng |
| `created_at` | DATETIME | Thời điểm tạo dòng (server default) |
| `created_by` | BIGINT | ID tài khoản tạo |
| `updated_at` | DATETIME | Thời điểm sửa lần cuối (auto on update) |
| `updated_by` | BIGINT | ID tài khoản sửa lần cuối |

Các mục bên dưới chỉ liệt kê cột đặc trưng của từng bảng, không nhắc lại 5 cột trên.

---

## `tab_user` — Tài khoản đăng nhập

Một dòng tương ứng một người dùng của hệ thống. Tài khoản được liên kết một-một với hồ sơ nhân sự qua `employee_id`. Ảnh đại diện không lưu URL trực tiếp mà lưu ID của bản ghi `tab_file`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `email` | VARCHAR(255) | Địa chỉ email đăng nhập (index); đồng bộ từ email nhân sự khi nhân sự đổi email |
| `google_sub` | VARCHAR(100) | Subject ID của tài khoản Google (dùng đăng nhập OAuth); rỗng nếu chưa liên kết |
| `password_hash` | VARCHAR(255) | Mật khẩu đã băm (bcrypt); rỗng khi chỉ dùng Google |
| `employee_id` | BIGINT | Trỏ tới `tab_employee.id`; 0 = tài khoản mồ côi chưa gắn hồ sơ |
| `avatar_file_id` | BIGINT | Trỏ tới `tab_file.id`; 0 = chưa có ảnh. Không lưu URL chuỗi |
| `signature` | VARCHAR(500) | URL ảnh chữ ký cá nhân trên storage; người dùng tự tải lên từ Trang cá nhân |
| `is_active` | BOOLEAN | Tài khoản đang hoạt động; `False` = bị khoá, không đăng nhập được |

**Logic chính:**
- Tài khoản mới tự động được gán vai trò `employee` (mã cứng trong `DEFAULT_ROLE_CODE`) — đủ để lập phiếu đề xuất cho bản thân; vai trò thêm phải gán tay ở màn Phân quyền.
- Khi đăng nhập Google lần đầu mà chưa có ảnh, hệ thống tải ảnh từ URL Google về storage nội bộ (`sync_google_avatar`), sau đó không còn phụ thuộc URL ngoài.
- `User.avatar` là property: ưu tiên trả `thumb_url` (nhẹ hơn), fallback về `url` của `tab_file`, cuối cùng trả chuỗi rỗng — mọi nơi đọc ảnh đều dùng property này, không đọc `avatar_file_id` trực tiếp.
- Đổi ảnh đại diện (`set_user_avatar`): tải file mới lên storage, cập nhật `avatar_file_id`, rồi xoá file cũ — không để lại file rác trên storage.
- Tài khoản bị coi là "mồ côi" khi `employee_id = 0` hoặc trỏ tới hồ sơ nhân sự đã xoá.

---

## `tab_user_role` — Gán vai trò cho tài khoản

Bảng nối nhiều-nhiều giữa `tab_user` và `tab_role`. Một tài khoản có thể giữ nhiều vai trò cùng lúc; quyền thực tế là hợp (union) các quyền của tất cả vai trò.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT | Trỏ tới `tab_user.id` |
| `role_id` | BIGINT | Trỏ tới `tab_role.id` |

**Logic chính:**
- Không có khóa ngoại cứng — ràng buộc đảm bảo ở tầng service: xoá vai trò phải kiểm tra không còn dòng nào tham chiếu ở bảng này, nếu còn thì từ chối.
- `assign_roles` xoá toàn bộ dòng cũ của `user_id` rồi chèn lại theo thứ tự người quản trị chọn — danh sách `role_id` được sắp xếp trước khi trả về để React Query so sánh ổn định.
- Thay đổi ở bảng này phải gọi `perm_cache_clear(user_id)` để vô hiệu cache quyền 60 giây.

---

## `tab_user_scope` — Phạm vi dữ liệu riêng từng tài khoản (Lớp B)

Mỗi dòng là một giá trị được **cấp thêm** hoặc **loại trừ** cho một tài khoản trong một vai trò cụ thể. Đây là **trục thứ hai** của hệ thống phân quyền hai trục: trong khi `tab_permission` quyết định hành động nào được phép (trục vai trò × hành động), bảng này điều chỉnh tầm nhìn dữ liệu theo từng người (trục người dùng × phạm vi).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT | Trỏ tới `tab_user.id` |
| `role_id` | BIGINT | Trỏ tới `tab_role.id`; 0 = áp cho mọi vai trò của người dùng |
| `entity` | VARCHAR(50) | Mã chức năng (vd `purchase_request`); rỗng = áp chung cho tất cả chức năng |
| `dim` | VARCHAR(20) | Chiều phân tách: `company` (theo pháp nhân) / `department` (theo phòng ban) / `employee` (theo cá nhân) |
| `value` | VARCHAR(100) | Giá trị cụ thể tương ứng chiều `dim` (vd ID pháp nhân, tên phòng ban) |
| `is_exclude` | BOOLEAN | `True` = loại trừ giá trị này khỏi tầm nhìn; `False` = cấp thêm quyền xem |

**Logic chính:**
- Phạm vi tổng của một người được xây dựng là tập hợp của **tất cả grant** mà người đó có quyền hành động trên entity đó — union, không giao.
- `entity = ''` ghi đè phạm vi tổng; `entity = 'purchase_request'` chỉ ảnh hưởng màn hình cụ thể đó.
- `is_exclude = True` dùng để rút lại một giá trị trong phạm vi rộng (vd vai trò được xem toàn công ty nhưng trừ phòng X).
- Thay đổi phạm vi phải gọi `perm_cache_clear` để cache quyền không cũ.

---

## `tab_role` — Vai trò

Định nghĩa vai trò trong hệ thống. Mỗi vai trò có một tập quyền (entity × hành động) được lưu trong `tab_permission`. Đây là **trục thứ nhất** của hệ thống phân quyền.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(50) UNIQUE | Mã vai trò tiếng Anh (vd `admin`, `pur_manager`), bất biến sau khi tạo |
| `name` | VARCHAR(100) | Tên hiển thị tiếng Việt |
| `description` | VARCHAR(255) | Mô tả ngắn |
| `sort_order` | INT | Thứ tự hiển thị trên màn Phân quyền; người quản trị kéo thả để sắp xếp (CR-172) |

**Logic chính:**
- Vai trò mới tạo ra nhận `sort_order = max_hiện_có + 1` để tự động xếp cuối danh sách, không nhảy lên đầu.
- Sắp xếp luôn kết hợp `sort_order ASC, id ASC` để hai vai trò cùng số không đảo vị trí.
- Không cho xoá vai trò có `code = 'admin'` hoặc `'administrator'` (không phân biệt hoa thường).
- Không cho xoá vai trò còn đang được gán cho tài khoản nào (kiểm tra `tab_user_role`).
- Xoá vai trò kéo theo xoá toàn bộ `tab_permission` và `tab_user_scope` của vai trò đó, rồi gọi `perm_cache_clear()`.

---

## `tab_permission` — Quyền chi tiết (Lớp A — trục vai trò × hành động)

Mỗi dòng là ma trận quyền của một vai trò trên một đối tượng chức năng (`entity`). Lưu cờ boolean cho từng hành động (trục X) và phạm vi hàng dữ liệu mặc định của vai trò (trục Y-mặc-định). Trục Y cá nhân hoá được lưu thêm ở `tab_user_scope`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `role_id` | BIGINT | Trỏ tới `tab_role.id` |
| `entity` | VARCHAR(50) | Mã đối tượng chức năng (vd `purchase_request`, `supplier`) |
| `can_read` | BOOLEAN | Được đọc danh sách và chi tiết |
| `can_create` | BOOLEAN | Được tạo mới |
| `can_write` | BOOLEAN | Được sửa |
| `can_delete` | BOOLEAN | Được xoá |
| `can_approve` | BOOLEAN | Được duyệt |
| `can_cancel` | BOOLEAN | Được huỷ |
| `can_print` | BOOLEAN | Được in / xuất phiếu |
| `can_export` | BOOLEAN | Được xuất CSV/Excel |
| `scope` | VARCHAR(10) | Phạm vi mặc định của vai trò: `own` / `assigned` / `proc` / `dept` / `company` / `all` |

**Logic chính:**
- `scope` của vai trò là phạm vi MẶC ĐỊNH cho người giữ vai trò đó; `tab_user_scope` có thể thu hẹp hoặc mở rộng thêm theo từng người.
- Khi kiểm tra quyền: `require(entity, action)` xem `can_<action>` trong tất cả vai trò của người dùng; đủ một vai trò có quyền là thông.
- Khi lọc dữ liệu: `apply_scope(query, Model, entity, user, profile)` tính union phạm vi của tất cả vai trò người dùng có quyền `read` trên entity đó.
- Mọi entity trong `ENTITIES` phải được khai báo trong `SCOPE_FIELDS` ở `scoping.py`; thiếu khai báo thì `apply_scope` chặn hoàn toàn (trả `false()`) thay vì để lọt tất cả.
- `set_permissions` xoá sạch và ghi lại toàn bộ quyền của vai trò trong một lần gọi, sau đó gọi `perm_cache_clear()`.
- Cache hồ sơ quyền (`_PERM_CACHE`) sống 60 giây; mọi thao tác thay đổi vai trò/quyền/gán vai trò phải chủ động gọi `perm_cache_clear()`.

---

## `tab_employee` — Hồ sơ nhân sự

Lưu thông tin nhân viên, là bản ghi gốc của tổ chức. Tài khoản đăng nhập (`tab_user`) liên kết ngược vào đây qua `tab_user.employee_id`. Phòng ban chính lưu trong `department_id`; phòng ban kiêm nhiệm bổ sung lưu ở `tab_employee_department`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(25) UNIQUE | Mã nhân viên, duy nhất trong hệ thống |
| `full_name` | VARCHAR(255) | Họ tên đầy đủ |
| `email` | VARCHAR(255) | Email công ty — đồng bộ sang `tab_user.email` khi giá trị thay đổi |
| `phone` | VARCHAR(25) | Số điện thoại |
| `company_id` | BIGINT | Trỏ tới `tab_company.id` — pháp nhân chủ quản |
| `department_id` | BIGINT | Trỏ tới `tab_department.id` — **phòng ban chính**; khớp với `is_primary = True` trong `tab_employee_department` |
| `position` | VARCHAR(100) | Vị trí / chức vụ (chữ tự do, không phân quyền) |
| `role_name` | VARCHAR(100) | Không còn dùng (CR-022); giữ lại để không mất dữ liệu cũ — không sao chép sang mã mới |
| `status` | VARCHAR(50) | Mã trạng thái nhân sự tiếng Anh (B-03): `official` / các mã trong `EMPLOYEE_STATUS`; nhãn tiếng Việt lấy qua property `status_label` |
| `is_active` | BOOLEAN | Đang làm việc hay đã nghỉ |

**Logic chính:**
- Ảnh đại diện nhân sự KHÔNG lưu riêng: property `avatar` đọc từ `tab_user.avatar` qua relationship `user` — một nguồn dữ liệu duy nhất.
- Khi email nhân sự thay đổi, service đồng bộ sang `tab_user.email` nếu tài khoản đang để email rỗng hoặc email khớp email cũ — không đụng vào `handle` admin/test.
- `status` lưu mã tiếng Anh từ `EMPLOYEE_STATUS`; property `status_label` dịch ngược sang tiếng Việt để xuất CSV và hiển thị; mã lạ trả chuỗi rỗng (không bịa nhãn).
- `role_name` (cột cũ) không còn có tác dụng phân quyền; quyền chỉ đi qua `tab_user_role`.

---

## `tab_employee_department` — Nhân sự kiêm nhiệm phòng ban (CR-167)

Bảng mở rộng cho phép một nhân sự thuộc nhiều phòng ban (kiêm nhiệm). Bổ sung cho `tab_employee.department_id` (phòng chính), không thay thế. Đây là bảng nhạy về quyền: thêm phòng cho ai là mở rộng tầm nhìn dữ liệu của họ theo phạm vi `dept`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `employee_id` | BIGINT | Trỏ tới `tab_employee.id` |
| `department_id` | BIGINT | Trỏ tới `tab_department.id` |
| `is_primary` | BOOLEAN | `True` = phòng chính, luôn khớp với `tab_employee.department_id`; đúng một dòng mỗi nhân sự |

**Logic chính:**
- Ràng buộc duy nhất `(employee_id, department_id)` — không cho khai trùng một phòng hai lần.
- `dat_phong_ban()` là điểm duy nhất ghi cả hai nơi (`department_id` và `is_primary`) để chúng không lệch nhau.
- Tầm nhìn theo phạm vi `dept` trong `apply_scope` bao gồm TẤT CẢ phòng trong bảng này (kể cả phòng không phải chính), không chỉ phòng chính — đây là mục đích chính của bảng.
- Chốt chặn ghi dữ liệu nằm ở `employee/department_service.py`; không mở thêm cổng vào trực tiếp.

---

## `tab_department` — Phòng ban

Đơn vị tổ chức nội bộ, có phân cấp qua `parent`. Phòng ban có thể thuộc nhiều pháp nhân (mô tả ở `tab_department_company`). `Department.company_id` là pháp nhân gốc; dùng cho mã Thu mua cũ.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(25) UNIQUE | Mã phòng ban |
| `name` | VARCHAR(255) | Tên phòng ban |
| `issue_code` | VARCHAR(20) | Mã đi vào số hiệu văn bản (chỉ chữ và số, vd `NS` trong `08/2026/TB-NS-DEGO`); khác `code` |
| `kind` | SMALLINT | Phân loại: `1` = phòng chức năng, `2` = đơn vị kinh doanh, `3` = ban dự án |
| `company_id` | BIGINT | Trỏ tới `tab_company.id` — pháp nhân gốc |
| `parent` | BIGINT | Trỏ tới `tab_department.id` phòng cấp trên; `0` = phòng gốc |
| `manager_id` | BIGINT | Trỏ tới `tab_employee.id` — trưởng bộ phận, chọn cứng |
| `is_active` | BOOLEAN | Đang hoạt động |

**Logic chính:**
- `issue_code` KHÔNG đổi được khi đã cấp số văn bản; thay đổi làm số hiệu cũ mất đồng nhất.
- Property `manager_name` đọc từ relationship `manager` sang `tab_employee`; trả `None` nếu chưa khai.
- Khi cần trưởng phòng tại một pháp nhân cụ thể, tra `tab_department_company.manager_employee_id` thay vì `manager_id`.

---

## `tab_department_company` — Phòng ban tại pháp nhân (A06)

Một phòng ban có thể hiện diện ở nhiều pháp nhân (ví dụ phòng Kế toán dùng chung toàn tập đoàn). Bảng này là nguồn dữ liệu đầy đủ cho trường hợp đó; `tab_department.company_id` và `manager_id` giữ giá trị pháp nhân gốc để mã cũ không gãy.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `department_id` | BIGINT FK → `tab_department` | Phòng ban, xoá cascade |
| `company_id` | BIGINT FK → `tab_company` | Pháp nhân, xoá cascade |
| `manager_employee_id` | BIGINT FK → `tab_employee` | Trưởng phòng tại pháp nhân này; `NULL` nếu dùng chung trưởng phòng gốc |
| `issue_code_override` | VARCHAR(20) | Mã số hiệu riêng tại pháp nhân này; rỗng thì lấy `Department.issue_code` |
| `is_active` | BOOLEAN | Phòng có đang hoạt động tại pháp nhân này |

**Logic chính:**
- Ràng buộc duy nhất `(department_id, company_id)` — một phòng không khai hai lần cho cùng pháp nhân.
- Khoá ngoại `ON DELETE CASCADE`: xoá phòng hoặc pháp nhân thì dòng tham chiếu tự xoá.
- `issue_code_override` dùng khi một phòng có mã văn bản khác nhau tại từng pháp nhân.

---

## `tab_company` — Pháp nhân

Đơn vị pháp lý trong tập đoàn: tập đoàn mẹ, công ty thành viên, đơn vị trực thuộc. Có phân cấp qua `parent`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(25) UNIQUE | Mã pháp nhân |
| `name` | VARCHAR(255) | Tên đầy đủ |
| `issue_code` | VARCHAR(20) | Mã đi vào số hiệu văn bản (vd `DEGO` trong `DEGO-QC-012`); cố ý tách khỏi `code`; index |
| `short_name` | VARCHAR(100) | Tên gọi tắt dùng trên thể thức văn bản |
| `level` | SMALLINT | Cấp bậc: `1` = Tập đoàn, `2` = Công ty thành viên, `3` = Đơn vị trực thuộc |
| `tax_code` | VARCHAR(25) | Mã số thuế |
| `address` | TEXT | Địa chỉ |
| `invoice_email` | VARCHAR(255) | Email nhận hóa đơn |
| `parent` | BIGINT | Trỏ tới `tab_company.id` pháp nhân cấp trên; `0` = gốc |
| `legal_representative_id` | BIGINT | Trỏ tới `tab_employee.id` — người đại diện pháp lý |
| `legal_rep_title` | VARCHAR(100) | Chức danh của người đại diện (vd "Tổng Giám đốc") |
| `is_active` | BOOLEAN | Đang hoạt động |

**Logic chính:**
- `issue_code` chỉ chứa chữ và số — KHÔNG để dấu hay khoảng trắng; sau khi cấp số văn bản không đổi được.
- Property `export_tax_code` tự thêm dấu nháy đơn phía trước (vd `'0123456789`) để ngăn Excel hiểu mã số thuế dài là số khoa học.
- Property `legal_rep_name` đọc từ relationship `legal_rep` → `tab_employee.full_name`.

---

## `tab_user_preference` — Tuỳ chọn cá nhân

Lưu cấu hình giao diện và tuỳ chọn riêng của từng người dùng dưới dạng khóa-giá trị. Không gác quyền — người dùng tự sửa phần của mình. Nội dung đi kèm hồ sơ `/api/auth/me`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT | Trỏ tới `tab_user.id` |
| `pref_key` | VARCHAR(64) | Khóa tuỳ chọn (vd `theme`, `table_density`) |
| `pref_value` | TEXT | Giá trị tuỳ chọn (JSON hoặc chuỗi đơn giản) |

**Logic chính:**
- Ràng buộc duy nhất `(user_id, pref_key)` — mỗi người chỉ có một giá trị cho mỗi khóa; upsert khi ghi.
- Thiết kế dạng khóa-giá trị để tránh migration mỗi khi thêm tuỳ chọn giao diện mới.
- KHÔNG lưu dữ liệu nhạy cảm (secret, token) — nội dung đây là public với chính chủ tài khoản.

---

## `tab_setting` — Cấu hình hệ thống

Cấu hình toàn hệ dạng khóa-giá trị. Khác `tab_user_preference` ở chỗ đây là một bộ duy nhất áp cho toàn tổ chức, cần quyền `setting.write` mới đổi được. Secret không lưu ở đây — chỉ có trong `.env`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `skey` | VARCHAR(64) UNIQUE | Khóa cấu hình |
| `svalue` | TEXT | Giá trị (JSON hoặc chuỗi) |

**Logic chính:**
- Khoá `skey` là unique — upsert khi ghi, không cho trùng.
- Toàn bộ secret (JWT_SECRET, VAPID, SMTP password...) nằm trong `.env` của VPS, không vào bảng này.

---

## `tab_audit_log` — Nhật ký thao tác

Ghi lại mọi hành động tạo/sửa/xoá trên các đối tượng nghiệp vụ. Chỉ append, không sửa. `created_by` và `created_at` từ `AuditMixin` là thông tin chính của mỗi mục.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `entity` | VARCHAR(50) | Mã đối tượng (vd `purchase_request`, `employee`) |
| `entity_id` | BIGINT | ID dòng bị tác động |
| `action` | VARCHAR(20) | Hành động: `create` / `update` / `delete` |
| `message` | TEXT | Mô tả ngắn về thay đổi (JSON diff hoặc ghi chú) |

**Logic chính:**
- Ghi qua `core/audit.py record(...)` — không ghi thủ công từ controller.
- Bảng này KHÔNG tính là "dữ liệu nghiệp vụ" khi kiểm tra trước khi xoá tài khoản — nhật ký giữ nguyên kể cả khi tài khoản bị xoá.
- Không có cơ chế tự xoá hay purge — quản lý thủ công nếu cần.

---

## `tab_db_backup` — Bản sao lưu cơ sở dữ liệu

Mỗi dòng là một lần sao lưu MySQL. File dump (`.sql.gz`) đẩy lên Cloudflare R2; bảng chỉ lưu key và metadata để quản lý. Celery-beat chạy tự động 2 lần/ngày.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `source` | VARCHAR(20) | Nguồn khởi tạo: `auto` (theo lịch Celery) / `manual` (bấm tay) |
| `status` | VARCHAR(20) | Trạng thái: `running` / `success` / `failed` |
| `file_key` | VARCHAR(255) | Key trên R2 (vd `backups/2026-08-28-123456.sql.gz`); rỗng khi chưa xong |
| `size_bytes` | BIGINT | Dung lượng file nén (byte) |
| `message` | TEXT | Thông báo lỗi khi `failed`; rỗng khi thành công |
| `started_at` | DATETIME | Worker bắt đầu chạy |
| `finished_at` | DATETIME | Worker kết thúc |

**Logic chính:**
- Celery-beat tạo dòng `status = running` ngay khi bắt đầu; cập nhật `success/failed` khi xong.
- Retention tự động: giữ N bản mới nhất, cũ hơn thì xoá cả file R2 lẫn dòng bảng này.
- Deploy backend phải build lại cả service `celery-worker` và `celery-beat`; nhánh `celery-worker` cũ là rác.

---

## `tab_file` — File thật trên storage

Mỗi dòng là một file vật lý trên R2 hoặc storage cục bộ. Tách biệt khỏi liên kết để một file có thể gắn vào nhiều record (`tab_file_link`), và dễ dọn file không có link nào tham chiếu.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `filename` | VARCHAR(255) | Tên gốc khi tải lên |
| `file_key` | VARCHAR(500) | Key trên storage (cấu trúc `{env}/{category}/{năm}/{tháng}/{id}-tên`) |
| `url` | VARCHAR(1000) | URL công khai tải về bản gốc |
| `content_type` | VARCHAR(100) | MIME type (vd `image/jpeg`, `application/pdf`) |
| `size` | BIGINT | Dung lượng bản gốc (byte) |
| `sha256` | VARCHAR(64) | Mã băm SHA-256 của nội dung; rỗng nếu tải lên trước khi có cột này |
| `thumb_key` | VARCHAR(500) | Key thumbnail trên storage (CR-193); rỗng nếu không phải ảnh hoặc ảnh nhỏ sẵn |
| `thumb_url` | VARCHAR(1000) | URL thumbnail; rỗng nếu không có — bên đọc fallback về `url` |

**Logic chính:**
- Thumbnail được sinh trong RAM TRƯỚC khi upload bản gốc (`make_thumb_for` gọi trước `upload_fileobj`) vì boto3 đóng fileobj sau khi đẩy xong — gọi sau là luồng đã chết.
- `thumb_key` đặt theo quy tắc `{file_key}.thumb.jpg`; nằm cạnh bản gốc trên storage.
- `sha256` tính bằng cách đọc theo khối 1 MB (tránh nạp hết RAM với file lớn); con trỏ luồng được trả về vị trí 0 sau khi băm để `upload_fileobj` đọc lại đúng.
- Xoá file: phải xoá cả bản gốc lẫn thumbnail trên storage (`_delete_storage_of`), sau đó xoá dòng DB.
- File không có `tab_file_link` nào trỏ vào là "file mồ côi" — có thể dọn định kỳ.

---

## `tab_file_link` — Liên kết file với record nghiệp vụ

Bảng nối file (`tab_file`) với một record cụ thể của bất kỳ chức năng nào. Xoá link không nhất thiết xoá file (file có thể dùng ở nhiều nơi).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `file_id` | BIGINT | Trỏ tới `tab_file.id` |
| `entity` | VARCHAR(50) | Mã chức năng chủ sở hữu liên kết (vd `purchase_order`) |
| `entity_id` | BIGINT | ID record của chức năng đó |
| `purchase_order_id` | BIGINT | Gom bộ chứng từ theo đơn mua hàng (tiện lọc tất cả file của một ĐMH dù đính ở các chứng từ con); `0` nếu không liên quan |
| `doc_type` | VARCHAR(50) | Loại chứng từ đính kèm (cố định trong code, vd `invoice`, `delivery_note`); rỗng = đính kèm thông thường |
| `sort_order` | INT | Thứ tự hiển thị (nhỏ hơn = trước); dùng chủ yếu cho ảnh sản phẩm |

**Logic chính:**
- Thiết kế "entity + entity_id" (polymorphic) cho phép một bảng `tab_file_link` phục vụ mọi chức năng mà không cần bảng nối riêng cho từng chức năng.
- `purchase_order_id` là cột denormalize phục vụ truy vấn gom tài liệu ĐMH — không cần join nhiều tầng.
- Khi xoá record nghiệp vụ, service cần chủ động xoá các `FileLink` và quyết định xem file có còn được link nơi khác không trước khi xoá `StoredFile`.

---

## `tab_import_batch` — Lô import dữ liệu

Mỗi dòng là một lần import (upload file Excel). Lưu cả thông tin file, chế độ chạy (thử hoặc thật), trạng thái và các bộ đếm kết quả.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `module` | SMALLINT | Phân hệ import (`ImportModule`): `1`=Khảo sát, `2`=ĐMH, `10`=Pháp nhân, `11`=Phòng ban, `12`=Nhân sự, `13`=NCC, `14`=SP, `15`=ĐVT, `16`=Phân loại, `17`=Kho, `18`=YCBG, `19`=YCMH |
| `mode` | SMALLINT | `0`=DRY_RUN (chạy thử), `1`=APPLY (ghi thật) |
| `filename` | VARCHAR(255) | Tên file Excel gốc |
| `file_id` | BIGINT | Trỏ tới `tab_file.id` — file .xlsx đã lưu trên storage |
| `file_size` | INT | Dung lượng file (byte) |
| `sheet_info` | TEXT | JSON: tên sheet + số dòng đọc được |
| `status` | SMALLINT | `ImportStatus`: `0`=QUEUED, `1`=RUNNING, `2`=DONE, `3`=FAILED, `4`=REVERTED |
| `total_rows` | INT | Tổng số dòng dữ liệu đọc từ Excel |
| `created_count` | INT | Số dòng tạo mới |
| `updated_count` | INT | Số dòng cập nhật |
| `deleted_count` | INT | Số dòng đánh dấu xoá (cột `__delete__` trong Excel) |
| `skipped_count` | INT | Số dòng bỏ qua |
| `warning_count` | INT | Số cảnh báo (level WARNING) |
| `error_count` | INT | Số lỗi (level ERROR) |
| `review_count` | INT | Số dòng cần rà soát tay (level REVIEW) |
| `error_summary` | TEXT | Tóm tắt lý do khi `status = FAILED` |
| `started_at` | DATETIME | Worker bắt đầu xử lý |
| `finished_at` | DATETIME | Worker kết thúc |

**Logic chính:**
- Cơ chế ba bước: (1) Upload file → tạo batch `DRY_RUN`, worker chạy thử và ghi log không đụng dữ liệu thật; (2) Người dùng xem log rồi xác nhận → `commit_dry_run` tạo batch mới `APPLY` dùng lại đúng file cũ (không upload lại), worker ghi thật + chụp ảnh vào `tab_import_change`; (3) Nếu cần hoàn tác → `status = REVERTED`, phục hồi từ snapshot.
- `add_log` ghi một dòng `tab_import_log` và tự động tăng đếm `warning_count`/`review_count`/`error_count`; level INFO không tính vào các bộ đếm.
- `ImportModule` phân nhóm thành ba nhóm: nghiệp vụ (1-9), danh mục nền (10-17), chứng từ nhiều dòng (18-19).

---

## `tab_import_log` — Chi tiết log từng dòng import

Lưu thông báo, cảnh báo và lỗi của từng dòng trong một lô import. Nhiều dòng cho một `ImportBatch`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `batch_id` | BIGINT | Trỏ tới `tab_import_batch.id` |
| `sheet` | VARCHAR(40) | Tên sheet trong file Excel (vd `3.KS-NCC`) |
| `row_no` | INT | Số dòng trong sheet (để người dùng tra lại file gốc) |
| `level` | SMALLINT | `LogLevel`: `0`=INFO, `1`=WARNING, `2`=REVIEW, `3`=ERROR |
| `category` | VARCHAR(40) | Mã loại vấn đề (danh sách mở, có thể thêm mà không cần migration) |
| `message` | TEXT | Nội dung thông báo (cắt tại 60.000 ký tự) |
| `ref_key` | VARCHAR(120) | Khóa tham chiếu trong file gốc (mã yêu cầu, số HĐ, mã NCC...) |
| `target_code` | VARCHAR(50) | Mã phiếu được tạo/cập nhật (vd `KS00123`, `PO00456`) |
| `raw` | TEXT | JSON vài cột gốc để tra cứu |

**Logic chính:**
- `category` là chuỗi mở (không IntEnum) để có thể thêm loại lỗi mới mà không phá vỡ mã hiện tại.
- Log level `REVIEW` là trung gian: dữ liệu import được nhưng người dùng cần kiểm tra lại bằng mắt.

---

## `tab_import_change` — Ảnh chụp trước khi import ghi thật (để hoàn tác)

Lưu snapshot JSON của phiếu TRƯỚC khi batch `APPLY` sửa, để có thể hoàn tác (revert) về trạng thái cũ nếu cần.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `batch_id` | BIGINT | Trỏ tới `tab_import_batch.id` |
| `survey_id` | BIGINT | ID phiếu khảo sát bị tác động (hoặc ĐMH trong tương lai); `0` nếu chưa dùng |
| `was_new` | SMALLINT | `1` = phiếu do batch này TẠO MỚI → revert là xoá; `0` = phiếu đã có từ trước → revert phục hồi snapshot |
| `snapshot` | TEXT | JSON toàn bộ phiếu + dòng TRƯỚC khi batch sửa; rỗng nếu `was_new = 1` |

**Logic chính:**
- Revert: với `was_new = 1` thì xoá phiếu; với `was_new = 0` thì deserialize snapshot và ghi đè lại phiếu.
- Snapshot lưu đủ dữ liệu để phục hồi mà không cần tái tính — bao gồm cả các dòng con.
- Sau khi revert, batch gốc chuyển sang `status = REVERTED`.

---

## `tab_export_log` — Nhật ký xuất dữ liệu

Ghi lại mỗi lần xuất CSV/Excel của người dùng. Chỉ lưu metadata — không lưu nội dung file để tránh phình dung lượng. File xuất được giữ lại trên storage để tải về đúng ảnh chụp lúc xuất.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `entity` | VARCHAR(50) | Đối tượng được xuất (trùng `ENTITIES`, vd `employee`, `department`) |
| `fmt` | VARCHAR(10) | Định dạng: `csv` hoặc `xlsx` |
| `row_count` | INT | Số dòng trong file xuất |
| `filename` | VARCHAR(255) | Tên file xuất |
| `file_size` | INT | Dung lượng file (byte) |
| `file_id` | BIGINT | Trỏ tới `tab_file.id` — file đã xuất được lưu storage; `0` = không có |
| `filter_summary` | TEXT | Tóm tắt bộ lọc lúc xuất (JSON/text); rỗng = xuất toàn bảng |

**Logic chính:**
- `file_id` trỏ vào `tab_file` để người dùng tải lại đúng bản đã xuất — không sinh lại file vì dữ liệu có thể đã thay đổi.
- `filter_summary` để trống khi xuất toàn bảng; dành sẵn cho khi hỗ trợ xuất theo bộ lọc.

---

## `tab_push_subscription` — Đăng ký nhận Web Push

Mỗi dòng là một thiết bị/trình duyệt đã bật nhận thông báo đẩy (Web Push API). Một người dùng có thể có nhiều dòng (nhiều thiết bị).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT | Trỏ tới `tab_user.id` |
| `endpoint` | TEXT | URL push service (do trình duyệt cấp, dài); dedup ở tầng code, không unique tại DB |
| `p256dh` | VARCHAR(255) | Public key ECDH dùng mã hoá payload |
| `auth` | VARCHAR(255) | Auth secret dùng mã hoá payload |

**Logic chính:**
- VAPID key cặp nằm trong `.env` của VPS (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`); không lưu vào DB.
- Dedup `endpoint` ở tầng service trước khi lưu — cùng một trình duyệt đăng ký lại thì cập nhật dòng cũ, không tạo dòng mới.
- Tài khoản bị xoá thì các dòng đăng ký push xoá theo (service tự dọn trong luồng xoá tài khoản).

---

## Quan hệ trong cụm

```
tab_company (1) ─── (N) tab_department            qua department.company_id
tab_company (1) ─── (N) tab_department_company    qua department_company.company_id
tab_department (1) ─── (N) tab_department_company qua department_company.department_id

tab_company (1) ─── (N) tab_employee              qua employee.company_id
tab_department (1) ─── (N) tab_employee           qua employee.department_id  [phòng chính]
tab_employee (1) ─── (N) tab_employee_department  qua employee_department.employee_id
tab_department (1) ─── (N) tab_employee_department qua employee_department.department_id

tab_employee (0..1) ─── (1) tab_user              qua user.employee_id
tab_user (1) ─── (N) tab_user_role                qua user_role.user_id
tab_role (1) ─── (N) tab_user_role                qua user_role.role_id
tab_role (1) ─── (N) tab_permission               qua permission.role_id
tab_user (1) ─── (N) tab_user_scope               qua user_scope.user_id
tab_role (1) ─── (N) tab_user_scope               qua user_scope.role_id

tab_user (1) ─── (N) tab_user_preference          qua user_preference.user_id
tab_user (1) ─── (0..1) tab_file                  qua user.avatar_file_id  [ảnh đại diện]

tab_file (1) ─── (N) tab_file_link                qua file_link.file_id
tab_import_batch (1) ─── (N) tab_import_log       qua import_log.batch_id
tab_import_batch (1) ─── (N) tab_import_change    qua import_change.batch_id
tab_import_batch (1) ─── (0..1) tab_file          qua import_batch.file_id  [file xlsx]
tab_export_log (1) ─── (0..1) tab_file            qua export_log.file_id    [file csv/xlsx]
```

Lưu ý: phần lớn quan hệ trong cụm này KHÔNG có khóa ngoại cứng ở cấp MySQL — ràng buộc toàn vẹn được giữ ở tầng service Python. Ngoại lệ có khóa ngoại thật: `tab_department_company.department_id` → `tab_department`, `tab_department_company.company_id` → `tab_company`, `tab_department_company.manager_employee_id` → `tab_employee` (đều với `ON DELETE` rõ ràng).
