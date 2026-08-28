"""Ô tìm nhanh ở màn Nhân sự (hr/employees) quét OR trên mã NV / họ tên / email /
điện thoại — trước đây chỉ khớp họ tên. Kiểm ở tầng `apply_keyword_search` để khỏi
dựng cả lớp RBAC của endpoint."""
from app.modules.employee.model import Employee
from app.modules.employee.service import apply_keyword_search


def _seed_people(db):
    people = [
        Employee(code="NV001", full_name="Nguyễn Văn An", email="an@dego.vn", phone="0912345678"),
        Employee(code="NV002", full_name="Trần Thị Bình", email="binh@dego.vn", phone="0987654321"),
        Employee(code="KT-09", full_name="Lê Công Danh", email="danh@corp.com", phone="0900000009"),
    ]
    db.add_all(people)
    db.flush()


def _codes(query):
    return sorted(e.code for e in query.all())


def test_finds_by_employee_code(db):
    _seed_people(db)
    assert _codes(apply_keyword_search(db.query(Employee), "NV002")) == ["NV002"]


def test_finds_by_email_fragment(db):
    _seed_people(db)
    assert _codes(apply_keyword_search(db.query(Employee), "danh@corp")) == ["KT-09"]


def test_finds_by_phone(db):
    _seed_people(db)
    assert _codes(apply_keyword_search(db.query(Employee), "0987654321")) == ["NV002"]


def test_still_finds_by_full_name(db):
    _seed_people(db)
    assert _codes(apply_keyword_search(db.query(Employee), "Bình")) == ["NV002"]


def test_blank_keyword_leaves_query_untouched(db):
    _seed_people(db)
    everyone = ["KT-09", "NV001", "NV002"]
    assert _codes(apply_keyword_search(db.query(Employee), "")) == everyone
    assert _codes(apply_keyword_search(db.query(Employee), "   ")) == everyone
    assert _codes(apply_keyword_search(db.query(Employee), None)) == everyone


def test_fragment_matching_many_returns_all_of_them(db):
    _seed_people(db)
    # "dego.vn" nằm trong email hai người -> OR trả cả hai, không nuốt bớt.
    assert _codes(apply_keyword_search(db.query(Employee), "dego.vn")) == ["NV001", "NV002"]


def test_no_match_returns_empty(db):
    _seed_people(db)
    assert _codes(apply_keyword_search(db.query(Employee), "khongtontai")) == []
