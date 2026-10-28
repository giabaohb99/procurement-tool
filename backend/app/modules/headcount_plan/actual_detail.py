"""Khối `computed.actual` của chi tiết kế hoạch (duoc-CR-690, phase 24): thực tế của các kỳ con đã qua / đang chạy.

Dùng đúng hàm tính thực tế của báo cáo A5 (`actual_cost`) nên hai nơi không thể lệch số. Quy ước:
- kỳ con TƯƠNG LAI → mọi phần tử của kỳ con đó là `None`; kỳ con ĐANG CHẠY chỉ cộng các tháng đã bắt đầu
  (`months_counted` ghi số tháng), và «kế hoạch phần so được» cũng chỉ cộng đúng các tháng đó → còn dư so được với nhau;
- `values` / `planned_comparable` / `remaining` là TIỀN: người không xem được tiền nhận `None`, còn `headcount` (số người
  đang làm tại cuối kỳ con, đếm theo pháp nhân × phòng của kế hoạch) và danh sách mã khoản vẫn trả.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import as_of_filtered

from .contract_records import scope_hides_contracts, scoped_contract_records
from .actual_cost import ActualIndex, actual_by_item, covered_codes, month_as_of
from .effective import meta_of
from .model import HeadcountPlan


def _headcount_at(db: Session, plan: HeadcountPlan, as_of: date) -> int:
    q = db.query(Employee).filter(Employee.company_id == plan.company_id)
    if plan.department_id:
        q = q.filter(Employee.department_id == plan.department_id)
    return sum(branch.with_entities(func.count(Employee.id)).scalar() or 0 for branch in as_of_filtered(q, as_of))


def build_actual_block(db: Session, plan: HeadcountPlan, items, computed: dict, see_money: bool, user,
                       profile: dict) -> dict:
    """`computed` là kết quả chưa che của `compute_plan` (cần `periods` và `monthly`)."""
    today = vn_today()
    metas = {i.code: meta_of(i) for i in items}
    covered = covered_codes(metas)
    money_ok = see_money and bool(covered)   # không khoản nào có nguồn thực tế → không có gì để so
    #  Phạm vi HĐLĐ của người xem bỏ bớt HĐ của nơi này (vd loại trừ một phòng của pháp nhân) → Thực tế sẽ thiếu mà nhìn
    #  như đủ, «Còn dư» phóng to. Không so nữa, báo `limited_scope` để giao diện ghi lý do.
    limited = money_ok and scope_hides_contracts(db, user, profile, plan.company_id, plan.department_id or None)
    money_ok = money_ok and not limited
    layout = computed["periods"]
    elapsed = [[m for m in sub["months"] if month_as_of(plan.year, m, today) is not None] for sub in layout]
    index = None
    if money_ok and any(elapsed):
        first = date(plan.year, min(m for ms in elapsed for m in ms), 1)
        last = month_as_of(plan.year, max(m for ms in elapsed for m in ms), today)
        #  Đi qua phạm vi labor_contract của người xem: phòng bị loại trừ / HĐ xóa mềm không được cộng vào thực tế
        records = scoped_contract_records(db, user, profile, first, last, today, plan.company_id,
                                          plan.department_id or None)
        index = ActualIndex(records, today, last)
    values, planned, remaining, heads, counted = [], [], [], [], []
    for sub, months in zip(layout, elapsed):
        counted.append(len(months) if months else None)
        heads.append(_headcount_at(db, plan, month_as_of(plan.year, months[-1], today)) if months else None)
        if not months or not money_ok:
            values.append(None)
            planned.append(None)
            remaining.append(None)
            continue
        actual = sum(sum(actual_by_item(index.rows(plan.year, m, plan.company_id, plan.department_id or 0), metas)
                         .values()) for m in months) if index else 0
        plan_sum = sum(computed["monthly"][m]["items"].get(c, 0) for m in months for c in covered)
        values.append(actual)
        planned.append(plan_sum)
        remaining.append(plan_sum - actual)
    return {"values": values, "headcount": heads, "covered_codes": covered,
            "missing_codes": [c for c in metas if c not in covered], "planned_comparable": planned,
            "remaining": remaining, "months_counted": counted, "limited_scope": limited}
