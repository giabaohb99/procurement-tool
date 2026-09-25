"""bao-CR-487 — bộ lọc màn Xử lý khảo sát chọn được NHIỀU NCC / NHIỀU phân loại.

Đại ca (25/09/2026): «màn hình xử lý khảo sát, cho nút bỏ lọc, và cho filter select nhiều,
ví dụ phân loại hay chỗ nhà cung cấp». Backend nhận `supplier_code` / `item_group` lặp trên
URL; trong CÙNG một ô nhiều giá trị là HOẶC, hai ô khác nhau vẫn là VÀ. Đường gọi cũ truyền
một chuỗi (màn Xử lý YCMH) phải chạy y như trước.
"""
from app.modules.survey.model import Survey, SurveyProductLine
from app.modules.survey_request import service as S


def _survey(db, code, group, status="approved"):
    sv = Survey(code=code, survey_type="product", status=status, item_group=group)
    db.add(sv)
    db.flush()
    return sv


def _line(db, sv, supplier, name, approve="Đã duyệt"):
    ln = SurveyProductLine(survey_id=sv.id, supplier_code=supplier, product_name=name, line_approve=approve)
    db.add(ln)
    db.flush()
    return ln


def _names(rows):
    return sorted(r.product_name for r in rows)


def _seed_lines(db):
    nhan, thung = _survey(db, "KS-487-NHAN", "Nhãn"), _survey(db, "KS-487-THUNG", "Thùng")
    _line(db, nhan, "NCC-A", "Nhãn A")
    _line(db, nhan, "NCC-B", "Nhãn B")
    _line(db, thung, "NCC-A", "Thùng A")
    _line(db, thung, "NCC-C", "Thùng C")
    _line(db, thung, "NCC-C", "Thùng C chưa duyệt", approve="Chờ duyệt")
    db.commit()


def test_normalize_accepts_one_string_or_a_list_and_drops_blanks():
    assert S.normalize_filter_values("NCC-A") == ["NCC-A"]
    assert S.normalize_filter_values(["NCC-A", " ", "", "NCC-B "]) == ["NCC-A", "NCC-B"]
    assert S.normalize_filter_values("") == []
    assert S.normalize_filter_values(None) == []
    assert S.normalize_filter_values([]) == []


def test_many_suppliers_in_one_box_mean_or(db):
    _seed_lines(db)
    rows, total = S.available_survey_lines(db, supplier_code=["NCC-A", "NCC-C"])
    assert total == 3 and _names(rows) == ["Nhãn A", "Thùng A", "Thùng C"]


def test_many_groups_in_one_box_mean_or_and_boxes_combine_with_and(db):
    _seed_lines(db)
    rows, total = S.available_survey_lines(db, item_group=["Nhãn", "Thùng"])
    assert total == 4
    rows, total = S.available_survey_lines(db, supplier_code=["NCC-A"], item_group=["Nhãn", "Thùng"])
    assert total == 2 and _names(rows) == ["Nhãn A", "Thùng A"]


def test_old_single_string_call_still_works(db):
    """Màn Xử lý YCMH (`purchase_request/controller.py`) và bản v1 vẫn truyền MỘT chuỗi."""
    _seed_lines(db)
    rows, total = S.available_survey_lines(db, supplier_code="NCC-B", item_group="Nhãn")
    assert total == 1 and rows[0].product_name == "Nhãn B"


def test_empty_list_means_no_filter_on_that_box_not_match_nothing(db):
    """Bỏ lọc một ô (danh sách rỗng) là KHÔNG lọc theo ô đó — không phải lọc «không có gì»."""
    _seed_lines(db)
    rows, total = S.available_survey_lines(db, supplier_code=[], item_group=[], search="Thùng")
    assert total == 2 and _names(rows) == ["Thùng A", "Thùng C"]


def test_unapproved_and_cancelled_lines_never_leak_through_a_wide_filter(db):
    _seed_lines(db)
    cancelled = _survey(db, "KS-487-HUY", "Thùng", status="cancelled")
    _line(db, cancelled, "NCC-C", "Thùng C của phiếu hủy")
    db.commit()
    rows, total = S.available_survey_lines(db, supplier_code=["NCC-C"])
    assert total == 1 and rows[0].product_name == "Thùng C"
