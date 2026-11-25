# Phase 03 — Báo giá: `source_type` / `source_id` NOT NULL + khóa duy nhất

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |
| 2 | 25/11/2026 | fullstack | **Xong trên nhánh `duoc-cr784-opt-p03`** (chưa commit, CHƯA lên dev) — migration `quotesrc784` | duoc-CR-784 |

Ưu tiên P2 · 4 giờ · cần phase 02 (cùng `product_price/model.py`; migration riêng `quotesrc784` nối sau `srcmerge784`).

## Liên kết
- `backend/app/modules/product_price/model.py::ProductPriceQuote`, `schema.py`, `quote_limit_controller.py`
- `backend/app/modules/packaging_cost/quote_import.py` (module 5 `PACKAGING_QUOTE` của `import_tool`)
- `backend/app/modules/import_tool/model.py` (`tab_import_batch`, `tab_import_log`)
- `backend/app/modules/survey_request/model.py::SurveyRequestOption` (`system_product_code`, `snap_price_by_volume`) — nguồn có thể có sau

## Hiện trạng
- Đúng **hai** đường ghi báo giá: hộp "+ Báo giá mới" / sửa ở màn Báo giá VTBB (`make_crud_router`, tạo bằng
  `Model(**data.model_dump())`, không có nhập CSV vì không khai `csv_headers`) và nhập Excel module 5. Không có đường nào sinh
  báo giá từ YCBG / khảo sát (dòng YCBG chỉ có nhóm hàng, không có mã; mã nằm ở phương án `system_product_code`).
- Nhập Excel dùng khóa `(mã, NCC, ngày hiệu lực)`: có rồi thì cập nhật giá / VAT / ghi chú, nhưng bảng KHÔNG có ràng buộc duy
  nhất này — hộp tay tạo được hai báo giá trùng khóa, "báo giá mới nhất" khi đó chọn theo id.
- Dữ liệu: local 0 dòng; dev chưa đo (chạy câu đếm chỉ đọc ở bước 1 dưới trước khi lên dev); prod chưa có bảng.

## Bộ mã mới — `QuoteSourceType` (SMALLINT + IntEnum, `core/packaging_price_codes.py`)
| Số | Khóa | Nhãn | `source_id` |
|---|---|---|---|
| 1 | `MANUAL` | Nhập tay | 0 = không có chứng từ gốc (C3 = A) |
| 2 | `EXCEL_IMPORT` | Nhập Excel | `tab_import_batch.id` của đợt nhập |
| (3) | để dành `SURVEY_OPTION` | Phương án YCBG | `tab_survey_request_option.id` — chỉ thêm khi làm đường tự tạo (C2) |

## Cấu trúc đích `tab_product_price_quote`
| Cột | Hiện | Đích | Lý do |
|---|---|---|---|
| `source_type` | — | SMALLINT NOT NULL, không server default | anh yêu cầu không NULL; ghi mới phải đặt rõ |
| `source_id` | — | BIGINT NOT NULL, không server default | như trên |
| `product_code`, `supplier_code` | String(50) | giữ | nối chuỗi theo nếp `product_code`, không FK |
| `price` | Numeric(18,4) | giữ | đơn giá VNĐ chưa VAT, 4 số lẻ như mọi đơn giá của hệ |
| `vat` | Numeric(5,2) | giữ | |
| `valid_from` | Date | giữ | chưa cần `valid_to` (luật "báo giá mới nhất thắng") |
| `note` | String(500) | giữ | |
| chỉ mục | `ix_ppq_code_from (mã, valid_from, id)` | giữ + `uq_ppq_key (mã, NCC, valid_from)` (C5) + `ix_ppq_source (source_type, source_id)` | khóa nhập Excel thành luật của bảng; tra "báo giá của đợt X" |

Không thêm `company_id`: báo giá là danh mục dùng chung (Q4 của 261120 đo phạm vi trên sổ giá). Cần báo giá riêng từng pháp
nhân thì là việc khác.

## Ghi nguồn ở mã
- ORM: `source_type` mặc định `MANUAL`, `source_id` mặc định 0 (mặc định phía Python) — đường CRUD không phải viết tay. Schema
  `QuoteCreate` / `QuoteUpdate` KHÔNG nhận hai trường (người gõ không tự khai nguồn); `QuoteOut` trả `source_type`,
  `source_id` (+ nhãn ở tầng hiển thị qua bộ mã sinh).
- `quote_import.run`: thêm mới → `(EXCEL_IMPORT, batch.id)`; cập nhật giá / VAT (C4 = A) → đổi nguồn sang đợt này. Sửa ở form
  (C4 = A) → `(MANUAL, 0)` khi giá / VAT đổi; chỉ đổi ghi chú thì giữ nguồn.
- Form tạo trùng khóa: bắt lỗi ràng buộc (đã có `commit_or_conflict`) → 409 câu tiếng Việt "Đã có báo giá cùng mã, NCC và ngày
  hiệu lực". Sửa câu trong bài kiểm so chuỗi cùng commit.
- Giao diện: cột "Nguồn" chỉ xem ở màn Báo giá VTBB (v2 `packaging-quote-crud.tsx`; v1 `packaging-cruds.tsx` — cụm này chạy cả hai
  bản), nguồn Excel bấm mở đợt nhập ở Quản lý Import. API chỉ THÊM trường nên bản nào chưa sửa vẫn chạy.

## Migration (kế hoạch ban đầu — thực hiện: `quotesrc784`, xem mục *Kết quả thực hiện* ở cuối)
Lên:
1. Đếm trước (chỉ đọc, ghi vào log migration): số dòng, số nhóm trùng `(mã, NCC, valid_from)`.
2. `add_column` hai cột với `server_default` tạm `1` / `0`.
3. Điền lại nguồn Excel: dòng báo giá khớp `tab_import_log` (`category = 'quote_new'`, `ref_key = product_code`, đợt
   `module = 5`, `status` xong, cùng `created_by`, `created_at` trong `[started_at, finished_at]` của đợt) → `(2, batch_id)`;
   còn lại giữ `(1, 0)`. Khớp mơ hồ (hai đợt) → để `(1, 0)` và đếm.
4. Trùng khóa: giữ dòng id lớn nhất mỗi nhóm, xóa còn lại (bảng đang 0 dòng ở local; dev đếm ở bước 1 — có trùng thì dừng, hỏi anh).
5. Tạo `uq_ppq_key`, `ix_ppq_source`; bỏ `server_default` hai cột.
Xuống: bỏ chỉ mục + hai cột (dòng đã xóa ở bước 4 không trả lại — chấp nhận, ghi rõ).

## Tệp sửa
`product_price/model.py`, `schema.py`, `quote_limit_controller.py`, `packaging_cost/quote_import.py`,
`core/packaging_price_codes.py` (+ `gen_status_ts.py`), migration `opt784`, FE v2 `packaging-quote-crud.tsx` +
`packaging-cost-types.ts`, FE v1 `config/packaging-cruds.tsx` + `api/packaging-cost-types.ts`.

## Bài kiểm
- Tạo tay → `(1, 0)`; nhập Excel thêm → `(2, batch.id)`; nhập Excel đè giá → nguồn đổi; đè chỉ ghi chú → không đổi.
- Gửi `source_type` trong thân POST bị bỏ qua (vẫn `MANUAL`).
- Trùng khóa ở form → 409; Excel chạy thử không ghi gì.
- Hàm điền lại nguồn của migration trên dữ liệu mẫu (một đợt khớp, một khớp mơ hồ, một dòng tay).

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Dev có báo giá trùng khóa | Thấp x Trung bình | bước 1 đếm, có trùng thì dừng và hỏi |
| Khớp nhật ký nhập nhầm đợt | Thấp x Thấp | chỉ gán khi khớp duy nhất; còn lại `(1, 0)` |
| Đường ghi mới sau này quên nguồn | Trung bình x Thấp | không server default; bài canh: mọi `ProductPriceQuote(` ngoài CRUD đều truyền `source_type` |

## Việc cần làm
- [x] Chủ dự án chốt C2: chỉ Nhập tay + Nhập Excel (25/11/2026)
- [x] Chủ dự án chốt C3–C5 (25/11/2026, cả ba chọn A)
- [x] Bộ mã `QuoteSourceType` + sinh TS (`gen_status_ts`: `QUOTE_SOURCE_TYPE`, `QUOTE_SOURCE_TYPE_CODE`)
- [x] Cột, khóa, migration `quotesrc784` + hàm điền lại có bài kiểm (SQLite lên / xuống / lên lại; MySQL 8 trên bản sao local)
- [x] CRUD + nhập Excel ghi nguồn; 409 trùng khóa
- [x] Cột Nguồn ở v1 + v2
- [ ] Lên dev: sao lưu, chạy câu đọc kiểm trùng khóa, khởi động lại api (xem *Việc cần làm khi lên dev*)

## Kết quả thực hiện (25/11/2026)

### Đã làm, và chỗ khác kế hoạch
| Hạng mục | Thực hiện | Khác kế hoạch? |
|---|---|---|
| Bộ mã | `QuoteSourceType` (1 `MANUAL` "Nhập tay", 2 `EXCEL_IMPORT` "Nhập Excel") ở `core/packaging_price_codes.py`, đăng ký bộ `quote_source_type`, TS sinh bằng `scripts/gen_status_ts.py` | không |
| Cột | `source_type` SMALLINT NOT NULL, `source_id` BIGINT NOT NULL, KHÔNG server default ở CSDL (mặc định Python `MANUAL` / 0 chỉ để CRUD tạo tay không phải viết lại); khóa `uq_ppq_key (product_code, supplier_code, valid_from)`; chỉ mục `ix_ppq_source` | không |
| Migration | `quotesrc784`, `down_revision = srcmerge784` (đã kiểm chỉ còn một đầu), viết tay, chạy MySQL + SQLite | id khác (`opt784` ban đầu); xem bên dưới |
| Điền lại nguồn | khớp `tab_import_log` (xem dưới) | **khác**: kế hoạch khớp theo `created_at` trong `[started_at, finished_at]` của đợt; thực hiện khớp theo thời điểm dòng nhật ký (cùng đồng hồ CSDL với `updated_at` của báo giá), vì `started_at` / `finished_at` ghi bằng `utcnow()` của Python còn `created_at` / `updated_at` bằng `now()` của MySQL — lệch múi giờ thì cửa sổ sai. Thêm: nhận cả báo giá bị Excel ĐÈ giá (C4), không chỉ báo giá Excel tạo |
| Trùng khóa lúc lên | **khác**: kế hoạch ghi "giữ id lớn nhất, xóa còn lại"; thực hiện theo yêu cầu của chủ dự án là DỪNG kèm câu báo rõ, KHÔNG xóa dòng nào (MySQL không hoàn tác DDL nên kiểm trước mọi thay đổi cấu trúc) | khác |
| Form tạo trùng | chốt kiểm trước ở `quote_limit_controller._ensure_quote_key_free` → **409** *Đã có báo giá cùng mã, NCC và ngày hiệu lực*; hai người gửi sát nhau thì `uq_ppq_key` nổ lúc commit và cũng ra 409 nhờ hai tham số mới `conflict_message` / `conflict_status` của `make_crud_router` / `commit_or_conflict` (mặc định vẫn 400 cho mọi danh mục khác) | thêm sửa `core/crud.py` (nhỏ, tương thích ngược) vì `commit_or_conflict` luôn là 400 |
| Form sửa | đổi đơn giá / VAT → `(1, 0)`; chỉ đổi ghi chú → giữ nguồn; sửa sang khóa đã có → 409 | **thêm**: đổi mã / NCC / ngày hiệu lực cũng về `(1, 0)` (dòng không còn là dòng đã nhập từ Excel) |
| Nhập Excel | thêm → `(2, batch.id)`; đè ĐƠN GIÁ hoặc VAT → `(2, batch.id)` của đợt này (C4); đè chỉ ghi chú → giữ nguồn; chạy thử không ghi gì | theo bài kiểm của kế hoạch ("đè chỉ ghi chú → không đổi") |
| API | `source_type`, `source_id` (QuoteOut) + `source_label` (enrich, nhãn bộ mã); `QuoteCreate` / `QuoteUpdate` không có hai trường, gửi lên bị bỏ qua | không |
| Giao diện | cột **Nguồn** (chỉ xem, không xếp) ở v2 `packaging-quote-crud.tsx` + `PackagingQuoteSourceCell` và v1 `packaging-cruds.tsx`; chữ "Nhập tay" / "Nhập Excel (lô #N)", bấm lô mở đợt nhập (`/system/imports/:id` v2, `/import-batches/:id` v1) | không |
| Số liệu tính giá | không đổi (không đụng `price_state_service`, bảng giá, tác động) | — |

### Quy tắc điền lại nguồn của migration (`backfill_quote_sources`)
Nhật ký nhập lấy từ `tab_import_log` của đợt `module = 5`, `mode = 1` (ghi thật), `status = 2` (xong), `category` `quote_new` / `quote_update`, đọc khóa `(mã, NCC, ngày hiệu lực)` từ chính câu nhật ký (`Thêm / Cập nhật báo giá MÃ · NCC X · từ dd/mm/yyyy: ...`). Với mỗi báo giá:
1. "Lần chạm cuối của Excel" = dòng nhật ký cùng khóa mà đợt do người = `updated_by` của báo giá và thời điểm cách `updated_at` không quá 300 giây. Không có (đã sửa tay sau đó, hoặc nhật ký không còn) → `(1, 0)`; chạm của HAI đợt → khớp mơ hồ → `(1, 0)`, in số mơ hồ.
2. Nguồn = lần GHI GIÁ (thêm mới, hoặc cập nhật có "Đơn giá:" / "VAT:") muộn nhất không sau lần chạm cuối → `(2, id đợt)`. Đợt chạy thử không tính.
Giới hạn đã biết: nhật ký INFO chỉ giữ 300 dòng mỗi đợt nên đợt lớn có thể khớp thiếu — phần thiếu ở lại `(1, 0)`. Dev / local hiện 0 báo giá nên chưa ảnh hưởng. Xuống (`downgrade`) bỏ hai chỉ mục + hai cột, mất dữ liệu nguồn, giữ nguyên mọi dòng báo giá.

### Câu đọc kiểm trước khi lên dev (chỉ đọc)
```sql
-- 1) Số báo giá hiện có (local = 0; dev chưa đo)
SELECT COUNT(*) FROM tab_product_price_quote;
-- 2) Nhóm trùng khóa (mã, NCC, ngày hiệu lực). KẾT QUẢ MONG ĐỢI: 0 dòng. Có dòng nào thì migration DỪNG, gộp / xóa tay rồi chạy lại.
SELECT product_code, supplier_code, valid_from, COUNT(*) AS so_dong, GROUP_CONCAT(id) AS cac_id
FROM tab_product_price_quote GROUP BY product_code, supplier_code, valid_from HAVING COUNT(*) > 1;
-- 3) Các đợt nhập báo giá sẽ được dùng để điền lại nguồn (chỉ tham khảo)
SELECT id, created_by, status, mode, created_at FROM tab_import_batch WHERE module = 5 ORDER BY id;
```
(MySQL so sánh mã không phân biệt hoa thường, đúng như khóa duy nhất sẽ làm — `cpt0075` và `CPT0075` là một nhóm.)

### Việc cần làm khi lên dev
1. Sao lưu database dev. 2. Chạy ba câu đọc trên; nhóm trùng khóa phải bằng 0. 3. Gộp migration lên `erp-v2`, khởi động lại `api` (`alembic upgrade head` tự chạy `quotesrc784`; log in `[quotesrc784] nguồn báo giá: ...`). 4. Kiểm: `SHOW COLUMNS FROM tab_product_price_quote LIKE 'source%'` (NOT NULL, không default) + `SHOW INDEX` thấy `uq_ppq_key`, `ix_ppq_source`. 5. Màn Báo giá VTBB v2 + v1: cột Nguồn hiện; thử tạo hai báo giá cùng khóa → báo 409. Quay lui: `alembic downgrade -1` (mất nguồn, giữ dòng).

### Kiểm thử (25/11/2026)
- Backend: `test_bao_gia_nguon_va_khoa_duy_nhat_cr784.py` 19 bài (bộ mã, form (1,0), schema không nhận nguồn, 409 tạo / sửa, đổi nguồn khi sửa, Excel thêm / đè giá / đè ghi chú / chạy thử, khóa ở CSDL, bài canh mọi `ProductPriceQuote(` phải truyền nguồn, migration SQLite lên / xuống / lên lại + điền lại + dừng khi trùng, một đầu migration); sửa `test_trang_thai_gia_theo_ma_cr784.py` (hòa ngày nay phải khác NCC). `-k "cr784 or cr789"` + `test_pham_vi_khai_du_b07` + `test_canh_do_dai_o_chu_cr538` + `test_status_catalog_b01` + `test_dong_bo_giao_dien_v2` xanh; ruff `app` 0 lỗi.
- MySQL 8 (bản sao local `p03_scratch`, đã xóa): lên / xuống / lên lại sạch, điền lại đúng (2 Excel, 2 tay), trùng khóa (kể cả khác hoa thường) → dừng, không đổi cấu trúc.
- Frontend: v2 `tsc` 0 lỗi, `eslint` các tệp đổi 0 lỗi, `vitest src/modules/procurement` 1.813 bài xanh; v1 `tsc` đúng 4 lỗi cũ.
