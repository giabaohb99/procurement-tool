"""ai-CR-190 — chỗ tham chiếu tới TÀI KHOẢN (người dùng) cho sổ `core/reference_guard`.

Ở hệ này gần như mọi chứng từ trỏ tới NHÂN SỰ (`employee_id`), tài khoản chỉ được trỏ ở vài chỗ mang nghĩa "tài khoản
đang xử lý / đang liên kết". KHÔNG khai (cố ý):
- `tab_user_role`, `tab_user_scope`, thông báo, đăng ký đẩy, phiên đăng nhập: thuộc chính tài khoản, `delete_user`
  xóa cứng kèm (phiên đăng nhập là "Giả định": xóa kèm chứ không chặn — phiên là vé, không phải dữ liệu nghiệp vụ).
- `created_by` / `updated_by` / `approved_by` / bình luận / cảm xúc / nhật ký yêu cầu / tùy chọn cá nhân / bộ lọc đã lưu:
  nhật ký, bộ đệm — `delete_user` đã có chốt riêng "tài khoản đã tạo dữ liệu" (`user_data_refs`), giữ nguyên.
- Bảng `tab_agent_*` của bot (liên kết chat, cấp quyền bot, sổ ghi nhớ…): ở dev/prod bot chạy `AGENT_MODE=service` với
  DB RIÊNG, phía ERP không có bảng đó để đếm — bỏ qua, ghi ở doc/erp/20 §4.
Tệp này được `user/service.py` import lúc khởi động.
"""
from app.core import reference_guard as rg
from app.modules.ticket.model import Ticket
from app.modules.vehicle_booking.model import Driver

ENTITY = "user"

rg.register(ENTITY, "Tài khoản", [
    rg.Reference(Ticket, "assignee_id", "phiếu hỗ trợ đang xử lý"),
    rg.Reference(Driver, "user_id", "tài xế liên kết"),
])
