"""duoc-CR-756 giai đoạn 02 — PHẠM VI QUYỀN + đọc hồ sơ + chủ thể theo mô hình HAI LOẠI DÒNG ĐỘC LẬP.

Mô hình: dòng loại PHÒNG BAN (phòng của công ty hiện tại, `company_id` = công ty chính) vào `dept_ids` như cũ; dòng loại
CÔNG TY B (khác công ty chính, không phòng) vào `concurrent_companies` và được tính như công ty của người đó THEO BẬC:
  `company` → công ty IN (chính, *B);  `dept` → công ty IN (chính, *B) AND phòng IN dept_ids;  `own` / `all` /
  `dept_proc` KHÔNG đổi.

Cảnh (xem `kiem_nhiem_factory`): p = a2 chính ở (A, phòng dùng chung SH). Mỗi chốt có cặp đối chứng ở chiều ngược —
chặn sạch thì bài nào cũng xanh.
"""
import logging

import pytest
from fastapi import HTTPException
from sqlalchemy import event

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.report_keys import ReportKey
from app.core.scoping import apply_scope, get_scoped, holds_handling_dept, scope_condition
from app.core.subject_match import (EFFECT_ALLOW, SUBJECT_COMPANY, SUBJECT_DEPARTMENT, subject_match_condition,
                                    subject_pairs)
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.folder_access_service import company_reach
from app.modules.document.access_model import DocumentAccess
from app.modules.employee import concurrent_members_service as members
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.employee.service import clear_perm_cache_of
from app.modules.leave.request_model import LeaveRequest
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.report_access.grant_guards import block_self_allow_grant
from app.modules.report_access.model import ReportAccess
from app.modules.report_access.schema import ReportAccessGrantIn, ReportAccessSubjectIn
from app.modules.report_access.service import viewable_keys
from hdld_factory import client_as  # noqa: F401
from kiem_nhiem_factory import DAY, TODAY, add_employee, build_kn_world, kc, kn

OFF_KW = [{"counts_scope": False}, {"to_date": TODAY - DAY}, {"from_date": TODAY + DAY}]
OFF_IDS = ["tat-cong-tac", "het-han-hom-qua", "sap-toi-ngay-mai"]


@pytest.fixture()
def w(world):
    return build_kn_world(world)


def pr(w, code, company_key, dept_key, **kw) -> int:
    row = PurchaseRequest(code=code, company_id=w.co[company_key], department_id=w.dept[dept_key],
                          status=kw.pop("status", "approved"), created_by=w.user_id("b1"),
                          requester_id=w.emp["b1"], **kw)
    w.db.add(row)
    w.db.commit()
    return row.id


def leave(w, code, company_key, dept_key) -> int:
    row = LeaveRequest(code=code, company_id=w.co[company_key], department_id=w.dept[dept_key],
                       employee_id=w.emp["b1"], leave_type_id=1, from_date=TODAY, to_date=TODAY, total_days=1.0,
                       reason="r", status="submitted", created_by=w.user_id("b1"))
    w.db.add(row)
    w.db.commit()
    return row.id


def count_queries(w, fn) -> int:
    """Số truy vấn của `fn()` — ĐO LƯỢT THỨ HAI: lượt đầu nạp lại đối tượng hết hạn sau `commit` (không dính tới mã
    đang kiểm). Cache quyền xóa trước mỗi lượt để đo lần dựng từ đầu."""
    perm_cache_clear()
    fn()
    perm_cache_clear()
    n: list[int] = []
    listener = lambda *a, **k: n.append(1)  # noqa: E731
    engine = w.db.get_bind()
    event.listen(engine, "before_cursor_execute", listener)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    return len(n)


# ── 1. Hồ sơ quyền: hai loại dòng ────────────────────────────────────────────

def test_ho_so_quyen_loai_phong_ban_vao_dept_ids_loai_cong_ty_vao_concurrent_companies(w):
    w.grant("a2", "purchase_request", "dept")
    kn(w, "a2", "A.mua")                  # loại 1, phòng của công ty chính
    kc(w, "a2", "B")
    kc(w, "a2", "B", from_date=TODAY - 5 * DAY)   # trùng công ty, dòng khác
    kc(w, "a2", "C")
    kc(w, "a2", "A")                      # trùng công ty CHÍNH (dữ liệu trôi): bỏ
    prof = w.actor("a2").profile()
    assert prof["company_id"] == w.co["A"]                              # company_id vẫn MỘT số
    assert prof["dept_ids"] == [w.dept["SH"], w.dept["A.mua"]]          # phòng chính đứng đầu
    assert prof["concurrent_companies"] == sorted([w.co["B"], w.co["C"]])
    assert "concurrent_pairs" not in prof


def test_dong_phong_ban_cong_ty_0_la_phong_dung_chung_van_vao_dept_ids(w):
    w.grant("a2", "purchase_request", "dept")
    w.db.add(EmployeeConcurrent(employee_id=w.emp["a2"], kind=1, department_id=w.dept["A.mua"], company_id=0,
                                from_date=TODAY - DAY))
    w.db.commit()
    perm_cache_clear()
    assert w.dept["A.mua"] in w.actor("a2").profile()["dept_ids"]


def test_dong_phong_ban_lech_cong_ty_chinh_bi_bo_qua_va_ghi_log(w, caplog):
    """Dữ liệu trôi (đổi pháp nhân mà dòng loại 1 không kết thúc): nối vào dept_ids là mở phòng đó ở công ty CHÍNH."""
    w.grant("a2", "purchase_request", "dept")
    w.db.add(EmployeeConcurrent(employee_id=w.emp["a2"], kind=1, department_id=w.dept["B.kt"],
                                company_id=w.co["B"], from_date=TODAY - DAY))
    w.db.commit()
    perm_cache_clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        prof = w.actor("a2").profile()
    assert prof["dept_ids"] == [w.dept["SH"]] and prof["concurrent_companies"] == []
    assert any("lech cong ty chinh" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("kw", OFF_KW, ids=OFF_IDS)
def test_dong_khong_hieu_luc_khong_vao_ho_so_quyen(w, kw):
    kc(w, "a2", "B", **kw)
    kn(w, "a2", "A.mua", **kw)
    prof = w.actor("a2").profile()
    assert prof["concurrent_companies"] == [] and prof["dept_ids"] == [w.dept["SH"]]


def test_so_truy_van_ho_so_quyen_khong_tang_theo_so_dong_ca_hai_loai(w):
    """0, 1 và 5 dòng kiêm nhiệm: cùng số truy vấn (đúng MỘT truy vấn đọc dòng)."""
    w.grant("a2", "purchase_request", "dept")
    user = w.actor("a2").user
    counts = [count_queries(w, lambda: get_perm_profile(w.db, user))]
    kc(w, "a2", "B")
    counts.append(count_queries(w, lambda: get_perm_profile(w.db, user)))
    kc(w, "a2", "C")
    kn(w, "a2", "A.mua")
    kn(w, "a2", "A.kt")
    kn(w, "a2", "SH")
    counts.append(count_queries(w, lambda: get_perm_profile(w.db, user)))
    assert counts[0] == counts[1] == counts[2], counts         # số truy vấn không tăng theo số dòng


# ── 2. Bậc `company` ─────────────────────────────────────────────────────────

def test_company_thay_moi_phieu_cua_cong_ty_b_khong_thay_cong_ty_c(w):
    a = w.grant("a2", "purchase_request", "company")
    in_a, in_b1, in_b2, in_c = (pr(w, "PA", "A", "A.kt"), pr(w, "PB1", "B", "B.kt"), pr(w, "PB2", "B", "B.hc"),
                                pr(w, "PC", "C", "C.kt"))
    assert a.sees(PurchaseRequest) == {in_a}                     # chưa kiêm nhiệm: chỉ công ty chính
    kc(w, "a2", "B")
    assert a.sees(PurchaseRequest) == {in_a, in_b1, in_b2}       # thấy MỌI phiếu của B, vẫn không thấy C
    assert not a.can_get(PurchaseRequest, in_c) and a.can_get(PurchaseRequest, in_b2)


def test_company_ap_cho_don_nghi_nhan_su_va_chung_tu_khac(w):
    a = w.grant("a2", "leave_request", "company")
    a.grant("employee", "company")
    l_b, l_c = leave(w, "LB", "B", "B.kt"), leave(w, "LC", "C", "C.kt")
    kc(w, "a2", "B")
    assert a.sees(LeaveRequest, "leave_request") == {l_b}
    assert l_c not in a.sees(LeaveRequest, "leave_request")
    emp_ids = a.sees(Employee, "employee")
    assert {w.emp["b1"], w.emp["y1"], w.emp["a1"]} <= emp_ids and w.emp["c1"] not in emp_ids


def test_company_chua_gan_phap_nhan_chinh_ma_co_cong_ty_kiem_nhiem_khong_bi_chan(w):
    a = w.grant("khongcty", "purchase_request", "company")
    in_b = pr(w, "PB", "B", "B.kt")
    assert a.sees(PurchaseRequest) == set()            # không gì cả: chặn như cũ
    kc(w, "khongcty", "B")
    assert a.sees(PurchaseRequest) == {in_b}


def test_company_loai_tru_cong_ty_b_o_o_pham_vi_thi_mat_b(w):
    a = w.grant("a2", "purchase_request", "company", exc_company=["B"])
    in_a, in_b = pr(w, "PA", "A", "A.kt"), pr(w, "PB", "B", "B.kt")
    kc(w, "a2", "B")
    assert a.sees(PurchaseRequest) == {in_a} and in_b not in a.sees(PurchaseRequest)


# ── 3. Bậc `dept` ────────────────────────────────────────────────────────────

def test_dept_thay_phong_cua_ho_o_b_khong_thay_phong_khac_o_b(w):
    a = w.grant("a2", "purchase_request", "dept")            # dept_ids = {SH}
    x_a, x_b, y_b, x_c, k_a = (pr(w, "XA", "A", "SH"), pr(w, "XB", "B", "SH"), pr(w, "YB", "B", "B.hc"),
                               pr(w, "XC", "C", "SH"), pr(w, "KA", "A", "A.kt"))
    assert a.sees(PurchaseRequest) == {x_a}                  # chưa kiêm nhiệm
    kc(w, "a2", "B")
    assert a.sees(PurchaseRequest) == {x_a, x_b}             # (SH, B) có; (B.hc, B), (SH, C), (A.kt, A) không
    assert not (a.can_get(PurchaseRequest, y_b) or a.can_get(PurchaseRequest, x_c) or a.can_get(PurchaseRequest, k_a))


def test_dept_phong_loai_1_cua_a_thay_ca_a_va_b(w):
    """Z = A.mua (loại 1, của A) → thấy (Z, A) và (Z, B): công ty IN (chính, B) AND phòng IN dept_ids."""
    a = w.grant("a2", "purchase_request", "dept")
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")
    z_a, z_b, z_c = pr(w, "ZA", "A", "A.mua"), pr(w, "ZB", "B", "A.mua"), pr(w, "ZC", "C", "A.mua")
    assert {z_a, z_b} <= a.sees(PurchaseRequest) and z_c not in a.sees(PurchaseRequest)


def test_dept_chi_dong_loai_1_khong_mo_cong_ty_khac(w):
    """Loại Phòng ban không kéo công ty B vào: (A.mua, B) không thấy khi chỉ có dòng loại 1."""
    a = w.grant("a2", "purchase_request", "dept")
    kn(w, "a2", "A.mua")
    assert a.sees(PurchaseRequest) == set()
    z_a, z_b = pr(w, "ZA", "A", "A.mua"), pr(w, "ZB", "B", "A.mua")
    assert a.sees(PurchaseRequest) == {z_a} and z_b not in a.sees(PurchaseRequest)


# ── 4. own / all / dept_proc không đổi ───────────────────────────────────────

def test_own_khong_doi_ke_ca_entity_own_roi_ve_company(w):
    own = w.grant("a2", "purchase_request", "own")
    own.grant("company", "own")                  # entity `company` không có cột chủ → `own` rơi về `company` (chỉ công ty chính)
    mine = pr(w, "MINE", "B", "B.kt")
    w.db.get(PurchaseRequest, mine).created_by = w.user_id("a2")
    w.db.commit()
    other = pr(w, "OTHER", "B", "B.hc")
    before = own.sees(Company, "company")
    assert before == {w.co["A"]}
    kc(w, "a2", "B")
    assert own.sees(PurchaseRequest, "purchase_request") == {mine}
    assert other not in own.sees(PurchaseRequest, "purchase_request")
    assert own.sees(Company, "company") == {w.co["A"]}              # KHÔNG phình sang B
    comp = w.grant("a2", "company", "company")                      # đối chứng: bậc company thì B vào
    assert comp.sees(Company, "company") == {w.co["A"], w.co["B"]}


def test_all_khong_doi(w):
    a = w.grant("a2", "purchase_request", "all")
    kc(w, "a2", "B")
    assert scope_condition(PurchaseRequest, "purchase_request", a.user, a.profile()) is None


def test_dept_proc_ycmh_khong_doi_so_voi_nguoi_khong_kiem_nhiem(w):
    """`dept_proc` vốn không ràng công ty (bao-CR-434): cộng công ty kiêm nhiệm không đổi gì."""
    a = w.grant("a2", "purchase_request", "dept_proc")
    handled = [pr(w, f"H{co}", co, "B.hc" if co == "B" else "A.kt", handler_dept_id=w.dept["SH"]) for co in "ABC"]
    pr(w, "NO", "B", "B.hc", handler_dept_id=w.dept["B.hc"])
    before = a.sees(PurchaseRequest)
    assert before == set(handled)
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")
    after = a.sees(PurchaseRequest)
    assert after == before


def test_dept_proc_entity_khac_roi_ve_dept_khong_cong_cong_ty(w):
    """Đơn nghỉ không phải chứng từ thu mua: `dept_proc` rơi về `_dept_match` thuần — công ty kiêm nhiệm không cộng."""
    a = w.grant("a2", "leave_request", "dept_proc")
    l_a, l_b = leave(w, "LA", "A", "SH"), leave(w, "LB", "B", "SH")
    before = a.sees(LeaveRequest, "leave_request")
    kc(w, "a2", "B")
    assert a.sees(LeaveRequest, "leave_request") == before and {l_a, l_b} <= before


def test_holds_handling_dept_chi_theo_dept_ids_khong_theo_cong_ty_kiem_nhiem(w):
    from types import SimpleNamespace
    a = w.grant("a3", "purchase_request", "dept_proc", actions=("read", "approve"))
    kc(w, "a3", "B")
    phieu = SimpleNamespace(handler_dept_id=w.dept["SH"], company_id=w.co["B"], department_id=0)
    assert holds_handling_dept(a.profile(), "purchase_request", phieu) is False       # SH không phải phòng của a3
    own = SimpleNamespace(handler_dept_id=w.dept["A.mua"], company_id=w.co["C"], department_id=0)
    assert holds_handling_dept(a.profile(), "purchase_request", own) is True          # phòng chính, không ràng công ty


# ── 5. Hết hiệu lực / công tắc / cache ───────────────────────────────────────

@pytest.mark.parametrize("kw", OFF_KW, ids=OFF_IDS)
def test_dong_khong_hieu_luc_mat_b_o_ca_hai_bac(w, kw):
    a = w.grant("a2", "purchase_request", "company")
    d = w.grant("a1", "purchase_request", "dept")
    kc(w, "a2", "B", **kw)
    kc(w, "a1", "B", **kw)
    in_b = pr(w, "PB", "B", "B.kt")
    in_b_a1 = pr(w, "PBA", "B", "A.kt")
    assert in_b not in a.sees(PurchaseRequest) and in_b_a1 not in d.sees(PurchaseRequest)


def test_cache_sua_dong_roi_clear_perm_cache_of_thi_thay_ngay(w):
    a = w.grant("a2", "purchase_request", "company")
    row = kc(w, "a2", "B")
    in_b = pr(w, "PB", "B", "B.kt")
    assert in_b in a.sees(PurchaseRequest)                 # nạp cache
    row.to_date = TODAY - DAY
    w.db.commit()
    assert in_b in a.sees(PurchaseRequest)                 # cache chưa xóa: vẫn bản cũ (60 giây)
    clear_perm_cache_of(w.db, w.emp["a2"])
    assert in_b not in a.sees(PurchaseRequest)


# ── 6. Chủ thể ACL (subject_match) ───────────────────────────────────────────

def _acl_report(w, subject_kind, subject_id, key=ReportKey(list(ReportKey)[0])):
    w.db.add(ReportAccess(report_key=int(key), subject_kind=subject_kind, subject_id=subject_id,
                          effect=EFFECT_ALLOW))
    w.db.commit()
    return int(key)


def test_subject_pairs_cong_chu_the_cong_ty_b_khong_cong_phong_cua_cap_khac_cong_ty(w):
    a = w.actor("a2")
    kc(w, "a2", "B")
    kc(w, "a2", "B", from_date=TODAY - DAY)                # trùng: một cặp
    kn(w, "a2", "A.mua")
    pairs = subject_pairs(a.profile())
    assert pairs.count((SUBJECT_COMPANY, w.co["B"])) == 1 and (SUBJECT_COMPANY, w.co["A"]) in pairs
    assert (SUBJECT_DEPARTMENT, w.dept["A.mua"]) in pairs and (SUBJECT_DEPARTMENT, w.dept["B.kt"]) not in pairs


def test_acl_bao_cao_chia_cho_cong_ty_b_khop_nguoi_kiem_nhiem_b(w):
    a = w.actor("a2")
    key = _acl_report(w, SUBJECT_COMPANY, w.co["B"])
    assert key not in viewable_keys(w.db, a.user)
    kc(w, "a2", "B")
    assert key in viewable_keys(w.db, a.user)


@pytest.mark.parametrize("kw", OFF_KW, ids=OFF_IDS)
def test_acl_mat_khi_dong_het_hieu_luc_hoac_tat_cong_tac(w, kw):
    a = w.actor("a2")
    key = _acl_report(w, SUBJECT_COMPANY, w.co["B"])
    kc(w, "a2", "B", **kw)
    assert key not in viewable_keys(w.db, a.user)


def test_acl_van_ban_va_skill_ai_chia_cho_cong_ty_b_khop_nguoi_kiem_nhiem(w):
    from app.modules.ai_skill.access_service import _match_condition
    from app.modules.ai_skill.model import AiSkillAccess

    a = w.actor("a2")
    w.db.add(DocumentAccess(document_id=77, subject_kind=SUBJECT_COMPANY, subject_id=w.co["B"]))
    w.db.add(AiSkillAccess(target_id=5, subject_kind=SUBJECT_COMPANY, subject_id=w.co["B"]))
    w.db.commit()

    def hit() -> tuple[bool, bool]:
        prof = a.profile()
        doc = w.db.query(DocumentAccess).filter(subject_match_condition(DocumentAccess, prof)).count() > 0
        cond = _match_condition(w.db, a.user, prof)
        skill = cond is not None and w.db.query(AiSkillAccess).filter(cond).count() > 0
        return doc, skill

    assert hit() == (False, False)
    kc(w, "a2", "B")
    assert hit() == (True, True)


def test_chot_tu_cap_quyen_bao_cao_chan_nguoi_kiem_nhiem_cap_cho_cong_ty_b(w):
    a = w.actor("a2")
    body = ReportAccessGrantIn(subjects=[ReportAccessSubjectIn(subject_kind=SUBJECT_COMPANY,
                                                               subject_id=w.co["B"])])
    block_self_allow_grant(w.db, body, a.user)             # chưa kiêm nhiệm B: qua
    kc(w, "a2", "B")
    with pytest.raises(HTTPException) as e:
        block_self_allow_grant(w.db, body, a.user)
    assert e.value.status_code == 403


# ── 7. company_reach (tạo văn bản / thư mục cho công ty nào) ─────────────────

@pytest.mark.parametrize("scope,expected", [
    ("company", True), ("dept", True), ("dept_proc", True), ("own", False), ("assigned", False), ("proc", False)])
def test_company_reach_cong_cong_ty_kiem_nhiem_cho_ba_bac(w, scope, expected):
    a = w.grant("a2", "document", scope, actions=("read", "create"))
    kc(w, "a2", "B")
    got = company_reach(a.profile(), "document", "create")
    assert got == ({w.co["A"], w.co["B"]} if expected else {w.co["A"]})


def test_company_reach_all_van_none_va_tat_cong_tac_mat_b(w):
    allp = w.grant("a1", "document", "all", actions=("read", "create"))
    kc(w, "a1", "B")
    assert company_reach(allp.profile(), "document", "create") is None
    d = w.grant("a2", "document", "dept", actions=("create",))
    kc(w, "a2", "B", counts_scope=False)
    assert company_reach(d.profile(), "document", "create") == {w.co["A"]}


# ── 8. Q1: đọc hồ sơ người kiêm nhiệm (`include_concurrent`) ─────────────────

def read_with_flag(w, viewer, target_key="a2"):
    return get_scoped(w.db, Employee, "employee", w.emp[target_key], viewer.user, viewer.profile(), "read",
                      include_concurrent=True)


def test_q1_bac_company_o_b_doc_duoc_bac_dept_dung_phong_doc_duoc_phong_khac_khong(w):
    """p (A, SH) kiêm nhiệm công ty B → ngồi ở (SH, B)."""
    kc(w, "a2", "B")
    company_b = w.grant("b1", "employee", "company")
    same_dept = w.grant("hb", "employee", "dept")                  # (B, SH)
    other_dept = w.grant("y1", "employee", "dept")                 # (B, B.hc)
    other_company = w.grant("c1", "employee", "dept")              # (C, SH): cùng phòng dùng chung, khác công ty
    assert read_with_flag(w, company_b) is not None
    assert read_with_flag(w, same_dept) is not None
    assert read_with_flag(w, other_dept) is None
    assert read_with_flag(w, other_company) is None
    assert not company_b.can_get(Employee, w.emp["a2"])          # cờ tắt: không thấy


def test_q1_phong_loai_1_z_doc_duoc_o_ca_a_va_b(w):
    """p có thêm dòng loại 1 Z = A.mua → ngồi ở (Z, A) và (Z, B)."""
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")
    z_a = w.grant("a3", "employee", "dept")                         # (A, A.mua)
    add_employee(w, "zb", "B", "A.mua")
    w.db.commit()
    z_b = w.grant("zb", "employee", "dept")                         # (B, A.mua)
    assert read_with_flag(w, z_a) is not None                       # nhờ dòng loại 1
    assert read_with_flag(w, z_b) is not None                       # nhờ dòng loại 2 × dòng loại 1 (EXISTS)


def test_q1_phong_loai_1_z_khong_mo_neu_khong_co_dong_loai_2(w):
    """Chỉ dòng loại 1: người xem (B, A.mua) không đọc được — Z chỉ ngồi ở A."""
    kn(w, "a2", "A.mua")
    add_employee(w, "zb", "B", "A.mua")
    w.db.commit()
    assert read_with_flag(w, w.grant("zb", "employee", "dept")) is None
    assert read_with_flag(w, w.grant("a3", "employee", "dept")) is not None


@pytest.mark.parametrize("kw", OFF_KW, ids=OFF_IDS)
def test_q1_khong_doc_khi_dong_loai_2_khong_hieu_luc(w, kw):
    kc(w, "a2", "B", **kw)
    assert read_with_flag(w, w.grant("b1", "employee", "company")) is None


def test_q1_khong_doc_khi_dong_loai_1_chi_con_dong_phong_het_hieu_luc(w):
    """Dòng loại 2 còn hiệu lực nhưng dòng loại 1 Z đã hết hạn: (Z, B) không còn ngồi."""
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua", to_date=TODAY - DAY)
    add_employee(w, "zb", "B", "A.mua")
    w.db.commit()
    assert read_with_flag(w, w.grant("zb", "employee", "dept")) is None


def test_q1_chi_doc_danh_sach_khong_co_p_va_khong_ghi_duoc(w):
    kc(w, "a2", "B")
    b = w.grant("b1", "employee", "company", actions=("read", "write"))
    prof = b.profile()
    assert w.emp["a2"] not in {r.id for r in apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof).all()}
    assert get_scoped(w.db, Employee, "employee", w.emp["a2"], b.user, prof, "write", include_concurrent=True) is None
    on = {r.id for r in apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof,
                                    include_concurrent=True).all()}
    assert w.emp["a2"] in on and w.emp["c1"] not in on and w.emp["a1"] not in on


def test_q1_scope_all_la_none_va_khong_quyen_la_false(w):
    kc(w, "a2", "B")
    allv = w.grant("a1", "employee", "all")
    assert scope_condition(Employee, "employee", allv.user, allv.profile(), include_concurrent=True) is None
    nobody = w.actor("a3")
    assert str(scope_condition(Employee, "employee", nobody.user, nobody.profile(),
                               include_concurrent=True)).strip() == "false"


def test_q1_mot_cau_sql_so_truy_van_danh_sach_khong_tang_khi_bat_co(w):
    b = w.grant("b1", "employee", "company")
    for i in range(30):
        add_employee(w, f"bulk{i}", "A", "SH")
        w.db.flush()
        kc(w, f"bulk{i}", "B")
    prof = b.profile()

    def run(flag):
        n: list[int] = []
        listener = lambda *a, **k: n.append(1)  # noqa: E731
        engine = w.db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            rows = apply_scope(w.db.query(Employee), Employee, "employee", b.user, prof,
                               include_concurrent=flag).all()
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(rows), len(n)

    off_rows, off_q = run(False)
    on_rows, on_q = run(True)
    assert off_q == on_q == 1 and on_rows == off_rows + 30


# ── 9. Danh sách người kiêm nhiệm theo phòng / công ty ───────────────────────

def members_of(w, viewer, **kw):
    return members.list_visible_members(w.db, viewer.user, viewer.profile(), **kw)


def test_theo_cong_ty_loai_2_thay_dung_nguoi_theo_cho_ngoi(w):
    kc(w, "a2", "B", position_label="Phó phòng")
    for key, scope, sees in (("b1", "company", True), ("hb", "dept", True), ("y1", "dept", False),
                             ("c1", "dept", False)):
        viewer = w.grant(key, "employee", scope)
        got = members_of(w, viewer, company_id=w.co["B"], kind=2)
        assert [i["code"] for i in got] == (["A2"] if sees else []), key
    item = members_of(w, w.actor("b1"), company_id=w.co["B"], kind=2)[0]
    assert (item["kind"], item["kind_label"], item["department_id"], item["department_name"]) == (2, "Công ty", 0, "")
    assert (item["company_name"], item["position_label"], item["can_open"]) == ("Công ty B", "Phó phòng", True)
    assert item["primary_company_name"] == "Công ty A"


def test_theo_phong_loai_1_khong_ra_dong_loai_2_va_nguoc_lai(w):
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")
    a3 = w.grant("a3", "employee", "dept")                     # (A, A.mua)
    got = members_of(w, a3, department_id=w.dept["A.mua"], kind=1)
    assert [(i["kind"], i["department_id"]) for i in got] == [(1, w.dept["A.mua"])]
    assert members_of(w, a3, department_id=w.dept["A.mua"], kind=2) == []
    assert members_of(w, a3, department_id=w.dept["SH"]) == []      # dòng loại 2 có phòng 0: không ra khi lọc phòng
    all_kinds = members_of(w, w.grant("a1", "employee", "all"), company_id=w.co["B"])
    assert [i["kind"] for i in all_kinds] == [2]                    # loại 1 ở công ty A, không ở B


def test_dong_loai_2_ngoi_o_phong_loai_1_cua_chinh_nguoi_do(w):
    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")
    add_employee(w, "zb", "B", "A.mua")
    w.db.commit()
    assert [i["kind"] for i in members_of(w, w.grant("zb", "employee", "dept"), company_id=w.co["B"])] == [2]


def test_dong_loai_1_trung_phong_chinh_van_bi_bo_dong_loai_2_khong_bao_gio_trung(w):
    kn(w, "hb", "SH")                      # trùng cặp (phòng chính, công ty chính)
    kc(w, "a2", "B")
    v = w.grant("a1", "employee", "all")
    got = members_of(w, v, company_id=w.co["B"])
    assert [(i["code"], i["kind"]) for i in got] == [("A2", 2)]


def test_so_truy_van_danh_sach_theo_cong_ty_co_dinh(w):
    v = w.grant("b1", "employee", "company")
    kc(w, "a2", "B")
    one = count_queries(w, lambda: members_of(w, v, company_id=w.co["B"], kind=2))
    for i in range(20):
        add_employee(w, f"m{i}", "A", "SH")
        w.db.flush()
        kc(w, f"m{i}", "B")
    many = count_queries(w, lambda: members_of(w, v, company_id=w.co["B"], kind=2))
    assert len(members_of(w, v, company_id=w.co["B"], kind=2)) == 21
    assert many == one, (one, many)


def test_endpoint_can_it_nhat_mot_id_va_kind_hop_le(w, client_as):  # noqa: F811
    v = w.grant("b1", "employee", "company")
    kc(w, "a2", "B")
    c = client_as(v)
    ok = c.get("/api/employee-concurrents", params={"company_id": w.co["B"], "kind": 2})
    assert ok.status_code == 200 and ok.json()["data"]["total"] == 1
    assert c.get("/api/employee-concurrents").status_code == 422
    assert c.get("/api/employee-concurrents", params={"kind": 2}).status_code == 422
    assert c.get("/api/employee-concurrents", params={"company_id": w.co["B"], "kind": 3}).status_code == 422
    assert c.get("/api/employee-concurrents", params={"department_id": w.dept["SH"], "kind": 1}
                 ).json()["data"]["items"] == []


def test_mo_ta_dong_kiem_nhiem_hai_loai(w):
    kc(w, "a2", "B", position_label="Phó phòng")
    kn(w, "a2", "A.mua", position_label="Trưởng nhóm")
    roles = members.effective_roles_of(w.db, {w.emp["a2"]})[w.emp["a2"]]
    dept_name = w.db.get(Department, w.dept["A.mua"]).name
    assert [(r["kind"], r["kind_label"], r["text"]) for r in roles] == [
        (1, "Phòng ban", f"{dept_name} (Trưởng nhóm)"), (2, "Công ty", "Công ty B (Phó phòng)")]
    assert members.describe_concurrent(2, "", "Dego Organic", "") == "Công ty Dego Organic"
    assert members.describe_concurrent(2, "", "Công ty TNHH Dego", "Giám đốc") == "Công ty TNHH Dego (Giám đốc)"
    assert members.describe_concurrent(1, "Phòng Kế toán", "Công ty A", "") == "Phòng Kế toán"


def test_khong_con_thuoc_tinh_cap_phong_cong_ty_trong_ma_nguon():
    """`concurrent_pairs` đã bỏ hẳn: còn sót là có chỗ đọc khóa không ai dựng nữa."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2] / "backend" / "app"
    left = [str(p.relative_to(root)) for p in root.rglob("*.py") if "concurrent_pairs" in p.read_text(encoding="utf-8")]
    assert left == []
