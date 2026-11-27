# Mô hình dữ liệu cụm Giá nguyên vật liệu sản xuất (sổ giá, báo giá, định mức bao bì)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 26/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Hiệu lực (chỉ trên dev; prod chưa có bảng nào của cụm) |
| CR liên quan | duoc-CR-784 (kế hoạch [261120](../plans/261120-tac-dong-gia-bao-bi/plan.md), tối ưu [261125](../plans/261125-toi-uu-bang-gia-nvl-duoc-cr-784/plan.md)), bao-CR-789 |

Tài liệu này giữ phần **cấu trúc bảng** của cụm (cột, khóa, chỉ mục, chuỗi migration). Luật nghiệp vụ (nguồn giá vào sổ khi
nào, mốc sổ Misa, giá cũ / giá mới, cảnh báo, xóa theo lô) nằm ở [chức năng 21](../chuc-nang/21-tac-dong-gia-bao-bi.md) mục 1 và 9;
đường API ở [api.md](api.md). Mã: `backend/app/modules/product_price/model.py`, `backend/app/modules/packaging_cost/model.py`, bộ mã ở
`backend/app/core/packaging_price_codes.py`.

Nối với `tab_product` bằng **chuỗi** `product_code` / mã thành phần, không khóa ngoại, không cột giá trên `tab_product` (D-025,
[mô hình dữ liệu sản phẩm](../../mat-hang/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) §2, §11).

## 1. Bốn bảng

| Bảng | Vai trò | Ai ghi | Cột kiểm toán |
|---|---|---|---|
| `tab_product_price_ledger` | Sổ giá đã giao dịch (dẫn xuất, dựng lại được bằng `scripts/backfill_product_price_ledger.py`) | máy: đồng bộ ĐMH, `snapshot_line` của lịch sử mua, nạp Misa (module 6 hoặc script HTML) | chỉ `synced_at` (giờ máy chủ CSDL) |
| `tab_product_price_quote` | Báo giá của nhà cung cấp theo ngày hiệu lực | người: hộp Báo giá, nhập Excel module 5 | `AuditMixin` |
| `tab_packaging_bom` | Đầu phiếu định mức bao bì, một dòng mỗi mã HH | người: form, nhập Excel module 4 | `AuditMixin` |
| `tab_packaging_bom_part` | Thành phần của định mức (loại + mã vật tư) | đi theo đầu phiếu (`bom_parts_service.set_bom_codes`) | không (vết sửa ở đầu phiếu) |

Bảng ngưỡng `tab_product_price_limit` đã **xóa** ở migration `cleanup784` (chủ dự án chốt C6, 25/11/2026). Cần lại thì làm lại,
đừng dựng lại bảng cũ.

## 2. `tab_product_price_ledger` (sổ giá)

| Cột | Kiểu | Nghĩa |
|---|---|---|
| `id` | BIGINT tự tăng | dòng ĐMH giữ nguyên id từ lúc duyệt tới lúc hoàn thành (từ `srcmerge784`) |
| `source_type` | SMALLINT, `PriceSourceType` | 1 lịch sử mua CŨ nạp Excel · 2 dòng ĐMH của ERP · 3 Sổ Misa |
| `source_id` | BIGINT | 1 → `tab_purchase_history.id` (chỉ dòng `po_item_id` trống) · 2 → `tab_po_item.id` · 3 → số thứ tự trong sổ, KHÔNG trỏ chứng từ (script HTML dùng id dòng Misa trong tệp, module 6 đánh `max + 1`) |
| `line_stage` | SMALLINT NOT NULL, không mặc định, `LedgerLineStage` | 1 Đang mở (dòng ĐMH chưa hoàn thành, còn đổi theo ĐMH) · 2 Đã chốt (nguồn 1, nguồn 3, dòng ĐMH đã hoàn thành — đồng bộ không đụng nữa) |
| `doc_id` | BIGINT, chỉ mục đơn | id ĐMH (0 = không có ĐMH) |
| `product_code` | VARCHAR(50) | mã vật tư |
| `supplier_code` / `supplier_name` | VARCHAR(50) / VARCHAR(200) NULL | tên chép theo dòng chỉ ở nguồn Misa (mã NCC Misa không có trong `tab_supplier`) |
| `warehouse_name` | VARCHAR(200) NULL | TÊN kho nhập hàng (Misa: cột kho; ERP: tên tra từ mã kho) |
| `company_id` | BIGINT, mặc định 0 | pháp nhân — phạm vi của năm khóa có giá của cụm (`packaging_impact`, `packaging_product_summary`, `packaging_price_list`, `packaging_last_price`, `packaging_history`; bao-CR-792) đo trên cột này |
| `price_date` | DATE | ngày mua |
| `price` | DECIMAL(18,4) | đơn giá VNĐ chưa VAT (giá dòng x tỷ giá) |
| `vat` | DECIMAL(5,2) NULL, không mặc định | NULL = không biết (dòng Misa, từ `cleanup784`), KHÔNG phải 0% |
| `qty` | DECIMAL(18,3) | số lượng |
| `amount` | DECIMAL(18,2) NULL | thành tiền chưa VAT: Misa = cột *Giá trị*; dòng đã chốt từ lịch sử = tiền dòng lịch sử bỏ VAT, quy VNĐ; dòng ĐMH đang mở luôn NULL |
| `unit` | VARCHAR(25) | ĐVT lúc mua (cảnh báo lệch ĐVT danh mục) |
| `import_batch_id` | BIGINT NOT NULL, mặc định 0 | lô module 6 đã THÊM dòng này (từ `bombatch784`); 0 = ĐMH, lịch sử cũ, script HTML |
| `synced_at` | DATETIME, `server_default now()` | ghi đè dùng `func.now()`, không dùng giờ Python |

Khóa và chỉ mục:

| Tên | Cột | Dùng cho |
|---|---|---|
| `uq_ppl_source` (duy nhất) | `source_type, source_id` | khóa đồng bộ idempotent, nối mồ côi, `max(source_id)` của Misa |
| `ix_ppl_code_latest` | `product_code, price_date, doc_id, id, price, company_id, source_type` | chỉ mục PHỦ cho "n lần mua gần nhất", số gộp, mốc Misa |
| `ix_ppl_date_latest` | `price_date, doc_id, id` | lần mua đầu / gần nhất không theo mã |
| `ix_tab_product_price_ledger_doc_id` | `doc_id` | đồng bộ theo đơn |
| `ix_ppl_import_batch` | `import_batch_id` | xóa theo lô module 6 |

Thứ tự "gần nhất" = `price_date` giảm, `doc_id` giảm, `id` giảm.

## 3. `tab_product_price_quote` (báo giá)

| Cột | Kiểu | Nghĩa |
|---|---|---|
| `product_code`, `supplier_code` | VARCHAR(50) (`supplier_code` mặc định chuỗi rỗng) | mã VTBB, mã NCC |
| `price` | DECIMAL(18,4) | đơn giá VNĐ chưa VAT |
| `vat` | DECIMAL(5,2), mặc định 0 | % VAT |
| `valid_from` | DATE | ngày hiệu lực (ngày tương lai vẫn tính là giá mới) |
| `note` | VARCHAR(500) | ghi chú |
| `source_type` | SMALLINT NOT NULL, không server default, `QuoteSourceType` | 1 Nhập tay · 2 Nhập Excel (số 3 để dành phương án YCBG) |
| `source_id` | BIGINT NOT NULL, không server default | nhập tay = 0 · nhập Excel = `tab_import_batch.id` của lô ghi giá / VAT cuối |

Khóa và chỉ mục: `uq_ppq_key` duy nhất `(product_code, supplier_code, valid_from)` (từ `quotesrc784`; trùng → 409),
`ix_ppq_code_from (product_code, valid_from, id)`, `ix_ppq_source (source_type, source_id)` (tra báo giá của lô, xóa theo lô).
Hai cột nguồn do máy chủ ghi; khuôn `QuoteCreate` / `QuoteUpdate` không nhận.

## 4. `tab_packaging_bom` + `tab_packaging_bom_part` (định mức bao bì)

| Bảng | Cột | Ghi chú |
|---|---|---|
| `tab_packaging_bom` | `id`, `fg_code` VARCHAR(50) duy nhất, `fg_name` VARCHAR(255), `legal_name` VARCHAR(255), `carton_qty` INT (0 = chưa có), `import_batch_id` BIGINT NOT NULL mặc định 0, `AuditMixin` | `fg_code` / `fg_name` đổi tên từ `hh_code` / `hh_name` ở `fgname784` (nhãn người dùng thấy vẫn là *Mã HH*, *Tên hàng hóa*). `import_batch_id` = lô module 4 TẠO hoặc SỬA lần cuối, form sửa tay không đổi; chỉ mục `ix_pbom_import_batch` |
| `tab_packaging_bom_part` | `id`, `bom_id` FK → `tab_packaging_bom.id` ON DELETE CASCADE, `part_type` SMALLINT (`PackagingRole`: 1 chai · 2 nắp · 3 nhãn · 4 nhãn thùng · 5 thùng), `part_code` VARCHAR(50) | duy nhất `uq_pbom_part_bom_type (bom_id, part_type)`; chỉ mục phủ `ix_pbom_part_code (part_code, part_type, bom_id)` cho tra ngược "sản phẩm nào dùng mã X". Thêm loại mới = thêm thành viên `PackagingRole` + nhãn, không đổi bảng |

API danh mục `/api/packaging-boms` vẫn trả trường phẳng `bottle_code`, `cap_code`, `label_code`, `carton_label_code`,
`carton_code` (thuộc tính chỉ đọc dựng bằng truy vấn con) nên hai giao diện không phải đổi khi tách bảng.

## 5. Chuỗi migration của cụm

Mọi migration viết tay, chạy được trên MySQL 8 và SQLite (bài kiểm), mỗi bước có `downgrade`. Trên `main` (prod) chưa có bước nào
từ `pkgcost784`; `mrg761a` đã có.

| Thứ tự | Revision | Đổi gì |
|---|---|---|
| 1 | `pkgcost784` (sau `mrg761a`) | tạo sổ giá, báo giá, ngưỡng, định mức (khóa quyền `packaging_cost` khai trong mã, không qua migration) |
| 2 | `misa784` | nguồn 3 Sổ Misa, `supplier_name`, `warehouse_name`, dựng lại `ix_ppl_code_latest` |
| 3 | `amt784` | cột `amount` |
| 4 | `ppld784` | chỉ mục `ix_ppl_date_latest` |
| 5 | `bompart784` | tách định mức thành đầu phiếu + `tab_packaging_bom_part` (bỏ 5 cột mã) |
| 6 | `srcmerge784` | `line_stage`; gộp nguồn 1 có ĐMH thành nguồn 2 Đã chốt (giữ id) |
| 7 | `quotesrc784` | `source_type` / `source_id` báo giá NOT NULL, `uq_ppq_key`, `ix_ppq_source`; DỪNG nếu có trùng khóa |
| 8 | `cleanup784` | xóa `tab_product_price_limit`; `vat` cho phép NULL, dòng Misa đổi sang NULL |
| 9 | `fgname784` | đổi tên `hh_code` / `hh_name` → `fg_code` / `fg_name` |
| 10 | `bombatch784` | `import_batch_id` ở định mức + sổ giá; đánh dấu định mức cũ theo lô khi khớp đúng `created_count` |
| 11 | `permsplit792` (bao-CR-792, 27/11/2026) | migration DỮ LIỆU, không đổi bảng: mỗi dòng `tab_permission` của khóa `packaging_cost` chuyển thành dòng của các khóa theo màn (`read` / `export` sang cả sáu khóa; `create` sang `packaging_price_list`, `packaging_bom`; `write` / `delete` sang `packaging_price_list`, `packaging_bom`, `packaging_history`), giữ vai trò + phạm vi, đã có thì bỏ qua, rồi xóa dòng `packaging_cost`. Quay lui gộp ngược về một dòng `packaging_cost` (hợp các cờ, phạm vi rộng nhất) |

Câu đọc kiểm trước từng bước và lệnh quay lui: phase 02, 03, 04, 07 của [kế hoạch 261125](../plans/261125-toi-uu-bang-gia-nvl-duoc-cr-784/plan.md);
danh sách việc lên prod: [phase 05](../plans/261125-toi-uu-bang-gia-nvl-duoc-cr-784/phase-05-tai-lieu-kiem-phat-hanh.md).
