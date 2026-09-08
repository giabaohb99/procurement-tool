"""
test_danh_muc_chuc_vu.py — DANH MỤC CHỨC VỤ (duoc-CR-320).

Ô «Vị trí / Chức vụ» của hồ sơ nhân sự nay lấy từ `tab_job_position` thay vì gõ
tay. Cái đắt nhất trong thiết kế đó là **hai cột cho một sự thật**: `position_id`
là khóa, còn `position` là nhãn đã chép — mười chỗ (bản in YCMH/YCBG, tệp Excel,
hồ sơ cho trợ lý AI, `core/audit`) vẫn đọc thẳng cột chữ.

Nhãn chép thì nhãn TRÔI. Bộ này canh đúng những nhịp giữ nó khớp, xếp theo mức
thiệt hại:

  1. **Đổi tên trong danh mục phải lan sang mọi hồ sơ đang giữ.** Thiếu nhịp
     này thì màn hình hiện tên mới (nó đọc theo id) còn **bản in đưa cho khách
     vẫn ra tên cũ** — sai lệch lộ ra ở tờ giấy, muộn nhất có thể.
  2. **Gán chức vụ phải chép nhãn**, và bỏ chọn phải xóa nhãn: để lại chữ cũ
     nghĩa là người dùng thấy ô trống trên màn hình mà phiếu in vẫn có chữ.
  3. **Không xóa chức vụ đang có người giữ** — xóa là để lại hồ sơ trỏ vào một
     id không tồn tại, ô chọn hiện trống còn cột nhãn vẫn giữ chữ cũ.
  4. **Không gán được id chết / chức vụ đã ngừng dùng**, nhưng **giữ nguyên
     được** giá trị cũ: cột này không có khóa ngoại cứng, và màn hồ sơ gửi lại
     mọi ô mỗi lần lưu.
"""
import pytest
from fastapi import HTTPException

from app.modules.employee import position_service
from app.modules.employee import service as emp_service
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.schema import EmployeeCreate, EmployeeUpdate


def _position(db, code="TP", name="Trưởng phòng", is_active=True) -> JobPosition:
    obj = JobPosition(code=code, name=name, is_active=is_active)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _emp(db, code="NS001", **kw) -> Employee:
    return emp_service.create_employee(
        db, EmployeeCreate(code=code, full_name=kw.pop("full_name", "Người Thử"), **kw), 1)


# ── 1. Đổi tên lan sang hồ sơ ───────────────────────────────────────────────────

def test_rename_position_updates_label_on_every_holding_profile(db):
    pos = _position(db, name="Trưởng phòng Mua hàg")     # gõ thiếu chữ
    a = _emp(db, code="NS001", position_id=pos.id)
    b = _emp(db, code="NS002", position_id=pos.id)

    touched = position_service.propagate_rename(db, pos, "Trưởng phòng Mua hàng")
    db.commit()

    assert touched == 2
    db.refresh(a)
    db.refresh(b)
    assert a.position == "Trưởng phòng Mua hàng"
    assert b.position == "Trưởng phòng Mua hàng"


def test_rename_leaves_profiles_of_other_positions_untouched(db):
    held = _position(db, code="TP", name="Trưởng phòng")
    other = _position(db, code="NV", name="Nhân viên")
    other_holder = _emp(db, code="NS002", position_id=other.id)

    position_service.propagate_rename(db, held, "Trưởng phòng Kinh doanh")
    db.commit()

    db.refresh(other_holder)
    assert other_holder.position == "Nhân viên"


def test_unchanged_name_writes_nothing(db):
    """Lưu danh mục mà không sửa tên → không được quét bảng nhân sự."""
    pos = _position(db, name="Trưởng phòng")
    _emp(db, code="NS001", position_id=pos.id)
    assert position_service.propagate_rename(db, pos, "Trưởng phòng") == 0
    assert position_service.propagate_rename(db, pos, "") == 0


# ── 2. Gán / bỏ chọn chức vụ trên hồ sơ ─────────────────────────────────────────

def test_assigning_position_copies_label_onto_profile(db):
    pos = _position(db, name="Kế toán trưởng")
    emp = _emp(db, code="NS001")
    assert emp.position == ""

    emp_service.update_employee(db, emp.id, EmployeeUpdate(position_id=pos.id), 1)

    db.refresh(emp)
    assert emp.position_id == pos.id
    assert emp.position == "Kế toán trưởng"


def test_clearing_position_also_clears_label(db):
    """Để lại chữ cũ = màn hình trống nhưng phiếu in vẫn có chức danh."""
    pos = _position(db, name="Kế toán trưởng")
    emp = _emp(db, code="NS001", position_id=pos.id)

    emp_service.update_employee(db, emp.id, EmployeeUpdate(position_id=0), 1)

    db.refresh(emp)
    assert (emp.position_id, emp.position) == (0, "")


def test_save_without_position_field_leaves_it_untouched(db):
    """Màn hồ sơ gửi PATCH một phần — sửa số điện thoại không được xóa chức vụ."""
    pos = _position(db, name="Kế toán trưởng")
    emp = _emp(db, code="NS001", position_id=pos.id)

    emp_service.update_employee(db, emp.id, EmployeeUpdate(phone="0900000000"), 1)

    db.refresh(emp)
    assert (emp.position_id, emp.position) == (pos.id, "Kế toán trưởng")


def test_creating_profile_also_copies_label(db):
    pos = _position(db, name="Thủ kho")
    emp = _emp(db, code="NS001", position_id=pos.id)
    assert emp.position == "Thủ kho"


def test_creating_profile_with_text_only_keeps_the_text(db):
    """Đường nhập CSV, seed và mã cũ truyền `position` chữ mà không có khóa.

    Luật "khóa = 0 thì xóa nhãn" chỉ đúng ở đường CẬP NHẬT (người dùng vừa bỏ
    chọn). Áp cả vào lúc TẠO thì hồ sơ mất chức danh ngay khi ra đời, im lặng —
    lỗi thật đã dính khi làm duoc-CR-320, `test_employee_position.py` bắt được.
    """
    emp = _emp(db, code="NS001", position="Nhân viên kho")
    assert (emp.position, emp.position_id) == ("Nhân viên kho", 0)


# ── 3. Chốt chặn xóa ───────────────────────────────────────────────────────────

def test_counts_the_profiles_currently_holding_position(db):
    pos = _position(db)
    _emp(db, code="NS001", position_id=pos.id)
    _emp(db, code="NS002", position_id=pos.id)
    _emp(db, code="NS003")

    assert position_service.count_employees(db, pos.id) == 2


def test_position_with_no_holder_counts_zero(db):
    pos = _position(db)
    assert position_service.count_employees(db, pos.id) == 0


# ── 4. Chốt gán: id chết, chức vụ đã ngừng ─────────────────────────────────────

def test_assigning_dead_id_is_blocked(db):
    """Cột không có khóa ngoại cứng — không chặn ở đây thì id chết ghi xuống êm ru."""
    emp = _emp(db, code="NS001")
    with pytest.raises(HTTPException) as e:
        emp_service.update_employee(db, emp.id, EmployeeUpdate(position_id=99999), 1)
    assert e.value.status_code == 400


def test_assigning_inactive_position_anew_is_blocked(db):
    retired = _position(db, code="CU", name="Chức vụ cũ", is_active=False)
    emp = _emp(db, code="NS001")
    with pytest.raises(HTTPException) as e:
        emp_service.update_employee(db, emp.id, EmployeeUpdate(position_id=retired.id), 1)
    assert "ngừng dùng" in e.value.detail


def test_profile_already_holding_inactive_position_still_saves(db):
    """Màn hồ sơ gửi lại MỌI ô mỗi lần lưu.

    Không có ngoại lệ này thì một người bị Nhân sự cho ngừng chức vụ sẽ **không
    sửa nổi ô nào khác** — mỗi lần bấm Lưu đều ăn câu «chức vụ đã ngừng dùng» —
    cho tới khi có ai đó đi đổi chức vụ của họ.
    """
    pos = _position(db, name="Chức vụ sắp bỏ")
    emp = _emp(db, code="NS001", position_id=pos.id)
    pos.is_active = False
    db.commit()

    emp_service.update_employee(
        db, emp.id, EmployeeUpdate(position_id=pos.id, phone="0900000000"), 1)

    db.refresh(emp)
    assert emp.position_id == pos.id


# ── 5. Khớp tên cho đường nhập CSV ─────────────────────────────────────────────

def test_name_matching_ignores_case_and_extra_spaces(db):
    """Tệp CSV người dùng sửa trong Excel: «Trưởng phòng » và «trưởng PHÒNG» là một."""
    pos = _position(db, name="Trưởng phòng")
    assert position_service.resolve_by_name(db, "  trưởng PHÒNG  ").id == pos.id
    #  Dấu cách ĐÔI ở GIỮA cũng khớp: `" ".join(s.split())` bóp mọi cụm khoảng
    #  trắng, không chỉ hai đầu. Cố ý — gõ thừa một dấu cách giữa hai chữ là lỗi
    #  gõ hay gặp nhất trong Excel, và nó vô hình trên màn hình.
    assert position_service.resolve_by_name(db, "Trưởng  phòng").id == pos.id
    #  Nhưng KHÁC CHỮ thì không khớp — bỏ dấu không phải cùng một chức vụ.
    assert position_service.resolve_by_name(db, "Truong phong") is None


def test_unmatched_name_returns_none_and_never_auto_creates(db):
    """Tự tạo thì mỗi lỗi gõ trong một tệp CSV đẻ ra một dòng danh mục rác."""
    _position(db, name="Trưởng phòng")
    assert position_service.resolve_by_name(db, "Trưởng phòng Mua hàng") is None
    assert db.query(JobPosition).count() == 1


def test_name_matching_skips_inactive_positions(db):
    _position(db, code="CU", name="Chức vụ cũ", is_active=False)
    assert position_service.resolve_by_name(db, "Chức vụ cũ") is None


def test_blank_name_matches_nothing(db):
    _position(db, name="Trưởng phòng")
    assert position_service.resolve_by_name(db, "") is None
    assert position_service.resolve_by_name(db, "   ") is None


# ── 6. Ràng buộc kích thước (SQLite KHÔNG ép, phải kiểm ở tầng SCHEMA) ─────────

def test_overlong_name_is_blocked_at_schema_level():
    """Bài học duoc-CR-316: thiếu `max_length` thì chuỗi dài xuống thẳng MySQL và
    người dùng nhận «mã sự cố» thay vì câu «tối đa 100 ký tự»."""
    from pydantic import ValidationError

    from app.modules.employee.position_schema import JobPositionCreate

    with pytest.raises(ValidationError):
        JobPositionCreate(code="TP", name="x" * 101)
    with pytest.raises(ValidationError):
        JobPositionCreate(code="x" * 31, name="Trưởng phòng")
    with pytest.raises(ValidationError):
        JobPositionCreate(code="TP", name="Trưởng phòng", note="x" * 501)


def test_blank_code_and_name_are_blocked():
    """Tên rỗng → ô chọn hiện một mục trắng không bấm trúng; mã rỗng → chỉ tồn tại
    được ĐÚNG MỘT dòng như vậy, lần sau người dùng ăn lỗi trùng mã khó hiểu."""
    from pydantic import ValidationError

    from app.modules.employee.position_schema import JobPositionCreate, JobPositionUpdate

    with pytest.raises(ValidationError):
        JobPositionCreate(code="TP", name="   ")
    with pytest.raises(ValidationError):
        JobPositionCreate(code="", name="Trưởng phòng")
    with pytest.raises(ValidationError):
        JobPositionUpdate(name="  ")


def test_update_schema_rejects_code():
    """Mã đi vào tệp CSV đã phát ra ngoài — đổi nó là mọi tệp đó trỏ chỗ khác."""
    from app.modules.employee.position_schema import JobPositionUpdate

    data = JobPositionUpdate.model_validate({"code": "MOI", "name": "Trưởng phòng"})
    assert "code" not in data.model_dump(exclude_unset=True)


# ── 7. Đếm NGƯỢC: ai đang giữ chức vụ này (duoc-CR-322) ───────────────────────
#
#  Con số này là thứ người quản lý danh mục đọc TRƯỚC khi sửa hay dẹp một chức
#  vụ. Ba thứ dễ sai và đều im lặng: đếm nhầm sang chức vụ khác, bỏ rơi hồ sơ
#  chưa gắn phòng ban (tổng không khớp tổng các dòng phòng), và gộp nhầm hồ sơ
#  "chưa gán chức vụ" (`position_id = 0`) thành một chức vụ có thật.

def _department(db, code, name) -> int:
    """Phòng ban THẬT — `create_employee` chặn `department_id` không tồn tại."""
    from app.modules.department.model import Department

    obj = Department(code=code, name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj.id


def _count_by_department(db, **kw):
    """Gọi hàm đếm với truy vấn KHÔNG lọc phạm vi — bài kiểm không dựng RBAC."""
    return position_service.count_holders_by_department(db, db.query(Employee), **kw)


def test_reverse_count_groups_by_position_and_department(db):
    manager = _position(db, code="TP", name="Trưởng phòng")
    staff = _position(db, code="NV", name="Nhân viên")
    sales = _department(db, "KD", "Phòng Kinh doanh")
    accounting = _department(db, "KT", "Phòng Kế toán")
    _emp(db, code="NS001", position_id=manager.id, department_id=sales)
    _emp(db, code="NS002", position_id=staff.id, department_id=sales)
    _emp(db, code="NS003", position_id=staff.id, department_id=accounting)
    _emp(db, code="NS004", position_id=staff.id, department_id=accounting)

    stats = _count_by_department(db)

    assert stats[manager.id]["total"] == 1
    assert stats[staff.id]["total"] == 3
    #  Phòng đông người hơn đứng trước — đó là phòng người đọc muốn biết.
    assert [d["count"] for d in stats[staff.id]["departments"]] == [2, 1]


def test_profile_without_position_never_becomes_a_row(db):
    """`position_id = 0` là *chưa gán*, không phải một chức vụ có mã 0."""
    _position(db, code="TP", name="Trưởng phòng")
    _emp(db, code="NS001", department_id=_department(db, "KD", "Phòng Kinh doanh"))

    assert _count_by_department(db) == {}


def test_profile_without_department_still_appears(db):
    """Bỏ nhóm `department_id = 0` thì tổng KHÔNG khớp tổng các dòng phòng ban,
    và người đọc đi tìm dòng còn thiếu."""
    manager = _position(db, code="TP", name="Trưởng phòng")
    _emp(db, code="NS001", position_id=manager.id,
         department_id=_department(db, "KD", "Phòng Kinh doanh"))
    _emp(db, code="NS002", position_id=manager.id)          # chưa gắn phòng

    entry = _count_by_department(db)[manager.id]

    assert entry["total"] == 2
    assert sum(d["count"] for d in entry["departments"]) == 2
    assert any(d["id"] == 0 for d in entry["departments"])


def test_position_with_no_holder_is_absent_from_result(db):
    """Giao diện đọc `?? 0`; trả về dòng total=0 chỉ tốn băng thông."""
    unused = _position(db, code="TRONG", name="Chức vụ chưa dùng")

    assert unused.id not in _count_by_department(db)


def test_faces_respect_the_cap_per_position_without_bleeding(db):
    """Cắt Ở PYTHON theo từng chức vụ: một `LIMIT` cho cả bảng thì chức vụ đứng
    sau mất sạch gương mặt."""
    crowded = _position(db, code="NV", name="Nhân viên")
    sparse = _position(db, code="TP", name="Trưởng phòng")
    cap = position_service.HOLDER_FACES_PER_POSITION
    for i in range(cap + 3):
        _emp(db, code=f"NS{i:03d}", full_name=f"Người Thử {i:02d}", position_id=crowded.id)
    _emp(db, code="NS900", full_name="Sếp Lớn", position_id=sparse.id)

    faces = position_service.list_holder_faces(db, db.query(Employee))

    assert len(faces[crowded.id]) == cap
    #  Chức vụ ít người KHÔNG bị câu trần của chức vụ đông người nuốt mất.
    assert [f["full_name"] for f in faces[sparse.id]] == ["Sếp Lớn"]


def test_faces_gather_holders_across_departments(db):
    """Gom theo CHỨC VỤ, không tách theo phòng: cột «Đang giữ» hỏi *ai đang mang
    chức danh này*, phòng nào là câu hỏi của cột bên cạnh."""
    staff = _position(db, code="NV", name="Nhân viên")
    sales = _department(db, "KD", "Phòng Kinh doanh")
    accounting = _department(db, "KT", "Phòng Kế toán")
    _emp(db, code="NS001", full_name="Người Kinh Doanh", position_id=staff.id, department_id=sales)
    _emp(db, code="NS002", full_name="Người Kế Toán", position_id=staff.id, department_id=accounting)

    faces = position_service.list_holder_faces(db, db.query(Employee))

    assert sorted(f["full_name"] for f in faces[staff.id]) == ["Người Kinh Doanh", "Người Kế Toán"]


def test_profile_without_account_yields_blank_avatar(db):
    """Ảnh đại diện lưu ở `tab_user`; hồ sơ chưa được cấp tài khoản thì rỗng và
    giao diện rơi về chữ viết tắt — không phải lỗi."""
    manager = _position(db, code="TP", name="Trưởng phòng")
    _emp(db, code="NS001", position_id=manager.id)

    faces = position_service.list_holder_faces(db, db.query(Employee))

    assert faces[manager.id][0]["avatar"] == ""
