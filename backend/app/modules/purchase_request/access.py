"""Chốt quyền + phạm vi của YCMH dùng chung cho controller VÀ serializer (bao-CR-711).

Bốn hàm dưới đây vừa là cổng của route (duyệt / điều phối / trả về) vừa là nguồn của
các cờ `can_dispatch` / `can_approve` / `can_return` mà `serializer._out` trả kèm phiếu —
giao diện bày nút theo đúng cờ đó. Để chúng ở controller thì serializer phải import ngược
controller (vòng import), nên tách ra đây; controller nhập lại đúng các tên này.

⚠️ Luật phạm vi của từng hàm giữ NGUYÊN như khi còn ở controller — đọc docstring trước khi sửa.
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
from app.core.scoping import apply_scope

from . import service
from .model import PurchaseRequest


def _can_dispatch(profile: dict) -> bool:
    """CR-034 — ai được ĐIỀU PHỐI (duyệt lần 2). Điều kiện: có quyền `approve` trên YCMH VỚI
    phạm vi thu mua/toàn bộ ('proc'/'all'). Trưởng phòng có approve nhưng phạm vi 'dept' →
    chỉ duyệt lần 1, không điều phối. Cùng lối đọc grant với `_see_all_items`."""
    # bao-CR-414: quản lý thu mua CỦA PHÒNG (bậc `dept_proc`) cũng điều phối được — phạm vi
    # đã khoanh phiếu về đúng phòng mình ở `_in_scope`.
    for g in profile.get("grants", []):
        p = g["perms"].get("purchase_request")
        if p and p.get("approve") and p.get("scope") in ("proc", "dept_proc", "all"):
            return True
    return False


def _scope_ok(db: Session, user, pid: int, action: str) -> bool:
    """Phiếu này có nằm trong phạm vi `action` của người gọi không (chỉ hỏi, không nạp).

    Tách khỏi `_in_scope` cho những chỗ đã cầm sẵn bản ghi hoặc cần trả True/False
    (cờ `can_approve` trên phiếu, cổng trả về/từ chối).
    """
    return apply_scope(service.query_by_id(db, pid),
                       PurchaseRequest, "purchase_request", user,
                       get_perm_profile(db, user), action).first() is not None


def _in_approve_scope(db: Session, user, pid: int) -> bool:
    """Phiếu có nằm trong phạm vi DUYỆT của người này không.
    CR-034: Admin thu mua có `approve` phạm vi 'proc' (để duyệt điều phối) — phạm vi đó không
    thấy phiếu 'submitted' nên họ tự động bị loại khỏi bước duyệt 1, không cần luật riêng.

    ⚠️ Trước bản vá này hàm KHÔNG truyền `action`, tức mượn phạm vi `read`. Sai cả hai
    chiều trên cùng một dòng: cấu hình "xem toàn công ty, duyệt phòng mình" làm cổng duyệt
    rộng bằng cổng xem; còn người chỉ được tick ô "Duyệt" mà không tick ô "Xem" thì
    `scope_condition` bỏ qua mọi grant (không grant nào có `read`) và trả `false()` — cổng
    đóng với MỌI phiếu, kể cả phòng mình. Truyền đúng `action="approve"` bịt cả hai vế.
    """
    return _scope_ok(db, user, pid, "approve")


def _can_return_requester(db: Session, user, pr: PurchaseRequest) -> bool:
    """bao-CR-554 — cờ "Trả về" cho người yêu cầu (đại ca chốt 02/10/2026): quản lý (quyền Hủy)
    hoặc người duyệt (quyền Duyệt, trong phạm vi) — cả hai ở Chờ duyệt lẫn Đã duyệt / Đã điều
    phối, miễn chưa dòng nào lên ĐMH (`service.can_return_requester`). Người duyệt trước đây chỉ
    trả được ở Chờ duyệt."""
    if not service.can_return_requester(db, pr):
        return False
    if user_has_permission(db, user, "purchase_request", "cancel") and _scope_ok(db, user, pr.id, "cancel"):
        return True
    return bool(user_has_permission(db, user, "purchase_request", "approve") and _in_approve_scope(db, user, pr.id))
