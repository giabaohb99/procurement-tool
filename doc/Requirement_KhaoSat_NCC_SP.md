# Requirement chi tiết — KHẢO SÁT NHÀ CUNG CẤP & KHẢO SÁT SẢN PHẨM

> Nguyên tắc trường: **HỢP (superset)** của `Sheet 3 (KS NCC)` + `Sheet 4 (KS SP)` + prototype FE. **Thà thừa hơn thiếu.**
> Mô hình: 1 phiếu khảo sát = **Header (tiếp nhận)** + **Bảng con** (mỗi dòng = 1 NCC hoặc 1 SP) + **Phê duyệt**. `survey_type = supplier | product`.
> UI: **trang detail riêng** (không popup) — section + **bảng con sửa inline kéo ngang** (Thêm dòng/Thêm nhiều) + đính kèm + log lịch sử.
> Key code = English snake_case (BE) / camelCase (FE). Cột `Sheet` = số cột gốc để đối chiếu.

---

## 0. BẢNG (DB)
- `tab_survey` — header (chung cho NCC & SP).
- `tab_survey_supplier_line` — dòng NCC (khi `survey_type=supplier`).
- `tab_survey_product_line` — dòng SP (khi `survey_type=product`).
- `tab_unit_conversion` — quy đổi ĐVT (dùng cho cột thành tiền quy đổi của SP).
- Đính kèm dùng `tab_attachment` (entity=`survey`).

### 0.1 `tab_survey` (Header — dùng chung)
| Nhãn | key | Kiểu | Sheet | Bắt buộc | Ghi chú |
|---|---|---|---|:--:|---|
| Mã phiếu | `code` | varchar(50) | — | auto | tự sinh `KS#####` |
| Loại khảo sát | `survey_type` | varchar(10) | — | ✓ | `supplier` / `product` |
| Mã yêu cầu (PYC) | `pr_code` | varchar(50) | 4 | ✓ | liên kết PYC |
| Ngày tiếp nhận | `received_date` | date | 1 | | |
| Ngày YC trả KQ | `result_due_date` | date | 2 | | |
| Phân loại nhóm hàng | `item_group` | varchar(100) | 5 | | select: Bao bì/Nguyên liệu/In ấn/Chai lọ/Hóa chất |
| Yêu cầu chi tiết | `requirement_detail` | text | 6 | | thông số, chiết khấu... |
| Số lượng YC | `request_qty` | decimal(18,3) | 7 | | |
| Giá thị trường | `market_price` | decimal(18,2) | 9 | | giá tham khảo BPYC |
| NSPT phụ trách | `nspt` | varchar(100) | 10 | | |
| Duyệt (TP/QL) | `approve_status` | varchar(20) | 34/37 | | `Duyệt`/`Không duyệt`/null |
| Yêu cầu (TP/QL) | `approve_note` | text | 35/38 | | ghi chú chỉ đạo |
| Trạng thái | `status` | varchar(30) | — | | draft/submitted/approved/rejected |
| (audit) | created_at/by, updated_at/by | | | | |

---

## A. KHẢO SÁT NHÀ CUNG CẤP (Sheet 3)

### A1. Giao diện
- **List** (`/surveys-supplier`): cột Mã YC, Ngày tiếp nhận, Nhóm hàng, **NCC chính** (dòng đầu), **Số NCC**, Trạng thái duyệt. Filter: mã YC, nhóm hàng, NSPT, trạng thái. Phân trang.
- **Detail** (`/surveys-supplier/{id}` & `/new`) — 3 section:
  1. **THÔNG TIN TIẾP NHẬN** (các field header 0.1).
  2. **BẢNG KHẢO SÁT NCC** — bảng con **inline kéo ngang**, mỗi dòng 1 NCC (đủ cột A2). Nút **Thêm NCC / Thêm nhiều**, xóa dòng. Auto: số NCC, NCC chính.
  3. **PHÊ DUYỆT (QLTM)** — `approve_status` (Duyệt/Không duyệt) + `approve_note`.
- Thanh đầu: Lưu · Gửi duyệt · Duyệt · Từ chối · (In) · Xóa — theo trạng thái & quyền. Có **Đính kèm** + **Lịch sử**.

### A2. `tab_survey_supplier_line` (mỗi dòng = 1 NCC) — ĐỦ cột Sheet 3
| Nhãn | key | Kiểu | Sheet | Bắt buộc | Ghi chú |
|---|---|---|---|:--:|---|
| (FK phiếu) | `survey_id` | bigint | — | ✓ | |
| Ngày liên hệ NCC | `contact_date` | date | 11 | | |
| Ngày NCC phản hồi | `reply_date` | date | 12 | | không phản hồi → dừng |
| Ngày trả KQ | `result_date` | date | 13 | | |
| Tên viết tắt NCC | `supplier_code` | varchar(50) | 14 | ✓ | NCC cũ chọn / mới nhập |
| Tên pháp lý NCC | `supplier_name` | varchar(255) | 15 | | tự điền nếu NCC cũ |
| Mã số thuế (MST) | `tax_code` | varchar(25) | 16 | | |
| Địa chỉ ĐKKD | `reg_address` | text | 17 | | |
| Địa chỉ kho NCC | `warehouse_address` | text | 18 | | |
| Link Google Maps | `google_maps` | varchar(500) | 19 | | |
| Người liên hệ (NVKD) | `contact_person` | varchar(100) | 20 | | |
| SĐT liên hệ | `contact_phone` | varchar(30) | 21 | | |
| Nhóm SP NCC cung ứng | `supply_group` | varchar(255) | 22 | | túi, chai, in ấn... |
| Link folder báo giá | `quote_folder` | varchar(500) | 23 | | Drive |
| Công nghệ SX | `production_tech` | varchar(255) | 25 | | In Flexo, in lụa... |
| Thời gian SX | `production_time` | varchar(100) | 26 | | 10-15 ngày |
| Đánh giá tư vấn NVKD | `nvkd_eval` | varchar(100) | 27 | | Tốt/Rất tốt... |
| Chính sách hóa đơn | `invoice_policy` | varchar(255) | 28 | | đủ SL, đúng giá... |
| Mức độ tin cậy | `reliability` | varchar(20) | 29 | | select: Cao/Trung bình/Thấp |
| Chính sách giao nhận | `delivery_policy` | varchar(255) | 30 | | TP/ngoại tỉnh... |
| Chính sách công nợ | `debt_policy` | varchar(50) | 31 | | select: Tiền mặt/CN30/CN60/CN90/Trả trước |
| Hàng lỗi / Hàng trả | `defect_return` | varchar(255) | 32 | | tỷ lệ trả hàng |
| Nhận xét (NSPT) | `nspt_note` | varchar(20) | 33 | | select Đạt/Không đạt (+ lý do ở `nspt_reason`) |
| Lý do nhận xét NSPT | `nspt_reason` | text | 33 | | |
| Duyệt dòng (TP/QL) | `line_approve` | varchar(20) | 34 | | tùy chọn (nếu duyệt theo từng NCC) |
| Yêu cầu dòng (TP/QL) | `line_approve_note` | text | 35 | | |

### A3. Backend & API
- `GET /api/surveys-supplier` (filter+phân trang) · `GET /{id}` (header + lines) · `POST` · `PATCH` (replace lines) · `DELETE` · `POST /{id}/submit|approve|reject`.
- Auto: `supplier_count = len(lines)`, `main_supplier = lines[0].supplier_name`.
- Khi chọn NCC cũ (`supplier_code` có trong `tab_supplier`) → tự fill tên pháp lý/MST/địa chỉ.

### A4. Tiêu chí ĐẠT
- [ ] Tạo phiếu + thêm ≥2 NCC inline (đủ cột Sheet 3, không thiếu cột nào).
- [ ] Chọn NCC cũ tự điền MST/tên pháp lý; NCC mới nhập tay.
- [ ] Mức tin cậy & nhận xét NSPT hiển thị badge.
- [ ] Gửi duyệt → Duyệt/Không duyệt (chỉ quyền `approve`) + ghi chú → log.
- [ ] Auto đếm số NCC + NCC chính ngoài list.
- [ ] Đính kèm báo giá; xem lịch sử.

---

## B. KHẢO SÁT SẢN PHẨM (Sheet 4)

### B1. Giao diện
- **List** (`/surveys-product`): Mã YC, Ngày, **NCC chính**, **SP chính**, Số SP, Trạng thái duyệt. Filter tương tự.
- **Detail** 3 section như A1, đổi bảng con = **BẢNG KHẢO SÁT SP** (đủ cột B2). Có **Tổng thành tiền** (sum). Nút Thêm SP/Thêm nhiều.

### B2. `tab_survey_product_line` (mỗi dòng = 1 SP) — ĐỦ cột Sheet 4
| Nhãn | key | Kiểu | Sheet | Bắt buộc | Ghi chú |
|---|---|---|---|:--:|---|
| (FK phiếu) | `survey_id` | bigint | — | ✓ | |
| Tên viết tắt NCC | `supplier_code` | varchar(50) | 14 | ✓ | |
| Mã NVL/VTBB nội bộ | `internal_code` | varchar(50) | 15 | | |
| Tên SP theo NCC | `product_name` | varchar(255) | 17 | ✓ | có thể khác tên nội bộ |
| Thông số kỹ thuật | `spec` | text | 18 | | kích thước, tỷ trọng, màu... |
| Xuất xứ | `origin` | varchar(100) | 19 | | VN, TQ, Lào... |
| ĐVT báo giá NCC | `quote_unit` | varchar(25) | 20 | | Cuộn, Thùng, Kg... |
| MOQ | `moq` | decimal(18,3) | 21 | | lượng đặt tối thiểu |
| Giá theo khung SL | `price_by_volume` | decimal(18,2) | 22 | | |
| Khung sản lượng | `volume_range` | varchar(100) | 23 | | 100-500, 500-1000... |
| VAT (%) | `vat` | decimal(5,2) | 24 | | |
| Thành tiền | `amount` | decimal(18,2) | 25 | | **auto** = qty×giá×(1+VAT) |
| ĐVT quy đổi nội bộ | `internal_unit` | varchar(25) | 26 | | từ Sheet 5 (quy đổi) |
| Thành tiền quy đổi | `amount_converted` | decimal(18,2) | 27 | | **auto** theo hệ số quy đổi |
| Số lượng YC | `request_qty` | decimal(18,3) | (7) | | dùng tính thành tiền |
| Chi phí chành/vận chuyển | `shipping_cost` | decimal(18,2) | 28 | | |
| Thời gian giao hàng | `delivery_time` | varchar(100) | 29 | | |
| Địa điểm giao nhận | `delivery_place` | varchar(255) | 30 | | kho cty/kho NCC |
| Link file báo giá | `quote_file` | varchar(500) | 31 | | Drive |
| Mẫu sẵn | `sample_ready` | tinyint(1) | 32 | | checkbox |
| Ngày lấy mẫu | `sample_date` | date | 33 | | |
| Số lượng mẫu | `sample_qty` | decimal(18,3) | 34 | | |
| Đánh giá chất lượng LAB | `lab_result` | varchar(20) | 35 | | select Đạt/Không đạt (+ `lab_note`) |
| Ghi chú LAB | `lab_note` | text | 35 | | tình trạng mẫu |
| Nhận xét (NSPT) | `nspt_note` | varchar(20) | 36 | | Hợp tác/Không + lý do |
| Lý do NSPT | `nspt_reason` | text | 36 | | |
| Duyệt dòng (TP/QL) | `line_approve` | varchar(20) | 37 | | tùy chọn |
| Yêu cầu dòng (TP/QL) | `line_approve_note` | text | 38 | | |

### B3. Backend & API
- `GET/POST/PATCH/DELETE /api/surveys-product` + `/{id}/submit|approve|reject`.
- Auto: `amount = request_qty × price_by_volume × (1 + vat/100)`; `amount_converted` qua `tab_unit_conversion` (nếu có hệ số) — chưa có thì = amount.
- Auto: `product_count`, `main_product = lines[0].product_name`, `main_supplier`.

### B4. Tiêu chí ĐẠT
- [ ] Thêm ≥1 SP inline đủ cột Sheet 4 (không thiếu).
- [ ] Thành tiền & thành tiền quy đổi auto đúng.
- [ ] Kết quả LAB Đạt/Không đạt badge.
- [ ] Mẫu sẵn (checkbox), ngày/số lượng mẫu.
- [ ] Gửi duyệt/Duyệt/Từ chối + log; đính kèm.

---

## C. QUY ĐỔI ĐVT (Sheet 5) — phục vụ cột "thành tiền quy đổi"
- `tab_unit_conversion(product_code, quote_unit, internal_unit, factor)`.
- Hàm `convert(amount, product_code, quote_unit)` → `amount / factor` (hoặc × tùy chiều). Không có hệ số → giữ nguyên + cảnh báo "chưa quy đổi".
- **ĐẠT:** [ ] giá quy đổi hiển thị; [ ] QLTM thấy giá đồng nhất giữa các NCC.

---

## D. LƯU Ý CHO DEV
- Bảng con **inline kéo ngang** (overflow-x), tái dùng pattern `PurchaseRequestDetail` (ô input/select trong cell, Thêm dòng/Thêm nhiều).
- Dropdown: `supplier_code` ← `/api/suppliers`; `item_group` ← `/api/item-groups`; `quote_unit`/`internal_unit` ← `/api/units`.
- Khi tạo từ PYC (`?pyc=<code>`): tự fill `pr_code`, `received_date`, `requirement_detail` (và với SP: tự nạp các dòng SP được phân cho NSPT hiện tại).
- Mọi cột Sheet 3/4 ở trên là **bắt buộc có** trong DB & form (thừa cột phụ được, thiếu thì KHÔNG đạt).
