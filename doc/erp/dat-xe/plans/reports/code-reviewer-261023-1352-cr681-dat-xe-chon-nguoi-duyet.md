# Review duoc-CR-681 — Đặt xe chọn Công ty + Người duyệt

Agent rà không ghi được tệp → bản tóm tắt do phiên chính ghi lại kèm cách xử lý.

| Mã | Phát hiện | Xử lý |
|---|---|---|
| H1 | Đường cũ (bộ máy tắt / không luồng khớp): thư chỉ tới người được chọn nhưng họ ngoài phạm vi → GET 404, Duyệt 404 | `approval_bridge.is_picked_legacy_approver` + nới `booking_for_approver` (đọc) và `_scoped_or_404(..., "approve")` (duyệt/trả/từ chối) khi phiếu Chờ duyệt, đúng người được chọn, không phiên nhiều bước đang chạy. Ép tải B2: 60/60 mở + duyệt được |
| H2 | Công ty chọn tự do quyết định luồng + ai thấy phiếu | GIỮ — anh Được chốt hai ô độc lập, phiếu thuộc công ty được chọn. Ghi rõ ở HDSD + tài liệu |
| M1 | Hồ sơ nghỉ việc (tài khoản còn mở) qua được chốt → bước rỗng | `permission_approvers.holders` join `Employee.is_active` |
| M2 | Tự chọn so theo tài khoản, không theo hồ sơ; người sửa hộ tự chọn mình rồi gửi | `check_approver` so hồ sơ nhân sự, với cả người tạo lẫn người bấm gửi |
| M3 | Thư bộ máy chỉ chặng đầu; câu gợi ý sai với luồng không có bước cách 9 | Câu gợi ý sửa; thư chặng sau / người được ủy quyền — để sau (đã ghi) |
| M4 | Lưu nháp bị chặn vì giao diện luôn gửi lại người duyệt | Chỉ kiểm khi đổi người hoặc khi gửi |
| L | Danh sách có chính mình · tên người duyệt lấy nhầm người đã ký · lỗi tải bị giấu · pick-options chỉ `create` · đồng bộ app cũ chèn `code=""` | Bỏ chính mình khỏi danh sách · `first_approver_name` · báo lỗi tải · mở cho `create` HOẶC `write` · đồng bộ app cũ chèn mã tạm |

Mã DX: thăm dò MySQL của agent xác nhận cửa xoay đúng; bảng rỗng (phiếu đầu tiên) chưa có cửa — chấp nhận.

Câu hỏi còn treo: bộ máy duyệt Đặt xe trên prod đang bật hay tắt? App đặt xe cũ có định tuyến theo `firstApproverUid` đồng bộ ngược không?

## Lượt 2 (24/10/2026) — công ty hai bên + thư mọi chặng

| Mã | Phát hiện | Xử lý |
|---|---|---|
| H1 | `email_queue` nghe `after_commit`/`after_rollback` — SQLAlchemy 2.0.35 phát cả khi nhả / hủy SAVEPOINT → đẩy thư trước commit ngoài, hoặc xóa nhầm cả hàng | Dò thật: trong sự kiện `in_transaction()` luôn True, `in_nested_transaction()` True = savepoint → bỏ qua sự kiện savepoint. Có 2 bài kiểm savepoint |
| M2 | Bậc «Phòng ban» chỉ so `company_id` | OR thêm `company_alt` ở nhánh `dept`, có bài kiểm |
| M3 | Tiêu đề thư > 255 (mẫu sửa thêm `{{ purpose }}`) → flush hỏng → cả lượt duyệt 500 | Cắt tiêu đề / địa chỉ về 255, có bài kiểm phiếu mục đích 600 ký tự |
| M4 | Đồng bộ app cũ ghi đè `requester_company_id` | Thêm vào `LEGACY_READONLY_FIELDS` |
| L6 | «Loại trừ công ty» chỉ so cột chính | GIỮ — ghi chú lý do ở `_explicit_cond` |
| L7 | Bộ lọc báo cáo / nhóm theo công ty ở tổng quan chỉ dùng `company_id` | GIỮ — báo cáo đếm theo công ty CHỌN trên phiếu; ghi vào câu hỏi treo |
| L8 | Trùng thư khi hai tài khoản chung hộp thư | Chống trùng theo địa chỉ |
| L11 | Docstring seed HDSD nhắc hàm đã bỏ | Sửa |
| L12 | Nhánh `own` của đặt xe so `requester_id` (id tài khoản) với `employee_id` | NGOÀI phạm vi CR này — có từ trước, ghi lại để xử lý riêng |
