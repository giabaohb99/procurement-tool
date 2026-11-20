# Phase 02 — BE đồng bộ sổ giá + script nạp lại

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P1 trong kế hoạch (sai ở đây là giá sai im lặng) · 6 giờ · cần phase 01.

## Bối cảnh (đã soát mã)
- Mọi dòng lịch sử **system** đi qua MỘT hàm `purchase_history/service.py::snapshot_line` (gọi từ
  `progress_service.auto_advance_line:103`, `import_tool/po_import.py:342`, `scripts/backfill_purchase_history.py:190`,
  `seed_demo_purchase_history.py`). Dòng **legacy** chỉ từ `scripts/import_purchase_history_legacy.py`, script này
  `DELETE ... WHERE source='legacy'` rồi nạp lại → id đổi mỗi lần chạy.
- Dòng ĐMH đổi giá / SL / VAT / trạng thái ở: `item_service._save_items` (+ `_delete_dropped_items`),
  `reprice_service.reprice_po` (tệp **chưa commit** của phiên khác), `import_tool/po_import.upsert_item:240-269`,
  `import_tool/service._revert_po:323-343`, `progress_service.set_item_progress` (hủy / tạm ngưng dòng),
  `edit_service.set_status` (duyệt / từ chối / hủy / bỏ duyệt qua `unapprove_po`), `edit_service.delete_po` (xóa mềm).
- Mỗi chỗ đó (trừ import) đều gọi `_sync_pr(db, po.pr_code)` ngay sau → đó là **mốc gắn hook** tự nhiên.
- Đồng bộ YCMH chỉ tính ĐMH `status NOT IN PO_PENDING_STATUSES + PO_DEAD_STATUSES` (`line_status_service.py:49-50`) và
  `is_deleted = False` — dùng lại đúng hai hằng đó (DRY).

## Luật sổ giá
- Nguồn 1 (lịch sử): **mỗi dòng `tab_purchase_history` một dòng sổ**, chỉ chèn, không sửa. Ngoại lệ duy nhất: dòng lịch sử
  bị xóa (nạp lại legacy) thì dòng sổ mồ côi bị xóa theo.
- Nguồn 2 (ĐMH): dòng có trong sổ **khi và chỉ khi** ĐMH được tính (đã duyệt trở đi, chưa xóa mềm) AND dòng chưa hủy AND
  `product_code` khác rỗng AND **chưa có** dòng lịch sử cho `po_item_id` đó. Đổi giá / SL / VAT / NCC / ngày / tỉ giá
  thì cập nhật đúng dòng sổ đó (id giữ nguyên).
- Giá sổ = `price x exchange_rate` (VNĐ). Legacy coi là VNĐ. Dòng giá 0 vẫn ghi (đếm "số lần mua"), tầng tính giá bỏ qua.

## Kiến trúc — `backend/app/modules/product_price/ledger_sync_service.py` (< 200 dòng)
| Hàm | Làm gì | Gọi từ |
|---|---|---|
| `record_history_row(db, ph, exchange_rate)` | chèn dòng nguồn 1 (bỏ qua nếu đã có) + xóa dòng nguồn 2 cùng `po_item_id`. Chỉ `add`/`delete`, không commit | `snapshot_line` sau `db.add(obj)` + `db.flush()` để có id |
| `sync_po_price_ledger(db, po, commit=True)` | dựng tập dòng đủ điều kiện của MỘT đơn (1 truy vấn dòng + 1 truy vấn id lịch sử + 1 truy vấn dòng sổ `doc_id=po.id, source_type=2`), chèn / cập nhật / xóa chênh lệch | ngay sau mọi `_sync_pr(` ở `purchase_order/*`; `po_import` sau `recompute_effects`; `_revert_po` |
| `sync_history_ledger(db, dry_run=False) -> dict` | toàn bảng: xóa dòng nguồn 1 mồ côi (anti-join), chèn dòng lịch sử còn thiếu theo lô 1000; tỉ giá lấy LEFT JOIN `tab_po_item` (thiếu → 1, đếm) | script nạp lại, cuối `import_purchase_history_legacy.py`, script backfill |
| `_ledger_values_from_line(po, item)` / `_ledger_values_from_history(ph, rate)` | một chỗ chuyển đổi (ngày chuỗi → Date, quy VNĐ) | nội bộ — DRY cho cả ba hàm |

Lỗi ở hook KHÔNG được chặn luồng mua hàng: `sync_po_price_ledger` bọc `try/except` + `log.exception` giống `_sync_pr`,
và tự `rollback` phần của mình khi `commit=True`. Trong `snapshot_line` tránh lỗi bằng cách **kiểm tồn tại trước** (không
dựa vào lỗi unique) — một flush hỏng giữa `auto_advance_line` làm hỏng cả phiên.

## Tệp
- Tạo: `backend/app/modules/product_price/ledger_sync_service.py`, `backend/scripts/backfill_product_price_ledger.py`,
  `test/backend/test_so_gia_san_pham_cr784.py`, `test/backend/test_moc_dong_bo_so_gia_cr784.py` (bài canh tĩnh).
- Sửa (mỗi tệp chỉ thêm lời gọi): `purchase_history/service.py` (`snapshot_line`), `purchase_order/edit_service.py`
  (`create_po`, `update_po`, `delete_po`, `set_status`), `purchase_order/progress_service.py` (`apply_auto_progress`,
  `set_item_progress`), `purchase_order/reprice_service.py` (`reprice_po` — **chờ tệp này lên erp-v2**),
  `import_tool/po_import.py` (`run`), `import_tool/service.py` (`_revert_po`), `scripts/import_purchase_history_legacy.py`.

## Các bước
1. Viết `ledger_sync_service.py` + bài kiểm đơn vị cho từng hàm (SQLite).
2. Gắn `record_history_row` trong `snapshot_line` (sau add + flush; truyền `item.exchange_rate`).
3. Gắn `sync_po_price_ledger(db, po)` ngay sau từng `_sync_pr(` ở `purchase_order/*`; ở `po_import.run` gọi cho từng `po`
   sau vòng `auto_advance_line` (chỉ khi `apply`); ở `_revert_po` sau khi xóa dòng.
4. Cuối `import_purchase_history_legacy.py` (sau `db.commit()` cuối): `sync_history_ledger(db)` và in số đếm.
5. Script `backfill_product_price_ledger.py`: cờ `--dry-run` (mặc định khi không truyền `--apply`) và `--check` (exit 1 nếu
   lệch — dùng làm kiểm định kỳ). Bước: `sync_history_ledger` → lặp mọi ĐMH được tính có dòng mở → `sync_po_price_ledger(commit=False)`
   theo lô 200 đơn, commit mỗi lô. In: chèn / cập nhật / xóa theo nguồn, dòng ngày hỏng, dòng ngày tương lai (Q5), dòng
   giá 0, dòng ngoại tệ, dòng thiếu `tab_po_item`.
6. Bài canh tĩnh: mọi hàm trong `purchase_order/*.py` có `_sync_pr(` phải có `sync_po_price_ledger(` (đọc AST, liệt kê
   miễn trừ kèm lý do nếu có).

## Bài kiểm (`test_so_gia_san_pham_cr784.py`)
- Duyệt ĐMH → có dòng nguồn 2; đơn nháp / chờ duyệt / từ chối → không có; bỏ duyệt → mất.
- Sửa đơn giá / SL / VAT → cùng id dòng sổ, giá trị mới; xóa dòng ĐMH → mất; hủy dòng (`set_item_progress`) → mất;
  hủy đơn / xóa mềm → mất hết dòng của đơn.
- Dòng ngoại tệ USD tỉ giá 25.000, đơn giá 2 → sổ 50.000.
- Dòng vào `completed` qua `auto_advance_line` → có nguồn 1, mất nguồn 2; gọi `sync_po_price_ledger` lần nữa không dựng lại.
- `reprice_po` đổi giá → cập nhật; `po_import` (apply) → có dòng; dry-run import → không có.
- Nạp lại legacy giả lập (xóa + chèn lại lịch sử legacy) → `sync_history_ledger` xóa mồ côi, chèn mới; chạy lần hai = 0 thay đổi.
- `snapshot_line` khi hook lỗi (giả lập) không chặn `auto_advance_line`.

## Kiểm xong
- Hai tệp bài kiểm xanh + `test_chup_ket_qua_luu_dong_sinh_don_cr715.py` (bài chụp `_save_items`) vẫn xanh.
- Script chạy `--dry-run` rồi `--apply` trên local, chạy lại `--check` exit 0.

## Rủi ro
| Rủi ro | KN x AH | Giảm thiểu |
|---|---|---|
| Sót một chỗ sửa dòng ĐMH → giá cũ treo trong sổ | TB x Cao | Bài canh tĩnh `_sync_pr` ↔ hook; `--check` định kỳ; script là bộ hòa giải |
| `reprice_service.py` chưa commit (phiên khác) | Cao x TB | Gắn hook sau khi tệp lên erp-v2; nếu phase 02 đi trước thì ghi việc treo cho chủ CR reprice |
| Nạp lại legacy làm mồ côi dòng sổ | Chắc chắn x Cao | `sync_history_ledger` cuối script + bài kiểm giả lập |
| Tỉ giá: lịch sử không lưu tiền tệ | TB x Cao | Lấy `tab_po_item.exchange_rate` lúc chụp / LEFT JOIN lúc backfill, đếm dòng thiếu |
| Hook ghi làm chậm lưu ĐMH | Thấp x Thấp | 3 truy vấn cố định mỗi đơn, không phụ thuộc số dòng |

## Quay lui
Bỏ các lời gọi (revert commit) — luồng mua hàng không đọc sổ giá nên không gãy gì. Dữ liệu sổ dựng lại bằng script.
