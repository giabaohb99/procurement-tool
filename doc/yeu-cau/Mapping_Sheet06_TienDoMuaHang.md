# Bản đồ ánh xạ — Sheet 6 "TIẾN ĐỘ MUA HÀNG" (46 cột) → kiến trúc Mini Tool

> Mục đích: chốt **trường nào nằm ở bảng/chức năng nào** trước khi code. Yêu cầu: tối thiểu phải có **đủ** 46 cột này.

## A. Kiến trúc (4 bảng dữ liệu + 1 nhóm tự tính)

```
┌─ tab_purchase_order (PO HEADER) ── 1 đơn ───────────────────────────────┐
│   ngày đặt · công ty (pháp lý HĐ) · NCC bán · bộ phận · NSPT · Mã MISA   │
│   hình thức thanh toán · yêu cầu khác · ghi chú · trạng thái             │
│                                                                          │
│   └─ tab_po_item (DÒNG HÀNG / mỗi VTBB-NL) ── nhiều dòng ───────────┐    │
│        mã/tên/phân loại/xuất xứ · tên trên HĐ · ĐVT · SL YC · SL đặt │    │
│        đơn giá · VAT · thành tiền(đặt) · Mã HH · NCC sẵn hàng        │    │
│        ngày yêu cầu có hàng · SL đã nhận(Σ) · còn lại · trạng thái dòng   │
│                                                                     │    │
│        └─ tab_po_delivery (VẬN CHUYỂN & NHẬN — GIAO NHIỀU LẦN) ─┐   │    │
│             lần giao · kho nhận · đơn vị VC · SL gửi · ĐVT VC    │   │    │
│             SL đã nhận · ngày dự kiến/nhận thực tế · số HĐ       │   │    │
│             đơn giá VC · thành tiền VC(=SL gửi×đơn giá) · QC     │   │    │
│             số ngày QĐ · ngày QĐ · CL ngày (3 loại) · trạng thái │   │    │
└──────────────────────────────────────────────────────────────────┘   │ │
            │ khi nhập "SL đã nhận" trên 1 lần giao → CHẠY NGẦM:          │ │
            ▼                                                            │ │
   tab_goods_receipt (phiếu nhập kho) · tab_inventory (+tồn)            │ │
   tab_payable (công nợ HÀNG = SL nhận×giá×VAT + công nợ VC = thành tiền VC)
```

- **Vận chuyển = bảng riêng `tab_po_delivery`, giao nhiều lần.** Nhập SL nhận + đơn giá VC → **ra tiền** (thành tiền VC + công nợ VC theo ĐVT vận chuyển).
- **Số hóa đơn** nhập ở **từng lần nhận** (mỗi lần giao gắn 1 sản phẩm → đúng "theo sản phẩm"); 1 SP giao nhiều lần thì mỗi lần 1 HĐ.

## B. Ánh xạ 46 cột

| # | Header (Sheet) | Nằm ở | Trường | TT |
|--|--|--|--|--|
| 1 | Stt | (UI) | — | Tự đánh số |
| 2 | Ngày tiếp nhận | PO header | `order_date` | ✅ |
| 3 | Ngày yêu cầu có hàng | PO item | `required_date` | 🔴 thêm |
| 4 | Ngày dự kiến nhận tại kho | PO delivery | `promised_date` | ✅ |
| 5 | Ngày nhận thực tế | PO delivery | `received_date` | ✅ |
| 6 | Bộ phận/Cá nhân đặt hàng | PO header | `department` | ✅ |
| 7 | Pháp lý lấy hóa đơn | PO header | `company_id` | ✅ |
| 8 | NSPT | PO header | `nspt` | ✅ |
| 9 | NCC VTBB/NL trong nước | PO header | `supplier_code`/`supplier_name` | ✅ |
| 10 | Mã đơn Misa | PO header | `misa_code` | ✅ |
| 11 | Phân loại VTBB/NL | PO item | `item_group` | ✅ |
| 12 | Mã VTBB/NL | PO item | `product_code` | ✅ |
| 13 | Tên VTBB/NL | PO item | `product_name` | ✅ |
| 14 | Xuất xứ/TSKT/chất liệu | PO item | `spec` | ✅ |
| 15 | Tên trên hóa đơn VTBB/NL | PO item | `invoice_name` | 🔴 thêm |
| 16 | Trạng thái | PO / item / delivery | `status`/`line_status` | ✅ |
| 17 | NCC có sẵn hàng | PO item | `supplier_ready` (bool) | 🔴 thêm |
| 18 | Kho nhận | PO delivery (+item mặc định) | `warehouse_code` | ✅ |
| 19 | Đơn vị vận chuyển | PO delivery | `carrier_code` | ✅ |
| 20 | Số lượng gửi vận chuyển | PO delivery | `ship_qty` | ✅ |
| 21 | ĐVT vận chuyển | PO delivery | `ship_unit` | ✅ |
| 22 | Số lượng yêu cầu | PO item | `qty_request` | ✅ |
| 23 | ĐVT | PO item | `unit` | ✅ |
| 24 | Số lượng đặt NCC | PO item | `qty_order` | ✅ |
| 25 | Số lượng đã nhận | PO item (Σ) + delivery | `qty_received`/`received_qty` | ✅ |
| 26 | Đơn giá | PO item | `price` | ✅ |
| 27 | VAT | PO item | `vat` | ✅ |
| 28 | **Thành tiền đơn hàng** | PO item (tính) | `amount` = **SL đặt × đơn giá × (1+VAT)** | ✅ ⚠️ |
| 29 | Yêu cầu khác | PO header | `extra_request` | 🟡 chuyển từ delivery → header |
| 30 | Ngày đặt hàng NCC | PO header | `order_date` (=cột 2) | ✅ |
| 31 | **Số hóa đơn** | PO delivery | `invoice_no` (theo từng lần nhận) | ✅ |
| 32 | ~~Số lần nhận~~ | — | **BỎ** | ❌ Excel phải tách dòng để đếm; mô hình ta đã có nhiều `po_delivery`/SP nên không cần cột này |
| 33 | Chi tiết tiến độ, ghi chú khác | PO delivery | `progress_note` | ✅ |
| 34 | Số ngày có hàng theo quy định | PO delivery (tính) | `std_days` | ✅ |
| 35 | Ngày quy định | PO delivery (tính) | `regulated_date` | ✅ |
| 36 | Đơn giá/ĐVT vận chuyển | PO delivery | `shipping_unit_price` | ✅ |
| 37 | Thành tiền vận chuyển | PO delivery (tính) | `shipping_amount`=SL gửi×đơn giá VC | ✅ |
| 38 | CL ngày NCC dự kiến − nhận | PO delivery (tính) | `diff_promise` | ✅ |
| 39 | CL ngày quy định − nhận | PO delivery (tính) | `diff_regulated` | ✅ |
| 40 | CL ngày quy định − KD yêu cầu | PO delivery (tính) | `diff_required` | 🔴 thêm |
| 41 | Tháng | (tính) | format MM/YYYY từ `order_date` | 🟢 tính |
| 42 | Mã HH | PO item | `fg_code` | 🔴 thêm |
| 43 | Tên VTBB/NL trên hóa đơn | PO item | `invoice_name` (=cột 15) | 🔴 thêm |
| 44 | Tên sản phẩm (HH) | (tra theo `fg_code`) | từ bảng product | 🟢 tính |
| 45 | Tên pháp lý (HH) | (tra theo `fg_code`) | product.`legal_name` | 🟡 cần field ở product |
| 46 | Hình thức thanh toán cho NCC | PO header | `payment_terms` (mặc định theo NCC) | 🟡 thêm |

**Chú thích:** ✅ đã có · 🔴 cần thêm field · 🟡 cần điều chỉnh · 🟢 tính/hiển thị (không lưu).

## C. Tổng hợp việc cần thêm (sau khi anh duyệt bảng này)
1. **PO item** thêm: `required_date` (ngày YC có hàng), `invoice_name` (tên trên HĐ), `supplier_ready` (NCC sẵn hàng – dùng tính số ngày QĐ), `fg_code` (Mã HH).
2. **PO delivery** thêm: `diff_required` (CL ngày quy định − KD yêu cầu).
3. **PO header** thêm: `payment_terms` (hình thức TT cho NCC); chuyển `extra_request` (yêu cầu khác) về header.
4. **Product** thêm: `legal_name` (tên pháp lý HH) — phục vụ cột 44/45.
5. Tính/hiển thị: Stt, Tháng, Số lần nhận, Tên HH/Tên pháp lý HH (tra theo fg_code).

## D. ✅ ĐÃ CHỐT — Cột 28 "Thành tiền đơn hàng" = **SL THỰC NHẬN × đơn giá × (1+VAT)**
- `po_item.amount` = `qty_received × price × (1+VAT)` (trùng công nợ hàng).
- **Bản in PO (đặt hàng gửi NCC)** tính riêng theo **SL đặt** (qty_order) — vì là chứng từ đặt hàng, không phụ thuộc SL nhận.
- `extra_request` (Yêu cầu khác, cột 29) giữ ở **dòng giao (delivery)** cho khớp dạng per-row của sheet.
