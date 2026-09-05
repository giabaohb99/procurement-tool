"""Duyệt dấu PHA 5 — ma trận PHÂN QUYỀN (apply_scope thật, không phải ẩn nút).

Chốt chặn ở backend: NS chỉ thấy phiếu của mình · TBP thấy phiếu cùng phòng · Văn thư
thấy phiếu CÔNG TY con dấu của mình · Quản trị con dấu thấy tất cả. Đặc biệt: Văn thư
công ty A KHÔNG thấy phiếu công ty B (theo `company_id` = công ty của con dấu).

Dùng fixture `cap_quyen` (vai trò thật + phạm vi) + `get_perm_profile` + `apply_scope`,
cùng khuôn `test_dat_xe_tong_the.py`.
"""
from types import SimpleNamespace

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import create_seal_request

COMPANY_A, COMPANY_B = 1, 2
DEPT_A, DEPT_B = 10, 20


def _person(db, cap_quyen, *, uid, code, dept, company, scope):
    emp = Employee(code=code, full_name=code, email=f"{code}@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=uid, employee_id=emp.id, email=f"{code}@dego.vn")
    cap_quyen(uid, "seal_request", scope=scope, read=True)
    return user


def _visible_ids(db, user):
    profile = get_perm_profile(db, user)
    q = apply_scope(db.query(m.SealRequest), m.SealRequest, "seal_request", user, profile)
    return {r.id for r in q.all()}


def _make(db, user, purpose, company_id):
    return create_seal_request(
        db, SealRequestCreate(purpose=purpose, seal_type_id=1, company_id=company_id),
        user, submit=False,
    )


def test_seal_permission_matrix(db, cap_quyen):
    ns1 = _person(db, cap_quyen, uid=2001, code="NS1", dept=DEPT_A, company=COMPANY_A, scope="own")
    ns2 = _person(db, cap_quyen, uid=2002, code="NS2", dept=DEPT_B, company=COMPANY_B, scope="own")
    tp1 = _person(db, cap_quyen, uid=2003, code="TP1", dept=DEPT_A, company=COMPANY_A, scope="dept")
    clerk_a = _person(db, cap_quyen, uid=2004, code="VTA", dept=DEPT_A, company=COMPANY_A, scope="company")
    clerk_b = _person(db, cap_quyen, uid=2005, code="VTB", dept=DEPT_B, company=COMPANY_B, scope="company")
    admin = _person(db, cap_quyen, uid=2006, code="ADM", dept=99, company=COMPANY_A, scope="all")

    #  A: phiếu con dấu CÔNG TY A do NS1 tạo (phòng A). B: công ty B do NS2 tạo (phòng B).
    a = _make(db, ns1, "[PQ] Đóng dấu HĐ công ty A", COMPANY_A)
    b = _make(db, ns2, "[PQ] Đóng dấu HĐ công ty B", COMPANY_B)

    # NS: chỉ phiếu của mình.
    assert _visible_ids(db, ns1) == {a.id}
    assert _visible_ids(db, ns2) == {b.id}
    # TBP: phiếu cùng phòng (A), không thấy B khác phòng/công ty.
    assert _visible_ids(db, tp1) == {a.id}
    # Văn thư: theo CÔNG TY con dấu — A chỉ thấy A, B chỉ thấy B (không lẫn).
    assert _visible_ids(db, clerk_a) == {a.id}
    assert _visible_ids(db, clerk_b) == {b.id}
    # Quản trị con dấu: thấy tất cả.
    assert _visible_ids(db, admin) == {a.id, b.id}
