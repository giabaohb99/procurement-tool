"""Ô tìm kiếm màn Khảo sát — tìm được cả theo dòng sản phẩm, và tìm bằng SUBQUERY.

Bản cũ gom `survey_id` của bảng dòng ra một list Python rồi `Survey.id.in_(list)`. Trên thật
bảng `tab_survey_product_line` đã hơn 5000 dòng, nên gõ một từ phổ biến là câu SQL phình ra
hàng nghìn tham số — đúng mẫu lỗi C1 đã vá ở `survey/service.py::report_rows`.

Hai thứ được kiểm ở đây: kết quả tìm kiếm KHÔNG đổi, và hình dạng SQL là subquery.
"""
from app.modules.survey.controller import search_condition
from app.modules.survey.model import Survey, SurveyProductLine


def codes(db, keyword: str) -> set[str]:
    return {s.code for s in db.query(Survey).filter(search_condition(keyword)).all()}


def make(db):
    """3 phiếu: khớp ở cột đầu phiếu · khớp ở dòng SP · không khớp gì."""
    rows = [
        Survey(code="KS001", survey_type="product", item_name="Thùng carton 3 lớp"),
        Survey(code="KS002", survey_type="product", item_name="Nhãn dán"),
        Survey(code="KS003", survey_type="product", item_name="Băng keo"),
    ]
    db.add_all(rows)
    db.commit()
    s2 = db.query(Survey).filter(Survey.code == "KS002").one()
    db.add_all([
        SurveyProductLine(survey_id=s2.id, internal_code="VT-CARTON-01", product_name="Carton A"),
        # Dòng chưa gắn phiếu (survey_id = 0, gặp ở dữ liệu nhập từ Excel) — không kéo theo gì.
        SurveyProductLine(survey_id=0, internal_code="VT-CARTON-99", product_name="Carton Z"),
    ])
    db.commit()


def test_tim_theo_cot_dau_phieu(db):
    make(db)
    assert codes(db, "KS003") == {"KS003"}
    assert codes(db, "Nhãn") == {"KS002"}


def test_tim_theo_ma_va_ten_hang_o_dong_san_pham(db):
    make(db)
    # "carton" khớp item_name của KS001 VÀ khớp dòng SP của KS002
    assert codes(db, "carton") == {"KS001", "KS002"}
    # Chỉ có ở dòng SP, không có trên đầu phiếu
    assert codes(db, "VT-CARTON-01") == {"KS002"}


def test_dong_chua_gan_phieu_khong_keo_theo_gi(db):
    make(db)
    assert codes(db, "VT-CARTON-99") == set()


def test_hinh_dang_sql_la_subquery_khong_phai_in_danh_sach_id(db):
    """Chốt mẫu C1: câu SQL phải chứa `IN (SELECT ...)`, không phải IN với id nhồi sẵn."""
    make(db)
    sql = str(db.query(Survey).filter(search_condition("carton")).statement)
    assert "IN (SELECT" in sql.replace("\n", " ").replace("  ", " ")
