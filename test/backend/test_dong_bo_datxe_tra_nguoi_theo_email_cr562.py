"""bao-CR-562 — bộ tra người tạo của đồng bộ app đặt xe cũ khớp thêm theo EMAIL.

Trước bản này `PeopleResolver` chỉ nhận UID đã được gắn sẵn lên hồ sơ (script
`sync_users`), nên người mới lập tài khoản bên app cũ thì phiếu về ERP trống người
tạo dù email của họ có sẵn trên ERP. Chạy trên SQLite in-memory, Firebase giả lập
qua `fetch_node`.
"""
from app.modules.employee.model import Employee
from app.modules.legacy_datxe.builder import PeopleResolver
from app.modules.legacy_datxe.mapping import USER_SKIPPED
from app.modules.user.model import User

NEW_UID = "uid_moi_lap_ben_app_cu"


class FakeFirebase:
    """Nhánh `users/<uid>` giả lập, đếm số lần bị hỏi."""

    def __init__(self, users: dict | None = None):
        self.users = users or {}
        self.calls: list[str] = []

    def __call__(self, path: str):
        self.calls.append(path)
        uid = path.split("/", 1)[1]
        return self.users.get(uid)


def add_employee(db, code: str, email: str = "", legacy_id: str = "") -> Employee:
    emp = Employee(code=code, full_name=f"Nhân sự {code}", email=email, legacy_id=legacy_id)
    db.add(emp)
    db.flush()
    return emp


def add_user(db, emp: Employee, email: str, active: bool = True) -> User:
    user = User(email=email, employee_id=emp.id, password_hash="x", is_active=active)
    db.add(user)
    db.flush()
    return user


def test_unknown_uid_matches_single_employee_by_email_and_stamps_it(db):
    emp = add_employee(db, "NSU900", email="moi.nguoi@degoholding.vn")
    user = add_user(db, emp, "moi.nguoi@degoholding.vn")
    fb = FakeFirebase({NEW_UID: {"email": "moi.nguoi@degoholding.vn"}})

    people = PeopleResolver(db, fetch_node=fb)

    assert people.employee(NEW_UID) is emp
    assert people.user_id(NEW_UID) == user.id
    assert emp.legacy_id == NEW_UID
    #  Lần thứ hai đi nấc `legacy_id` trong bộ nhớ, không hỏi Firebase nữa.
    assert fb.calls == [f"users/{NEW_UID}"]


def test_email_match_ignores_case_and_surrounding_spaces(db):
    emp = add_employee(db, "NSU901", email="Ho.Ten@Degoholding.VN")
    fb = FakeFirebase({NEW_UID: {"email": "  ho.ten@degoholding.vn "}})

    assert PeopleResolver(db, fetch_node=fb).employee(NEW_UID) is emp


def test_account_email_counts_when_employee_email_is_blank(db):
    emp = add_employee(db, "NSU902", email="")
    add_user(db, emp, "chi.co.tai.khoan@gmail.com")
    fb = FakeFirebase({NEW_UID: {"email": "chi.co.tai.khoan@gmail.com"}})

    assert PeopleResolver(db, fetch_node=fb).employee(NEW_UID) is emp
    assert emp.legacy_id == NEW_UID


def test_email_shared_by_two_employees_is_never_guessed(db):
    #  Ca 38/201 có thật trên prod: một email, hai hồ sơ. Đoán là gắn phiếu nhầm người.
    first = add_employee(db, "NSU903", email="trung@gmail.com")
    second = add_employee(db, "NSU904", email="trung@gmail.com")
    fb = FakeFirebase({NEW_UID: {"email": "trung@gmail.com"}})
    people = PeopleResolver(db, fetch_node=fb)

    assert people.employee(NEW_UID) is None
    assert first.legacy_id == "" and second.legacy_id == ""
    assert people.unknown_uid[NEW_UID] == 1


def test_profile_email_and_another_profiles_account_email_is_ambiguous(db):
    #  Email nằm ở hồ sơ A nhưng lại là email tài khoản của hồ sơ B: hai người, không đoán.
    first = add_employee(db, "NSU905", email="lan@gmail.com")
    second = add_employee(db, "NSU906", email="")
    add_user(db, second, "lan@gmail.com")
    fb = FakeFirebase({NEW_UID: {"email": "lan@gmail.com"}})

    assert PeopleResolver(db, fetch_node=fb).employee(NEW_UID) is None
    assert first.legacy_id == "" and second.legacy_id == ""


def test_profile_already_wearing_another_uid_is_used_but_not_overwritten(db):
    emp = add_employee(db, "NSU907", email="hai.tai.khoan@gmail.com", legacy_id="uid_cu")
    fb = FakeFirebase({NEW_UID: {"email": "hai.tai.khoan@gmail.com"}})

    assert PeopleResolver(db, fetch_node=fb).employee(NEW_UID) is emp
    assert emp.legacy_id == "uid_cu"


def test_skipped_uid_is_never_looked_up(db):
    skipped = next(iter(USER_SKIPPED))
    fb = FakeFirebase({skipped: {"email": "bat.ky@gmail.com"}})

    assert PeopleResolver(db, fetch_node=fb).employee(skipped) is None
    assert fb.calls == []


def test_firebase_unreachable_or_no_email_leaves_requester_empty_and_asks_once(db):
    add_employee(db, "NSU908", email="")
    for answer in (None, {}, {"email": ""}, "chuoi la"):
        fb = FakeFirebase({NEW_UID: answer})
        people = PeopleResolver(db, fetch_node=fb)
        assert people.employee(NEW_UID) is None
        assert people.employee(NEW_UID) is None
        assert len(fb.calls) == 1, answer


def test_blank_email_never_matches_profiles_without_email(db):
    #  Hồ sơ trống email + người app cũ trống email: "" == "" không được thành một cặp.
    add_employee(db, "NSU909", email="")
    fb = FakeFirebase({NEW_UID: {"email": "   "}})

    assert PeopleResolver(db, fetch_node=fb).employee(NEW_UID) is None


def test_stamped_uid_and_empty_uid_skip_firebase(db):
    emp = add_employee(db, "NSU910", email="da.gan@gmail.com", legacy_id=NEW_UID)
    fb = FakeFirebase()
    people = PeopleResolver(db, fetch_node=fb)

    assert people.employee(NEW_UID) is emp
    assert people.employee("") is None
    assert fb.calls == []
