"""Bộ lọc của màn QUỸ PHÉP NĂM — tìm theo tên / mã nhân sự.

`apply_filters` chỉ lọc được cột của chính bảng quỹ, mà bảng đó chỉ giữ
`employee_id` — người dùng thì tìm bằng TÊN. Không có đường này thì màn Quỹ phép
chỉ còn cách cuộn tay: một công ty vài trăm người là vài chục trang.

⚠️ Bài quan trọng nhất là `test_khong_ai_khop_thi_tra_RONG`. Cách viết ẩu nhất
cho hàm này là "không tìm thấy ai thì thôi không lọc" — và lúc đó gõ sai một chữ
lại ra nguyên cả bảng, người dùng nhìn 39 dòng rồi tưởng mình vừa tìm đúng.
"""
import pytest

from app.modules.employee.model import Employee
from app.modules.leave.balance_controller import apply_employee_search
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType

ACTOR = 1


@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def nhan_su(db, leave_type):
    """Ba người, tên và mã cố tình có phần chồng nhau để bắt lỗi khớp lỏng."""
    rows = [
        ("DEMOTP", "Trần Trưởng Phòng"),
        ("DEMOTP2", "Lý Phó Phòng"),
        ("NV001", "Nguyễn Văn Nhân Viên"),
    ]
    created = []
    for code, name in rows:
        employee = Employee(code=code, full_name=name, company_id=1,
                            department_id=7, is_active=True)
        db.add(employee)
        db.flush()
        db.add(LeaveBalance(employee_id=employee.id, year=2026,
                            leave_type_id=leave_type.id, allocated_days=12.0,
                            created_by=ACTOR, updated_by=ACTOR))
        created.append(employee)
    db.commit()
    return created


def _search(db, keyword):
    query = apply_employee_search(db, db.query(LeaveBalance), keyword)
    return sorted(row.employee_id for row in query.all())


def _ids(employees, *names):
    return sorted(e.id for e in employees if e.full_name in names)


def test_tim_theo_TEN(db, nhan_su):
    assert _search(db, "Trưởng Phòng") == _ids(nhan_su, "Trần Trưởng Phòng")


def test_tim_theo_MA_nhan_su(db, nhan_su):
    """Nhân sự hay được gọi bằng mã hơn tên — bỏ vế này là nửa số lượt tìm hụt."""
    assert _search(db, "NV001") == _ids(nhan_su, "Nguyễn Văn Nhân Viên")


def test_khong_phan_biet_hoa_thuong(db, nhan_su):
    """Không ai gõ đúng hoa thường của tên người khác."""
    assert _search(db, "trƯỞng phÒng") == _search(db, "Trưởng Phòng")


def test_khop_GIUA_chuoi_chu_khong_chi_dau_chuoi(db, nhan_su):
    """Người ta nhớ tên riêng («Phòng») chứ ít khi nhớ họ."""
    assert _search(db, "Phó") == _ids(nhan_su, "Lý Phó Phòng")


def test_khong_ai_khop_thi_tra_RONG(db, nhan_su):
    """ĐỪNG nới bài này. Bỏ qua bộ lọc khi không khớp ai thì gõ sai một chữ lại
    ra nguyên cả bảng, và người dùng tưởng mình vừa tìm đúng."""
    assert _search(db, "zzzkhongcoai") == []


@pytest.mark.parametrize("keyword", [None, "", "   ", "\n\t "])
def test_tu_khoa_rong_thi_KHONG_loc_gi(db, nhan_su, keyword):
    """Ô tìm để trống phải ra cả bảng, không phải ra rỗng."""
    assert _search(db, keyword) == sorted(e.id for e in nhan_su)


def test_mot_tu_khoa_khop_NHIEU_nguoi_thi_ra_du(db, nhan_su):
    """«Phòng» khớp cả hai người — trả thiếu là người dùng tưởng chỉ có một."""
    assert _search(db, "Phòng") == _ids(nhan_su, "Trần Trưởng Phòng", "Lý Phó Phòng")


def test_ma_khop_TIEN_TO_thi_ra_ca_nhom(db, nhan_su):
    """`DEMOTP` khớp cả `DEMOTP2` — đúng ý người gõ mã rút gọn để quét một nhóm."""
    assert _search(db, "DEMOTP") == _ids(nhan_su, "Trần Trưởng Phòng", "Lý Phó Phòng")


def test_ky_tu_dac_biet_cua_LIKE_khong_lam_no(db, nhan_su):
    """`%` và `_` là ký tự đại diện của LIKE. Người dùng gõ vào không được nổ,
    và cũng không được biến thành "khớp mọi thứ"."""
    for keyword in ("%", "_", "%%%", "'"):
        _search(db, keyword)   # không ném là đạt
