# Phase 03 — BE báo giá, ngưỡng giá, định mức bao bì + nhập Excel

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P2 · 5 giờ · cần 01, đi sau 02 (cùng sửa `import_tool/service.py`).

## CRUD — dùng `make_crud_router` (`core/crud.py`), cả ba gác `packaging_cost`
| Router | Bảng | `unique_field` | Chốt chặn |
|---|---|---|---|
| `/api/product-price-quotes` | quote | không (nhiều dòng mỗi mã) — kiểm `make_crud_router` nhận `None`, nếu không thì `before_create` tự kiểm | `before_create/update`: `product_code` có trong `tab_product`; `supplier_code` rỗng hoặc có trong `tab_supplier`; `price >= 0`; `valid_from` trong 2000–2100 |
| `/api/product-price-limits` | limit | `product_code` | mã có trong `tab_product`; `floor <= ceiling` khi có cả hai; giá >= 0 |
| `/api/packaging-boms` | BOM | `hh_code` | 5 mã thành phần rỗng hoặc có trong `tab_product`; `carton_qty` 0–100000; `bottle_code` bắt buộc; từ 25/11/2026 năm mã ghi sang `tab_packaging_bom_part` qua `virtual_fields` + `after_create` / `before_update` của bộ sinh (API giữ trường phẳng) |

- Schema: mọi `String(n)` có `max_length` đúng n (`backend-input-limits.md`); tiền `Field(ge=0, le=1e12)`. Danh sách lọc
  theo `product_code`, `supplier_code`, `hh_code`, `q` (LIKE tên).
- Đầu ra BOM kèm tên + ĐVT 5 mã thành phần: gom MỘT truy vấn `tab_product WHERE code IN (...)` cho cả trang (không N+1).
- Docstring tiếng Việt cho từng đường (dòng đầu = tóm tắt) + `tags=["packaging-cost"]`.

## Nhập định mức từ `DATA_CHAI.xlsx` — `ImportModule.PACKAGING_BOM = 4`
Số 4 thuộc dải "3..9 cho nghiệp vụ" (`import_tool/model.py:24`), đi đường **đọc riêng** như `CUSTOMS_DECLARATION`
(tệp không theo khuôn tiêu đề một dòng của `catalog_import`).

`backend/app/modules/packaging_cost/bom_import.py` — đọc đúng logic `importExcel()` của bản mẫu:
- Có sheet `MAP_SP` (ưu tiên): bỏ 4 dòng đầu, lấy dòng có cột C; cột A chai, B nắp, C mã HH, D tên HH, E tên pháp lý,
  F quy cách thùng (số), I nhãn, J nhãn thùng, K thùng. Ô bắt đầu bằng `#` (lỗi công thức Excel) = rỗng.
- Không có `MAP_SP` thì sheet `data` (cùng cột A–F) + sheet `DATA CHUNG` (bỏ 2 dòng đầu; cột C mã nhãn, cột F mã HH): mã
  tiền tố `NHG/NHD/NTN` → nhãn, `NDT` → nhãn thùng; một HH nhiều mã thì chọn mã có **lần mua có giá gần nhất trong sổ giá**
  (một truy vấn `MAX(price_date)` theo mã). Khớp HH bỏ số 0 đầu (`HH0417.1` = `HH417.1`).
- Có rồi thì cập nhật (theo `hh_code`), chưa có thì tạo; dòng trên DB không có trong tệp **giữ nguyên** và báo số đếm.
- Nhật ký từng dòng (`add_log`): mã thành phần không có trong `tab_product` = cảnh báo (vẫn nhận), thiếu chai / mã HH =
  lỗi (bỏ dòng), quy cách không phải số = cảnh báo (đặt 0). Trần 20.000 dòng (`check_row_limit`).
- Chạy thử (dry-run) rồi xác nhận theo luồng có sẵn của `import_tool`; **không hỗ trợ hoàn tác** đợt đầu — `revert_batch`
  trả lỗi rõ ràng "Phân hệ này chưa hỗ trợ hoàn tác" (kiểm hàm đang xử lý module lạ ra sao, đừng để rơi vào nhánh khác).
- Gác: `_guard_module` của `import_tool/controller.py` cho module 4 = `packaging_cost.create` (như customs dùng khóa riêng).

## Tệp
- Tạo: `backend/app/modules/packaging_cost/{schema,bom_controller,bom_import}.py`,
  `backend/app/modules/product_price/{schema,quote_limit_controller}.py` (đặt tên theo nếp `customs/pesticide_controller.py`), `test/backend/test_dinh_muc_bao_bi_cr784.py`,
  `test/backend/test_bao_gia_nguong_gia_cr784.py`.
- Sửa: `app/main.py` (đăng ký 3 router), `import_tool/model.py` (thêm `PACKAGING_BOM = 4`), `import_tool/tasks.py` (nhãn
  + nhánh gọi `bom_import.run`), `import_tool/service.py` (nhóm `"procurement"` + nhánh revert), `import_tool/controller.py`
  (gác module 4), `test/backend/test_canh_do_dai_o_chu_cr538.py` (`MODULES` + `TARGETS`), `core/action_catalog.py` nếu
  phát sinh mã hành động mới.

## Bài kiểm
- Schema: chuỗi dài hơn n → `ValidationError` (kiểm ở tầng schema, SQLite không ép độ dài); giá âm; `floor > ceiling`;
  `valid_from` năm 0001.
- CRUD: mã không có trong danh mục → 422 câu tiếng Việt; trùng `hh_code` / `product_code` (limit) → 400.
- Nhập Excel: dựng workbook openpyxl trong bài (không cần tệp thật) cho cả hai khuôn (`MAP_SP`; `data` + `DATA CHUNG`); ô
  `#N/A`; HH có hai nhãn → chọn nhãn mua gần nhất; dry-run không ghi; chạy hai lần = cập nhật, không nhân đôi.
- Người không có `packaging_cost.create` tải lên module 4 → 403.

## Rủi ro
| Rủi ro | KN x AH | Giảm thiểu |
|---|---|---|
| Khuôn tệp thật khác bản mẫu (cột dời) | TB x Cao | Kiểm tiêu đề dòng 1–4 có chữ mong đợi, sai thì dừng lô với câu rõ; xin tệp thật (Q6) trước khi viết |
| Mã thành phần chưa có trong danh mục | Cao x TB | Nhận + cảnh báo, màn hiện "chưa có trong danh mục" |
| Ghi đè định mức đã sửa tay bằng tệp cũ | TB x TB | Bản chạy thử liệt kê ô sẽ đổi (cũ → mới) trước khi xác nhận |

## Quay lui
Bỏ router + nhánh module 4. Dữ liệu định mức nằm ở bảng riêng, không ai khác đọc.
