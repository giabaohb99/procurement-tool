# Thông báo và Trang cá nhân

Tài liệu này mô tả hai chức năng liên quan đến người dùng cá nhân:

- **Phần I — Hệ thống thông báo**: chuông thông báo trên thanh tiêu đề, trang `/notifications`, API quản lý thông báo, và cơ chế sinh thông báo tự động.
- **Phần II — Trang cá nhân `/me`**: xem thông tin tài khoản, đổi mật khẩu, và danh sách việc cần làm.

---

## Phần I: Hệ thống thông báo

### Mục đích

Cung cấp kênh thông báo nội bộ (in-app) giúp người dùng nắm trạng thái chứng từ liên quan đến họ mà không cần rời khỏi màn hình. Không gửi email cho các sự kiện workflow thông thường — email chỉ dùng cho cấp tài khoản và đặt lại mật khẩu.

Đường dẫn: Chuông trên thanh tiêu đề (mọi trang), `/notifications` (trang xem toàn bộ).

### Vai trò tham gia

Tất cả người dùng đã đăng nhập đều nhận và quản lý thông báo của chính mình. Không có phân quyền riêng cho entity `notification` — hệ thống tự động cô lập theo `user_id`.

---

### A. Chuông thông báo (dropdown)

Chuông hiển thị trên thanh tiêu đề, tự làm mới mỗi **20 giây**.

#### 1. Badge số

- Hiển thị tổng `unread` (thông báo chưa đọc) + `danger` (cảnh báo hệ thống từ `/api/alerts`).
- Giới hạn hiển thị: `99+` khi vượt 99.
- Khi badge tăng so với lần tải trước → phát âm thanh hai nốt "ding" (Web Audio API, không cần file).

#### 2. Dropdown

Mở khi bấm chuông; đóng khi bấm ra ngoài.

| Thành phần | Mô tả |
|---|---|
| Tab "Tất cả" | Hiển thị tối đa 8 thông báo gần nhất (mọi trạng thái) |
| Tab "Chưa đọc" | Hiển thị tối đa 8 thông báo chưa đọc gần nhất |
| Mỗi dòng thông báo | Icon + tiêu đề + nội dung + thời gian (múi giờ VN, +7 UTC) |
| Nền dòng | Xanh nhạt (`#eff6ff`) = chưa đọc; trắng = đã đọc |
| Gộp trùng | Nhiều thông báo cùng chứng từ (cùng `link`) gộp thành 1 dòng, hiển thị nhãn `· N cập nhật` màu teal |

#### 3. Nút thao tác ở chân dropdown

| Nút | Điều kiện hiển thị | Hành động |
|---|---|---|
| Đánh dấu đã đọc | `unread > 0` | Gọi `POST /api/notifications/read-all` |
| Xóa đã đọc | Luôn hiển thị | Gọi `DELETE /api/notifications/read` |
| Xem tất cả → | Luôn hiển thị | Điều hướng đến `/notifications` |

#### 4. Khu "Cảnh báo"

Phía dưới danh sách thông báo, hiển thị thêm các cảnh báo hệ thống (công nợ quá hạn, hàng giao trễ, hợp đồng sắp hết hạn) từ `/api/alerts`. Cảnh báo không có trạng thái đọc/chưa đọc — chỉ điều hướng khi bấm.

---

### B. Trang `/notifications`

Trang xem toàn bộ thông báo, hỗ trợ lọc, tìm kiếm, phân trang và xóa.

#### Bộ lọc & tìm kiếm

| Trường | Mô tả |
|---|---|
| Tab Trạng thái | "Tất cả" hoặc "Chưa đọc" — đổi tab nạp lại ngay |
| Ô tìm kiếm | Tìm theo tiêu đề hoặc nội dung thông báo; debounce 350 ms |

#### Danh sách thông báo

Mỗi dòng hiển thị: icon (màu teal = chưa đọc, xám = đã đọc), tiêu đề (đậm = chưa đọc), nội dung, thời gian (múi giờ VN). Bấm dòng → đánh dấu đã đọc rồi điều hướng đến `link` của thông báo.

#### Thao tác trên từng dòng

| Nút | Điều kiện | Hành động |
|---|---|---|
| ✓ (Đánh dấu đã đọc) | Dòng chưa đọc | `POST /api/notifications/{id}/read` |
| Thùng rác (Xóa) | Mọi dòng | `DELETE /api/notifications/{id}` (xác nhận không bắt buộc) |

#### Thao tác hàng loạt (đầu trang)

| Nút | Điều kiện | Hành động |
|---|---|---|
| Đánh dấu đã đọc tất cả | `unread > 0` | `POST /api/notifications/read-all` |
| Xóa đã đọc | Luôn hiển thị | `DELETE /api/notifications/read` (có hộp thoại xác nhận) |

#### Phân trang

Component `Pagination` tiêu chuẩn; mặc định 20 dòng/trang, tối đa 100.

---

### C. API thông báo

Tất cả endpoint đều lọc theo `user_id` của người đang đăng nhập — không xem/sửa thông báo của người khác.

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/notifications` | Danh sách thông báo (xem bên dưới) |
| `POST` | `/api/notifications/{id}/read` | Đánh dấu 1 thông báo đã đọc |
| `POST` | `/api/notifications/read-all` | Đánh dấu tất cả thông báo chưa đọc là đã đọc |
| `DELETE` | `/api/notifications/{id}` | Xóa 1 thông báo |
| `DELETE` | `/api/notifications/read` | Xóa toàn bộ thông báo đã đọc |

#### `GET /api/notifications` — tham số truy vấn

| Tham số | Kiểu | Mô tả |
|---|---|---|
| `page` | int (mặc định 1) | Trang hiện tại |
| `page_size` | int (mặc định 20, tối đa 100) | Số dòng mỗi trang |
| `unread` | `true` / bỏ qua | Chỉ lấy thông báo chưa đọc |
| `q` | string | Tìm kiếm trong `title` và `body` (LIKE) |

#### `GET /api/notifications` — dữ liệu trả về

```json
{
  "unread": 3,
  "total": 47,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 101,
      "title": "[Đã duyệt] PYC00123",
      "body": "Yêu cầu mua hàng PYC00123 của bạn đã được phê duyệt.",
      "link": "/purchase-requests/42",
      "is_read": false,
      "at": "2026-07-13T08:30:00"
    }
  ]
}
```

- `unread`: tổng thông báo chưa đọc của user (không phụ thuộc bộ lọc hiện tại).
- `total`: tổng theo bộ lọc đang áp dụng (dùng cho phân trang).
- `at`: thời điểm tạo (UTC naive, frontend tự chuyển sang +7 VN bằng `fmtDateTime`).

#### Tự dọn thông báo cũ

Mỗi lần gọi `GET /api/notifications`, hệ thống tự xóa thông báo **đã đọc** của user đó có `created_at` cũ hơn **90 ngày** (chặn phình bảng `tab_notification`). Thông báo chưa đọc không bao giờ bị xóa tự động.

---

### D. Sinh thông báo — `trigger_notification`

Hàm `trigger_notification` được các controller gọi sau mỗi thao tác thay đổi trạng thái chứng từ. Hàm chạy đồng bộ (không background task) và commit ngay vào DB.

#### Loại chứng từ được hỗ trợ

| `doc_type` | Nhãn hiển thị |
|---|---|
| `purchase_request` | Yêu cầu mua hàng |
| `survey_request` | Phiếu khảo sát |
| `purchase_order` | Đơn mua hàng |
| `payment_request` | Đề nghị thanh toán |

#### Nội dung thông báo theo sự kiện

| Sự kiện (`event`) | Tiêu đề | Nội dung |
|---|---|---|
| `pr_submitted` | `[Yêu cầu phê duyệt] PYC {code}` | "Có một yêu cầu mua hàng mới … cần bạn phê duyệt." |
| `pr_approved` | `[Đã duyệt] PYC {code}` | "Yêu cầu mua hàng … đã được phê duyệt." |
| `pr_rejected` | `[Từ chối] PYC {code}` | "Yêu cầu mua hàng … đã bị từ chối phê duyệt." |
| `survey_submitted` | `[Yêu cầu phê duyệt] Khảo sát {code}` | "Có một phiếu khảo sát mới … cần bạn phê duyệt." |
| `survey_approved` | `[Đã duyệt] Khảo sát {code}` | "Phiếu khảo sát … đã được phê duyệt." |
| `survey_rejected` | `[Từ chối] Khảo sát {code}` | "Phiếu khảo sát … đã bị từ chối phê duyệt." |
| Khác (fallback) | `{Nhãn loại} {code}` | `"{Nhãn loại} {code} {động từ}."` (ví dụ: "Đơn mua hàng PO00001 đã được duyệt.") |

Nếu `is_urgent=True` → tiêu đề thêm tiền tố `[GẤP]`.

Động từ fallback lấy từ phần cuối của `event` (cách `_`) theo bảng: `submitted` → "đã được gửi duyệt", `approved` → "đã được duyệt", `rejected` → "đã bị từ chối", `cancelled` → "đã bị hủy", `completed` → "đã hoàn thành", `paid` → "đã ghi nhận thanh toán".

#### Người nhận theo sự kiện

| Sự kiện | Người nhận |
|---|---|
| `pr_submitted` | Trưởng bộ phận của phòng ban người yêu cầu (theo `Department.manager_id`). Nếu chưa gán trưởng phòng → không gửi ai. |
| `survey_submitted` | Người có quyền `approve` trên entity `survey` (Quản lý / Admin thu mua). |
| `pr_approved` | Người tạo YCMH + tất cả người thuộc vai trò `pur_manager` và `pur_admin`. |
| Các sự kiện còn lại | Người tạo chứng từ (`creator_id`). |

Danh sách người nhận được khử trùng (mỗi `user_id` chỉ nhận 1 thông báo).

#### Gộp sự kiện (coalescing)

Trước khi tạo thông báo mới, hàm kiểm tra: nếu người nhận đã có **1 thông báo chưa đọc** cùng `link` trong vòng **5 phút** gần đây → cập nhật thông báo đó (tiêu đề, nội dung, `created_at`) thay vì tạo mới. Mục đích: tránh spam khi nhiều sự kiện liên tiếp xảy ra trên cùng 1 chứng từ (ví dụ submit → approve trong vài giây).

---

### E. Model dữ liệu

Bảng: `tab_notification`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | BigInteger PK | Khóa chính tự tăng |
| `user_id` | BigInteger | ID người nhận (có index) |
| `title` | String(255) | Tiêu đề thông báo |
| `body` | Text | Nội dung thông báo |
| `link` | String(500) | Đường dẫn nội bộ (ví dụ `/purchase-requests/42`) |
| `is_read` | Boolean | `False` = chưa đọc (mặc định) |
| `created_at` | DateTime | Thời điểm tạo (UTC) — kế thừa từ `AuditMixin` |

---

## Phần II: Trang cá nhân `/me`

### Mục đích

Cho phép người dùng xem thông tin tài khoản, đổi mật khẩu và theo dõi toàn bộ việc cần xử lý của mình (phân trang đầy đủ, không bị giới hạn 5 mục như khối Dashboard).

Đường dẫn: `/me` (mặc định tab Thông tin cá nhân), `/me?tab=tasks` (tab Việc cần làm).

### Vai trò tham gia

Tất cả người dùng đã đăng nhập. Không có phân quyền riêng — thông tin và việc cần làm được lọc theo đúng quyền + phạm vi dữ liệu của người đang đăng nhập.

---

### A. Tab Thông tin cá nhân

Gọi `GET /api/auth/me` khi trang tải. Hiển thị các trường sau (chỉ đọc):

| Nhãn | Trường nguồn | Mô tả |
|---|---|---|
| Họ và tên | `full_name` (từ `Employee`) | Tên đầy đủ của nhân sự gắn với tài khoản |
| Mã nhân viên | `emp_code` (từ `Employee.code`) | Hiển thị `—` nếu chưa gắn nhân sự |
| Email | `email` (từ `User`) | Email đăng nhập |
| Số điện thoại | `phone` (từ `Employee`) | Hiển thị `—` nếu trống |
| Phòng ban | `department_name` (từ `Employee`) | Hiển thị `—` nếu trống |
| Chức vụ | `position` hoặc `role_name` (từ `Employee`) | Ưu tiên `position`, fallback sang `role_name`; hiển thị `—` nếu cả hai trống |

Nút "Thông báo" ở đầu trang → điều hướng sang `/notifications`.

#### API: `GET /api/auth/me`

- Không nhận tham số.
- Trả về: `id`, `email`, `employee_id`, `emp_code`, `company_id`, `full_name`, `avatar`, `phone`, `department_name`, `role_name`, `position`, `permissions` (ma trận quyền đầy đủ của user).

---

### B. Đổi mật khẩu (trong Tab Thông tin cá nhân)

Form đổi mật khẩu nằm cùng tab "Thông tin cá nhân", phía bên phải thông tin tài khoản.

#### Trường nhập

| Trường | Mô tả |
|---|---|
| Mật khẩu hiện tại | Bắt buộc; dùng để xác minh trước khi đổi |
| Mật khẩu mới | Bắt buộc; tối thiểu 6 ký tự |
| Xác nhận mật khẩu mới | Phải trùng khớp với "Mật khẩu mới" |

Nút "Đổi mật khẩu" bị vô hiệu hóa khi ô mật khẩu hiện tại hoặc mật khẩu mới còn trống.

#### Luồng xử lý

1. Frontend kiểm tra sơ bộ: `new_password.length >= 6` và `new_password === confirm_password`; thất bại → hiển thị lỗi toast, không gửi API.
2. Gọi `POST /api/auth/change-password` với `{old_password, new_password}`.
3. Server xác minh: mật khẩu cũ đúng không → mật khẩu mới ≥ 6 ký tự → mật khẩu mới không trùng mật khẩu cũ. Thất bại → HTTP 400 kèm thông báo lỗi.
4. Thành công → server cập nhật `password_hash`, trả `200`.
5. Frontend hiển thị toast "Đã đổi mật khẩu — vui lòng đăng nhập lại", sau **1 giây** tự động gọi `logout()` và điều hướng về `/login`.

#### API: `POST /api/auth/change-password`

- Yêu cầu: đăng nhập (Bearer token).
- Body: `{ "old_password": "...", "new_password": "..." }`
- Lỗi có thể trả về:

| Mã HTTP | Thông báo lỗi |
|---|---|
| 400 | "Mật khẩu hiện tại không đúng" |
| 400 | "Mật khẩu mới phải từ 6 ký tự trở lên" |
| 400 | "Mật khẩu mới không được trùng mật khẩu cũ" |

---

### C. Tab Việc cần làm

Danh sách đầy đủ (phân trang) tất cả công việc đang chờ người dùng xử lý, lọc theo đúng quyền và phạm vi dữ liệu. Dashboard hiển thị tối đa 5 mục mỗi loại kèm nút "Xem tất cả" → `/me?tab=tasks`.

#### Các loại việc cần làm

| `type` | Nhãn | Nguồn dữ liệu | Điều kiện lấy |
|---|---|---|---|
| `pr` | YCMH chờ duyệt | `PurchaseRequest` | `status = "submitted"` |
| `sr` | Khảo sát chờ duyệt | `SurveyRequest` | `status = "submitted"` |
| `po` | ĐMH chờ duyệt | `PurchaseOrder` | `status = "submitted"` |
| `late` | Giao hàng trễ | `PODelivery` | `received_qty <= 0` và `expected_date` (hoặc `promised_date`) < hôm nay |
| `payable` | Công nợ quá hạn | `Payable` | `status != "Đã TT"`, `remaining > 0`, `due_date < hôm nay` |

Mỗi loại chỉ được đưa vào danh sách nếu người dùng có quyền `read` trên entity tương ứng. Dữ liệu đã qua `apply_scope` (phạm vi của user).

#### Bộ lọc & tìm kiếm

| Trường | Mô tả |
|---|---|
| Dropdown "Loại việc" | Lọc theo `type`; hiển thị số lượng từng loại trong ngoặc. Chọn "Tất cả" để xem tổng. |
| Ô tìm kiếm | Tìm trên `code + title + subtitle`; debounce 350 ms |

Lưu ý: số lượng trong dropdown được tính trên **toàn bộ danh sách** trước khi áp lọc loại và tìm kiếm (để hiển thị đúng ngay cả khi đang lọc).

#### Hiển thị mỗi dòng

- Icon màu theo `type` (xanh dương / teal / tím / cam / đỏ).
- Nhãn loại + mã chứng từ + tên/mô tả.
- Dòng phụ: thông tin bổ sung (người yêu cầu, hạn giao, số dư nợ…).
- Ngày tham chiếu (ngày yêu cầu / hạn giao / hạn trả).
- Bấm dòng → điều hướng đến `link` của việc.

#### Phân trang

Component `Pagination` tiêu chuẩn; mặc định 20 dòng/trang, tối đa 100.

#### API: `GET /api/dashboard/tasks`

| Tham số | Kiểu | Mô tả |
|---|---|---|
| `page` | int (mặc định 1) | Trang hiện tại |
| `page_size` | int (mặc định 20, tối đa 100) | Số dòng mỗi trang |
| `type` | string | Lọc theo loại: `pr`, `sr`, `po`, `late`, `payable` |
| `q` | string | Tìm kiếm tự do |

Dữ liệu trả về:

```json
{
  "total": 12,
  "by_type": { "pr": 3, "late": 5, "payable": 4 },
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "type": "pr",
      "label": "YCMH chờ duyệt",
      "code": "PYC00045",
      "title": "Mua văn phòng phẩm",
      "subtitle": "Nguyễn Văn A",
      "date": "2026-07-10",
      "link": "/purchase-requests/45"
    }
  ]
}
```

- `by_type`: đếm từng loại trên toàn bộ danh sách (trước khi lọc `type`/`q`) — dùng để hiển thị số trong dropdown.
- `total`: tổng **sau** khi lọc (dùng cho phân trang).

---

### D. Quyền thao tác

Không có entity RBAC riêng cho trang `/me`. Quyền áp dụng gián tiếp:

| Chức năng | Điều kiện |
|---|---|
| Xem thông tin cá nhân & đổi mật khẩu | Đã đăng nhập (không cần quyền riêng) |
| Thấy loại việc `pr` trong Tab Việc cần làm | Có `purchase_request:read` |
| Thấy loại việc `sr` | Có `survey_request:read` |
| Thấy loại việc `po` và `late` | Có `purchase_order:read` |
| Thấy loại việc `payable` | Có `payable:read` |
