# Requirement chi tiết — ĐƠN MUA HÀNG (PO) · NHẬN HÀNG (GR) · CÔNG NỢ & THANH TOÁN

> Phase 2–4. Trường = superset Sheet 6 (Tiến độ mua hàng) + chứng từ thật. Quy ước/UX/Approval/Email theo các file: `Requirement_Features_Detail.md`, `Requirement_Email_Approval.md`.
> Key = English snake_case (BE). Bảng con sửa **inline kéo ngang** (như PYC/Survey).

---

# C10. ĐƠN MUA HÀNG — PO (Phase 2)

## C10.1 Giao diện
- **List** (`/purchase-orders`): Mã PO, Mã MISA, NCC, Công ty hóa đơn, Ngày đặt, Tổng tiền, **Trạng thái**, cờ **trễ hạn**. Filter: NCC, kho, NSPT, trạng thái, cờ trễ, khoảng ngày đặt/nhận, pháp nhân.
- **Detail** (`/purchase-orders/{id}` & `/new`) — sections:
  1. *Thông tin chung*: Mã PO (tự sinh), Mã đơn MISA, Mã PYC liên kết, NCC (dropdown), Công ty nhận hóa đơn (dropdown), Ngày đặt, VAT(%), Ghi chú.
  2. *Dòng hàng (inline)*: SP, ĐVT, **SL đặt NCC**, đơn giá, VAT → **thành tiền auto**.
  3. *Giao hàng (bảng con nhiều lần, inline kéo ngang)* — đủ cột Sheet 6 (C10.3).
  4. Tổng tiền hàng / VAT / Tổng thanh toán + **Tổng cước vận chuyển (riêng)**.
- Nút: Lưu · Gửi duyệt · **Duyệt PO** · **In PO gửi NCC** · Cập nhật giao nhận · Hủy.

## C10.2 `tab_purchase_order` (header) + `tab_po_item`
**Header**
| Nhãn | key | Kiểu | Sheet | Ghi chú |
|---|---|---|---|---|
| Mã PO | `code` | varchar(50) | — | auto `PO#####` |
| Mã đơn MISA | `misa_code` | varchar(50) | J | nhập tay |
| Mã PYC | `pr_code` | varchar(50) | — | liên kết yêu cầu mua |
| Công ty nhận hóa đơn | `company_id` | bigint | G | dropdown |
| NCC | `supplier_code` | varchar(50) | I | dropdown (goods) |
| Pháp lý hóa đơn | `legal_entity` | varchar(100) | G | (nếu khác company) |
| Ngày đặt hàng | `order_date` | date | AD | |
| VAT (%) | `vat_rate` | decimal(5,4) | AA | |
| Trạng thái | `status` | varchar(30) | P | Nháp→Chưa đặt→Đã đặt→Đang giao→Đã nhận đủ→Hoàn thành/Hủy |
| Ghi chú | `note` | text | | |

**Item** (`tab_po_item`)
| Nhãn | key | Kiểu | Sheet |
|---|---|---|---|
| Mã SP | `product_code` | varchar(50) | L |
| Tên SP | `product_name` | varchar(255) | M |
| Phân loại | `item_group` | varchar(100) | K |
| Xuất xứ/TSKT | `spec` | varchar(255) | N |
| ĐVT | `unit` | varchar(25) | W |
| SL yêu cầu | `qty_request` | decimal(18,3) | V |
| **SL đặt NCC** | `qty_order` | decimal(18,3) | X |
| Đơn giá | `price` | decimal(18,2) | Z |
| VAT (%) | `vat` | decimal(5,2) | AA |
| Thành tiền | `amount` | decimal(18,2) | AB | auto = SL đặt×giá×(1+VAT) |

## C10.3 `tab_po_delivery` (giao nhiều lần — đủ cột Sheet 6)
| Nhãn | key | Kiểu | Sheet | Ghi chú |
|---|---|---|---|---|
| (FK) | `po_id` | bigint | — | |
| (FK dòng hàng) | `po_item_id` | bigint | — | giao cho SP nào |
| Lần giao | `delivery_no` | int | AF | 1,2,3… |
| Kho nhận | `warehouse` | varchar(100) | R | dropdown kho |
| Đơn vị vận chuyển | `carrier_code` | varchar(50) | S | NCC `supplier_type=transport` / "NCC tự VC" |
| SL gửi vận chuyển | `ship_qty` | decimal(18,3) | T | |
| ĐVT vận chuyển | `ship_unit` | varchar(25) | U | Kiện, thùng… |
| **SL đã nhận** | `received_qty` | decimal(18,3) | Y | |
| NCC cam kết giao | `promised_date` | date | D | đổi ngày = trễ |
| Ngày dự kiến nhận | `expected_date` | date | D | |
| **Ngày nhận thực tế** | `received_date` | date | E | |
| Ngày quy định | `regulated_date` | date | AI | theo Data 1 |
| Số ngày quy định | `std_days` | int | AH | theo phân loại + NCC sẵn hàng |
| Số hóa đơn | `invoice_no` | varchar(50) | AE | |
| **Đơn giá vận chuyển** | `shipping_unit_price` | decimal(18,2) | AJ | riêng |
| **Thành tiền vận chuyển** | `shipping_amount` | decimal(18,2) | AK | riêng, KHÔNG cộng giá hàng |
| CL ngày (cam kết−nhận) | `diff_promise` | int | AL | auto: <0 trễ |
| CL ngày (quy định−nhận) | `diff_regulated` | int | AM | auto: <0 Không đạt |
| Chi tiết tiến độ/ghi chú | `progress_note` | text | AG | nguyên nhân trễ |
| Trạng thái dòng giao | `status` | varchar(30) | P | Chờ giao/Đang giao/Đã nhận/Thiếu/Lỗi |

## C10.4 Backend & quy tắc
- `GET/POST/PATCH/DELETE /api/purchase-orders` + `/{id}/submit|approve` + `/{id}/print` (PDF) + `/{id}/deliveries` (CRUD lồng hoặc trong PATCH).
- Auto: `amount` item; tổng hàng = Σ amount; **tổng cước = Σ shipping_amount (riêng)**; `diff_promise/diff_regulated` tính từ ngày.
- **Vận chuyển là NCC riêng** (`supplier_type=transport`) → công nợ vận chuyển riêng (xem C12).
- Approval theo ngưỡng (`Requirement_Email_Approval` §1.3). In PO = mẫu gửi NCC.

## C10.5 Tiêu chí ĐẠT
- [ ] Tạo PO từ NCC đã duyệt + duyệt + **in PO**.
- [ ] 1 dòng hàng **giao nhiều lần** (nhiều `tab_po_delivery`), mỗi lần kho/đơn vị VC/SL nhận khác nhau.
- [ ] **Chi phí vận chuyển tách riêng**, không cộng vào giá hàng.
- [ ] Cảnh báo **trễ hạn** (diff_regulated < 0) hiển thị badge đỏ ở list.
- [ ] Trạng thái chạy đúng Nháp→…→Hoàn thành.

---

# C11. NHẬN HÀNG & KIỂM TRA — GR (Phase 2)

## C11.1 Giao diện
- Từ PO / từng lần giao → màn **Nhận hàng**: đối chiếu PO (mã/quy cách/SL), nhập **SL thực nhận** + **ngày nhận**, **kết quả QC** (Đạt/Thiếu/Lỗi) + ghi chú, **đính kèm** Phiếu giao hàng + Hóa đơn.
- Nút: Xác nhận nhận · Báo lỗi/Trả hàng · **Duyệt chứng từ nhập kho** · In phiếu nhập kho.
- Sau duyệt → **cập nhật tồn kho** (theo company/kho).

## C11.2 `tab_goods_receipt` (+ `tab_gr_item`) · `tab_inventory` (+ `tab_inventory_move`)
**goods_receipt**: `code`, `po_id`, `delivery_id`, `warehouse`, `received_date`, `qc_result`(Đạt/Thiếu/Lỗi), `qc_note`, `doc_status`(chờ/đã duyệt), `note`.
**gr_item**: `gr_id`, `product_code`, `product_name`, `qty_received`, `unit`, `qc_result`, `note`.
**inventory**: `warehouse_id`, `product_code`, `qty` (tồn hiện tại).
**inventory_move**: `warehouse_id`, `product_code`, `qty`(+/−), `ref_type`(gr/issue), `ref_id`, `created_at`.
**tolerance_rule** (đã có ở danh mục): `supplier_code`, `tolerance_pct` (±%), `check_days` (số ngày kiểm) — dùng làm **tiêu chí chấp nhận**.

## C11.3 Quy tắc
- Tiêu chí **chấp nhận**: đúng mã/quy cách + lệch SL trong `tolerance_pct` + QC đạt + trong `check_days`.
- **Thiếu** → trạng thái "Giao thiếu", theo dõi giao bù; **Lỗi** → trả/đổi (NCC chịu phí, đổi trả trong 07 ngày — theo điều khoản PO).
- **Công nợ ghi theo SL thực nhận** (không theo SL đặt).
- Nhập kho: tạo `inventory_move` (+qty) → cập nhật `inventory.qty`.

## C11.4 Tiêu chí ĐẠT
- [ ] Nhận hàng cập nhật `received_qty` + ngày nhận + QC.
- [ ] Duyệt chứng từ → **tồn kho tăng đúng** theo kho/SP.
- [ ] Xử lý thiếu/lỗi/trả (trạng thái + ghi chú).
- [ ] Đính kèm phiếu giao hàng + hóa đơn; in phiếu nhập kho.

---

# C12. CÔNG NỢ & THANH TOÁN (Phase 4)

## C12.1 Giao diện
- **Công nợ** (`/payables`): 2 tab/luồng — **Hàng** (NCC bán) và **Vận chuyển** (đơn vị VC). Cột: NCC, chứng từ (PO/đợt giao), số tiền, VAT, hạn TT, đã trả, còn lại, trạng thái. Filter theo NCC, luồng, kỳ, trạng thái.
- **Thanh toán**: nút **"Thanh toán"** ngay trên màn → chọn nhiều công nợ (gom) **hoặc** theo từng đơn → nhập số tiền + **đính kèm chứng từ** → tạo phiếu.
- Đối chiếu công nợ NCC trước **ngày 12** hằng tháng (cảnh báo email — §2.5 file Email).

## C12.2 `tab_payable` · `tab_payment` (+ `tab_payment_line`)
**payable**: `supplier_code`, `source_type`(`goods`|`shipping`), `ref_type`(po/delivery), `ref_id`, `period`(MM/YYYY), `amount`, `vat`, `due_date`, `paid_amount`, `status`(chờ/một phần/đã trả).
**payment** (header): `code`, `supplier_code`, `payment_date`, `type`(`by_order`|`by_month`), `total`, `note`, `status`.
**payment_line**: `payment_id`, `payable_id`, `amount` (nối phiếu ↔ công nợ; **1 phiếu gom nhiều công nợ**).

## C12.3 Quy tắc
- **2 luồng công nợ riêng** (`source_type`): hàng cho NCC bán; vận chuyển cho đơn vị VC — **không trộn**.
- Công nợ hàng sinh từ GR (SL thực nhận × đơn giá + VAT); công nợ VC sinh từ `tab_po_delivery.shipping_amount`.
- Thanh toán: cập nhật `paid_amount` từng payable trong `payment_line`; `status` payable đổi theo (một phần/đã trả).
- Mọi phiếu thanh toán **đính kèm chứng từ** + ghi audit.

## C12.4 Tiêu chí ĐẠT
- [ ] Công nợ hàng & vận chuyển **tách riêng**, đúng số tiền (theo thực nhận).
- [ ] 1 phiếu thanh toán **gom nhiều công nợ** (theo tháng) hoặc theo đơn.
- [ ] Nút thanh toán ngay trên màn + đính kèm chứng từ.
- [ ] Cảnh báo công nợ tới hạn (trước ngày 12).

---

## PHỤ LỤC — Thứ tự build đề xuất
1. **PO** (header+item+delivery) + in PO + duyệt → 2. **GR** + tồn kho → 3. **Công nợ** (2 luồng) + thanh toán gom.
- Tái dùng: `core/crud.py`, `core/approval.py` (transition), bảng con inline (pattern PYC/Survey), `tab_attachment`, `tab_audit_log`, danh mục (warehouse/unit/supplier).
