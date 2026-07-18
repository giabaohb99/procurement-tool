# MÔ TẢ CHỨC NĂNG: IMPORT KHẢO SÁT (Phiếu khảo sát)

Nguồn: `[Data Chuẩn] 3. THU MUA_MR TIÊN.xlsx` — sheet **3** (Đánh giá NCC) + sheet **4** (Đánh giá SP/lấy mẫu).

## 1. Mục tiêu
Nạp dữ liệu khảo sát cũ vào **Phiếu khảo sát (Survey)**. Chạy **nền (Celery)**, **upsert theo dòng** (có → cập nhật, chưa → tạo), xong **báo chuông** cho người import, có **màn hình quản lý + log lỗi**.

## 2. Input
- Upload **1 file .xlsx** (cả workbook). Tool tự nhận 2 sheet theo tên `3. KHẢO SÁT ... N` và `4. KHẢO SÁT ... S`.
- Header dòng **5**, data từ dòng **6**; dừng khi cột A (Stt) và E (Mã yêu cầu) đều trống.
- 2 chế độ: **Dry-run** (xem trước, không ghi) và **Apply** (ghi, chạy nền).

## 3. Khoá gom — 1 Phiếu = (Phân loại F + NCC O)
- Cùng **Phân loại (F)** + cùng **NCC (O)** → CHUNG 1 phiếu khảo sát.
- Trong 1 phiếu: 1 dòng đánh giá NCC (sheet 3) + các dòng báo giá SP của NCC đó (sheet 4).
- Định danh phiếu (để re-import): `import_key = norm("{phân_loại}::{ncc_code}")`.
- (Mã yêu cầu E chỉ lưu tham khảo vào `pr_code`, không dùng để gom.)

## 4. Định danh NCC (resolve về danh mục Supplier)
| Nguồn | Khoá tra | Không thấy / xung đột |
|---|---|---|
| KS Sản phẩm (sheet 4) | Tên viết tắt (O) | không khớp supplier_code → **NCC text-only** + log |
| KS NCC (sheet 3) | MST (Q) | MST là NCC khác tên viết tắt → **NCC text-only** ("NCC không có sẵn, nhập text") + log |
- Không thấy hẳn → **tạo NCC mới** từ sheet 3 (tên P, MST Q, địa chỉ R, liên hệ U/V, công nợ AF). Đã có → chỉ **điền field trống**, không đè.

## 5. Check trùng / Upsert (idempotent)
- **Phiếu**: tìm theo `import_key (Phân loại + NCC)`. Có → dùng lại; chưa → tạo (status=**approved**).
- **Dòng NCC** (SurveySupplierLine): khoá **MST** (fallback supplier_code). Có → cập nhật; chưa → tạo.
- **Dòng SP** (SurveyProductLine): khoá **NCC + Mã VTBB nội bộ (P)** (fallback NCC + tên SP). Có → cập nhật; chưa → tạo.
- 2 dòng cùng khoá trong 1 file → dòng sau đè dòng trước + cảnh báo.
- Chạy lại cùng file ⇒ chỉ cập nhật, KHÔNG nhân đôi.

## 6. Mapping cột → field
**Survey header** (từ A–N): `pr_code=E · received_date=B · result_due_date=C · item_group=F · requirement_detail=G · request_qty=H · uom=I · proposed_rate=J · nspt=K · main_content=D · status=approved · code=KS#####(tự sinh)`

**SurveySupplierLine** (O→AJ): `supplier_code=O · supplier_name=P · tax_code=Q · reg_address=R · warehouse_address=S · google_maps=T · contact_person=U · contact_phone=V · supply_group=W · quote_folder=X · source_of_information=Y · production_tech=Z · production_time=AA · nvkd_eval=AB · invoice_policy=AC · reliability=AD · delivery_policy=AE · debt_policy=AF · defect_return=AG · nspt_reason=AH · line_approve=AI · line_approve_note=AJ · contact_date=L · reply_date=M · result_date=N`

**SurveyProductLine** (O→AM): `supplier_code=O · internal_code=P · product_name=Q/R · spec=S · origin=T · quote_unit=U · moq=V · price_by_volume=W · volume_range=X · vat=Y · amount=Z · internal_unit=AA · amount_converted=AB · shipping_cost=AC · delivery_time=AD · delivery_place=AE · quote_file=AF · sample_ready=AG · sample_date=AH · sample_qty=AI · lab_result=AJ · nspt_note=AK · line_approve=AL · line_approve_note=AM · contact_date=L · reply_date=M · result_date=N`

## 7. Xử lý ngoại lệ (try/catch, không chặn cả file)
- Ngày/số sai (kể cả serial rác) → để trống/0 + cảnh báo.
- Thiếu Phân loại (F) hoặc NCC (O) → bỏ dòng + ghi lỗi.
- NCC text-only / MST xung đột → vẫn tạo dòng (text) + log để rà tay.
- Mã VTBB (P) không có trong danh mục Product → giữ text (internal_code), log.

## 8. Chạy nền + chuông
1. Upload → lưu file tạm → tạo `ImportBatch(status=running)` → đẩy **Celery task** → trả `batch_id` ngay.
2. Task: parse → upsert theo lô → ghi warning/lỗi vào log → cập nhật đếm.
3. Xong → `status=done` + **chuông** cho người import: "Import khảo sát xong: X tạo · Y cập nhật · Z lỗi".

## 9. Màn hình Quản lý Import + Log
Bảng `tab_import_batch`: `id · module='survey' · filename · uploaded_by · started_at · finished_at · status · created · updated · skipped · warnings · errors · log_detail(JSON)`.
- Trang riêng: danh sách các lần import (khi nào · ai · file · trạng thái · số liệu) → bấm xem **log chi tiết từng dòng** (NCC text-only, MST xung đột, ngày/số sai, Mã VTBB thiếu…).

## 10. Output
- Dry-run: thống kê + preview + danh sách cảnh báo/lỗi (không ghi).
- Apply: như trên + danh sách `code` phiếu tạo/cập nhật, lưu vào ImportBatch.
