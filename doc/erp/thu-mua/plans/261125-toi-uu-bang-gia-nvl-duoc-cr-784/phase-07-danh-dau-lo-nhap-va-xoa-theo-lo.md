# Phase 07 — Đánh dấu lô nhập trên định mức và xóa dữ liệu theo lô

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | điều phối | Đã duyệt, chờ làm | duoc-CR-784 |
| 2 | 26/11/2026 | tài liệu và kiểm thử | **Xong, đã commit + lên dev 25/11/2026** (commit `0039f8758`, migration `bombatch784`); HDSD + tài liệu ở phase 05 | duoc-CR-784 |

Ưu tiên P2 · 3 giờ · làm sau phase 03 (cùng ý "nguồn nhập": báo giá nhập Excel có `source_id` = id lô).

## Bối cảnh
Chủ dự án hỏi 25/11/2026: 1.000 dòng định mức nạp từ bản mẫu HTML, sau này muốn xóa thì định danh thế nào. Soát dev
(chỉ đọc) cùng ngày:
- `tab_packaging_bom` có 1.000 dòng, tạo cùng lúc 21/11/2026 03:57:30 (UTC), cùng người tạo id 275, từ **lô 98** của Quản lý
  Import (module 4, tệp `data-chai-test-tu-ban-mau-html.xlsx`; lô 96, 97 là chạy thử).
- Bảng định mức KHÔNG lưu dòng nào thuộc lô nào; `tab_import_change` không có dòng cho module 4 nên không hoàn tác lô được.
  Hiện chỉ đoán được theo giờ tạo + người tạo — sẽ hỏng khi nạp tệp DATA_CHAI thật (trùng mã HH là ghi đè lên chính dòng đó).
- Sổ Misa (5.041 dòng, `source_type = 3`) đã nhận diện được và gỡ được bằng `import_misa_price_ledger --purge`.

## Việc làm
1. **Cột `import_batch_id`** BIGINT NOT NULL default 0 trên `tab_packaging_bom` (0 = nhập tay / form), chỉ mục. Nhập Excel
   định mức (`bom_import.py`) ghi id lô vào dòng nó TẠO hoặc SỬA (lần ghi cuối, cùng luật C4 của báo giá). Form sửa tay không
   đổi cột này. Migration riêng (`bombatch784`, sau migration của phase 03).
2. **Đánh dấu dữ liệu thử đang có**: trong migration hoặc script một lần, gán `import_batch_id = 98` cho dòng khớp lô 98
   (cùng `created_at` + `created_by` của lô, đếm đủ 1.000 mới ghi; lệch thì dừng và báo). Chỉ áp ở nơi có lô 98 (dev /
   local); prod chưa có dữ liệu này.
3. **Xóa theo lô** ở màn chi tiết lô nhập (Quản lý Import, cả v1 và v2) cho module 4 (định mức), 5 (báo giá), 6 (sổ Misa):
   - Bước xem trước: số dòng sẽ xóa, số dòng đã bị sửa tay sau khi nhập (`updated_at` > giờ ghi lô) tách riêng, hỏi lại.
   - Gác quyền `packaging_cost.delete` + `import.read`; ghi nhật ký thao tác (`core/audit.py`); xóa định mức thì thành phần tự
     xóa theo (FK cascade).
   - Báo giá: xóa dòng có `source_type = 2` (Nhập Excel) và `source_id` = id lô (phase 03).
   - Sổ Misa: xóa dòng nguồn 3 của lô (cần phase 04 thống nhất cách ghi `source_id` của Misa) rồi tính lại mốc Misa.

## Bài kiểm
- Nhập Excel định mức ghi đúng `import_batch_id`; form sửa tay không đổi.
- Xóa theo lô chỉ đụng dòng của lô; dòng sửa tay sau nhập được tách ra hỏi lại; thiếu quyền trả 403; thành phần xóa theo.
- Script đánh dấu: đủ 1.000 thì ghi, lệch thì dừng.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Xóa lô thử khi màn Tác động / Tổng hợp đang dùng dữ liệu đó | Trung bình x Thấp | xem trước số dòng; dev trống tới khi có DATA_CHAI thật — báo người dùng trước |
| Lô thật ghi đè dòng của lô thử rồi xóa lô thử | Thấp x Trung bình | dòng mang id lô của LẦN GHI CUỐI, nên xóa lô 98 không đụng dòng đã bị lô thật ghi đè |

## Việc cần làm
- [x] Chủ dự án duyệt hướng làm (25/11/2026)
- [x] Cột `import_batch_id` trên `tab_packaging_bom` VÀ `tab_product_price_ledger` (module 6 ghi id lô vào dòng Misa THÊM mới) + ghi khi nhập Excel định mức
- [x] Đánh dấu 1.000 dòng lô 98 trên dev (migration `bombatch784` đánh dấu mọi lô module 4 ghi thật khi số dòng khớp đúng `created_count`, lệch thì bỏ qua và cảnh báo)
- [x] Xóa theo lô (backend `batch_purge_service.py` / `batch_purge_controller.py`, v2 `import-batch-purge-dialog.tsx`, v1 `PackagingBatchPurgeModal.tsx`) cho module 4, 5, 6
- [x] Bài kiểm (`test_xoa_theo_lo_nhap_cr784.py`, 17 bài), tài liệu (chức năng 21 mục 9, `api.md`), HDSD (bài *Xóa dữ liệu đã nhập nhầm theo lô nhập Excel*, phase 05 26/11/2026)

**Khác kế hoạch:** sổ Misa dùng cột `import_batch_id` mới (không suy từ `source_id`); 5.041 dòng Misa trên dev nạp bằng script HTML mang 0 nên không gỡ được theo lô (gỡ bằng `import_misa_price_ledger --purge`).
