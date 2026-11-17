# Mẫu thu mua khi in YCMH từ ĐMH (duoc-CR-777)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 17/11/2026 | Anh Được (NSU231) | Hiệu lực | duoc-CR-777 |

Trạng thái kế hoạch: xong

## Yêu cầu (anh Được chốt 17/11/2026)

- Màn `/print/purchase-request-from-po/:id` (v1 và v2) thêm **Mẫu thu mua – có chữ ký** và **Mẫu thu mua – không chữ ký**,
  CHỈ ở chế độ in từ ĐMH (màn in YCMH thường và nhóm Tách theo NCC không đổi).
- Người đề xuất = người đang đăng nhập; Trưởng phòng ban/bộ phận = quản lý trực tiếp (`Employee.manager_id`).
- Ô ký: *Người lập* = chữ ký người đăng nhập, *TP/BP đề xuất* = chữ ký quản lý trực tiếp; hai ô còn lại như mẫu thường.
  Mẫu không chữ ký để trống như *Mẫu thường – không chữ ký*.
- NCC do bộ phận đề xuất và bảng hàng theo **ĐMH** (SL đặt, đơn giá, VAT; bỏ dòng Hủy). Cột Thành tiền = SL × đơn giá
  (trước VAT), tiền VAT và tổng thanh toán ở dòng riêng; nơi giao / ghi chú dòng mượn từ YCMH theo mã hàng.
- Chỉ người có quyền **đọc ĐMH** và đơn nằm trong phạm vi đọc mới thấy hai mẫu.
- Thứ tự trong ô Mẫu in (khi dùng được Mẫu thu mua): Thu mua có chữ ký · Thu mua không chữ ký · Thường có chữ ký ·
  Thường không chữ ký · Thuế; mở màn là **chọn sẵn Mẫu thu mua – có chữ ký**. Không đủ quyền thì như cũ (Thường có chữ ký).

## Thiết kế

- Đường API mới `GET /api/purchase-orders/{pid}/purchasing-print` (`purchase_order/purchasing_print.py`), gác
  `require("purchase_order", "read")` + `_in_scope(..., "read")` (ngoài phạm vi 404). NCC che khi thiếu `supplier.read`.
- Giao diện gọi đường này khi in từ ĐMH và có quyền đọc; lỗi 403 / 404 thì ẩn hai mẫu, không báo lỗi.

## Kiểm

- Backend `test/backend/test_mau_in_thu_mua_cr777.py` (6 bài) + bài cũ CR-314, canh phạm vi.
- v2: typecheck, eslint, vitest `procurement/utils`, hai tệp bài kiểm màn in, `app/router`. v1: không thêm lỗi kiểu.
- Trình duyệt: PO00362 (v2), PO363 (v1) — năm mẫu khi in từ ĐMH, ba mẫu ở in YCMH thường.
