# Phase 02 — Sổ giá: gộp nguồn lịch sử mua (system) và dòng ĐMH thành một dòng theo `po_item_id`

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784, bao-CR-789 |
| 2 | 25/11/2026 | fullstack | **Xong trên nhánh `duoc-cr784-opt-p02`** (chưa commit, chưa deploy dev) | duoc-CR-784 |

Trạng thái: **XONG phần mã, kiểm thử và đối chiếu trên bản sao dữ liệu local (25/11/2026)**, chưa commit / deploy — xem mục *Kết quả* cuối tệp.

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

## Migration (`srcmerge784`, phần sổ giá) — viết tay
> Đổi 25/11/2026: mỗi phase một migration riêng nên phase này là revision **`srcmerge784`** (`down_revision = bompart784`), không còn chung `opt784`.
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
- [x] Migration phần sổ giá + hàm chuyển dữ liệu có bài kiểm (`srcmerge784`, hàm `merge_history_sources` / `split_history_sources`)
- [x] Sửa sync / mốc Misa / lịch sử / backfill
- [x] API `line_stage` + `is_open`, FE v1 + v2
- [x] Bài kiểm cụm sổ giá xanh, đếm truy vấn không tăng (sync mỗi đơn còn 2 truy vấn, trước 3)
- [ ] Sao lưu DB dev, deploy dev, chạy `backfill_product_price_ledger --check` (xem *Việc phải làm trên dev*)

## Kết quả (25/11/2026)
**Đã làm gì và vì sao.** Một lần mua của hệ thống từng nằm ở hai dòng sổ (nguồn 2 khi đang mở, bị xóa rồi chèn lại thành nguồn 1 lúc hoàn
thành, id mới). Nay là MỘT dòng nguồn 2 theo `po_item_id` suốt đời, id giữ nguyên, cột mới `line_stage` (1 Đang mở · 2 Đã chốt); nguồn 1
chỉ còn lịch sử cũ nạp Excel. Những chỗ vá vì việc tách (`doc_id` chen vào thứ tự, vế `doc_id > 0` của mốc Misa, truy vấn `covered`, bước xóa
nguồn 2 đã có lịch sử) đã bỏ.

| Hạng mục | Kết quả |
|---|---|
| Cấu trúc | `tab_product_price_ledger.line_stage SMALLINT NOT NULL`, KHÔNG mặc định (ghi mới phải đặt rõ: ba nơi ghi — đồng bộ ĐMH / lịch sử, nạp Misa HTML, nạp Misa Excel — đều đặt). `IntEnum LedgerLineStage {OPEN = 1, FINAL = 2}` + bộ mã `ledger_line_stage`, đã sinh lại `statuses.ts` bằng `gen_status_ts.py`. Không thêm chỉ mục |
| Đồng bộ | `sync_po_price_ledger`: chỉ đụng dòng `OPEN`, bỏ qua dòng `FINAL` (kể cả ĐMH sau đó hủy / xóa mềm); 2 truy vấn mỗi đơn. `record_history_row` (gọi từ `snapshot_line`, giữ nguyên khối savepoint của bao-CR-789): cập nhật CHÍNH dòng `(2, po_item_id)` bằng số chụp rồi `FINAL`, chưa có dòng thì chèn `FINAL`, lịch sử hỏng ngày / giá thì giữ dòng `OPEN`. `sync_history_ledger`: dọn mồ côi (cả dòng nguồn 1 sai dạng trỏ vào lịch sử có ĐMH), trả dòng chốt không còn lịch sử về `OPEN`, chèn dòng thiếu / nâng dòng đang mở lên `FINAL`, điền kho + thành tiền cho dòng chốt. `eligible_po_ids` chỉ xét dòng còn `OPEN`. Số đếm mới `finalized`, `reopened` thay `deleted_covered_po_lines` |
| Mốc Misa | sau mốc chỉ nhận `source_type = 2` (bỏ vế `doc_id > 0`) |
| API | mỗi dòng Lịch sử mua hàng thêm `line_stage`, `is_open`; nhãn cột Nguồn (màn hình, Excel, công cụ AI `source_label`) giữ nguyên chữ, tính từ cặp (nguồn, giai đoạn) bằng `price_source_text`; khóa xếp `source` theo thứ tự lịch sử < ĐMH mở < Misa. `PricePoint` / `LedgerRow` mang thêm `line_stage` (không thêm truy vấn) |
| Giao diện | v1 (`PackagingHistoryTable`, `PackagingHistoryPrintParts`) và v2 (`packaging-history-cells`, `packaging-history-print-parts`) đánh dấu "ĐMH đang mở" theo `row.is_open`; bỏ hằng `PRICE_SOURCE_PO_LINE` của v1 |
| Migration `srcmerge784` | Lên: thêm cột, dòng nguồn 2 sẵn có = `OPEN`, xóa dòng nguồn 2 va chạm (lịch sử thắng, in số dòng), nguồn 1 có ĐMH -> `(2, po_item_id, FINAL)` giữ id. Xuống: dòng nguồn 2 đã chốt có lịch sử -> `(1, id lịch sử)`, bỏ cột. Chạy thật trên bản sao MySQL: lên -> xuống -> lên; băm nội dung sổ (mã, ngày, giá, SL, VAT, thành tiền, kho, NCC) giống hệt cả ba lần, băm `(id, nguồn, source_id)` sau khi xuống giống hệt trước khi lên; ca va chạm (chèn tay 3 dòng) xóa đúng 3 |
| Số dòng local | 87 dòng nguồn 1 có ĐMH đổi thành nguồn 2 `FINAL`; 6.418 nguồn 1 (lịch sử cũ) + 14 nguồn 2 `OPEN` + 5.041 Misa giữ nguyên; tổng 11.560 không đổi, va chạm 0 |

**Đối chiếu cũ / mới** (cùng bản sao dữ liệu local 11.560 dòng, mã cũ + lược đồ cũ so với mã mới + đã migrate; Tác động 500 mã, Tổng hợp theo
sản phẩm x2, Bảng giá phạm vi bom + all + trang, Giá mua gần nhất x2, Lịch sử theo mã (tất cả, 1.000 dòng, riêng NHG3790, xếp `source` hai chiều)
và theo sản phẩm (tất cả, mẫu 20 sản phẩm, có chữ tìm, xếp `source`), 40 dòng đầu tệp Excel Lịch sử, mọi dòng ba lần mua / công cụ AI của 520 mã,
`backfill --check`; chạy hai vòng: dữ liệu thô và sau `backfill --apply`):
- GIỐNG HỆT từng byte: Tác động, Tổng hợp, Bảng giá, Giá mua gần nhất, Excel, công cụ AI.
- Khác đúng theo thiết kế: mỗi dòng Lịch sử mua hàng thêm `line_stage` + `is_open`; `source_type` của dòng lịch sử hệ thống đổi 1 -> 2 (87 dòng); tên khóa số đếm của `backfill`. Sau khi chuẩn hóa (bỏ hai trường mới, 2 + `FINAL` -> 1) JSON Lịch sử khớp hoàn toàn, **cùng thứ tự id**, số dòng `is_open` đúng bằng số dòng nguồn 2 cũ.
- `backfill --check`: bản cũ báo 6.505 thay đổi trên dữ liệu thô (thành tiền chưa điền ở local), bản mới báo cùng 6.505 (`updated_amount`); sau `--apply` cả hai về 0.
- Lưu ý: khi chưa cố định `PYTHONHASHSEED`, ô chọn nhà cung cấp của Giá mua gần nhất có thể đổi thứ tự / tên giữa hai lần chạy (cùng mã, hai tên) — lỗi sẵn có của `supplier_options` (duyệt tập), không liên quan phase này.

**Tốc độ** (trung vị 5 lần, bản sao local, MySQL 8, cũ -> mới): Lịch sử theo sản phẩm tất cả 142 -> 121 ms · Lịch sử theo mã tất cả 62 -> 64 ms ·
Tác động 500 mã 90 -> 90 ms · Bảng giá phạm vi all 88 -> 72 ms · số truy vấn mọi màn không đổi · `sync_po_price_ledger` 3 -> 2 truy vấn mỗi
đơn, `backfill --check` 289 -> 201 truy vấn (88 đơn). Chênh lệch nhỏ nằm trong dao động đo; không có hồi quy.

**Bài kiểm.** Backend: 1.005 qua, 5 bỏ qua (cụm `cr784` / `cr789`, phạm vi khai đủ B-07, độ dài ô chữ CR-538, bộ mã trạng thái, đồng bộ giao diện
v2, công cụ Trợ lý, sắp xếp màn Thu mua, lịch sử mua hàng, phạm vi Thu mua) + 225 bài phạm vi / lịch sử liên quan. Mới: `test_gop_nguon_so_gia_cr784.py`
(vòng đời mở -> chốt giữ id -> đóng băng, hủy / xóa mềm sau chốt, hai truy vấn cố định, script dựng lại từ số không ra đúng khóa cũ và `--check` = 0,
bài canh không dòng nguồn 1 nào mang ĐMH, API `line_stage` / `is_open`, khóa xếp `source`, nhãn Excel / công cụ AI, bộ mã, migration lên / xuống /
lên trên SQLite kèm ca va chạm). Sửa các bài cũ dựng nguồn 1 + `doc_id` làm "lịch sử hệ thống" sang nguồn 2 `FINAL`; sửa `half_then_boom` (bài savepoint
bao-CR-789) để dòng ghi dở thật sự có `line_stage`. Giao diện: v2 `tsc` 0 lỗi, eslint các tệp đổi sạch, vitest `src/modules/procurement` 188 tệp / 1.806 bài qua;
v1 `tsc` đúng 4 lỗi cũ. ruff `app` + script + migration sạch.

**Khác kế hoạch (đã chốt khi làm).**
1. Mỗi phase một migration (`srcmerge784`), không chung `opt784`.
2. `ledger_sync_service.py` KHÔNG tách (đã 330 dòng từ trước): nhiều bài kiểm `monkeypatch` thẳng `sync.record_history_row`; tách thì phải sửa hàng chục chỗ mà không bớt rủi ro. Việc tách để dịp khác.
3. Nhãn bộ mã `price_source_type` đổi theo bảng *Mô hình đích* (*Lịch sử mua hàng cũ (nạp Excel)*, *Đơn mua hàng ERP*) nhưng chữ thấy được ở cột Nguồn giữ nguyên nhờ `price_source_text`; công cụ Trợ lý cũng đi qua hàm này (phát hiện khi soát: nếu dùng thẳng nhãn bộ mã thì `source_label` đổi chữ).
4. Khóa xếp `source` dùng biểu thức hạng (1 / 2 / 3) thay cho cột `source_type` để đúng nhãn đang hiện.
5. `reopened` (dòng chốt mất lịch sử -> về `OPEN`) xóa luôn `amount` để dòng đang mở không giữ số chốt.
6. Thứ tự "gần nhất" `(ngày, doc_id, id)` giữ nguyên (luật 6): hai lần mua cùng ngày cùng mã của CÙNG một ĐMH nay xếp theo id lúc duyệt thay vì id lúc hoàn thành — hiếm, chấp nhận.
7. Hệ quả nhỏ của luật 5: dòng lịch sử cũ (nguồn 1) mang `doc_id > 0` mà không có ĐMH (dữ liệu hỏng, local không có) trước đây còn được tính sau mốc Misa, nay bị loại; xem câu kiểm bên dưới.

## Việc phải làm trên dev (trước khi lên prod)
1. **Sao lưu DB dev** (migration xóa / đổi khóa dòng sổ giá; sổ giá dựng lại được bằng script nhưng vẫn sao lưu).
2. Chạy thử, chỉ đọc, đếm trước: va chạm (`SELECT COUNT(*) FROM tab_product_price_ledger l2 JOIN tab_purchase_history ph ON ph.po_item_id = l2.source_id JOIN tab_product_price_ledger l1 ON l1.source_type = 1 AND l1.source_id = ph.id WHERE l2.source_type = 2` — kỳ vọng 0) và dòng nguồn 1 sai dạng (`... WHERE l.source_type = 1 AND l.doc_id > 0 AND ph.po_item_id IS NULL` — kỳ vọng 0; > 0 thì xem lại trước khi lên).
3. Khởi động lại `api` (`start.sh` tự chạy `alembic upgrade head`; nối đúng sau `bompart784`, một head duy nhất); log in dòng `[srcmerge784] xoa N dong ... gop M dong ...`.
4. `docker compose exec -T api python -m scripts.backfill_product_price_ledger --check` (thành tiền của dòng chưa điền có thể báo thay đổi — chạy `--apply` một lần rồi `--check` phải ra 0).
5. Mở màn Lịch sử mua hàng v1 (devthumua, nhớ Tải lại) và v2 (deverp): dòng ĐMH đang mở có nhãn *ĐMH đang mở*, dòng đã hoàn thành chỉ có số ĐMH bấm được.
6. Quay lui: `alembic downgrade bompart784` (tách lại nguồn 1 cho dòng chốt có lịch sử) + revert commit; sổ giá sai thì `backfill --apply` dựng lại.
