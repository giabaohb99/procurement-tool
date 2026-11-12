"""duoc-CR-755 giai đoạn 03 — các ĐƯỜNG GHI kiêm nhiệm từ nơi khác: Áp quá trình công tác loại 4, giữ phòng cũ,
đổi pháp nhân chính (Q4), nhập Excel nhân sự và hoàn tác, chặn xóa chức vụ đang dùng, L2 cho dòng công ty = 0.

Tách khỏi `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py` (CRUD của tab) cho dễ đọc. Mỗi chốt có cặp đối chứng ở chiều ngược.
"""
import json
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.core.hr_work_history_codes import WorkEventType
from app.core.vn_time import vn_today
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.employee import concurrent_service, department_service as dv
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.service import update_employee, update_employee_core
from app.modules.employee.work_history_model import EmployeeWorkHistory

from test_nhap_excel_nhan_su_cr628 import emp, errors, hr, make_wb, run_import  # noqa: F401

ACTOR = 1
TODAY = vn_today()
YESTERDAY = TODAY - timedelta(days=1)


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng dữ liệu
# ══════════════════════════════════════════════════════════════════════════════

def _conc(db, eid, company, dept, **kw) -> EmployeeConcurrent:
    kw.setdefault("from_date", TODAY - timedelta(days=10))
    row = EmployeeConcurrent(employee_id=eid, company_id=company, department_id=dept, counts_scope=True,
                             created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _fresh(db, row) -> EmployeeConcurrent:
    db.expire_all()
    return db.get(EmployeeConcurrent, row.id)


def _wh(db, eid, event_type, from_date, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _rows_of(db, eid) -> list[EmployeeConcurrent]:
    db.expire_all()
    return db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == eid).order_by(
        EmployeeConcurrent.id).all()


@pytest.fixture
def move(world):
    """a3 (công ty A) có 5 dòng kiêm nhiệm để thử đổi pháp nhân A -> C:
    ở A: đang hiệu lực / đã hết / chưa bắt đầu; ở B: đang hiệu lực (công ty KHÁC, không bao giờ bị đụng)."""
    db = world.db
    c_new = Company(code="CTY_C", name="Công ty C", is_active=True)
    db.add(c_new)
    db.flush()
    eid, co_a, co_b = world.emp["a3"], world.co["A"], world.co["B"]
    rows = {
        "open": _conc(db, eid, co_a, world.dept["A.kt"]),
        "ended": _conc(db, eid, co_a, world.dept["A.kt"], from_date=TODAY - timedelta(days=100),
                       to_date=TODAY - timedelta(days=50)),
        "future": _conc(db, eid, co_a, world.dept["B.hc"],
                        from_date=TODAY + timedelta(days=5)),
        "b": _conc(db, eid, co_b, world.dept["B.kt"]),
    }
    return {"world": world, "eid": eid, "c_new": c_new.id, "rows": rows, "co_a": co_a, "co_b": co_b}


# ══════════════════════════════════════════════════════════════════════════════
#  1. Đổi pháp nhân chính (Q4)
# ══════════════════════════════════════════════════════════════════════════════

def test_doi_phap_nhan_ket_thuc_dong_cong_ty_cu_xoa_dong_chua_bat_dau_khong_dung_dong_cong_ty_khac(move):
    w, rows = move["world"], move["rows"]
    update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c_new"], department_id=0), ACTOR)

    assert _fresh(w.db, rows["open"]).to_date == YESTERDAY, "dòng còn hiệu lực ở công ty cũ kết thúc hôm qua"
    assert _fresh(w.db, rows["ended"]).to_date == TODAY - timedelta(days=50), "dòng đã hết giữ nguyên ngày"
    assert w.db.get(EmployeeConcurrent, rows["future"].id) is None, "dòng chưa bắt đầu bị xóa"
    other = _fresh(w.db, rows["b"])
    assert other.to_date is None and other.company_id == move["co_b"], "dòng ở công ty khác không bị đụng"
    assert concurrent_service.active_concurrent_rows(w.db, move["eid"]) == [other]


def test_doi_phap_nhan_ghi_nhat_ky_dong_da_ket_thuc(move):
    from app.modules.audit.model import AuditLog

    w = move["world"]
    update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c_new"], department_id=0), ACTOR)

    msgs = [r.message or "" for r in w.db.query(AuditLog).filter(
        AuditLog.entity == "employee", AuditLog.entity_id == move["eid"])]
    assert any("kết thúc 2 dòng kiêm nhiệm ở công ty cũ" in m and "Phòng Kế toán" in m
               and "chưa bắt đầu, đã xóa" in m for m in msgs)


def test_doi_phap_nhan_tham_so_giu_lai_dong_duoc_chon(move):
    w, rows = move["world"], move["rows"]
    update_employee(w.db, move["eid"], EmployeeUpdate(
        company_id=move["c_new"], department_id=0, keep_concurrent_ids=[rows["open"].id]), ACTOR)

    assert _fresh(w.db, rows["open"]).to_date is None, "dòng được chọn giữ thì nguyên"
    assert w.db.get(EmployeeConcurrent, rows["future"].id) is None, "dòng không được chọn vẫn bị xử lý"


def test_doi_phap_nhan_tat_co_ket_thuc_thi_giu_het(move):
    w, rows = move["world"], move["rows"]
    update_employee(w.db, move["eid"], EmployeeUpdate(
        company_id=move["c_new"], department_id=0, end_old_company_concurrent=False), ACTOR)

    assert _fresh(w.db, rows["open"]).to_date is None
    assert _fresh(w.db, rows["future"]).from_date > TODAY


def test_co_dieu_khien_khong_thanh_cot_ho_so(move):
    w = move["world"]
    update_employee(w.db, move["eid"], EmployeeUpdate(
        company_id=move["c_new"], department_id=0, end_old_company_concurrent=True, keep_concurrent_ids=[1]), ACTOR)

    obj_vars = vars(w.db.get(Employee, move["eid"]))
    assert "end_old_company_concurrent" not in obj_vars and "keep_concurrent_ids" not in obj_vars


def test_khong_doi_cong_ty_thi_khong_ket_thuc_gi(move):
    w, rows = move["world"], move["rows"]
    update_employee(w.db, move["eid"], EmployeeUpdate(phone="0900000001"), ACTOR)

    assert all(_fresh(w.db, r).to_date in (None, TODAY - timedelta(days=50)) for r in rows.values())
    assert w.db.get(EmployeeConcurrent, rows["future"].id) is not None


def test_doi_phap_nhan_dong_chua_bat_dau_co_tep_nhay_cam_thi_chan_neu_thieu_quyen(move):
    """Xóa dòng kéo theo xóa tệp quyết định -> cùng chốt `employee_sensitive.read` với DELETE ở tab Kiêm nhiệm."""
    w, rows = move["world"], move["rows"]
    stored = StoredFile(filename="qd.pdf", file_key="k/qd.pdf")
    w.db.add(stored)
    w.db.flush()
    w.db.add(FileLink(file_id=stored.id, entity="employee_concurrent", entity_id=rows["future"].id))
    w.db.commit()

    nobody = w.actor("a1").user.id         # tài khoản không có vai trò nào
    with pytest.raises(HTTPException) as exc:
        update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c_new"], department_id=0), nobody)
    assert exc.value.status_code == 403
    assert w.db.get(EmployeeConcurrent, rows["future"].id) is not None
    assert w.db.get(Employee, move["eid"]).company_id == move["co_a"], "lỗi thì lùi cả lượt"


# ══════════════════════════════════════════════════════════════════════════════
#  2. Giữ phòng cũ khi đổi phòng chính (bao-CR-709) -> dòng kiêm nhiệm
# ══════════════════════════════════════════════════════════════════════════════

def test_giu_phong_cu_tao_dung_mot_dong_cong_ty_truoc_luc_luu(world):
    db = world.db
    eid = world.emp["a1"]                                    # A, phòng chính A.kt
    old = world.dept["A.kt"]
    obj = db.get(Employee, eid)
    out = update_employee_core(db, obj, EmployeeUpdate(department_id=world.dept["A.mua"], keep_old_department=True), ACTOR)
    db.commit()

    (row,) = _rows_of(db, eid)
    assert (row.department_id, row.company_id, row.from_date, row.to_date) == (old, world.co["A"], TODAY, None)
    assert row.note == "Giữ phòng cũ khi đổi phòng chính" and row.counts_scope is True
    assert any("giữ phòng cũ" in n for n in out.notes)


def test_giu_phong_cu_khi_dong_hieu_luc_da_co_thi_khong_tao_trung(world):
    db = world.db
    eid, old = world.emp["a1"], world.dept["A.kt"]
    exist = _conc(db, eid, world.co["A"], old)
    update_employee_core(db, db.get(Employee, eid),
                         EmployeeUpdate(department_id=world.dept["A.mua"], keep_old_department=True), ACTOR)
    db.commit()

    assert [r.id for r in _rows_of(db, eid)] == [exist.id]


def test_khong_chon_giu_thi_phong_cu_khong_thanh_dong_nao(world):
    db = world.db
    eid = world.emp["a1"]
    update_employee_core(db, db.get(Employee, eid), EmployeeUpdate(department_id=world.dept["A.mua"]), ACTOR)
    db.commit()

    assert _rows_of(db, eid) == []


def test_giu_phong_cu_cung_luc_doi_cong_ty_dong_giu_o_cong_ty_truoc_va_khong_bi_ket_thuc(move):
    """Đổi A -> C, chọn phòng của C và giữ phòng cũ: dòng phòng cũ (công ty A) là LỰA CHỌN TƯỜNG MINH nên sống sót."""
    from app.modules.department.model import Department

    w = move["world"]
    d_c = Department(code="C_KT", name="Phòng KT C", company_id=move["c_new"], is_active=True)
    w.db.add(d_c)
    w.db.flush()
    old_primary = w.db.get(Employee, move["eid"]).department_id
    update_employee(w.db, move["eid"], EmployeeUpdate(
        company_id=move["c_new"], department_id=d_c.id, keep_old_department=True), ACTOR)

    kept = [r for r in _rows_of(w.db, move["eid"]) if r.note == "Giữ phòng cũ khi đổi phòng chính"]
    assert [(r.department_id, r.company_id, r.to_date) for r in kept] == [(old_primary, move["co_a"], None)]


# ══════════════════════════════════════════════════════════════════════════════
#  3. Áp quá trình công tác loại KIÊM NHIỆM
# ══════════════════════════════════════════════════════════════════════════════

def test_ap_hai_lan_ra_mot_dong_sua_ngay_roi_ap_lai_thi_cap_nhat_dong(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=10), department_id=world.dept["A.kt"],
             decision_no="QD-1")

    assert applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    assert applysvc.apply(db, wh, a1.user, a1.profile()) == [], "Áp lại khi đã khớp: không đổi gì"
    db.commit()
    assert len(_rows_of(db, eid)) == 1

    wh.from_date, wh.decision_no = TODAY - timedelta(days=20), "QD-2"
    db.commit()
    assert applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (row,) = _rows_of(db, eid)
    assert (row.from_date, row.decision_no) == (TODAY - timedelta(days=20), "QD-2")


def test_ap_khong_doi_cong_tac_pham_vi_da_tat_tay(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=3), department_id=world.dept["A.kt"])
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (row,) = _rows_of(db, eid)
    row.counts_scope = False
    db.commit()

    wh.note = "đổi ghi chú"
    db.commit()
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (row,) = _rows_of(db, eid)
    assert row.counts_scope is False and row.note == "đổi ghi chú"


def test_ap_ghi_cong_ty_khac_va_dong_het_han_khong_mo_pham_vi(world):
    """Công ty của dòng QTCT được giữ (khác công ty chính); dòng đã hết hạn không nằm trong `dept_ids`."""
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=10), department_id=world.dept["B.kt"],
             company_id=world.co["B"])
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (row,) = _rows_of(db, eid)
    assert (row.company_id, row.department_id) == (world.co["B"], world.dept["B.kt"])

    wh2 = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=60), department_id=world.dept["A.kt"],
              to_date=TODAY - timedelta(days=30))
    applysvc.apply(db, wh2, a1.user, a1.profile())      # chưa có dòng + đã hết -> không tạo dòng chết
    db.commit()
    assert len(_rows_of(db, eid)) == 1


def test_ap_dong_het_han_da_co_dong_thi_thanh_da_het_khong_mo_pham_vi(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    a3 = world.grant("a3", "purchase_request", scope="dept")       # cùng tài khoản a3 để soi hồ sơ quyền
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=10), department_id=world.dept["A.kt"])
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    assert world.dept["A.kt"] in a3.profile()["dept_ids"]

    wh.to_date = YESTERDAY
    db.commit()
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    assert world.dept["A.kt"] not in a3.profile()["dept_ids"], "dòng hết hạn không mở phạm vi"


def test_ap_lien_ket_tep_quyet_dinh_sang_dong_kiem_nhiem_khong_nhan_doi(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=2), department_id=world.dept["A.kt"])
    stored = StoredFile(filename="qd.pdf", file_key="k/qd.pdf")
    db.add(stored)
    db.flush()
    db.add(FileLink(file_id=stored.id, entity="employee_work_history", entity_id=wh.id, doc_type="decision"))
    db.commit()

    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (row,) = _rows_of(db, eid)
    links = db.query(FileLink).filter(FileLink.entity == "employee_concurrent", FileLink.entity_id == row.id).all()
    assert [(lk.file_id, lk.doc_type) for lk in links] == [(stored.id, "decision")]
    assert db.query(FileLink).filter(FileLink.entity == "employee_work_history").count() == 1, "liên kết gốc còn"


def test_ap_cap_cong_ty_khac_phai_qua_l2_theo_cap(world):
    db = world.db
    eid = world.emp["a3"]
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=2), department_id=world.dept["B.kt"],
             company_id=world.co["B"])

    a1_dept = world.grant("a1", "employee", scope="dept", actions=("read", "write"))
    with pytest.raises(HTTPException) as exc:
        applysvc.apply(db, wh, a1_dept.user, a1_dept.profile())
    assert exc.value.status_code == 403
    assert _rows_of(db, eid) == []


def test_ap_chong_giai_doan_cua_dong_nhap_tay_thi_409(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    eid = world.emp["a3"]
    _conc(db, eid, world.co["A"], world.dept["A.kt"])                   # đang mở, nhập tay ở tab
    wh = _wh(db, eid, WorkEventType.CONCURRENT, TODAY - timedelta(days=2), department_id=world.dept["A.kt"])

    with pytest.raises(HTTPException) as exc:
        applysvc.apply(db, wh, a1.user, a1.profile())
    assert exc.value.status_code == 409


def test_ap_khong_tu_ap_cho_chinh_minh_l1(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    wh = _wh(db, world.emp["a1"], WorkEventType.CONCURRENT, TODAY - timedelta(days=2), department_id=world.dept["A.mua"])

    with pytest.raises(HTTPException) as exc:
        applysvc.apply(db, wh, a1.user, a1.profile())
    assert exc.value.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
#  4. Dòng có công ty = 0 (dữ liệu cũ) — người sửa được hồ sơ thì sửa được, không cần phạm vi `all`
# ══════════════════════════════════════════════════════════════════════════════

def test_l2_dong_cong_ty_0_dung_phong_thi_theo_phong_cua_nguoi_thao_tac(world):
    a1_company = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    assert dv.pair_in_write_scope(world.db, a1_company.profile(), world.dept["A.kt"], 0) is True
    assert dv.pair_in_write_scope(world.db, a1_company.profile(), world.dept["A.kt"], world.co["B"]) is False

    a2_dept = world.grant("a2", "employee", scope="dept", actions=("read", "write"))
    assert dv.pair_in_write_scope(world.db, a2_dept.profile(), world.dept["A.kt"], 0) is True, "phòng của mình"
    assert dv.pair_in_write_scope(world.db, a2_dept.profile(), world.dept["A.mua"], 0) is False, "phòng người khác"


def test_sua_va_xoa_dong_cong_ty_0_bang_nguoi_co_pham_vi_cong_ty(world):
    db = world.db
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    emp_b = db.get(Employee, world.emp["a3"])
    row = _conc(db, emp_b.id, 0, world.dept["A.kt"])

    from app.modules.employee.concurrent_schema import ConcurrentPatch
    concurrent_service.update_concurrent(db, emp_b, row.id, ConcurrentPatch(note="đã nhập đủ"), a1.user, a1.profile())
    assert _fresh(db, row).note == "đã nhập đủ"
    concurrent_service.delete_concurrent(db, emp_b, row.id, a1.user, a1.profile())
    db.commit()
    assert db.get(EmployeeConcurrent, row.id) is None


# ══════════════════════════════════════════════════════════════════════════════
#  5. Chặn xóa chức vụ đang được dòng kiêm nhiệm dùng
# ══════════════════════════════════════════════════════════════════════════════

def test_chuc_vu_dang_duoc_dong_kiem_nhiem_dung_thi_chan_xoa(world):
    from app.core import reference_guard
    from app.modules.employee import position_controller  # noqa: F401  — đăng ký sổ tham chiếu

    db = world.db
    cv = JobPosition(code="PHO", name="Phó phòng", is_active=True)
    db.add(cv)
    db.flush()
    row = _conc(db, world.emp["a3"], world.co["A"], world.dept["A.kt"], position_id=cv.id, position_label="Phó phòng")

    assert ("dòng kiêm nhiệm", 1) in reference_guard.count_references(db, "job_position", cv)
    db.delete(row)
    db.commit()
    assert reference_guard.count_references(db, "job_position", cv) == []


# ══════════════════════════════════════════════════════════════════════════════
#  6. Nhập Excel nhân sự + hoàn tác
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def xl(db, seed, hr):
    """DEMONV (công ty seed) có kiêm nhiệm ở công ty seed; CT02 là công ty đích với phòng DEPT02."""
    from app.modules.department.model import Department

    co2 = Company(code="CT02", name="Cty Hai", is_active=True)
    db.add(co2)
    db.flush()
    d2 = Department(code="DEPT02", name="Phòng Hai", company_id=co2.id, is_active=True)
    d3 = Department(code="DEPT03", name="Phòng Ba", company_id=seed.company_id, is_active=True)
    db.add_all([d2, d3])
    db.commit()
    return {"co2": co2.id, "d2": d2.id, "d3": d3.id, "eid": seed.emp_nstm_id, "co1": seed.company_id}


ROW = {"Mã NV *": "DEMONV", "Công ty (mã)": "CT02", "Phòng ban (mã)": "DEPT02"}


def test_nhap_excel_doi_phap_nhan_ket_thuc_kiem_nhiem_cong_ty_cu_va_hoan_tac_tra_lai(db, seed, hr, xl):
    open_row = _conc(db, xl["eid"], xl["co1"], xl["d3"])
    other = _conc(db, xl["eid"], 4242, xl["d3"])                   # công ty KHÁC công ty cũ
    b = run_import(db, [ROW], hr)
    assert b.error_count == 0 and b.updated_count == 1

    assert _fresh(db, open_row).to_date == YESTERDAY
    assert _fresh(db, other).to_date is None
    from app.modules.import_tool.model import ImportChange
    (change,) = db.query(ImportChange).filter(ImportChange.batch_id == b.id).all()
    ended = json.loads(change.snapshot)["cols"]["_concurrent_ended"]
    assert ended == [[open_row.id, None, YESTERDAY.isoformat()]]

    from app.modules.import_tool import service
    res = service.revert_batch(db, b, hr)
    assert res["ok"], res
    assert _fresh(db, open_row).to_date is None
    assert emp(db, "DEMONV").company_id == xl["co1"]


def test_nhap_excel_chay_thu_khong_ket_thuc_that(db, seed, hr, xl):
    open_row = _conc(db, xl["eid"], xl["co1"], xl["d3"])
    b = run_import(db, [ROW], hr, apply=False)

    assert b.error_count == 0
    assert _fresh(db, open_row).to_date is None
    assert emp(db, "DEMONV").company_id == xl["co1"]


def test_nhap_excel_con_kiem_nhiem_chua_bat_dau_o_cong_ty_cu_la_loi_dong(db, seed, hr, xl):
    future = _conc(db, xl["eid"], xl["co1"], xl["d3"], from_date=TODAY + timedelta(days=3))
    b = run_import(db, [ROW], hr)

    assert b.error_count == 1 and b.updated_count == 0
    assert "chưa bắt đầu ở công ty cũ" in errors(db, b.id)[0].message
    assert db.get(EmployeeConcurrent, future.id) is not None
    assert emp(db, "DEMONV").company_id == xl["co1"], "dòng lỗi thì hồ sơ không đổi"


def test_hoan_tac_tu_choi_khi_dong_kiem_nhiem_da_bi_sua_sau_khi_nhap(db, seed, hr, xl):
    open_row = _conc(db, xl["eid"], xl["co1"], xl["d3"])
    b = run_import(db, [ROW], hr)
    row = _fresh(db, open_row)
    row.to_date = TODAY - timedelta(days=5)              # ai đó sửa sau khi nhập
    db.commit()

    from app.modules.import_tool import service
    res = service.revert_batch(db, b, hr)
    assert not res["ok"] and "DEMONV" in res["message"] and "kiêm nhiệm" in res["message"]
    assert _fresh(db, open_row).to_date == TODAY - timedelta(days=5)


def test_hoan_tac_tu_choi_lo_cu_ghi_phong_phu_theo_cach_cu(db, seed, hr, xl):
    """Lô trước duoc-CR-755 có `_depts` chứa phòng PHỤ: không dựng lại được kiêm nhiệm kiểu cũ -> từ chối rõ."""
    from app.modules.import_tool import service
    from app.modules.import_tool.model import ImportChange

    b = run_import(db, [{"Mã NV *": "DEMONV", "Điện thoại": "0933333333"}], hr)
    (change,) = db.query(ImportChange).filter(ImportChange.batch_id == b.id).all()
    snap = json.loads(change.snapshot)
    snap["cols"]["_depts"] = [[[xl["d3"], False]], [[xl["d3"], False]]]
    change.snapshot = json.dumps(snap)
    db.commit()

    res = service.revert_batch(db, b, hr)
    assert not res["ok"] and "theo cách cũ" in res["message"]


def test_hoan_tac_lo_tao_bi_chan_neu_nhan_su_moi_da_co_kiem_nhiem(db, seed, hr, xl):
    from app.modules.import_tool import service

    b = run_import(db, [{"Mã NV *": "MOI55", "Họ tên *": "Người Mới", "Phòng ban (mã)": "DEPT01"}], hr)
    new = emp(db, "MOI55")
    _conc(db, new.id, xl["co1"], xl["d3"])
    res = service.revert_batch(db, b, hr)

    assert not res["ok"] and "MOI55" in res["message"] and "kiêm nhiệm" in res["message"]
    assert emp(db, "MOI55") is not None
