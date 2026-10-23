"""Cách chọn người duyệt thứ chín — NGƯỜI CÓ QUYỀN DUYỆT theo màn Phân quyền (duoc-CR-680).

`approver_ref` = khóa quyền, luôn bằng loại chứng từ của luồng: `flow_controller` ghi đè lúc lưu bước và
ghi lại khi đổi loại chứng từ của luồng (review C2 — để lệch thì `get_scoped` soi nhầm bảng, id trùng là
phiếu duyệt dấu bị giao cho điều phối đặt xe).

Một người được giao bước khi đủ bốn điều:

1. Giữ một **grant đủ điều kiện**: vai trò có ô **Duyệt** trên khóa đó, phạm vi thuộc `ROW_SCOPES`
   (Phòng ban · Công ty · Tất cả), và KHÔNG phải vai trò `admin`. Bỏ «Của mình» / «Được giao» /
   «… đã duyệt»: các bậc đó chỉ với tới phiếu do chính họ tạo hoặc đã qua duyệt, không bao giờ phủ một
   phiếu mới của người khác — tính vào chỉ làm danh sách dài ra người không bao giờ được giao (local
   23/10/2026: 7 «Quản lý thu mua» có Duyệt đặt xe phạm vi «Của mình» vì seed cấp vai trò này mọi khóa).
   Bỏ `admin` vì Quản trị có mọi quyền theo ma trận, tính vào là mọi phiếu đổ về tài khoản quản trị.
2. Tài khoản đang mở và đã gắn hồ sơ nhân sự (việc duyệt giao theo `employee_id`).
3. **Phạm vi của CHÍNH các grant đủ điều kiện** phủ được phiếu này — cùng điều kiện `get_scoped(..., "approve")`
   dựng (gom một truy vấn cho mọi người), trên một hồ sơ quyền ĐÃ LỌC chỉ còn các grant đó (review C1: dùng nguyên hồ sơ thì grant `admin`
   «Tất cả» hay grant «Của mình» lọt lại qua cửa sau, điều phối công ty 3 nhận phiếu công ty 5).
4. Loại chứng từ nằm trong `_MODELS`. Chỉ mở cho loại mà phạm vi Phòng ban / Công ty nghĩa đúng là
   «phiếu của phòng / công ty đó». CỐ Ý CHƯA MỞ: `document` (quyền đọc còn đi qua ACL thư mục + luật
   CẤM của `access_service`, giao việc là mở cửa đọc vòng qua các luật đó — review H1) và
   `seal_request` (phạm vi Công ty chỉ phủ phiếu ĐÃ duyệt, không bao giờ khớp phiếu đang chờ — H2).
   Bối cảnh không có `id` thì trả RỖNG, không đoán (M1/M2).
"""
from __future__ import annotations

import importlib

from sqlalchemy import case, select, true
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.permissions import SCOPE_LABELS
from app.core.privilege_escalation import system_admin_role_id
from app.core.scoping import not_deleted_cond, scope_condition

#  Bậc phạm vi phủ được phiếu MỚI của người khác — xem điều 1.
ROW_SCOPES = ("dept", "company", "all")

#  entity → (mô-đun, lớp) của bảng chứng từ, nạp lười để khỏi vòng import với các bridge. Thêm loại
#  chứng từ = thêm một dòng SAU KHI xác nhận phạm vi Phòng ban / Công ty của nó nghĩa đúng như trên.
_MODELS = {
    "vehicle_booking": ("app.modules.vehicle_booking.model", "VehicleBooking"),
    "leave_request": ("app.modules.leave.request_model", "LeaveRequest"),
    "room_booking": ("app.modules.meeting_room.model", "RoomBooking"),
}
SUPPORTED_ENTITIES = tuple(_MODELS)


def model_of(entity: str):
    path = _MODELS.get(entity)
    if path is None:
        return None
    return getattr(importlib.import_module(path[0]), path[1])


def _approve_grant_conds(Permission, entity: str) -> list:
    return [Permission.entity == entity, Permission.can_approve.is_(True), Permission.scope.in_(ROW_SCOPES)]


def _qualifying_role_ids(db: Session, entity: str) -> set[int]:
    from app.modules.role.model import Permission

    admin_id = system_admin_role_id(db) or 0
    return {row[0] for row in db.query(Permission.role_id)
            .filter(*_approve_grant_conds(Permission, entity), Permission.role_id != admin_id).distinct()}


def holders(db: Session, entity: str, role_ids: set[int] | None = None) -> list:
    """Tài khoản đang mở, có hồ sơ, giữ ít nhất một grant đủ điều kiện trên `entity` (điều 1-2)."""
    from app.modules.user.model import User, UserRole

    if entity not in _MODELS:
        return []
    role_ids = _qualifying_role_ids(db, entity) if role_ids is None else role_ids
    if not role_ids:
        return []
    user_ids = {row[0] for row in
                db.query(UserRole.user_id).filter(UserRole.role_id.in_(role_ids)).all()}
    if not user_ids:
        return []
    return (db.query(User)
            .filter(User.id.in_(user_ids), User.is_active.is_(True), User.employee_id > 0)
            .order_by(User.id.asc()).all())


def _narrowed_profile(profile: dict, role_ids: set[int]) -> dict:
    """Bản sao hồ sơ quyền CHỈ còn grant đủ điều kiện (điều 3). Không sửa bản cache dùng chung."""
    return {**profile, "grants": [g for g in profile.get("grants", []) if g["role_id"] in role_ids]}


def resolve(db: Session, raw: str, subject: dict) -> list[int]:
    """employee_id của người có quyền duyệt phiếu này — xem docstring đầu tệp."""
    entity = (raw or "").strip()
    model = model_of(entity)
    row_id = subject.get("id")
    if model is None or not str(row_id or "").isdigit():
        return []
    role_ids = _qualifying_role_ids(db, entity)
    users = holders(db, entity, role_ids)
    if not users:
        return []
    #  MỘT truy vấn soi phạm vi cho mọi người giữ quyền: mỗi người một cột `CASE WHEN <phạm vi của họ>`
    #  trên đúng dòng phiếu — cùng điều kiện `get_scoped` dựng, khác ở chỗ không chạy N lượt
    #  (ép tải MySQL 23/10/2026: 200 người giữ quyền = 205 truy vấn lúc bộ đệm quyền nóng → còn 6).
    #  Phiếu đã xóa mềm / không tồn tại thì không có dòng nào → không ai được giao.
    columns = []
    for user in users:
        cond = scope_condition(model, entity, user,
                               _narrowed_profile(get_perm_profile(db, user), role_ids), "approve")
        columns.append(case((true() if cond is None else cond, 1), else_=0))
    query = select(*columns).select_from(model).where(model.id == int(row_id))
    deleted = not_deleted_cond(model)
    if deleted is not None:
        query = query.where(deleted)
    row = db.execute(query).first()
    if row is None:
        return []
    return [user.employee_id for user, hit in zip(users, row) if hit]


def holder_profiles(db: Session, entity: str) -> list[dict]:
    """Danh sách cho màn khai luồng: ai đang giữ grant đủ điều kiện trên `entity`, qua vai trò nào.

    Chưa lọc theo phiếu (lúc khai luồng chưa có phiếu) — phạm vi trả kèm để người khai đọc được
    «Điều phối viên · Tất cả» khác «Trưởng phòng · Phòng ban». Số truy vấn cố định.
    """
    from app.modules.employee.model import Employee
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole

    role_ids = _qualifying_role_ids(db, entity) if entity in _MODELS else set()
    users = holders(db, entity, role_ids)
    if not users:
        return []
    employees = {row.id: row for row in db.query(Employee.id, Employee.code, Employee.full_name,
                                                   Employee.is_active)
                 .filter(Employee.id.in_({user.employee_id for user in users})).all()}
    grants = (db.query(UserRole.user_id, Role.name, Permission.scope)
              .join(Role, Role.id == UserRole.role_id)
              .join(Permission, Permission.role_id == UserRole.role_id)
              .filter(UserRole.user_id.in_([user.id for user in users]),
                      UserRole.role_id.in_(role_ids), *_approve_grant_conds(Permission, entity))
              .order_by(Role.sort_order.asc(), Role.name.asc()).all())
    roles_of: dict[int, list[dict]] = {}
    for user_id, role_name, scope in grants:
        roles_of.setdefault(user_id, []).append(
            {"role": role_name, "scope": scope, "scope_label": SCOPE_LABELS.get(scope, scope)})

    out: dict[int, dict] = {}
    for user in users:
        employee = employees.get(user.employee_id)
        if employee is None or not employee.is_active:
            continue
        row = out.setdefault(employee.id, {"employee_id": employee.id, "code": employee.code,
                                           "name": employee.full_name, "roles": []})
        for grant in roles_of.get(user.id, []):
            if grant not in row["roles"]:
                row["roles"].append(grant)
    return list(out.values())
