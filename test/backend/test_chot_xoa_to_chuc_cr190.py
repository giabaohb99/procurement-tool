"""ai-CR-190 — đợt 3 xóa mềm, cụm TỔ CHỨC: Công ty · Phòng ban · Nhân sự · Tài khoản · Vai trò.

Đang được tham chiếu thì CHẶN xóa (400, cùng câu của `core/reference_guard`), chỉ cho ngưng dùng (`is_active`);
hết tham chiếu thì xóa như cũ. Xóa nhiều: một dòng vướng → không xóa dòng nào. duoc-CR-628: Nhập CSV Nhân sự + Phòng ban đã ngừng (410) nên không còn đường xóa hàng loạt qua tệp.
"""
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.core import reference_guard as rg
from app.modules.company import service as company_service
from app.modules.company.model import Company
from app.modules.department import service as department_service
from app.modules.department.model import Department
from app.modules.employee import service as employee_service
from app.modules.employee.model import Employee
from app.modules.role import service as role_service
from app.modules.role.model import Permission, Role
from app.modules.user import service as user_service
from app.modules.user.model import User, UserRole


def _csv_import_endpoint(router):
    return next(r.endpoint for r in router.routes if r.path.endswith("/import/csv"))


def _upload(text: str) -> UploadFile:
    return UploadFile(file=BytesIO(text.encode("utf-8")), filename="x.csv")


def _assert_blocked(exc: HTTPException, label: str, name: str, ref_label: str) -> None:
    assert exc.status_code == 400
    assert f"{label} «{name}» đang được dùng ở" in exc.detail
    assert ref_label in exc.detail and "ngưng dùng" in exc.detail


def test_nam_danh_muc_da_dang_ky_dung_ten_entity_phan_quyen():
    for entity in ("company", "department", "employee", "user", "role"):
        assert rg.registered(entity), entity


# ───────────────────────────── Công ty ─────────────────────────────
def test_cong_ty_con_tham_chieu_thi_400_dong_con_nguyen(db, seed):
    with pytest.raises(HTTPException) as e:
        company_service.delete_company(db, seed.company_id, 1)
    _assert_blocked(e.value, "Công ty", "CT01", "phòng ban")
    assert "nhân sự" in e.value.detail
    assert db.get(Company, seed.company_id) is not None


def test_cong_ty_het_tham_chieu_thi_xoa_duoc(db, seed):
    free = Company(code="CT_TRONG", name="Công ty trống", is_active=True)
    db.add(free)
    db.commit()
    company_service.delete_company(db, free.id, 1)
    assert db.get(Company, free.id) is None


def test_xoa_nhieu_cong_ty_mot_dong_vuong_thi_khong_xoa_dong_nao(db, seed, cap_quyen):
    from app.modules.company.controller import bulk_delete_companies

    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "company", scope="all", read=True, delete=True)
    free = Company(code="CT_TRONG", name="Công ty trống", is_active=True)
    db.add(free)
    db.commit()

    with pytest.raises(HTTPException) as e:
        bulk_delete_companies(ids=f"{seed.company_id},{free.id}", db=db, user=user)
    assert e.value.status_code == 400
    assert "CT01 (" in e.value.detail and "phòng ban" in e.value.detail and "ngưng dùng" in e.value.detail
    assert "CT_TRONG" not in e.value.detail                      # chỉ kể dòng vướng
    db.rollback()
    assert db.get(Company, seed.company_id) is not None and db.get(Company, free.id) is not None

    #  Lô toàn dòng trống thì xóa như cũ (`delete(synchronize_session=False)` không gỡ đối tượng khỏi phiên → expire).
    free_id = free.id
    bulk_delete_companies(ids=str(free_id), db=db, user=user)
    db.expire_all()
    assert db.get(Company, free_id) is None


# ───────────────────────────── Phòng ban ─────────────────────────────
def test_phong_ban_con_nhan_su_thi_400_het_thi_xoa_duoc(db, seed):
    with pytest.raises(HTTPException) as e:
        department_service.delete_department(db, seed.dept_id, 1)
    _assert_blocked(e.value, "Phòng ban", "DEPT01", "4 nhân sự")
    assert db.get(Department, seed.dept_id) is not None

    free = Department(code="PB_TRONG", name="Phòng trống", company_id=seed.company_id, is_active=True)
    db.add(free)
    db.commit()
    department_service.delete_department(db, free.id, 1)
    assert db.get(Department, free.id) is None


def test_phong_ban_cha_con_phong_con_thi_400(db, seed):
    parent = Department(code="PB_CHA", name="Phòng cha", company_id=seed.company_id, is_active=True)
    db.add(parent)
    db.flush()
    db.add(Department(code="PB_CON", name="Phòng con", company_id=seed.company_id, parent=parent.id, is_active=True))
    db.commit()
    with pytest.raises(HTTPException) as e:
        department_service.delete_department(db, parent.id, 1)
    _assert_blocked(e.value, "Phòng ban", "PB_CHA", "1 phòng ban con")


def test_csv_phong_ban_da_ngung_410_va_khong_xoa_gi(db, seed, cap_quyen):
    """duoc-CR-628: đường CSV cũ ghi thẳng cột + xóa hàng loạt → ngừng hẳn; dữ liệu không đổi."""
    from app.modules.department.controller import router as dept_router

    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "department", scope="all", read=True, write=True, delete=True)
    free = Department(code="PB_TRONG", name="Phòng trống", company_id=seed.company_id, is_active=True)
    db.add(free)
    db.commit()
    import_csv = _csv_import_endpoint(dept_router)

    with pytest.raises(HTTPException) as e:
        import_csv(file=_upload("Mã PB,Tên phòng ban,Trạng thái\nPB_TRONG,Phòng trống,xóa\n"), db=db, user=user)
    assert e.value.status_code == 410 and "Excel" in e.value.detail
    assert db.get(Department, free.id) is not None
    assert db.get(Department, seed.dept_id) is not None


# ───────────────────────────── Nhân sự ─────────────────────────────
def test_nhan_su_con_phan_cong_thi_400_dong_con_nguyen(db, seed):
    with pytest.raises(HTTPException) as e:
        employee_service.delete_employee(db, seed.emp_nstm_id, 1)
    _assert_blocked(e.value, "Nhân sự", "DEMONV", "2 phân công nhóm hàng (chính)")
    assert db.get(Employee, seed.emp_nstm_id) is not None
    #  Chặn TRƯỚC `detach_users`: tài khoản của người đó không bị khóa oan.
    assert db.get(User, seed.u_nstm_id).is_active is True and db.get(User, seed.u_nstm_id).employee_id == seed.emp_nstm_id


def test_nhan_su_dang_la_quan_ly_cua_nguoi_khac_thi_400(db, seed):
    boss = Employee(code="SEP01", full_name="Sếp", is_active=True)
    db.add(boss)
    db.flush()
    db.add(Employee(code="NV01", full_name="Lính", manager_id=boss.id, is_active=True))
    db.commit()
    with pytest.raises(HTTPException) as e:
        employee_service.delete_employee(db, boss.id, 1)
    _assert_blocked(e.value, "Nhân sự", "SEP01", "1 nhân sự do người này quản lý")


def test_nhan_su_la_chang_duyet_dich_danh_thi_400(db, seed):
    """`approver_ref` là CHUỖI chứa id nhân sự — so được với khóa số (SQLite ép kiểu theo cột, MySQL ép số)."""
    from app.modules.approval.flow_model import APPROVER_EMPLOYEE, APPROVER_ROLE, ApprovalFlow, ApprovalNode

    emp = Employee(code="DUYET01", full_name="Người duyệt", is_active=True)
    db.add(emp)
    db.flush()
    flow = ApprovalFlow(entity="leave_request", code="LF", name="Luồng")
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(emp.id)))
    #  Chặng theo vai trò mang chuỗi khác — không được đếm nhầm vào nhân sự.
    db.add(ApprovalNode(flow_id=flow.id, seq=2, approver_kind=APPROVER_ROLE, approver_ref="admin"))
    db.commit()
    assert rg.count_references(db, "employee", emp) == [("chặng duyệt đích danh", 1)]


def test_nhan_su_chi_con_tai_khoan_thi_van_xoa_va_khoa_tai_khoan_nhu_cu(db, seed):
    """Giả định ai-CR-190: tài khoản gắn hồ sơ KHÔNG tính là tham chiếu (tránh bế tắc với luật «tài khoản còn hồ sơ
    thì không xóa» của `delete_user`) — giữ lối CR-023: xóa hồ sơ → tự khóa + gỡ tài khoản."""
    locked = employee_service.delete_employee(db, seed.emp_req_id, 1)
    assert locked == 1
    assert db.get(Employee, seed.emp_req_id) is None
    u = db.get(User, seed.u_req_id)
    assert u.is_active is False and u.employee_id == 0


def test_csv_nhan_su_da_ngung_410_va_khong_xoa_gi(db, seed, cap_quyen):
    from app.modules.employee.controller import router as emp_router

    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "employee", scope="all", read=True, write=True, delete=True)
    free = Employee(code="NV_TRONG", full_name="Người trống", is_active=True)
    db.add(free)
    db.commit()
    import_csv = _csv_import_endpoint(emp_router)

    with pytest.raises(HTTPException) as e:
        import_csv(file=_upload("Mã NV,Họ tên,Hành động\nNV_TRONG,Người trống,xóa\n"), db=db, user=user)
    assert e.value.status_code == 410 and "Nhập Excel" in e.value.detail
    assert db.get(Employee, free.id) is not None
    assert db.get(Employee, seed.emp_nstm_id) is not None
    assert db.get(User, seed.u_nstm_id).is_active is True


# ───────────────────────────── Tài khoản ─────────────────────────────
def test_tai_khoan_con_phieu_ho_tro_dang_xu_ly_thi_400_het_thi_xoa_kem_phien(db, seed):
    from app.modules.login_session.model import LoginSession
    from app.modules.ticket.model import Ticket

    u = User(email="mo-coi@x", employee_id=0, password_hash="x", is_active=False)
    db.add(u)
    db.commit()
    t = Ticket(code="HT-1", subject="Hỏng máy in", assignee_id=u.id, created_by=1, updated_by=1)
    db.add(t)
    db.add(LoginSession(user_id=u.id, token_id="tok-1"))
    db.commit()

    with pytest.raises(HTTPException) as e:
        user_service.delete_user(db, u.id, 1)
    #  Tài khoản không có `code`/`name` nên câu chặn in id (`reference_guard.deletable_error`) — xem báo cáo ai-CR-190.
    _assert_blocked(e.value, "Tài khoản", u.email, "1 phiếu hỗ trợ đang xử lý")    # tên hiển thị = email
    assert db.get(User, u.id) is not None

    t.assignee_id = 0
    db.commit()
    user_service.delete_user(db, u.id, 1)
    assert db.get(User, u.id) is None
    assert db.query(LoginSession).filter(LoginSession.user_id == u.id).count() == 0   # phiên xóa cứng kèm


def test_tai_khoan_tai_xe_lien_ket_thi_400(db, seed):
    from app.modules.vehicle_booking.model import Driver

    u = User(email="taixe@x", employee_id=0, password_hash="x", is_active=False)
    db.add(u)
    db.commit()
    db.add(Driver(user_id=u.id, name="Tài xế A", created_by=1, updated_by=1))
    db.commit()
    with pytest.raises(HTTPException) as e:
        user_service.delete_user(db, u.id, 1)
    _assert_blocked(e.value, "Tài khoản", u.email, "1 tài xế liên kết")


# ───────────────────────────── Vai trò ─────────────────────────────
def _role(db, code: str) -> Role:
    r = Role(code=code, name=f"Vai trò {code}")
    db.add(r)
    db.flush()
    db.add(Permission(role_id=r.id, entity="ticket", can_read=True))
    db.commit()
    return r


def test_vai_tro_con_nguoi_giu_thi_400_cung_cau_het_thi_xoa_kem_quyen(db, seed):
    r = _role(db, "vt_thu")
    db.add(UserRole(user_id=seed.u_req_id, role_id=r.id))
    db.commit()
    with pytest.raises(HTTPException) as e:
        role_service.delete_role(db, r.id, 1)
    _assert_blocked(e.value, "Vai trò", "vt_thu", "1 tài khoản")
    assert db.get(Role, r.id) is not None

    db.query(UserRole).filter(UserRole.role_id == r.id).delete()
    db.commit()
    role_service.delete_role(db, r.id, 1)
    assert db.get(Role, r.id) is None
    assert db.query(Permission).filter(Permission.role_id == r.id).count() == 0


def test_vai_tro_la_chang_duyet_theo_vai_tro_thi_400(db, seed):
    from app.modules.approval.flow_model import APPROVER_ROLE, ApprovalFlow, ApprovalNode

    r = _role(db, "vt_duyet")
    flow = ApprovalFlow(entity="leave_request", code="LF", name="Luồng")
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, approver_kind=APPROVER_ROLE, approver_ref="vt_duyet"))
    db.commit()
    with pytest.raises(HTTPException) as e:
        role_service.delete_role(db, r.id, 1)
    _assert_blocked(e.value, "Vai trò", "vt_duyet", "1 chặng duyệt theo vai trò")


def test_vai_tro_duoc_cap_quyen_xem_bao_cao_thi_400(db, seed):
    from app.modules.document.access_model import SUBJECT_ROLE
    from app.modules.report_access.model import ReportAccess

    r = _role(db, "vt_bc")
    db.add(ReportAccess(report_key=1, subject_kind=SUBJECT_ROLE, subject_id=r.id, created_by=1, updated_by=1))
    db.commit()
    with pytest.raises(HTTPException) as e:
        role_service.delete_role(db, r.id, 1)
    _assert_blocked(e.value, "Vai trò", "vt_bc", "1 quyền xem báo cáo")
