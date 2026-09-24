"""bao-CR-474 — NGƯỜI ĐƯỢC CHỌN Ở Ô «TRƯỞNG BỘ PHẬN» CŨNG NHẬN CHUÔNG BÁO DUYỆT.

Ô TBP của YCMH cho chọn một người trong số những người duyệt được phiếu (CR-071). Trước
CR này, chọn ai thì chuông «cần bạn phê duyệt» VẪN chỉ đi theo phòng ban — trưởng phòng
gán cứng (`Department.manager_id`) + tài khoản vai trò `dept_head` của phòng — nên người
được chọn nếu khác trưởng phòng mặc định thì không hề biết có phiếu chờ mình.

Luồng duyệt này KHÔNG gửi email (chỉ chuông + web push) — xem `trigger_notification`.

Kèm theo: `/meta/dept-head` trả thêm `head_of_dept_id` để màn tạo mới v2 điền sẵn đúng
NGƯỜI (ô chọn cần id), không chỉ cái tên.
"""
import json

from fastapi import BackgroundTasks

from app.modules.department.model import Department
from app.modules.notification.model import Notification
from app.modules.notification.service import trigger_notification
from app.modules.purchase_request.controller import dept_head
from app.modules.user.model import User


def _uid(db, employee_id):
    return db.query(User.id).filter(User.employee_id == employee_id).scalar()


def _notified(db):
    return {n.user_id for n in db.query(Notification).all()}


def _submit(db, seed, **kw):
    trigger_notification(db=db, event="pr_submitted", doc_type="purchase_request", doc_code="PYCTEST",
                         creator_id=seed.u_req_id, background_tasks=BackgroundTasks(),
                         department="Phòng Test", department_id=seed.dept_id, **kw)


def _with_head(db, seed):
    dep = db.get(Department, seed.dept_id)
    dep.manager_id = seed.emp_tp_id
    db.commit()


def test_mac_dinh_chi_truong_phong_gan_cung_nhan(db, seed):
    _with_head(db, seed)
    _submit(db, seed)
    assert _notified(db) == {_uid(db, seed.emp_tp_id)}


def test_nguoi_duoc_chon_o_tbp_cung_nhan(db, seed):
    """Chọn một người KHÁC trưởng phòng mặc định → cả hai cùng nhận, không ai bị bỏ."""
    _with_head(db, seed)
    _submit(db, seed, extra_employee_ids=[seed.emp_backup_id])
    assert _notified(db) == {_uid(db, seed.emp_tp_id), _uid(db, seed.emp_backup_id)}


def test_chon_dung_truong_phong_thi_khong_nhan_doi(db, seed):
    _with_head(db, seed)
    _submit(db, seed, extra_employee_ids=[seed.emp_tp_id])
    assert db.query(Notification).count() == 1


def test_tai_khoan_da_khoa_khong_nhan(db, seed):
    _with_head(db, seed)
    u = db.query(User).filter(User.employee_id == seed.emp_backup_id).one()
    u.is_active = False
    db.commit()
    _submit(db, seed, extra_employee_ids=[seed.emp_backup_id])
    assert _notified(db) == {_uid(db, seed.emp_tp_id)}


def test_meta_dept_head_tra_ca_id(db, seed):
    """Màn tạo mới v2 cần id để ô chọn hiện đúng người ngay từ đầu."""
    _with_head(db, seed)
    body = json.loads(dept_head(department="", department_id=seed.dept_id, db=db, user=None).body)
    assert body["data"]["head_of_dept_id"] == seed.emp_tp_id
    assert body["data"]["head_of_dept"] == "Trưởng Phòng"
