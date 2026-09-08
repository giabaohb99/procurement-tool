"""
test_ho_so_nhan_su_cuc_doan.py — STRESS TEST hồ sơ nhân sự (duoc-CR-316).

Bộ `test_ho_so_nhan_su_dot1.py` kiểm LUẬT NGHIỆP VỤ chạy đúng. Bộ này thì cố
tình PHÁ: chuỗi dài hơn cột, số âm, số tràn kiểu, ngày ngoài dải, danh sách
khổng lồ, chuỗi quản lý sâu hơn trần dò.

Vì sao cần: ngày 08/09/2026 bắn thử vào MySQL thật thì **6 nhóm ca trả 500**
«Hệ thống gặp lỗi không lường trước» — chỉ vì Pydantic không khai `max_length`
nên chuỗi dài đi thẳng xuống cột `VARCHAR` và MySQL từ chối. Người dùng dán
nhầm một đoạn văn bản vào ô là ăn mã sự cố, còn quản trị đi tra một lỗi vốn
đáng ra phải là câu «tối đa 20 ký tự».

⚠️ **SQLite KHÔNG ép độ dài VARCHAR.** Nên ca tràn độ dài phải kiểm ở tầng
SCHEMA (Pydantic 422) chứ không kiểm bằng cách ghi xuống DB — ghi xuống thì
SQLite nhận hết và bài kiểm xanh giả.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.employee import contact_service
from app.modules.employee import service as emp_service
from app.modules.employee.constants import (MAX_EXTRA_FIELDS, RELATION_FATHER,
                                             RELATION_SON)
from app.modules.employee.model import Employee
from app.modules.employee.schema import (EmployeeContactIn, EmployeeCreate,
                                         EmployeeUpdate)


def _emp(db, code="NS001", **kw):
    obj = Employee(code=code, full_name=kw.pop("full_name", "Người Thử"), is_active=True, **kw)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── 1. Chuỗi DÀI HƠN CỘT phải bị chặn ở schema, không để MySQL nổ ───────────
#  (cột, độ dài cột). Gửi dài hơn là phải 422 kèm câu tiếng Việt, KHÔNG phải
#  500 «lỗi không lường trước».
_TEXT_LIMITS = [
    # Trường CŨ — lỗ hổng có sẵn từ trước duoc-CR-314, vá luôn vì cùng một dòng.
    ("full_name", 255),
    ("email", 255),
    ("phone", 25),
    ("position", 100),
    # Trường của hồ sơ mở rộng
    ("place_of_birth", 255),
    ("ethnicity", 50),
    ("religion", 50),
    ("personal_email", 255),
    ("tax_code", 20),
    ("major", 255),
    ("work_location", 255),
    ("permanent_address", 500),
    ("current_address", 500),
    ("bank_account_no", 50),
    ("bank_account_name", 255),
    ("bank_name", 100),
    ("bank_branch", 255),
    ("id_number", 20),
    ("id_issue_place", 255),
    ("social_insurance_no", 20),
    ("health_care_place", 255),
    ("health_care_code", 20),
]


@pytest.mark.parametrize("field,limit", _TEXT_LIMITS)
def test_string_longer_than_column_is_blocked_at_schema(field, limit):
    """Dài hơn cột một ký tự là 422, không phải 500."""
    with pytest.raises(ValidationError):
        EmployeeUpdate(**{field: "x" * (limit + 1)})


@pytest.mark.parametrize("field,limit", _TEXT_LIMITS)
def test_string_exactly_at_column_width_passes(field, limit):
    """Chặn ĐÚNG mức cột, không chặn hụt — người dùng có quyền dùng hết ô."""
    EmployeeUpdate(**{field: "x" * limit})


def test_blocked_on_create_path_too_not_only_update():
    """Chặn một bên thì bên còn lại vẫn nổ — đúng bài học B-03."""
    with pytest.raises(ValidationError):
        EmployeeCreate(full_name="A", tax_code="9" * 100)


def test_child_table_fields_are_blocked_as_well(db, seed):
    """Bảng con đi cửa riêng nên có schema riêng — dễ quên đúng chỗ này."""
    with pytest.raises(ValidationError):
        EmployeeContactIn(full_name="T" * 5000)
    with pytest.raises(ValidationError):
        EmployeeContactIn(full_name="A", address="Đ" * 5000)


# ── 2. Ô JSON tùy biến ──────────────────────────────────────────────────────

def test_key_count_cap_still_applies():
    with pytest.raises(ValidationError):
        EmployeeUpdate(extra_fields={f"k{i}": i for i in range(MAX_EXTRA_FIELDS + 1)})


def test_huge_value_is_blocked():
    """20 khóa × 2MB = 40MB một hồ sơ — trần SỐ KHÓA không cứu được gì.

    MySQL nhận (cột JSON chứa tới 1GB), nên không có gì nổ; chỉ là mọi màn hình
    đọc hồ sơ đó về sau đều đứng hình, và không ai truy ra vì sao.
    """
    with pytest.raises(ValidationError):
        EmployeeUpdate(extra_fields={"k": "z" * 2_000_000})


def test_overlong_key_is_blocked():
    with pytest.raises(ValidationError):
        EmployeeUpdate(extra_fields={"k" * 10_000: 1})


def test_deeply_nested_value_is_blocked():
    """JSON lồng sâu 100 tầng làm MySQL từ chối → 500.

    Ô này sinh ra cho nhu cầu LẺ (size áo, số hộ chiếu), tức giá trị vô hướng.
    Nhận cả cây lồng nhau là biến nó thành một cơ sở dữ liệu thứ hai không ai rà.
    """
    nested = {"n": 1}
    for _ in range(100):
        nested = {"n": nested}
    with pytest.raises(ValidationError):
        EmployeeUpdate(extra_fields={"a": nested})


def test_scalar_value_still_passes():
    """Chặn cây lồng nhau nhưng KHÔNG chặn thứ ô này sinh ra để chứa."""
    EmployeeUpdate(extra_fields={"size_ao": "L", "so_ho_chieu": "C1234567", "da_tiem": True,
                                 "so_nam_kinh_nghiem": 7, "ghi_chu": None})


# ── 3. Ngày ngoài dải hợp lý ────────────────────────────────────────────────

def test_birth_date_in_year_0001_is_blocked():
    """MySQL nhận, nhưng thâm niên sẽ tính ra HAI NGHÌN NĂM.

    `balance_service` cộng ngày phép theo bậc thâm niên, nên một ô gõ nhầm ở đây
    thành một người có vài nghìn ngày phép — và không dòng mã nào nói rằng con
    số đó vô lý.
    """
    with pytest.raises(ValidationError):
        EmployeeUpdate(date_of_birth="0001-01-01")


def test_birth_date_in_the_future_is_blocked():
    with pytest.raises(ValidationError):
        EmployeeUpdate(date_of_birth="9999-12-31")


def test_hire_date_too_far_out_is_blocked():
    with pytest.raises(ValidationError):
        EmployeeUpdate(hire_date="1800-01-01")


def test_reasonable_date_still_passes():
    EmployeeUpdate(date_of_birth="1990-05-01", hire_date="2015-03-02",
                   id_issue_date="2021-06-10", id_expiry_date="2041-06-10")


def test_resign_before_hire_date_is_blocked():
    """Nghỉ việc trước khi vào làm — không có cách nào đúng."""
    with pytest.raises(ValidationError):
        EmployeeUpdate(hire_date="2026-01-01", resign_date="2000-01-01")


def test_resign_on_the_hire_date_passes():
    """Vào làm rồi nghỉ ngay trong ngày là chuyện CÓ THẬT (thử việc một buổi)."""
    EmployeeUpdate(hire_date="2026-01-01", resign_date="2026-01-01")


def test_sending_resign_date_alone_is_not_blocked(db):
    """PATCH chỉ một ô: không có `hire_date` trong payload thì không so được.

    Chặn ở đây là chặn nhầm mọi lần sửa riêng ngày nghỉ việc.
    """
    EmployeeUpdate(resign_date="2000-01-01")


# ── 4. Bảng con: trần số dòng ───────────────────────────────────────────────

def test_child_table_row_count_cap(db, seed):
    """Không trần thì `PUT` 5000 dòng lọt thẳng — đã thử được trên MySQL thật.

    Đây là bảng «cha, mẹ, vợ/chồng» trong một tab; vài chục dòng đã là vô lý.
    Kèm theo: `sort_order` là SMALLINT, dòng thứ 32768 tràn kiểu.
    """
    from app.modules.employee.schema import MAX_PEOPLE_ROWS, EmployeeContactsIn

    too_many = [{"full_name": f"Người {i}"} for i in range(MAX_PEOPLE_ROWS + 1)]
    with pytest.raises(ValidationError):
        EmployeeContactsIn(items=too_many)

    EmployeeContactsIn(items=[{"full_name": f"Người {i}"} for i in range(MAX_PEOPLE_ROWS)])


# ── 5. Chuỗi quản lý sâu hơn trần dò ────────────────────────────────────────

def test_manager_chain_deeper_than_the_cap_is_blocked(db):
    """⚠️ Ca khó nhất, và là ca `block_manager_cycle` từng BỎ LỌT.

    Vòng dò đi ngược lên tối đa `_MAX_MANAGER_DEPTH` cấp rồi dừng. Bản đầu dừng
    xong là **trả về im lặng** = cho qua — nên một chuỗi dài hơn trần mà vòng lại
    ở cấp cuối thì lọt, và cái lọt đó là một VÒNG LẶP VÔ HẠN trong bộ máy duyệt.

    Chuỗi sâu như vậy không có ở sơ đồ tổ chức thật (DEGO sâu 6 cấp), nhưng đây
    đúng là thứ chỉ xuất hiện khi ai đó cố tình dựng nó.
    """
    depth = emp_service._MAX_MANAGER_DEPTH + 5
    chain = [_emp(db, f"NS{i:03d}") for i in range(depth)]
    #  Nối thành chuỗi thẳng: chain[i] có quản lý là chain[i+1].
    for i in range(depth - 1):
        chain[i].manager_id = chain[i + 1].id
    db.commit()

    #  Giờ khép vòng: người CUỐI chuỗi nhận người ĐẦU làm quản lý.
    with pytest.raises(HTTPException):
        emp_service.block_manager_cycle(db, chain[-1].id, chain[0].id)


def test_long_manager_chain_within_the_cap_is_allowed(db):
    """Đừng chặn nhầm: chuỗi dài mà KHÔNG vòng và chưa chạm trần thì hợp lệ.

    Sơ đồ tổ chức thật của DEGO sâu 6 cấp, nên 40 cấp đã là rất rộng rãi.
    """
    depth = emp_service._MAX_MANAGER_DEPTH - 10
    chain = [_emp(db, f"NS{i:03d}") for i in range(depth)]
    for i in range(depth - 1):
        chain[i].manager_id = chain[i + 1].id
    db.commit()

    newcomer = _emp(db, "NSMOI")
    emp_service.block_manager_cycle(db, newcomer.id, chain[0].id)


def test_acyclic_chain_past_the_cap_is_still_blocked(db):
    """⚠️ Đánh đổi CÓ CHỦ Ý, ghi lại đây để lần sau khỏi tưởng là lỗi.

    Chuỗi dài hơn trần mà không vòng thì vẫn bị chặn — vì đứng ở cấp thứ 50
    không có cách nào biết phía trên còn gì. Hai lựa chọn:

      · cho qua  → chuỗi khép vòng ở cấp 51 lọt, và cái lọt đó là vòng lặp vô
                   hạn trong bộ máy duyệt, nổ lúc ai đó nộp đơn nghỉ phép;
      · chặn     → chặn nhầm một sơ đồ tổ chức sâu hơn 50 cấp.

    Chọn vế sau: sơ đồ 50 cấp không tồn tại ở doanh nghiệp thật, nên chuỗi dài
    vậy đã là dấu hiệu dữ liệu hỏng — đáng để người dùng đọc câu cảnh báo và đi
    kiểm, hơn là để hệ thống treo về sau. Câu lỗi nói rõ phải đi kiểm ô nào.
    """
    depth = emp_service._MAX_MANAGER_DEPTH + 5
    chain = [_emp(db, f"NS{i:03d}") for i in range(depth)]
    for i in range(depth - 1):
        chain[i].manager_id = chain[i + 1].id
    db.commit()

    newcomer = _emp(db, "NSMOI")
    with pytest.raises(HTTPException) as e:
        emp_service.block_manager_cycle(db, newcomer.id, chain[0].id)
    assert "cấp" in e.value.detail, "câu lỗi phải nói ra là do chuỗi quá sâu"


# ── 6. Ca rỗng / một phần tử / trùng nhau ───────────────────────────────────

def test_resetting_child_table_with_an_empty_list(db, seed):
    """Xóa hết người báo tin là một thao tác hợp lệ, không phải lỗi."""
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [EmployeeContactIn(full_name="Cha")], 1)
    db.commit()
    contact_service.set_contacts(db, emp.id, [], 1)
    db.commit()
    assert contact_service.list_contacts(db, emp.id) == []


def test_two_fully_identical_rows_still_save(db, seed):
    """Hai người thân trùng tên là chuyện có thật (cha và con cùng tên).

    Không khử trùng — khử là xóa dữ liệu người dùng cố ý nhập.
    """
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [
        EmployeeContactIn(full_name="Nguyễn Văn A", relation=RELATION_FATHER),
        EmployeeContactIn(full_name="Nguyễn Văn A", relation=RELATION_SON),
    ], 1)
    db.commit()
    assert len(contact_service.list_contacts(db, emp.id)) == 2


def test_all_blank_rows_yield_an_empty_table_not_an_error(db, seed):
    emp = _emp(db)
    contact_service.set_contacts(db, emp.id, [
        EmployeeContactIn(), EmployeeContactIn(full_name="  "), EmployeeContactIn(full_name="\t"),
    ], 1)
    db.commit()
    assert contact_service.list_contacts(db, emp.id) == []


def test_missing_profile_yields_empty_child_tables_not_an_error(db, seed):
    """Id lạ → danh sách rỗng, không nổ. Chốt phạm vi nằm ở controller."""
    assert contact_service.list_contacts(db, 999999) == []
    assert contact_service.list_families(db, 999999) == []
