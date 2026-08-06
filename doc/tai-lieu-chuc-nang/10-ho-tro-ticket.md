# Phiếu hỗ trợ (Ticket)

Tài liệu mô tả phân hệ **Hỗ trợ nội bộ** — kênh để mọi nhân viên gửi yêu cầu hỗ trợ (kỹ thuật, tài khoản, quy trình, dữ liệu…) và trao đổi qua lại với nhóm Hỗ trợ ngay trong ứng dụng, thay cho email/chat rời rạc.

Đường dẫn: `/tickets` (màn **quản lý** — chỉ nhóm Hỗ trợ), `/tickets/:id` (chi tiết một phiếu), `/me?tab=tickets` (tab **"Yêu cầu hỗ trợ của tôi"** ở Trang cá nhân).

> **Trạng thái triển khai:** phân hệ này bật ở **dev**, **tắt ở prod** (chờ nghiệm thu). Điều khiển bằng build arg `VITE_FEATURE_TICKET` — prod mặc định `off` (ẩn cả menu lẫn route), dev mặc định `on`. Bật ở prod: đặt `VITE_FEATURE_TICKET=on` trong `.env` rồi build lại `web`.

### Lối vào theo vai trò

| Vai trò | Gửi phiếu | Xem phiếu |
|---|---|---|
| **Nhân viên thường** | Icon **tai nghe** ("Gửi yêu cầu hỗ trợ") trong menu thả xuống ở avatar → mở **popup** ngay tại trang đang đứng; hoặc nút trong tab cá nhân | Trang cá nhân → tab **"Yêu cầu hỗ trợ của tôi"** (`/me?tab=tickets`) |
| **Nhóm Hỗ trợ** | Như trên (popup) | Menu **"Hỗ trợ"** ở sidebar → màn **Quản lý phiếu hỗ trợ** (`/tickets`); phiếu do chính họ gửi vẫn nằm ở tab cá nhân |

Menu sidebar **"Hỗ trợ"** chỉ hiện với nhóm Hỗ trợ (gate bằng `can('ticket','delete')` — xem §2), nhân viên thường **không thấy**. Không còn trang tạo phiếu riêng `/tickets/new`; form tạo là popup dùng chung `components/TicketCreateModal.tsx`.

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

## 3. Ba màn hình của phân hệ

### 3.1. Tab "Yêu cầu hỗ trợ của tôi" — `/me?tab=tickets`

Tab thứ ba ở Trang cá nhân (cạnh "Thông tin cá nhân" và "Việc cần làm"), chỉ hiện khi bật `VITE_FEATURE_TICKET`.

- Gọi `GET /api/tickets?mine=1` → **chỉ phiếu do chính mình gửi** (`created_by = user.id`). Tham số `mine` cần thiết vì người thuộc nhóm Hỗ trợ có scope `all` — không lọc thì tab cá nhân sẽ hiện phiếu của cả công ty.
- Bộ lọc: tab trạng thái (Tất cả / Mới / Đang xử lý / Đã trả lời / Đã đóng).
- Cột: Chủ đề (+ mã phiếu) · Bộ phận · Ưu tiên · Trạng thái · **Người xử lý** ("Chưa nhận" nếu chưa ai nhận) · Cập nhật.
- Nút **"Gửi yêu cầu hỗ trợ"** mở popup tạo phiếu (§3.3). Phân trang 10 dòng/trang.

### 3.2. Màn quản lý — `/tickets` (chỉ nhóm Hỗ trợ)

Tiêu đề **"Quản lý phiếu hỗ trợ"** — toàn bộ phiếu người dùng gửi lên (vẫn qua `apply_scope`).

| Bộ lọc | Mô tả |
|---|---|
| Trạng thái | Tất cả / Mới / Đang xử lý / Đã trả lời / Đã đóng |
| Người xử lý | Tất cả / **Chưa ai nhận** (`assignee=unassigned`) / **Tôi đang xử lý** (`assignee=me`) |
| Ưu tiên | Dropdown: Tất cả / Thấp / Trung bình / Cao / Khẩn |
| Ô tìm kiếm | Tìm theo **chủ đề** (`subject`, LIKE); debounce 350 ms |

Cột: Chủ đề (+ mã phiếu) · **Người gửi** · Bộ phận · Ưu tiên · Trạng thái · **Người xử lý** · Cập nhật · nút **"Nhận"**.

Nút **"Nhận"** chỉ hiện ở dòng **chưa ai nhận và chưa đóng**; bấm → `POST /api/tickets/{id}/assign` với `assignee_id` = chính mình. Bấm vào dòng → mở chi tiết. Phân trang 20 dòng/trang.

### 3.3. Popup "Gửi yêu cầu hỗ trợ" (`components/TicketCreateModal.tsx`)

Mở từ **icon tai nghe** ở menu avatar (mọi trang) hoặc nút trong tab cá nhân. Không còn trang riêng.

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| Chủ đề | Có | Tóm tắt vấn đề (nút Gửi khóa khi để trống) |
| Bộ phận / Nhóm | — | Chọn từ danh sách cố định (xem §7) |
| Mức ưu tiên | — | Dải nút Thấp / Trung bình / Cao / Khẩn, mặc định "Trung bình" |
| Nội dung | — | Mô tả chi tiết; trở thành **tin nhắn đầu tiên** của phiếu. Dán ảnh chụp màn hình thẳng vào ô này bằng **Ctrl/⌘ + V** |
| Tệp đính kèm | — | Kéo-thả / bấm chọn ngay trong popup, nhiều tệp, ≤ **20 MB**/tệp |

**Đính kèm ngay lúc tạo:** file được upload **ngay khi chọn** qua `POST /api/attachments/upload-file` (entity `ticket`) → trả `file_id`, chưa gắn vào phiếu. Danh sách tệp hiện bên dưới, gỡ được bằng nút X. Lúc bấm Gửi, các `file_ids` đi kèm request tạo phiếu và `service.create_ticket` gắn chúng vào phiếu (`_register_files`). Nút Gửi khóa trong lúc đang upload. Vẫn đính kèm thêm được ở màn chi tiết sau đó.

Đóng popup bằng nút X, nút Hủy, phím **Esc** hoặc bấm ra nền. Mỗi lần mở là form trắng. Gửi thành công → điều hướng thẳng vào chi tiết phiếu.

**Trang lúc tạo (`origin_url`) — hỗ trợ debug.** Lúc bấm icon tai nghe, `AppLayout` lấy **đường dẫn trang đang đứng** và truyền vào popup qua prop `originUrl`; popup gửi kèm khi tạo phiếu và **hiển thị nhắc trong form** ("Đính kèm trang bạn đang xem: …"). Ở màn chi tiết, nhóm Hỗ trợ thấy dòng **"Trang lúc tạo"** là **link bấm được** để nhảy thẳng tới đúng màn hình người dùng gặp lỗi.

> Hằng số và badge dùng chung (trạng thái, ưu tiên, danh sách bộ phận) nằm ở `frontend/src/config/ticketMeta.tsx` để 3 màn hình + chi tiết cùng một nguồn.

---

## 4. Chi tiết phiếu — `/tickets/:id`

Bố cục **hai khối xếp dọc** (thông tin trước — trao đổi sau), không còn cột phải:

### Khối trên — Yêu cầu hỗ trợ

- **Đầu khối**: nút "Danh sách", **tiêu đề phiếu** (chủ đề) kèm badge trạng thái + mức ưu tiên, dòng phụ `mã phiếu · người gửi · thời điểm gửi`, và **cụm nút hành động** nằm bên phải (xem bảng dưới).
- **Lưới thông tin**: mã phiếu, bộ phận/nhóm, mức ưu tiên, trạng thái, người gửi, người xử lý (hoặc "Chưa ai nhận"), ngày tạo, cập nhật, ngày đóng (nếu có), trang lúc tạo (link bấm được). Lưới tự xuống dòng theo bề rộng màn hình.
- **Nội dung yêu cầu**: chính là **tin nhắn đầu tiên của người gửi** — được tách khỏi luồng trao đổi và đưa lên đây (kiểu trang issue). Kèm bên dưới là **tệp gửi kèm lúc tạo phiếu** (`entity=ticket`): ảnh xem ngay dạng thumbnail, tệp khác là thẻ bấm để mở/tải.

### Khối dưới — Trao đổi (kiểu nhắn tin)

- **Luồng tin nhắn**: chỉ còn các lượt qua lại thực sự (đã bỏ tin đầu tiên vì nằm ở khối trên). Mỗi tin có avatar (chữ cái đầu), tên người gửi, thời gian, nội dung. Tin của **nhóm Hỗ trợ** (`is_staff = true`) căn phải, nền xanh, kèm badge **"Hỗ trợ"**; tin người gửi căn trái, nền trắng. Ảnh/tệp đính kèm của tin hiển thị **ngay trong bong bóng tin đó**. Khung tự cuộn xuống tin mới nhất. Chưa có lượt nào thì hiện trạng thái rỗng.
- **Ô trả lời gộp chung với đính kèm** — không còn khu upload riêng: một khung duy nhất gồm textarea + nút **kẹp giấy** để chọn tệp + **kéo-thả tệp vào ô** + **dán ảnh chụp màn hình bằng Ctrl/⌘ + V**. Tệp được upload ngay khi chọn (`POST /api/attachments/upload-file` với `entity=ticket_message`), hiện thành chip có nút bỏ, rồi gắn vào tin nhắn qua `file_ids` lúc bấm **Gửi**. Gửi **chỉ tệp không kèm chữ** cũng hợp lệ. Phím tắt **Ctrl/⌘ + Enter**; nút Gửi khóa khi đang tải tệp. Khi phiếu **đã đóng**, cả khung ẩn đi (phải mở lại phiếu để tiếp tục).

### Hành động (khác nhau theo vai trò)

| Vai trò | Nút hiển thị |
|---|---|
| Nhóm Hỗ trợ | **Nhận phiếu** (hoặc "Nhận lại phiếu" nếu người khác đang giữ / "Trả phiếu" nếu chính mình đang giữ); **Đang xử lý** / **Đã trả lời** / **Đóng phiếu**; khi đã đóng → **Mở lại phiếu** |
| Người gửi | **Đóng phiếu** (khi chưa đóng) / **Mở lại phiếu** (khi đã đóng) |

Nút **"Danh sách"** quay về `/tickets` với nhóm Hỗ trợ, về `/me?tab=tickets` với người gửi thường.

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
- **Nhận phiếu** (`assign`) khi phiếu còn `open` → tự chuyển **`in_progress`** (khỏi phải bấm 2 lần). Phiếu đã ở trạng thái khác thì giữ nguyên; **trả phiếu** về hàng chờ không đổi trạng thái.
- **Người gửi chỉ được đặt** `closed` (đóng) hoặc `in_progress` (mở lại) trên phiếu của mình; nhóm Hỗ trợ đặt được mọi trạng thái + gán người xử lý.

Mức ưu tiên: `low` (Thấp) · `normal` (Trung bình) · `high` (Cao) · `urgent` (Khẩn).

---

## 6. Thông báo

Dùng helper `_notify` riêng của module (chuông in-app + Web Push nền best-effort + email workflow khi `EMAIL_WORKFLOW_ENABLED`). Người tạo sự kiện không tự nhận thông báo của mình.

| Sự kiện | Người nhận | Tiêu đề / Nội dung |
|---|---|---|
| Tạo phiếu mới | **Nhóm Hỗ trợ = vai trò `support`** (fallback quản trị nếu chưa gán ai) | `{code} — Phiếu hỗ trợ mới` |
| Hỗ trợ trả lời | Người gửi phiếu | `{code} — Hỗ trợ đã trả lời` |
| Người gửi phản hồi | Người xử lý (nếu đã gán) hoặc nhóm Hỗ trợ | `{code} — Người gửi phản hồi` |
| **Giao phiếu cho người khác** | Người được giao (tự nhận phiếu thì không báo) | `{code} — Bạn được giao phiếu hỗ trợ` |
| Đóng phiếu | Hỗ trợ đóng → báo người gửi; người gửi đóng → báo nhóm Hỗ trợ | `{code} — Đã đóng phiếu hỗ trợ` |

Mọi thông báo có `link = /tickets/{id}`.

**Nhóm nhận việc chỉ gồm vai trò `support`** — Quản lý thu mua (`pur_manager`) đã được **bỏ khỏi** danh sách nhận vì họ không phải người xử lý phiếu (nhận vào chỉ là spam). Vì vậy **phải gán vai trò "Nhân viên hỗ trợ" cho người phụ trách**; chưa gán ai thì phiếu rơi về quản trị (`admin`/`ADMINISTRATOR`) để không mất phiếu.

Email workflow dùng nhãn loại chứng từ **"Phiếu hỗ trợ"** (`doc_type = ticket`).

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
| `GET` | `/api/tickets` | `ticket:read` | Danh sách (lọc `code/subject/status/priority/department` + phân trang). Tham số riêng: `mine=1` (chỉ phiếu mình gửi), `assignee=unassigned\|me\|<user_id>` |
| `GET` | `/api/tickets/{id}` | `ticket:read` + trong phạm vi | Chi tiết kèm toàn bộ tin nhắn |
| `POST` | `/api/tickets` | `ticket:create` | Tạo phiếu (chủ đề, bộ phận, ưu tiên, nội dung) |
| `PATCH` | `/api/tickets/{id}` | chủ phiếu hoặc handler | Sửa chủ đề/bộ phận/ưu tiên (chặn khi đã đóng) |
| `POST` | `/api/tickets/{id}/messages` | chủ phiếu hoặc handler | Gửi tin trả lời (`is_staff` tự suy theo handler) + `file_ids` đính kèm cho chính tin đó |
| `POST` | `/api/tickets/{id}/assign` | **chỉ handler** | Nhận phiếu (`assignee_id` = user) / trả về hàng chờ (`assignee_id = 0`). Nhận phiếu đang `open` → tự chuyển `in_progress`; giao cho người khác thì báo cho họ |
| `POST` | `/api/tickets/{id}/status` | handler = mọi trạng thái; chủ phiếu = `closed`/`in_progress` | Đổi trạng thái (+ gán người xử lý nếu handler) |

Đính kèm dùng API chung `/api/attachments` với `entity=ticket` (tệp gửi kèm lúc tạo phiếu) và `entity=ticket_message` (tệp gắn vào một tin trả lời) — quyền upload gate theo entity cha `ticket` (`write` HOẶC `create`), giới hạn 20 MB/tệp. Cả hai chỗ đều **upload trước** qua `POST /api/attachments/upload-file` lấy `file_id`, rồi gửi `file_ids` kèm `POST /api/tickets` (popup tạo) hoặc `POST /api/tickets/{id}/messages` (ô trả lời). `GET /api/tickets/{id}` trả kèm mảng `files` cho **từng tin nhắn** để hiển thị ngay trong bong bóng.

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
