"""CÔNG TY CỦA NHÂN SỰ PHẢI RA TỚI GIAO DIỆN (26/08/2026).

Cột `tab_employee.company_id` có từ đầu nhưng `EmployeeOut` **chưa bao giờ trả
tên pháp nhân**, nên mở hồ sơ ra không biết người này thuộc công ty nào — trong
khi pháp nhân chính là thứ quyết định phạm vi dữ liệu họ nhìn thấy.

Hai điều bài kiểm này giữ:

  1. `company_name` có mặt trong phản hồi, và đúng tên;
  2. danh sách **nạp gộp** quan hệ `company` — thiếu `selectinload` thì mỗi dòng
     tự lazy-load thành N+1, mà lỗi kiểu đó không bao giờ lộ ra ở màn hình, chỉ
     lộ ra lúc bảng lên vài nghìn dòng.
"""
from app.modules.company.model import Company
from app.modules.employee import service as emp_service
from app.modules.employee.schema import EmployeeCreate, EmployeeOut


def test_ho_so_tra_ve_ten_cong_ty(db, seed):
    obj = emp_service.create_employee(db, EmployeeCreate(
        full_name="Nhân Viên A", company_id=seed.company_id), 1)
    db.commit()

    out = EmployeeOut.model_validate(obj)
    assert out.company_id == seed.company_id
    assert out.company_name == "Cty Test"


def test_chua_gan_cong_ty_thi_de_trong_chu_khong_no(db, seed):
    """Hồ sơ cũ chưa gán pháp nhân vẫn phải đọc được — giao diện tự hiện gạch."""
    obj = emp_service.create_employee(db, EmployeeCreate(full_name="Nhân Viên B"), 1)
    db.commit()

    assert EmployeeOut.model_validate(obj).company_name is None


def _dem_truy_van(db, line_count: int) -> tuple[int, list]:
    """Đếm số truy vấn để dựng một trang danh sách `so_dong` dòng."""
    from sqlalchemy import event

    from app.modules.employee.model import Employee

    count = {"n": 0}

    def _ghi(conn, cursor, statement, params, context, executemany):
        count["n"] += 1

    #  ⚠️ `expunge_all`, KHÔNG phải `expire_all`. `expire_all` chỉ đánh dấu thuộc
    #  tính là cũ nhưng ĐỂ NGUYÊN đối tượng trong identity map, nên `emp.company`
    #  vẫn lấy được từ bộ nhớ mà không cần truy vấn — bản đầu của bài kiểm này
    #  dùng `expire_all` và nó XANH cả khi đã gỡ `selectinload(Employee.company)`,
    #  tức là một bài kiểm rỗng. Đẩy hết ra khỏi phiên thì quan hệ buộc phải đi
    #  hỏi CSDL, và N+1 mới lộ ra.
    db.expunge_all()
    event.listen(db.get_bind(), "before_cursor_execute", _ghi)
    try:
        _, items = emp_service.list_employees(
            db, db.query(Employee), {"offset": 0, "limit": line_count})
        name = [EmployeeOut.model_validate(row).company_name for row in items]
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _ghi)
    return count["n"], name


def test_danh_sach_NAP_GOP_khong_de_thanh_N_cong_1(db, seed):
    """Chốt hiệu năng, không chốt hiển thị.

    `company_name` đọc qua quan hệ `Employee.company`, nên thiếu `selectinload`
    là mỗi dòng một truy vấn thêm.

    ⚠️ Đo bằng **tính chất**, không bằng một con số ma: chạy hai lượt với số dòng
    khác hẳn nhau rồi đòi số truy vấn **y hệt**. Ngưỡng kiểu `<= 6` thì vừa dễ đỏ
    oan khi thêm một quan hệ chính đáng, vừa lọt N+1 ở trang nhỏ.

    Bài này đã bắt được một lỗi CÓ SẴN TỪ TRƯỚC: `department_name` và
    `manager_name` cũng đọc qua quan hệ nên danh sách vốn đã N+1, chỉ là chưa ai
    đo. Đã nạp gộp cả hai (`manager_name` đi qua hai cấp nên phải nối chuỗi).
    """
    #  ⚠️ MỖI NGƯỜI MỘT CÔNG TY RIÊNG. Cho cả 25 người chung một pháp nhân thì
    #  bài kiểm rỗng: dù không nạp gộp, SQLAlchemy chỉ hỏi CSDL đúng MỘT lần cho
    #  pháp nhân đó rồi lấy lại từ identity map — số truy vấn vẫn là hằng số và
    #  N+1 không lộ ra. Bản đầu của bài này dính đúng chỗ đó.
    def _add(so_luong: int, tu: int = 0) -> None:
        for i in range(tu, tu + so_luong):
            cty = Company(code=f"C{i:03d}", name=f"Công ty {i}", is_active=True)
            db.add(cty)
            db.flush()
            emp_service.create_employee(db, EmployeeCreate(
                full_name=f"Nhân Viên {i}", company_id=cty.id), 1)
        db.commit()

    _add(3)
    it_dong, name = _dem_truy_van(db, 3)
    assert "Công ty 2" in name

    _add(22, tu=3)

    nhieu_dong, _ = _dem_truy_van(db, 25)

    assert nhieu_dong == it_dong, (
        f"N+1: 3 dòng tốn {it_dong} truy vấn, 25 dòng tốn {nhieu_dong} — "
        "số truy vấn phải là hằng số, không chạy theo số dòng"
    )
