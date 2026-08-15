"""CR-071 — ô "Trưởng bộ phận" trên YCMH CHỌN ĐƯỢC, nhưng chỉ để LƯU + IN.

Trước bản này ô TBP tự điền theo `Department.manager_id` và không sửa được, nên phòng có
nhiều người ký (phó phòng, quyền trưởng phòng) thì in ra sai tên. Nay phiếu neo thêm
`head_of_dept_id` (id nhân sự) và người lập chọn được trong số những người duyệt được phiếu.

QUAN TRỌNG — chọn ai KHÔNG khóa quyền duyệt. Đã có một bản làm theo hướng "chỉ người được
chỉ định mới bấm Duyệt", khách bác bỏ: người nào có quyền duyệt trên phiếu đó thì vẫn duyệt
được như cũ. Nếu thấy ai đó thêm điều kiện chặn theo `head_of_dept_id`, đó là lỗi hồi quy.
"""
import pytest

from app.core.auth import perm_cache_clear
from app.modules.purchase_request import service as S
from app.modules.purchase_request.model import PurchaseRequest


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    """Cache quyền là in-process theo user.id — mà mỗi test lại dựng DB mới với id lặp lại,
    không xóa thì test sau ăn hồ sơ quyền của test trước."""
    perm_cache_clear()
    yield
    perm_cache_clear()


def _grant(db, user_id: int, entity: str, scope: str, **actions):
    """Cấp cho user một vai trò mới có đúng bộ quyền cần cho ca test."""
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code=f"R{user_id}{scope}{entity[:4]}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                      can_read=actions.get("read", True), can_approve=actions.get("approve", False)))
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return role.id


def _pr(db, seed, **kw):
    pr = PurchaseRequest(code="PYC-CR071", company_id=seed.company_id, department="Phòng Test",
                         status="submitted", created_by=seed.u_req_id, updated_by=seed.u_req_id, **kw)
    db.add(pr)
    db.flush()
    return pr


def _users(db, seed):
    from app.modules.user.model import User
    u_tp = db.query(User).filter(User.employee_id == seed.emp_tp_id).first()
    u_backup = db.query(User).filter(User.employee_id == seed.emp_backup_id).first()
    return u_tp, u_backup


def test_danh_sach_chon_chi_gom_nguoi_that_su_duyet_duoc_phieu_nay(db, seed):
    u_tp, u_backup = _users(db, seed)
    _grant(db, u_tp.id, "purchase_request", "dept", approve=True)
    _grant(db, u_backup.id, "purchase_request", "dept", approve=True)
    # Người yêu cầu chỉ có quyền đọc phạm vi "của mình" -> không phải ứng viên
    _grant(db, seed.u_req_id, "purchase_request", "own", approve=False)
    pr = _pr(db, seed)

    ids = {c["employee_id"] for c in S.dept_head_candidates(db, pr)}
    assert ids == {seed.emp_tp_id, seed.emp_backup_id}


def test_khac_phong_thi_khong_vao_danh_sach_chon(db, seed):
    """Phạm vi 'dept' so theo TÊN PHÒNG của nhân sự — người phòng khác không duyệt được."""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    dep2 = Department(code="DEPT02", name="Phòng Khác", company_id=seed.company_id, is_active=True)
    db.add(dep2)
    db.flush()
    emp2 = Employee(code="TPKHAC", full_name="TP Phòng Khác", company_id=seed.company_id,
                    department_id=dep2.id, is_active=True)
    db.add(emp2)
    db.flush()
    u2 = User(email="TPKHAC", employee_id=emp2.id, password_hash="x", is_active=True)
    db.add(u2)
    db.flush()

    u_tp, _ = _users(db, seed)
    _grant(db, u_tp.id, "purchase_request", "dept", approve=True)
    _grant(db, u2.id, "purchase_request", "dept", approve=True)
    pr = _pr(db, seed)

    ids = {c["employee_id"] for c in S.dept_head_candidates(db, pr)}
    assert ids == {seed.emp_tp_id}


def test_man_tao_moi_tra_ung_vien_theo_phong_ban(db, seed):
    """Màn tạo mới chưa có id phiếu nên phải tra theo tên phòng, và ra cùng một danh sách."""
    u_tp, u_backup = _users(db, seed)
    _grant(db, u_tp.id, "purchase_request", "dept", approve=True)
    _grant(db, u_backup.id, "purchase_request", "dept", approve=True)
    _pr(db, seed)   # phòng đã có phiếu -> soi được bằng chính apply_scope

    ids = {c["employee_id"]
           for c in S.dept_head_candidates_by_department(db, "Phòng Test", seed.company_id)}
    assert ids == {seed.emp_tp_id, seed.emp_backup_id}


def test_man_tao_moi_phong_chua_co_phieu_nao_van_ra_ung_vien(db, seed):
    """Phiếu ĐẦU TIÊN của một phòng: không có phiếu cũ để soi phạm vi, vẫn phải chọn được người."""
    u_tp, u_backup = _users(db, seed)
    _grant(db, u_tp.id, "purchase_request", "dept", approve=True)
    _grant(db, u_backup.id, "purchase_request", "dept", approve=True)

    ids = {c["employee_id"]
           for c in S.dept_head_candidates_by_department(db, "Phòng Test", seed.company_id)}
    assert ids == {seed.emp_tp_id, seed.emp_backup_id}


def test_chon_nguoi_nay_khong_chan_nguoi_kia_duyet(db, seed):
    """Chốt của khách: ô TBP chỉ để lưu, KHÔNG được sinh ra luật chặn duyệt nào.

    Ca này canh lỗi hồi quy — trước đây có bản chặn khiến trưởng phòng "xịn" của phòng mất
    nút Duyệt khi phiếu chỉ tên phó phòng.
    """
    assert not hasattr(S, "designation_blocks"), \
        "Ô TBP chỉ để lưu + in; không được thêm lại luật chặn duyệt theo head_of_dept_id"


def test_dong_bo_ten_theo_id_de_khong_in_mot_dang_luu_mot_neo(db, seed):
    pr = _pr(db, seed, head_of_dept=" tên cũ ", head_of_dept_id=seed.emp_tp_id)
    S.sync_head_of_dept_name(db, pr)
    assert pr.head_of_dept == "Trưởng Phòng"
