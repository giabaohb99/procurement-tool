# Dashboard — Bản mô tả chức năng cho UX/UI (handoff)

> Tài liệu bàn giao cho người thiết kế UX/UI. Liệt kê **mọi khối** trên trang chủ (Dashboard), nội dung, tương tác, trạng thái và **dữ liệu có sẵn**. Người thiết kế có thể vẽ lại tự do — miễn giữ đúng các trường dữ liệu ở phần "Dữ liệu API".

Route: `/` · File: `frontend/src/pages/Dashboard.tsx` · Dữ liệu: 1 request `GET /api/dashboard/overview`.

---

## 1. Nền tảng thương hiệu (bắt buộc giữ)

| Hạng mục | Giá trị |
|---|---|
| Màu nhấn chính | Xanh biển `#00AEEF` (logo DEGO) |
| Màu phụ / tích cực | Xanh lá `#92C83E` |
| Chữ tiêu đề (navy) | `#1B2559` |
| Chữ phụ / nhãn | `#A3AED0` |
| Nền trang | `#F4F7FE` |
| Nền thẻ | `#FFFFFF` · bo góc `20px` · bóng mềm `0 18px 40px rgba(112,144,176,.12)` |
| Cảnh báo | vàng `#D97706` · cam `#EA580C` · đỏ `#E24B4A` |
| Font | DM Sans (fallback Inter) |
| Logo | `frontend/public/logo.svg` |

---

## 2. Bố cục tổng thể

```
Topbar (breadcrumb · chuông · avatar · đăng xuất)   ← khung chung, không thuộc dashboard
────────────────────────────────────────────────
[ Header: lời chào + tên + "Số liệu năm N" + số cảnh báo ]
[ 8 thẻ KPI · lưới 4 cột × 2 hàng ]
[ Chi phí theo tháng (rộng 1.7) | Cơ cấu phân loại (1) ]
[ Trạng thái đơn hàng (1) | Tuổi nợ (1) ]
[ Top NCC (1) | Chi tiêu bộ phận (1) ]
[ Cảnh báo cần xử lý (1) | Tồn kho thấp (1) ]
[ Đơn hàng gần đây (full width) ]
```
Lưới: khoảng cách 16–20px. Desktop 4 cột KPI; tablet 2 cột; điện thoại 1 cột. Các thẻ cùng hàng nên **cùng chiều cao**.

---

## 3. Danh sách chi tiết từng khối

### 3.1 Header
- **Nội dung:** dòng nhỏ "Chào mừng trở lại"; tên người dùng (26px đậm); bên phải "Số liệu năm {year}" + (nếu có) "🔔 {n} cảnh báo" màu đỏ.
- **Tương tác:** không.

### 3.2 Thẻ KPI (8 thẻ)
- **Cấu trúc 1 thẻ:** chip icon tròn (nền màu nhạt + icon màu) · nhãn nhỏ xám · số lớn navy đậm.
- **Tương tác:** bấm cả thẻ → điều hướng.
- **Danh sách 8 thẻ:**

| # | Nhãn | Giá trị | Icon | Màu | Bấm đến |
|---|---|---|---|---|---|
| 1 | Đơn chờ duyệt | số | file-alert | vàng | /purchase-requests?status=submitted |
| 2 | PO đang chạy | số | shopping-cart | xanh biển | /purchase-orders |
| 3 | Giao trễ | số | truck-return | cam | /purchase-orders |
| 4 | Khảo sát chờ | số | clipboard-check | tím | /surveys-supplier |
| 5 | Nợ đến hạn (7n) | tiền | cash | teal | /payables |
| 6 | Nợ quá hạn | tiền | alert-triangle | đỏ | /payables |
| 7 | HĐ sắp hết hạn | số | file-certificate | xanh lá | /contracts |
| 8 | Giá trị tồn kho | tiền | building-warehouse | xanh biển đậm | /inventory |

### 3.3 Chi phí mua hàng theo tháng — **biểu đồ cột**
- **Nội dung:** 12 cột (T1–T12) giá trị nhận hàng của năm gần nhất có dữ liệu; trục Y hiển thị mốc tiền; **nhãn số trên đầu cột** có dữ liệu.
- **Tương tác:** hover cột → hiện số tiền đầy đủ (tooltip).
- **Ghi chú thiết kế:** chiều cao cố định (~240px) để không lệch với thẻ bên cạnh.

### 3.4 Cơ cấu theo phân loại — **biểu đồ tròn (donut)**
- **Nội dung:** tỉ trọng chi tiêu theo nhóm hàng (Nguyên liệu, Thùng…), tối đa 4 nhóm + "Khác"; chú thích bên phải: chấm màu · tên · **%**.

### 3.5 Trạng thái đơn hàng — **biểu đồ tròn (donut)**
- **Nội dung:** số đơn theo trạng thái (Nháp/Chờ duyệt/Đã duyệt/Giao 1 phần/Đã nhận/Hoàn thành/Đã hủy); chú thích: màu · tên trạng thái · **số đơn**. Chỉ hiện trạng thái có đơn.

### 3.6 Tuổi nợ (còn phải trả) — **thanh ngang**
- **Nội dung:** 4 mức: Chưa đến hạn · 1–30 ngày · 31–60 ngày · > 60 ngày; mỗi mức 1 thanh + số tiền. Màu: xanh lá → vàng → cam → đỏ.

### 3.7 Top nhà cung cấp theo giá trị — **thanh ngang**
- **Nội dung:** 5 NCC chi nhiều nhất; mỗi dòng tên + số tiền + thanh tỉ lệ (xanh biển).

### 3.8 Chi tiêu theo bộ phận — **thanh ngang**
- **Nội dung:** giá trị mua theo phòng ban; mỗi dòng tên + số tiền + thanh.

### 3.9 Cảnh báo cần xử lý — **danh sách**
- **Nội dung:** tối đa 6 dòng: chấm màu (đỏ=nguy hiểm, vàng=cảnh báo) + nội dung (nợ quá hạn / HĐ sắp hết hạn / giao trễ…).
- **Tương tác:** bấm dòng → tới màn liên quan.

### 3.10 Tồn kho thấp / sắp hết — **bảng mini**
- **Cột:** Sản phẩm · Kho · Tồn (kèm ĐVT). Dòng tồn ≤ 0 **tô nền đỏ nhạt**, số đỏ.

### 3.11 Đơn hàng gần đây — **bảng đầy đủ**
- **Cột:** Mã đơn (màu nhấn) · Nhà cung cấp · Ngày đặt · Trạng thái (badge màu) · Giá trị (phải).
- **Tương tác:** bấm dòng → mở chi tiết đơn.

---

## 4. Trạng thái chung (mọi khối)
- **Đang tải:** có thể hiện khung xám (skeleton) — hiện tại để trống tới khi có dữ liệu.
- **Rỗng:** hiển thị dòng chữ xám "Chưa có dữ liệu".
- **Số tiền:** rút gọn (k / tr / tỷ) trên thẻ và trục; đầy đủ "đ" khi hover / trong bảng.

---

## 5. Dữ liệu API (hợp đồng dữ liệu — người thiết kế đọc để biết có gì)

`GET /api/dashboard/overview` → `data`:
```jsonc
{
  "year": "2026",
  "kpi": {
    "pr_pending": 0, "po_ordered": 2, "late_deliveries": 0, "survey_pending": 0,
    "due_soon": 0, "overdue": 18980000, "contract_expiring": 1,
    "inv_value": 17500000, "out_of_stock": 0
  },
  "cost_12m":    [{ "label": "T1", "value": 0 }, ... 12 phần tử ],
  "categories":  [{ "name": "Thùng", "cost": 10800000, "pct": 57.1 }, ...],   // tối đa 4 + "Khác"
  "top_suppliers":[{ "name": "...", "value": 10800000 }, ...],                 // 5
  "dept_spend":  [{ "name": "Sản xuất", "value": 10800000 }, ...],            // 5
  "po_status":   [{ "key": "partial", "label": "Giao 1 phần", "value": 1 }, ...],
  "ap_aging":    [{ "label": "Chưa đến hạn", "value": 0 }, { "label": "1–30 ngày", "value": 18980000 }, ...],
  "recent_pos":  [{ "id": 2, "code": "PO00002", "supplier": "...", "order_date": "2026-06-20", "status": "partial", "total": 8100000 }, ...], // 8
  "low_stock":   [{ "product_code": "NL0001", "product_name": "...", "qty": 500, "unit": "Kg", "warehouse_code": "ADU" }, ...], // 8
  "alerts":      [{ "type": "payable", "level": "danger", "title": "...", "link": "/payables" }, ...], // 6
  "alert_total": 5
}
```

> **Muốn thêm chỉ số mới** (vd: tỉ lệ giao đúng hạn, chi tiêu theo NSPT, biểu đồ theo quý…): báo team backend bổ sung field vào endpoint này; UI chỉ cần đọc thêm.

---

## 6. Dựng lại từ ảnh thiết kế
Khi có bản thiết kế (ảnh/Figma), gửi kèm càng tốt:
- Ảnh tổng thể + thứ tự các khối.
- Mã màu, cỡ chữ, bo góc (nếu có).
- Khối nào giữ/bỏ so với danh sách trên, khối nào thêm mới.

Đội dev sẽ dựng lại đúng bố cục/màu; nếu khối mới cần dữ liệu chưa có, sẽ bổ sung vào `GET /api/dashboard/overview`.
