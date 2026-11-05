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

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `product`; danh mục dựng bằng `make_crud_router`: `/api/units`, `/api/item-groups`, `/api/brands`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/brands` | Danh sách thương hiệu / Bộ phận, có lọc và phân trang. | `brand.read` | `apply_scope` |  |
| POST | `/api/brands` | Thêm một dòng thương hiệu / Bộ phận; chặn trùng mã, ghi nhật ký. | `brand.create` |  |  |
| GET | `/api/brands/export/csv` | Xuất thương hiệu / Bộ phận ra tệp CSV theo bộ lọc đang chọn. | `brand.export` | `apply_scope` |  |
| POST | `/api/brands/import/csv` | Nhập thương hiệu / Bộ phận hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `brand.import` | `scope_condition` |  |
| GET | `/api/brands/{oid}` | Xem một dòng thương hiệu / Bộ phận theo id. | `brand.read` | `get_scoped` |  |
| PATCH | `/api/brands/{oid}` | Sửa một dòng thương hiệu / Bộ phận; chỉ ghi các ô gửi lên, ghi nhật ký. | `brand.write` | `get_scoped` |  |
| DELETE | `/api/brands/{oid}` | Xóa một dòng thương hiệu / Bộ phận; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `brand.delete` | `get_scoped` |  |
| GET | `/api/item-groups` | Danh sách phân loại VTBB/NL, có lọc và phân trang. | `item_group.read` | `apply_scope` | tự dò: v2 `inventory`, v2 `procurement`, v2 `production` |
| POST | `/api/item-groups` | Thêm một dòng phân loại VTBB/NL; chặn trùng mã, ghi nhật ký. | `item_group.create` |  | tự dò: v2 `inventory`, v2 `procurement`, v2 `production` |
| GET | `/api/item-groups/export/csv` | Xuất phân loại VTBB/NL ra tệp CSV theo bộ lọc đang chọn. | `item_group.export` | `apply_scope` |  |
| POST | `/api/item-groups/import/csv` | Nhập phân loại VTBB/NL hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `item_group.import` | `scope_condition` |  |
| GET | `/api/item-groups/{oid}` | Xem một dòng phân loại VTBB/NL theo id. | `item_group.read` | `get_scoped` |  |
| PATCH | `/api/item-groups/{oid}` | Sửa một dòng phân loại VTBB/NL; chỉ ghi các ô gửi lên, ghi nhật ký. | `item_group.write` | `get_scoped` |  |
| DELETE | `/api/item-groups/{oid}` | Xóa một dòng phân loại VTBB/NL; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `item_group.delete` | `get_scoped` |  |
| GET | `/api/products` | list products | `product.read` |  | tự dò: v2 `dossier`, v2 `inventory`, v2 `procurement`, v2 `production` |
| POST | `/api/products` | create product | `product.create` |  | tự dò: v2 `dossier`, v2 `inventory`, v2 `procurement`, v2 `production` |
| DELETE | `/api/products` | bulk delete products | `product.delete` | `apply_scope` | tự dò: v2 `dossier`, v2 `inventory`, v2 `procurement`, v2 `production` |
| GET | `/api/products/export/csv` | export products csv | `product.export` | `apply_scope` |  |
| POST | `/api/products/import/csv` | import products csv | `product.import` |  |  |
| GET | `/api/products/{pid}` | get product | `product.read` |  |  |
| PATCH | `/api/products/{pid}` | update product | `product.write` |  |  |
| DELETE | `/api/products/{pid}` | delete product | `product.delete` | `get_scoped` |  |
| GET | `/api/units` | Danh sách đơn vị tính, có lọc và phân trang. | `unit.read` | `apply_scope` | tự dò: v2 `procurement`, v2 `production` |
| POST | `/api/units` | Thêm một dòng đơn vị tính; chặn trùng mã, ghi nhật ký. | `unit.create` |  | tự dò: v2 `procurement`, v2 `production` |
| GET | `/api/units/export/csv` | Xuất đơn vị tính ra tệp CSV theo bộ lọc đang chọn. | `unit.export` | `apply_scope` |  |
| POST | `/api/units/import/csv` | Nhập đơn vị tính hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `unit.import` | `scope_condition` |  |
| GET | `/api/units/{oid}` | Xem một dòng đơn vị tính theo id. | `unit.read` | `get_scoped` |  |
| PATCH | `/api/units/{oid}` | Sửa một dòng đơn vị tính; chỉ ghi các ô gửi lên, ghi nhật ký. | `unit.write` | `get_scoped` |  |
| DELETE | `/api/units/{oid}` | Xóa một dòng đơn vị tính; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `unit.delete` | `get_scoped` |  |

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
