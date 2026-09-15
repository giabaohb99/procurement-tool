"""KHÓA TÀI KHOẢN THÌ THÔI GIAO VIỆC DUYỆT (duoc-CR-398).

Lỗi đo được ngày 14/09/2026 trên máy chạy thật, bằng cách tắt `User.is_active`
của một nhân sự mà GIỮ NGUYÊN hồ sơ nhân sự:

    đăng nhập  : BỊ CHẶN 401
    luồng duyệt: VẪN CHỌN  -> [6]
    email      : KHÔNG AI NHẬN -> []

`approver_resolver._only_active_employees` lọc theo `Employee.is_active`, còn
`task_notification._accounts` lọc theo `User.is_active` — hai nơi dùng hai định
nghĩa khác nhau cho cùng một câu hỏi "người này còn dùng hệ thống không". Ghép
lại ra ca tệ nhất: việc GIAO cho người không đăng nhập được, mà cũng KHÔNG ai
được báo. Phiếu đứng im vĩnh viễn, không toast, không log, không chỗ nào đỏ lên
— và `task_service` / `instance_service` không có chốt nào bắt lại.

Bài kiểm hỏi theo HẬU QUẢ ("người không bấm được thì đừng giao"), không hỏi theo
cách cài đặt, nên đổi cách lọc mà vẫn đúng ý thì test vẫn xanh.
"""
from app.modules.approval.approver_resolver import _only_active_employees
from app.modules.employee.model import Employee
from app.modules.user.model import User


def _nhan_su(db, code: str, *, active: bool = True) -> Employee:
    emp = Employee(code=code, full_name=f"NS {code}", is_active=active)
    db.add(emp)
    db.commit()
    return emp


def _tai_khoan(db, emp: Employee, *, active: bool = True) -> User:
    user = User(
        email=f"{emp.code}@dego.test",
        password_hash="x",
        employee_id=emp.id,
        is_active=active,
    )
    db.add(user)
    db.commit()
    return user


def test_tai_khoan_bi_khoa_thi_khong_con_duoc_chon_lam_nguoi_duyet(db):
    """Chính ca đo được 14/09/2026: hồ sơ nhân sự VẪN đang làm, chỉ khóa tài khoản."""
    emp = _nhan_su(db, "KHOA01")
    _tai_khoan(db, emp, active=False)

    assert emp.is_active is True, "hồ sơ nhân sự phải còn nguyên — đó là điểm mấu chốt"
    assert _only_active_employees(db, [emp.id]) == []


def test_tai_khoan_dang_mo_thi_van_duoc_giao_binh_thuong(db):
    emp = _nhan_su(db, "MO01")
    _tai_khoan(db, emp, active=True)

    assert _only_active_employees(db, [emp.id]) == [emp.id]


def test_chua_duoc_cap_tai_khoan_thi_GIU_NGUYEN(db):
    """Quyết 14/09/2026 (phương án A).

    Người chưa có tài khoản cũng không bấm được, nhưng loại họ ở đây là âm thầm
    đổi định tuyến của những luồng đang chạy trên hệ thật — nơi có thể còn hồ sơ
    chưa kịp cấp tài khoản. Chỉ loại người ĐÃ CÓ tài khoản mà mọi tài khoản đều
    đang khóa.
    """
    emp = _nhan_su(db, "CHUACAP")

    assert db.query(User).filter(User.employee_id == emp.id).count() == 0
    assert _only_active_employees(db, [emp.id]) == [emp.id]


def test_con_mot_tai_khoan_dang_mo_thi_van_giao(db):
    """Một người có thể mang NHIỀU tài khoản — xem `lock_linked_users` cũng duyệt `.all()`.

    Khóa bớt một cái mà vẫn còn cái khác mở thì họ vẫn đăng nhập được, nên vẫn
    phải giao việc. Lọc kiểu "có bất kỳ tài khoản khóa nào thì loại" là sai.
    """
    emp = _nhan_su(db, "HAITK")
    _tai_khoan(db, emp, active=False)
    thu_hai = User(
        email="haitk2@dego.test",
        password_hash="x",
        employee_id=emp.id,
        is_active=True,
    )
    db.add(thu_hai)
    db.commit()

    assert _only_active_employees(db, [emp.id]) == [emp.id]


def test_nghi_viec_van_bi_loai_nhu_cu(db):
    """Vế cũ của hàm không được rơi mất khi thêm vế tài khoản."""
    emp = _nhan_su(db, "NGHI01", active=False)
    _tai_khoan(db, emp, active=True)

    assert _only_active_employees(db, [emp.id]) == []


def test_giu_nguyen_thu_tu_khai_va_bo_trung(db):
    """Thứ tự có nghĩa với bước «lần lượt» — lọc thêm điều kiện không được xáo nó."""
    a = _nhan_su(db, "TT_A")
    b = _nhan_su(db, "TT_B")
    c = _nhan_su(db, "TT_C")
    for emp in (a, b, c):
        _tai_khoan(db, emp)
    khoa = _nhan_su(db, "TT_KHOA")
    _tai_khoan(db, khoa, active=False)

    ids = [c.id, khoa.id, a.id, c.id, b.id]
    assert _only_active_employees(db, ids) == [c.id, a.id, b.id]


def test_danh_sach_rong_thi_tra_rong_khong_no(db):
    assert _only_active_employees(db, []) == []
