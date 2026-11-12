"""duoc-CR-755 giai đoạn 02 — PHẠM VI QUYỀN theo CẶP (phòng, công ty) của kiêm nhiệm khác công ty.

Ba luật phải giữ, và tệp này là chỗ canh từng luật:

1. Dòng kiêm nhiệm hiệu lực + bật công tắc mở ĐÚNG cặp (phòng, công ty) — không mở phòng đó ở công ty chính, không mở
   cả công ty kia. Phòng DÙNG CHUNG (`company_id = 0`) là ca khó nhất: cùng một id phòng ở công ty A và B.
2. Quên một đường = THIẾU quyền chứ không LỘ dữ liệu: `dept_proc`, `_narrow_to_dept`, `_handler_match`,
   `holds_handling_dept` đều ràng công ty.
3. Q1 (đọc hồ sơ người kiêm nhiệm) mặc định TẮT, chỉ ĐỌC, một câu SQL — không N+1.

Mỗi chốt có cặp đối chứng ở chiều ngược (mở được cặp đúng NHƯNG không mở cặp sai), vì chặn sạch thì bài nào cũng xanh.
"""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import event

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.report_keys import ReportKey
from app.core.scoping import (PUBLIC, SCOPE_FIELDS, apply_scope, concurrent_row_scope_condition,
                              get_scoped, holds_handling_dept, scope_condition)
from app.core.subject_match import (EFFECT_ALLOW, SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                                    subject_match_condition, subject_pairs)
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.document.access_model import DocumentAccess
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.leave.request_model import LeaveRequest
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.report_access.grant_guards import block_self_allow_grant
from app.modules.report_access.model import ReportAccess
from app.modules.report_access.schema import ReportAccessGrantIn, ReportAccessSubjectIn
from app.modules.report_access.service import viewable_keys
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User

TODAY = vn_today()
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


# ── Dựng dữ liệu ─────────────────────────────────────────────────────────────

@pytest.fixture()
def w(world):
    """Thế giới mẫu + công ty C + phòng DÙNG CHUNG `SH` (company 0) + nhân sự `c1` ở (C, SH)."""
    db = world.db
    c = Company(code="CTY_C", name="Công ty C", is_active=True)
    db.add(c)
    db.flush()
    world.co["C"] = c.id
    for key, code, company_id in (("SH", "SH_DC", 0), ("C.kt", "C_KT", c.id)):
        row = Department(code=code, name=f"Phòng {code}", company_id=company_id, is_active=True)
        db.add(row)
        db.flush()
        world.dept[key] = row.id
    emp = Employee(code="C1", full_name="Nhân sự c1", company_id=c.id, department_id=world.dept["SH"],
                   is_active=True)
    db.add(emp)
    db.flush()
    world.emp["c1"] = emp.id
    user = User(email="c1", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    from scope_factory import Actor
    world._actors["c1"] = Actor(world, "c1", user, emp)
    db.commit()
    return world


def kn(w, emp_key: str, dept_key: str, company_key: str | None = "B", **kw) -> EmployeeConcurrent:
    """Một dòng kiêm nhiệm. Mặc định đang hiệu lực + bật công tắc; `company_key=None` = công ty 0."""
    row = EmployeeConcurrent(
        employee_id=w.emp[emp_key], department_id=w.dept[dept_key],
        company_id=w.co[company_key] if company_key else 0,
        from_date=kw.pop("from_date", TODAY - timedelta(days=30)), **kw)
    w.db.add(row)
    w.db.commit()
    perm_cache_clear()
    return row


def pr(w, code, company_key, dept_key, **kw) -> int:
    row = PurchaseRequest(code=code, company_id=w.co[company_key], department_id=w.dept[dept_key],
                          status=kw.pop("status", "approved"), created_by=w.user_id("b1"),
                          requester_id=w.emp["b1"], **kw)
    w.db.add(row)
    w.db.commit()
    return row.id


def pairs_of(w, key: str) -> list[list[int]]:
    return w.actor(key).profile()["concurrent_pairs"]


# ── 1. Hồ sơ quyền: cặp tách khỏi `dept_ids` ─────────────────────────────────

def test_hoso_quyen_cung_cong_ty_vao_dept_ids_khac_cong_ty_vao_cap(w):
    w.grant("a2", "purchase_request", "dept")
    kn(w, "a2", "A.mua", "A")       # cùng công ty chính
    kn(w, "a2", "B.kt", "B")        # khác
    kn(w, "a2", "SH", None)         # công ty 0 = coi như công ty chính (phòng dùng chung)
    prof = w.actor("a2").profile()
    assert prof["company_id"] == w.co["A"]                       # company_id vẫn MỘT số
    assert set(prof["dept_ids"]) == {w.dept["A.kt"], w.dept["A.mua"], w.dept["SH"]}
    assert prof["concurrent_pairs"] == [[w.dept["B.kt"], w.co["B"]]]


def test_cap_xep_on_dinh_va_bo_trung(w):
    w.grant("a2", "purchase_request", "dept")
    kn(w, "a2", "B.hc", "B")
    kn(w, "a2", "B.kt", "B")
    kn(w, "a2", "B.kt", "B", from_date=TODAY - timedelta(days=5))   # trùng cặp, dòng khác
    kn(w, "a2", "C.kt", "C")
    got = pairs_of(w, "a2")
    assert got == sorted(got, key=lambda p: (p[1], p[0]))
    assert len(got) == 3
    assert all(isinstance(x, int) for p in got for x in p)


def test_so_truy_van_dung_ho_so_quyen_khong_tang_theo_so_dong(w):
    """Đếm truy vấn `get_perm_profile` ở 1 dòng và 10 dòng kiêm nhiệm khác công ty: bằng nhau."""
    w.grant("a2", "purchase_request", "dept")
    user = w.actor("a2").user
    counts = []

    def count_profile() -> int:
        perm_cache_clear()
        n = []
        listener = lambda *a, **k: n.append(1)  # noqa: E731
        engine = w.db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            get_perm_profile(w.db, user)
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(n)

    kn(w, "a2", "B.kt", "B")
    counts.append(count_profile())
    for i in range(9):
        d = Department(code=f"X{i}", name=f"Phòng X{i}", company_id=0, is_active=True)
        w.db.add(d)
        w.db.flush()
        w.dept[f"X{i}"] = d.id
        kn(w, "a2", f"X{i}", "B")
    counts.append(count_profile())
    assert len(pairs_of(w, "a2")) == 10
    assert counts[0] == counts[1], counts


# ── 2. Bậc `dept`: mở đúng cặp ───────────────────────────────────────────────

def test_dept_thay_dung_cap_khong_thay_phong_khac_hay_cong_ty_khac(w):
    a = w.grant("a2", "purchase_request", "dept")
    kn(w, "a2", "B.kt", "B")
    ok = pr(w, "OK", "B", "B.kt")             # đúng cặp (B.kt, B)
    sai_phong = pr(w, "SAI_PHONG", "B", "B.hc")        # (Y, B)
    sai_cty = pr(w, "SAI_CTY", "A", "B.kt")            # cùng id phòng nhưng công ty A (chính) — phòng B.kt không là phòng mình ở A
    cua_toi = pr(w, "CUA_TOI", "A", "A.kt")            # phòng chính vẫn thấy
    assert a.sees(PurchaseRequest) == {ok, cua_toi}
    assert not a.can_get(PurchaseRequest, sai_phong) and not a.can_get(PurchaseRequest, sai_cty)


def test_dept_phong_dung_chung_khong_lan_sang_cong_ty_khac(w):
    """X dùng chung: kiêm nhiệm (X, B) thấy phiếu (X, B), KHÔNG thấy (X, C) và KHÔNG thấy (X, A)."""
    a = w.grant("a3", "purchase_request", "dept")
    kn(w, "a3", "SH", "B")
    x_b, x_c, x_a = pr(w, "XB", "B", "SH"), pr(w, "XC", "C", "SH"), pr(w, "XA", "A", "SH")
    assert a.sees(PurchaseRequest) == {x_b}
    assert not a.can_get(PurchaseRequest, x_c) and not a.can_get(PurchaseRequest, x_a)


def test_dept_don_nghi_va_ho_so_nhan_su_cua_cap(w):
    """Ba entity khác nhau cùng đi qua nhánh `dept`: đơn nghỉ, hồ sơ nhân sự (đã đọc theo vị trí CHÍNH)."""
    a = w.grant("a2", "leave_request", "dept")
    a.grant("employee", "dept")
    kn(w, "a2", "B.kt", "B")

    def leave(code, co, dept, emp):
        row = LeaveRequest(code=code, company_id=w.co[co], department_id=w.dept[dept], employee_id=w.emp[emp],
                           leave_type_id=1, from_date=TODAY, to_date=TODAY, total_days=1.0, reason="r",
                           status="submitted", created_by=w.user_id("b1"))
        w.db.add(row)
        w.db.commit()
        return row.id

    ok, sai = leave("L_OK", "B", "B.kt", "b1"), leave("L_SAI", "B", "B.hc", "b1")
    assert a.sees(LeaveRequest, "leave_request") == {ok}
    assert not a.can_get(LeaveRequest, sai, "leave_request")
    assert a.sees(Employee, "employee") >= {w.emp["b1"], w.emp["a1"], w.emp["a2"]}   # b1 chính ở (B.kt, B)
    assert w.emp["a3"] not in a.sees(Employee, "employee")                        # A.mua không phải phòng mình


def test_company_khong_phinh_cap_b_khong_mo_ca_cong_ty_b(w):
    a = w.grant("a2", "purchase_request", "company")
    kn(w, "a2", "B.kt", "B")
    a_pr, b_pr = pr(w, "A1", "A", "A.kt"), pr(w, "B1", "B", "B.kt")
    assert a.sees(PurchaseRequest) == {a_pr}
    assert b_pr not in a.sees(PurchaseRequest)
    assert not a.can_get(PurchaseRequest, b_pr)


def test_own_va_all_khong_doi(w):
    own = w.grant("a2", "purchase_request", "own")
    allp = w.grant("a1", "purchase_request", "all")
    kn(w, "a2", "B.kt", "B")
    kn(w, "a1", "B.kt", "B")
    x = pr(w, "P", "B", "B.kt")
    assert x not in own.sees(PurchaseRequest)
    assert x in allp.sees(PurchaseRequest)
    assert scope_condition(PurchaseRequest, "purchase_request", allp.user, allp.profile()) is None


# ── 3. `dept_proc`: không lọt qua đường không ràng công ty ───────────────────

def test_dept_proc_ycmh_phong_xu_ly_dung_cap_lot_sai_cong_ty_khong_lot(w):
    a = w.grant("a3", "purchase_request", "dept_proc")
    kn(w, "a3", "SH", "B")
    x_b = pr(w, "XB", "B", "B.hc", handler_dept_id=w.dept["SH"])
    x_c = pr(w, "XC", "C", "C.kt", handler_dept_id=w.dept["SH"])
    x_a = pr(w, "XA", "A", "A.kt", handler_dept_id=w.dept["SH"])
    assert a.sees(PurchaseRequest) == {x_b}
    assert not a.can_get(PurchaseRequest, x_c) and not a.can_get(PurchaseRequest, x_a)


def test_dept_proc_ycbg_va_dmh_dung_cap(w):
    a = w.grant("a3", "survey_request", "dept_proc")
    a.grant("purchase_order", "dept_proc")
    kn(w, "a3", "SH", "B")

    def sr(code, co):
        row = SurveyRequest(code=code, company_id=w.co[co], department_id=w.dept["A.kt"], status="processing",
                            handler_dept_id=w.dept["SH"], created_by=w.user_id("b1"), requester_id=w.emp["b1"])
        w.db.add(row)
        w.db.commit()
        return row.id

    def po(code, co):
        row = PurchaseOrder(code=code, company_id=w.co[co], status="approved", created_by=w.user_id("b1"),
                            department_id=w.dept["A.kt"], handler_dept_id=w.dept["SH"])
        w.db.add(row)
        w.db.commit()
        return row.id

    sr_b, sr_c = sr("SR_B", "B"), sr("SR_C", "C")
    po_b, po_c = po("PO_B", "B"), po("PO_C", "C")
    assert a.sees(SurveyRequest, "survey_request") == {sr_b}
    assert not a.can_get(SurveyRequest, sr_c, "survey_request")
    assert a.sees(PurchaseOrder, "purchase_order") == {po_b}
    assert not a.can_get(PurchaseOrder, po_c, "purchase_order")


def test_dept_proc_entity_khac_roi_ve_dept_van_ranh_cong_ty(w):
    """Đơn nghỉ không phải chứng từ thu mua: `dept_proc` rơi về bậc phòng — cặp vẫn ràng công ty."""
    a = w.grant("a2", "leave_request", "dept_proc")
    kn(w, "a2", "B.kt", "B")

    def leave(code, co, dept):
        row = LeaveRequest(code=code, company_id=w.co[co], department_id=w.dept[dept], employee_id=w.emp["b1"],
                           leave_type_id=1, from_date=TODAY, to_date=TODAY, total_days=1.0, reason="r",
                           status="submitted", created_by=w.user_id("b1"))
        w.db.add(row)
        w.db.commit()
        return row.id

    ok, sai = leave("L1", "B", "B.kt"), leave("L2", "C", "B.kt")
    assert a.sees(LeaveRequest, "leave_request") == {ok}
    assert not a.can_get(LeaveRequest, sai, "leave_request")


def test_dept_proc_chi_co_cap_khong_phong_chinh_van_khong_bi_chan(w):
    """Người chưa gắn phòng chính nhưng có cặp: không bị `_chan` oan, và vẫn chỉ thấy đúng cặp."""
    a = w.grant("khongphong", "purchase_request", "dept_proc")
    kn(w, "khongphong", "SH", "B")
    ok = pr(w, "OK", "B", "B.hc", handler_dept_id=w.dept["SH"])
    pr(w, "NO", "C", "C.kt", handler_dept_id=w.dept["SH"])
    assert a.sees(PurchaseRequest) == {ok}


def test_dept_proc_khong_cap_khong_phong_van_bi_chan(w):
    a = w.grant("khongphong", "purchase_request", "dept_proc")
    pr(w, "NO", "B", "B.hc", handler_dept_id=w.dept["SH"])
    assert a.sees(PurchaseRequest) == set()


# ── 4. Hết hạn / tắt công tắc / sắp tới ──────────────────────────────────────

@pytest.mark.parametrize("kw", [
    {"counts_scope": False},
    {"to_date": YESTERDAY},
    {"from_date": TOMORROW},
], ids=["tat-cong-tac", "het-han-hom-qua", "sap-toi-ngay-mai"])
def test_dong_khong_hieu_luc_khong_mo_gi_o_moi_duong(w, kw):
    a = w.grant("a3", "purchase_request", "dept")
    a.grant("purchase_request", "dept_proc")
    kn(w, "a3", "SH", "B", **kw)
    x_dept = pr(w, "X1", "B", "SH")
    x_handler = pr(w, "X2", "B", "B.hc", handler_dept_id=w.dept["SH"])
    assert pairs_of(w, "a3") == []
    assert {x_dept, x_handler}.isdisjoint(a.sees(PurchaseRequest))
    assert not holds_handling_dept(a.profile(), "purchase_request",
                                   SimpleNamespace(handler_dept_id=w.dept["SH"], company_id=w.co["B"]))
    assert subject_pairs(a.profile()).count((SUBJECT_DEPARTMENT, w.dept["SH"])) == 0


def test_ngay_dau_va_ngay_cuoi_deu_con_hieu_luc(w):
    w.grant("a3", "purchase_request", "dept")
    kn(w, "a3", "SH", "B", from_date=TODAY, to_date=TODAY)
    assert pairs_of(w, "a3") == [[w.dept["SH"], w.co["B"]]]


def test_gio_vn_00h30_tinh_dung_ngay_viet_nam(w, monkeypatch):
    """00:30 giờ VN ngày D = 17:30 UTC ngày D-1: dòng `from_date = D` PHẢI hiệu lực, `to_date = D-1` PHẢI hết."""
    from app.core import vn_time

    class FakeDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return datetime(2026, 11, 11, 17, 30)

    monkeypatch.setattr(vn_time, "datetime", FakeDatetime)
    w.grant("a3", "purchase_request", "dept")
    kn(w, "a3", "SH", "B", from_date=date(2026, 11, 12))
    kn(w, "a3", "B.kt", "B", from_date=date(2026, 10, 1), to_date=date(2026, 11, 11))
    assert pairs_of(w, "a3") == [[w.dept["SH"], w.co["B"]]]


# ── 5. `holds_handling_dept` ─────────────────────────────────────────────────

def test_holds_handling_dept_dung_cap_moi_duoc_chuyen_phong(w):
    a = w.grant("a3", "purchase_request", "dept_proc", actions=("read", "approve"))
    kn(w, "a3", "SH", "B")
    prof = a.profile()
    phieu = lambda co: SimpleNamespace(handler_dept_id=w.dept["SH"], company_id=w.co[co], department_id=0)  # noqa: E731
    assert holds_handling_dept(prof, "purchase_request", phieu("B")) is True
    assert holds_handling_dept(prof, "purchase_request", phieu("C")) is False
    assert holds_handling_dept(prof, "purchase_request", phieu("A")) is False
    # đối chứng: phòng chính (dept_ids) vẫn không cần công ty khớp, y như cũ
    cu = SimpleNamespace(handler_dept_id=w.dept["A.mua"], company_id=w.co["C"], department_id=0)
    assert holds_handling_dept(prof, "purchase_request", cu) is True


# ── 6. Q3: subject_match ─────────────────────────────────────────────────────

def _acl_report(w, subject_kind, subject_id, key=ReportKey(list(ReportKey)[0])):
    w.db.add(ReportAccess(report_key=int(key), subject_kind=subject_kind, subject_id=subject_id,
                          effect=EFFECT_ALLOW))
    w.db.commit()
    return int(key)


def test_acl_cap_cho_phong_x_khop_nguoi_kiem_nhiem_x_b(w):
    a = w.actor("a3")
    key = _acl_report(w, SUBJECT_DEPARTMENT, w.dept["SH"])
    assert key not in viewable_keys(w.db, a.user)              # chưa kiêm nhiệm: không khớp
    kn(w, "a3", "SH", "B")
    assert key in viewable_keys(w.db, a.user)
    prof = a.profile()
    assert (SUBJECT_DEPARTMENT, w.dept["SH"]) in subject_pairs(prof)
    assert subject_pairs(prof).count((SUBJECT_DEPARTMENT, w.dept["SH"])) == 1   # bỏ trùng
    assert (SUBJECT_COMPANY, w.co["B"]) not in subject_pairs(prof)                # không thành chủ thể công ty


@pytest.mark.parametrize("kw", [{"counts_scope": False}, {"to_date": YESTERDAY}, {"from_date": TOMORROW}],
                         ids=["tat-cong-tac", "het-han", "sap-toi"])
def test_acl_mat_khi_het_hieu_luc(w, kw):
    a = w.actor("a3")
    key = _acl_report(w, SUBJECT_DEPARTMENT, w.dept["SH"])
    kn(w, "a3", "SH", "B", **kw)
    assert key not in viewable_keys(w.db, a.user)


def test_acl_cap_cho_cong_ty_b_khong_khop_nho_kiem_nhiem(w):
    a = w.actor("a3")
    key = _acl_report(w, SUBJECT_COMPANY, w.co["B"])
    kn(w, "a3", "SH", "B")
    assert key not in viewable_keys(w.db, a.user)


def test_acl_van_ban_va_skill_ai_cung_khop_phong_kiem_nhiem(w):
    from app.modules.ai_skill.access_service import _match_condition
    from app.modules.ai_skill.model import AiSkillAccess

    a = w.actor("a3")
    w.db.add(DocumentAccess(document_id=77, subject_kind=SUBJECT_DEPARTMENT, subject_id=w.dept["SH"]))
    w.db.add(AiSkillAccess(target_id=5, subject_kind=SUBJECT_DEPARTMENT, subject_id=w.dept["SH"]))
    w.db.commit()

    def hit() -> tuple[bool, bool]:
        prof = a.profile()
        doc = w.db.query(DocumentAccess).filter(subject_match_condition(DocumentAccess, prof)).count() > 0
        cond = _match_condition(w.db, a.user, prof)
        skill = cond is not None and w.db.query(AiSkillAccess).filter(cond).count() > 0
        return doc, skill

    assert hit() == (False, False)
    kn(w, "a3", "SH", "B")
    assert hit() == (True, True)


def test_chot_tu_cap_quyen_bao_cao_chan_nguoi_kiem_nhiem_cap_cho_phong_x(w):
    a = w.actor("a3")
    body = ReportAccessGrantIn(subjects=[ReportAccessSubjectIn(subject_kind=SUBJECT_DEPARTMENT,
                                                               subject_id=w.dept["SH"])])
    block_self_allow_grant(w.db, body, a.user)       # chưa kiêm nhiệm: qua
    kn(w, "a3", "SH", "B")
    with pytest.raises(HTTPException) as e:
        block_self_allow_grant(w.db, body, a.user)
    assert e.value.status_code == 403


# ── 7. Q1: `include_concurrent` (chỉ đọc, mặc định tắt) ──────────────────────

def test_q1_truong_phong_bac_dept_o_cap_doc_duoc_ho_so_nguoi_kiem_nhiem(w):
    """a2 chính ở A; có dòng (B.kt, B). b1 là trưởng phòng bậc `dept` ở (B.kt, B)."""
    b = w.grant("b1", "employee", "dept", actions=("read", "write"))
    kn(w, "a2", "B.kt", "B")
    eid = w.emp["a2"]
    assert not b.can_get(Employee, eid)                                       # cờ tắt: không thấy
    prof = b.profile()
    got = get_scoped(w.db, Employee, "employee", eid, b.user, prof, "read", include_concurrent=True)
    assert got is not None and got.id == eid
    # chỉ ĐỌC: sửa vẫn theo vị trí chính
    assert get_scoped(w.db, Employee, "employee", eid, b.user, prof, "write", include_concurrent=True) is None
    # danh sách mặc định không đổi; bật cờ thì thêm đúng người này
    assert eid not in {r.id for r in apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof).all()}
    assert eid in {r.id for r in apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof,
                                             include_concurrent=True).all()}


def test_q1_bac_company_o_b_cung_doc_duoc_nhung_khong_mo_nguoi_khong_kiem_nhiem(w):
    b = w.grant("b1", "employee", "company")
    kn(w, "a2", "B.hc", "B")
    prof = b.profile()
    ids = {r.id for r in apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof,
                                     include_concurrent=True).all()}
    assert w.emp["a2"] in ids
    assert w.emp["a1"] not in ids and w.emp["a3"] not in ids        # không kiêm nhiệm ở B: vẫn ngoài tầm


@pytest.mark.parametrize("kw", [{"counts_scope": False}, {"to_date": YESTERDAY}, {"from_date": TOMORROW}],
                         ids=["tat-cong-tac", "het-han", "sap-toi"])
def test_q1_khong_doc_khi_dong_khong_hieu_luc(w, kw):
    b = w.grant("b1", "employee", "dept")
    kn(w, "a2", "B.kt", "B", **kw)
    assert get_scoped(w.db, Employee, "employee", w.emp["a2"], b.user, b.profile(), "read",
                      include_concurrent=True) is None


def _viewer(w, key, company_key, dept_key):
    """Dựng thêm một người xem có tài khoản ở (công ty, phòng) chỉ định."""
    from scope_factory import Actor
    emp = Employee(code=key.upper(), full_name=f"Người xem {key}", company_id=w.co[company_key],
                   department_id=w.dept[dept_key], is_active=True)
    w.db.add(emp)
    w.db.flush()
    user = User(email=key, employee_id=emp.id, password_hash="x", is_active=True)
    w.db.add(user)
    w.db.flush()
    w.emp[key] = emp.id
    w._actors[key] = Actor(w, key, user, emp)
    return w._actors[key]


def _read_with_flag(w, viewer, target_key):
    return get_scoped(w.db, Employee, "employee", w.emp[target_key], viewer.user, viewer.profile(), "read",
                      include_concurrent=True)


def test_q1_nguoi_xem_chi_phu_cap_khac_khong_doc_duoc(w):
    """Dòng ở (B.kt, B): người xem chỉ phủ (B.hc, B) KHÔNG đọc được. Đối chứng: phủ (B.kt, B) thì được."""
    kn(w, "a2", "B.kt", "B")
    only_hc = _viewer(w, "v_hc", "B", "B.hc")
    only_hc.grant("employee", "dept")
    assert _read_with_flag(w, only_hc, "a2") is None
    ok = _viewer(w, "v_kt", "B", "B.kt")
    ok.grant("employee", "dept")
    assert _read_with_flag(w, ok, "a2") is not None


def test_q1_phong_dung_chung_dong_x_b_khong_mo_cho_nguoi_xem_x_c(w):
    """c1 chính ở (C, SH). Dòng của a3 ở (SH, B): KHÔNG đọc được; dòng (SH, C) thì đọc được (đối chứng)."""
    c1 = w.grant("c1", "employee", "dept")
    kn(w, "a3", "SH", "B")
    assert _read_with_flag(w, c1, "a3") is None
    kn(w, "a3", "SH", "C")
    assert _read_with_flag(w, c1, "a3") is not None


def test_q1_nguoi_xem_co_cap_rieng_doc_duoc_hoso_cung_cap(w):
    """Người xem chính ở A nhưng có cặp (B.kt, B): đọc được hồ sơ người có dòng (B.kt, B), không đọc dòng (B.hc, B)."""
    v = w.grant("a1", "employee", "dept")
    kn(w, "a1", "B.kt", "B")
    kn(w, "a3", "B.kt", "B")                 # a3 chính ở A.mua: ngoài phạm vi chính của a1
    kn(w, "khongphong", "B.hc", "B")
    assert _read_with_flag(w, v, "a3") is not None
    assert _read_with_flag(w, v, "khongphong") is None
    assert v.can_get(Employee, w.emp["a3"]) is False        # cờ tắt: vẫn không


def test_q1_cap_va_co_chi_ap_cho_employee_read(w):
    """Entity khác bật cờ cũng không đổi: SQL y hệt."""
    a = w.grant("a2", "purchase_request", "dept")
    prof = a.profile()
    off = str(scope_condition(PurchaseRequest, "purchase_request", a.user, prof))
    on = str(scope_condition(PurchaseRequest, "purchase_request", a.user, prof, include_concurrent=True))
    assert off == on
    e = w.grant("a2", "employee", "dept", actions=("read", "write"))
    off_w = str(scope_condition(Employee, "employee", e.user, e.profile(), "write"))
    on_w = str(scope_condition(Employee, "employee", e.user, e.profile(), "write", include_concurrent=True))
    assert off_w == on_w


def test_q1_scope_all_giu_none_va_khong_phu_gi_khi_khong_co_quyen(w):
    allv = w.grant("a1", "employee", "all")
    assert scope_condition(Employee, "employee", allv.user, allv.profile(), include_concurrent=True) is None
    none = w.actor("a3")      # chưa cấp quyền employee nào
    cond = scope_condition(Employee, "employee", none.user, none.profile(), include_concurrent=True)
    assert str(cond).strip() == "false"


def test_q1_so_truy_van_danh_sach_50_ho_so_bang_khi_tat_co(w):
    b = w.grant("b1", "employee", "dept")
    for i in range(50):
        e = Employee(code=f"BULK{i}", full_name=f"Bulk {i}", company_id=w.co["B"], department_id=w.dept["B.hc"],
                     is_active=True)
        w.db.add(e)
        w.db.flush()
        w.db.add(EmployeeConcurrent(employee_id=e.id, company_id=w.co["B"], department_id=w.dept["B.kt"],
                                    from_date=TODAY))
    w.db.commit()
    prof = b.profile()

    def run(flag: bool) -> tuple[int, int]:
        n = []
        listener = lambda *a, **k: n.append(1)  # noqa: E731
        engine = w.db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            rows = apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof,
                               include_concurrent=flag).all()
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(rows), len(n)

    off_rows, off_queries = run(False)
    on_rows, on_queries = run(True)
    assert off_queries == on_queries == 1
    assert on_rows == off_rows + 50          # 50 người chính ở B.hc, kiêm nhiệm B.kt (b1 phủ B.kt)


# ── 8. `concurrent_row_scope_condition` (cho giai đoạn 05) ───────────────────

def _visible_rows(w, actor, action="read") -> set[int]:
    cond = concurrent_row_scope_condition(actor.user, actor.profile(), action)
    q = w.db.query(EmployeeConcurrent)
    return {r.id for r in (q if cond is None else q.filter(cond)).all()}


def test_dong_kiem_nhiem_truong_phong_x_b_thay_dong_x_b_khong_thay_dong_y_b(w):
    r_kt = kn(w, "a2", "B.kt", "B")
    r_hc = kn(w, "a3", "B.hc", "B")
    b = w.grant("b1", "employee", "dept")                   # b1 chính ở (B.kt, B)
    assert _visible_rows(w, b) == {r_kt.id}
    assert r_hc.id not in _visible_rows(w, b)


def test_dong_kiem_nhiem_bac_company_va_all_va_khong_quyen(w):
    r_kt = kn(w, "a2", "B.kt", "B")
    r_a = kn(w, "a3", "A.kt", "A")
    comp = w.grant("b1", "employee", "company")
    assert _visible_rows(w, comp) == {r_kt.id}              # chỉ công ty B
    allv = w.grant("a1", "employee", "all")
    assert concurrent_row_scope_condition(allv.user, allv.profile()) is None
    assert _visible_rows(w, allv) == {r_kt.id, r_a.id}
    nobody = w.actor("a3")
    assert _visible_rows(w, nobody) == set()


def test_dong_kiem_nhiem_loai_tru_cong_ty_va_chon_cong_ty_an_theo_dong(w):
    r_kt = kn(w, "a2", "B.kt", "B")
    inc = w.grant("b1", "employee", "dept", inc_company=["B"])
    assert _visible_rows(w, inc) == {r_kt.id}
    exc = w.grant("a1", "employee", "all", exc_company=["B"])
    assert r_kt.id not in _visible_rows(w, exc)


def test_dong_kiem_nhiem_loai_tru_dich_danh_nhan_su_theo_luat_cua_ho_so(w):
    """Loại trừ đích danh KHÔNG có chiều `owner` ở entity `employee` (`SCOPE_FIELDS["employee"]` không khai) nên hồ sơ
    chính cũng KHÔNG bị loại: dòng kiêm nhiệm đi cùng luật của hồ sơ, không thêm không bớt. Bài này chốt cả hai vế để
    ngày nào ai thêm `owner` cho `employee`, dòng kiêm nhiệm phải đổi theo (adapter chưa khai `created_by`)."""
    r_kt = kn(w, "a2", "B.kt", "B")
    a1 = w.grant("a1", "employee", "company", exc_employee=["a2"])
    assert w.emp["a2"] in a1.sees(Employee, "employee")        # luật gốc: ô loại trừ nhân sự bị bỏ qua ở `employee`
    b = w.grant("b1", "employee", "company", exc_employee=["a2"])
    assert r_kt.id in _visible_rows(w, b)                       # dòng kiêm nhiệm: cùng luật


# ── 9. Canh khai báo ─────────────────────────────────────────────────────────

def test_canh_moi_entity_co_dept_id_deu_co_company():
    """Cặp (phòng, công ty) chỉ ràng được khi entity có cột công ty. Thêm entity có phòng mà thiếu công ty thì
    cặp kiêm nhiệm KHÔNG cộng được ở entity đó (thiếu quyền, không lộ) — nhưng phải biết để khai thêm."""
    missing = [e for e, f in SCOPE_FIELDS.items()
               if f is not PUBLIC and f.get("dept_id") and not f.get("company")]
    assert missing == [], f"entity có dept_id mà không có company: {missing}"


def test_canh_entity_khong_co_cot_cong_ty_khong_nhan_cap(w):
    """Entity có phòng mà không có công ty (giả lập) → `_pair_conds` không cộng gì."""
    from app.core.scoping import _pair_conds
    assert _pair_conds(PurchaseRequest, {"dept_id": "department_id"}, [(1, 2)], lambda ids: ids) == []
    assert _pair_conds(PurchaseRequest, {"company": "company_id"}, [], lambda ids: ids) == []
