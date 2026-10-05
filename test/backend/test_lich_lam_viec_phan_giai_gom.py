"""Lịch làm việc — bản GOM (`load_day_plans_many`) phải ra đúng như bản một người (`load_day_plans`).

Hai bản chia sẻ `_pick` nhưng tự dựng chỉ mục riêng; bài này khóa việc chúng không lệch nhau
khi gán bắt đầu/kết thúc giữa kỳ, nhiều cấp chồng nhau, nhân sự thiếu phòng/pháp nhân,
và mẫu thiếu một thứ trong tuần (rơi về lịch mặc định).
"""
from datetime import date, timedelta

import pytest

from app.core.work_schedule_codes import WorkScheduleLevel as L
from app.modules.employee.model import Employee
from app.modules.work_schedule.resolver import load_day_plans
from app.modules.work_schedule.resolver_many import load_day_plans_many
from lich_lam_viec_factory import FULL, OFF, SAT_AM, SAT_PM, assign, make_schedule, make_world

START = date(2026, 1, 5)
DAYS = [START + timedelta(days=i) for i in range(14)]


@pytest.fixture
def world(db):
    company, dept, e_full = make_world(db, "EQ1")
    mk = lambda code, **kw: Employee(code=code, full_name=code, is_active=True, **kw)
    e_nodept = mk("EQ2", company_id=company.id, department_id=0)
    e_nocomp = mk("EQ3", company_id=0, department_id=dept.id)
    e_solo = mk("EQ4", company_id=0, department_id=0)
    db.add_all([e_nodept, e_nocomp, e_solo])
    db.flush()
    s_sys = make_schedule(db, "Hệ thống", [FULL] * 5 + [SAT_AM, OFF])
    s_co = make_schedule(db, "Công ty", [FULL] * 5 + [SAT_PM, OFF])
    s_dept = make_schedule(db, "Phòng", [OFF] + [FULL] * 6)
    s_emp = make_schedule(db, "Nhân sự", [FULL] * 6 + [OFF])
    s_gap = make_schedule(db, "Thiếu thứ", [FULL] * 3)          # chỉ T2–T4 → T5.. rơi mặc định
    assign(db, L.SYSTEM, 0, s_sys.id, date(2026, 1, 8))                      # bắt đầu giữa kỳ
    assign(db, L.COMPANY, company.id, s_co.id, date(2026, 1, 1), date(2026, 1, 12))   # kết thúc giữa kỳ
    assign(db, L.DEPARTMENT, dept.id, s_dept.id, date(2026, 1, 10), date(2026, 1, 14))
    assign(db, L.DEPARTMENT, dept.id, s_gap.id, date(2026, 1, 15))
    assign(db, L.EMPLOYEE, e_full.id, s_emp.id, date(2026, 1, 6), date(2026, 1, 7))
    assign(db, L.EMPLOYEE, e_solo.id, s_gap.id, date(2026, 1, 1))
    db.commit()
    return [e_full, e_nodept, e_nocomp, e_solo]


def test_many_matches_single_for_every_employee_and_day(db, world):
    many = load_day_plans_many(db, world, DAYS[0], DAYS[-1])
    for e in world:
        single = load_day_plans(db, employee_id=e.id, department_id=int(e.department_id or 0),
                                company_id=int(e.company_id or 0), from_date=DAYS[0], to_date=DAYS[-1])
        for d in DAYS:
            assert many.at(e.id, d)[0] == single(d), (e.code, d)


def test_many_reports_fallback_id_zero_when_template_misses_weekday(db, world):
    many = load_day_plans_many(db, world, DAYS[0], DAYS[-1])
    e_solo = world[3]
    spec, sched_id = many.at(e_solo.id, date(2026, 1, 8))      # thứ Năm, mẫu chỉ có T2–T4
    assert sched_id == 0 and spec == load_day_plans(db, employee_id=e_solo.id, from_date=DAYS[0],
                                                    to_date=DAYS[-1])(date(2026, 1, 8))


def test_many_handles_empty_employee_list(db):
    many = load_day_plans_many(db, [], DAYS[0], DAYS[-1])
    assert many.at(1, DAYS[0])[1] == 0
