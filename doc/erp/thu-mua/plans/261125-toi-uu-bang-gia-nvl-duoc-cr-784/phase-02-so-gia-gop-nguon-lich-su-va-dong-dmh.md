# Phase 02 — Sổ giá: gộp nguồn lịch sử mua (system) và dòng ĐMH thành một dòng theo `po_item_id`

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784, bao-CR-789 |

Ưu tiên P1 (đổi nghĩa cột khóa của sổ giá, làm trước khi lên prod) · 8 giờ · cần phase 01 đã gộp · C1 đã chốt gộp (25/11/2026).

## Liên kết
- `backend/app/modules/product_price/model.py`, `ledger_sync_service.py`, `misa_cutoff.py`, `ledger_stats.py`
- `backend/app/modules/purchase_history/service.py` (`snapshot_line` → `_record_in_price_ledger`, savepoint của bao-CR-789)
- `backend/app/core/packaging_price_codes.py` (`PriceSourceType`)
- Luật cũ: [261120 phase-01](../261120-tac-dong-gia-bao-bi/phase-01-be-mo-hinh-du-lieu-migration-quyen.md), [phase-02](../261120-tac-dong-gia-bao-bi/phase-02-be-so-gia-dong-bo-backfill.md)

## Hiện trạng (đã soát mã + DB local)
| `source_type` | `source_id` trỏ vào | `doc_id` | Dòng local | Luật |
|---|---|---|---|---|
| 1 Lịch sử mua | `tab_purchase_history.id` | `ph.po_id` (system) / 0 (legacy) | 6.505 = 87 system + 6.418 legacy | chỉ chèn; legacy nạp lại thì id đổi, xóa mồ côi rồi chèn |
| 2 Dòng ĐMH | `tab_po_item.id` | id ĐMH | 14 | có rồi thì cập nhật; dòng vào lịch sử thì XÓA |
| 3 Misa | id dòng Misa (tệp HTML) hoặc số tự đánh `max + 1` (tệp xlsx, module 6) | 0 | 5.041 | chỉ chèn / khớp theo nội dung |

- `tab_purchase_history.po_item_id` là **duy nhất** (NULL với legacy) và `snapshot_line` không chép lại nếu đã có: dòng lịch sử
  system là **bản chụp 1-1** của một dòng ĐMH lúc hoàn thành. Anh nói đúng: nguồn 1 (system) và nguồn 2 là CÙNG một lần mua.
- Hệ quả của việc tách: lúc hoàn thành, dòng sổ bị xóa rồi chèn lại với id mới. Vì thế mới phải chen `doc_id` vào thứ tự
  "gần nhất" (`price_state_service`), bộ lọc Misa phải viết `source_type = 2 OR doc_id > 0`, `sync_po_price_ledger` phải đọc
  thêm bảng lịch sử để biết dòng nào "đã có lịch sử", `sync_history_ledger` có bước 4 xóa dòng nguồn 2 đã có lịch sử.
- Giao diện v1 (`PackagingHistoryTable.tsx`, `PackagingHistoryPrintParts.tsx`) và v2 (`packaging-history-cells.tsx`,
  `packaging-history-print-parts.tsx`) đánh dấu "ĐMH đang mở" bằng `source_type === PO_LINE`.
- Lịch sử chụp giá theo đồng tiền dòng nhưng KHÔNG chụp tỉ giá; sổ lấy tỉ giá sống từ `tab_po_item` — bản chụp vốn đã không
  thuần, gộp không làm mất gì.

## Mô hình đích
| `source_type` | Nhãn mới | `source_id` | `line_stage` (MỚI) |
|---|---|---|---|
| 1 | Lịch sử mua hàng cũ (nạp Excel) | `tab_purchase_history.id`, chỉ dòng `po_item_id IS NULL` | 2 Đã chốt |
| 2 | Đơn mua hàng ERP | `tab_po_item.id` — cả khi đang mở lẫn đã hoàn thành | 1 Đang mở / 2 Đã chốt |
| 3 | Sổ Misa | không đổi | 2 Đã chốt |

Số 1 giữ nghĩa "đến từ `tab_purchase_history`", chỉ thu hẹp; không tái dùng số (luật R2).

Cột mới: `line_stage SMALLINT NOT NULL` + `IntEnum LedgerLineStage {OPEN = 1, FINAL = 2}` trong `packaging_price_codes.py`,
đăng ký bộ mã, chạy `gen_status_ts.py`. Không thêm chỉ mục (không câu nào lọc theo nó trên đường nóng; sync lọc theo `doc_id`).

### Luật mới (thay luật "chỉ chèn / có rồi thì cập nhật" của 261120)
1. ĐMH được tính (đã duyệt trở đi, chưa xóa mềm) + dòng chưa hủy + có mã: dòng sổ `(2, po_item.id)` tồn tại, `OPEN`, có rồi thì
   cập nhật — như nguồn 2 cũ.
2. Dòng hoàn thành (`snapshot_line`): `record_history_row` **cập nhật đúng dòng sổ đó** bằng số chụp (giá, SL, VAT, ĐVT, kho,
   `amount` bỏ VAT) và đặt `FINAL`; chưa có dòng (ĐMH chưa từng vào sổ) thì chèn `FINAL`. Không xóa, id giữ nguyên.
   Lịch sử hỏng (ngày sai / quá trần) thì giữ dòng `OPEN` như hiện nay.
3. Dòng `FINAL` là bản chốt: `sync_po_price_ledger` bỏ qua hẳn (không cập nhật, không xóa) — đúng nghĩa "chỉ chèn" của lịch sử
   cũ, kể cả khi ĐMH sau đó bị hủy / xóa mềm.
4. `sync_history_ledger` (nạp lại toàn bảng): legacy như cũ (xóa mồ côi theo `ph.id`, chèn thiếu); system: dòng lịch sử có
   `po_item_id` mà sổ chưa `FINAL` thì nâng lên `FINAL` (bước 4 cũ "xóa nguồn 2 đã có lịch sử" bỏ). Dòng `FINAL` nguồn 2 mà không
   còn dòng lịch sử nào trỏ `po_item_id` đó (hiếm: hoàn tác nhập ĐMH) thì trả về `OPEN` rồi để sync quyết.
5. Mốc Misa (`misa_cutoff_condition`): sau mốc chỉ nhận `source_type = 2` — bỏ vế `doc_id > 0`. Cùng kết quả vì dòng lịch sử
   system nào cũng có ĐMH; chỉ còn hai cột trong chỉ mục phủ.
6. Thứ tự "gần nhất" giữ `(ngày, doc_id, id)` — không đổi chỉ mục; lý do cũ của `doc_id` hết, nhưng đổi chỉ mục không đáng.

## API (giữ tương thích v1 + v2)
Mọi dòng trả về thêm `line_stage` (số) và `is_open` (`source_type == 2 and line_stage == OPEN`). Sửa bốn chỗ ở giao diện
(hai v1, hai v2) từ `source_type === PO_LINE` sang `is_open`. Nhãn cột "Nguồn" khi xuất Excel (`export_columns.py`) tính từ cặp
(`source_type`, `line_stage`): ERP + Đang mở = "Dòng đơn mua hàng", ERP + Đã chốt và nguồn 1 = "Lịch sử mua hàng", 3 = "Sổ Misa"
— chữ người dùng thấy không đổi. Khóa xếp `source` xếp theo cùng nhãn đó (luật §8). Soát `assistant/tools/packaging_cost_tool.py`.

## Migration (`opt784`, phần sổ giá) — viết tay
Lên:
1. `add_column line_stage SMALLINT NOT NULL server_default '2'`; `UPDATE ... SET line_stage = 1 WHERE source_type = 2`.
2. Kiểm va chạm: đếm dòng nguồn 2 có `source_id` trùng `po_item_id` của một dòng nguồn 1 system — theo luật cũ phải 0; >0 thì
   xóa dòng nguồn 2 đó (lịch sử thắng, đúng bước 4 cũ) và in số dòng.
3. `UPDATE L JOIN tab_purchase_history PH ON L.source_type = 1 AND L.source_id = PH.id AND PH.po_item_id IS NOT NULL
   SET L.source_type = 2, L.source_id = PH.po_item_id, L.line_stage = 2` (MySQL `UPDATE ... JOIN`; SQLite dùng truy vấn con —
   tách hàm nhận kết nối như `bompart784` để bài kiểm gọi thẳng).
4. Bỏ `server_default` của `line_stage` (ghi mới phải đặt rõ).
Xuống: đảo 3 (`source_type = 2 AND line_stage = 2` nối `PH.po_item_id = L.source_id` → `(1, PH.id)`), dòng `FINAL` không có lịch sử
thì để nguồn 2; xóa cột. Local: 87 dòng đổi nguồn. Dev: chạy đếm trước (chỉ đọc) theo câu ở bước 2–3.

## Tệp sửa
- `product_price/model.py` (cột, chú thích nguồn) · `core/packaging_price_codes.py` (nhãn, `LedgerLineStage`) · chạy `gen_status_ts.py`
- `product_price/ledger_sync_service.py` (luật 1–4; bỏ truy vấn `covered`, còn 2 truy vấn mỗi đơn) · `ledger_stats.py`
- `product_price/misa_cutoff.py` (luật 5) · `purchase_history/service.py` (chỉ tên hàm gọi, giữ savepoint)
- `packaging_cost/history_page_rows.py`, `last_prices_service.py`, `export_columns.py`, `impact_service.py` nếu trả `source_type`
- `scripts/backfill_product_price_ledger.py` (thứ tự bước) · FE: 2 tệp v1 + 2 tệp v2 + kiểu dữ liệu `packaging-cost-types.ts` cả hai
- Bài kiểm: `so_gia_factory_cr784.py` + khoảng 7 tệp `test_*_cr784.py` đang dựng nguồn 1 / 2 (`test_so_gia_*`, `test_nguon_misa_*`,
  `test_trang_thai_gia_*`, `test_lich_su_mua_*`, `test_gia_tri_mua_*`, `test_nhap_bao_gia_va_so_misa_*`)

## Bài kiểm (mới / sửa)
- Duyệt ĐMH → 1 dòng `OPEN`; sửa giá → cùng id; hoàn thành → cùng id, `FINAL`, `amount` theo lịch sử; hủy ĐMH sau đó → dòng còn.
- Lịch sử hỏng ngày → dòng giữ `OPEN`. Nạp lại legacy → chỉ nguồn 1 đổi, nguồn 2 không đụng.
- Mốc Misa: dòng ERP `FINAL` sau mốc được tính, legacy sau mốc bị loại (so với kết quả trước khi gộp trên cùng dữ liệu).
- Migration lên / xuống trên dữ liệu mẫu: số dòng, tổng giá, tập `(product_code, price_date, price)` không đổi.
- Đếm truy vấn của `sync_po_price_ledger` = 2 cố định; các bài đếm truy vấn màn giá giữ nguyên.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Sót chỗ ghi sổ còn chèn nguồn 1 cho dòng system | Trung bình x Cao | grep `PURCHASE_HISTORY` toàn backend; bài canh: không dòng nguồn 1 nào có `doc_id > 0` |
| bao-CR-789 đang sửa cùng `purchase_history/service.py` | Trung bình x Trung bình | gộp `origin/erp-v2` trước khi làm, giữ nguyên khối savepoint |
| Giao diện v1 sót, mất dấu "ĐMH đang mở" | Thấp x Thấp | bài vitest v2 + soát tay v1 (devthumua) |

## Việc cần làm
- [x] Chủ dự án chốt C1: gộp (25/11/2026)
- [ ] Migration phần sổ giá + hàm chuyển dữ liệu có bài kiểm
- [ ] Sửa sync / mốc Misa / lịch sử / backfill
- [ ] API `line_stage` + `is_open`, FE v1 + v2
- [ ] Bài kiểm cụm sổ giá xanh, đếm truy vấn không tăng
