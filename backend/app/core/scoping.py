"""Lọc dữ liệu theo phạm vi — Lớp B (mô hình GRANT).

Mỗi vai trò của user là 1 grant: có quyền hành động + phạm vi riêng
(cấp bậc own/dept/company/all theo vai trò + chọn cụ thể công ty/phòng ban/nhân sự + loại trừ).
`apply_scope` = HỢP (OR) điều kiện của mọi grant có quyền `action` trên entity.
"""
from sqlalchemy import and_, or_

from app.core.auth import get_perm_profile  # noqa: F401  (re-export tiện dùng)

# Entity → tên cột theo từng chiều. Thiếu chiều nào = không lọc theo chiều đó.
SCOPE_FIELDS = {
    "purchase_request": {"company": "company_id", "dept_name": "department", "owner": "created_by"},
    "purchase_order":   {"company": "company_id", "dept_name": "department", "owner": "created_by"},
    "payable":          {"company": "company_id", "owner": "created_by"},
    "payment_request":  {"company": "company_id", "owner": "created_by"},
    "inventory":        {"company": "company_id"},
    "survey":           {"owner": "created_by"},
}


def _role_scope_cond(model, entity, scope, user, profile):
    """Điều kiện theo cấp bậc vai trò (own/dept/company/all). None = 'all' (không giới hạn)."""
    if scope == "all":
        return None
    f = SCOPE_FIELDS.get(entity)
    if not f:
        return None
    company_id = profile.get("company_id") or 0
    dept_name = profile.get("dept_name") or ""

    if scope == "own":
        if f.get("owner"):
            return getattr(model, f["owner"]) == user.id
        scope = "company"

    if scope == "dept":
        cs = []
        if f.get("company") and company_id:
            cs.append(getattr(model, f["company"]) == company_id)
        if f.get("dept_name"):
            cs.append(getattr(model, f["dept_name"]) == dept_name)
        elif f.get("owner"):
            cs.append(getattr(model, f["owner"]) == user.id)
        return and_(*cs) if cs else None

    if scope == "company":
        if f.get("company") and company_id:
            return getattr(model, f["company"]) == company_id
    return None


def _explicit_cond(model, entity, scopeconf):
    """Điều kiện theo chọn cụ thể + loại trừ (công ty/phòng ban/nhân sự). None = không đặt."""
    f = SCOPE_FIELDS.get(entity) or {}
    dim_col = {"company": f.get("company"), "department": f.get("dept_name"), "employee": f.get("owner")}
    cs = []
    for dim, col in dim_col.items():
        if not col:
            continue
        column = getattr(model, col)
        inc = (scopeconf.get("inc") or {}).get(dim) or []
        exc = (scopeconf.get("exc") or {}).get(dim) or []
        cast = (lambda v: int(v)) if dim in ("company", "employee") else (lambda v: v)
        if inc:
            cs.append(column.in_([cast(v) for v in inc]))
        if exc:
            cs.append(~column.in_([cast(v) for v in exc]))
    return and_(*cs) if cs else None


def apply_scope(query, model, entity: str, user, profile: dict, action: str = "read"):
    """Lọc query theo HỢP các grant có quyền `action` trên entity."""
    conds = []
    for g in profile.get("grants", []):
        p = g["perms"].get(entity)
        if not p or not p.get(action):
            continue
        rc = _role_scope_cond(model, entity, p.get("scope", "all"), user, profile)
        ec = _explicit_cond(model, entity, g.get("scope") or {})
        parts = [c for c in (rc, ec) if c is not None]
        if not parts:
            return query          # grant này thấy tất cả → không lọc
        conds.append(and_(*parts))
    if not conds:
        return query.filter(model.id == -1)   # không grant nào cấp quyền này → không thấy gì
    return query.filter(or_(*conds))
