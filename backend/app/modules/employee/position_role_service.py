"""QUYỀN MẶC ĐỊNH THEO CHỨC VỤ (duoc-CR-653).

Mỗi chức vụ khai một GÓI = danh sách vai trò có sẵn (`tab_job_position_role`). Tài khoản của nhân sự
đang giữ chức vụ X được hệ thống tự cấp gói của X, để nhân sự mới làm việc được ngay mà quản trị không
phải tick vai trò bằng tay.

Nguyên tắc (đại ca chốt):

* Dòng do hệ thống cấp mang `tab_user_role.granted_by_position_id > 0`. Dòng quản trị gán tay là `0`
  và KHÔNG BAO GIỜ bị hàm nào ở đây gỡ.
* Hàm lõi `sync_employee_roles` là "đối chiếu", không phải "áp độ lệch": nó nhìn chức vụ hiện tại của hồ
  sơ rồi làm cho phần tự cấp khớp gói — nên gọi lại bao nhiêu lần cũng ra cùng kết quả, và mọi đường đổi
  chức vụ (lưu hồ sơ, nhập Excel, áp quá trình công tác, hoàn tác lô) chỉ cần gọi nó SAU khi đổi.
* Vai trò đã có (gán tay) cũng nằm trong gói thì không thêm dòng trùng và không đánh dấu lại → đổi chức
  vụ sau này vẫn giữ nguyên.
* Chỉ `flush`, audit không commit (`record(..., commit=False)`): đi chung giao dịch với thay đổi gây ra
  nó; xóa cache quyền SAU commit (xem `_clear_cache_after_commit`).
* Tài khoản khóa / hồ sơ đã nghỉ việc: không cấp, không thu hồi (tài khoản đã bị khóa rồi).
"""
from dataclasses import dataclass, field

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Employee
from .position_model import JobPosition, JobPositionRole

STATUS_RESIGNED = "resigned"

#  M5: mã vai trò quản trị — không bao giờ vào gói / không bao giờ tự cấp.
_ADMIN_ROLE_CODES = ("admin", "administrator")
#  M5: đối tượng quản lý phân quyền — vai trò có ghi/tạo/xóa ở đây = quyền quản lý quyền.
_PERMISSION_ENTITIES = ("role", "user")
FORBIDDEN_MESSAGE = ("Không đưa vào quyền mặc định của chức vụ các vai trò quản trị hoặc có quyền ghi/tạo/xóa "
                     "trên Vai trò / Tài khoản — những vai trò này chỉ gán tay.")


@dataclass
class SyncResult:
    """Kết quả đối chiếu cho MỘT tài khoản."""
    user_id: int
    granted: list[int] = field(default_factory=list)
    revoked: list[int] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)   # H1/M5: vai trò trong gói nhưng không được tự cấp
    skipped_self: bool = False                         # C1: tài khoản của chính người thao tác

    @property
    def changed(self) -> bool:
        return bool(self.granted or self.revoked)

    @property
    def noteworthy(self) -> bool:
        return self.changed or bool(self.skipped) or self.skipped_self


@dataclass
class ActorCtx:
    """Người thao tác: có phải quản trị không + tập quyền (entity, action) của họ."""
    id: int
    is_admin: bool
    perms: set


def actor_ctx(db: Session, actor_id: int) -> ActorCtx:
    """Không tìm thấy tài khoản của người thao tác (id 0 / hệ thống) → coi là KHÔNG quản trị, không quyền:
    mặc định an toàn là không tự cấp gì."""
    from app.core import privilege_escalation as pe
    from app.modules.user.model import User

    user = db.get(User, actor_id) if actor_id else None
    if not user:
        return ActorCtx(actor_id, False, set())
    if pe.is_system_admin(db, user.id):
        return ActorCtx(user.id, True, set())
    return ActorCtx(user.id, False, pe._actor_permissions(db, user))


def forbidden_role_ids(db: Session) -> set[int]:
    """M5: vai trò KHÔNG được vào gói — quản trị, hoặc có ghi/tạo/xóa trên `role`/`user`."""
    from sqlalchemy import func, or_
    from app.modules.role.model import Permission, Role

    ids = {r for (r,) in db.query(Role.id).filter(func.lower(Role.code).in_(_ADMIN_ROLE_CODES)).all()}
    ids |= {r for (r,) in db.query(Permission.role_id).filter(
        Permission.entity.in_(_PERMISSION_ENTITIES),
        or_(Permission.can_write.is_(True), Permission.can_create.is_(True),
            Permission.can_delete.is_(True))).all()}
    return ids


def block_forbidden_roles(db: Session, role_ids) -> None:
    bad = set(int(r) for r in role_ids) & forbidden_role_ids(db)
    if bad:
        raise HTTPException(400, f"{FORBIDDEN_MESSAGE} Vai trò vướng: {_role_names(db, bad)}.")


def bundle_role_ids(db: Session, position_id: int) -> list[int]:
    """Gói của chức vụ. JOIN `tab_role` (H3): dòng gói trỏ vào vai trò đã xóa bị bỏ qua, không đẻ dòng mồ côi."""
    from app.modules.role.model import Role

    if not position_id:
        return []
    return sorted(r for (r,) in db.query(JobPositionRole.role_id)
                  .join(Role, Role.id == JobPositionRole.role_id)
                  .filter(JobPositionRole.job_position_id == position_id).all())


def _role_names(db: Session, role_ids) -> str:
    from app.modules.role.model import Role
    ids = sorted({int(r) for r in role_ids})
    if not ids:
        return ""
    by_id = {i: (n or c) for i, n, c in db.query(Role.id, Role.name, Role.code).filter(Role.id.in_(ids)).all()}
    return ", ".join(by_id.get(i, f"#{i}") for i in ids)


def _clear_cache_after_commit(db: Session, user_ids: list[int]) -> None:
    """Xóa cache quyền ngay + lần nữa sau commit (cache dựng lại giữa chừng sẽ thấy bản CŨ 60 giây)."""
    from app.core.auth import perm_cache_clear

    ids = sorted(set(user_ids))
    for uid in ids:
        perm_cache_clear(uid)

    def _again(_session):
        for uid in ids:
            perm_cache_clear(uid)

    event.listen(db, "after_commit", _again, once=True)


def employee_eligible(emp: Employee | None, user) -> bool:
    """Có được tự cấp cho tài khoản này không: tài khoản đang mở, hồ sơ còn làm."""
    return bool(emp and user and user.is_active and emp.is_active
                and (emp.status or "") != STATUS_RESIGNED)


def _insert_role(db: Session, user_id: int, role_id: int, pos_id: int, actor_id: int) -> bool:
    """Thêm một dòng vai trò trong SAVEPOINT. Trùng (M2: unique user×role do ghi đồng thời) → coi như đã có."""
    from app.modules.user.model import UserRole

    try:
        with db.begin_nested():
            db.add(UserRole(user_id=user_id, role_id=role_id, granted_by_position_id=pos_id,
                            created_by=actor_id, updated_by=actor_id))
        return True
    except IntegrityError:
        return False


def _sync_user(db: Session, user, position: JobPosition | None, desired: set[int], actor: ActorCtx) -> SyncResult:
    from app.modules.user.model import UserRole

    res = SyncResult(user_id=user.id)
    pos_id = position.id if position else 0
    rows = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    held = {r.role_id for r in rows}
    forbidden = forbidden_role_ids(db)
    for row in rows:
        if not row.granted_by_position_id:
            continue                                   # gán tay — không đụng
        if row.role_id in desired and row.role_id not in forbidden:
            if row.granted_by_position_id != pos_id:   # cùng vai trò, chức vụ mới → chỉ đổi nhãn nguồn
                row.granted_by_position_id = pos_id
                row.updated_by = actor.id
        else:
            db.delete(row)                             # THU HỒI luôn được phép (kể cả vai trò vừa thành "cấm")
            res.revoked.append(row.role_id)
    missing = sorted(desired - held)
    if not missing:
        return res
    #  C1: không tự cấp cho chính mình (trừ quản trị) — chống HR tự đặt chức vụ cho mình để lấy gói.
    if user.id == actor.id and not actor.is_admin:
        res.skipped_self = True
        return res
    for rid in missing:
        #  M5 + H1: vai trò cấm, hoặc người thao tác (không phải quản trị) không đủ quyền để cấp.
        if rid in forbidden or (not actor.is_admin and not _within(actor, rid, db)):
            res.skipped.append(rid)
            continue
        if _insert_role(db, user.id, rid, pos_id, actor.id):
            res.granted.append(rid)
    return res


def _within(actor: ActorCtx, role_id: int, db: Session) -> bool:
    """Quyền của vai trò ⊆ quyền người thao tác — cùng chốt L2 của gán vai trò thủ công."""
    from app.core import privilege_escalation as pe
    return not (pe.permissions_of_roles(db, [role_id]) - actor.perms)


def _audit(db: Session, actor_id: int, res: SyncResult, position: JobPosition | None, why: str) -> None:
    from app.modules.user.service import user_label

    who = user_label(db, res.user_id)
    pos = f"\"{position.name}\"" if position else "(chưa có chức vụ)"
    if res.granted:
        record(db, actor_id, "user", res.user_id, "auto_grant_position",
               f"Tự cấp vai trò theo chức vụ {pos} cho {who} ({why}): {_role_names(db, res.granted)}",
               commit=False)
    if res.revoked:
        record(db, actor_id, "user", res.user_id, "auto_revoke_position",
               f"Tự thu hồi vai trò do chức vụ đổi sang {pos} — {who} ({why}): {_role_names(db, res.revoked)}",
               commit=False)
    if res.skipped:
        record(db, actor_id, "user", res.user_id, "auto_grant_skipped_position",
               f"Bỏ qua, không đủ quyền cấp (hoặc vai trò bị cấm tự cấp) theo chức vụ {pos} cho {who} ({why}): "
               f"{_role_names(db, res.skipped)}", commit=False)
    if res.skipped_self:
        record(db, actor_id, "user", res.user_id, "auto_grant_skipped_position",
               f"Bỏ qua, không tự cấp quyền theo chức vụ {pos} cho chính người thao tác ({who}, {why}) — "
               "nhờ quản trị bấm \"Áp lại\"", commit=False)


def sync_employee_roles(db: Session, emp: Employee, actor_id: int, why: str = "đổi chức vụ") -> list[SyncResult]:
    """Làm cho phần vai trò TỰ CẤP của mọi tài khoản gắn hồ sơ `emp` khớp gói chức vụ hiện tại.

    Bên gọi phải gọi SAU khi `emp.position_id` đã gán, và lo `commit`/`rollback`. Trả kết quả từng tài
    khoản có thay đổi hoặc có vai trò bị bỏ qua.
    """
    from app.modules.user.model import User

    if not emp or not emp.id:
        return []
    users = db.query(User).filter(User.employee_id == emp.id).all()
    if not users:
        return []
    position = db.get(JobPosition, emp.position_id) if emp.position_id else None
    desired = set(bundle_role_ids(db, position.id)) if position else set()
    actor = actor_ctx(db, actor_id)
    out: list[SyncResult] = []
    for u in users:
        if not employee_eligible(emp, u):
            continue
        res = _sync_user(db, u, position, desired, actor)
        if res.noteworthy:
            _audit(db, actor_id, res, position, why)
            out.append(res)
    if out:
        db.flush()
        _clear_cache_after_commit(db, [r.user_id for r in out if r.changed])
    return out


def grant_on_account_creation(db: Session, emp: Employee, user_id: int, actor_id: int) -> list[int]:
    """Cấp gói cho tài khoản VỪA tạo — chỉ phần người thao tác được phép cấp (H1). Trả vai trò đã cấp."""
    from app.modules.user.model import User

    user = db.get(User, user_id)
    if not user or not emp.position_id or not employee_eligible(emp, user):
        return []
    position = db.get(JobPosition, emp.position_id)
    desired = set(bundle_role_ids(db, emp.position_id))
    if not position or not desired:
        return []
    res = _sync_user(db, user, position, desired, actor_ctx(db, actor_id))
    if res.noteworthy:
        _audit(db, actor_id, res, position, "cấp tài khoản")
        db.flush()
        _clear_cache_after_commit(db, [user.id])
    return res.granted


def revoke_system_grants(db: Session, user_id: int, actor_id: int) -> list[int]:
    """L3: hồ sơ bị xóa cứng → gỡ mọi dòng HỆ THỐNG đã cấp của tài khoản (dòng gán tay giữ). Không commit."""
    from app.modules.user.model import UserRole

    rows = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.granted_by_position_id > 0).all()
    ids = [r.role_id for r in rows]
    for r in rows:
        db.delete(r)
    if ids:
        db.flush()
        record(db, actor_id, "user", user_id, "auto_revoke_position",
               f"Tự thu hồi vai trò theo chức vụ vì hồ sơ nhân sự bị xóa: {_role_names(db, ids)}", commit=False)
        _clear_cache_after_commit(db, [user_id])
    return ids


# ── Quản lý gói (API) ────────────────────────────────────────────────────────────────────────────

def get_bundle(db: Session, position_id: int) -> list[dict]:
    from app.modules.role.model import Role

    ids = bundle_role_ids(db, position_id)
    roles = {r.id: r for r in db.query(Role).filter(Role.id.in_(ids)).all()} if ids else {}
    return [{"role_id": i, "role_code": roles[i].code, "role_name": roles[i].name}
            for i in ids if i in roles]


def actor_holds_position(db: Session, actor, position_id: int) -> bool:
    """H2: người thao tác (qua hồ sơ nhân sự của họ) đang giữ chức vụ này không."""
    emp = db.get(Employee, actor.employee_id) if getattr(actor, "employee_id", 0) else None
    return bool(emp and emp.position_id == position_id)


def set_bundle(db: Session, position: JobPosition, role_ids: list[int], actor_id: int) -> tuple[list[int], list[int]]:
    """Ghi đè gói. KHÔNG đụng tài khoản nào — muốn áp cho người đang giữ phải bấm "Áp lại".
    Trả (vai trò thêm, vai trò bỏ). Gói + nhật ký đi CHUNG một giao dịch; ghi đồng thời bị unique chặn → 409."""
    from app.core import privilege_escalation

    new = sorted(set(role_ids))
    privilege_escalation.block_missing_roles(db, new)
    block_forbidden_roles(db, new)
    before = set(bundle_role_ids(db, position.id))
    added, removed = sorted(set(new) - before), sorted(before - set(new))
    if removed:
        db.query(JobPositionRole).filter(JobPositionRole.job_position_id == position.id,
                                         JobPositionRole.role_id.in_(removed)).delete(synchronize_session=False)
    for rid in added:
        db.add(JobPositionRole(job_position_id=position.id, role_id=rid, created_by=actor_id, updated_by=actor_id))
    parts = []
    if added:
        parts.append("thêm " + _role_names(db, added))
    if removed:
        parts.append("bỏ " + _role_names(db, removed))
    try:
        record(db, actor_id, "job_position", position.id, "set_position_roles",
               f"Sửa quyền mặc định của chức vụ \"{position.name}\""
               + (": " + "; ".join(parts) if parts else " (không đổi)"), commit=False)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Gói quyền của chức vụ vừa được người khác sửa — tải lại rồi thử lại.")
    return added, removed


def eligible_holder_pairs(db: Session, position_id: int) -> list[tuple[Employee, object]]:
    """(hồ sơ, tài khoản) đủ điều kiện nhận gói của chức vụ."""
    from app.modules.user.model import User

    rows = (db.query(Employee, User).join(User, User.employee_id == Employee.id)
            .filter(Employee.position_id == position_id).order_by(User.id).all())
    return [(e, u) for e, u in rows if employee_eligible(e, u)]


def count_eligible_holders(db: Session, position_id: int) -> int:
    return len(eligible_holder_pairs(db, position_id))


def reapply_to_holders(db: Session, position: JobPosition, actor) -> dict:
    """Đối chiếu lại phần tự cấp của MỌI người đang giữ chức vụ. Tài khoản của chính người bấm bị bỏ qua
    (trừ quản trị), báo riêng, KHÔNG tính vào `holders`. Vai trò người bấm không đủ quyền cấp bị bỏ qua + báo."""
    ctx = actor_ctx(db, actor.id)
    desired = set(bundle_role_ids(db, position.id))
    holders = eligible_holder_pairs(db, position.id)
    results, skipped_self, skipped_roles, counted = [], 0, 0, 0
    for emp, user in holders:
        if user.id == actor.id and not ctx.is_admin:
            skipped_self += 1
            #  Vẫn thu hồi được phần thừa của chính mình; chỉ không CẤP thêm (xử lý trong `_sync_user`).
        else:
            counted += 1
        res = _sync_user(db, user, position, desired, ctx)
        skipped_roles += len(res.skipped)
        if res.noteworthy:
            _audit(db, actor.id, res, position, "áp lại gói chức vụ")
            results.append(res)
    db.flush()
    changed = [r.user_id for r in results if r.changed]
    if changed:
        _clear_cache_after_commit(db, changed)
    summary = {"holders": counted, "changed_users": len(changed),
               "granted": sum(len(r.granted) for r in results),
               "revoked": sum(len(r.revoked) for r in results),
               "skipped_self": skipped_self, "skipped_no_permission": skipped_roles}
    record(db, actor.id, "job_position", position.id, "apply_position_roles",
           f"Áp lại quyền mặc định của \"{position.name}\": {summary['holders']} người giữ chức vụ, "
           f"{summary['changed_users']} tài khoản đổi (+{summary['granted']} / -{summary['revoked']}), "
           f"bỏ qua {skipped_roles} vai trò không đủ quyền cấp, {skipped_self} tài khoản của chính người bấm",
           commit=False)
    db.commit()
    return summary


def require_position(db: Session, position_id: int) -> JobPosition:
    obj = db.get(JobPosition, position_id)
    if not obj:
        raise HTTPException(404, "Không tìm thấy chức vụ")
    return obj
