"""Gộp tên pháp nhân / phòng và CHE số lương cho một danh sách kế hoạch (mỗi loại tên MỘT truy vấn)."""
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.labor_contract.access import has_perm
from app.modules.labor_contract.lookup import names_map

from .model import HeadcountPlan

WHOLE_COMPANY_LABEL = "Toàn pháp nhân"


def _ints(values) -> set[int]:
    return {int(v) for v in (values or []) if str(v).lstrip("-").isdigit()}


def can_see_payroll(profile: dict, company_id: int | None = None) -> bool:
    """Số lương kế hoạch chỉ trả cho người ĐỌC ĐƯỢC hợp đồng lao động CỦA PHÁP NHÂN ĐÓ.

    Không đủ «có khóa `labor_contract.read`»: quyền đó chỉ có nghĩa trong phạm vi dữ liệu. Chỉ phạm vi
    `all` hoặc `company` (đúng pháp nhân hồ sơ của người xem) mới phủ một pháp nhân; `dept` / `own` / còn lại
    thì ẨN. Ô «chọn công ty» thu hẹp, ô «loại trừ công ty» trừ bớt, giống `scoping._explicit_cond`.
    `company_id=None` = hỏi «có quyền nào đọc HĐLĐ không» (dùng cho chốt chung, không theo dòng)."""
    if company_id is None:
        return has_perm(profile, "labor_contract", "read")
    for g in (profile or {}).get("grants", []):
        p = (g.get("perms") or {}).get("labor_contract")
        if not p or not p.get("read"):
            continue
        scope = p.get("scope", "all")
        if scope == "all":
            covered = True
        elif scope == "company":
            covered = bool(profile.get("company_id")) and company_id == profile.get("company_id")
        else:
            covered = False
        sc = g.get("scope") or {}
        inc, exc = (sc.get("inc") or {}).get("company"), (sc.get("exc") or {}).get("company")
        if covered and inc and company_id not in _ints(inc):
            covered = False
        if covered and company_id in _ints(exc):
            covered = False
        if covered:
            return True
    return False


def serialize_plans(db: Session, rows: list[HeadcountPlan], profile: dict) -> list[dict]:
    if not rows:
        return []
    companies = names_map(db, Company, {r.company_id for r in rows})
    departments = names_map(db, Department, {r.department_id for r in rows})
    return [{
        "id": r.id, "year": int(r.year), "company_id": r.company_id,
        "company_name": companies.get(r.company_id, ""), "department_id": r.department_id or 0,
        "department_name": departments.get(r.department_id, "") if r.department_id else WHOLE_COMPANY_LABEL,
        "planned_headcount": int(r.planned_headcount or 0),
        "planned_payroll_monthly": int(r.planned_payroll_monthly or 0) if can_see_payroll(profile, r.company_id) else None,
        "note": r.note or "", "updated_at": r.updated_at,
    } for r in rows]
