"""Đếm phiếu CHỜ MÌNH DUYỆT cho bóng đỏ trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Một khóa cho mỗi mục menu có bước duyệt: Yêu cầu báo giá · Yêu cầu mua hàng · Đơn mua hàng · Phiếu khảo
sát. "Chờ duyệt" = trạng thái `submitted`. Người không có quyền `approve` trên entity thì bỏ hẳn khóa.

duoc-CR-723 lượt f (anh Được chốt 09/11/2026): YCBG · YCMH · ĐMH đếm phiếu Chờ duyệt mà ô **Trưởng phòng
phê duyệt** (`approver_employee_id`, bao-CR-499) là CHÍNH nhân sự của tài khoản đang đăng nhập. Ô này lúc
chưa duyệt giữ người được chọn (mặc định TBP); phiếu cũ để trống (0) thì không đếm cho ai. Tài khoản không
gắn nhân sự thì ba mục này luôn 0. Vẫn lọc thêm phạm vi DUYỆT (`apply_scope(..., "approve")`) để người
được chọn nhưng không bấm Duyệt được thì không thấy số ảo. Bỏ phần đếm phiếu chờ duyệt điều phối của
lượt e (chỉ đếm Chờ duyệt).

Phiếu khảo sát không có ô Trưởng phòng phê duyệt nên giữ cách đếm của lượt e: quyền `approve` + phạm vi
duyệt.

Thẻ thống kê "Đơn mua hàng chờ duyệt" ở Trang chủ vẫn đếm theo phạm vi XEM: đó là số liệu, không phải việc
cần làm, nên hai số không nhất thiết khớp.
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey.model import Survey
from app.modules.survey_request.model import SurveyRequest

PENDING_STATUS = "submitted"

#  Khóa trả về = khóa quyền (entity) của mục menu, để giao diện tra thẳng theo `entity` của mục đó.
MENU_MODELS = {
    "survey_request": SurveyRequest,
    "purchase_request": PurchaseRequest,
    "purchase_order": PurchaseOrder,
    "survey": Survey,
}

#  Chứng từ có ô "Trưởng phòng phê duyệt" (`approver_employee_id`) — đếm theo người được chọn ở ô đó.
APPROVER_FIELD_ENTITIES = {"survey_request", "purchase_request", "purchase_order"}


def count_pending_by_menu(db: Session, user) -> dict[str, int]:
    """Đếm phiếu Chờ duyệt đang chờ người xem duyệt theo từng mục menu.

    Thiếu quyền duyệt thì bỏ hẳn khóa (giao diện không vẽ bóng). Phạm vi lấy theo hành động `approve`.
    """
    profile = get_perm_profile(db, user)
    my_employee_id = int(getattr(user, "employee_id", 0) or 0)
    counts: dict[str, int] = {}
    for entity, model in MENU_MODELS.items():
        if not profile["perms_union"].get(entity, {}).get("approve"):
            continue
        if entity in APPROVER_FIELD_ENTITIES and not my_employee_id:
            counts[entity] = 0
            continue
        query = apply_scope(db.query(model), model, entity, user, profile, "approve")
        query = query.filter(model.status == PENDING_STATUS)
        if entity in APPROVER_FIELD_ENTITIES:
            query = query.filter(model.approver_employee_id == my_employee_id)
        counts[entity] = query.count()
    return counts
