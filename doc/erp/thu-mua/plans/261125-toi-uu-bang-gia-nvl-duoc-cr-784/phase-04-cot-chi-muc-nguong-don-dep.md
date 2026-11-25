# Phase 04 — Cột, chỉ mục, BỎ ngưỡng sàn / trần và dọn nhỏ

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |

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
- [ ] Chốt C5 (khóa duy nhất báo giá)
- [ ] Gỡ ngưỡng sàn / trần (backend, v1, v2, Excel, Trợ lý / MCP, tài liệu)
- [ ] `synced_at` một nguồn giờ
- [ ] Chặn hai đường nạp Misa đá nhau
- [ ] (C7 = A) VAT Misa NULL
