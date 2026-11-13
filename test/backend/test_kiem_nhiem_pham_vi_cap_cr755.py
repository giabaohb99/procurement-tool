"""duoc-CR-755 giai đoạn 02 (chỉnh theo mô hình hai loại dòng ở duoc-CR-756) — PHẠM VI QUYỀN của kiêm nhiệm.

Phần phạm vi theo công ty kiêm nhiệm (bậc `company` / `dept`, hồ sơ quyền, ACL công ty, Q1 theo chỗ ngồi) nằm ở
`test_kiem_nhiem_doc_lap_cr756.py`. Tệp này giữ những luật bất biến của CR-755 vẫn đúng ở mô hình mới:

1. Dòng loại PHÒNG BAN hiệu lực + bật công tắc mở phòng đó như phòng của người này (`dept_ids`, hành vi y CR-167).
2. `dept_proc`, `_narrow_to_dept`, `_handler_match`, `holds_handling_dept` KHÔNG ràng công ty (bao-CR-434) nên dòng
   loại Công ty không đổi gì ở đó; người chưa gắn phòng vẫn bị chặn.
3. Q1 (đọc hồ sơ người kiêm nhiệm) mặc định TẮT, chỉ ĐỌC, chỉ cho entity `employee`.
4. Điều kiện nhìn dòng kiêm nhiệm (`concurrent_row_visible_condition`) theo chỗ ngồi của dòng.

Mỗi chốt có cặp đối chứng ở chiều ngược, vì chặn sạch thì bài nào cũng xanh.
"""
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.core.auth import perm_cache_clear
from app.core.scoping import (PUBLIC, SCOPE_FIELDS, concurrent_row_visible_condition, get_scoped, holds_handling_dept,
                              scope_condition)
from app.core.subject_match import SUBJECT_DEPARTMENT, subject_match_condition, subject_pairs
from app.modules.document.access_model import DocumentAccess
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import SurveyRequest
from kiem_nhiem_factory import DAY, TODAY, build_kn_world, kc, kn

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


# ── 1. Dòng loại Phòng ban: phòng của chính công ty chính ────────────────────

def test_dong_phong_ban_mo_dung_phong_o_cong_ty_chinh_bac_dept(w):
    a = w.grant("a2", "purchase_request", "dept")            # chính (A, SH)
    ok, tren_a, khac = pr(w, "OK", "A", "A.mua"), pr(w, "SH_A", "A", "SH"), pr(w, "SAI", "A", "A.kt")
    assert a.sees(PurchaseRequest) == {tren_a}
    kn(w, "a2", "A.mua")
    assert a.sees(PurchaseRequest) == {tren_a, ok} and khac not in a.sees(PurchaseRequest)


@pytest.mark.parametrize("kw", OFF_KW, ids=OFF_IDS)
def test_dong_phong_ban_khong_hieu_luc_khong_mo_gi(w, kw):
    a = w.grant("a3", "purchase_request", "dept")            # chính (A, A.mua)
    a.grant("purchase_request", "dept_proc")
    kn(w, "a3", "A.kt", **kw)
    x_dept = pr(w, "X1", "A", "A.kt")
    x_handler = pr(w, "X2", "A", "SH", handler_dept_id=w.dept["A.kt"])
    assert w.dept["A.kt"] not in a.profile()["dept_ids"]
    assert {x_dept, x_handler}.isdisjoint(a.sees(PurchaseRequest))
    assert subject_pairs(a.profile()).count((SUBJECT_DEPARTMENT, w.dept["A.kt"])) == 0


def test_dong_phong_ban_hieu_luc_mo_ca_nhanh_dept_lan_nhanh_handler(w):
    """Đối chứng của bài trên: cùng cảnh nhưng dòng CÒN hiệu lực thì cả hai phiếu hiện."""
    a = w.grant("a3", "purchase_request", "dept")
    a.grant("purchase_request", "dept_proc")
    kn(w, "a3", "A.kt")
    x_dept = pr(w, "X1", "A", "A.kt")
    x_handler = pr(w, "X2", "A", "SH", handler_dept_id=w.dept["A.kt"])
    assert {x_dept, x_handler} <= a.sees(PurchaseRequest)


def test_ngay_dau_va_ngay_cuoi_deu_con_hieu_luc(w):
    w.grant("a3", "purchase_request", "dept")
    kn(w, "a3", "A.kt", from_date=TODAY, to_date=TODAY)
    assert w.dept["A.kt"] in w.actor("a3").profile()["dept_ids"]


def test_gio_vn_00h30_tinh_dung_ngay_viet_nam(w, monkeypatch):
    """00:30 giờ VN ngày D = 17:30 UTC ngày D-1: dòng `from_date = D` PHẢI hiệu lực, `to_date = D-1` PHẢI hết."""
    from app.core import vn_time

    class FakeDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return datetime(2026, 11, 11, 17, 30)

    monkeypatch.setattr(vn_time, "datetime", FakeDatetime)
    w.grant("a3", "purchase_request", "dept")
    kn(w, "a3", "A.kt", from_date=date(2026, 11, 12))
    kc(w, "a3", "B", from_date=date(2026, 10, 1), to_date=date(2026, 11, 11))
    prof = w.actor("a3").profile()
    assert w.dept["A.kt"] in prof["dept_ids"] and prof["concurrent_companies"] == []


# ── 2. dept_proc / handler: không ràng công ty, dòng loại Công ty không đổi gì ──

def test_dept_proc_phong_chua_gan_van_bi_chan_du_co_cong_ty_kiem_nhiem(w):
    """Người chưa gắn phòng chính: công ty kiêm nhiệm không thay cho phòng, vẫn bị chặn (không mở oan)."""
    a = w.grant("khongphong", "purchase_request", "dept_proc")
    kc(w, "khongphong", "B")
    pr(w, "NO", "B", "B.hc", handler_dept_id=w.dept["SH"])
    assert a.sees(PurchaseRequest) == set()


def test_dept_proc_ycbg_va_dmh_khong_doi_khi_co_cong_ty_kiem_nhiem(w):
    a = w.grant("a3", "survey_request", "dept_proc")
    a.grant("purchase_order", "dept_proc")

    def sr(code, co):
        row = SurveyRequest(code=code, company_id=w.co[co], department_id=w.dept["A.kt"], status="processing",
                            handler_dept_id=w.dept["A.mua"], created_by=w.user_id("b1"), requester_id=w.emp["b1"])
        w.db.add(row)
        w.db.commit()
        return row.id

    def po(code, co):
        row = PurchaseOrder(code=code, company_id=w.co[co], status="approved", created_by=w.user_id("b1"),
                            department_id=w.dept["A.kt"], handler_dept_id=w.dept["A.mua"])
        w.db.add(row)
        w.db.commit()
        return row.id

    ids = {sr("SR_A", "A"), sr("SR_B", "B")}, {po("PO_A", "A"), po("PO_B", "B")}
    before = a.sees(SurveyRequest, "survey_request"), a.sees(PurchaseOrder, "purchase_order")
    assert before == ids                                       # phòng xử lý là phòng của a3, không ràng công ty
    kc(w, "a3", "B")
    assert (a.sees(SurveyRequest, "survey_request"), a.sees(PurchaseOrder, "purchase_order")) == before


def test_holds_handling_dept_theo_phong_cua_nguoi_dong_loai_1_cung_tinh(w):
    a = w.grant("a3", "purchase_request", "dept_proc", actions=("read", "approve"))
    phieu = SimpleNamespace(handler_dept_id=w.dept["A.kt"], company_id=w.co["A"], department_id=0)
    assert holds_handling_dept(a.profile(), "purchase_request", phieu) is False
    kn(w, "a3", "A.kt")
    assert holds_handling_dept(a.profile(), "purchase_request", phieu) is True


# ── 3. ACL theo phòng: dòng loại Phòng ban khớp, hết hiệu lực thì mất ────────

def test_acl_van_ban_chia_cho_phong_kiem_nhiem_loai_1(w):
    a = w.actor("a3")
    w.db.add(DocumentAccess(document_id=77, subject_kind=SUBJECT_DEPARTMENT, subject_id=w.dept["A.kt"]))
    w.db.commit()

    def hit() -> bool:
        return w.db.query(DocumentAccess).filter(subject_match_condition(DocumentAccess, a.profile())).count() > 0

    assert not hit()
    row = kn(w, "a3", "A.kt")
    assert hit() and subject_pairs(a.profile()).count((SUBJECT_DEPARTMENT, w.dept["A.kt"])) == 1
    row.counts_scope = False
    w.db.commit()
    perm_cache_clear()
    assert not hit()


# ── 4. Q1: cờ `include_concurrent` chỉ ĐỌC, chỉ entity `employee` ────────────

def test_q1_cap_va_co_chi_ap_cho_employee_read(w):
    """Entity khác bật cờ cũng không đổi: SQL y hệt. Ghi cũng không."""
    a = w.grant("a2", "purchase_request", "dept")
    kc(w, "a2", "B")
    prof = a.profile()
    assert str(scope_condition(PurchaseRequest, "purchase_request", a.user, prof)) == \
        str(scope_condition(PurchaseRequest, "purchase_request", a.user, prof, include_concurrent=True))
    e = w.grant("a2", "employee", "dept", actions=("read", "write"))
    assert str(scope_condition(Employee, "employee", e.user, e.profile(), "write")) == \
        str(scope_condition(Employee, "employee", e.user, e.profile(), "write", include_concurrent=True))


def test_q1_nguoi_xem_khac_cong_ty_khong_co_cho_ngoi_khong_doc_duoc(w):
    """p kiêm nhiệm B ngồi ở (SH, B): người xem chỉ phủ (B.hc, B) hoặc (SH, C) KHÔNG đọc được; (SH, B) thì được."""
    kc(w, "a2", "B")

    def read(viewer):
        return get_scoped(w.db, Employee, "employee", w.emp["a2"], viewer.user, viewer.profile(), "read",
                          include_concurrent=True)

    assert read(w.grant("y1", "employee", "dept")) is None
    assert read(w.grant("c1", "employee", "dept")) is None
    assert read(w.grant("hb", "employee", "dept")) is not None


# ── 5. Điều kiện nhìn dòng kiêm nhiệm theo chỗ ngồi ──────────────────────────

def _visible_rows(w, actor, action="read") -> set[int]:
    cond = concurrent_row_visible_condition(EmployeeConcurrent, Employee.department_id, actor.user, actor.profile(),
                                            action)
    q = w.db.query(EmployeeConcurrent).join(Employee, Employee.id == EmployeeConcurrent.employee_id)
    return {r.id for r in (q if cond is None else q.filter(cond)).all()}


def test_dong_loai_1_ngoi_o_phong_dong_loai_2_ngoi_o_phong_cua_nguoi_do_tai_cong_ty_b(w):
    r1 = kn(w, "a2", "A.mua")                         # ngồi (A.mua, A)
    r2 = kc(w, "a2", "B")                             # ngồi (SH, B) và (A.mua, B)
    assert _visible_rows(w, w.grant("a3", "employee", "dept")) == {r1.id}          # (A, A.mua): chỉ dòng loại 1
    assert _visible_rows(w, w.grant("hb", "employee", "dept")) == {r2.id}          # (B, SH)
    assert _visible_rows(w, w.grant("y1", "employee", "dept")) == set()            # (B, B.hc)
    assert _visible_rows(w, w.grant("c1", "employee", "dept")) == set()            # (C, SH)


def test_dong_kiem_nhiem_bac_company_all_va_khong_quyen(w):
    r_b = kc(w, "a2", "B")
    r_a = kn(w, "a2", "A.mua")
    assert _visible_rows(w, w.grant("b1", "employee", "company")) == {r_b.id}      # công ty B
    allv = w.grant("a1", "employee", "all")
    assert concurrent_row_visible_condition(EmployeeConcurrent, Employee.department_id, allv.user, allv.profile()) \
        is None
    assert _visible_rows(w, allv) == {r_a.id, r_b.id}
    assert _visible_rows(w, w.actor("a3")) == set()                                # chưa cấp quyền employee nào


def test_dong_kiem_nhiem_loai_tru_cong_ty_va_chon_cong_ty_an_theo_chi_cho_ngoi(w):
    r_b = kc(w, "a2", "B")
    assert _visible_rows(w, w.grant("b1", "employee", "company", inc_company=["B"])) == {r_b.id}
    assert r_b.id not in _visible_rows(w, w.grant("a1", "employee", "all", exc_company=["B"]))


def test_dong_kiem_nhiem_loai_tru_dich_danh_nhan_su_theo_luat_cua_ho_so(w):
    """`SCOPE_FIELDS["employee"]` không khai `owner` nên loại trừ đích danh bị bỏ qua ở hồ sơ; dòng kiêm nhiệm đi
    cùng luật đó (ngày nào thêm `owner` cho `employee` thì dòng phải đổi theo)."""
    r_b = kc(w, "a2", "B")
    a1 = w.grant("a1", "employee", "company", exc_employee=["a2"])
    assert w.emp["a2"] in a1.sees(Employee, "employee")
    assert r_b.id in _visible_rows(w, w.grant("b1", "employee", "company", exc_employee=["a2"]))


# ── 6. Canh khai báo ─────────────────────────────────────────────────────────

def test_canh_moi_entity_co_dept_id_deu_co_company():
    """Bậc `dept` ràng `công ty IN (...)` khi entity có cột công ty. Entity có phòng mà thiếu công ty thì công ty
    kiêm nhiệm không có chỗ ràng — phải biết để khai thêm."""
    missing = [e for e, f in SCOPE_FIELDS.items()
               if f is not PUBLIC and f.get("dept_id") and not f.get("company")]
    assert missing == [], f"entity có dept_id mà không có company: {missing}"
