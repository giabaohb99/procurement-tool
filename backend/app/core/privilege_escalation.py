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

**Ngoại lệ Quản trị hệ thống (bao-CR-523, khách chốt 30/09/2026).** Người đang giữ
vai trò `admin` được MIỄN L1: tự sửa vai trò / phạm vi của chính mình, và sửa ma
trận của vai trò mình đang giữ. Lý do: admin vốn đã có mọi quyền (vai trò `admin`
luôn FULL, xem dưới), nên L1 với họ không chặn được leo thang nào — nó chỉ bắt
họ đi nhờ người khác cho những việc vặt. L2 vẫn giữ (admin đủ quyền nên luôn
qua). Đổi lại có hai chốt mới:

  · **Tự bỏ vai trò Quản trị của chính mình** phải kèm cờ xác nhận
    `confirm_self_admin_removal` — thiếu cờ thì 409 để giao diện hỏi lại.
  · **Không thao tác nào được để hệ còn 0 quản trị đang hoạt động** (bỏ vai trò,
    khóa, xóa tài khoản) — 400, kể cả có cờ.

Và **vai trò `admin` luôn FULL** mọi `ENTITIES × ACTIONS`, phạm vi `all`: cửa ghi
ma trận từ chối mọi bản làm hụt nó (400), còn `seed.ensure_admin_role` (chạy mỗi
lần deploy) tự lấp lại nếu DB lệch.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import ACTIONS, ENTITIES, ENTITY_LABELS

#  Mã vai trò Quản trị hệ thống. Chữ thường đúng như trên DB thật — so khớp
#  chính xác, không ép hoa/thường (vai trò `ADMINISTRATOR` đời cũ KHÔNG được miễn).
SYSTEM_ADMIN_ROLE_CODE = "admin"

#  Câu lỗi dùng chung: nói rõ PHẢI LÀM GÌ, vì người đọc nó thường là quản trị
#  đang tưởng hệ hỏng chứ không phải kẻ đang cố leo thang.
SELF_CHANGE_MESSAGE = ("Không tự đổi quyền của chính mình được. Nhờ một quản trị khác thao tác "
          "trên tài khoản của bạn — đây là chốt hai người của phân quyền.")

#  409: giao diện hiện NGUYÊN câu này trong hộp xác nhận, bấm Đồng ý thì gửi lại
#  kèm `confirm_self_admin_removal: true`.
SELF_ADMIN_REMOVAL_MESSAGE = (
    "Bạn đang tự bỏ vai trò Quản trị hệ thống của chính mình — sau khi lưu bạn sẽ mất "
    "quyền quản trị, muốn lấy lại phải nhờ quản trị khác. Tiếp tục?")

LAST_ADMIN_MESSAGE = "Hệ thống phải còn ít nhất một quản trị đang hoạt động"

ADMIN_ROLE_FULL_MESSAGE = ("Vai trò Quản trị hệ thống luôn đủ mọi quyền — không bớt quyền "
                           "hay thu hẹp phạm vi của vai trò này được.")


def system_admin_role_id(db: Session) -> int | None:
    """Id vai trò `admin`; hệ chưa seed thì `None` (mọi chốt dưới tự bỏ qua)."""
    from app.modules.role.model import Role

    row = db.query(Role.id).filter(Role.code == SYSTEM_ADMIN_ROLE_CODE).first()
    return row[0] if row else None


def is_system_admin(db: Session, user_id: int) -> bool:
    """Tài khoản này đang giữ vai trò `admin` không."""
    from app.modules.user.model import UserRole

    admin_id = system_admin_role_id(db)
    if not admin_id:
        return False
    return db.query(UserRole.id).filter(
        UserRole.user_id == user_id, UserRole.role_id == admin_id).first() is not None


def block_edit_own_permissions(user_id: int, actor, db: Session | None = None) -> None:
    """L1. Gọi ở mọi cửa ghi phân quyền có tham số «tài khoản đích».

    Truyền `db` thì Quản trị hệ thống được miễn (bao-CR-523). Không truyền thì
    giữ L1 cứng — quên truyền là CHẶN THỪA chứ không mở lỗ.
    """
    if user_id != actor.id:
        return
    if db is not None and is_system_admin(db, actor.id):
        return
    raise HTTPException(403, SELF_CHANGE_MESSAGE)


def count_active_admins(db: Session, exclude_user_id: int | None = None) -> int:
    """Số tài khoản ĐANG HOẠT ĐỘNG giữ vai trò `admin` (trừ `exclude_user_id` nếu có)."""
    from app.modules.user.model import User, UserRole

    admin_id = system_admin_role_id(db)
    if not admin_id:
        return 0
    query = (db.query(UserRole.user_id).join(User, User.id == UserRole.user_id)
             .filter(UserRole.role_id == admin_id, User.is_active.is_(True)))
    if exclude_user_id is not None:
        query = query.filter(UserRole.user_id != exclude_user_id)
    return query.distinct().count()


def block_last_admin_loss(db: Session, user_id: int) -> None:
    """Chốt «còn ít nhất một quản trị»: gọi TRƯỚC khi tài khoản #user_id thôi là
    quản trị đang hoạt động (bỏ vai trò, khóa, xóa). Người đó không giữ `admin`
    thì không có gì để mất, cho qua."""
    if not is_system_admin(db, user_id):
        return
    if count_active_admins(db, exclude_user_id=user_id) == 0:
        raise HTTPException(400, LAST_ADMIN_MESSAGE)


def removes_system_admin(db: Session, user_id: int, new_role_ids) -> bool:
    """Lượt gán vai trò này có TƯỚC vai trò `admin` của tài khoản #user_id không."""
    admin_id = system_admin_role_id(db)
    if not admin_id or admin_id in {int(r) for r in new_role_ids or []}:
        return False
    return is_system_admin(db, user_id)


def block_admin_role_removal(db: Session, user_id: int, actor, new_role_ids,
                             confirm_self_removal: bool = False) -> None:
    """Hai chốt khi một lượt gán vai trò bỏ `admin` khỏi tài khoản #user_id.

    Xếp «còn ít nhất một quản trị» (400) TRƯỚC «tự bỏ phải xác nhận» (409): hỏi
    người ta xác nhận một việc rồi đằng nào cũng từ chối là trêu người dùng.
    """
    if not removes_system_admin(db, user_id, new_role_ids):
        return
    block_last_admin_loss(db, user_id)
    if user_id == actor.id and not confirm_self_removal:
        raise HTTPException(409, SELF_ADMIN_REMOVAL_MESSAGE)


def block_admin_role_reduction(db: Session, role_id: int, permissions) -> None:
    """Vai trò `admin` chỉ nhận ma trận FULL: mọi entity trong `ENTITIES` bật đủ
    mọi hành động, phạm vi `all`. Vai trò khác thì cho qua.

    Dòng entity LẠ (không còn trong `ENTITIES`) không xét — thừa không hại gì.
    """
    from app.modules.role.model import Role

    role = db.get(Role, role_id)
    if role is None or role.code != SYSTEM_ADMIN_ROLE_CODE:
        return
    full: set[str] = set()
    for item in permissions or []:
        entity = getattr(item, "entity", None)
        if (entity and getattr(item, "scope", "") == "all"
                and all(getattr(item, f"can_{action}", False) for action in ACTIONS)):
            full.add(entity)
    if set(ENTITIES) - full:
        raise HTTPException(400, ADMIN_ROLE_FULL_MESSAGE)


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

    Quản trị hệ thống được miễn (bao-CR-523) — họ vốn đủ mọi quyền.
    """
    from app.modules.user.model import UserRole

    if is_system_admin(db, actor.id):
        return
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
