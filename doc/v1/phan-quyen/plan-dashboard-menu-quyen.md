# Plan: Quyền → Menu → Dashboard (home)

## Nguyên tắc
- **Menu**: mục hiện nếu có quyền **Xem** entity đó (đã làm, tự ẩn).
- **Dashboard**: mỗi khối chỉ hiện nếu có quyền **Xem** entity tương ứng; **số liệu tính trong phạm vi** của user (own/dept/company/all + được giao). Endpoint `/api/dashboard/overview` trả kèm `can` để FE ẩn thẻ.

## Khối Dashboard → cần quyền Xem
| Khối | Entity | Ghi chú |
|---|---|---|
| KPI Tổng chi tiêu · Chi phí theo tháng · Cơ cấu phân loại · Top NCC · Chi tiêu bộ phận · Trạng thái đơn · Đơn hàng hoạt động (PO) | **purchase_order** | số theo phạm vi PO của user |
| KPI Yêu cầu chờ duyệt · Yêu cầu mua gần đây | **purchase_request** | theo phạm vi PYC (own/dept/company/all/được giao) |
| KPI Công nợ quá hạn · Tuổi nợ | **payable** | |
| KPI HĐ sắp hết hạn | **contract** | |
| KPI Tồn / Tồn thấp | **inventory** | |
| Khảo sát chờ | **survey** | |
| Cảnh báo cần xử lý | payable / contract / purchase_order | chỉ hiện mục thuộc quyền mình |

## Home page theo vai trò (ví dụ)
| Vai trò | Menu chính | Dashboard thấy gì |
|---|---|---|
| **Nhân sự** | Trang chủ · Yêu cầu mua (+ vài danh mục cần cho form) | Chỉ **KPI Yêu cầu chờ duyệt (của mình)** + **Yêu cầu mua gần đây (của mình)**. Không thấy chi tiêu/PO/công nợ/tồn. |
| **Nhân viên thu mua** | + Khảo sát · Đơn mua hàng · Tồn kho · Công nợ · Thanh toán | PYC (được giao) · PO/chi phí/cơ cấu (phạm vi phòng) · tồn/công nợ (phạm vi công ty) |
| **Trưởng phòng** | Trang chủ · Yêu cầu mua · Báo cáo | PYC + báo cáo theo **phòng ban** của mình |
| **Quản lý / Admin thu mua** | Đầy đủ mua hàng | Toàn bộ dashboard, phạm vi tất cả |
| **Admin hệ thống** | Tất cả | Toàn bộ |

## Đã siết vai trò Nhân sự
- Bỏ read **Hợp đồng** + **Nhà cung cấp** → không còn KPI "HĐ sắp hết hạn" và menu Hợp đồng/NCC.
- Giữ read **Sản phẩm · ĐVT · Phân loại · Kho · Phòng ban** vì **form Tạo yêu cầu cần** để chọn.

## Điểm cần chốt (menu vs quyền-đọc)
Form Tạo yêu cầu cần đọc danh mục (Sản phẩm/ĐVT/Phân loại/Kho) → các mục này **hiện trong menu Danh mục** của Nhân sự.
- **Phương án A (đơn giản, đang dùng):** chấp nhận Nhân sự thấy vài mục Danh mục trong menu (chỉ xem, không sửa).
- **Phương án B:** tách "hiện trên menu" khỏi "quyền đọc" → Nhân sự đọc được danh mục cho form nhưng **ẩn khỏi menu**. Cần thêm cấu hình menu riêng.
→ Anh chọn A hay B?
