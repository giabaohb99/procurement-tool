"""CHỐNG TỰ NÂNG QUYỀN — hai luật, áp cho mọi cửa ghi phân quyền.

Màn *Phân quyền tài khoản* là cửa duy nhất trong hệ mà thao tác của người dùng
quyết định chính quyền hạn của người dùng. Trước 25/08/2026 nó không có chốt nào,
nên **bất kỳ ai có `user.write` đều tự phong mình làm quản trị hệ thống trong một
lần bấm**: mở trang của chính mình, tick «Quản trị hệ thống», bấm *Lưu vai trò*.
Dựng lại được qua API — sau cú bấm đó `/api/auth/me` trả hồ sơ quyền đủ **42/42**
entity. Cùng lỗ đó còn ba lối vào khác: gán admin cho người khác rồi nhờ họ gán
ngược lại · tick full ma trận của chính vai trò mình đang giữ (`role.write`) ·
tự nới phạm vi dữ liệu của mình.

Hai luật ở đây, cố ý viết ngắn để đọc là hiểu:

**L1 — KHÔNG TỰ SỬA QUYỀN CỦA CHÍNH MÌNH.** Người làm phân quyền vẫn phải nhờ
người khác đổi quyền của họ. Đây là chốt bốn mắt tiêu chuẩn, và nó chặn đứng cả
ba lối tự nâng ở trên mà không cần biết vai trò nào "cao" hơn vai trò nào — hệ
này không có khái niệm cấp bậc vai trò, nên mọi cách xếp hạng đều là bịa ra.

**L2 — KHÔNG CẤP THỨ MÌNH KHÔNG CÓ.** Gán một vai trò cho người khác, hoặc tick
thêm ô vào ma trận của một vai trò, thì mọi `(entity × action)` đụng tới phải nằm
trong bộ quyền của **chính người đang thao tác**. Không có L2 thì L1 vô nghĩa:
gán admin cho đồng nghiệp rồi nhờ họ gán ngược lại là đi vòng xong trong hai phút.

⚠️ **Phạm vi dữ liệu (`scope`) cố ý KHÔNG nằm trong L2.** Một người có
`employee.read` phạm vi *phòng ban* vẫn phải gán được vai trò `vanban_xem` (vai
trò đó khai `employee.read` phạm vi *tất cả*) — đó là việc hằng ngày, chặn là
hỏng nghiệp vụ. Chiều nới phạm vi cho CHÍNH MÌNH đã bị L1 chặn; nới cho người
khác thì vẫn còn, và cần hai người thông đồng. Ghi ra đây để lần sau ai đọc cũng
biết là đã cân nhắc, không phải bỏ sót.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import ACTIONS, ENTITY_LABELS

#  Câu lỗi dùng chung: nói rõ PHẢI LÀM GÌ, vì người đọc nó thường là quản trị
#  đang tưởng hệ hỏng chứ không phải kẻ đang cố leo thang.
SELF_CHANGE_MESSAGE = ("Không tự đổi quyền của chính mình được. Nhờ một quản trị khác thao tác "
          "trên tài khoản của bạn — đây là chốt hai người của phân quyền.")


def block_edit_own_permissions(user_id: int, actor) -> None:
    """L1. Gọi ở mọi cửa ghi phân quyền có tham số «tài khoản đích»."""
    if user_id == actor.id:
        raise HTTPException(403, SELF_CHANGE_MESSAGE)


def permissions_of_roles(db: Session, role_ids: list[int]) -> set[tuple[str, str]]:
    """Tập `(entity, action)` mà mấy vai trò này cấp. Vai trò không có thì rỗng."""
    from app.modules.role.model import Permission

    if not role_ids:
        return set()
    result: set[tuple[str, str]] = set()
    for row in db.query(Permission).filter(Permission.role_id.in_(role_ids)).all():
        for action in ACTIONS:
            if getattr(row, f"can_{action}", False):
                result.add((row.entity, action))
    return result


def _actor_permissions(db: Session, actor) -> set[tuple[str, str]]:
    from app.core.auth import get_perm_profile

    union = (get_perm_profile(db, actor) or {}).get("perms_union") or {}
    return {(entity, action)
            for entity, o in union.items()
            for action in ACTIONS if o.get(action)}


def block_privilege_escalation(db: Session, actor, to_grant: set[tuple[str, str]]) -> None:
    """L2. `dang_cap` = tập `(entity, action)` mà thao tác này sắp trao đi."""
    excess = to_grant - _actor_permissions(db, actor)
    if not excess:
        return

    #  Kể tên vài cái đầu thôi: người khai quyền cần biết vướng ở đâu, không cần
    #  một danh sách 300 dòng.
    names = sorted({ENTITY_LABELS.get(entity, entity) for entity, _ in excess})
    head = ", ".join(f"«{item}»" for item in names[:4])
    suffix = f" và {len(names) - 4} mục nữa" if len(names) > 4 else ""
    raise HTTPException(
        403,
        f"Không cấp được quyền mà chính bạn không có: {head}{suffix}. "
        "Nhờ người có đủ quyền đó thao tác, hoặc xin cấp quyền cho mình trước.",
    )


def block_role_escalation(db: Session, actor, role_ids: list[int]) -> None:
    """Gộp L2 cho cửa «gán vai trò cho tài khoản»."""
    block_privilege_escalation(db, actor, permissions_of_roles(db, role_ids))


def block_edit_own_role(db: Session, role_id: int, actor) -> None:
    """L1 cho cửa «sửa ma trận quyền của một vai trò».

    Cửa này không đụng tới tài khoản nào nên nhìn qua tưởng vô hại, nhưng tick
    thêm ô vào vai trò mình đang giữ thì quyền của mình lên ngay ở request sau —
    `set_permissions` gọi `perm_cache_clear()` xóa sạch cache, đúng như nó phải làm.
    """
    from app.modules.user.model import UserRole

    held = db.query(UserRole.id).filter(
        UserRole.user_id == actor.id, UserRole.role_id == role_id).first()
    if held:
        raise HTTPException(
            403, "Bạn đang giữ vai trò này nên không tự sửa quyền của nó được. " + SELF_CHANGE_MESSAGE)


def permissions_in_matrix(permissions) -> set[tuple[str, str]]:
    """Tập `(entity, action)` mà một lượt lưu ma trận vai trò sắp bật lên.

    Nhận thẳng danh sách schema Pydantic của `PUT /api/roles/{id}/permissions`.
    """
    result: set[tuple[str, str]] = set()
    for item in permissions or []:
        entity = getattr(item, "entity", None)
        if not entity:
            continue
        for action in ACTIONS:
            if getattr(item, f"can_{action}", False):
                result.add((entity, action))
    return result


def block_missing_roles(db: Session, role_ids: list[int]) -> None:
    """Gán một id vai trò không có thật thì `tab_user_role` ôm dòng rác vĩnh viễn.

    Bảng này không có khóa ngoại, nên CSDL không đỡ hộ; dòng rác không hiện ở đâu
    trên giao diện, mà mọi thống kê đếm theo vai trò đều đếm cả nó.
    """
    from app.modules.role.model import Role

    if not role_ids:
        return
    found_ids = {row[0] for row in
               db.query(Role.id).filter(Role.id.in_(set(role_ids))).all()}
    missing = sorted(set(role_ids) - found_ids)
    if missing:
        raise HTTPException(400, f"Vai trò không tồn tại: {missing}")
