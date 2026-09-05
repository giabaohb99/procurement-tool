"""Loại trừ email theo cá nhân / phòng ban / công ty — áp mọi mẫu HOẶC từng mẫu.

CHỈ lọc người nhận EMAIL; chuông không đụng tới.
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.notification import email_exclusion_service as ex
from app.modules.user.model import User

USER = SimpleNamespace(id=99)


def _user_emp(db, uid, dept, company):
    emp = Employee(code=f'E{uid}', full_name=f'NV{uid}', email=f'{uid}@dego.vn',
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    u = User(email=f'{uid}@dego.vn', is_active=True, employee_id=emp.id)
    u.id = uid
    db.add(u)
    db.flush()
    return u, emp


def test_exclude_by_employee(db):
    u1, e1 = _user_emp(db, 1, 10, 100)
    u2, _ = _user_emp(db, 2, 10, 100)
    ex.add(db, 'employee', e1.id, 'NV1', '', USER)
    assert [u.id for u in ex.filter_recipients(db, [u1, u2])] == [2]


def test_exclude_by_department(db):
    u1, _ = _user_emp(db, 1, 10, 100)
    u2, _ = _user_emp(db, 2, 20, 100)
    ex.add(db, 'department', 10, 'Phòng A', '', USER)
    assert [u.id for u in ex.filter_recipients(db, [u1, u2])] == [2]


def test_exclude_by_company(db):
    u1, _ = _user_emp(db, 1, 10, 100)
    u2, _ = _user_emp(db, 2, 10, 200)
    ex.add(db, 'company', 100, 'Cty A', '', USER)
    assert [u.id for u in ex.filter_recipients(db, [u1, u2])] == [2]


def test_no_exclusion_keeps_all(db):
    u1, _ = _user_emp(db, 1, 10, 100)
    assert ex.filter_recipients(db, [u1]) == [u1]


def test_exclusion_scoped_to_one_event(db):
    u1, e1 = _user_emp(db, 1, 10, 100)
    ex.add(db, 'employee', e1.id, 'NV1', 'dx_submitted', USER)
    # Bị loại ở đúng event đó...
    assert ex.filter_recipients(db, [u1], 'dx_submitted') == []
    # ...nhưng KHÔNG ở event khác.
    assert [u.id for u in ex.filter_recipients(db, [u1], 'dx_approved_dispatcher')] == [1]


def test_all_templates_exclusion_applies_to_every_event(db):
    u1, e1 = _user_emp(db, 1, 10, 100)
    ex.add(db, 'employee', e1.id, 'NV1', '', USER)  # "" = mọi mẫu
    assert ex.filter_recipients(db, [u1], 'dx_submitted') == []
    assert ex.filter_recipients(db, [u1], 'dx_completed_creator') == []


def test_same_target_different_event_are_separate_rows(db):
    ex.add(db, 'employee', 5, 'X', '', USER)
    ex.add(db, 'employee', 5, 'X', 'dx_submitted', USER)  # khác event → dòng riêng
    assert len(ex.list_all(db)) == 2
    # Thêm lại đúng (scope, ref_id, event) chỉ cập nhật, không nhân đôi.
    ex.add(db, 'employee', 5, 'X2', 'dx_submitted', USER)
    assert len(ex.list_all(db)) == 2


def test_list_carries_event_label(db):
    ex.add(db, 'company', 100, 'Cty A', 'dx_approved_dispatcher', USER)
    row = ex.list_all(db)[0]
    assert row['event'] == 'dx_approved_dispatcher'
    assert 'Điều phối viên' in row['event_label']
    ex.add(db, 'company', 200, 'Cty B', '', USER)
    labels = {r['ref_id']: r['event_label'] for r in ex.list_all(db)}
    assert labels[200] == 'Tất cả mẫu'
