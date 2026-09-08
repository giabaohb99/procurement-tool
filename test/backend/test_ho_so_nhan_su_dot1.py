"""
test_ho_so_nhan_su_dot1.py — HRM Đợt 1: nền dữ liệu hồ sơ nhân sự.

Thiết kế: `doc/erp/hrm/01-ho-so-nhan-su.md`. Bộ này canh bốn thứ dễ vỡ nhất,
xếp theo mức thiệt hại nếu vỡ:

  1. **Che nhóm nhạy cảm ở tầng SERIALIZER.** Ẩn ô trên giao diện thì API, tệp
     xuất và trợ lý AI vẫn trả nguyên số tài khoản ngân hàng của cả công ty.
  2. **Ngoại lệ `self`** — ai cũng đọc được hồ sơ của chính mình, và nhánh này
     phải chặn `employee_id = 0` (tài khoản chưa gắn nhân sự), nếu không «chưa
     gắn ai» hóa ra khớp mọi hồ sơ.
  3. **Vòng quản lý.** `manager_id` là thứ bộ máy duyệt đọc để tìm người ký; A
     quản lý B, B quản lý A thì mọi vòng dò cấp trên chạy mãi không dừng — và
     nó nổ lúc ai đó nộp đơn nghỉ phép, không phải lúc lưu hồ sơ.
  4. **`employee_sensitive` KHÔNG được rơi vào vai trò nghiệp vụ.** Quản lý thu
     mua đọc được CCCD của toàn công ty là một dòng `for e in ENTITIES` vô tình.
"""
import pytest
from fastapi import HTTPException

from app.core.permissions import ENTITIES
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.modules.employee import contact_service, sensitive
from app.modules.employee import service as emp_service
from app.modules.employee.constants import RELATION_FATHER, RELATION_SON
from app.modules.employee.model import Employee
from app.modules.employee.schema import (EmployeeContactIn, EmployeeFamilyIn,
                                         EmployeeOut, EmployeeUpdate)


def _profile(*, sensitive_read=False, employee_id=0) -> dict:
    """Hồ sơ quyền tối thiểu — đúng hình dạng `get_perm_profile` trả về."""
    perms = {"employee": {"read": True}}
    if sensitive_read:
        perms["employee_sensitive"] = {"read": True}
    return {"perms_union": perms, "employee_id": employee_id}


def _emp(db, code="NS001", **kw):
    obj = Employee(code=code, full_name=kw.pop("full_name", "Người Thử"),
                   is_active=True, **kw)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── 1. Che nhóm nhạy cảm ────────────────────────────────────────────────────

def test_without_permission_sensitive_fields_come_back_blank(db):
    from datetime import date

    emp = _emp(db, bank_account_no="1903 8888 8888", id_number="079203001234",
               permanent_address="12 Nguyễn Huệ, Q1", date_of_birth=date(1990, 5, 1),
               health_care_place="BV Thống Nhất")
    data = EmployeeOut.model_validate(emp).model_dump()

    out = sensitive.mask(dict(data), allowed=False)
    assert out["bank_account_no"] == ""
    assert out["id_number"] == ""
    assert out["permanent_address"] == ""
    assert out["date_of_birth"] is None, "ô NGÀY phải che thành None, nhét '' vào là 500"
    #  Nơi khám chữa bệnh CỐ Ý không nằm trong nhóm — hành chính hỏi nhau hằng
    #  ngày để làm thủ tục, giấu nó chỉ đẻ ra một vòng hỏi qua Zalo.
    assert out["health_care_place"] == "BV Thống Nhất"


def test_with_permission_values_are_kept(db):
    emp = _emp(db, bank_account_no="1903 8888 8888")
    data = EmployeeOut.model_validate(emp).model_dump()
    assert sensitive.mask(dict(data), allowed=True)["bank_account_no"] == "1903 8888 8888"


def test_masking_blanks_the_value_without_dropping_the_key(db):
    """Xóa trắng chứ KHÔNG bỏ khóa khỏi dict.

    Bỏ khóa thì giao diện phải đoán xem "không có quyền" hay "chưa nhập", và mọi
    chỗ đọc phải thêm một nhánh `if "bank_name" in data`.
    """
    data = EmployeeOut.model_validate(_emp(db)).model_dump()
    out = sensitive.mask(dict(data), allowed=False)
    for f in sensitive.SENSITIVE_FIELDS:
        assert f in out, f"khóa {f} bị bỏ hẳn khỏi dict thay vì xóa trắng"


# ── 2. Ngoại lệ `self` ──────────────────────────────────────────────────────

def test_everyone_can_read_their_own_profile(db):
    emp = _emp(db)
    assert sensitive.can_read_sensitive(_profile(employee_id=emp.id), emp.id)


def test_cannot_read_someone_elses_profile(db):
    me, other = _emp(db, "NS001"), _emp(db, "NS002")
    assert not sensitive.can_read_sensitive(_profile(employee_id=me.id), other.id)


def test_account_without_employee_link_unlocks_nothing(db):
    """`employee_id = 0` (admin, tài khoản hệ thống) KHÔNG được coi là «chính mình».

    Hồ sơ chưa lưu cũng mang id 0 trong bộ nhớ, nên so bằng mà không chặn `0`
    thì ngoại lệ self mở cho tất cả — đúng cái bẫy `leave_request` đã dính.
    """
    assert not sensitive.can_read_sensitive(_profile(employee_id=0), 0)
    assert not sensitive.can_read_sensitive(_profile(employee_id=0), _emp(db).id)


def test_list_unmasks_only_the_callers_own_row(db):
    me = _emp(db, "NS001", bank_account_no="111")
    other = _emp(db, "NS002", bank_account_no="222")
    rows = [EmployeeOut.model_validate(x).model_dump() for x in (me, other)]

    out = sensitive.mask_many(rows, _profile(employee_id=me.id))
    by_id = {r["id"]: r for r in out}
    assert by_id[me.id]["bank_account_no"] == "111", "dòng của chính mình phải giữ nguyên"
    assert by_id[other.id]["bank_account_no"] == "", "dòng người khác phải che"


def test_with_permission_the_whole_list_is_unmasked(db):
    rows = [EmployeeOut.model_validate(_emp(db, "NS001", bank_account_no="111")).model_dump()]
    out = sensitive.mask_many(rows, _profile(sensitive_read=True))
    assert out[0]["bank_account_no"] == "111"


# ── 3. Vòng quản lý ─────────────────────────────────────────────────────────

def test_cannot_be_ones_own_manager(db):
    emp = _emp(db)
    with pytest.raises(HTTPException) as e:
        emp_service.block_manager_cycle(db, emp.id, emp.id)
    assert e.value.status_code == 400


def test_blocks_two_person_cycle(db):
    a, b = _emp(db, "NS001"), _emp(db, "NS002")
    emp_service.update_employee(db, b.id, EmployeeUpdate(manager_id=a.id), 1)
    with pytest.raises(HTTPException):
        emp_service.update_employee(db, a.id, EmployeeUpdate(manager_id=b.id), 1)


def test_blocks_three_person_cycle(db):
    """Vòng dài cũng phải chặn — chỉ so `manager_id == id` là bỏ lọt A→B→C→A."""
    a, b, c = _emp(db, "NS001"), _emp(db, "NS002"), _emp(db, "NS003")
    emp_service.update_employee(db, b.id, EmployeeUpdate(manager_id=a.id), 1)
    emp_service.update_employee(db, c.id, EmployeeUpdate(manager_id=b.id), 1)
    with pytest.raises(HTTPException):
        emp_service.update_employee(db, a.id, EmployeeUpdate(manager_id=c.id), 1)


def test_straight_manager_chain_is_allowed(db):
    a, b, c = _emp(db, "NS001"), _emp(db, "NS002"), _emp(db, "NS003")
    emp_service.update_employee(db, b.id, EmployeeUpdate(manager_id=a.id), 1)
    emp_service.update_employee(db, c.id, EmployeeUpdate(manager_id=b.id), 1)
    assert db.get(Employee, c.id).manager_id == b.id


def test_nonexistent_manager_is_blocked(db):
    emp = _emp(db)
    with pytest.raises(HTTPException):
        emp_service.update_employee(db, emp.id, EmployeeUpdate(manager_id=999999), 1)


def test_deleting_a_manager_clears_the_field_on_reports(db):
    """Xóa hồ sơ đang là quản lý của ai đó → ô `manager_id` bên kia về `0`.

    Để nguyên là một id trỏ vào hư không, và bộ máy duyệt lùi về trưởng bộ phận
    một cách IM LẶNG. `0` thì màn danh sách có cảnh báo, id chết thì không.
    """
    sep, nv = _emp(db, "NS001"), _emp(db, "NS002")
    emp_service.update_employee(db, nv.id, EmployeeUpdate(manager_id=sep.id), 1)
    emp_service.delete_employee(db, sep.id, 1)
    assert db.get(Employee, nv.id).manager_id == 0


# ── 4. Hai bảng con ─────────────────────────────────────────────────────────

def test_skips_rows_with_blank_full_name(db):
    """Giao diện dựng sẵn một dòng trống cho người dùng gõ vào, và vẫn gửi nó lên.

    Lưu dòng đó là mỗi lần mở hồ sơ lại đẻ thêm một người báo tin không tên.
    """
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [
        EmployeeContactIn(full_name="Nguyễn Văn Cha", relation=RELATION_FATHER, phone="0901"),
        EmployeeContactIn(full_name="   "),
        EmployeeContactIn(),
    ], 1)
    db.commit()
    rows = contact_service.list_contacts(db, emp.id)
    assert [r.full_name for r in rows] == ["Nguyễn Văn Cha"]


def test_sort_order_stays_contiguous_despite_blank_rows(db):
    """Bỏ dòng trống ở giữa KHÔNG được để lại lỗ hổng trong `sort_order`.

    Đánh số theo chỉ số đầu vào thì ra (0, 2) — người đọc dữ liệu tưởng dòng số
    1 đã bị ai xóa mất.
    """
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [
        EmployeeContactIn(full_name="Cha"),
        EmployeeContactIn(full_name=""),
        EmployeeContactIn(full_name="Mẹ"),
    ], 1)
    db.commit()
    assert [r.sort_order for r in contact_service.list_contacts(db, emp.id)] == [0, 1]


def test_keeps_the_order_the_client_sent(db):
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [
        EmployeeContactIn(full_name="Mẹ"), EmployeeContactIn(full_name="Cha"),
    ], 1)
    db.commit()
    assert [r.full_name for r in contact_service.list_contacts(db, emp.id)] == ["Mẹ", "Cha"]


def test_replaces_the_whole_child_table_instead_of_appending(db):
    """`PUT` là ĐẶT LẠI toàn bộ — gửi lần hai không cộng dồn vào lần một."""
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [EmployeeContactIn(full_name="Cha")], 1)
    db.commit()
    contact_service.set_contacts(db, emp.id, [EmployeeContactIn(full_name="Mẹ")], 1)
    db.commit()
    assert [r.full_name for r in contact_service.list_contacts(db, emp.id)] == ["Mẹ"]


def test_deleting_a_profile_deletes_both_child_tables(db):
    """Dữ liệu cá nhân của NGƯỜI THỨ BA không có lý do gì tồn tại sau khi xóa hồ sơ.

    FK đã khai CASCADE, nhưng bộ test chạy SQLite — nơi ràng buộc khóa ngoại
    mặc định TẮT. Nên `delete_all_of` xóa tường minh, và bài này canh đúng nó.
    """
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [EmployeeContactIn(full_name="Cha")], 1)
    contact_service.set_families(db, emp.id, [EmployeeFamilyIn(full_name="Con", gender=1)], 1)
    db.commit()

    emp_service.delete_employee(db, emp.id, 1)
    assert contact_service.list_contacts(db, emp.id) == []
    assert contact_service.list_families(db, emp.id) == []


# ── 5. Phân quyền: khóa mới không được rơi vào vai trò nghiệp vụ ────────────

def test_every_entity_is_declared(db):
    assert "employee_sensitive" in ENTITIES
    #  PUBLIC ở đây KHÔNG nghĩa là công khai — nghĩa là entity này không có bảng
    #  riêng để `apply_scope` lọc. Hồ sơ NÀO thì khóa `employee` đã lọc.
    assert SCOPE_FIELDS["employee_sensitive"] is PUBLIC


def test_purchase_manager_cannot_read_sensitive_fields():
    """⚠️ `_PUR_MANAGER_PERMS` quét cả `ENTITIES`.

    Quên đưa khóa mới vào `_SYS_ENTITIES` là Quản lý thu mua tự nhiên đọc được
    số CCCD và tài khoản ngân hàng của toàn công ty — thứ chẳng liên quan gì tới
    nghiệp vụ mua hàng, và không một dòng mã nào nói ra chuyện đó.
    """
    from app.seed import STD_ROLES
    assert "employee_sensitive" not in STD_ROLES["pur_manager"]["perms"]
    assert "employee_sensitive" not in STD_ROLES["pur_admin"]["perms"]
    assert "employee_sensitive" not in STD_ROLES["employee"]["perms"]


def test_hr_profile_role_holds_that_permission():
    from app.seed import STD_ROLES
    actions, scope = STD_ROLES["hr_profile"]["perms"]["employee_sensitive"]
    assert "read" in actions and scope == "all"


# ── 6. Ô tùy biến ───────────────────────────────────────────────────────────

def test_extra_fields_key_count_cap():
    from app.modules.employee.constants import MAX_EXTRA_FIELDS

    too_many = {f"k{i}": i for i in range(MAX_EXTRA_FIELDS + 1)}
    with pytest.raises(ValueError):
        EmployeeUpdate(extra_fields=too_many)
    EmployeeUpdate(extra_fields={f"k{i}": i for i in range(MAX_EXTRA_FIELDS)})


def test_null_json_column_reads_as_empty_dict(db):
    """Hàng trăm dòng có trước cột này mang `NULL` — đọc phải ra `{}`, không phải `None`."""
    emp = _emp(db)
    assert emp.extra_fields is None
    assert emp.extra_fields_map == {}


# ── 7. Bộ mã số ─────────────────────────────────────────────────────────────

def test_unknown_code_is_blocked():
    with pytest.raises(ValueError):
        EmployeeUpdate(job_level=99)
    with pytest.raises(ValueError):
        EmployeeUpdate(marital_status=7)


def test_vietnamese_labels_are_sent_along(db):
    from app.modules.employee.constants import (JOB_LEVEL_MANAGER,
                                                MARITAL_MARRIED)

    emp = _emp(db, job_level=JOB_LEVEL_MANAGER, marital_status=MARITAL_MARRIED)
    out = EmployeeOut.model_validate(emp).model_dump()
    assert out["job_level_label"] == "Trưởng phòng"
    assert out["marital_status_label"] == "Có gia đình"


def test_code_outside_the_set_yields_a_blank_label(db):
    """Ghi thẳng vào cột (dữ liệu cũ, nhập tay) → nhãn rỗng, KHÔNG trả lại con số.

    Trả rỗng thì nhìn dữ liệu là biết ngay dòng nào mang giá trị ngoài bộ mã —
    cùng lý lẽ với `Employee.status_label` của B-03.
    """
    emp = _emp(db)
    emp.job_level = 99
    db.commit()
    assert emp.job_level_label == ""
