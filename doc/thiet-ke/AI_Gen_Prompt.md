# Prompt gen UI cho AI (v0 / Lovable / Bolt / Claude)

Có 2 bản. Bản A ghim brand (ra sát app hiện tại). Bản B chỉ mô tả chức năng (AI tự do thiết kế,
mỗi lần ra một kiểu — tránh rập khuôn).

---

## Bản A — có brand (ra giống app đang chạy)

```text
Build a Vietnamese procurement dashboard (React + TS), Horizon UI style: clean, white rounded
cards (radius 20, soft shadow) on #F4F7FE, one accent #00AEEF, success #92C83E, navy text #1B2559,
muted #A3AED0, font DM Sans, no gradients, no emoji, money as k/tr/tỷ.

Sidebar (dark #0f172a) + DEGO logo + grouped menu; white topbar (breadcrumb, bell, avatar, Đăng xuất).

Dashboard: 8 KPI cards (4x2, icon+label+number): Đơn chờ duyệt, PO đang chạy, Giao trễ,
Khảo sát chờ, Nợ đến hạn(7n), Nợ quá hạn, HĐ sắp hết hạn, Giá trị tồn kho.
Then equal-height 2-col rows:
- Chi phí mua theo tháng (bar 12 tháng, h~240) | Cơ cấu phân loại (donut %)
- Trạng thái đơn hàng (donut) | Tuổi nợ (bars: chưa/1-30/31-60/>60, green→red)
- Top NCC (bars) | Chi tiêu bộ phận (bars)
- Cảnh báo cần xử lý (list, chấm màu, clickable) | Tồn kho thấp (table, qty<=0 đỏ)
- Đơn hàng gần đây (full table: mã/NCC/ngày/trạng thái badge/giá trị)
Responsive: sidebar→drawer mobile. Mock data, empty state "Chưa có dữ liệu".
```

---

## Bản B — chỉ chức năng (AI tự do màu/bố cục)

```text
Design an internal Procurement Management dashboard, Vietnamese UI. You choose the visual style,
colors, layout and chart types — make it modern, clean, easy to scan; be creative, don't follow a
fixed template. Charts clear and proportional. Responsive (sidebar → drawer on mobile). Use realistic
Vietnamese mock data, money in đ (k/tr/tỷ), no emoji.

Sidebar nav: Trang chủ, Báo cáo mua hàng, Yêu cầu mua, Khảo sát NCC, Khảo sát SP, Đơn mua hàng,
Tồn kho, Công nợ, Yêu cầu thanh toán, Nhà cung cấp, Sản phẩm, Hợp đồng, Kho, Đơn vị tính, Phân loại,
Phòng ban, Công ty, Nhân sự, Vai trò. Topbar: breadcrumb, thông báo, avatar, đăng xuất.

Dashboard must surface (pick the best visualization for each):
- KPIs: đơn chờ duyệt, PO đang chạy, giao trễ, khảo sát chờ, nợ đến hạn (7n), nợ quá hạn,
  HĐ sắp hết hạn, giá trị tồn kho, mặt hàng hết.
- Chi phí mua hàng theo tháng.
- Cơ cấu chi tiêu theo phân loại hàng.
- Trạng thái đơn hàng (Nháp/Chờ duyệt/Đã duyệt/Giao 1 phần/Đã nhận/Hoàn thành/Hủy).
- Tuổi nợ phải trả (chưa đến hạn / 1-30 / 31-60 / >60 ngày).
- Top nhà cung cấp theo giá trị; chi tiêu theo bộ phận.
- Cảnh báo cần xử lý (nợ quá hạn, HĐ sắp hết hạn, giao trễ), click để mở.
- Tồn kho thấp/sắp hết; đơn hàng gần đây (mã, NCC, ngày, trạng thái, giá trị).
```

Muốn hướng nhẹ mà vẫn thoáng: thêm 1 dòng như "tông xanh biển + xanh lá theo logo" hoặc
"style tối giản kiểu SaaS hiện đại".
