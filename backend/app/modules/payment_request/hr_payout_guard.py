"""CHỐT XEM YCTT THANH TOÁN NGHỈ PHÉP (duoc-CR-719, D1a).

YCTT sinh từ phiếu thanh toán nghỉ phép mang số tiền = lương ngày x số ngày nên KHÔNG được thấy như YCTT mua hàng.
Người xem chỉ thấy phiếu đó khi còn có `leave_encashment.read` phủ phiếu nguồn (phạm vi của chính khóa đó). Quản lý /
Nhân viên thu mua không có khóa này (nằm trong `_SYS_ENTITIES`) nên mặc định KHÔNG thấy; muốn thấy phải được tick
vai trò Kế toán / Nhân sự.

Chốt gắn vào `core.scoping.scope_condition` cho entity `payment_request` nên phủ mọi đường đọc: `apply_scope`,
`get_scoped`, danh sách người duyệt (`get_approvers_for_entity`).
"""
from sqlalchemy import or_, select

#  Giá trị `tab_payment_request.source_type` của YCTT thanh toán nghỉ phép — MỘT chỗ khai, nơi khác import.
PAYMENT_SOURCE_LEAVE_ENCASHMENT = "leave_encashment"


def payout_visibility_cond(model, user, profile: dict):
    """Điều kiện AND vào phạm vi YCTT; `None` = không cần thu hẹp thêm.

    * Phạm vi `leave_encashment` là "thấy tất cả" (`None`) → không thu hẹp;
    * không có grant (`false()`) → chỉ còn YCTT KHÔNG phải nguồn nghỉ phép;
    * còn lại → YCTT thường HOẶC YCTT nguồn nghỉ phép có phiếu nằm trong phạm vi.
    """
    from app.core.scoping import scope_condition  # nhập trong hàm: scoping gọi ngược module này
    from app.modules.leave.encashment_model import LeaveEncashment

    enc_cond = scope_condition(LeaveEncashment, "leave_encashment", user, profile, "read")
    if enc_cond is None:
        return None
    visible_ids = select(LeaveEncashment.id).where(enc_cond)
    return or_(model.source_type != PAYMENT_SOURCE_LEAVE_ENCASHMENT,
               model.source_ref_id.in_(visible_ids))
