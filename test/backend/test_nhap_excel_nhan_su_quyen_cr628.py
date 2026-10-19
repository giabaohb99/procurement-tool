"""duoc-CR-628 — Nhập Excel Nhân sự: QUYỀN · PHẠM VI · CỘT NHẠY CẢM · GÁC ĐƯỜNG `/api/imports`.

Chạy thẳng `catalog_import.run` (người tạo lô = `u_req`) và các hàm controller của import_tool.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.import_tool import controller as imp_ctl
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus, LogLevel
from app.modules.attachment.model import StoredFile
from app.modules.user.model import User

from test_nhap_excel_nhan_su_cr628 import emp, errors, logs, run_import, savepoint_that

CCCD = "079123456789"
STK = "9704123400001"


@pytest.fixture
def world2(db, seed):
    """Thêm công ty 2 + phòng 3 (cùng công ty seed) + nhân viên XA ở công ty 2."""
    savepoint_that(db)
    co2 = Company(name="Cty Hai", code="CT02", is_active=True)
    db.add(co2)
    db.flush()
    d3 = Department(code="DEPT03", name="Phòng Ba", company_id=seed.company_id, is_active=True)
    xa = Employee(code="XA01", full_name="Người Công Ty Hai", company_id=co2.id, is_active=True)
    db.add_all([d3, xa])
    db.commit()
    return {"co2": co2.id, "d3": d3.id, "xa": xa.id}


def grant(cap_quyen, uid, scope="all", employee=("read", "create", "write"), sens=("read", "write")):
    if employee:
        cap_quyen(uid, "employee", scope=scope, **{a: True for a in employee})
    if sens:
        cap_quyen(uid, "employee_sensitive", scope="all", **{a: True for a in sens})


# ── 1. phạm vi: mã ngoài phạm vi ────────────────────────────────────────────────
def test_ma_ngoai_pham_vi_la_loi_khong_tao_ban_trung_khong_doi(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, scope="company")
    b = run_import(db, [{"Mã NV *": "XA01", "Họ tên *": "Bị đổi tên"}], seed.u_req_id)
    assert b.error_count == 1 and errors(db, b.id)[0].category == "out_of_scope"
    assert db.query(Employee).filter(Employee.code == "XA01").count() == 1
    assert emp(db, "XA01").full_name == "Người Công Ty Hai"


# ── 2. phạm vi: tạo vào công ty ngoài phạm vi (kiểm SAU ghi) ───────────────────
def test_tao_vao_cong_ty_ngoai_pham_vi_lui_savepoint_sach(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, scope="company")
    b = run_import(db, [{"Mã NV *": "MOI01", "Họ tên *": "Người Mới", "Công ty (mã)": "CT02"},
                        {"Mã NV *": "MOI02", "Họ tên *": "Người Hai", "Công ty (mã)": "CT01"}], seed.u_req_id)
    assert b.error_count == 1 and b.created_count == 1
    assert emp(db, "MOI01") is None and emp(db, "MOI02") is not None


# ── 3. chỉ write / chỉ create ───────────────────────────────────────────────────
def test_chi_write_thi_dong_moi_loi_dong_sua_ok(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, employee=("read", "write"))
    b = run_import(db, [{"Mã NV *": "DEMONV", "Họ tên *": "Sửa được"},
                        {"Mã NV *": "MOI01", "Họ tên *": "Không tạo được"}], seed.u_req_id)
    assert emp(db, "DEMONV").full_name == "Sửa được" and emp(db, "MOI01") is None
    assert b.updated_count == 1 and b.error_count == 1


def test_chi_create_thi_dong_sua_loi_dong_moi_ok(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, employee=("read", "create"))
    b = run_import(db, [{"Mã NV *": "DEMONV", "Họ tên *": "Không sửa được"},
                        {"Mã NV *": "MOI01", "Họ tên *": "Tạo được", "Công ty (mã)": "CT01"}], seed.u_req_id)
    assert emp(db, "DEMONV").full_name == "NSTM Chính" and emp(db, "MOI01") is not None
    assert b.created_count == 1 and b.error_count == 1


# ── 4-6. cột nhạy cảm ──────────────────────────────────────────────────────────
ROW_SENS = {"Mã NV *": "DEMONV", "Điện thoại": "0911000111", "Số CCCD": CCCD,
            "Số tài khoản": STK, "Ngày sinh": "01/02/1990"}


def test_thieu_quyen_ghi_nhay_cam_bo_cot_canh_bao_mot_lan(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, sens=("read",))             # chỉ ĐỌC, không GHI
    b = run_import(db, [ROW_SENS, {**ROW_SENS, "Mã NV *": "DEMOTP"}], seed.u_req_id)
    e = emp(db, "DEMONV")
    assert e.phone == "0911000111"                              # cột thường vẫn ghi
    assert (e.id_number or "") == "" and (e.bank_account_no or "") == "" and e.date_of_birth is None
    warn = [x for x in logs(db, b.id, LogLevel.WARNING) if x.category == "sensitive_ignored"]
    assert len(warn) == 1 and "Số CCCD" in warn[0].message and CCCD not in warn[0].message
    assert b.error_count == 0


def test_co_quyen_ghi_nhay_cam_thi_ghi_duoc(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id)
    b = run_import(db, [ROW_SENS], seed.u_req_id)
    e = emp(db, "DEMONV")
    assert (e.id_number, e.bank_account_no) == (CCCD, STK) and str(e.date_of_birth) == "1990-02-01"
    assert not [x for x in logs(db, b.id) if x.category == "sensitive_ignored"]


def test_log_khong_chua_gia_tri_cot_nhay_cam_ke_ca_khi_loi(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id)
    b = run_import(db, [{"Mã NV *": "DEMONV", "Số CCCD": CCCD + "9" * 30, "Số tài khoản": STK,
                         "Ngày sinh": "ngày lạ " + STK},
                        {"Mã NV *": "DEMOTP", "Số CCCD": CCCD, "Số tài khoản": STK}], seed.u_req_id)
    assert b.error_count >= 1
    for x in logs(db, b.id):
        for secret in (CCCD, STK):
            assert secret not in x.message and secret not in (x.ref_key or "")


# ── 7. tự đổi phòng ban (L1) / phòng ngoài tầm (L2) ────────────────────────────
def test_tu_doi_phong_ban_cua_minh_la_loi_l1(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id)
    b = run_import(db, [{"Mã NV *": "TESTREQ", "Phòng ban (mã)": "DEPT03"}], seed.u_req_id)
    assert b.error_count == 1 and errors(db, b.id)[0].category == "department_denied"
    assert emp(db, "TESTREQ").department_id == seed.dept_id


def test_gan_phong_ngoai_tam_la_loi_l2(db, seed, cap_quyen, world2):
    grant(cap_quyen, seed.u_req_id, scope="dept")               # chỉ thấy phòng của mình (DEPT01)
    b = run_import(db, [{"Mã NV *": "DEMONV", "Phòng ban (mã)": "DEPT03"}], seed.u_req_id)
    assert b.error_count == 1
    assert emp(db, "DEMONV").department_id == seed.dept_id


# ── 8-11. gác đường /api/imports ────────────────────────────────────────────────
class _FakeUpload:
    filename = "nhan-su.xlsx"

    class file:                                                 # noqa: N801
        @staticmethod
        def read():
            raise AssertionError("không được đọc tệp khi thiếu quyền")


def _import_perms(cap_quyen, uid):
    cap_quyen(uid, "import", scope="all", read=True, create=True, delete=True)


def test_upload_lo_nhan_su_thieu_quyen_employee_la_403_khong_luu_tep(db, seed, cap_quyen):
    _import_perms(cap_quyen, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    before = db.query(StoredFile).count()
    with pytest.raises(HTTPException) as e:
        imp_ctl.upload_import(module=ImportModule.EMPLOYEE, mode=0, file=_FakeUpload(), db=db, user=user)
    assert e.value.status_code == 403
    assert db.query(StoredFile).count() == before


def _batch(db, module, uid):
    sf = StoredFile(filename="a.xlsx", file_key="k/a.xlsx", content_type="application/octet-stream")
    db.add(sf)
    db.flush()
    b = ImportBatch(module=module, mode=ImportMode.APPLY, filename="a.xlsx", file_id=sf.id,
                    status=ImportStatus.DONE, created_by=uid, updated_by=uid)
    db.add(b)
    db.commit()
    return b


def test_tai_tep_lo_nhan_su_can_nhay_cam_read_lo_kho_van_tai_duoc(db, seed, cap_quyen, monkeypatch):
    _import_perms(cap_quyen, seed.u_req_id)
    monkeypatch.setattr(imp_ctl, "download_bytes", lambda key: b"PK-data")
    user = db.get(User, seed.u_req_id)
    emp_batch = _batch(db, ImportModule.EMPLOYEE, user.id)
    wh_batch = _batch(db, ImportModule.WAREHOUSE, user.id)
    with pytest.raises(HTTPException) as e:
        imp_ctl.download_import_file(emp_batch.id, db=db, user=user)
    assert e.value.status_code == 403 and "nhạy cảm" in e.value.detail
    assert imp_ctl.download_import_file(wh_batch.id, db=db, user=user).status_code == 200
    cap_quyen(user.id, "employee_sensitive", scope="all", read=True)
    assert imp_ctl.download_import_file(emp_batch.id, db=db, user=user).status_code == 200


def test_hoan_tac_lo_nhan_su_thieu_employee_write_la_403(db, seed, cap_quyen):
    _import_perms(cap_quyen, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    b = _batch(db, ImportModule.EMPLOYEE, user.id)
    with pytest.raises(HTTPException) as e:
        imp_ctl.revert_import(b.id, db=db, user=user)
    assert e.value.status_code == 403


def test_ghi_that_tu_ban_chay_thu_can_quyen_employee(db, seed, cap_quyen):
    _import_perms(cap_quyen, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    b = _batch(db, ImportModule.EMPLOYEE, user.id)
    b.mode = ImportMode.DRY_RUN
    db.commit()
    with pytest.raises(HTTPException) as e:
        imp_ctl.commit_import(b.id, db=db, user=user)
    assert e.value.status_code == 403


def test_hai_duong_csv_cu_tra_410(db, seed, cap_quyen):
    from io import BytesIO

    from fastapi import UploadFile

    from app.modules.department.controller import import_departments_csv
    from app.modules.employee.controller import import_employees_csv

    user = db.get(User, seed.u_req_id)
    f = lambda: UploadFile(file=BytesIO(b"a,b\n1,2\n"), filename="x.csv")   # noqa: E731
    for fn in (import_employees_csv, import_departments_csv):
        with pytest.raises(HTTPException) as e:
            fn(file=f(), db=db, user=user)
        assert e.value.status_code == 410
    assert db.query(Employee).count() == 4
