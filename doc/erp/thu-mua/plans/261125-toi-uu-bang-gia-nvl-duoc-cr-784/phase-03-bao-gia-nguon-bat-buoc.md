# Phase 03 — Báo giá: `source_type` / `source_id` NOT NULL + khóa duy nhất

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P2 · 4 giờ · cần phase 02 (cùng `product_price/model.py`, cùng migration `opt784`).

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

## Migration (`opt784`, phần báo giá)
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
- [ ] Chủ dự án chốt C3–C5
- [ ] Bộ mã `QuoteSourceType` + sinh TS
- [ ] Cột, khóa, migration + hàm điền lại có bài kiểm
- [ ] CRUD + nhập Excel ghi nguồn; 409 trùng khóa
- [ ] Cột Nguồn ở v1 + v2
