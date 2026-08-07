"""Lọc dữ liệu theo phạm vi — Lớp B (mô hình GRANT).

Mỗi vai trò của user là 1 grant: có quyền hành động + phạm vi riêng
(cấp bậc own/dept/company/all theo vai trò + chọn cụ thể công ty/phòng ban/nhân sự + loại trừ).
`apply_scope` = HỢP (OR) điều kiện của mọi grant có quyền `action` trên entity.
"""
from sqlalchemy import and_, or_, select

from app.core.auth import get_perm_profile  # noqa: F401  (re-export tiện dùng)

# Entity → tên cột theo từng chiều. Thiếu chiều nào = không lọc theo chiều đó.
SCOPE_FIELDS = {
    "purchase_request": {"company": "company_id", "dept_name": "department", "owner": "created_by"},
    "survey_request":   {"company": "company_id", "dept_name": "department", "owner": "created_by"},
    "purchase_order":   {"company": "company_id", "dept_name": "department", "owner": "created_by"},
    "payable":          {"company": "company_id", "owner": "created_by"},
    "payment_request":  {"company": "company_id", "owner": "created_by"},
    "inventory":        {"company": "company_id"},
    "survey":           {"owner": "created_by"},
    "employee":         {"company": "company_id", "dept_id": "department_id", "self": "id"},
    "ticket":           {"company": "company_id", "owner": "created_by"},
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
    dept_id = profile.get("dept_id") or 0

    # "Được giao": của mình HOẶC được phân bổ cho mình (áp cho PYC)
    if scope in ("assigned", "proc"):
        if entity == "purchase_request":
            from app.modules.purchase_request.model import PurchaseRequestItem
            conds = [model.created_by == user.id]
            if profile.get("employee_id"):
                conds.append(model.requester_id == profile["employee_id"])   # phiếu mình là người yêu cầu
            # "proc" (NV/Admin thu mua): thấy thêm MỌI phiếu đã duyệt để nhặt việc + phân bổ.
            # CR-034: gồm cả 'approved' (TP duyệt xong, ĐANG CHỜ ĐIỀU PHỐI) — thiếu trạng thái này
            # thì chính người phải điều phối lại không nhìn thấy phiếu.
            if scope == "proc":
                conds.append(model.status.in_(["approved", "dispatched"]))
            if profile.get("employee_id"):
                conds.append(model.assignee_id == profile["employee_id"])
            if profile.get("emp_code"):
                sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == profile["emp_code"])
                conds.append(model.id.in_(sub))
            return or_(*conds)
        if entity == "survey_request":
            from app.modules.survey_request.model import SurveyRequestLine
            conds = [model.created_by == user.id]   # phiếu MÌNH tạo → thấy mọi trạng thái
            # "Việc thu mua của tôi" CHỈ áp cho phiếu ĐÃ DUYỆT (bỏ nháp/chờ duyệt/từ chối).
            # NSTM chỉ thấy phiếu khi CÓ DÒNG gán mã mình — việc khảo sát nằm ở DÒNG.
            # (Bỏ điều kiện theo `assignee_id` đầu phiếu: trường đó chỉ ghi 1 lần lúc duyệt và
            #  không đồng bộ khi đổi NSTM dòng → người cũ vẫn thấy phiếu không còn phần việc nào.)
            emp_id = profile.get("employee_id") or 0
            if emp_id:
                conds.append(model.requester_id == emp_id)   # phiếu mình là người yêu cầu → thấy mọi trạng thái
            if profile.get("emp_code"):
                code_sub = (select(SurveyRequestLine.survey_request_id)
                            .where(SurveyRequestLine.assignee == profile["emp_code"]))
                conds.append(and_(model.status.notin_(["draft", "submitted", "rejected"]),
                                  model.id.in_(code_sub)))
            return or_(*conds)
        if entity == "purchase_order":
            # ĐMH: thấy đơn MÌNH tạo HOẶC đơn có NSPT phụ trách = mình (nspt lưu theo TÊN)
            conds = [model.created_by == user.id]
            if scope == "proc":
                conds.append(model.status == "approved")
            if profile.get("emp_name"):
                conds.append(model.nspt == profile["emp_name"])
            return or_(*conds)
        scope = "own"   # entity khác chưa có phân bổ → coi như của mình

    if scope == "own":
        if f.get("owner"):
            cond = getattr(model, f["owner"]) == user.id
            # Người YÊU CẦU cũng thấy phiếu của mình dù người khác (admin) tạo giùm
            rid = profile.get("employee_id") or 0
            if rid and hasattr(model, "requester_id"):
                cond = or_(cond, model.requester_id == rid)
            return cond
        if f.get("self"):   # entity không có owner (vd. employee) → chỉ chính mình
            return getattr(model, f["self"]) == (profile.get("employee_id") or 0)
        scope = "company"

    if scope == "dept":
        cs = []
        if f.get("company") and company_id:
            cs.append(getattr(model, f["company"]) == company_id)
        if f.get("dept_name"):
            cs.append(getattr(model, f["dept_name"]) == dept_name)
        elif f.get("dept_id"):
            cs.append(getattr(model, f["dept_id"]) == dept_id)
        elif f.get("owner"):
            cs.append(getattr(model, f["owner"]) == user.id)
        return and_(*cs) if cs else None

    if scope == "company":
        if f.get("company") and company_id:
            return getattr(model, f["company"]) == company_id
    return None


def _explicit_cond(model, entity, scopeconf):
    """Điều kiện THU HẸP: include công ty/nhân sự + MỌI loại trừ (AND).
    Riêng 'Phòng ban được xem' (department include) = CỘNG THÊM → xử lý ở apply_scope."""
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
        if inc and dim != "department":       # department include = additive (không thu hẹp)
            cs.append(column.in_([cast(v) for v in inc]))
        if exc:
            cs.append(~column.in_([cast(v) for v in exc]))
    return and_(*cs) if cs else None


def _dept_include_cond(model, entity, scopeconf):
    """'Phòng ban được xem' → điều kiện CỘNG THÊM (OR với phạm vi vai trò). None = không chọn phòng nào."""
    f = SCOPE_FIELDS.get(entity) or {}
    col = f.get("dept_name")
    inc = (scopeconf.get("inc") or {}).get("department") or []
    if not col or not inc:
        return None
    return getattr(model, col).in_(list(inc))


def apply_scope(query, model, entity: str, user, profile: dict, action: str = "read"):
    """Lọc query theo HỢP các grant có quyền `action` trên entity."""
    conds = []
    for g in profile.get("grants", []):
        p = g["perms"].get(entity)
        if not p or not p.get(action):
            continue
        scopeconf = g.get("scope") or {}
        rc = _role_scope_cond(model, entity, p.get("scope", "all"), user, profile)
        # 'Phòng ban được xem' = CỘNG THÊM vào phạm vi vai trò.
        # rc None (scope=all) → đã thấy hết, bỏ qua để không thu hẹp nhầm.
        dept_add = _dept_include_cond(model, entity, scopeconf)
        base = or_(rc, dept_add) if (rc is not None and dept_add is not None) else rc
        ec = _explicit_cond(model, entity, scopeconf)   # thu hẹp: company include + mọi loại trừ
        parts = [c for c in (base, ec) if c is not None]
        if not parts:
            return query          # grant này thấy tất cả → không lọc
        conds.append(and_(*parts))
    if not conds:
        return query.filter(model.id == -1)   # không grant nào cấp quyền này → không thấy gì
    return query.filter(or_(*conds))
