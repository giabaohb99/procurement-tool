# Kế hoạch: Công cụ Import dữ liệu cũ (Khảo sát + Đơn mua hàng)

Nguồn: `doc/chung/[Data Chuẩn] 3. THU MUA_MR TIÊN.xlsx`

## 0. Nguồn dữ liệu (đã khảo sát)

| Sheet | Ý nghĩa | Header | Data từ | Map tới |
|---|---|---|---|---|
| `3. KHẢO SÁT ... N` | Đánh giá **Nhà cung cấp** | dòng 5 | dòng 6 | `SurveySupplierLine` |
| `4. KHẢO SÁT ... S` | Đánh giá **Sản phẩm / lấy mẫu** | dòng 5 | dòng 6 | `SurveyProductLine` |
| `6. TIẾN ĐỘ MUA HÀNG` | ĐMH + tiến độ giao | dòng 4 | dòng 5 | `PurchaseOrder + POItem + PODelivery` |

> Model `app/modules/survey/model.py` được thiết kế mirror 1:1 với sheet 3/4 (comment ghi rõ "Sheet 3", "Sheet 4") → mapping rất thuận.

---

## PHẦN 1 — IMPORT KHẢO SÁT (làm trước)

### 1.1 Cách nhóm
- Cả sheet 3 và 4 chung 14 cột đầu (A–N) mô tả **1 yêu cầu**; cột **E "Mã yêu cầu"** (vd `PYC.NM.01042026.01`) là khóa nhóm.
- **1 Mã yêu cầu = 1 Phiếu khảo sát (Survey)**:
  - các dòng sheet 3 cùng E → `supplier_lines[]`
  - các dòng sheet 4 cùng E → `product_lines[]`
  - header phiếu lấy từ A–N của dòng đầu nhóm.
- Liên kết 2 loại dòng theo cột **O "Tên viết tắt NCC"** (mỗi NCC 1 dòng đánh giá + 1 dòng báo giá SP).

### 1.2 Mapping cột → field

**Survey (header)** — từ A–N:
`pr_code=E` · `received_date=B` · `result_due_date=C` · `item_group=F` · `requirement_detail=G` · `request_qty=H` · `uom=I` · `proposed_rate=J` · `nspt=K` · `main_content=D (BP/Người YC)` · `code=tự sinh KS#####`

**SurveySupplierLine (sheet 3)** — O→AJ:
`contact_date=L` · `reply_date=M` · `result_date=N` · `supplier_code=O` · `supplier_name=P` · `tax_code=Q` · `reg_address=R` · `warehouse_address=S` · `google_maps=T` · `contact_person=U` · `contact_phone=V` · `supply_group=W` · `quote_folder=X` · `source_of_information=Y` · `production_tech=Z` · `production_time=AA` · `nvkd_eval=AB` · `invoice_policy=AC` · `reliability=AD` · `delivery_policy=AE` · `debt_policy=AF` · `defect_return=AG` · `nspt_reason=AH` · `line_approve=AI` · `line_approve_note=AJ`

**SurveyProductLine (sheet 4)** — O→AM:
`contact_date=L` · `reply_date=M` · `result_date=N` · `supplier_code=O` · `internal_code=P` · `product_name=Q/R` · `spec=S` · `origin=T` · `quote_unit=U` · `moq=V` · `price_by_volume=W` · `volume_range=X` · `vat=Y` · `amount=Z` · `internal_unit=AA` · `amount_converted=AB` · `shipping_cost=AC` · `delivery_time=AD` · `delivery_place=AE` · `quote_file=AF` · `sample_ready=AG` · `sample_date=AH` · `sample_qty=AI` · `lab_result=AJ` · `nspt_note=AK` · `line_approve=AL` · `line_approve_note=AM`

### 1.3 Kiến trúc công cụ
- **Backend** `POST /api/surveys/import`:
  - nhận file `.xlsx` (multipart) hoặc chọn sheet.
  - parse bằng `openpyxl` → nhóm theo Mã yêu cầu → tạo Survey + 2 loại dòng.
  - 2 chế độ: `dry_run` (chỉ trả thống kê + lỗi, KHÔNG ghi) và `apply`.
  - trả report: số phiếu sẽ tạo, số dòng NCC/SP, danh sách cảnh báo (thiếu NCC, sai ngày, trùng mã…).
- **Frontend**: nút **"Import Excel"** ở trang *Phiếu khảo sát* → modal: chọn file → chạy dry-run → xem preview → **Xác nhận import**.
- **Phụ thuộc**: thêm `openpyxl` vào `requirements.txt`.
- **Upsert NCC**: sheet 3 có đủ thông tin NCC (tên/MST/địa chỉ/liên hệ/công nợ) → tạo/cập nhật `Supplier` theo `supplier_code` (để danh mục đồng bộ).
- **Khớp sản phẩm**: `internal_code` (P) → thử khớp `Product`; không có thì giữ nguyên text.
- **Idempotency**: khóa theo `pr_code` (Mã yêu cầu). Re-import → bỏ qua (báo) hoặc ghi đè (tuỳ chọn).

### 1.4 Quyết định đã chốt
1. **Có** tạo/cập nhật NCC vào danh mục (theo `supplier_code`).
2. Phiếu sau import = **approved** (đã khảo sát xong); `line_approve` lấy theo cột Duyệt.
3. Tạo **Phiếu khảo sát độc lập**, `pr_code = Mã yêu cầu` (không tạo YCKS cha).
4. Re-import trùng Mã yêu cầu → **bỏ qua + ghi vào report**.

### 1.5 Luồng xử lý tổng thể (logic)

```
[1] INPUT  → [2] PARSE → [3] GROUP → [4] CHECK TRÙNG → [5] VALIDATE
   → [6] DRY-RUN REPORT → (người dùng xem) → [7] APPLY → [8] FINAL REPORT
```

**[1] Input**
- Người dùng upload **1 file .xlsx** (cả workbook). Tool tự tìm 2 sheet theo tên: `3. KHẢO SÁT ... N` (NCC) và `4. KHẢO SÁT ... S` (SP). Thiếu 1 trong 2 → vẫn chạy phần có.
- Chọn chế độ: **Dry-run** (mặc định, chỉ xem) hoặc **Apply** (ghi).

**[2] Parse (đọc & chuẩn hoá)**
- Header ở **dòng 5**, data từ **dòng 6**. Dừng khi cả cột A (Stt) và E (Mã yêu cầu) đều trống.
- Chuẩn hoá từng ô: cắt khoảng trắng; ngày `datetime → 'YYYY-MM-DD'` (ô ngày lỗi/serial rác → để trống + cảnh báo); số (`"100.0"`, `"20.500"` → float); bool (`"True/False"`, tick ô có sẵn hàng).

**[3] Group — gom thành phiếu**
- Khoá gom = **Mã yêu cầu (E)**. Mỗi mã = **1 Phiếu khảo sát**.
- Trong 1 nhóm:
  - **Header** phiếu lấy từ cột A–N của **dòng đầu** nhóm.
  - **Dòng NCC** = mọi dòng sheet 3 cùng E (mỗi NCC 1 dòng, khoá theo cột O).
  - **Dòng SP** = mọi dòng sheet 4 cùng E (mỗi NCC 1 báo giá).
  - Liên kết NCC↔SP theo **Tên viết tắt NCC (O)**.

**[4] Xử lý TRÙNG — 3 loại**
| Loại | Tình huống | Xử lý |
|---|---|---|
| a. Trùng DB | Đã có Survey `pr_code = E` | **Bỏ qua cả nhóm**, ghi report "E đã tồn tại (KS#####)" |
| b. Trùng trong file | Cùng (E, NCC O) xuất hiện >1 dòng trong cùng sheet | Giữ **dòng đầu**, cảnh báo "NCC X lặp ở E, giữ dòng đầu" |
| c. Lệch 2 sheet | NCC có ở sheet 3 mà thiếu sheet 4 (hoặc ngược lại) | Vẫn tạo dòng đang có; cảnh báo "NCC X thiếu báo giá SP / thiếu đánh giá NCC" |

**[5] Validate (gom cảnh báo, không chặn cả file)**
- Thiếu **Mã yêu cầu (E)** → bỏ dòng, ghi lỗi.
- Thiếu **NCC (O)** trên 1 dòng → bỏ dòng đó, cảnh báo.
- Ngày/số sai → để trống/0 + cảnh báo (không làm hỏng phiếu).

**[6] Dry-run report** (xem trước, CHƯA ghi):
```
Tổng nhóm: N   |   Sẽ tạo: X phiếu   |   Bỏ qua (đã có): [E...]
NCC: mới A, cập nhật B
Cảnh báo: [ {ma_yeu_cau, ncc, message} ... ]
Lỗi: [ ... ]
Preview: [ {ma_yeu_cau, so_ncc, so_sp, status='approved'} ... ]
```

**[7] Apply — tạo phiếu (chỉ nhóm KHÔNG bị bỏ qua)**
Với mỗi nhóm, trong 1 transaction:
1. Sinh `code = KS#####` (theo bộ đếm hiện có).
2. Tạo **Survey header**: `status='approved'`, `pr_code=E`, ngày/nspt/phân loại/SL/giá đề xuất từ A–N.
3. Mỗi **dòng NCC**: **upsert Supplier** theo `supplier_code` (tạo mới nếu chưa có; nếu đã có chỉ **điền field còn trống**, không đè data đang dùng) → tạo `SurveySupplierLine` (kèm `line_approve`).
4. Mỗi **dòng SP**: tạo `SurveyProductLine`; `internal_code` thử khớp `Product` (không có thì giữ text).
5. Ghi audit `import`. Commit từng phiếu (1 phiếu lỗi không làm hỏng cả lô).

**[8] Final report**: như dry-run + danh sách `code` phiếu đã tạo + số lỗi/bỏ qua.

### 1.6 Công cụ (UI)
- Trang **Phiếu khảo sát** → nút **"Import Excel"** → modal: chọn file → **Chạy thử** (hiện report [6]) → **Xác nhận import** (chạy [7], hiện report [8]).
- Backend `POST /api/surveys/import?mode=dry_run|apply` (multipart file). Thêm `openpyxl` vào requirements.
- Quyền: chỉ vai trò có `survey create` (thu mua/admin).

---

---

## PHẦN 1B — PHƯƠNG ÁN UPSERT THEO DÒNG (chốt theo hướng mới của anh)

> Thay "gom theo Mã yêu cầu + bỏ qua khi trùng" bằng **upsert theo dòng**: file to, chạy
> nền, mỗi lần import 1 cụm → dòng nào đã có thì **cập nhật**, chưa có thì **tạo mới**.
> Mã yêu cầu chỉ là phụ (thực tế không có).

### B.1 Khoá gom phiếu (survey grouping)
- **Survey = (Phân loại F) + (NCC O)** — cùng NCC + cùng phân loại → CHUNG 1 phiếu.
- Trong 1 phiếu: dòng đánh giá NCC (sheet 3) + các dòng báo giá SP của NCC đó (sheet 4).
- Cần cột định danh ổn định `import_key = norm("{phân_loại}::{ncc_code}")` trên Survey để re-import tìm lại đúng phiếu.

### B.2 Định danh NCC (resolve về danh mục Supplier) — 2 nhánh
| Nguồn dòng | Khoá tra NCC | Không thấy / xung đột |
|---|---|---|
| **KS Sản phẩm** (sheet 4) | `tên viết tắt` (O) | không có supplier_code khớp → **NCC text-only** + log |
| **KS NCC** (sheet 3) | `MST` (Q) | MST khớp NCC **khác** với tên viết tắt → **NCC text-only** (dùng tính năng "NCC không có sẵn, nhập text") + log |
- Không thấy hẳn (cả 2 khoá) → **tạo mới Supplier** (từ dữ liệu sheet 3: tên/MST/địa chỉ/công nợ).
- Mọi trường hợp text-only / xung đột → ghi **log lỗi** để xử lý tay sau.

### B.3 Định danh dòng để UPSERT (check trùng)
Với mỗi dòng, tìm trong phiếu `(F, NCC)` tương ứng:
- **Dòng NCC** (SurveySupplierLine): khoá = `MST` (hoặc supplier_code nếu thiếu MST). Có → cập nhật; không → tạo.
- **Dòng SP** (SurveyProductLine): khoá = `NCC + Mã VTBB nội bộ (P)` (fallback: NCC + tên SP). Có → cập nhật; không → tạo.
- Trùng ngay trong file (2 dòng cùng khoá) → gộp, **dòng sau đè dòng trước** + cảnh báo.

### B.4 Chạy nền (async) + chuông
- Upload → lưu file tạm → tạo bản ghi **ImportBatch(status=running)** → đẩy **Celery task** → trả `batch_id` ngay (không đợi).
- Task: parse + upsert theo lô, cập nhật tiến độ vào ImportBatch; xong → `status=done` + **bắn thông báo (chuông)** cho người import: "Import xong: X tạo, Y cập nhật, Z lỗi".
- (Celery + hệ thống thông báo đã dựng sẵn ở các task trước → tận dụng được.)

### B.5 Màn hình "Quản lý Import" + log lỗi
Bảng mới **`tab_import_batch`**: `id, module(survey|purchase_order), filename, uploaded_by, started_at, finished_at, status, created, updated, skipped, warnings, errors, log_detail(JSON)`.
- Màn hình riêng: liệt kê các lần import (khi nào · ai · file gì · trạng thái · số tạo/cập nhật/lỗi) → bấm vào xem **log chi tiết từng dòng** (NCC text-only, MST xung đột, ngày/số sai…).

### B.6 Luồng tổng thể (mới)
```
Upload file → tạo ImportBatch(running) → Celery task chạy nền
   → parse → với mỗi dòng: resolve NCC → tìm phiếu (F,NCC) → upsert dòng (theo B.3)
   → ghi warning/lỗi vào log → cập nhật đếm
→ xong: status=done + CHUÔNG cho người import
→ Màn hình Quản lý Import xem lại chi tiết
```
Idempotent: chạy lại cùng file → chỉ cập nhật, không nhân đôi.

---

## PHẦN 2 — IMPORT ĐƠN MUA HÀNG (sau khi xong khảo sát)

Sheet 6 (72+ dòng ví dụ; sheet "DỮ LIỆU CŨ" ~508 dòng) → gộp theo **Mã đơn Misa (J)** = 1 ĐMH.
Mapping chính: `order_date=AD` · `company=G` · `supplier_code=I` · `misa_code=J` · `nspt=H` · `payment_terms=AT` · `item_group=K` · `product_code=L` · `product_name=M` · `warehouse=R` · `qty_order=X` · `qty_received=Y` · `price=Z` · `vat=AA` · `invoice_no=AE` · `progress_status=P` · lần giao: `carrier=S` · `ship_qty=T` · `received_date=E` · `promised_date=D`.
→ Sẽ chi tiết + chốt sau khi phần khảo sát chạy ổn.
