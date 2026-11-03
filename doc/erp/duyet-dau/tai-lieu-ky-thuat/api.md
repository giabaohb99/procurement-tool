# TÀI LIỆU API — DUYỆT DẤU

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `seal-request`, `seal_clerk`, `seal_type`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `seal_request`, `seal_clerk`; danh mục dựng bằng `make_crud_router`: `/api/seal-types`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/seal-requests` | list seal requests | `seal_request.read` | `apply_scope` | |
| POST | `/api/seal-requests` | create seal request | `seal_request.create` |  | |
| GET | `/api/seal-requests/approvers` | Trưởng bộ phận có quyền phê duyệt (để chọn), mặc định = TBP của người tạo. | `seal_request.create` |  | |
| GET | `/api/seal-requests/overview` | Tổng quan Duyệt dấu theo vai trò — gác từng khối bằng quyền, lọc theo phạm vi. | — |  | |
| GET | `/api/seal-requests/summary` | seal summary | `báo cáo 10`, `seal_request.read` |  | |
| GET | `/api/seal-requests/summary/export` | seal summary export | `báo cáo 10`, `seal_request.export` |  | |
| DELETE | `/api/seal-requests/{rid}` | delete seal request | `seal_request.delete` |  | |
| GET | `/api/seal-requests/{rid}` | Chi tiết phiếu: trong phạm vi dữ liệu, HOẶC đang được giao duyệt nó (bao-CR-584). | — | `get_scoped` | |
| PATCH | `/api/seal-requests/{rid}` | update seal request | `seal_request.write` |  | |
| POST | `/api/seal-requests/{rid}/approve` | approve seal | `seal_request.approve` |  | |
| POST | `/api/seal-requests/{rid}/complete` | Văn thư đóng dấu xong → Hoàn thành. | `seal_request.write` |  | |
| POST | `/api/seal-requests/{rid}/reject` | reject seal | `seal_request.approve` |  | |
| POST | `/api/seal-requests/{rid}/reject-clerk` | Văn thư TỪ CHỐI (phiếu Đã duyệt). | `seal_request.write` |  | |
| POST | `/api/seal-requests/{rid}/return` | return seal | `seal_request.approve` |  | |
| POST | `/api/seal-requests/{rid}/return-clerk` | Văn thư YÊU CẦU CHỈNH SỬA (phiếu Đã duyệt) — vd chụp lại chữ ký rõ hơn. | `seal_request.write` |  | |
| POST | `/api/seal-requests/{rid}/submit` | Gửi duyệt phiếu Nháp / bị Yêu cầu chỉnh sửa (kiểm dữ liệu + ≥1 chứng từ chữ ký sống). | `seal_request.write` |  | |
| GET | `/api/seal-clerks` | Danh sách phân công văn thư — GỘP THEO VĂN THƯ (mỗi người một dòng). | `seal_type.read` |  | |
| POST | `/api/seal-clerks` | create  | `seal_type.create` |  | |
| POST | `/api/seal-clerks/bulk` | bulk  | `seal_type.create` |  | |
| GET | `/api/seal-clerks/by-employee/{eid}` | Gộp phân công của một văn thư (danh sách công ty + cờ tổng) — cho màn chi tiết. | `seal_type.read` |  | |
| POST | `/api/seal-clerks/sync` | Đặt lại toàn bộ công ty một văn thư phụ trách = đúng danh sách gửi lên. | `seal_type.create` |  | |
| DELETE | `/api/seal-clerks/{cid}` | delete  | `seal_type.delete` |  | |
| GET | `/api/seal-clerks/{cid}` | get  | `seal_type.read` |  | |
| PATCH | `/api/seal-clerks/{cid}` | update  | `seal_type.write` |  | |
| GET | `/api/seal-types` | list items | `seal_type.read` | `apply_scope` | |
| POST | `/api/seal-types` | create item | `seal_type.create` |  | |
| GET | `/api/seal-types/export/csv` | export csv | `seal_type.export` | `apply_scope` | |
| POST | `/api/seal-types/import/csv` | import csv | `seal_type.import` | `scope_condition` | |
| DELETE | `/api/seal-types/{oid}` | delete item | `seal_type.delete` | `get_scoped` | |
| GET | `/api/seal-types/{oid}` | get item | `seal_type.read` | `get_scoped` | |
| PATCH | `/api/seal-types/{oid}` | update item | `seal_type.write` | `get_scoped` | |

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
