"""Đếm phiếu CHỜ DUYỆT cho bóng đỏ trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Một khóa cho mỗi mục menu có bước duyệt: Yêu cầu báo giá · Yêu cầu mua hàng · Đơn mua hàng · Phiếu khảo
sát. "Chờ duyệt" = trạng thái `submitted`, đếm trong PHẠM VI dữ liệu của người xem (`apply_scope`) — đúng
cách thẻ thống kê Trang chủ đếm, nên số trên menu và số trên thẻ luôn khớp nhau.
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


def count_pending_by_menu(db: Session, user) -> dict[str, int]:
    """Đếm phiếu chờ duyệt theo từng mục menu; bỏ hẳn khóa người xem không có quyền đọc."""
    profile = get_perm_profile(db, user)
    counts: dict[str, int] = {}
    for entity, model in MENU_MODELS.items():
        if not profile["perms_union"].get(entity, {}).get("read"):
            continue
        query = apply_scope(db.query(model), model, entity, user, profile)
        counts[entity] = query.filter(model.status == PENDING_STATUS).count()
    return counts
