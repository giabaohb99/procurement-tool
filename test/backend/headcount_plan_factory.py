"""Khung dựng dữ liệu cho test kế hoạch nhân sự theo kỳ (duoc-CR-689/690): body API, người có quyền, dòng kế hoạch."""
from app.modules.headcount_plan.cost_model import HeadcountPlanCostItem
from app.modules.headcount_plan.model import HeadcountPlan, HeadcountPlanLine

URL = "/api/headcount-plans"
ALL = ("read", "create", "write", "delete", "export")


def grant_hr(world, client_as, *, pay=True, scope="all", key="a1", **grant_kw):
    """Người có quyền kế hoạch (+ xem hợp đồng lao động nếu `pay`)."""
    world.grant(key, "headcount_plan", scope, actions=ALL, **grant_kw)
    if pay:
        world.grant(key, "labor_contract", "all", actions=("read",))
    return client_as(world.actor(key))


def cost_item(code, method=1, **kw):
    """Một khoản ở dạng JSON gửi lên API."""
    return {"code": code, "name": kw.pop("name", code), "calc_method": method, **kw}


def basic_items():
    return [cost_item("L", 1, name="Lương", group_id=0),
            cost_item("BH", 2, name="BHXH", rate=17.5, base_codes=["L"], cap_amount=46_800_000),
            cost_item("B13", 3, name="Thưởng 13", factor=1, base_codes=["L"], months=[12])]


def plan_body(world, **kw):
    """Kế hoạch Năm 2026 · pháp nhân A · phòng A.kt; mặc định có 3 khoản + 1 dòng vị trí."""
    body = {"year": 2026, "period_type": 1, "period_no": 1, "company_id": world.co["A"],
            "department_id": world.dept["A.kt"], "note": "Được duyệt", "basis_no": "12/QĐ-BGĐ",
            "cost_items": basic_items(),
            "lines": [{"position_id": 0, "headcounts": [2, 2, 3, 3], "amounts": {"L": 10_000_000}}]}
    body.update(kw)
    return body


def add_costed_plan(db, world, dept="A.kt", headcounts=(10, 10, 10, 10), *, co="A", year=2026, period_type=1,
                    period_no=1, items=(), amounts=None, lines=None):
    """Kế hoạch ghi thẳng vào DB (không qua API). `items` = các dict khoản (`code`, `name`, `calc_method`, …);
    `lines` = [(position_id, headcounts, amounts)] — mặc định một dòng «không theo vị trí» với `headcounts`/`amounts`."""
    row = HeadcountPlan(year=year, period_type=period_type, period_no=period_no, company_id=world.co[co],
                        department_id=world.dept[dept] if dept else 0, note="")
    db.add(row)
    db.flush()
    for pos, heads, amt in (lines or [(0, list(headcounts), amounts or {})]):
        db.add(HeadcountPlanLine(plan_id=row.id, position_id=pos, headcounts=list(heads), amounts=dict(amt)))
    for it in items:
        db.add(HeadcountPlanCostItem(plan_id=row.id, **{"base_codes": [], "position_ids": [], "months": [], **it}))
    db.commit()
    return row


def add_plan(db, world, dept="A.kt", co="A", year=2026, n=10, period_type=1, period_no=1, lump=None):
    """Kế hoạch gần với dữ liệu đợt 4: một dòng «không theo vị trí» + (tuỳ chọn) khoản cả phòng."""
    items = [{"code": "QL", "name": "Quỹ lương", "calc_method": 5, "amount": lump, "applies_to": 3}] if lump else []
    return add_costed_plan(db, world, dept, [n] * 4, co=co, year=year, period_type=period_type,
                           period_no=period_no, items=items)
