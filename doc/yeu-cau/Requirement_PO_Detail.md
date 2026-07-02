# Requirement chi tiết — ĐƠN MUA HÀNG (PO) · Module trung tâm (Phase 2)

> PO là **hub vận hành**: từ 1 đơn mua thao tác gần hết — đặt hàng → in PO → giao hàng (nhiều lần) → nhận hàng (GR) → nhập kho/tồn → hóa đơn → công nợ (2 luồng) → thanh toán.
> Nguyên tắc gốc (bám yêu cầu ban đầu):
> 1. **1 PO thao tác gần hết mọi thứ** của vòng đời mua hàng.
> 2. **1 dòng hàng (sản phẩm) có thể GIAO NHIỀU LẦN** (giao từng phần) → mỗi lần là 1 `po_delivery`.
> 3. **Vận chuyển tách bạch**: NCC vận chuyển có **công nợ & thanh toán RIÊNG** với NCC bán hàng.

---

## 0. PHÂN TÍCH PHỤ THUỘC MODULE (làm trước khi code)

| Module | Trạng thái | Vai trò với PO |
|---|---|---|
| `company`, `supplier`, `product`, `warehouse`, `unit`, `item_group` | ✅ Có | Danh mục dropdown (NCC, kho, ĐVT…) |
| `supplier` (`supplier_type=transport`) | ✅ Có | **NCC vận chuyển** (carrier) — dùng cho công nợ VC riêng |
| `purchase_request`, `survey` | ✅ Có | Nguồn tạo PO (đã duyệt NCC/SP) |
| **`purchase_order`** (header+items+deliveries) | 🔴 Dựng mới | Trung tâm |
| **`goods_receipt`** (GR + items) | 🔴 Dựng mới | Nhận hàng & QC theo từng lần giao |
| **`inventory`** (+ `inventory_move`) | 🔴 Dựng mới | Tồn kho theo company/kho; +nhập từ GR |
| **`payable`** (2 luồng goods/shipping) | 🔴 Dựng mới | Công nợ — **module/màn riêng**, PO không hiển thị |
| **`payment_request`** (+ lines) | 🔴 Dựng mới | Phiếu **yêu cầu thanh toán** (1 NCC/phiếu, gom nhiều PO, in được) |
| `core/approval.py` | 🔴 Dựng mới | Duyệt theo ngưỡng (xem `Requirement_Email_Approval.md`) |
| `attachment` (+ entity `delivery`), `audit_log`, `notify(email)` | ✅/🟡 | Đính kèm phiếu giao/chứng từ, log, thông báo |
| `contract` | ⏳ Sau | Cảnh báo HĐ hết hạn (không chặn Phase 2) |

**Thứ tự dựng đề xuất:** ① `inventory` → ② `purchase_order` (header+item+delivery trong popup +đính kèm phiếu giao) + approval + in PO A4 ngang → ③ `goods_receipt` **ngầm** (→ ghi `inventory_move` + sinh `payable` hàng+VC) → ④ màn **Công nợ** (xem/tuổi nợ/filter) → ⑤ **Yêu cầu thanh toán** (gom theo NCC + in).

---

## 1. MÔ HÌNH DỮ LIỆU (đủ — superset Sheet 6)

### 1.1 `tab_purchase_order` (header)
| Nhãn | key | Kiểu | Sheet | Ghi chú |
|---|---|---|---|---|
| Mã PO | `code` | varchar(50) | — | auto **`PO00045`** (`PO` + số tăng dần 5 chữ số) — gọn, không theo mẫu in |
| Mã đơn MISA | `misa_code` | varchar(50) | J | nhập tay — **bắt buộc khi Gửi duyệt/Duyệt** (nháp cho trống) |
| Mã PYC | `pr_code` | varchar(50) | — | nguồn (nếu tạo từ PYC) |
| Mã khảo sát | `survey_code` | varchar(50) | — | nếu tạo từ khảo sát |
| Công ty nhận hóa đơn | `company_id` | bigint | G | dropdown |
| NCC bán hàng | `supplier_code` | varchar(50) | I | dropdown (goods) |
| Bộ phận đặt | `department` | varchar(255) | F | |
| NSPT | `nspt` | varchar(100) | H | |
| Ngày đặt hàng | `order_date` | date | AD | |
| VAT (%) | `vat_rate` | decimal(5,4) | AA | mặc định 0.08 |
| Là đơn gấp | `is_urgent` | tinyint(1) | — | luồng duyệt nhanh |
| Trạng thái | `status` | varchar(30) | P | (mục 2) |
| Ghi chú | `note` | text | | |
| (audit) | created_*/updated_* | | | |

### 1.2 `tab_po_item` (dòng hàng)
| Nhãn | key | Kiểu | Sheet | Ghi chú |
|---|---|---|---|---|
| (FK) | `po_id` | bigint | | |
| Mã SP | `product_code` | varchar(50) | L | dropdown products |
| Tên SP | `product_name` | varchar(255) | M | |
| Phân loại | `item_group` | varchar(100) | K | |
| Xuất xứ/TSKT | `spec` | varchar(255) | N | |
| ĐVT | `unit` | varchar(25) | W | dropdown units |
| SL yêu cầu | `qty_request` | decimal(18,3) | V | |
| **SL đặt NCC** | `qty_order` | decimal(18,3) | X | có thể tròn tối thiểu |
| Đơn giá | `price` | decimal(18,2) | Z | |
| VAT (%) | `vat` | decimal(5,2) | AA | |
| Thành tiền | `amount` | decimal(18,2) | AB | auto = qty_order×price×(1+VAT) |
| **SL đã nhận (tổng)** | `qty_received` | decimal(18,3) | Y | auto = Σ delivery.received_qty |
| **SL còn lại** | `qty_remaining` | decimal(18,3) | — | auto = qty_order − qty_received |
| Trạng thái dòng | `line_status` | varchar(30) | — | Chưa giao/Đang giao/Đủ/Thiếu |

### 1.3 `tab_po_delivery` (GIAO NHIỀU LẦN — mỗi dòng = 1 lần giao của 1 po_item)
| Nhãn | key | Kiểu | Sheet | Ghi chú |
|---|---|---|---|---|
| (FK PO) | `po_id` | bigint | | |
| (FK dòng hàng) | `po_item_id` | bigint | | giao cho SP nào |
| Lần giao | `delivery_no` | int | AF | 1,2,3… |
| Kho nhận | `warehouse_code` | varchar(50) | R | dropdown kho |
| **Đơn vị vận chuyển** | `carrier_code` | varchar(50) | S | supplier `transport` / "NCC tự VC" |
| SL gửi VC | `ship_qty` | decimal(18,3) | T | |
| ĐVT vận chuyển | `ship_unit` | varchar(25) | U | Kiện, thùng… |
| **SL đã nhận** | `received_qty` | decimal(18,3) | Y | |
| NCC cam kết giao | `promised_date` | date | D | |
| Ngày dự kiến nhận | `expected_date` | date | D | |
| **Ngày nhận thực tế** | `received_date` | date | E | |
| Ngày quy định | `regulated_date` | date | AI | |
| Số ngày quy định | `std_days` | int | AH | theo phân loại + NCC sẵn hàng (Data 1) |
| Số hóa đơn | `invoice_no` | varchar(50) | AE | |
| **Đơn giá VC** | `shipping_unit_price` | decimal(18,2) | AJ | RIÊNG |
| **Thành tiền VC** | `shipping_amount` | decimal(18,2) | AK | RIÊNG (không cộng giá hàng) |
| CL ngày (cam kết−nhận) | `diff_promise` | int | AL | auto: <0 = trễ |
| CL ngày (quy định−nhận) | `diff_regulated` | int | AM | auto: <0 = không đạt |
| Yêu cầu khác | `extra_request` | text | AC | ghi chú yêu cầu thêm cho lần giao |
| Chi tiết tiến độ/ghi chú | `progress_note` | text | AG | nguyên nhân trễ |
| Kết quả QC | `qc_result` | varchar(20) | — | Đạt/Thiếu/Lỗi |
| Trạng thái giao | `status` | varchar(30) | P | auto: Chờ giao/Giao thiếu/Đã nhận/Lỗi |

> **ĐVT vận chuyển (`ship_unit`)** là đơn vị tính cước (Kiện/Chuyến/m²/tấn) → công nợ vận chuyển = `ship_qty × shipping_unit_price` theo ĐVT này, tách khỏi ĐVT hàng. `std_days/regulated_date/diff_promise/diff_regulated/status` được **tính tự động** khi lưu (theo `order_date`, phân loại, ngày cam kết/nhận).

### 1.4 `tab_goods_receipt` (+ `tab_gr_item`) — ✅ CHỐT: bảng RIÊNG, sinh NGẦM
> Người dùng **chỉ thao tác trên dòng giao (po_delivery) của PO**: nhập `received_qty` + QC. Backend **tự sinh** 1 bản ghi `goods_receipt` + `gr_item` ngầm (KHÔNG có màn nhập GR riêng) để lưu vết phiếu nhập kho & phục vụ tồn/báo cáo. Sửa lại SL nhận trên dòng giao → cập nhật lại GR + inventory_move tương ứng (idempotent theo `delivery_id`).
`goods_receipt`: `code` (auto `GR#####`), `po_id`, `delivery_id`, `warehouse_code`, `received_date`, `qc_result`, `qc_note`, `doc_status`, `note`.
`gr_item`: `gr_id`, `po_item_id`, `product_code`, `qty_received`, `unit`, `qc_result`, `note`.

### 1.5 `tab_inventory` (+ `tab_inventory_move`)
`inventory`: `company_id`, `warehouse_code`, `product_code`, `qty` (tồn hiện tại). (unique: company+warehouse+product)
`inventory_move`: `warehouse_code`, `product_code`, `qty` (+/−), `ref_type`(gr/adjust), `ref_id`, `note`, `created_at`.

### 1.6 `tab_payable` · `tab_payment_request` (+ `tab_payment_request_line`)
`payable` (1 dòng = 1 khoản nợ phát sinh, sinh ngầm khi nhận hàng):
`company_id`, `supplier_code`, **`source_type`** (`goods`|`shipping`), `ref_type`(delivery), `ref_id`, `po_code`, `invoice_no`, `incur_date` (ngày phát sinh = ngày nhận), `amount`, `vat`, `total` (amount+vat), `due_date`, `paid_amount`, `status` (`Chờ TT`|`Trả một phần`|`Đã TT`).
`payment_request` (phiếu **yêu cầu thanh toán** — in được, **chỉ 1 NCC/phiếu**):
`code` (auto `YCTT00045`), `supplier_code`, `company_id`, `request_date`, `total`, `note`, `status` (`Nháp`|`Chờ duyệt`|`Đã duyệt`|`Đã chi`), `created_by`, `attachment_ref`.
`payment_request_line`: `request_id`, `payable_id`, `po_code`, `amount` (số tiền đề nghị trả cho khoản nợ đó).

---

## 2. VÒNG ĐỜI PO (state machine) + SIDE-EFFECT

```
Nháp ──submit──► Chờ duyệt ──approve──► Đã duyệt ──(gửi NCC)──► Đã đặt hàng
   ▲                 │reject                                        │
   └─────────────────┘                                              ▼
                                              Đang giao ◄── tạo lần giao (delivery)
                                                 │ nhận hàng (GR) từng lần
                                                 ▼
                              Đã nhận đủ (Σ received = Σ qty_order) ──► Hoàn thành
                                                 │ (hoặc) Giao thiếu / Hủy
```
**Side-effect khi thao tác:**
- **approve** → mở khóa "gửi NCC" + in PO (kiểm ngưỡng duyệt — `Requirement_Email_Approval §1.3`).
- **Nhận hàng (GR)** cho 1 delivery → ghi `inventory_move (+received_qty)` → cập nhật `inventory.qty`; cập nhật `po_item.qty_received/qty_remaining`; **sinh/cộng `payable` luồng `goods`** (received_qty × price + VAT).
- **shipping_amount** của delivery → **sinh `payable` luồng `shipping`** cho `carrier_code`.
- Khi `Σ received_qty == Σ qty_order` mọi dòng → PO `Đã nhận đủ`.

**"1 SP giao nhiều lần":** `po_item.qty_remaining = qty_order − Σ delivery.received_qty`. Cho phép tạo nhiều `po_delivery` cho cùng `po_item_id` đến khi remaining = 0. Mỗi lần giao có thể khác kho/đơn vị VC/ngày.

---

## 3. GIAO DIỆN — PO detail là "bàn làm việc" (1 trang)

`/purchase-orders/{id}` & `/new`:
1. **Thông tin chung** (header fields 1.1) — NCC, công ty hóa đơn, ngày đặt, VAT, gấp, ghi chú; Mã PYC autocomplete (tự điền NSPT/bộ phận).
2. **Dòng hàng** — bảng inline (1.2) kéo ngang: mã SP, tên, ĐVT, SL đặt, đơn giá, VAT, thành tiền (auto), **SL đã nhận / còn lại (readonly, auto từ các lần giao)**, cột **Tiến độ giao** (vd "300/1.000"), nút **mở popup Chi tiết dòng**.
3. ✅ **GIAO HÀNG NẰM TRONG POPUP "CHI TIẾT DÒNG" của từng `po_item`** (giống popup Khảo sát). Mở popup 1 dòng hàng → thấy:
   - Thông tin SP (readonly) + tổng SL đặt / đã nhận / còn lại.
   - **Bảng các lần giao (`po_delivery`) của riêng dòng hàng đó** — kéo ngang, thêm/xóa dòng: Lần giao · Kho nhận · **Đơn vị vận chuyển** · SL gửi · ĐVT VC · **SL đã nhận** · Ngày cam kết/dự kiến/thực nhận · Số HĐ · **Đơn giá VC · Thành tiền VC (riêng)** · QC (Đạt/Thiếu/Lỗi) · ghi chú tiến độ.
   - **Đính kèm phiếu giao hàng thực tế cho từng lần giao** (upload ảnh/PDF biên bản giao nhận → lưu vào `tab_delivery_attachment` gắn `delivery_id`).
   - Nhập `received_qty` + QC trên 1 dòng giao = **nhận hàng** → backend ngầm: sinh/cập nhật `goods_receipt`, ghi `inventory_move (+)`, cộng `payable` (goods + shipping). User không mở màn GR riêng.
4. **Chứng từ chung** đính kèm (báo giá, HĐ…) + **Lịch sử thao tác**.
- Thanh đầu: Lưu · Gửi duyệt · Duyệt · **🖨 In PO gửi NCC** (§3b) · Hủy.
- Tổng: tiền hàng / VAT / tổng tiền hàng + **Tổng cước vận chuyển (riêng)**.

> ⚠️ **PO KHÔNG hiển thị công nợ.** Nhận hàng vẫn sinh công nợ ngầm, nhưng việc xem/thanh toán nằm ở **module Công nợ riêng** (§4).

> Lý do gom giao hàng vào popup dòng: 1 SP giao nhiều lần → đặt ngay trong ngữ cảnh dòng hàng đó là tự nhiên nhất, tránh bảng giao hàng phẳng phải chọn lại po_item.

### Bảng phụ: `tab_delivery_attachment`
`id`, `delivery_id`, `file_url`, `filename`, `kind` (delivery_slip/invoice/other), `uploaded_by`, `created_at`. (Dùng chung `core/storage.py` R2 + endpoint `/api/attachments` mở rộng entity=`delivery`.)

---

## 3b. IN PO GỬI NCC — mẫu **A4 NẰM NGANG (landscape)**

Route in riêng (ngoài layout): `/print/purchase-order/:id` → mở tab mới, CSS `@page { size: A4 landscape; margin: 12mm }`, nút **In PO gửi NCC** ở thanh đầu PO detail. Bám đúng mẫu ảnh DEGO HOLDING:

**Đầu trang (trái):** Tên công ty xuất HĐ (`company.name`) in đậm · Địa chỉ · Mã số thuế. **Kính gửi:** tên NCC (`supplier.name`) + Địa chỉ NCC.

**Tiêu đề giữa:** `ĐƠN ĐẶT HÀNG` · **Số: `{po.code}`** (mã PO gọn, vd `PO00045`).

**Bảng hàng hóa** (đúng 13 cột theo ảnh):
`STT · Mã · Tên hàng hóa · Xuất xứ/TSKT/chất liệu · ĐVT · SL · Đơn giá (Chưa VAT) · VAT · Đơn giá (Đã VAT) · Thành tiền · Kho nhận · Tên trên HĐ · Ghi chú`
- Đơn giá (Đã VAT) = `price × (1+vat)`; Thành tiền = `qty_order × đơn giá đã VAT`.
- "Tên trên HĐ" = tên SP đầy đủ hiển thị trên hóa đơn (lấy `product_name`); "Kho nhận" = kho của lần giao/đặt.
- Dòng cuối **TỔNG CỘNG** = Σ Thành tiền.

**Khối "Thoả thuận khác"** (text cố định, đổ dữ liệu PO/NCC vào chỗ trống):
1. Thời gian thanh toán / Số ngày công nợ: `{debt_policy của NCC}` (vd "Công nợ 30 ngày").
2. Thời gian nhận hóa đơn: "Chậm nhất 24h kể từ khi nhận hàng".
3. Thông tin nhận hàng: Phương thức giao nhận · Nơi giao (`supplier.name`/địa điểm) · Địa chỉ · Người liên hệ bên mua.
4. Thông tin nhận hóa đơn: Tên đơn vị (`company.name`) · MST · Địa chỉ · Mail nhận HĐ (`company.invoice_email`).
5. Hàng lỗi, sai mẫu: 3 dòng điều khoản cố định (kiểm tra 15 ngày · báo kèm bằng chứng · thu hồi/đổi trả 07 ngày, phí do bên bán chịu).

**Cuối trang:** "Các thông tin, file, hình ảnh gửi kèm đơn hàng:" · dòng địa điểm-ngày "Cần Thơ, ngày {dd} tháng {mm} năm {yyyy}" (theo `order_date`) · 2 ô chữ ký: **Trưởng bộ phận** | **Người lập**.

> Các điều khoản cố định (#2, #5, mục nhận HĐ) đặt trong 1 chỗ cấu hình (constants/`tab_setting`) để sửa không cần đụng code.

---

## 4. MODULE CÔNG NỢ (màn hình riêng) + YÊU CẦU THANH TOÁN

**Nguyên tắc:** NCC sản phẩm và NCC vận chuyển là **2 supplier khác nhau** (`supplier_type` = goods / transport) → mỗi công nợ gắn `supplier_code` của đúng đối tượng + `source_type` để không bao giờ trộn. Công nợ **sinh tự động** khi nhận hàng, người dùng hầu như không tạo tay. **Việc xem & thanh toán tách hẳn khỏi PO**, nằm ở 2 màn hình: **Công nợ** và **Yêu cầu thanh toán**.

### 4.1 Khi nào sinh công nợ — sinh theo TỪNG LẦN NHẬN (mỗi `po_delivery` được nhận)
Lúc user nhập `received_qty` + QC trên 1 lần giao (= nhận hàng), backend chạy ngầm tạo/cập nhật **2 bản ghi payable** cho lần giao đó (idempotent theo `ref_id = delivery_id` — sửa SL nhận thì cập nhật lại, không nhân đôi):

**(A) Công nợ NCC sản phẩm — `source_type='goods'`**
- `supplier_code` = NCC bán của PO (`po.supplier_code`).
- `ref_type='delivery'`, `ref_id=delivery_id`, `po_code`.
- `amount` (trước VAT) = `received_qty × po_item.price` (giá của dòng hàng mà lần giao này thuộc về).
- `vat` = `amount × po_item.vat`; tổng phải trả = `amount + vat`.
- Chỉ tính theo **SL thực nhận** (không phải SL đặt) → giao thiếu thì nợ ít, giao bù lần sau sinh payable mới.

**(B) Công nợ NCC vận chuyển — `source_type='shipping'`**
- `supplier_code` = `delivery.carrier_code`. Nếu là **"NCC tự vận chuyển"** (không có carrier riêng) ⇒ **KHÔNG sinh công nợ VC**.
- `ref_type='delivery'`, `ref_id=delivery_id`, `po_code`.
- `amount` = `delivery.shipping_amount` (= đơn giá VC × SL gửi, nhập ở popup). VAT VC mặc định 0 (chỉnh được).
- Hoàn toàn tách khỏi tiền hàng — không cộng vào (A).

`due_date` mỗi payable = `received_date + số ngày công nợ` lấy từ `supplier.debt_policy` (Tiền mặt = 0 ngày; Công nợ 30/60/90 ngày). `paid_amount=0`, `status='Chờ thanh toán'`.

> **Hiệu năng (đã chốt):** KHÔNG sum-từ-deliveries khi đọc. Mỗi `payable` lưu sẵn `total`/`paid_amount`/**`remaining`** (tính sẵn lúc ghi). Màn Công nợ phân trang ở DB + **mặc định lọc theo năm** (`period`=YYYY, có index) để giới hạn dữ liệu; 4 thẻ tổng dùng **1 truy vấn `SUM` ở DB** (index trên `due_date`/`status`/`period`), không quét toàn bảng. Bảng snapshot vật lý chỉ làm cho **báo cáo lịch sử ở Phase 3** (chạy ngầm), không dùng cho số liệu live (tránh lệch).

### 4.2 Màn hình CÔNG NỢ (`/payables`) — chỉ xem & lọc, không sửa tay
Danh sách các khoản nợ (`payable`), 1 dòng = 1 khoản phát sinh từ 1 lần nhận hàng. Cột: NCC · loại (Hàng/Vận chuyển) · Công ty · **Phát sinh từ PO** (`po_code`, click mở PO) · Số HĐ · Ngày phát sinh · Hạn trả · **Tuổi nợ** · Tổng nợ · Đã trả · **Còn lại** · Trạng thái.
- **Tuổi nợ (aging)** = số ngày từ `due_date` đến hôm nay (nếu đã quá hạn). Phân nhóm hiển thị màu: `Chưa đến hạn` · `1–30` · `31–60` · `61–90` · `>90` ngày quá hạn.
- **Filter:** theo **Công ty** · theo **Nhà cung cấp** · loại nợ (hàng/VC) · trạng thái (Chờ TT/Trả một phần/Đã TT) · khoảng ngày phát sinh · nhóm tuổi nợ · theo PO.
- Thẻ tổng trên đầu: Tổng nợ · Đã trả · Còn phải trả · Quá hạn.
- Nút **"Tạo yêu cầu thanh toán"**: tích nhiều dòng nợ (kể cả **nhiều PO khác nhau**) rồi bấm tạo. **Tiên quyết: các dòng đã chọn phải CÙNG 1 nhà cung cấp** — nếu chọn nợ của nhiều NCC, hệ thống **tách tự động: mỗi NCC ra 1 phiếu yêu cầu thanh toán riêng** (bao nhiêu NCC = bấy nhiêu phiếu).

### 4.3 PHIẾU YÊU CẦU THANH TOÁN (`/payment-requests`) — gom nhiều đơn, 1 NCC/phiếu, in được
`payment_request` (1 phiếu = 1 NCC). Tạo từ màn Công nợ (4.2) hoặc tạo mới rồi chọn NCC → liệt kê các khoản nợ còn lại của NCC đó (gồm **nhiều PO**) → tích + nhập số tiền đề nghị trả từng khoản → `payment_request_line[]`.
- `total` = Σ line. Trạng thái: Nháp → Chờ duyệt → Đã duyệt → **Đã chi**.
- Khi phiếu chuyển **Đã chi**: cộng `amount` từng line vào `payable.paid_amount`; `paid_amount ≥ total` ⇒ payable `Đã TT`, còn thiếu ⇒ `Trả một phần`.
- **Đính kèm chứng từ** (ủy nhiệm chi…) vào phiếu (R2).
- **🖨 In phiếu yêu cầu thanh toán** (A4 dọc): thông tin NCC, công ty, bảng các khoản nợ (PO/HĐ/ngày/số tiền), tổng tiền + tổng bằng chữ, ô ký (Người lập / Kế toán / Duyệt chi).

Vì mỗi phiếu chỉ gắn **1 `supplier_code`** → NCC sản phẩm và NCC vận chuyển luôn là **2 phiếu độc lập**, đúng yêu cầu "thanh toán NCC vận chuyển riêng, NCC sản phẩm riêng".

### 4.3 Hiển thị trên PO
Tab **Công nợ & Thanh toán** của PO có **2 bảng tách biệt**: "Công nợ hàng (NCC bán)" và "Công nợ vận chuyển (carrier)", mỗi bảng có tổng nợ / đã trả / còn lại + nút Thanh toán riêng.

---

## 5. API (gợi ý cho subagent BE)
```
purchase-orders:  GET (filter+page) · GET/{id} · POST · PATCH · DELETE
                  POST /{id}/submit|approve|reject · GET /{id}/print
deliveries:       quản lý lồng trong po_item (PATCH PO) HOẶC POST/PATCH/DELETE /po-items/{id}/deliveries
                  POST /deliveries/{id}/receive  (nhập SL nhận + QC → ngầm: GR + tồn + payable)
                  POST /attachments (entity=delivery, entity_id=delivery_id) — đính kèm phiếu giao thực tế
print PO:         GET /purchase-orders/{id}/print  → dữ liệu render mẫu A4 ngang (FE route /print/purchase-order/:id)
inventory:        GET /inventory?warehouse=&product=
payables:         GET /payables?company=&supplier=&source_type=&status=&aging=&po_code=  (chỉ xem, auto sinh)
                  GET /payables/summary  (tổng nợ/đã trả/còn lại/quá hạn theo filter)
payment-requests: POST /payment-requests {supplier_code, lines:[{payable_id, amount}]}  (nếu chọn nhiều NCC → server tách mỗi NCC 1 phiếu)
                  GET · GET/{id} · PATCH · POST /{id}/submit|approve|pay · GET /{id}/print
```
Mọi list trả `{total, items}`; action `POST /{id}/{verb}`; envelope `{success,data}`.

---

## 6. TIÊU CHÍ ĐẠT (acceptance)
**PO core**
- [ ] Tạo PO (từ PYC autocomplete hoặc thủ công) + dòng hàng + duyệt theo ngưỡng + **in PO**.
- [ ] Trạng thái chạy đúng state machine.

**Giao hàng nhiều lần (trong popup dòng hàng)**
- [ ] Mở popup 1 `po_item` → tạo được **nhiều `po_delivery`** ngay trong popup; `qty_remaining` giảm dần đúng; PO chuyển "Đã nhận đủ" khi remaining=0.
- [ ] Mỗi lần giao chọn được kho + **đơn vị vận chuyển** + đơn giá/thành tiền VC riêng.
- [ ] **Đính kèm phiếu giao hàng thực tế** cho từng lần giao (ảnh/PDF), xem lại được.

**In PO**
- [ ] Nút **In PO** → mẫu **A4 nằm ngang** đúng layout DEGO HOLDING (13 cột + Thoả thuận khác + chữ ký); số PO `PUR-ORD-YYYY-#####`; đổ đúng dữ liệu công ty/NCC/dòng hàng.

**GR + Tồn kho**
- [ ] Nhận hàng 1 delivery → **tồn kho tăng đúng** (inventory_move) theo company/kho/SP.
- [ ] QC Đạt/Thiếu/Lỗi; xử lý thiếu (giao bù) / lỗi (trả).

**Công nợ (module riêng) & yêu cầu thanh toán**
- [ ] PO **không** hiển thị công nợ; công nợ sinh ngầm khi nhận hàng (hàng theo SL thực nhận, VC theo `shipping_amount` — 2 luồng tách bạch).
- [ ] Màn **Công nợ**: xem **tuổi nợ**, filter theo **công ty / NCC / loại / trạng thái / PO**, thấy nợ từ PO nào, đã trả / còn lại; thẻ tổng.
- [ ] Bấm **Tạo yêu cầu thanh toán** từ nhiều dòng nợ (nhiều PO); chọn lẫn nhiều NCC → **tách mỗi NCC 1 phiếu** (bao nhiêu NCC = bấy nhiêu phiếu).
- [ ] Phiếu yêu cầu thanh toán **chỉ 1 NCC**, gom nhiều PO, **in được**; khi "Đã chi" cập nhật đã trả/còn lại của payable.

**DoD Phase 2 = tất cả mục trên pass + đính kèm + log + email cơ bản (PO duyệt).**

---

## 7. QUYẾT ĐỊNH ĐÃ CHỐT (2026-06-30)
1. ✅ **Tạo PO: CẢ HAI** — từ PYC/khảo sát đã duyệt (autocomplete tự điền) **hoặc** tạo tay.
2. ✅ **Phí vận chuyển theo TỪNG LẦN GIAO** (mỗi `po_delivery` 1 cước riêng).
3. ✅ **GR: có bảng `goods_receipt` riêng nhưng SINH NGẦM** — user chỉ thao tác trên dòng giao (line item) của PO; backend tự tạo/cập nhật phiếu nhập kho + inventory_move (xem §1.4). KHÔNG làm màn nhập GR riêng.
4. ✅ **Công nợ hàng sinh theo TỪNG LẦN NHẬN** (mỗi GR ngầm → cộng payable goods theo SL thực nhận).
5. ✅ **Hóa đơn theo lần giao** — `invoice_no` lưu ở `po_delivery` (1 PO có thể nhiều HĐ).
6. ✅ **Tồn kho Phase 2: chỉ +NHẬP (từ GR ngầm) + điều chỉnh tay.** Xuất kho để phase sau.
7. ✅ **ĐVT vận chuyển ≠ ĐVT hàng**: chỉ để hiển thị/tính cước, KHÔNG quy đổi vào SL nhận.

→ Thiết kế đã chốt. Bắt đầu dựng theo thứ tự **mục 0**: ① inventory → ② purchase_order(+items+deliveries) → ③ GR ngầm → ④ payable → ⑤ payment.
