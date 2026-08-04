# Phiếu hỗ trợ (Ticket)

Tài liệu mô tả phân hệ **Hỗ trợ nội bộ** — kênh để mọi nhân viên gửi yêu cầu hỗ trợ (kỹ thuật, tài khoản, quy trình, dữ liệu…) và trao đổi qua lại với nhóm Hỗ trợ ngay trong ứng dụng, thay cho email/chat rời rạc.

Đường dẫn: `/tickets` (danh sách "Yêu cầu hỗ trợ của tôi"), `/tickets/:id` (chi tiết một phiếu).

> **Trạng thái triển khai:** phân hệ này bật ở **dev**, **tắt ở prod** (chờ nghiệm thu). Điều khiển bằng build arg `VITE_FEATURE_TICKET` — prod mặc định `off` (ẩn cả menu lẫn route), dev mặc định `on`. Bật ở prod: đặt `VITE_FEATURE_TICKET=on` trong `.env` rồi build lại `web`.

Lối vào: menu **"Hỗ trợ"** ở sidebar (nhóm Tổng quan) **và** mục **"Hỗ trợ"** trong menu thả xuống ở avatar (góc phải, thay cho "Hướng dẫn sử dụng" — HDSD vẫn còn ở sidebar). Vào từ menu avatar sẽ mở thẳng **màn hình tạo phiếu riêng** (`/tickets/new`) và **tự ghi lại trang đang đứng** (xem §Trang lúc tạo). Danh sách "Yêu cầu hỗ trợ của tôi" (`/tickets`) và form tạo (`/tickets/new`) là hai màn hình tách biệt.

---

## 1. Mục đích & phạm vi (v1 — MVP)

- **Định tuyến tập trung**: mọi phiếu về **một nhóm Hỗ trợ** duy nhất. Trường "Bộ phận / Nhóm" chỉ là **nhãn phân loại** để nhóm Hỗ trợ dễ lọc, KHÔNG định tuyến tự động theo phòng ban.
- **Người gửi**: **mọi nhân viên đã đăng nhập** đều mở được phiếu và **chỉ thấy phiếu của chính mình**.
- **Nội dung MVP**: chủ đề + bộ phận/nhóm + mức ưu tiên + luồng tin nhắn qua lại + trạng thái + tệp đính kèm + chuông thông báo (in-app + Web Push + email workflow khi bật).

---

## 2. Vai trò tham gia

| Nhóm | Cách nhận biết (backend) | Quyền trong phân hệ |
|---|---|---|
| **Người gửi** (mọi nhân viên) | grant `ticket` scope `own` (không có `delete`) | Mở phiếu, xem/nhắn trên **phiếu của mình**, đính kèm, tự **đóng / mở lại** phiếu của mình |
| **Nhóm Hỗ trợ** | grant `ticket` scope `dept/company/all` (có `delete`) — vai trò `support`, `pur_manager`, `admin`/`ADMINISTRATOR` | Xem **mọi phiếu**, trả lời (đánh dấu tin của mình là "Hỗ trợ"), đổi **mọi trạng thái**, nhận/gán người xử lý |

**Phía frontend** không có thông tin scope trong ma trận quyền, nên dùng quyền `ticket:delete` làm **proxy nhận biết handler** (chỉ nhóm Hỗ trợ/quản trị có `delete`). Backend mới là nơi thực thi thật (`_is_handler` xét scope grant).

Vai trò **`support` ("Nhân viên hỗ trợ")** được thêm vào seed với quyền `ticket` = `read/create/write/delete` scope `all`. Gán vai trò này cho nhân sự phụ trách hỗ trợ. Nếu **chưa gán ai**, thông báo phiếu mới rơi về nhóm quản trị (`admin`/`ADMINISTRATOR`) để không thất lạc.

---

## 3. Danh sách phiếu — `/tickets`

Tiêu đề **"Yêu cầu hỗ trợ của tôi"**. Nút **"Mở phiếu hỗ trợ"** ở góc phải.

### Bộ lọc & tìm kiếm

| Trường | Mô tả |
|---|---|
| Tab Trạng thái | Tất cả / Mới / Đang xử lý / Đã trả lời / Đã đóng — đổi tab nạp lại ngay |
| Ưu tiên | Dropdown: Tất cả / Thấp / Trung bình / Cao / Khẩn |
| Ô tìm kiếm | Tìm theo **chủ đề** (`subject`, LIKE); debounce 350 ms |

### Cột bảng

| Cột | Nội dung |
|---|---|
| Chủ đề | Chủ đề phiếu + mã phiếu (`TKddmmyyNN`) ở dòng phụ |
| Bộ phận | Nhãn bộ phận/nhóm |
| Ưu tiên | Badge màu theo mức |
| Trạng thái | Badge màu theo trạng thái |
| Cập nhật | Thời điểm cập nhật gần nhất (giờ VN) |

Bấm một dòng → mở chi tiết `/tickets/:id`. Phân trang bằng component `Pagination` (mặc định 20 dòng/trang).

Người gửi chỉ thấy phiếu của mình (lọc qua `apply_scope`, scope `own` = `created_by`). Nhóm Hỗ trợ thấy toàn bộ.

### Màn hình "Mở phiếu hỗ trợ" (`/tickets/new`)

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| Chủ đề | Có | Tóm tắt vấn đề |
| Bộ phận / Nhóm | — | Chọn từ danh sách cố định (xem §7) |
| Mức ưu tiên | — | Mặc định "Trung bình" |
| Nội dung | — | Mô tả chi tiết; trở thành **tin nhắn đầu tiên** của phiếu |

Tệp đính kèm được thêm **sau khi tạo phiếu** (ở màn chi tiết) — vì hệ thống đính kèm cần `entity_id` của phiếu đã lưu. Gửi thành công → điều hướng thẳng vào chi tiết phiếu.

**Trang lúc tạo (`origin_url`) — hỗ trợ debug.** Khi người dùng bấm "Hỗ trợ" (menu avatar) hoặc điều hướng trong app, `AppLayout` ghi lại **đường dẫn trang đang đứng** vào `sessionStorage` (`support_origin`, bỏ qua các trang `/tickets`). Lúc tạo phiếu, đường dẫn này được gửi kèm (`origin_url`) và **hiển thị nhắc trong form** ("Sẽ đính kèm trang bạn đang gặp vấn đề: …"). Ở màn chi tiết, nhóm Hỗ trợ thấy dòng **"Trang lúc tạo"** là **link bấm được** để nhảy thẳng tới đúng màn hình người dùng gặp lỗi.

---

## 4. Chi tiết phiếu — `/tickets/:id`

Bố cục hai cột:

### Cột trái — Trao đổi & đính kèm

- **Luồng tin nhắn**: mỗi tin hiển thị avatar (chữ cái đầu), tên người gửi, thời gian, nội dung. Tin của **nhóm Hỗ trợ** (`is_staff = true`) căn phải, nền xanh, kèm badge **"Hỗ trợ"**; tin người gửi căn trái, nền trắng. Khung tự cuộn xuống tin mới nhất.
- **Ô trả lời**: textarea + nút Gửi. Phím tắt **Ctrl/⌘ + Enter** để gửi nhanh. Khi phiếu **đã đóng**, ô trả lời ẩn đi (phải mở lại phiếu để tiếp tục).
- **Tệp đính kèm**: dùng component chung `DocumentAttachmentSection` với `entity="ticket"`, kéo-thả trực tiếp, tối đa **10 MB/tệp**. Khóa khi phiếu đã đóng.

### Cột phải — Thông tin & hành động

- **Thông tin phiếu**: mã, bộ phận/nhóm, ưu tiên, trạng thái, người gửi, người xử lý (hoặc "Chưa nhận"), ngày tạo, cập nhật, ngày đóng (nếu có).
- **Hành động** (khác nhau theo vai trò):

| Vai trò | Nút hiển thị |
|---|---|
| Nhóm Hỗ trợ | Đánh dấu **đang xử lý** / **đã trả lời** / **Đóng phiếu**; khi đã đóng → **Mở lại phiếu** |
| Người gửi | **Đóng phiếu** (khi chưa đóng) / **Mở lại phiếu** (khi đã đóng) |

---

## 5. Trạng thái & tự chuyển trạng thái

| Mã | Nhãn | Ý nghĩa |
|---|---|---|
| `open` | Mới | Vừa tạo, chưa ai xử lý |
| `in_progress` | Đang xử lý | Nhóm Hỗ trợ đang xử lý (hoặc người gửi vừa phản hồi tiếp) |
| `answered` | Đã trả lời | Nhóm Hỗ trợ vừa trả lời |
| `closed` | Đã đóng | Đã giải quyết / đóng lại |

Quy tắc tự chuyển (service `add_message` / `set_status`):

- Nhóm Hỗ trợ trả lời → trạng thái = **`answered`**, xóa `closed_at`.
- Người gửi phản hồi khi phiếu đang `answered`/`closed` → trạng thái quay lại **`in_progress`**.
- Đặt trạng thái `closed` → ghi `closed_at`; các trạng thái khác → xóa `closed_at`.
- **Người gửi chỉ được đặt** `closed` (đóng) hoặc `in_progress` (mở lại) trên phiếu của mình; nhóm Hỗ trợ đặt được mọi trạng thái + gán người xử lý.

Mức ưu tiên: `low` (Thấp) · `normal` (Trung bình) · `high` (Cao) · `urgent` (Khẩn).

---

## 6. Thông báo

Dùng helper `_notify` riêng của module (chuông in-app + Web Push nền best-effort + email workflow khi `EMAIL_WORKFLOW_ENABLED`). Người tạo sự kiện không tự nhận thông báo của mình.

| Sự kiện | Người nhận | Tiêu đề / Nội dung |
|---|---|---|
| Tạo phiếu mới | Nhóm Hỗ trợ (`support` + `pur_manager`; fallback quản trị) | `{code} — Phiếu hỗ trợ mới` |
| Hỗ trợ trả lời | Người gửi phiếu | `{code} — Hỗ trợ đã trả lời` |
| Người gửi phản hồi | Người xử lý (nếu đã gán) hoặc nhóm Hỗ trợ | `{code} — Người gửi phản hồi` |
| Đóng phiếu | Hỗ trợ đóng → báo người gửi; người gửi đóng → báo nhóm Hỗ trợ | `{code} — Đã đóng phiếu hỗ trợ` |

Mọi thông báo có `link = /tickets/{id}`.

---

## 7. Bộ phận / Nhóm (nhãn phân loại)

Danh sách cố định ở frontend (không phải bảng danh mục riêng), chỉ để phân loại hiển thị:

- Kỹ thuật / Phần mềm
- Tài khoản & Đăng nhập
- Quy trình mua hàng
- Dữ liệu & Báo cáo
- Khác

---

## 8. API

Prefix: `/api/tickets`. Mọi endpoint yêu cầu đăng nhập; danh sách/chi tiết lọc qua `apply_scope` (người gửi chỉ thấy phiếu của mình).

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/api/tickets` | `ticket:read` | Danh sách (lọc `code/subject/status/priority/department` + phân trang) |
| `GET` | `/api/tickets/{id}` | `ticket:read` + trong phạm vi | Chi tiết kèm toàn bộ tin nhắn |
| `POST` | `/api/tickets` | `ticket:create` | Tạo phiếu (chủ đề, bộ phận, ưu tiên, nội dung) |
| `PATCH` | `/api/tickets/{id}` | chủ phiếu hoặc handler | Sửa chủ đề/bộ phận/ưu tiên (chặn khi đã đóng) |
| `POST` | `/api/tickets/{id}/messages` | chủ phiếu hoặc handler | Gửi tin trả lời (`is_staff` tự suy theo handler) |
| `POST` | `/api/tickets/{id}/status` | handler = mọi trạng thái; chủ phiếu = `closed`/`in_progress` | Đổi trạng thái (+ gán người xử lý nếu handler) |

Đính kèm dùng API chung `/api/attachments` với `entity=ticket` (và `ticket_message` cho tệp theo tin nhắn) — quyền upload gate theo entity cha `ticket` (`write` HOẶC `create`).

---

## 9. Model dữ liệu

**`tab_ticket`** (kế thừa `AuditMixin`: `id`, `created_at/by`, `updated_at/by`):

| Cột | Kiểu | Mô tả |
|---|---|---|
| `code` | String(50), unique | Mã phiếu `TKddmmyyNN` (MAX+1 trong ngày) |
| `subject` | String(255) | Chủ đề |
| `department` | String(255), index | Nhãn bộ phận/nhóm |
| `priority` | String(20), index | `low/normal/high/urgent` |
| `status` | String(30), index | `open/in_progress/answered/closed` |
| `company_id` | BigInteger | Công ty của người gửi (suy từ hồ sơ quyền) |
| `requester_id` | BigInteger | `Employee.id` người gửi (nếu có) |
| `assignee_id` | BigInteger, index | User xử lý (0 = chưa nhận) |
| `origin_url` | String(500) | Đường dẫn trang người gửi đang đứng lúc tạo phiếu (debug) |
| `closed_at` | DateTime, null | Thời điểm đóng |

**`tab_ticket_message`** (kế thừa `AuditMixin`):

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ticket_id` | BigInteger, index | Phiếu cha |
| `body` | Text | Nội dung tin |
| `is_staff` | Boolean | `true` = tin của nhóm Hỗ trợ |

Migration: `d8f1a3c5e7b9_ticket.py` (down_revision `c4d8f1a6b023`).

---

## 10. Phân quyền (RBAC)

Entity mới **`ticket`** ("Phiếu hỗ trợ") thêm vào `ENTITIES`/`ENTITY_LABELS`. `SCOPE_FIELDS["ticket"] = {"company": "company_id", "owner": "created_by"}`.

Seed (`seed.py`):

- Vai trò cơ bản (`employee`, `dept_head`, `company_head`, `pur_staff`, `pur_admin`): `ticket` = `read/create/write` scope **`own`**.
- Vai trò mới **`support`**: `ticket` = `read/create/write/delete` scope **`all`**.
- `pur_manager` nhận `ticket` tự động qua `_PUR_MANAGER_PERMS` (mọi entity trừ hệ thống, scope `all`); `admin`/`ADMINISTRATOR` nhận đủ qua vòng lặp `ENTITIES` trong `run()`.

`seed_standard_roles` là INSERT-only theo `(vai trò, entity)` nên thêm `ticket` vào các vai trò sẵn có sẽ **bổ sung** trên DB đã seed mà không reset cấu hình khác.
