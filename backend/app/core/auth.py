"""Xác thực (JWT) + phân quyền (RBAC) dùng chung — giống AuthMiddleware."""
import time
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(raw, hashed)


def _create_token(user_id: int, kind: str, minutes: int) -> str:
    payload = {
        "sub": str(user_id), "type": kind,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", settings.ACCESS_EXPIRE_MIN)


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", settings.REFRESH_EXPIRE_DAYS * 24 * 60)

def create_reset_token(user_id: int) -> str:
    return _create_token(user_id, "reset_password", 24 * 60)


def decode_token(token: str, expected_type: str) -> int:
    """Giải mã token, kiểm tra đúng loại (access/refresh). Trả user_id."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if payload.get("type") != expected_type:
            raise HTTPException(401, "Sai loại token")
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    from app.modules.user.model import User

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Thiếu token đăng nhập")
    user_id = decode_token(authorization.split(" ", 1)[1], "access")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


# ===== Hồ sơ quyền + cache in-process (xem doc/Thiet_Ke_Phan_Quyen.md mục 9) =====
_PERM_CACHE: dict = {}   # {user_id: (profile, expires_at)}
_PERM_TTL = 60           # giây


def perm_cache_clear(user_id: int | None = None):
    """Xóa cache quyền khi admin sửa vai trò/quyền/gán vai trò."""
    if user_id is None:
        _PERM_CACHE.clear()
    else:
        _PERM_CACHE.pop(user_id, None)


def _dept_ref_map(db: Session, values) -> tuple[dict, dict]:
    """Tra một lượt các phòng ban được nhắc trong `tab_user_scope` → (id→tên, tên→id).

    Giá trị lưu có thể là ID (CR-086) hoặc TÊN (dòng cũ / FE cũ), nên tra cả hai chiều trong
    MỘT câu truy vấn. Trả về map rỗng nếu không có dòng phòng ban nào.
    """
    from sqlalchemy import or_

    from app.modules.department.model import Department
    vals = [(v or "").strip() for v in values]
    ids = {int(v) for v in vals if v.isdigit()}
    names = {v for v in vals if v and not v.isdigit()}
    if not ids and not names:
        return {}, {}
    conds = []
    if ids:
        conds.append(Department.id.in_(ids))
    if names:
        conds.append(Department.name.in_(names))
    rows = db.query(Department.id, Department.name).filter(or_(*conds)).all()
    return {r[0]: r[1] for r in rows}, {r[1]: r[0] for r in rows}


def get_perm_profile(db: Session, user) -> dict:
    """Hồ sơ quyền (cache in-process) theo mô hình GRANT — mỗi vai trò của user là 1 grant
    (quyền hành động + phạm vi RIÊNG). Trả:
      { grants: [ {role_id, perms:{entity:{action:bool,scope}}, scope:{inc,exc}} ],
        perms_union: {entity:{action:bool}}, company_id, dept_name }.
    """
    now = time.time()
    hit = _PERM_CACHE.get(user.id)
    if hit and hit[1] > now:
        return hit[0]

    from app.core.permissions import ACTIONS
    from app.modules.role.model import Permission
    from app.modules.user.model import UserRole, UserScope, User

    role_ids = [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()]

    # Quyền theo từng vai trò
    role_perms: dict = {}
    if role_ids:
        for p in db.query(Permission).filter(Permission.role_id.in_(role_ids)).all():
            rp = role_perms.setdefault(p.role_id, {})
            ent = rp.setdefault(p.entity, {**{a: False for a in ACTIONS}, "scope": "own"})
            for a in ACTIONS:
                if getattr(p, f"can_{a}", False):
                    ent[a] = True
            ent["scope"] = p.scope

    # Phạm vi cụ thể theo (user, vai trò); chiều nhân sự → đổi employee_id thành user_id (created_by)
    scope_rows = db.query(UserScope).filter(UserScope.user_id == user.id).all()
    emp_ids = {int(s.value) for s in scope_rows if s.dim == "employee" and (s.value or "").isdigit()}
    emp_to_user = {}
    if emp_ids:
        emp_to_user = {u.employee_id: u.id for u in db.query(User).filter(User.employee_id.in_(emp_ids)).all()}
    # CR-086: chiều phòng ban lưu ID. Dòng cũ (và FE cũ) còn ghi TÊN → đọc được cả hai và dựng
    # song song 2 khóa: `department` = id (để khớp `department_id` trên phiếu) và
    # `department_name` = tên (chỉ để lùi cho phiếu chưa điền lùi được id — xem scoping._dept_match).
    dep_by_id, dep_by_name = _dept_ref_map(db, [s.value for s in scope_rows if s.dim == "department"])
    scope_by_role: dict = {}
    for s in scope_rows:
        b = scope_by_role.setdefault(s.role_id, {"inc": {}, "exc": {}})
        kind = "exc" if s.is_exclude else "inc"
        if s.dim == "employee":
            uid = emp_to_user.get(int(s.value)) if (s.value or "").isdigit() else None
            if uid is not None:
                b[kind].setdefault("employee", []).append(uid)
        elif s.dim == "company":
            b[kind].setdefault("company", []).append(int(s.value) if (s.value or "").isdigit() else s.value)
        else:
            v = (s.value or "").strip()
            did = int(v) if v.isdigit() else dep_by_name.get(v, 0)
            name = dep_by_id.get(did, "") if v.isdigit() else v
            if did:
                b[kind].setdefault("department", []).append(did)
            if name:
                b[kind].setdefault("department_name", []).append(name)

    grants = [{"role_id": rid, "perms": role_perms.get(rid, {}),
               "scope": scope_by_role.get(rid, {"inc": {}, "exc": {}})} for rid in role_ids]

    perms_union: dict = {}
    for g in grants:
        for ent, p in g["perms"].items():
            u = perms_union.setdefault(ent, {a: False for a in ACTIONS})
            for a in ACTIONS:
                if p.get(a):
                    u[a] = True

    # Cờ tổng hợp cho FE: "process" = là nhân sự thu mua (được xem/xử lý khảo sát, thấy NCC).
    # = có grant survey_request read với scope proc|all (người YC own / trưởng BP dept → False).
    is_purchaser = any(
        g["perms"].get("survey_request", {}).get("read") and
        g["perms"].get("survey_request", {}).get("scope") in ("proc", "all")
        for g in grants
    )
    if is_purchaser:
        perms_union.setdefault("survey_request", {a: False for a in ACTIONS})["process"] = True

    company_id, dept_name, emp_code, dept_id, emp_name = 0, "", "", 0, ""
    dept_ids: list[int] = []
    dept_names: list[str] = []
    if getattr(user, "employee_id", 0):
        from app.modules.department.model import Department
        from app.modules.employee.department_service import phong_ban_cua
        from app.modules.employee.model import Employee
        emp = db.get(Employee, user.employee_id)
        if emp:
            company_id = emp.company_id or 0
            emp_code = emp.code or ""
            emp_name = emp.full_name or ""   # dùng khớp NSPT (ĐMH lưu theo tên)
            dept_id = emp.department_id or 0

            #  KIÊM NHIỆM (CR-167) — người này có chân ở những phòng nào. Phòng
            #  CHÍNH đứng đầu danh sách; `dept_id` / `dept_name` số ít vẫn là
            #  phòng chính, giữ nguyên cho những nơi chỉ dùng được một phòng.
            #
            #  ⚠️ Lùi về đúng phòng chính khi bảng kiêm nhiệm chưa có dòng nào
            #  (hồ sơ tạo trước migration, hoặc dữ liệu nhập tay): thiếu nhánh
            #  này là người đó mất sạch phạm vi phòng ban.
            dept_ids = phong_ban_cua(db, user.employee_id) or ([dept_id] if dept_id else [])
            if dept_ids:
                ten_phong = dict(db.query(Department.id, Department.name)
                                 .filter(Department.id.in_(dept_ids)).all())
                dept_names = [ten_phong[i] for i in dept_ids if ten_phong.get(i)]
                dept_name = ten_phong.get(dept_id, "")

    profile = {"grants": grants, "perms_union": perms_union, "company_id": company_id,
               "dept_name": dept_name, "dept_id": dept_id, "emp_code": emp_code, "emp_name": emp_name,
               #  Danh sách ĐẦY ĐỦ cho phạm vi dữ liệu — xem `core/scoping._dept_match`.
               "dept_ids": dept_ids, "dept_names": dept_names,
               "employee_id": getattr(user, "employee_id", 0) or 0}
    _PERM_CACHE[user.id] = (profile, now + _PERM_TTL)
    return profile


def get_user_permissions(db: Session, user) -> dict:
    """Map { entity: {action: bool} } — dùng cho /api/auth/me (FE ẩn menu/nút)."""
    return get_perm_profile(db, user)["perms_union"]


def user_has_permission(db: Session, user, entity: str, action: str) -> bool:
    return bool(get_perm_profile(db, user)["perms_union"].get(entity, {}).get(action, False))


def require(entity: str, action: str):
    """Dependency: chặn nếu user không có quyền `action` trên `entity`."""

    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if not user_has_permission(db, user, entity, action):
            raise HTTPException(403, f"Không có quyền: {action} {entity}")
        return user

    return dep
