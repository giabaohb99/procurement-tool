"""bao-CR-368 — Một email chỉ được thuộc về MỘT hồ sơ nhân sự.

Lỗi thật trên hệ đang chạy (phát hiện 11/09/2026): màn Nhân sự có hai hồ sơ cùng tên
"Danh Hoàng Nguyên" và cùng `dhnguyen.icare@gmail.com` — NSU089 (Nhân sự, tạo 01/07) và
NSU238 (Thủ kho, tạo 11/09). `create_employee` khi đó chỉ kiểm trùng MÃ nhân viên, email
thả nổi hoàn toàn, nên UI cho lưu bình thường.

Email không phải thông tin trang trí, nó là KHOÁ ĐĂNG NHẬP:
  · `authenticate` tra `User.email`;
  · `google_login` tra `Employee.email` rồi `.first()`.
Trùng email nghĩa là người dùng rơi vào hồ sơ nào hoàn toàn do thứ tự bản ghi quyết định —
chức vụ, phòng ban, phiếu của họ đều bám theo hồ sơ "trúng thăm" đó.

Bộ kiểm này canh cả hai cửa ghi: tạo mới và sửa hồ sơ.
"""
import pytest
from fastapi import HTTPException

from app.modules.employee import service as emp_service
from app.modules.employee.schema import EmployeeCreate, EmployeeUpdate

EMAIL = "dhnguyen.icare@gmail.com"


def _tao(db, name: str, email: str = ""):
    return emp_service.create_employee(db, EmployeeCreate(full_name=name, email=email), 1)


def test_tao_nhan_su_trung_email_bi_chan(db, seed):
    """Đúng ca hỏng trên hệ thật: hồ sơ thứ hai cùng email phải bị từ chối."""
    _tao(db, "Danh Hoàng Nguyên", EMAIL)
    with pytest.raises(HTTPException) as e:
        _tao(db, "Danh Hoàng Nguyên", EMAIL)
    assert e.value.status_code == 400
    assert "đã thuộc về nhân sự" in e.value.detail


def test_chan_trung_email_bo_qua_hoa_thuong_va_khoang_trang(db, seed):
    """"A@X.com " và "a@x.com" là cùng một hòm thư — đừng để lách bằng phím Shift."""
    _tao(db, "Người Thứ Nhất", "Nguoi.Mot@Gmail.com")
    with pytest.raises(HTTPException):
        _tao(db, "Người Thứ Hai", "  nguoi.mot@gmail.com  ")


def test_email_rong_khong_tinh_trung(db, seed):
    """Nhiều nhân sự chưa có email và họ đăng nhập bằng mã nhân viên — không được chặn nhóm này."""
    a = _tao(db, "Chưa Có Email A")
    b = _tao(db, "Chưa Có Email B")
    assert a.id != b.id and a.email == "" and b.email == ""


def test_email_duoc_cat_khoang_trang_khi_luu(db, seed):
    """Lưu bản đã cắt khoảng trắng, nếu không lần sau so sánh lại trượt."""
    obj = _tao(db, "Gõ Thừa Dấu Cách", "  co.khoang.trang@gmail.com ")
    assert obj.email == "co.khoang.trang@gmail.com"


def test_sua_ho_so_sang_email_cua_nguoi_khac_bi_chan(db, seed):
    """Cửa thứ hai: không chặn ở màn sửa thì vẫn tạo được cặp trùng, chỉ mất thêm một bước."""
    _tao(db, "Người Giữ Email", EMAIL)
    khac = _tao(db, "Người Khác", "nguoi.khac@gmail.com")
    with pytest.raises(HTTPException) as e:
        emp_service.update_employee(db, khac.id, EmployeeUpdate(email=EMAIL), 1)
    assert e.value.status_code == 400


def test_luu_hong_thi_hoan_tac_ca_lan_luu(db, seed):
    """Báo lỗi thì phải trả hồ sơ về nguyên trạng — không được "lỗi mà vẫn ghi".

    Ca này đi qua cửa kiểm THỨ HAI (`_sync_user_email_from_employee`): email chưa thuộc nhân sự
    nào nên qua được vòng đầu, nhưng lại đang là email đăng nhập của một TÀI KHOẢN khác. Bản cũ
    commit hồ sơ trước rồi mới gọi hàm này, nên người dùng thấy báo đỏ mà email lẫn chức vụ đều
    đã đổi trong cơ sở dữ liệu.
    """
    from app.modules.user.model import User

    giu_cho = _tao(db, "Người Giữ Chỗ", "nguoi.giu.cho@gmail.com")
    db.add(User(employee_id=giu_cho.id, email="handle.rieng@gmail.com", is_active=True))
    nan_nhan = _tao(db, "Người Bị Từ Chối", "nan.nhan@gmail.com")
    db.add(User(employee_id=nan_nhan.id, email="nan.nhan@gmail.com", is_active=True))
    db.flush()

    with pytest.raises(HTTPException):
        emp_service.update_employee(
            db, nan_nhan.id,
            EmployeeUpdate(email="handle.rieng@gmail.com", position="Thủ kho"), 1)

    db.expire_all()
    sau_khi_loi = emp_service.get_employee(db, nan_nhan.id)
    assert sau_khi_loi.email == "nan.nhan@gmail.com"
    assert sau_khi_loi.position == ""


def test_sua_chinh_minh_giu_nguyen_email_van_luu_duoc(db, seed):
    """Lưu lại hồ sơ mà không đổi email thì không được tự coi là trùng với chính nó."""
    obj = _tao(db, "Tự Lưu Lại", "tu.luu.lai@gmail.com")
    emp_service.update_employee(
        db, obj.id, EmployeeUpdate(email="tu.luu.lai@gmail.com", position="Thủ kho"), 1)
    assert emp_service.get_employee(db, obj.id).position == "Thủ kho"
