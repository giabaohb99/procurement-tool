# TÀI LIỆU API — HẢI QUAN (TRA CỨU THỊ TRƯỜNG)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `customs`, `customs_price`, `customs_regulation`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `customs`; danh mục dựng bằng `make_crud_router`: `/api/customs-formulation-codes`, `/api/customs-kind-keywords`, `/api/customs-regulations`, `/api/customs-search-synonyms`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/customs/alerts` | get alerts | `customs_price.read` |  | |
| GET | `/api/customs/columns` | 32 cột đúng thứ tự + tiêu đề Excel — nguồn dựng cột trên màn hình. | `customs_price.read` |  | |
| GET | `/api/customs/compare` | get compare | `customs_price.read` |  | |
| GET | `/api/customs/coverage` | get coverage | `customs_price.read` |  | |
| GET | `/api/customs/importers` | get importers | `customs_price.read` |  | |
| GET | `/api/customs/imports` | list batches | `customs_price.read` |  | |
| POST | `/api/customs/imports` | Tải lên MỘT hoặc NHIỀU tệp của cùng một lần kết xuất → mỗi tệp một lô CHẠY THỬ. | `customs_price.write` |  | |
| GET | `/api/customs/imports/{bid}` | get batch | `customs_price.read` |  | |
| POST | `/api/customs/imports/{bid}/commit` | Ghi thật từ một lô chạy thử đã xong — dùng lại đúng tệp, không tải lại. | `customs_price.write` |  | |
| GET | `/api/customs/imports/{bid}/file` | Tải lại tệp GTT02 đã nạp (bao-CR-493, đề xuất đại ca 25/09). Lô nạp bằng script (không | `customs_price.read` |  | |
| GET | `/api/customs/imports/{bid}/logs` | get batch logs | `customs_price.read` |  | |
| POST | `/api/customs/imports/{bid}/revert` | revert batch | `customs_price.delete` |  | |
| GET | `/api/customs/imports/{bid}/rows` | batch rows | `customs_price.read` |  | |
| GET | `/api/customs/imports/{bid}/rows/summary` | batch row summary | `customs_price.read` |  | |
| POST | `/api/customs/kinds/retag` | Gắn lại hoạt chất + hàm lượng + nhãn Thành phẩm/Nguyên liệu cho MỌI dòng. | `customs_price.write` |  | |
| GET | `/api/customs/lines` | get lines | `customs_price.read` |  | |
| GET | `/api/customs/lines/export` | export lines | `customs_price.export` |  | |
| DELETE | `/api/customs/lines/{line_id}` | bao-CR-608 — xóa tay một dòng; chụp bản trước khi xóa vào `tab_customs_line_change`. | `customs_price.delete` |  | |
| GET | `/api/customs/lines/{line_id}` | get line | `customs_price.read` |  | |
| PATCH | `/api/customs/lines/{line_id}` | bao-CR-608 — sửa tay một dòng; chụp bản trước khi sửa vào `tab_customs_line_change`. | `customs_price.write` |  | |
| GET | `/api/customs/options` | get options | `customs_price.read` |  | |
| GET | `/api/customs/parties` | get parties | `customs_price.read` |  | |
| GET | `/api/customs/pesticides` | list pesticides | `customs_price.read` |  | |
| POST | `/api/customs/pesticides` | create pesticide | `customs_pesticide.create` |  | |
| GET | `/api/customs/pesticides/export` | Xuất Excel mục "Thuốc BVTV" — đặt TRƯỚC `/{pesticide_id}` để "export" không bị nuốt làm id. | `customs_price.export` |  | |
| POST | `/api/customs/pesticides/import` | Nạp danh mục từ tệp `thuoc-bvtv.json`/`thuoc-bvtv.xlsx` của bản cào, HOẶC tệp hệ thống | `customs_pesticide.write` |  | |
| GET | `/api/customs/pesticides/options` | get options | `customs_price.read` |  | |
| DELETE | `/api/customs/pesticides/{pesticide_id}` | delete pesticide | `customs_pesticide.delete` |  | |
| GET | `/api/customs/pesticides/{pesticide_id}` | get pesticide | `customs_price.read` |  | |
| PATCH | `/api/customs/pesticides/{pesticide_id}` | update pesticide | `customs_pesticide.write` |  | |
| GET | `/api/customs/pesticides/{pesticide_id}/related` | "Sản phẩm khác cùng công ty" + "Thuốc cùng hoạt chất" của trang chi tiết (01/10/2026). | `customs_price.read` |  | |
| GET | `/api/customs/regulations` | Mục "Pháp lý" (29/09/2026) — duyệt cả danh mục hóa chất theo văn bản, có phân trang. | `customs_price.read` |  | |
| GET | `/api/customs/regulations/lookup` | get regulation lookup | `customs_price.read` |  | |
| GET | `/api/customs/regulations/options` | get regulation options | `customs_price.read` |  | |
| GET | `/api/customs/saved-filters` | list saved filters | `customs_price.read` |  | |
| POST | `/api/customs/saved-filters` | create saved filter | `customs_price.read` |  | |
| DELETE | `/api/customs/saved-filters/{fid}` | delete saved filter | `customs_price.read` |  | |
| PATCH | `/api/customs/saved-filters/{fid}` | update saved filter | `customs_price.read` |  | |
| GET | `/api/customs/search/explain` | Ô tìm đang hiểu thế nào: từ CÓ / KHÔNG CÓ và các cách viết sẽ khớp (đồng nghĩa + nồng độ). | `customs_price.read` |  | |
| GET | `/api/customs/stats` | Biểu đồ + bảng theo kỳ. Chỉ chạy khi đã lọc (từ khóa / hoạt chất / mã HS). | `customs_price.read` |  | |
| GET | `/api/customs/tariff` | get tariff | `customs_price.read` |  | |
| GET | `/api/customs-formulation-codes` | list items | `customs_price.read` | `apply_scope` | |
| POST | `/api/customs-formulation-codes` | create item | `customs_price.create` |  | |
| GET | `/api/customs-formulation-codes/export/csv` | export csv | `customs_price.export` | `apply_scope` | |
| POST | `/api/customs-formulation-codes/import/csv` | import csv | `customs_price.import` | `scope_condition` | |
| DELETE | `/api/customs-formulation-codes/{oid}` | delete item | `customs_price.delete` | `get_scoped` | |
| GET | `/api/customs-formulation-codes/{oid}` | get item | `customs_price.read` | `get_scoped` | |
| PATCH | `/api/customs-formulation-codes/{oid}` | update item | `customs_price.write` | `get_scoped` | |
| GET | `/api/customs-kind-keywords` | list items | `customs_price.read` | `apply_scope` | |
| POST | `/api/customs-kind-keywords` | create item | `customs_price.create` |  | |
| GET | `/api/customs-kind-keywords/export/csv` | export csv | `customs_price.export` | `apply_scope` | |
| POST | `/api/customs-kind-keywords/import/csv` | import csv | `customs_price.import` | `scope_condition` | |
| DELETE | `/api/customs-kind-keywords/{oid}` | delete item | `customs_price.delete` | `get_scoped` | |
| GET | `/api/customs-kind-keywords/{oid}` | get item | `customs_price.read` | `get_scoped` | |
| PATCH | `/api/customs-kind-keywords/{oid}` | update item | `customs_price.write` | `get_scoped` | |
| GET | `/api/customs-regulations` | list items | `customs_regulation.read` | `apply_scope` | |
| POST | `/api/customs-regulations` | create item | `customs_regulation.create` |  | |
| GET | `/api/customs-regulations/export/csv` | export csv | `customs_regulation.export` | `apply_scope` | |
| POST | `/api/customs-regulations/import/csv` | import csv | `customs_regulation.import` | `scope_condition` | |
| DELETE | `/api/customs-regulations/{oid}` | delete item | `customs_regulation.delete` | `get_scoped` | |
| GET | `/api/customs-regulations/{oid}` | get item | `customs_regulation.read` | `get_scoped` | |
| PATCH | `/api/customs-regulations/{oid}` | update item | `customs_regulation.write` | `get_scoped` | |
| GET | `/api/customs-search-synonyms` | list items | `customs_price.read` | `apply_scope` | |
| POST | `/api/customs-search-synonyms` | create item | `customs_price.create` |  | |
| GET | `/api/customs-search-synonyms/export/csv` | export csv | `customs_price.export` | `apply_scope` | |
| POST | `/api/customs-search-synonyms/import/csv` | import csv | `customs_price.import` | `scope_condition` | |
| DELETE | `/api/customs-search-synonyms/{oid}` | delete item | `customs_price.delete` | `get_scoped` | |
| GET | `/api/customs-search-synonyms/{oid}` | get item | `customs_price.read` | `get_scoped` | |
| PATCH | `/api/customs-search-synonyms/{oid}` | update item | `customs_price.write` | `get_scoped` | |

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
