# NHẬT KÝ THAY ĐỔI & YÊU CẦU THAY ĐỔI (Change Log / CR)

## Mini Tool Quản lý Thu Mua — DEGO Holding

Ghi lại **AI đổi gì, khi nào, ảnh hưởng ra sao** (theo [quy-trinh-tai-lieu.md](quy-trinh-tai-lieu.md) §⑥). Mọi thay đổi cấu trúc/luồng phải có 1 dòng CR ở đây.

**Trạng thái:** `Đề xuất` → `Đã duyệt` → `Đang làm` → `Hoàn tất` (hoặc `Từ chối` / `Hoãn`).

---

| CR | Ngày | Người đề xuất | Nội dung | Ảnh hưởng scope | Trạng thái | Tài liệu liên quan |
|---|---|---|---|---|---|---|
| **CR-001** | 2026-07-13 | Khách (phòng TM) | **Redesign phân hệ Kho**: thêm `company_id` (kho nội bộ) + `supplier_code` (kho đối tác) + `warehouse_type`; phân loại & redesign UI. **Giữ nguyên mã kho cũ** (không đụng tồn kho/PO/PYC). | Trung bình — thêm 3 cột `tab_warehouse` + migration phân loại; đổi UI danh mục Kho. Không ảnh hưởng tham chiếu string hiện có. | `Đề xuất` (chờ duyệt) | [tdd-redesign-kho.md](tdd-redesign-kho.md) |

---

## Quyết định đã chốt (Decision log)

| # | Ngày | Quyết định | Lý do |
|---|---|---|---|
| D-001 | 2026-07-13 | Kho: **giữ nguyên mã cũ**, không chuẩn hóa mã hàng loạt đợt này | Mã kho là khóa ngoại dạng chuỗi ở tồn kho/GR/PO/PYC → đổi mã dễ làm mồ côi dữ liệu. Chuẩn hóa mã cũ (nếu cần) tách thành CR riêng kèm migration ánh xạ toàn bảng. |
| D-002 | 2026-07-13 | Chủ sở hữu kho: **nội bộ → `company_id`**, **đối tác → `supplier_code`** | Kho đối tác (An Nông, Agama…) thuộc NCC bên ngoài, không phải công ty tập đoàn → link NCC mới đúng bản chất, tránh trùng danh mục NCC. |
