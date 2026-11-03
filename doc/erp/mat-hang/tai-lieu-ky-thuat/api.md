# TÀI LIỆU API — MẶT HÀNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `brand`, `item_group`, `product`, `unit`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `product`; danh mục dựng bằng `make_crud_router`: `/api/units`, `/api/item-groups`, `/api/brands`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| DELETE | `/api/products` | bulk delete products | `product.delete` | `apply_scope` | |
| GET | `/api/products` | list products | `product.read` |  | |
| POST | `/api/products` | create product | `product.create` |  | |
| GET | `/api/products/export/csv` | export products csv | `product.export` | `apply_scope` | |
| POST | `/api/products/import/csv` | import products csv | `product.import` |  | |
| DELETE | `/api/products/{pid}` | delete product | `product.delete` | `get_scoped` | |
| GET | `/api/products/{pid}` | get product | `product.read` |  | |
| PATCH | `/api/products/{pid}` | update product | `product.write` |  | |
| GET | `/api/units` | list items | `unit.read` | `apply_scope` | |
| POST | `/api/units` | create item | `unit.create` |  | |
| GET | `/api/units/export/csv` | export csv | `unit.export` | `apply_scope` | |
| POST | `/api/units/import/csv` | import csv | `unit.import` | `scope_condition` | |
| DELETE | `/api/units/{oid}` | delete item | `unit.delete` | `get_scoped` | |
| GET | `/api/units/{oid}` | get item | `unit.read` | `get_scoped` | |
| PATCH | `/api/units/{oid}` | update item | `unit.write` | `get_scoped` | |
| GET | `/api/item-groups` | list items | `item_group.read` | `apply_scope` | |
| POST | `/api/item-groups` | create item | `item_group.create` |  | |
| GET | `/api/item-groups/export/csv` | export csv | `item_group.export` | `apply_scope` | |
| POST | `/api/item-groups/import/csv` | import csv | `item_group.import` | `scope_condition` | |
| DELETE | `/api/item-groups/{oid}` | delete item | `item_group.delete` | `get_scoped` | |
| GET | `/api/item-groups/{oid}` | get item | `item_group.read` | `get_scoped` | |
| PATCH | `/api/item-groups/{oid}` | update item | `item_group.write` | `get_scoped` | |
| GET | `/api/brands` | list items | `brand.read` | `apply_scope` | |
| POST | `/api/brands` | create item | `brand.create` |  | |
| GET | `/api/brands/export/csv` | export csv | `brand.export` | `apply_scope` | |
| POST | `/api/brands/import/csv` | import csv | `brand.import` | `scope_condition` | |
| DELETE | `/api/brands/{oid}` | delete item | `brand.delete` | `get_scoped` | |
| GET | `/api/brands/{oid}` | get item | `brand.read` | `get_scoped` | |
| PATCH | `/api/brands/{oid}` | update item | `brand.write` | `get_scoped` | |

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
