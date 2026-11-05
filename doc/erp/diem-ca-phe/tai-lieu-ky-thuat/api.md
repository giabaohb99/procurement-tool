# TÀI LIỆU API — ĐIỂM CÀ PHÊ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `coffee-point`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `coffee_point`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/coffee/ledger` | list ledger | `coffee_ledger.read` | `apply_scope` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/ledger/adjust` | adjust ledger | `coffee_ledger.write` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/lookup` | Trả đúng {name, balance} — KHÔNG lịch sử, KHÔNG danh sách (04 §4.2): khớp đúng mã NV hoặc SĐT đầy đủ, đáp án tối đa MỘT người. | `coffee_member.read` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/members` | list members | `coffee_member.read` | `apply_scope` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/members` | create member | `coffee_member.create` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/members/pos-search` | Tra khách bên POS365 (SĐT/tên) phục vụ ghép — proxy, đã lọc `Password`. | `coffee_member.write` |  | tự dò: v2 `dego-coffee` |
| PATCH | `/api/coffee/members/{mid}` | update member | `coffee_member.write` | `get_scoped` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/members/{mid}/create-partner` | B-03: tạo khách mới bên POS365 (mã = mã nhân viên) rồi tự ghép. | `coffee_member.write` | `get_scoped` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/members/{mid}/match` | match member | `coffee_member.write` | `get_scoped` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/members/{mid}/unmatch` | unmatch member | `coffee_member.write` | `get_scoped` | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/menu` | Thực đơn đọc từ POS365 (tên/giá/ảnh theo dữ liệu quán đang bán). | đăng nhập |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/meta` | get meta | `coffee_member.read` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/my-wallet` | Ví của CHÍNH người gọi — chỉ cần đăng nhập, service tự lấy `employee_id` của người gọi; không nhận tham số id nên không có gì để vượt scope (04 §3). | đăng nhập |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/policies` | list policies | `coffee_policy.read` | `apply_scope` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/policies` | create policy | `coffee_policy.create` |  | tự dò: v2 `dego-coffee` |
| PATCH | `/api/coffee/policies/{pid}` | update policy | `coffee_policy.write` | `get_scoped` | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/pos-dashboard` | Số liệu quầy đọc TRỰC TIẾP từ POS365 lúc mở màn: hôm nay + doanh thu theo ngày + đơn gần đây kèm phương thức. | `pos_order.read` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/pos-orders` | list pos orders | `pos_order.read` | `apply_scope` | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/pos-orders/{oid}/resolve` | resolve pos order | `coffee_ledger.write` |  | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/reset/execute` | CHỐT cấp phát kỳ — dòng grant mang `created_by` = người chốt (dấu vết duyệt). | `coffee_ledger.approve` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/reset/preview` | Bảng DỰ KIẾN của kỳ: từng người thu bao nhiêu / cấp bao nhiêu — chưa ghi gì. | `coffee_ledger.approve` |  | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/self-order` | Nhân sự tự đặt: DEGO tạo đơn trên POS365 (trả trọn bằng tài khoản "Trừ điểm", gắn khách đã ghép) → quầy thấy đơn và pha → điểm trừ qua vòng kéo. | đăng nhập |  | tự dò: v2 `dego-coffee` |
| POST | `/api/coffee/sync/run` | Chạy đồng bộ NGAY trong request (không cần worker) — quán nhỏ, mỗi vòng vài giây. | `pos_order.write` |  | tự dò: v2 `dego-coffee` |
| GET | `/api/coffee/sync/runs` | Nhật ký đồng bộ RIÊNG của POS365 — cùng dữ liệu với màn Sổ đồng bộ chung, chỉ lọc sẵn nguồn `pos365` và hạt LƯỢT CHẠY để người coi quán khỏi phải lọc tay giữa cả trăm nguồn khác. | `pos_order.read` |  | tự dò: v2 `dego-coffee` |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
