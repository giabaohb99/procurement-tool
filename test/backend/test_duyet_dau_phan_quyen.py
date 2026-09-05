"""Duyệt dấu — ma trận PHÂN QUYỀN (apply_scope thật), có MULTI-CÔNG TY.

- NS (own): chỉ phiếu của mình (mọi trạng thái).
- TBP (dept): phiếu cùng phòng (mọi trạng thái), KHÔNG chặn theo công ty con dấu.
- Văn thư / Giám đốc (company): phiếu có CÔNG TY MÌNH trong danh sách VÀ ĐÃ DUYỆT
  (đã qua TBP). Phiếu nháp KHÔNG hiện. Một phiếu gắn nhiều công ty → Văn thư của
  từng công ty đều thấy.
- Quản trị (all): tất cả.
"""
from types import SimpleNamespace

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import create_seal_request

CTY_A, CTY_B = 1, 2
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


def _make(db, user, purpose, company_ids, *, status):
    req = create_seal_request(
        db, SealRequestCreate(purpose=purpose, company_ids=company_ids, first_approver_id=500),
        user, submit=False)
    req.status = status
    db.flush()
    return req


def test_seal_permission_matrix_multi_company(db, cap_quyen):
    ns1 = _person(db, cap_quyen, uid=3001, code="NS1", dept=DEPT_A, company=CTY_A, scope="own")
    ns2 = _person(db, cap_quyen, uid=3002, code="NS2", dept=DEPT_B, company=CTY_B, scope="own")
    tp1 = _person(db, cap_quyen, uid=3003, code="TP1", dept=DEPT_A, company=CTY_A, scope="dept")
    clerk_a = _person(db, cap_quyen, uid=3004, code="VTA", dept=99, company=CTY_A, scope="company")
    clerk_b = _person(db, cap_quyen, uid=3005, code="VTB", dept=99, company=CTY_B, scope="company")
    admin = _person(db, cap_quyen, uid=3006, code="ADM", dept=99, company=CTY_A, scope="all")

    #  a: NS1 tạo, con dấu CỦA CẢ HAI công ty A+B, ĐÃ DUYỆT.
    a = _make(db, ns1, "[PQ] HĐ A+B", [CTY_A, CTY_B], status=m.SEAL_APPROVED)
    #  b: NS2 tạo, chỉ công ty B, ĐÃ DUYỆT.
    b = _make(db, ns2, "[PQ] HĐ B", [CTY_B], status=m.SEAL_APPROVED)
    #  c: NS1 tạo, công ty A, còn NHÁP (chưa qua TBP).
    c = _make(db, ns1, "[PQ] nháp A", [CTY_A], status=m.SEAL_DRAFT)

    # NS: chỉ phiếu của mình (mọi trạng thái).
    assert _visible_ids(db, ns1) == {a.id, c.id}
    assert _visible_ids(db, ns2) == {b.id}
    # TBP phòng A: phiếu cùng phòng (a, c), không thấy b (phòng B).
    assert _visible_ids(db, tp1) == {a.id, c.id}
    # Văn thư A: phiếu ĐÃ DUYỆT có công ty A → chỉ a. c là nháp nên KHÔNG hiện.
    assert _visible_ids(db, clerk_a) == {a.id}
    # Văn thư B: phiếu đã duyệt có công ty B → a (A+B) và b. (multi-công ty)
    assert _visible_ids(db, clerk_b) == {a.id, b.id}
    # Quản trị: tất cả.
    assert _visible_ids(db, admin) == {a.id, b.id, c.id}
