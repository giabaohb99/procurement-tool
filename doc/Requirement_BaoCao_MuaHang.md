# Requirement chi tiết — BÁO CÁO MUA HÀNG

> Màn **Báo cáo mua hàng** (`/reports`) — 1 màn, chia **tab**; mỗi báo cáo xem theo **Kỳ** (Cả năm / từng tháng) để tránh bảng 12 cột kéo ngang. Số liệu **tính sẵn (precompute)** vào bảng snapshot → đọc nhanh; nút **Cập nhật** tính lại (gắn lịch chạy ngầm ở Phase 3).

## 1. Danh sách báo cáo (7 tab)
| Tab | Chiều nhóm (dòng) | Tháng theo | Chỉ số | Công thức đặc biệt |
|---|---|---|---|---|
| Tổng quan | — | — | KPI: số PO, giá trị đặt, công nợ (còn/quá hạn), tồn; đơn theo trạng thái; tiến độ giao; chi phí/tháng | — |
| **NCC (trễ giao)** | Nhà cung cấp | `received_date` | Số lần giao dịch · Số lần trễ · **Tỷ lệ trễ** | trễ = `diff_regulated < 0`; **đỏ khi tỷ lệ > 30%** |
| **Phân loại VTBB/NL** | `item_group` | `received_date` | Số lần mua · Tổng chi phí mua | chi phí = SL nhận × giá × (1+VAT) |
| **NSPT** | `po.nspt` | `received_date` | Số đơn · Trễ QĐ · Đúng hạn · Sớm · Tỷ lệ trễ | phân theo `diff_regulated` (<0 / =0 / >0) |
| **Bộ phận (đơn gấp)** | `po.department` | `order_date` | Số lần đặt · Số lần gấp · **Tỷ lệ gấp** | gấp = `po.is_urgent`; **đỏ khi > 30%** |
| **Chi phí vận chuyển** | `carrier` (đơn vị VC) | `received_date` | Tần suất · Giá trị đơn hàng · CP vận chuyển · **Tỷ lệ** | **Tỷ lệ = CP vận chuyển / Giá trị đơn hàng**; kèm bảng chi tiết theo đơn |
| Tồn kho | Kho / Sản phẩm | — | Giá trị tồn theo kho + top SP (đơn giá BQ gia quyền) | — |

## 2. Nguồn dữ liệu & cách tính (DB)
Bảng dùng: `tab_purchase_order` (PO), `tab_po_item` (dòng hàng), `tab_po_delivery` (lần giao/nhận), `tab_payable` (công nợ), `tab_inventory` (tồn).

Quy ước:
- **Giá trị đặt** 1 dòng = `qty_order × price × (1 + vat/100)`.
- **Giá trị nhận / chi phí mua** 1 dòng = `qty_received × price × (1 + vat/100)`.
- Báo cáo **theo lần giao** (NCC/NSPT/Phân loại/Vận chuyển): duyệt `tab_po_delivery` có `received_qty > 0`, tháng = `received_date[:7]`, join `po` (lấy nspt/supplier/department) + `po_item` (item_group/price/vat).
- Báo cáo **theo đơn đặt** (Bộ phận): duyệt `tab_purchase_order`, tháng = `order_date[:7]`.
- Chỉ số trễ dùng `po_delivery.diff_regulated` (chênh lệch ngày quy định − ngày nhận, <0 = trễ) — đã tính sẵn khi lưu PO.
- Tỷ lệ = phần / tổng × 100 (làm tròn 2 số); cảnh báo tô đỏ khi tỷ lệ > 30% (NCC trễ, Bộ phận gấp).

Pseudo (rút gọn) — xem `app/modules/report/service.py::compute`:
```
pos      = PO filter(company, order_date like year)
items    = POItem where po_id in pos
delivs   = PODelivery where po_id in pos and received_qty>0
# ma trận: {key: {m: {YYYY-MM: {metrics}}, <total metrics>, warn}}
for d in delivs:  # NCC / NSPT / phân loại / vận chuyển
    key = supplier/nspt/item_group/carrier ; month = received_date[:7]
    cộng dồn chỉ số vào cell tháng + tổng năm
for p in pos:     # bộ phận
    key = department ; month = order_date[:7] ; đếm đặt + gấp
tính tỷ lệ + cờ cảnh báo
```

## 3. Precompute (tính trước) + chạy ngầm
Vấn đề: aggregate mỗi lần mở báo cáo tốn query khi dữ liệu lớn.

Giải pháp — bảng **`tab_report_snapshot`**:
| cột | ý nghĩa |
|---|---|
| `key` | `'{year}|{company_id or all}'` (unique) |
| `data` | JSON toàn bộ báo cáo ma trận đã tính |
| `computed_at` | thời điểm tính (hiện trên UI: "Tính lúc: …") |

Luồng (`service.get_snapshot`):
1. Đọc báo cáo → nếu có snapshot theo `key` **và không refresh** → trả JSON ngay (không đụng bảng nghiệp vụ) → **rất nhanh**.
2. Chưa có snapshot **hoặc** `refresh=1` (nút **Cập nhật**) → `compute()` → ghi đè snapshot → trả kết quả.

**Chạy ngầm (Phase 3):** khi có Celery/Redis (hoặc cron), tạo job định kỳ (vd mỗi 15–30 phút hoặc cuối ngày) gọi `get_snapshot(year, company, refresh=True)` cho các kỳ hay dùng → người dùng luôn thấy số mới mà không phải bấm. Trước mắt: bấm **Cập nhật** thủ công.

**Lưu ý staleness:** snapshot KHÔNG tự đổi khi PO/giao hàng thay đổi → cần bấm **Cập nhật** (hoặc chờ job). UI luôn hiển thị `computed_at` để biết độ mới.

### 3b. Chiến lược hiệu năng (index / precompute / partition — theo quy mô)
Không cần tối ưu quá sớm. Áp dụng theo 3 tầng, tăng dần theo lượng dữ liệu:
1. **Index cột lọc/gom** (đang dùng): `payable.incur_date/period/status/supplier_code`, `purchase_order.order_date/status/supplier_code`, `po_delivery.received_date/po_id`. → query lọc theo tháng/NCC rất nhanh, không cần quét toàn bảng.
2. **Precompute snapshot** (đang dùng): báo cáo ma trận tháng (nặng) tính sẵn 1 lần, đọc lại tức thì. Drill-down theo ngày = query nhẹ on-demand (lọc 1 tháng).
3. **Partition bảng** — CHƯA cần. Chỉ cân nhắc khi bảng (payable/po_delivery) lên **hàng triệu dòng**: partition theo `YEAR(incur_date)` để mỗi truy vấn chỉ đụng 1 phân vùng. Với quy mô ~20 user, index + snapshot đã đủ; partition thêm phức tạp vận hành.

Tóm: **index + snapshot** giải quyết 99% nhu cầu hiện tại; partition để dành cho tương lai khi dữ liệu thực sự lớn.

## 4. API
```
GET /api/reports/procurement?year=&company_id=   -> KPI tổng quan + tồn (tính trực tiếp, nhẹ)
GET /api/reports/matrix?year=&company_id=&refresh=0|1  -> 5 báo cáo ma trận (đọc snapshot; refresh=1 tính lại)
```
Quyền: cả 2 yêu cầu `require("report","read")`.

## 5. UI/UX
- 1 màn `/reports`, tab: Tổng quan · NCC · Phân loại · NSPT · Bộ phận · Vận chuyển · Tồn kho.
- **Bộ chọn Kỳ** (Cả năm / từng tháng) cho các tab ma trận → bảng gọn (đối tượng × chỉ số), không kéo ngang 12 cột.
- Lọc chung: **Năm + Công ty**. Nút **Cập nhật** (tính lại) · **In** (ẩn sidebar/topbar khi in).
- Cảnh báo tô đỏ dòng khi tỷ lệ > 30%.

## 6. Mở rộng sau
- Lịch tự refresh snapshot (Phase 3 worker).
- Xuất Excel/PDF từng báo cáo.
- Thêm chiều lọc (theo nhóm hàng, theo kho) nếu cần.
