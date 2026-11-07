"""Đếm phiếu CHỜ MÌNH DUYỆT cho bóng đỏ trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Một khóa cho mỗi mục menu có bước duyệt: Yêu cầu báo giá · Yêu cầu mua hàng · Đơn mua hàng · Phiếu khảo
sát. "Chờ duyệt" = trạng thái `submitted`.

duoc-CR-723 lượt e (anh Được chốt 07/11/2026): bóng là việc CỦA NGƯỜI XEM — chỉ đếm phiếu người đó bấm
Duyệt được: có quyền `approve` trên entity và phiếu nằm trong phạm vi DUYỆT (`apply_scope(..., "approve")`),
đúng cổng của đường `POST /{id}/approve` ở cả bốn phân hệ. Trước đó bóng đếm theo quyền + phạm vi XEM nên
admin thấy toàn bộ phiếu chờ duyệt của hệ, người chỉ xem cũng có bóng cho phiếu mình không duyệt được.

YCMH có thêm bước DUYỆT ĐIỀU PHỐI (CR-034): phiếu `approved` chờ quản lý thu mua. Người điều phối được
(`_can_dispatch`) và công tắc bước này đang BẬT thì đếm cả những phiếu đó, cùng phạm vi duyệt — nếu không
quản lý thu mua luôn thấy 0 dù đang có phiếu chờ họ.

Thẻ thống kê "Đơn mua hàng chờ duyệt" ở Trang chủ vẫn đếm theo phạm vi XEM: đó là số liệu, không phải việc
cần làm, nên hai số chỉ khớp khi phạm vi xem = phạm vi duyệt.
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.access import _can_dispatch
from app.modules.purchase_request.dispatch_service import dispatch_enabled
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey.model import Survey
from app.modules.survey_request.model import SurveyRequest

PENDING_STATUS = "submitted"
#  YCMH đã qua bước duyệt 1, chờ quản lý thu mua duyệt điều phối.
PR_AWAITING_DISPATCH_STATUS = "approved"

#  Khóa trả về = khóa quyền (entity) của mục menu, để giao diện tra thẳng theo `entity` của mục đó.
MENU_MODELS = {
    "survey_request": SurveyRequest,
    "purchase_request": PurchaseRequest,
    "purchase_order": PurchaseOrder,
    "survey": Survey,
}


def count_pending_by_menu(db: Session, user) -> dict[str, int]:
    """Đếm phiếu chờ người xem duyệt theo từng mục menu.

    Thiếu quyền duyệt thì bỏ hẳn khóa (giao diện không vẽ bóng). Phạm vi lấy theo hành động `approve`.
    """
    profile = get_perm_profile(db, user)
    counts: dict[str, int] = {}
    for entity, model in MENU_MODELS.items():
        if not profile["perms_union"].get(entity, {}).get("approve"):
            continue
        statuses = [PENDING_STATUS]
        if entity == "purchase_request" and dispatch_enabled() and _can_dispatch(profile):
            statuses.append(PR_AWAITING_DISPATCH_STATUS)
        query = apply_scope(db.query(model), model, entity, user, profile, "approve")
        counts[entity] = query.filter(or_(*(model.status == status for status in statuses))).count()
    return counts
