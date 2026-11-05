# TÀI LIỆU API — HẢI QUAN (TRA CỨU THỊ TRƯỜNG)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-718 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `customs`, `customs_price`, `customs_regulation`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `customs`; danh mục dựng bằng `make_crud_router`: `/api/customs-formulation-codes`, `/api/customs-kind-keywords`, `/api/customs-regulations`, `/api/customs-search-synonyms`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/customs-formulation-codes` | Danh sách tra cứu thị trường, có lọc và phân trang. | `customs_price.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/customs-formulation-codes` | Thêm một dòng tra cứu thị trường; chặn trùng mã, ghi nhật ký. | `customs_price.create` |  | tự dò: v2 `procurement` |
| GET | `/api/customs-formulation-codes/export/csv` | Xuất tra cứu thị trường ra tệp CSV theo bộ lọc đang chọn. | `customs_price.export` | `apply_scope` |  |
| POST | `/api/customs-formulation-codes/import/csv` | Nhập tra cứu thị trường hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `customs_price.import` | `scope_condition` |  |
| GET | `/api/customs-formulation-codes/{oid}` | Xem một dòng tra cứu thị trường theo id. | `customs_price.read` | `get_scoped` |  |
| PATCH | `/api/customs-formulation-codes/{oid}` | Sửa một dòng tra cứu thị trường; chỉ ghi các ô gửi lên, ghi nhật ký. | `customs_price.write` | `get_scoped` |  |
| DELETE | `/api/customs-formulation-codes/{oid}` | Xóa một dòng tra cứu thị trường; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `customs_price.delete` | `get_scoped` |  |
| GET | `/api/customs-kind-keywords` | Danh sách tra cứu thị trường, có lọc và phân trang. | `customs_price.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/customs-kind-keywords` | Thêm một dòng tra cứu thị trường; chặn trùng mã, ghi nhật ký. | `customs_price.create` |  | tự dò: v2 `procurement` |
| GET | `/api/customs-kind-keywords/export/csv` | Xuất tra cứu thị trường ra tệp CSV theo bộ lọc đang chọn. | `customs_price.export` | `apply_scope` |  |
| POST | `/api/customs-kind-keywords/import/csv` | Nhập tra cứu thị trường hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `customs_price.import` | `scope_condition` |  |
| GET | `/api/customs-kind-keywords/{oid}` | Xem một dòng tra cứu thị trường theo id. | `customs_price.read` | `get_scoped` |  |
| PATCH | `/api/customs-kind-keywords/{oid}` | Sửa một dòng tra cứu thị trường; chỉ ghi các ô gửi lên, ghi nhật ký. | `customs_price.write` | `get_scoped` |  |
| DELETE | `/api/customs-kind-keywords/{oid}` | Xóa một dòng tra cứu thị trường; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `customs_price.delete` | `get_scoped` |  |
| GET | `/api/customs-regulations` | Danh sách danh mục hóa chất theo văn bản (hải quan), có lọc và phân trang. | `customs_regulation.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/customs-regulations` | Thêm một dòng danh mục hóa chất theo văn bản (hải quan); chặn trùng mã, ghi nhật ký. | `customs_regulation.create` |  | tự dò: v2 `procurement` |
| GET | `/api/customs-regulations/export/csv` | Xuất danh mục hóa chất theo văn bản (hải quan) ra tệp CSV theo bộ lọc đang chọn. | `customs_regulation.export` | `apply_scope` |  |
| POST | `/api/customs-regulations/import/csv` | Nhập danh mục hóa chất theo văn bản (hải quan) hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `customs_regulation.import` | `scope_condition` |  |
| GET | `/api/customs-regulations/{oid}` | Xem một dòng danh mục hóa chất theo văn bản (hải quan) theo id. | `customs_regulation.read` | `get_scoped` |  |
| PATCH | `/api/customs-regulations/{oid}` | Sửa một dòng danh mục hóa chất theo văn bản (hải quan); chỉ ghi các ô gửi lên, ghi nhật ký. | `customs_regulation.write` | `get_scoped` |  |
| DELETE | `/api/customs-regulations/{oid}` | Xóa một dòng danh mục hóa chất theo văn bản (hải quan); danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `customs_regulation.delete` | `get_scoped` |  |
| GET | `/api/customs-search-synonyms` | Danh sách tra cứu thị trường, có lọc và phân trang. | `customs_price.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/customs-search-synonyms` | Thêm một dòng tra cứu thị trường; chặn trùng mã, ghi nhật ký. | `customs_price.create` |  | tự dò: v2 `procurement` |
| GET | `/api/customs-search-synonyms/export/csv` | Xuất tra cứu thị trường ra tệp CSV theo bộ lọc đang chọn. | `customs_price.export` | `apply_scope` |  |
| POST | `/api/customs-search-synonyms/import/csv` | Nhập tra cứu thị trường hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `customs_price.import` | `scope_condition` |  |
| GET | `/api/customs-search-synonyms/{oid}` | Xem một dòng tra cứu thị trường theo id. | `customs_price.read` | `get_scoped` |  |
| PATCH | `/api/customs-search-synonyms/{oid}` | Sửa một dòng tra cứu thị trường; chỉ ghi các ô gửi lên, ghi nhật ký. | `customs_price.write` | `get_scoped` |  |
| DELETE | `/api/customs-search-synonyms/{oid}` | Xóa một dòng tra cứu thị trường; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `customs_price.delete` | `get_scoped` |  |
| GET | `/api/customs/alerts` | get alerts | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/columns` | 32 cột đúng thứ tự + tiêu đề Excel — nguồn dựng cột trên màn hình. | `customs_price.read` |  |  |
| GET | `/api/customs/compare` | get compare | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/coverage` | get coverage | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/export-batches` | Lô xuất của chính mình, mới nhất trước. | `customs_price.export` | của mình | màn Lô xuất |
| POST | `/api/customs/export-batches` | Xuất TOÀN BỘ dòng khớp bộ lọc đang chọn (bỏ trống = cả bảng): tạo lô chạy nền, trả ngay tổng dòng + số tệp dự kiến. | `customs_price.export` | lô của mình | màn Danh sách |
| GET | `/api/customs/export-batches/{bid}` | Chi tiết lô: trạng thái, tiến độ, danh sách tệp | `customs_price.export` | người xuất hoặc phạm vi tất cả | màn Lô xuất (hỏi lại 3 giây khi đang chạy) |
| POST | `/api/customs/export-batches/{bid}/cancel` | Dừng lô đang chờ / chạy | `customs_price.export` | chỉ người xuất | màn Lô xuất |
| GET | `/api/customs/export-batches/{bid}/files/{part}` | Tải một tệp của lô | `customs_price.export` | người xuất hoặc phạm vi tất cả | màn Lô xuất |
| GET | `/api/customs/importers` | get importers | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports` | list batches | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/imports` | Tải lên MỘT hoặc NHIỀU tệp của cùng một lần kết xuất → mỗi tệp một lô CHẠY THỬ. | `customs_price.write` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports/{bid}` | get batch | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/imports/{bid}/commit` | Ghi thật từ một lô chạy thử đã xong — dùng lại đúng tệp, không tải lại. | `customs_price.write` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports/{bid}/file` | Tải lại tệp GTT02 đã nạp (bao-CR-493, đề xuất đại ca 25/09). | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports/{bid}/logs` | get batch logs | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/imports/{bid}/revert` | revert batch | `customs_price.delete` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports/{bid}/rows` | batch rows | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/imports/{bid}/rows/summary` | batch row summary | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/kinds/retag` | Gắn lại hoạt chất + hàm lượng + nhãn Thành phẩm/Nguyên liệu cho MỌI dòng. | `customs_price.write` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/lines` | get lines | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/lines/export` | export lines (xuất ngay, tối đa 50.000 dòng) | `customs_price.export` |  | màn Danh sách |
| GET | `/api/customs/lines/{line_id}` | get line | `customs_price.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/customs/lines/{line_id}` | bao-CR-608 — sửa tay một dòng; chụp bản trước khi sửa vào `tab_customs_line_change`. | `customs_price.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/customs/lines/{line_id}` | bao-CR-608 — xóa tay một dòng; chụp bản trước khi xóa vào `tab_customs_line_change`. | `customs_price.delete` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/options` | get options | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/parties` | get parties | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/pesticides` | list pesticides | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/pesticides` | create pesticide | `customs_pesticide.create` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/pesticides/export` | Xuất Excel mục "Thuốc BVTV" — đặt TRƯỚC `/{pesticide_id}` để "export" không bị nuốt làm id. | `customs_price.export` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/pesticides/import` | Nạp danh mục từ tệp `thuoc-bvtv.json`/`thuoc-bvtv.xlsx` của bản cào, HOẶC tệp hệ thống tự xuất (C1, 02/10/2026): tệp xuất TOÀN BỘ / bản cào gốc → THAY TOÀN BỘ như trước giờ; tệp xuất THEO TRANG (sheet ẩn `_xuat`… | `customs_pesticide.write` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/pesticides/options` | get options | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/pesticides/{pesticide_id}` | get pesticide | `customs_price.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/customs/pesticides/{pesticide_id}` | update pesticide | `customs_pesticide.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/customs/pesticides/{pesticide_id}` | delete pesticide | `customs_pesticide.delete` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/pesticides/{pesticide_id}/related` | "Sản phẩm khác cùng công ty" + "Thuốc cùng hoạt chất" của trang chi tiết (01/10/2026). | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/regulations` | Mục "Pháp lý" (29/09/2026) — duyệt cả danh mục hóa chất theo văn bản, có phân trang. | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/regulations/lookup` | get regulation lookup | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/regulations/options` | get regulation options | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/saved-filters` | list saved filters | `customs_price.read` |  | tự dò: v2 `procurement` |
| POST | `/api/customs/saved-filters` | create saved filter | `customs_price.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/customs/saved-filters/{fid}` | update saved filter | `customs_price.read` |  | tự dò: v2 `procurement` |
| DELETE | `/api/customs/saved-filters/{fid}` | delete saved filter | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/search/explain` | Ô tìm đang hiểu thế nào: từ CÓ / KHÔNG CÓ và các cách viết sẽ khớp (đồng nghĩa + nồng độ). | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/stats` | Biểu đồ + bảng theo kỳ. | `customs_price.read` |  | tự dò: v2 `procurement` |
| GET | `/api/customs/tariff` | get tariff | `customs_price.read` |  | tự dò: v2 `procurement` |

## 2. Dữ liệu vào / ra chính

Ghi chú chi tiết từng đường (chuyển từ cột *Mục đích* của bảng mục 1 ngày 05/11/2026, khi cột đó chuyển sang lấy docstring):

- `POST /api/customs/export-batches`: Tạo lô xuất toàn bộ theo bộ lọc (cùng tham số `/lines`), trả tổng dòng + số tệp dự kiến

## 3. Lỗi riêng của phân hệ

| Đường | Mã | Khi nào |
|---|---|---|
| `POST /export-batches` | 409 | Người gọi đang có một lô chờ / chạy (khóa UNIQUE `active_user_id`) |
| `POST /export-batches` | 400 | Bộ lọc không có dòng nào |
| `GET /export-batches/{bid}`, `/files/{part}` | 403 | Không phải người xuất và không có `customs_price.export` phạm vi tất cả |
| `GET /export-batches/{bid}/files/{part}` | 404 | Tệp đã quá hạn giữ và bị dọn, hoặc không có tệp số đó |
| `POST /export-batches/{bid}/cancel` | 400 | Lô đã kết thúc |

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-718 | Thêm năm đường `/export-batches` (xuất toàn bộ chạy nền); `/lines` đếm qua đệm, `/options` qua đệm |
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
