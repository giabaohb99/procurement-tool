"""bao-CR-291 — dòng YCBG phải đủ thông tin như popup dòng YCMH cũ.

Ba luật khóa ở đây:

1. **Tên vật tư đi CẶP với mã hàng.** Dòng YCBG không lưu tên hàng, nên tên (và ảnh
   gốc) phải tra LIVE từ danh mục theo `product_code`. Dòng không có mã thì tên rỗng —
   giao diện nhắc người lập mô tả vào ô Chi tiết thông số, chứ không bịa tên.
2. **Ảnh gốc lấy ảnh sort_order nhỏ nhất của SẢN PHẨM**, không lẫn ảnh của dòng.
3. **Sửa tiến độ gác theo DÒNG.** Quyền `survey_request.process` chỉ nói "là người thu
   mua"; không gác thêm thì NSTM sửa được tiến độ dòng của đồng nghiệp — ngược hẳn luật
   vừa siết ở nút lên đơn (bao-CR-290).
"""
import pytest
from fastapi import HTTPException

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.product.model import Product
from app.modules.survey_request import controller as sr_ct
from app.modules.survey_request import service
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine


def _profile(emp_code: str, scope: str = "proc") -> dict:
    return {"emp_code": emp_code, "employee_id": 0,
            "grants": [{"perms": {"survey_request": {"read": True, "scope": scope}}}]}


class _User:
    """Chỉ cần `.id` — hồ sơ quyền đã thay bằng monkeypatch."""
    id = 1


def _product_with_images(db, code: str, name: str, urls: list[tuple[str, int]]) -> Product:
    p = Product(code=code, name=name, is_active=True)
    db.add(p)
    db.flush()
    for url, sort_order in urls:
        f = StoredFile(filename=url.rsplit("/", 1)[-1], url=url, content_type="image/png",
                       size=1, file_key=url)
        db.add(f)
        db.flush()
        db.add(FileLink(entity="product", entity_id=p.id, file_id=f.id, sort_order=sort_order))
    db.commit()
    return p


def _sr_with_lines(db, codes: list[str]) -> tuple[SurveyRequest, list[SurveyRequestLine]]:
    s = SurveyRequest(code="YCBG-C291", status="survey_done")
    db.add(s)
    db.commit()
    lines = []
    for code in codes:
        ln = SurveyRequestLine(survey_request_id=s.id, item_group="Thùng", request_qty=3,
                               product_code=code, assignee="DEMONV")
        db.add(ln)
        lines.append(ln)
    db.commit()
    return s, lines


def test_dong_co_ma_thi_lay_ten_va_anh_goc_tu_danh_muc(db, seed):
    _product_with_images(db, "VT-A", "Thùng carton 3 lớp",
                         [("/f/anh-phu.png", 5), ("/f/anh-chinh.png", 1)])
    s, lines = _sr_with_lines(db, ["VT-A"])

    out = sr_ct._out(db, s)["lines"][0]

    assert out["product_name"] == "Thùng carton 3 lớp"
    # Ảnh đại diện = sort_order NHỎ NHẤT. Lấy nhầm ảnh cuối thì dòng nào cũng hiện
    # tấm ảnh phụ chụp góc khuất, người duyệt không nhận ra hàng.
    assert out["product_thumbnail_url"] == "/f/anh-chinh.png"
    assert out["product_id"] == db.query(Product).filter(Product.code == "VT-A").one().id
    assert lines[0].product_code == "VT-A", "tra danh mục là chỉ ĐỌC, không ghi ngược lên dòng"


@pytest.mark.parametrize("code", ["", "   ", "VT-KHONG-CO-TRONG-DANH-MUC"])
def test_dong_khong_khop_danh_muc_thi_ten_rong_chu_khong_bia(db, seed, code):
    s, _ = _sr_with_lines(db, [code])

    out = sr_ct._out(db, s)["lines"][0]

    assert out["product_name"] == ""
    assert out["product_thumbnail_url"] == ""
    assert out["product_id"] == 0


def test_nhieu_dong_trung_ma_van_ra_dung_ten(db, seed):
    """Mã lặp lại giữa các dòng: gom theo mã, không được lệch dòng hay rơi mất dòng."""
    _product_with_images(db, "VT-A", "Thùng carton", [])
    _product_with_images(db, "VT-B", "Nhãn dán", [])
    s, _ = _sr_with_lines(db, ["VT-A", "VT-B", "VT-A", ""])

    names = [ln["product_name"] for ln in sr_ct._out(db, s)["lines"]]

    assert names == ["Thùng carton", "Nhãn dán", "Thùng carton", ""]


def test_resolve_catalog_name_ma_rong_va_ma_la(db, seed):
    _product_with_images(db, "VT-A", "Thùng carton", [])

    assert service.resolve_catalog_name(db, "VT-A") == "Thùng carton"
    assert service.resolve_catalog_name(db, " VT-A ") == "Thùng carton"
    assert service.resolve_catalog_name(db, "") == ""
    assert service.resolve_catalog_name(db, None) == ""
    assert service.resolve_catalog_name(db, "KHONG-CO") == ""


def test_sua_tien_do_dong_cua_nguoi_khac_thi_403(db, seed, monkeypatch):
    s, lines = _sr_with_lines(db, ["VT-A"])       # dòng của DEMONV
    monkeypatch.setattr(sr_ct, "get_perm_profile", lambda _db, _u: _profile("NSTM-KHAC"))

    with pytest.raises(HTTPException) as e:
        sr_ct.set_line_progress_(s.id, lines[0].id, {"progress_note": "x"},
                                 db=db, user=_User())

    assert e.value.status_code == 403
    assert "nhân sự thu mua khác" in e.value.detail
    db.refresh(lines[0])
    assert lines[0].progress_note == ""


def test_nstm_phu_trach_ghi_duoc_ca_ghi_chu_thu_mua(db, seed, monkeypatch):
    s, lines = _sr_with_lines(db, ["VT-A"])
    monkeypatch.setattr(sr_ct, "get_perm_profile", lambda _db, _u: _profile("DEMONV"))

    sr_ct.set_line_progress_(s.id, lines[0].id,
                             {"expected_date": "2026-09-20", "progress_note": "NCC hẹn giao",
                              "purchaser_note": "Đề nghị đổi quy cách"},
                             db=db, user=_User())

    db.refresh(lines[0])
    assert lines[0].expected_date == "2026-09-20"
    assert lines[0].progress_note == "NCC hẹn giao"
    # Ô riêng của thu mua — KHÔNG được ghi đè ô "Yêu cầu khác" của người yêu cầu.
    assert lines[0].purchaser_note == "Đề nghị đổi quy cách"
    assert lines[0].other_requirement == ""


def test_quan_ly_scope_all_sua_duoc_tien_do_moi_dong(db, seed, monkeypatch):
    s, lines = _sr_with_lines(db, ["VT-A"])
    monkeypatch.setattr(sr_ct, "get_perm_profile",
                        lambda _db, _u: _profile("QL-TM", scope="all"))

    sr_ct.set_line_progress_(s.id, lines[0].id, {"purchaser_note": "ghi hộ"},
                             db=db, user=_User())

    db.refresh(lines[0])
    assert lines[0].purchaser_note == "ghi hộ"
