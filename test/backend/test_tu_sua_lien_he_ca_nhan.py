"""
test_tu_sua_lien_he_ca_nhan.py — bao-CR-508: TỰ SỬA LIÊN HỆ ở Trang cá nhân.

Khách chốt 28/09/2026: ai đã gắn hồ sơ nhân sự cũng tự sửa được nhóm LIÊN HỆ
của CHÍNH MÌNH (số điện thoại · địa chỉ thường trú · địa chỉ hiện nay · người
báo tin) mà không cần `employee.write`. Mọi nhóm khác vẫn chỉ phòng Nhân sự sửa.

Bộ này cố làm cửa mới SAI, xếp theo mức thiệt hại nếu vỡ:

  1. Nhét thêm ô ngoài nhóm liên hệ (phòng ban, pháp nhân, tài khoản ngân hàng,
     trạng thái…) — phải 422 và KHÔNG ô nào bị ghi.
  2. Trỏ sang hồ sơ người khác — cửa không nhận id nào, nên mọi cách gửi id
     đều không đụng được hồ sơ khác.
  3. Tài khoản chưa gắn hồ sơ → câu báo rõ, không thành công rỗng.
  4. Chuỗi quá dài → 422 ở tầng schema (SQLite không ép VARCHAR, xem CLAUDE.md).
  5. Có dòng nhật ký; không đổi gì thì không ghi dòng rác.
  6. Người KHÔNG có quyền nhân sự nào vẫn dùng được (lý do tồn tại của cửa).
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.employee import controller
from app.modules.employee.contact_model import EmployeeContact
from app.modules.employee.field_limits import MAX_PEOPLE_ROWS
from app.modules.employee.model import Employee
from app.modules.employee.schema import SelfContactsIn, SelfContactUpdate
from app.modules.user.model import User


# ── Dựng dữ liệu ────────────────────────────────────────────────────────────

def _emp(db, code: str, **kw) -> Employee:
    obj = Employee(code=code, full_name=kw.pop("full_name", f"Người {code}"),
                   is_active=True, **kw)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _user(db, employee_id: int, email: str = "tu.sua@dego.vn") -> User:
    """Tài khoản KHÔNG có vai trò nào — tức không có khóa `employee.*` nào."""
    u = User(email=email, employee_id=employee_id, is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def world(db):
    """Hai hồ sơ: của tôi và của đồng nghiệp — đủ để thử trỏ sang người khác."""
    mine = _emp(db, "NS508A", phone="0900000001", permanent_address="Cũ thường trú",
                current_address="Cũ tạm trú", department_id=7, company_id=3,
                bank_account_no="111222333", status="official")
    other = _emp(db, "NS508B", phone="0900000002", permanent_address="Nhà người khác")
    me = _user(db, mine.id)
    return mine, other, me


@pytest.fixture
def client_as(db):
    """TestClient đăng nhập bằng một tài khoản cho trước (ghi đè `get_current_user`)."""
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _audits(db, employee_id: int) -> list[AuditLog]:
    return (db.query(AuditLog)
            .filter(AuditLog.entity == "employee", AuditLog.entity_id == employee_id)
            .order_by(AuditLog.id).all())


# ── 6. Chốt cửa: chỉ đòi đăng nhập, khai trước /{eid} ───────────────────────

def _route(path: str, method: str):
    for r in controller.router.routes:
        if getattr(r, "path", None) == path and method in getattr(r, "methods", set()):
            return r
    raise AssertionError(f"Không tìm thấy route {method} {path}")


def _guards(route) -> str:
    return " ".join(getattr(d.call, "__qualname__", "") or repr(d.call)
                    for d in route.dependant.dependencies)


@pytest.mark.parametrize("path,method", [
    ("/api/employees/me/contact", "PATCH"),
    ("/api/employees/me/contacts", "GET"),
    ("/api/employees/me/contacts", "PUT"),
])
def test_self_routes_only_require_login(path, method):
    """Gác bằng `require("employee", ...)` là mất đúng nhóm người cửa này sinh ra cho."""
    guards = _guards(_route(path, method))
    assert "get_current_user" in guards
    assert "require" not in guards


def test_self_contacts_routes_are_declared_before_the_id_routes():
    """`/me/contacts` đứng sau `/{eid}/contacts` là «me» rơi vào `eid: int` → 422."""
    paths = [getattr(r, "path", "") for r in controller.router.routes]
    assert paths.index("/api/employees/me/contacts") < paths.index("/api/employees/{eid}/contacts")
    assert paths.index("/api/employees/me/contact") < paths.index("/api/employees/{eid}")


def test_user_without_any_employee_permission_cannot_use_the_hr_door(db, world, client_as):
    """Mốc đối chứng: người này KHÔNG có `employee.write` — cửa của phòng Nhân sự
    phải chặn họ, còn cửa tự phục vụ thì không (các bài dưới)."""
    mine, _, me = world
    res = client_as(me).patch(f"/api/employees/{mine.id}", json={"phone": "0911"})
    assert res.status_code == 403


# ── Ghi được ba ô liên hệ + người báo tin ──────────────────────────────────

def test_user_updates_own_phone_and_both_addresses(db, world, client_as):
    mine, _, me = world
    res = client_as(me).patch("/api/employees/me/contact", json={
        "phone": "  0987654321 ",
        "permanent_address": "12 Lê Lợi, Huế",
        "current_address": "34 Nguyễn Huệ, TP.HCM",
    })

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    #  Hồ sơ của chính mình: đọc đủ địa chỉ trong câu trả lời (ngoại lệ `self`).
    assert body["data"]["permanent_address"] == "12 Lê Lợi, Huế"
    db.refresh(mine)
    assert mine.phone == "0987654321", "phải cắt khoảng trắng hai đầu"
    assert mine.permanent_address == "12 Lê Lợi, Huế"
    assert mine.current_address == "34 Nguyễn Huệ, TP.HCM"
    assert mine.updated_by == me.id


def test_partial_patch_leaves_unsent_fields_alone(db, world, client_as):
    """Gửi mỗi số điện thoại thì hai địa chỉ phải GIỮ NGUYÊN, không bị xóa trắng."""
    mine, _, me = world
    res = client_as(me).patch("/api/employees/me/contact", json={"phone": "0912345678"})
    assert res.status_code == 200, res.text
    db.refresh(mine)
    assert mine.phone == "0912345678"
    assert mine.permanent_address == "Cũ thường trú"
    assert mine.current_address == "Cũ tạm trú"


def test_explicit_null_clears_the_field_instead_of_writing_null(db, world, client_as):
    mine, _, me = world
    res = client_as(me).patch("/api/employees/me/contact", json={"current_address": None})
    assert res.status_code == 200, res.text
    db.refresh(mine)
    assert mine.current_address == ""


def test_user_replaces_own_emergency_contacts(db, world, client_as):
    mine, _, me = world
    c = client_as(me)
    res = c.put("/api/employees/me/contacts", json={"items": [
        {"full_name": "Nguyễn Văn Cha", "relation": 0, "phone": "0901", "address": "Huế"},
        #  Dòng rỗng họ tên bị bỏ — cùng luật với cửa của phòng Nhân sự.
        {"full_name": "   ", "relation": 0, "phone": "0902", "address": ""},
    ]})
    assert res.status_code == 200, res.text
    assert [r["full_name"] for r in res.json()["data"]] == ["Nguyễn Văn Cha"]

    listed = c.get("/api/employees/me/contacts")
    assert listed.status_code == 200, listed.text
    assert [r["full_name"] for r in listed.json()["data"]] == ["Nguyễn Văn Cha"]


# ── 1. Ô ngoài nhóm liên hệ bị chặn và KHÔNG bị ghi ────────────────────────

@pytest.mark.parametrize("extra", [
    {"department_id": 99},
    {"company_id": 99},
    {"bank_account_no": "999999999"},
    {"status": "resigned"},
    {"position_id": 5},
    {"full_name": "Đổi Tên"},
    {"id_number": "079000000000"},
    {"manager_id": 1},
    #  Cố trỏ sang hồ sơ khác bằng thân yêu cầu.
    {"id": 2},
    {"employee_id": 2},
])
def test_fields_outside_the_contact_group_are_rejected_and_never_written(
        db, world, client_as, extra):
    mine, _, me = world
    before = (mine.department_id, mine.company_id, mine.bank_account_no, mine.status,
              mine.full_name, mine.phone)
    res = client_as(me).patch("/api/employees/me/contact",
                              json={"phone": "0999999999", **extra})

    assert res.status_code == 422, res.text
    db.refresh(mine)
    assert (mine.department_id, mine.company_id, mine.bank_account_no, mine.status,
            mine.full_name, mine.phone) == before, "422 mà vẫn ghi nửa chừng là lủng"
    assert _audits(db, mine.id) == []


def test_contacts_payload_rejects_unknown_root_keys(db, world, client_as):
    """Gốc thân `PUT /me/contacts` cũng cấm khóa lạ, kể cả `employee_id`."""
    mine, other, me = world
    res = client_as(me).put("/api/employees/me/contacts",
                            json={"employee_id": other.id, "items": []})
    assert res.status_code == 422, res.text


# ── 2. Không trỏ được sang hồ sơ người khác ────────────────────────────────

def test_query_string_id_cannot_redirect_the_write(db, world, client_as):
    """Cửa không khai tham số id nào: `?employee_id=` / `?eid=` bị lờ, hồ sơ
    được ghi luôn là hồ sơ của phiên đăng nhập."""
    mine, other, me = world
    c = client_as(me)
    res = c.patch(f"/api/employees/me/contact?employee_id={other.id}&eid={other.id}",
                  json={"phone": "0933333333"})
    assert res.status_code == 200, res.text
    assert res.json()["data"]["id"] == mine.id
    db.refresh(other)
    assert other.phone == "0900000002"

    c.put(f"/api/employees/me/contacts?employee_id={other.id}",
          json={"items": [{"full_name": "Người lạ", "relation": 0}]})
    assert db.query(EmployeeContact).filter(EmployeeContact.employee_id == other.id).count() == 0


def test_contact_rows_carrying_foreign_ids_still_land_on_own_profile(db, world, client_as):
    """Từng dòng mang `employee_id` người khác: lớp dòng lờ khóa lạ, và
    `contact_service` chỉ chép bốn cột — dòng vẫn thuộc hồ sơ của mình."""
    mine, other, me = world
    res = client_as(me).put("/api/employees/me/contacts", json={"items": [
        {"full_name": "Mẹ", "relation": 0, "employee_id": other.id, "id": 12345},
    ]})
    assert res.status_code == 200, res.text
    rows = db.query(EmployeeContact).all()
    assert [(r.employee_id, r.full_name) for r in rows] == [(mine.id, "Mẹ")]


# ── 3. Tài khoản chưa gắn hồ sơ / hồ sơ mồ côi ─────────────────────────────

def test_account_without_employee_gets_a_clear_error(db, client_as):
    admin = _user(db, 0, email="admin@dego.vn")
    c = client_as(admin)

    res = c.patch("/api/employees/me/contact", json={"phone": "0911"})
    assert res.status_code == 400
    assert "chưa gắn hồ sơ nhân sự" in res.text

    assert c.put("/api/employees/me/contacts", json={"items": []}).status_code == 400
    assert c.get("/api/employees/me/contacts").status_code == 400
    #  Không được "trúng" hồ sơ nào: id 0 không khớp ai.
    assert db.query(EmployeeContact).count() == 0


def test_dangling_employee_link_is_404_not_a_write(db, client_as):
    ghost = _user(db, 999_999, email="ma@dego.vn")
    res = client_as(ghost).patch("/api/employees/me/contact", json={"phone": "0911"})
    assert res.status_code == 404


# ── 4. Chuỗi quá dài → 422 ở tầng schema ───────────────────────────────────

@pytest.mark.parametrize("field,limit", [
    ("phone", 25),
    ("permanent_address", 500),
    ("current_address", 500),
])
def test_too_long_values_are_rejected_at_schema_level(field, limit):
    SelfContactUpdate(**{field: "x" * limit})          # vừa đúng trần: nhận
    with pytest.raises(ValidationError):
        SelfContactUpdate(**{field: "x" * (limit + 1)})


def test_too_long_value_is_422_over_http(db, world, client_as):
    mine, _, me = world
    res = client_as(me).patch("/api/employees/me/contact", json={"phone": "0" * 26})
    assert res.status_code == 422
    db.refresh(mine)
    assert mine.phone == "0900000001"


def test_contacts_row_cap_and_row_limits_are_inherited():
    """Trần dòng và độ dài từng ô lấy từ schema của phòng Nhân sự, không chép lại."""
    with pytest.raises(ValidationError):
        SelfContactsIn(items=[{"full_name": "A"}] * (MAX_PEOPLE_ROWS + 1))
    with pytest.raises(ValidationError):
        SelfContactsIn(items=[{"full_name": "A", "phone": "0" * 26}])
    with pytest.raises(ValidationError):
        SelfContactsIn(items=[{"full_name": "A", "relation": 999}])


def test_too_many_contact_rows_do_not_wipe_existing_ones(db, world, client_as):
    """Trần chặn TRƯỚC khi xóa bảng cũ — một lần gửi hỏng không được mất dữ liệu."""
    mine, _, me = world
    c = client_as(me)
    c.put("/api/employees/me/contacts", json={"items": [{"full_name": "Giữ lại", "relation": 0}]})
    res = c.put("/api/employees/me/contacts",
                json={"items": [{"full_name": "X", "relation": 0}] * (MAX_PEOPLE_ROWS + 1)})
    assert res.status_code == 422
    assert [r.full_name for r in db.query(EmployeeContact).all()] == ["Giữ lại"]


# ── 5. Nhật ký ─────────────────────────────────────────────────────────────

def test_audit_row_is_written_with_the_changed_fields(db, world, client_as):
    mine, _, me = world
    client_as(me).patch("/api/employees/me/contact",
                        json={"phone": "0977777777", "current_address": "Cũ tạm trú"})

    rows = _audits(db, mine.id)
    assert len(rows) == 1
    assert rows[0].action == "update"
    assert rows[0].created_by == me.id
    assert "số điện thoại" in rows[0].message
    #  Ô gửi lên y nguyên giá trị cũ không được kể là đã sửa.
    assert "tạm trú" not in rows[0].message


def test_saving_without_changes_writes_no_audit_row(db, world, client_as):
    mine, _, me = world
    res = client_as(me).patch("/api/employees/me/contact", json={"phone": "0900000001"})
    assert res.status_code == 200
    assert _audits(db, mine.id) == []


def test_contacts_save_writes_an_audit_row(db, world, client_as):
    mine, _, me = world
    client_as(me).put("/api/employees/me/contacts",
                      json={"items": [{"full_name": "Vợ", "relation": 0}]})
    rows = _audits(db, mine.id)
    assert len(rows) == 1
    assert "người báo tin" in rows[0].message
    assert rows[0].created_by == me.id
