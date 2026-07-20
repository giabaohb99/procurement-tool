# MÔ TẢ CHỨC NĂNG: IMPORT ĐƠN MUA HÀNG (Purchase Order)

Nguồn: `[Data Chuẩn] 3. THU MUA_MR TIÊN.xlsx` — sheet **6. TIẾN ĐỘ MUA HÀNG** (và "DỮ LIỆU CŨ" cùng khuôn).

## 1. Mục tiêu
Nạp lịch sử mua hàng vào **Đơn mua hàng (PO) + dòng hàng + lần giao + công nợ + thanh toán**. Chạy **nền (Celery)**, upsert theo khoá, xong **báo chuông**, có **màn hình quản lý + log lỗi**.

## 2. Input
- Upload **1 file .xlsx**. Header dòng **4**, data từ dòng **5**; dừng khi cột A (Stt) và J (Mã Misa) đều trống.
- **Dry-run** (xem trước) và **Apply** (ghi, chạy nền).
- Tuỳ chọn trên tool: **gán sẵn NSPT mặc định** cho cả lô (dùng khi cột NSPT không khớp danh sách).

## 3. Khoá gom 3 tầng
```
Mã Misa (J)                       → 1 ĐƠN MUA HÀNG (PurchaseOrder)
  └ (Mã SP L + Số hóa đơn AE)    → 1 DÒNG HÀNG   (POItem)   [số HĐ thuộc dòng hàng]
      └ mỗi dòng sheet            → 1 LẦN GIAO    (PODelivery)
```
- **PO** = gom theo `misa_code (J)`.
- **Dòng hàng (POItem)** = gom theo `(Mã SP L + Số hóa đơn AE)`. Số hóa đơn là **thuộc tính của dòng hàng** (model: `POItem.invoice_no` — "Số hóa đơn theo sản phẩm").
  - **Cùng sản phẩm, KHÁC số HĐ → 2 dòng hàng riêng.** (Vd ĐMH01705 → 2 dòng THC0077 với HĐ 1215 và 1216.)
  - **Cùng (sản phẩm + số HĐ) → 1 dòng hàng.**
- **Lần giao (PODelivery)** = mỗi dòng sheet = 1 lần nhận (SL nhận Y, ngày nhận E, kho R, đơn vị VC S). Khoá lần giao = `(dòng hàng + số HĐ + ngày nhận + KHO + VẬN CHUYỂN)`.
  - **Cùng số HĐ vẫn có thể giao NHIỀU LẦN** (khác kho / khác đơn vị VC) → là các lần giao riêng, KHÔNG phải trùng. `POItem.qty_received = Σ các lần giao`. Vd ĐMH01497/THC0247/HĐ158: SL đặt 150, giao 2 lần (147 Dego Cần Thơ/Mekong + 150 Hà Long/NCC tự VC) → tổng nhận 297.
  - Chỉ khi trùng CẢ (số HĐ + ngày + kho + vận chuyển) mới là trùng thật → ghi đè + log WARNING `duplicate_line`.
- **Số HĐ KHÔNG duy nhất toàn cục** (vd 158 xuất hiện ở nhiều Misa/SP) → khoá luôn phải kèm Misa + sản phẩm.
- Định danh để re-import: PO theo `misa_code`; dòng hàng theo `(misa, product_code, invoice_no)`; lần giao theo `(misa, product_code, invoice_no, received_date, warehouse, carrier)`.

**Edge-case SL đặt (X) lệch:** nếu cùng `(misa + SP + số HĐ)` mà các dòng ghi X khác nhau → lấy X của dòng đầu làm SL đặt của POItem + log REVIEW "SL đặt lệch — cần rà".

## 4. Trạng thái → done + Công nợ + Thanh toán
Theo cột **Trạng thái (P)** của dòng:
- **"Hoàn thành"** → set `POItem.progress_status = "Hoàn thành"` (done) **và**:
  - Công nợ hàng (Payable) tự sinh khi có SL nhận (Y) — như luồng hiện tại.
  - **Tạo Yêu cầu thanh toán (YCTT) + ghi nhận ĐÃ CHI** cho công nợ đó (đủ số).
- **Khác "Hoàn thành"** → **chỉ ghi nhận công nợ**, KHÔNG tạo YCTT.

## 5. Mapping cột → field
**PurchaseOrder (header)**: `misa_code=J · order_date=AD · company(G) → company_id · supplier_code=I · nspt=H · payment_terms=AT · department=F · status(suy từ tiến độ các dòng)`

**POItem (dòng hàng)**: `product_code=L · product_name=M · item_group=K · invoice_name=O · spec=N · unit=W · qty_request=V · qty_order=X · price=Z · vat=AA · invoice_no=AE · warehouse_code=R · supplier_ready=Q · required_date=C · progress_status=P · fg_code=AP · fg_name=AR · note=AC`

**PODelivery (lần giao)**: `carrier_name/code=S · ship_qty=T · ship_unit=U · received_qty=Y · received_date=E · promised_date=D · std_days=AH · regulated_date=AI · shipping_unit_price=AJ · shipping_amount=AK · invoice_no=AE · progress_note=AG · (chênh lệch AL/AM/AN tự tính lại)`

## 6. Xử lý ngoại lệ (try/catch — điểm rủi ro chính vì DB lưu text)
| Trường hợp | Cách xử lý |
|---|---|
| **Mã hàng (L) không có** trong danh mục | **Tạo Product mới** tạm từ đơn (mã L, tên M, ĐVT W, phân loại K) để dòng chạy được → log "SP tạo tự động" |
| **NSPT (H) không có** trong nhân sự | Để **trống**, hoặc dùng **NSPT mặc định của lô** (chọn trên tool) → log |
| **NCC (I) không có** | Tra theo tên viết tắt; không có → tạo mới NCC tối thiểu (tên) hoặc để text → log |
| **Kho (R) / Công ty (G) / Phân loại (K)** không khớp danh mục | Để trống/giữ text + log |
| **Trạng thái (P)** không thuộc tập chuẩn | Map gần đúng hoặc để "Chưa đặt hàng" + log |
| Ngày/số sai | để trống/0 + log |

## 7. Rủi ro mapping sai (do lưu text) & danh sách rà soát
- Mọi giá trị **không khớp tập chọn chuẩn** (trạng thái, ĐVT, kho, phân loại, công ty, hình thức TT) → đưa vào **"Danh sách cần rà soát"** trong log (mô phỏng, không tự sửa).
- Dry-run hiển thị các giá trị lệch **trước khi Apply** để người dùng đối chiếu.
- Cảnh báo trùng/nghi ngờ: cùng Misa nhưng lệch NCC/công ty; cùng (Misa,HĐ) nhưng lệch product_code; SL nhận > SL đặt…

## 8. Check trùng / Upsert (idempotent)
- PO theo `misa_code`: có → cập nhật header + dòng; chưa → tạo.
- Dòng hàng theo `(misa, product_code, invoice_no)`; lần giao theo `(misa, product_code, invoice_no, received_date, warehouse, carrier)`.
- Re-import cùng file/cụm ⇒ cập nhật, không nhân đôi.
- Trùng hết khoá lần giao (số HĐ + ngày + kho + VC giống hệt) ⇒ dedup + log WARNING "duplicate_line".

## 8b. Đồng bộ với hạ tầng Import Khảo sát (tái dùng)
- Parser số kiểu VN (`_n`: "20.600"→20600), sinh log INFO `po_new`/`po_update` để soi phiếu mới vs cập nhật, cảnh báo `duplicate_line`.
- **Revert**: snapshot PO+dòng+lần giao (+ payable/payment đã sinh) vào `tab_import_change` khi Apply → hoàn tác được như khảo sát.
- **Phân quyền**: dùng chung entity `import` (create/read/delete) đã seed.

## 9. Chạy nền + chuông + màn hình quản lý
- Giống Import Khảo sát: `ImportBatch(module='purchase_order')` → **Celery task** → xong **chuông** + trang **Quản lý Import** xem log chi tiết từng dòng.

## 10. "Phần thu mua cần bổ sung gì để chạy được import này"
1. **Hạ tầng Import dùng chung**: bảng `tab_import_batch` + trang Quản lý Import + Celery worker (đã dựng nhánh `celery-worker`, cần merge/bật ở prod).
2. **Tạo Product nhanh khi thiếu mã** (service tạo SP tối thiểu từ dòng đơn).
3. **Đường tạo Payable + YCTT + ghi ĐÃ CHI theo lập trình** (bỏ qua các bước bấm tay) cho dòng "Hoàn thành".
4. **Ghi đè tiến độ dòng khi import** (đặt thẳng progress_status, không qua ràng buộc nhập-tay như luồng thường).
5. **Chọn NSPT mặc định cho lô** trên form import.
6. **Chuẩn hoá/đối chiếu giá trị text** (map trạng thái, ĐVT, kho… về tập chuẩn) + log lệch.
