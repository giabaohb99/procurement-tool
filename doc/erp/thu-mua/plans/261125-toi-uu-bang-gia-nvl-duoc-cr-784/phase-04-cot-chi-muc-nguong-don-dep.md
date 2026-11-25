# Phase 04 — Cột, chỉ mục, BỎ ngưỡng sàn / trần và dọn nhỏ

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |
| 2 | 25/11/2026 | fullstack | **Xong trên nhánh `duoc-cr784-opt-p04` (chưa commit, CHƯA lên dev)** — migration `cleanup784` | duoc-CR-784 |

Ưu tiên P3 · 4,5 giờ (2,5 + 2 gỡ ngưỡng) · cần phase 03 (cùng migration `opt784`).

## Liên kết
`product_price/model.py`, `misa_ledger_import.py`, `packaging_cost/misa_xlsx_import.py`, `scripts/import_misa_price_ledger.py`,
`latest_priced_query.py`, `price_state_service.py`, `packaging_cost/history_page_rows.py`, `core/scoping.py` (`packaging_cost`).

## Soát từng cột của sổ giá (kết luận: kiểu dữ liệu đã đúng, không đổi kiểu)
| Cột | Kiểu | Số liệu local | Kết luận |
|---|---|---|---|
| `price` | Numeric(18,4) | Misa có 902 dòng giá lẻ đồng; ĐMH ngoại tệ x tỉ giá ra lẻ | giữ 4 số lẻ (đơn giá, không phải tiền — luật 18,2 là cho thành tiền) |
| `amount` | Numeric(18,2) NULL | nguồn 2 luôn NULL (cố ý) | giữ |
| `qty` | Numeric(18,3) | max 8.000.000, 68 dòng lẻ | giữ |
| `vat` | Numeric(5,2) | Misa luôn 0 = không biết | C7 ĐÃ CHỐT: NULL ở Misa, giao diện hiện trống |
| `unit` | String(25) | 223 dòng legacy rỗng | giữ (cảnh báo lệch ĐVT cần) |
| `supplier_code` / `supplier_name` | 50 / 200 NULL | `supplier_name` chỉ Misa (mã Misa không có trong `tab_supplier`) | giữ, là phi chuẩn hóa CÓ LÝ DO |
| `warehouse_name` | String(200) NULL | lưu TÊN; nguồn 1 / 2 tra tên từ mã kho | giữ (Misa chỉ có tên); đổi tên kho thì `backfill` tự sửa |
| `company_id` | BIGINT default 0 | 1 dòng nguồn 2 = 0 | giữ; dòng 0 vô hình với phạm vi pháp nhân — sync ghi cảnh báo log khi ĐMH không có pháp nhân |
| `doc_id` | BIGINT, chỉ mục đơn | 11.459 / 11.560 dòng = 0 | giữ; chỉ dùng `doc_id = id ĐMH` (sync) và nối số ĐMH |
| `synced_at` | DateTime, `server_default now()` + `default=datetime.utcnow` | lệch múi (máy chủ DB vs UTC) | bỏ `default=` phía Python, ghi đè dùng `func.now()` |
| `line_stage` | (phase 02) | | |

Không bỏ cột phi chuẩn hóa nào: ba cột chép theo dòng đều là dữ liệu Misa không tra được ở danh mục. Không đặt cột giá lên
`tab_product`, không FK sang `tab_product` (D-025).

## Chỉ mục sổ giá (giữ nguyên bộ hiện tại)
| Chỉ mục | Câu dùng | Kết luận |
|---|---|---|
| `uq_ppl_source (source_type, source_id)` | khóa đồng bộ, nối mồ côi, `max(source_id)` của Misa | giữ — là bảo đảm idempotent |
| `ix_ppl_code_latest (mã, ngày, doc_id, id, price, company_id, source_type)` | mọi truy vấn "n lần gần nhất", số gộp, mốc Misa, `seq` / `prev_price` | giữ (phủ đủ; sau phase 02 mốc Misa còn đọc ít cột hơn) |
| `ix_ppl_date_latest (ngày, doc_id, id)` | "lần đầu / gần nhất" không theo mã, lọc khoảng ngày Misa xlsx | giữ |
| `ix_..._doc_id (doc_id)` | sync theo đơn | giữ |

Không thêm chỉ mục `supplier_code`: lọc NCC luôn đi kèm tập mã nên đọc theo chỉ mục mã rồi lọc.

## Bảng tóm tắt "giá gần nhất mỗi mã" / cột sinh (C9 ĐÃ CHỐT 25/11: không làm)
Đường nóng đã đo 6,7 s → 0,24 s trên dev (LATERAL + chỉ mục phủ). Bảng tóm tắt phải giữ theo pháp nhân x mã, đổi theo mốc
Misa (thay mốc = dựng lại cả bảng) và ba đường ghi — rủi ro sai im lặng lớn hơn lợi. Cột sinh không làm được vì mốc nằm ở
`tab_setting`. Làm lại khi p95 màn giá trên prod > 1 s.

## Ngưỡng `tab_product_price_limit` — BỎ HẲN (C6, anh chốt 25/11/2026)
Lý do: đang tắt ở cả hai giao diện từ 21/11, 0 dòng, nhưng vẫn tốn một truy vấn mỗi lần tính giá và còn lòi ra hai cột trống
trong Excel Bảng giá VTBB + hai trường rỗng trong công cụ Trợ lý / MCP. Min / Max tự tính từ sổ giá GIỮ NGUYÊN (không liên
quan bảng này). Cần lại thì làm lại (ước 3–4 giờ).

Phạm vi gỡ:
| Khu | Gỡ gì |
|---|---|
| Model / migration | `ProductPriceLimit` khỏi `product_price/model.py` + `core/all_models.py`; `opt784` DROP `tab_product_price_limit` (downgrade dựng lại bảng rỗng đúng cấu trúc cũ) |
| API | router `/api/product-price-limits` trong `quote_limit_controller.py` (giữ router báo giá), schema Limit*, mục khai trong `main.py` nếu tách |
| Tính giá | truy vấn ngưỡng + trường `floor` / `ceiling` trong `price_state_service.py`; luật cảnh báo `BELOW_FLOOR` (6) / `ABOVE_CEILING` (7) ở `cost_service` / `impact_service` / `price_list_service`; bộ lọc "chỉ mã ngoài ngưỡng" (tham số + điều kiện) |
| Bộ mã | `CostWarning` 6, 7: bỏ khỏi bộ mã nhưng GHI CHÚ số đã cấp không tái dùng; chạy `gen_status_ts.py` |
| Excel | cột `floor` / `ceiling` trong `export_columns.py` |
| Trợ lý / MCP | trường `floor_price` / `ceiling_price` trong `assistant/tools/packaging_cost_format.py`; sửa `doc/agent-hub/06-cong-mcp.md`, `doc/erp/tro-ly-ai/.../02-danh-sach-api-tool.md`, bài kiểm sổ công cụ |
| v1 | `utils/packaging-flags.ts` (bỏ `PACKAGING_LIMITS_ENABLED`), `components/packaging/PackagingLimitModal.tsx`, cột / nút / ô lọc ở `PackagingPriceList.tsx` và `PackagingImpactSelectedTable.tsx`, bản in, kiểu ở `api/packaging-cost-types.ts`, hàm gọi ở `api/packaging-cost.ts` |
| v2 | `config/packaging-feature-flags.ts`, cột `limit`, hộp thoại ngưỡng, ô lọc, kiểu ở `types/packaging-cost-types.ts`, hàm ở `api/packaging-cost-api.ts`, bài kiểm vitest liên quan |
| Tài liệu | `21-tac-dong-gia-bao-bi.md`, `api.md`, HDSD `seed_help_gia_bao_bi_cr784.py`, cẩm nang trợ lý (mục Giá NVL) |

Khóa quyền `packaging_cost` không đổi (ngưỡng dùng chung khóa này, không có entity riêng).

## Dọn nhỏ không đổi cấu trúc
1. **Hai đường nạp Misa đá nhau.** Script HTML (`import_misa_price_ledger.py`) dùng id Misa thật và XÓA mọi dòng Misa không có
   trong tệp; module 6 (xlsx) tự đánh `source_id = max + 1`. Chạy script sau module 6 là mất dòng xlsx. Đề xuất: script HTML từ
   chối chạy khi sổ đã có dòng Misa do module 6 nạp (hoặc gỡ script, module 6 là đường chính). Ghi nghĩa `source_id` của Misa
   = số thứ tự trong sổ, không trỏ chứng từ.
2. Chú thích đầu `product_price/model.py` cập nhật bảng nguồn (phase 02, 03).
3. `ProductPriceLedger.supplier_name` / `warehouse_name`: thêm hằng độ dài dùng chung thay vì lặp 200 ở ba tệp.

## Migration (`opt784`, phần cuối)
DROP `tab_product_price_limit` (xuống: dựng lại bảng rỗng). Chỉ khi C7 = A: `alter_column vat` cho phép NULL; `UPDATE ... SET vat = NULL WHERE source_type = 3`; nhập Misa ghi NULL. Xuống:
`vat = 0` rồi NOT NULL. Không có gì khác (synced_at chỉ sửa ORM).

## Bài kiểm
- C7 = A: dòng Misa VAT trống ở Lịch sử + Excel; số gộp không đổi.
- Script HTML gặp sổ có dòng module 6 → dừng với câu tiếng Việt.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Sót chỗ đọc `floor` / `ceiling` (Excel, công cụ AI, bản in) | Trung bình x Thấp | grep `floor\|ceiling\|LIMITS_ENABLED\|product-price-limits` cả ba khu sau khi gỡ |
| Chỗ đọc `vat` coi None là lỗi | Trung bình x Thấp | grep `.vat` trong `packaging_cost/`, `num(None)` đã trả None |

## Việc cần làm
- [x] Chốt C6: bỏ hẳn ngưỡng (25/11/2026)
- [x] Chốt C7 (VAT Misa NULL), C9 (không làm bảng tóm tắt) — 25/11/2026
- [x] Chốt C5 (khóa duy nhất báo giá) — làm ở phase 03
- [x] Gỡ ngưỡng sàn / trần (backend, v1, v2, Excel, Trợ lý / MCP, tài liệu)
- [x] `synced_at` một nguồn giờ
- [x] Chặn hai đường nạp Misa đá nhau
- [x] (C7 = A) VAT Misa NULL
- [x] Sửa lỗi sẵn có của phase 02: ô chọn nhà cung cấp Giá mua gần nhất đổi thứ tự / tên giữa các lần chạy

## Kết quả thực hiện (25/11/2026)
### Đã gỡ (C6)
| Khu | Gỡ gì |
|---|---|
| Model / API | `ProductPriceLimit` (model), `LimitCreate` / `LimitUpdate` / `LimitOut` + `_check_floor_ceiling` (schema), `limit_router` + hàm `_limit_*` trong `quote_limit_controller.py` (giữ `quote_router`; tên tệp giữ để khỏi đổi đường dẫn), mục khai ở `main.py`, bí danh nhật ký `packaging_cost_limit` ở `audit/controller.py` |
| Tính giá | truy vấn ngưỡng + `floor` / `ceiling` của `PriceState` (`get_price_states` còn tối đa 4 truy vấn, trước 5); `price_warnings(price, purchase_unit)` bỏ tham số `applied` và hai luật 6 / 7; `breach_only` (tham số + `BREACH` + nhánh đường nhanh) ở `price_list_service` / `impact_controller` (gửi lên vẫn được nhận, bị bỏ qua); `floor` / `ceiling` khỏi `impact_service.selected_row` và `price_list_service._row` / `SORT_KEYS` |
| Bộ mã | `CostWarning.BELOW_FLOOR` (6) / `ABOVE_CEILING` (7) và nhãn khỏi `packaging_price_codes.py` — ghi chú số đã cấp, KHÔNG tái dùng; `gen_status_ts.py` chạy lại (`statuses.ts` bớt 4 dòng) |
| Excel / Trợ lý | hai cột `floor` / `ceiling` ở `PRICE_LIST_COLUMNS`; `floor_price` / `ceiling_price` ở `packaging_cost_format.py`; mô tả công cụ `packaging_price_lookup` |
| v1 | xóa `utils/packaging-flags.ts`, `PackagingLimitModal.tsx`; bỏ `isOutsideLimit`, `COST_WARNING_KIND`, `selectedCodeNote` (thay bằng `joinWarnings`), `RangeText`, cột / nút / ô lọc / `breachOnly`, kiểu `PackagingPriceLimit`, `fetchPriceLimit` / `savePriceLimit` |
| v2 | xóa `config/packaging-feature-flags.ts`, `components/packaging-price-limit-dialog.tsx`; bỏ `isOutsidePriceLimit`, `buildSelectedCodeNote`, `RangeText`, khóa query `limit`, hook `usePackagingPriceLimit` / `useSavePackagingPriceLimit`, `fetchPackagingPriceLimit` / `savePackagingPriceLimit`, kiểu `PackagingPriceLimit`, cột / ô lọc / `breachOnly`, trường `floor` / `ceiling` / `breach_only` |
| Tài liệu | `21-tac-dong-gia-bao-bi.md` (bảng cảnh báo, mục nguồn Misa, mục "Đã bỏ hẳn"), `01-yeu-cau-chuc-nang.md`, `api.md` (bỏ 5 hàng ngưỡng + hàng 25/11), `doc/agent-hub/06-cong-mcp.md`, chú thích HDSD `seed_help_gia_bao_bi_cr784.py` (chỉ chữ, KHÔNG chạy). Cẩm nang Trợ lý (`10-quy-trinh-thu-mua.md`) và `02-danh-sach-api-tool.md` không nhắc ngưỡng nên không đổi |

### Migration `cleanup784` (viết tay, `down_revision = quotesrc784`, một đầu)
Lên: DROP `tab_product_price_limit` (in số dòng bị bỏ); `tab_product_price_ledger.vat` cho phép NULL VÀ bỏ mặc định 0 của CSDL (cột NULL = không biết, ghi thiếu `vat` không được tự thành 0%); `UPDATE ... SET vat = NULL WHERE source_type = 3`. Xuống: `vat NULL -> 0`, NOT NULL + mặc định 0 trở lại, dựng lại `tab_product_price_limit` RỖNG đúng cấu trúc `pkgcost784` (đã so `SHOW CREATE TABLE`: chỉ khác bộ đếm AUTO_INCREMENT). Chạy thật trên bản sao MySQL local (`p04_scratch`, đã xóa): lên / xuống / lên lại sạch; trước-lên và sau-xuống trùng `SHOW CREATE TABLE` sổ giá + băm nội dung sổ; sau-lên và sau-lên-lại trùng.

### VAT dòng Misa (C7 = A)
Cả hai đường nạp (`misa_ledger_import.build_misa_rows` và `misa_xlsx_import.read_rows`) ghi `vat = None`. Mô hình bỏ `default=0` của `vat` (ORM coi `None` là "chưa gán" nên sẽ ghi 0 thay NULL — phát hiện qua bài kiểm). Chỗ đọc `vat` duy nhất là `history_page_rows.row_to_item` (`num(None)` trả `None`) + khóa xếp `vat` (`build_blank_last_order` dồn NULL xuống cuối cả hai chiều) + cột Excel *VAT (%)* (ô trống); không chỗ nào tính số học trên VAT sổ giá; giao diện v1 / v2 không có cột VAT ở Lịch sử mua hàng (kiểu đã là `number | null`).

### `synced_at`
Bỏ `default=datetime.utcnow`; còn `server_default=func.now()` (khớp `DEFAULT CURRENT_TIMESTAMP` của CSDL). Mọi nơi ghi đè dùng `func.now()` (`ledger_sync_service._apply`, hai chỗ cập nhật kho / thành tiền, `UPDATE ... reopen`, `misa_ledger_import` nhánh cập nhật, `misa_xlsx_import` nhánh bổ sung thành tiền). Bài canh grep không cho `synced_at = datetime...` quay lại.

### Hai đường nạp Misa đá nhau
- `source_id` của Misa: script HTML = id dòng Misa trong tệp; module 6 (xlsx) = số thứ tự trong sổ (`max + 1`). KHÔNG trỏ chứng từ. Ghi ở chú thích đầu `product_price/model.py`, `misa_ledger_import.py`, `misa_xlsx_import.py`, tài liệu 21.
- Chốt chặn: `misa_ledger_import.ensure_no_xlsx_misa_rows(db)` gọi đầu `import_misa_rows` — ném `MisaSourceError` (script in `LỖI: ...`, thoát mã 2, kể cả khi chạy thử) nếu sổ CÓ dòng Misa VÀ tồn tại lô module 6 `mode = ghi thật`, `status = xong`. Sổ chưa có dòng Misa (kể cả sau `--purge --apply`) thì qua dù lô cũ còn; lô chạy thử / lỗi không chặn. Đã chạy script thật trên bản sao MySQL: bị chặn → `--purge --apply` → nạp lại được.
- Giới hạn đã biết: lô module 6 từng ghi thật rồi sổ Misa bị gỡ, sau đó nạp lại bằng HTML → qua (vì sổ trống). Ngược lại lô module 6 cũ + nạp HTML mới + sổ có dòng → bị chặn dù dòng hiện có do HTML nạp (hiếm; cách gỡ: `--purge --apply`).
- **Cho phase 07:** sổ giá KHÔNG lưu dòng Misa nào thuộc lô nhập nào, `source_id` của module 6 chỉ là số thứ tự (không mã hóa id lô) nên chưa nhận diện được từng dòng. Muốn "xóa theo lô" cho module 6 phase 07 phải tự thêm cột `import_batch_id` trên `tab_product_price_ledger` (module 6 ghi id lô lúc chèn; dòng cũ = 0 = không rõ lô; HTML script = 0). Không làm ở phase này (tránh làm quá tay, dữ liệu dev 5.041 dòng Misa nạp từ HTML không gán lại được).

### Sai khác so với kế hoạch
| Chỗ | Kế hoạch | Thực hiện |
|---|---|---|
| Migration | `opt784` | `cleanup784` (mỗi phase một migration, xem plan.md) |
| Cột `vat` | cho phép NULL | thêm: bỏ cả mặc định 0 của CSDL + bỏ `default=0` của ORM (xem trên) |
| `price_warnings` | bỏ hai luật | bỏ luôn tham số `applied` (thành thừa), sửa năm chỗ gọi |
| Mục 3 "hằng độ dài dùng chung" thay `200` lặp ở ba tệp | có | KHÔNG làm: `MAX_SUPPLIER_NAME` / `MAX_WAREHOUSE_NAME` đã là hằng dùng chung ở `misa_ledger_import.py`; chỗ lặp còn lại chỉ là `String(200)` trong model (YAGNI) |
| Chú thích đầu `model.py` | cập nhật bảng nguồn | đã cập nhật (ba nguồn + nghĩa `source_id` Misa + VAT) |
| Sửa thêm | — | `last_prices_service`: `supplier_options` chọn tên nhỏ nhất theo (bỏ dấu, chữ gốc) cho mỗi mã NCC và `build_last_prices` duyệt `sorted(all_codes)` (lỗi tập không có thứ tự của phase 02) |

### Đối chiếu cũ / mới (bản sao MySQL local 11.560 dòng sổ giá, mã cũ + lược đồ cũ so với mã mới + đã migrate)
Giống hệt từng số: Tác động 500 mã (+ giá giả định, trang 2, Excel), Tổng hợp theo sản phẩm (1.000 SP, lọc có cảnh báo, Excel), Bảng giá (bom / all, xếp theo số, theo khoảng ngày; 1.135 / 2.927 mã), Giá mua gần nhất (535 / 2.909 mã), Lịch sử theo mã (1.568 dòng), theo sản phẩm (346 dòng), 5 công cụ Trợ lý. Chỉ khác ở phần ĐÃ DỰ KIẾN: (1) không còn `floor` / `ceiling` / `floor_price` / `ceiling_price` (23.272 chỗ); (2) không cảnh báo 6 / 7 (không dòng nào phát ra: 0 dòng ngưỡng); (3) VAT dòng Misa `0 -> null` (3.796 chỗ trong các lượt hỏi Lịch sử) và Excel Lịch sử ô VAT trống (349 + 321 ô); `sort_by=vat` đổi thứ tự vì NULL xuống cuối (cùng tập dòng, nội dung từng dòng giống hệt); (4) Excel Bảng giá bớt hai cột; (5) ô nhà cung cấp của Giá mua gần nhất: mã `1801356017` có hai tên (tên Misa và tên danh mục) — bản cũ chọn một tên tùy thứ tự tập (vì thế thứ tự danh sách đổi nhịp), bản mới luôn chọn tên nhỏ nhất ("CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ THÀNH CÔNG"); các dòng của bảng không đổi.

### Kiểm thử
- Backend (container api, mã nhánh này): `-k "cr784 or cr789 or don_dep"` 688 bài qua, 4 bỏ qua (sẵn có); thêm `test_pham_vi_khai_du_b07`, `test_canh_do_dai_o_chu_cr538`, `test_status_catalog_b01`, `test_dong_bo_giao_dien_v2`, `test_pham_vi_luat_bat_bien`, `test_assistant_pham_vi_doc`, `test_pham_vi_bo_may_duyet_xuyen_suot`, `test_assistant_tool_router`, `test_assistant_tools`, `test_agent_hub_cong_mcp_cr207`, `test_assistant_tool_audit` 216 qua; ruff `app` + hai tệp đổi 0 lỗi. Bài mới `test_don_dep_so_gia_nguong_vat_misa_cr784.py` (29 bài: VAT NULL cả hai đường nạp + API Lịch sử + xếp + Excel, `synced_at` server, chốt chặn Misa, thứ tự NCC, migration SQLite lên / xuống / lên lại + một đầu), thêm bài đường ngưỡng 404 (`test_bao_gia_nguong_gia_cr784.py`) và cảnh báo 6 / 7 không phát ra (`test_tac_dong_gia_bao_bi_cr784.py`); sửa số truy vấn 4 -> 3 / 5 -> 4 (`test_trang_thai_gia_theo_ma_cr784.py`).
- Frontend: v2 `tsc` 0 lỗi, `eslint` các tệp đổi 0 lỗi, `vitest src/modules/procurement` 1.810 bài xanh; v1 `tsc` đúng 4 lỗi cũ.

### Câu đọc kiểm TRƯỚC khi lên dev (chỉ đọc)
```sql
-- 1) Số dòng ngưỡng sẽ bị bỏ. Local = 0 (bảng từng có một dòng rồi đã xóa). MONG ĐỢI trên dev: 0
SELECT COUNT(*) FROM tab_product_price_limit;
-- 2) VAT dòng Misa trước khi đổi. Local: 5.041 dòng, đều 0,00
SELECT COUNT(*), MIN(vat), MAX(vat) FROM tab_product_price_ledger WHERE source_type = 3;
-- 3) Lô module 6 từng ghi thật (quyết định chốt chặn Misa có chặn script HTML hay không)
SELECT id, status, mode, created_at FROM tab_import_batch WHERE module = 6 ORDER BY id;
```
Lên dev: sao lưu DB dev, chạy ba câu trên (câu 1 phải 0), gộp, khởi động lại `api` (`alembic upgrade head` tự chạy `cleanup784`, log in `[cleanup784] ...`), kiểm `SHOW COLUMNS FROM tab_product_price_ledger LIKE 'vat'` (Null = YES, Default = NULL), `SHOW TABLES LIKE 'tab_product_price_limit'` rỗng; mở Bảng giá VTBB (cả hai giao diện) thấy không còn cột Sàn – Trần / nút Ngưỡng. Quay lui: `alembic downgrade -1`.
