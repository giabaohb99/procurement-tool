# TÀI LIỆU API — KHO

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `inventory`, `warehouse`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `inventory`; danh mục dựng bằng `make_crud_router`: `/api/warehouses`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/inventory` | list inventory | `inventory.read` | `apply_scope` | tự dò: v2 `inventory` |
| POST | `/api/inventory/adjust` | adjust | `inventory.write` |  | tự dò: v2 `inventory` |
| GET | `/api/inventory/moves` | list moves | `inventory.read` | `apply_scope` | tự dò: v2 `inventory` |
| GET | `/api/warehouses` | Danh sách kho, có lọc và phân trang. | `warehouse.read` | `apply_scope` | tự dò: v2 `inventory`, v2 `procurement`, v2 dùng chung |
| POST | `/api/warehouses` | Thêm một dòng kho; chặn trùng mã, ghi nhật ký. | `warehouse.create` |  | tự dò: v2 `inventory`, v2 `procurement`, v2 dùng chung |
| GET | `/api/warehouses/export/csv` | Xuất kho ra tệp CSV theo bộ lọc đang chọn. | `warehouse.export` | `apply_scope` |  |
| POST | `/api/warehouses/import/csv` | Nhập kho hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `warehouse.import` | `scope_condition` |  |
| GET | `/api/warehouses/{oid}` | Xem một dòng kho theo id. | `warehouse.read` | `get_scoped` |  |
| PATCH | `/api/warehouses/{oid}` | Sửa một dòng kho; chỉ ghi các ô gửi lên, ghi nhật ký. | `warehouse.write` | `get_scoped` |  |
| DELETE | `/api/warehouses/{oid}` | Xóa một dòng kho; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `warehouse.delete` | `get_scoped` |  |

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
