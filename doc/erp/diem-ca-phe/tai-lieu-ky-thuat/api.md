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

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `coffee_point`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/coffee/ledger` | list ledger | `coffee_ledger.read` | `apply_scope` | |
| POST | `/api/coffee/ledger/adjust` | adjust ledger | `coffee_ledger.write` |  | |
| GET | `/api/coffee/lookup` | Trả đúng {name, balance} — KHÔNG lịch sử, KHÔNG danh sách (04 §4.2): | `coffee_member.read` |  | |
| GET | `/api/coffee/members` | list members | `coffee_member.read` | `apply_scope` | |
| POST | `/api/coffee/members` | create member | `coffee_member.create` |  | |
| GET | `/api/coffee/members/pos-search` | Tra khách bên POS365 (SĐT/tên) phục vụ ghép — proxy, đã lọc `Password`. | `coffee_member.write` |  | |
| PATCH | `/api/coffee/members/{mid}` | update member | `coffee_member.write` | `get_scoped` | |
| POST | `/api/coffee/members/{mid}/create-partner` | B-03: tạo khách mới bên POS365 (mã = mã nhân viên) rồi tự ghép. | `coffee_member.write` | `get_scoped` | |
| POST | `/api/coffee/members/{mid}/match` | match member | `coffee_member.write` | `get_scoped` | |
| POST | `/api/coffee/members/{mid}/unmatch` | unmatch member | `coffee_member.write` | `get_scoped` | |
| GET | `/api/coffee/menu` | Thực đơn đọc từ POS365 (tên/giá/ảnh theo dữ liệu quán đang bán). | — |  | |
| GET | `/api/coffee/meta` | get meta | `coffee_member.read` |  | |
| GET | `/api/coffee/my-wallet` | Ví của CHÍNH người gọi — chỉ cần đăng nhập, service tự lấy `employee_id` | — |  | |
| GET | `/api/coffee/policies` | list policies | `coffee_policy.read` | `apply_scope` | |
| POST | `/api/coffee/policies` | create policy | `coffee_policy.create` |  | |
| PATCH | `/api/coffee/policies/{pid}` | update policy | `coffee_policy.write` | `get_scoped` | |
| GET | `/api/coffee/pos-dashboard` | Số liệu quầy đọc TRỰC TIẾP từ POS365 lúc mở màn: hôm nay + doanh thu theo | `pos_order.read` |  | |
| GET | `/api/coffee/pos-orders` | list pos orders | `pos_order.read` | `apply_scope` | |
| POST | `/api/coffee/pos-orders/{oid}/resolve` | resolve pos order | `coffee_ledger.write` |  | |
| POST | `/api/coffee/reset/execute` | CHỐT cấp phát kỳ — dòng grant mang `created_by` = người chốt (dấu vết duyệt). | `coffee_ledger.approve` |  | |
| GET | `/api/coffee/reset/preview` | Bảng DỰ KIẾN của kỳ: từng người thu bao nhiêu / cấp bao nhiêu — chưa ghi gì. | `coffee_ledger.approve` |  | |
| POST | `/api/coffee/self-order` | Nhân sự tự đặt: DEGO tạo đơn trên POS365 (trả trọn bằng tài khoản "Trừ | — |  | |
| POST | `/api/coffee/sync/run` | Chạy đồng bộ NGAY trong request (không cần worker) — quán nhỏ, mỗi vòng | `pos_order.write` |  | |
| GET | `/api/coffee/sync/runs` | Nhật ký đồng bộ RIÊNG của POS365 — cùng dữ liệu với màn Sổ đồng bộ chung, | `pos_order.read` |  | |

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
