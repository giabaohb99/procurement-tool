"""Gộp tên pháp nhân / phòng, tổng chi phí và CHE tiền cho danh sách kế hoạch (mỗi loại tên MỘT truy vấn).
Kèm bộ chuyển ORM / schema → dữ liệu thuần cho `costing`. Chi tiết một kế hoạch ở `detail_serializer.py`."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.labor_contract.access import has_perm
from app.modules.labor_contract.lookup import names_map

from .costing import CostItem, PlanCalcError, PlanLine, compute_plan, period_label
from .cost_model import HeadcountPlanCostItem, HrCostGroup
from .model import HeadcountPlan, HeadcountPlanLine

WHOLE_COMPANY_LABEL = "Toàn pháp nhân"


def _ints(values) -> set[int]:
    return {int(v) for v in (values or []) if str(v).lstrip("-").isdigit()}


def can_see_payroll(profile: dict, company_id: int | None = None, department_id: int = 0) -> bool:
    """Số lương kế hoạch chỉ trả cho người ĐỌC ĐƯỢC hợp đồng lao động CỦA PHÁP NHÂN ĐÓ.

    Không đủ «có khóa `labor_contract.read`»: quyền đó chỉ có nghĩa trong phạm vi dữ liệu. Chỉ phạm vi
    `all` hoặc `company` (đúng pháp nhân hồ sơ của người xem) mới phủ một pháp nhân; `dept` / `own` / còn lại
    thì ẨN. Ô «chọn công ty» thu hẹp, ô «loại trừ công ty» trừ bớt, giống `scoping._explicit_cond`.
    `department_id` khác 0 (kế hoạch của MỘT phòng): phòng bị LOẠI TRỪ ở grant nào thì grant đó không phủ kế hoạch này
    (khớp `apply_scope(labor_contract)`: HĐ của phòng đó vốn không đọc được). Kế hoạch «Toàn pháp nhân» (0) xét theo pháp nhân.
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
        if covered and department_id and department_id in _ints((sc.get("exc") or {}).get("department")):
            covered = False
        if covered:
            return True
    return False


def to_cost_item(obj) -> CostItem:
    """ORM `HeadcountPlanCostItem` / `HrCostTemplateItem` hoặc schema `CostItemIn` → `CostItem` (tiền None → 0)."""
    return CostItem(
        code=obj.code, name=obj.name or "", group_id=int(obj.group_id or 0), calc_method=int(obj.calc_method),
        rate=Decimal(str(obj.rate or 0)), factor=Decimal(str(obj.factor or 0)),
        cap_amount=int(obj.cap_amount or 0), amount=int(obj.amount or 0), base_codes=tuple(obj.base_codes or ()),
        applies_to=int(obj.applies_to or 1), position_ids=tuple(int(p) for p in (obj.position_ids or ())),
        months=tuple(int(m) for m in (obj.months or ())), sort_order=int(obj.sort_order or 0),
        actual_source=int(getattr(obj, "actual_source", 0) or 0))


def to_plan_line(obj) -> PlanLine:
    return PlanLine(position_id=int(obj.position_id or 0), headcounts=tuple(int(h) for h in (obj.headcounts or ())),
                    amounts={k: int(v or 0) for k, v in (obj.amounts or {}).items()})


def compute_from(db: Session, year: int, period_type: int, period_no: int, items, lines) -> dict:
    """Tính từ ORM hoặc schema. Có thể ném `PlanCalcError`."""
    rows = db.query(HrCostGroup.id, HrCostGroup.name, HrCostGroup.sort_order).all()
    return compute_plan(period_type, period_no, year, [to_cost_item(i) for i in items],
                        [to_plan_line(ln) for ln in lines], {g: n for g, n, _ in rows}, {g: o for g, _, o in rows})


def mask_computed(computed: dict) -> dict:
    """Người không xem được tiền: chỉ giữ kỳ con + định biên; mọi con số tiền bỏ."""
    return {"periods": computed["periods"], "headcount": computed["headcount"], "items": [], "groups": [],
            "total": None, "avg_per_head": None, "money_hidden": True,
            "monthly": {m: {"headcount": v["headcount"], "items": {}} for m, v in computed["monthly"].items()}}


def readable_names(db: Session, user, profile: dict, employee_ids) -> dict[int, str]:
    """{id: họ tên} chỉ của hồ sơ người xem ĐỌC ĐƯỢC (`apply_scope(employee)`); hồ sơ ngoài phạm vi vắng mặt → tên rỗng."""
    ids = {i for i in employee_ids if i}
    if not ids:
        return {}
    q = apply_scope(db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)), Employee, "employee",
                    user, profile)
    return dict(q.all())


def serialize_plans(db: Session, rows: list[HeadcountPlan], profile: dict, user) -> list[dict]:
    if not rows:
        return []
    ids = [r.id for r in rows]
    companies = names_map(db, Company, {r.company_id for r in rows})
    departments = names_map(db, Department, {r.department_id for r in rows})
    approvers = readable_names(db, user, profile, {r.approver_employee_id for r in rows})
    items_by, lines_by = {}, {}
    for it in db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id.in_(ids)).all():
        items_by.setdefault(it.plan_id, []).append(it)
    for ln in db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id.in_(ids)).all():
        lines_by.setdefault(ln.plan_id, []).append(ln)
    out = []
    for r in rows:
        lines = lines_by.get(r.id, [])
        see = can_see_payroll(profile, r.company_id, r.department_id or 0)
        total = None
        if see:
            try:
                total = compute_plan(r.period_type, r.period_no, r.year, [to_cost_item(i) for i in items_by.get(r.id, [])],
                                     [to_plan_line(ln) for ln in lines])["total"]["total"]   # tổng không cần tên nhóm → không truy vấn thêm
            except PlanCalcError:
                total = None   # dữ liệu cũ sai luật tính — danh sách vẫn mở được
        out.append(header_out(r, companies, departments, approvers) | {
            "headcount_end": sum((ln.headcounts or [0])[-1] for ln in lines), "total_cost": total})
    return out


def header_out(r: HeadcountPlan, companies: dict, departments: dict, approvers: dict) -> dict:
    return {
        "id": r.id, "year": int(r.year), "period_type": int(r.period_type or 1), "period_no": int(r.period_no or 1),
        "period_label": period_label(int(r.year), int(r.period_type or 1), int(r.period_no or 1)),
        "company_id": r.company_id, "company_name": companies.get(r.company_id, ""),
        "department_id": r.department_id or 0,
        "department_name": departments.get(r.department_id, "") if r.department_id else WHOLE_COMPANY_LABEL,
        "basis_no": r.basis_no or "", "basis_date": r.basis_date,
        "approver_employee_id": r.approver_employee_id or 0, "approver_name": approvers.get(r.approver_employee_id, ""),
        "template_id": r.template_id or 0, "note": r.note or "", "updated_at": r.updated_at,
    }
