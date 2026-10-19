"""duoc-CR-628 — Nhập Excel Nhân sự: nghiệp vụ (ô trống, mã số, ngày, độ dài, tham chiếu, hoàn tác…).

Chạy thẳng `catalog_import.run` + `service.revert_batch` trên SQLite in-memory, người tạo lô = `u_req`
được cấp `employee.*` + `employee_sensitive.*` phạm vi `all`. Phần quyền/phạm vi/nhạy cảm ở
`test_nhap_excel_nhan_su_quyen_cr628.py`.
"""
from datetime import date, datetime

import openpyxl
import pytest

from app.modules.employee import service as employee_service
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.schema import EmployeeUpdate
from app.modules.import_tool import catalog_import, service
from app.modules.import_tool.employee_import_fields import EMPLOYEE_FIELDS
from app.modules.import_tool.model import (ImportBatch, ImportLog, ImportMode, ImportModule,
                                           ImportStatus, LogLevel)
from app.modules.user.model import User

SENT = "__/empty_value/__"


# ── helper ──────────────────────────────────────────────────────────────────────
def make_wb(rows: list[dict]):
    """Workbook sheet «Nhan su»; khóa dict = TIÊU ĐỀ cột (cột nào không ai khai thì vắng hẳn)."""
    headers: list[str] = []
    for r in rows:
        for k in r:
            if k not in headers:
                headers.append(k)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nhan su"
    for i, h in enumerate(headers, start=1):
        ws.cell(row=1, column=i, value=h)
    for ri, r in enumerate(rows, start=2):
        for i, h in enumerate(headers, start=1):
            if h in r:
                ws.cell(row=ri, column=i, value=r[h])
    return wb


def run_import(db, rows, uid, apply=True, wb=None):
    b = ImportBatch(module=ImportModule.EMPLOYEE, mode=ImportMode.APPLY if apply else ImportMode.DRY_RUN,
                    filename="t.xlsx", file_id=0, status=ImportStatus.QUEUED, created_by=uid, updated_by=uid)
    db.add(b)
    db.commit()
    db.refresh(b)
    catalog_import.run(db, b, wb or make_wb(rows), apply=apply)
    db.refresh(b)
    return b


def logs(db, bid, level=None):
    q = db.query(ImportLog).filter(ImportLog.batch_id == bid)
    if level is not None:
        q = q.filter(ImportLog.level == level)
    return q.all()


def errors(db, bid):
    return logs(db, bid, LogLevel.ERROR)


def savepoint_that(db):
    """pysqlite (chế độ cũ) KHÔNG phát `BEGIN` trước `SAVEPOINT` → savepoint ngoài cùng tự thành giao dịch
    và `RELEASE` của nó COMMIT luôn, làm hỏng phép thử dry-run. Ép `BEGIN` tường minh như MySQL thật."""
    from sqlalchemy import event
    engine = db.get_bind()
    db.connection().connection.dbapi_connection.isolation_level = None
    event.listen(engine, "begin", lambda conn: conn.exec_driver_sql("BEGIN"))


@pytest.fixture
def hr(db, seed, cap_quyen):
    """Người nhập có đủ quyền Nhân sự + nhạy cảm, phạm vi toàn bộ."""
    savepoint_that(db)
    uid = seed.u_req_id
    cap_quyen(uid, "employee", scope="all", read=True, create=True, write=True, delete=True)
    cap_quyen(uid, "employee_sensitive", scope="all", read=True, write=True)
    return uid


def emp(db, code):
    db.expire_all()
    return db.query(Employee).filter(Employee.code == code).first()


# ── 1. ô trống giữ nguyên ───────────────────────────────────────────────────────
def test_o_trong_giu_nguyen_trang_thai_va_dang_dung(db, seed, hr):
    e = emp(db, "DEMONV")
    e.status, e.is_active = "resigned", False
    db.commit()
    b = run_import(db, [{"Mã NV *": "DEMONV", "Họ tên *": "NSTM Chính đổi tên",
                         "Trạng thái": None, "Đang dùng (1/0)": None}], hr)
    e = emp(db, "DEMONV")
    assert e.full_name == "NSTM Chính đổi tên"
    assert e.status == "resigned" and e.is_active is False
    assert b.updated_count == 1 and b.error_count == 0


# ── 2. sentinel xóa ─────────────────────────────────────────────────────────────
def test_sentinel_xoa_o_thuong_va_chan_o_bat_buoc(db, seed, hr):
    e = emp(db, "DEMONV")
    e.bank_branch, e.hire_date, e.manager_id = "CN Hà Nội", date(2020, 1, 1), seed.emp_tp_id
    db.commit()
    b = run_import(db, [{"Mã NV *": "DEMONV", "Chi nhánh": SENT, "Ngày vào làm": SENT,
                         "Quản lý trực tiếp (mã NV)": SENT}], hr)
    e = emp(db, "DEMONV")
    assert e.bank_branch == "" and e.hire_date is None and e.manager_id == 0
    assert b.error_count == 0

    b2 = run_import(db, [{"Mã NV *": "DEMONV", "Họ tên *": SENT}, {"Mã NV *": "DEMOTP", "Trạng thái": SENT}], hr)
    assert b2.error_count == 2
    assert emp(db, "DEMONV").full_name == "NSTM Chính"
    assert emp(db, "DEMOTP").status == "official"


# ── 3. trạng thái ───────────────────────────────────────────────────────────────
def test_trang_thai_nhan_ma_nhan_va_bo_dau_sai_thi_loi(db, seed, hr):
    run_import(db, [{"Mã NV *": "DEMONV", "Trạng thái": "Nghỉ thai sản"},
                    {"Mã NV *": "DEMOTP", "Trạng thái": "cong tac vien"},
                    {"Mã NV *": "BACKUP01", "Trạng thái": "resigned"}], hr)
    assert emp(db, "DEMONV").status == "maternity_leave"
    assert emp(db, "DEMOTP").status == "collaborator" and emp(db, "BACKUP01").status == "resigned"
    b = run_import(db, [{"Mã NV *": "DEMOTP", "Trạng thái": "Đang lơ lửng"}], hr)
    assert b.error_count == 1
    assert emp(db, "DEMOTP").status == "collaborator"          # giá trị lạ KHÔNG bị đoán/ghi đè
    assert "Trạng thái" in errors(db, b.id)[0].message


# ── 4. mã số ────────────────────────────────────────────────────────────────────
def test_ma_so_nhan_so_va_nhan_sai_thi_loi(db, seed, hr):
    b = run_import(db, [{"Mã NV *": "DEMONV", "Giới tính": 2, "Cấp bậc": "Trưởng phòng",
                         "Hình thức nhân viên": "thoi vu"}], hr)
    e = emp(db, "DEMONV")
    assert (e.gender, e.job_level, e.employment_type) == (2, 4, 3)
    assert b.error_count == 0
    b2 = run_import(db, [{"Mã NV *": "DEMONV", "Giới tính": 9}, {"Mã NV *": "DEMOTP", "Cấp bậc": "Sếp tổng"}], hr)
    assert b2.error_count == 2
    assert emp(db, "DEMONV").gender == 2


# ── 5. ngày ─────────────────────────────────────────────────────────────────────
def test_ngay_dd_mm_yyyy_o_ngay_excel_va_nam_vo_ly(db, seed, hr):
    b = run_import(db, [
        {"Mã NV *": "DEMONV", "Ngày sinh": "05/03/1990", "Ngày vào làm": datetime(2021, 6, 1)},
        {"Mã NV *": "DEMOTP", "Ngày vào làm": date(1, 1, 1)},
        {"Mã NV *": "BACKUP01", "Ngày vào làm": "không phải ngày"},
    ], hr)
    e = emp(db, "DEMONV")
    assert e.date_of_birth == date(1990, 3, 5) and e.hire_date == date(2021, 6, 1)
    assert b.error_count == 2
    assert emp(db, "DEMOTP").hire_date is None


# ── 6. độ dài ───────────────────────────────────────────────────────────────────
def test_chuoi_vuot_tran_la_loi_dong_khong_sap_batch(db, seed, hr):
    b = run_import(db, [{"Mã NV *": "DEMONV", "Mã số thuế": "1" * 21},
                        {"Mã NV *": "DEMOTP", "Điện thoại": "9" * 26},
                        {"Mã NV *": "BACKUP01", "Điện thoại": "0912345678"}], hr)
    assert b.status == ImportStatus.DONE
    assert b.error_count == 2 and b.updated_count == 1
    msgs = " ".join(x.message for x in errors(db, b.id))
    assert "Mã số thuế" in msgs and "Điện thoại" in msgs
    assert "1" * 21 not in msgs


# ── 7. email trùng ──────────────────────────────────────────────────────────────
def test_email_trung_nhan_vien_khac_la_loi(db, seed, hr):
    e = emp(db, "DEMOTP")
    e.email = "tp@dego.vn"
    db.commit()
    b = run_import(db, [{"Mã NV *": "DEMONV", "Email": "TP@dego.vn"}], hr)
    assert b.error_count == 1 and "DEMOTP" in errors(db, b.id)[0].message
    assert emp(db, "DEMONV").email == ""


# ── 8. quản lý ──────────────────────────────────────────────────────────────────
def test_quan_ly_theo_ma_tu_quan_ly_va_vong(db, seed, hr):
    b = run_import(db, [{"Mã NV *": "DEMONV", "Quản lý trực tiếp (mã NV)": "DEMOTP"}], hr)
    assert emp(db, "DEMONV").manager_id == seed.emp_tp_id and b.error_count == 0
    b2 = run_import(db, [{"Mã NV *": "DEMONV", "Quản lý trực tiếp (mã NV)": "DEMONV"},
                         {"Mã NV *": "DEMOTP", "Quản lý trực tiếp (mã NV)": "DEMONV"},
                         {"Mã NV *": "BACKUP01", "Quản lý trực tiếp (mã NV)": "KHONGCO"}], hr)
    assert b2.error_count == 3
    assert emp(db, "DEMOTP").manager_id == 0


# ── 9. phòng ban ────────────────────────────────────────────────────────────────
def test_phong_ban_theo_ma_ten_trung_va_khac_cong_ty(db, seed, hr):
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    co2 = Company(name="Cty Hai", code="CT02", is_active=True)
    db.add(co2)
    db.flush()
    d2 = Department(code="DEPT02", name="Phòng Test", company_id=co2.id, is_active=True)   # trùng tên DEPT01
    d3 = Department(code="DEPT03", name="Phòng Ba", company_id=seed.company_id, is_active=True)
    db.add_all([d2, d3])
    db.commit()

    b = run_import(db, [{"Mã NV *": "DEMONV", "Phòng ban (mã)": "DEPT03"}], hr)
    assert emp(db, "DEMONV").department_id == d3.id and b.error_count == 0
    # tên 'Phòng Test' ở công ty seed → khớp đúng 1 phòng của công ty đó
    b2 = run_import(db, [{"Mã NV *": "DEMOTP", "Phòng ban (mã)": "Phòng Ba"}], hr)
    assert b2.error_count == 0
    # không ghi công ty → tên trùng giữa 2 công ty = lỗi
    e = emp(db, "BACKUP01")
    e.company_id = 0
    db.commit()
    b3 = run_import(db, [{"Mã NV *": "BACKUP01", "Phòng ban (mã)": "Phòng Test"}], hr)
    assert b3.error_count == 1 and "MÃ" in errors(db, b3.id)[0].message
    # phòng thuộc công ty khác với công ty của hồ sơ → chốt L3 của lõi chặn
    b4 = run_import(db, [{"Mã NV *": "DEMOTP", "Phòng ban (mã)": "DEPT02"}], hr)
    assert b4.error_count == 1
    assert emp(db, "DEMOTP").department_id == d3.id


# ── 10. chức vụ ─────────────────────────────────────────────────────────────────
def test_chuc_vu_theo_ma_ten_va_khong_khop_giu_chu(db, seed, hr):
    jp = JobPosition(code="TP", name="Trưởng phòng", is_active=True)
    db.add(jp)
    db.commit()
    run_import(db, [{"Mã NV *": "DEMONV", "Chức vụ (mã/tên)": "TP"},
                    {"Mã NV *": "DEMOTP", "Chức vụ (mã/tên)": "trưởng  PHÒNG"}], hr)
    for code in ("DEMONV", "DEMOTP"):
        e = emp(db, code)
        assert e.position_id == jp.id and e.position == "Trưởng phòng"
    b = run_import(db, [{"Mã NV *": "BACKUP01", "Chức vụ (mã/tên)": "Chuyên gia lạ"}], hr)
    e = emp(db, "BACKUP01")
    assert e.position == "Chuyên gia lạ" and (e.position_id or 0) == 0
    assert logs(db, b.id, LogLevel.REVIEW) and b.error_count == 0


# ── 11. phòng chính ─────────────────────────────────────────────────────────────
def test_doi_phong_chinh_khop_bang_kiem_nhiem(db, seed, hr):
    from app.modules.department.model import Department
    from app.modules.employee.department_service import departments_of

    d3 = Department(code="DEPT03", name="Phòng Ba", company_id=seed.company_id, is_active=True)
    db.add(d3)
    db.commit()
    run_import(db, [{"Mã NV *": "DEMONV", "Phòng ban (mã)": "DEPT03"}], hr)
    db.expire_all()
    assert departments_of(db, seed.emp_nstm_id)[0] == d3.id


# ── 12. cấm xóa ─────────────────────────────────────────────────────────────────
def test_dong_xoa_la_loi_delete_not_allowed_ban_ghi_con_nguyen(db, seed, hr):
    wb = make_wb([{"Mã NV *": "DEMONV", "Họ tên *": "NSTM Chính", "Hành động": "__/delete/__"}])
    b = run_import(db, None, hr, wb=wb)
    assert b.error_count == 1
    assert errors(db, b.id)[0].category == "delete_not_allowed"
    assert emp(db, "DEMONV") is not None and db.get(User, seed.u_nstm_id).is_active


# ── 13. nghỉ việc: dry-run vs apply ─────────────────────────────────────────────
def test_nghi_viec_dry_run_khong_khoa_apply_khoa_va_tang_token(db, seed, hr):
    u = db.get(User, seed.u_nstm_id)
    tv = u.token_version or 0
    b = run_import(db, [{"Mã NV *": "DEMONV", "Trạng thái": "resigned"}], hr, apply=False)
    db.expire_all()
    assert db.get(User, seed.u_nstm_id).is_active is True
    assert emp(db, "DEMONV").status == "official"
    assert any(x.category == "will_lock_user" for x in logs(db, b.id, LogLevel.WARNING))

    run_import(db, [{"Mã NV *": "DEMONV", "Trạng thái": "resigned"}], hr, apply=True)
    db.expire_all()
    u = db.get(User, seed.u_nstm_id)
    assert u.is_active is False and (u.token_version or 0) > tv
    assert emp(db, "DEMONV").status == "resigned"


# ── 14. hoàn tác lô sửa ─────────────────────────────────────────────────────────
def test_hoan_tac_lo_sua_khoi_phuc_du_cot_va_khong_mo_lai_tai_khoan(db, seed, hr):
    e = emp(db, "DEMONV")
    e.id_number, e.date_of_birth, e.bank_account_no = "0790001", date(1991, 2, 3), "111222"
    e.position = "Chữ cũ"
    db.commit()
    b = run_import(db, [{"Mã NV *": "DEMONV", "Số CCCD": "9999999", "Ngày sinh": "01/01/2000",
                         "Số tài khoản": "555", "Chức vụ (mã/tên)": "Chữ mới", "Trạng thái": "resigned"}], hr)
    e = emp(db, "DEMONV")
    assert e.id_number == "9999999" and e.position == "Chữ mới"
    res = service.revert_batch(db, b, hr)
    assert res["ok"], res
    e = emp(db, "DEMONV")
    assert (e.id_number, e.date_of_birth, e.bank_account_no) == ("0790001", date(1991, 2, 3), "111222")
    assert e.position == "Chữ cũ" and e.status == "official"
    assert db.get(User, seed.u_nstm_id).is_active is False        # KHÔNG mở lại tài khoản


# ── 15. hoàn tác lô tạo ─────────────────────────────────────────────────────────
def test_hoan_tac_lo_tao_xoa_nv_moi_va_tu_choi_khi_da_gan_tai_khoan(db, seed, hr):
    from app.modules.employee.department_model import EmployeeDepartment

    b = run_import(db, [{"Mã NV *": "MOI01", "Họ tên *": "Người Mới", "Phòng ban (mã)": "DEPT01"}], hr)
    new = emp(db, "MOI01")
    assert new is not None and b.created_count == 1
    nid = new.id
    assert db.query(EmployeeDepartment).filter(EmployeeDepartment.employee_id == nid).count() == 1
    res = service.revert_batch(db, b, hr)
    assert res["ok"] and res["deleted"] == 1
    assert emp(db, "MOI01") is None
    assert db.query(EmployeeDepartment).filter(EmployeeDepartment.employee_id == nid).count() == 0

    b2 = run_import(db, [{"Mã NV *": "MOI02", "Họ tên *": "Người Hai"}], hr)
    n2 = emp(db, "MOI02")
    db.add(User(email="moi02", employee_id=n2.id, password_hash="x", is_active=True))
    db.commit()
    res2 = service.revert_batch(db, b2, hr)
    assert not res2["ok"] and "MOI02" in res2["message"]
    assert emp(db, "MOI02") is not None


# ── 16. lõi không commit ────────────────────────────────────────────────────────
def test_loi_update_core_khong_commit_va_lock_users_false_khong_khoa(db, seed):
    e = db.get(Employee, seed.emp_nstm_id)
    out = employee_service.update_employee_core(
        db, e, EmployeeUpdate(full_name="Đổi tạm", status="resigned"), seed.u_req_id, lock_users=False)
    assert out.left_company is True and out.locked_users == []
    assert db.get(User, seed.u_nstm_id).is_active is True
    db.rollback()
    db.expire_all()
    assert db.get(Employee, seed.emp_nstm_id).full_name == "NSTM Chính"
    assert db.get(Employee, seed.emp_nstm_id).status == "official"


# ── 17. trần dòng ───────────────────────────────────────────────────────────────
def test_tep_qua_2000_dong_bi_tu_choi(db, seed, hr):
    rows = [{"Mã NV *": f"X{i}", "Họ tên *": "A"} for i in range(2001)]
    with pytest.raises(catalog_import.ImportValidationError):
        run_import(db, rows, hr, apply=False)


# ── 18. mẫu + alias ─────────────────────────────────────────────────────────────
def test_file_mau_khong_co_cot_hanh_dong_co_huong_dan_va_du_cot(db):
    from io import BytesIO
    wb = openpyxl.load_workbook(BytesIO(catalog_import.build_template(ImportModule.EMPLOYEE)))
    assert "Huong dan" in wb.sheetnames
    ws = wb["Nhan su"]
    heads = [c.value for c in ws[1]]
    assert "Hành động" not in heads
    assert heads == [f["header"] for f in EMPLOYEE_FIELDS]


def test_tep_xuat_cu_8_cot_nhap_lai_duoc_nho_alias(db, seed, hr):
    b = run_import(db, [{"Mã NV": "DEMONV", "Họ tên": "NSTM Chính", "Email": "n@x.vn",
                         "Số điện thoại": "0987654321", "Phòng ban": "Phòng Test",
                         "Vị trí": "Chuyên viên", "Trạng thái NS": "Chính thức"}], hr)
    e = emp(db, "DEMONV")
    assert b.error_count == 0, [x.message for x in errors(db, b.id)]
    assert e.phone == "0987654321" and e.email == "n@x.vn" and e.status == "official"
    assert e.position == "Chuyên viên"


# ── mã tự sinh ──────────────────────────────────────────────────────────────────
def test_dong_khong_ma_tu_sinh_nsu_va_ghi_log(db, seed, hr):
    b = run_import(db, [{"Mã NV *": None, "Họ tên *": "Người Không Mã"}], hr)
    e = db.query(Employee).filter(Employee.full_name == "Người Không Mã").first()
    assert e is not None and e.code.startswith("NSU")
    assert any(e.code in x.message and "tự sinh" in x.message for x in logs(db, b.id, LogLevel.INFO))
