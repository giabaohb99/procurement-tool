"""ĐIỀU KIỆN ÁP DỤNG CỦA HỒ SƠ — `apply_doc_kinds` + `apply_conditions` (21/09/2026).

Hồ sơ khai *«giấy này phải kèm theo chứng từ nào»*; trang chi tiết chứng từ mọc
ra thẻ «Hồ sơ cần kèm». Luật ở `app/modules/dossier/applicability.py`.

Soi đúng mấy chỗ hỏng trong im lặng:

* **Hai ca rỗng, hai nghĩa ngược nhau.** `apply_doc_kinds` rỗng = không bao giờ
  hiện (hành vi của mọi hồ sơ lập trước ngày này); `apply_doc_kinds` có +
  `apply_conditions` rỗng = áp cho MỌI phiếu loại đó. Lẫn hai ca là hoặc cả
  công ty thấy thẻ rác, hoặc điều kiện khai xong không bao giờ chạy.
* **Ô rỗng không được khớp `contains`.** Dòng YCBG chưa chốt phương án thì không
  có mã SP; không chặn thì mọi dòng như vậy lọt vào điều kiện theo sản phẩm.
* **Khai sai phải NÉM**, không nuốt. Nuốt thì người dùng thấy báo lưu thành công
  rồi tin rằng hồ sơ đã gắn điều kiện — trong khi nó sẽ không hiện ra ở đâu cả.
"""
import pytest
from pydantic import ValidationError

from app.modules.dossier.applicability import (DOC_KINDS, FIELDS, OPS,
                                               matches_line, reason_of,
                                               validate_conditions,
                                               validate_doc_kinds)
from app.modules.dossier.schema import DossierCreate, DossierUpdate


def _cond(field="product_code", op="eq", value="SP-001"):
    return {"field": field, "op": op, "value": value}


# ── Bộ mã ───────────────────────────────────────────────────────────────────
def test_bon_loai_chung_tu_va_hai_chieu_dieu_kien():
    """Khai thừa một mã ở đây là hứa một màn mà không ai dựng thẻ cho nó."""
    assert set(DOC_KINDS) == {"purchase_request", "purchase_order",
                              "survey_request", "survey"}
    assert set(FIELDS) == {"product_code", "item_group"}
    #  Không có gt/lt: so mã sản phẩm «lớn hơn» thì ra câu không ai đọc được nghĩa.
    assert set(OPS) == {"eq", "ne", "in", "not_in", "contains"}


def test_moi_loai_chung_tu_khai_du_entity_de_gac_cua_thu_hai():
    """Thiếu `entity` là endpoint không gác được chứng từ nguồn → lộ nội dung đơn."""
    for kind, meta in DOC_KINDS.items():
        assert meta["entity"], kind
        assert meta["label"], kind


# ── Kiểm lúc KHAI ───────────────────────────────────────────────────────────
def test_ma_man_la_bi_bo_qua_chu_khong_no():
    assert validate_doc_kinds(["purchase_order", "khong_co_that", "purchase_order"]) == [
        "purchase_order"
    ]
    assert validate_doc_kinds(None) == []
    assert validate_doc_kinds("purchase_order") == []


def test_chieu_hoac_phep_so_sanh_la_thi_NEM_loi():
    with pytest.raises(ValueError, match="chiều điều kiện"):
        validate_conditions([_cond(field="supplier_code")])
    with pytest.raises(ValueError, match="phép so sánh"):
        validate_conditions([_cond(op="gt")])


def test_gia_tri_rong_bi_chan_o_ca_hai_dang():
    """Điều kiện không có giá trị để so là điều kiện không bao giờ khớp."""
    with pytest.raises(ValueError, match="chưa nhập giá trị"):
        validate_conditions([_cond(value="   ")])
    with pytest.raises(ValueError, match="ít nhất một giá trị"):
        validate_conditions([_cond(op="in", value=[" ", ""])])


def test_in_chuan_hoa_ve_danh_sach_con_lai_ve_chuoi():
    assert validate_conditions([_cond(op="in", value="SP-001")])[0]["value"] == ["SP-001"]
    assert validate_conditions([_cond(value=" SP-001 ")])[0]["value"] == "SP-001"


def test_chan_tran_so_dong_va_so_gia_tri():
    with pytest.raises(ValueError, match="Tối đa 10 dòng"):
        validate_conditions([_cond() for _ in range(11)])
    with pytest.raises(ValueError, match="tối đa 50 giá trị"):
        validate_conditions([_cond(op="in", value=[f"SP-{i}" for i in range(51)])])
    with pytest.raises(ValueError, match="tối đa 100 ký tự"):
        validate_conditions([_cond(value="x" * 101)])


def test_schema_chan_ngay_luc_luu_chu_khong_de_lot_xuong_DB():
    """⚠️ SQLite của bộ test KHÔNG ép gì cả — phải kiểm ở tầng SCHEMA."""
    with pytest.raises(ValidationError):
        DossierCreate(name="X", dossier_type_id=1, apply_conditions=[_cond(op="gt")])
    with pytest.raises(ValidationError):
        DossierUpdate(apply_conditions=[_cond(field="gia")])


def test_update_khong_gui_thi_giu_nguyen_chu_khong_xoa():
    """`None` = không đụng tới. Đổi thành `[]` là gỡ sạch điều kiện đã khai."""
    assert DossierUpdate(name="X").apply_conditions is None
    assert DossierUpdate(apply_conditions=[]).apply_conditions == []


# ── Khớp ────────────────────────────────────────────────────────────────────
def test_khong_khai_dieu_kien_thi_moi_dong_deu_thoa():
    assert matches_line([], {"product_code": "SP-001"}) is True
    assert matches_line([], {}) is True


def test_cac_dong_dieu_kien_noi_nhau_bang_VA():
    conds = validate_conditions([
        _cond(field="product_code", value="SP-001"),
        _cond(field="item_group", value="Thiết bị"),
    ])
    assert matches_line(conds, {"product_code": "SP-001", "item_group": "Thiết bị"})
    assert not matches_line(conds, {"product_code": "SP-001", "item_group": "Bao bì"})


def test_khop_bo_qua_hoa_thuong_va_khoang_trang():
    """Mã SP gõ tay ở bốn màn — «sp-001 » và «SP-001» là cùng một thứ với người dùng."""
    conds = validate_conditions([_cond(value="SP-001")])
    assert matches_line(conds, {"product_code": " sp-001 "})
    conds_in = validate_conditions([_cond(op="in", value=["sp-001", "SP-002"])])
    assert matches_line(conds_in, {"product_code": "SP-001"})


@pytest.mark.parametrize("op,value,actual,expected", [
    ("eq", "SP-001", "SP-001", True),
    ("eq", "SP-001", "SP-0011", False),
    ("ne", "SP-001", "SP-002", True),
    ("ne", "SP-001", "SP-001", False),
    ("in", ["A", "B"], "B", True),
    ("in", ["A", "B"], "C", False),
    ("not_in", ["A", "B"], "C", True),
    ("not_in", ["A", "B"], "A", False),
    ("contains", "THEP", "Ống thep ma kem", True),
    ("contains", "THEP", "Van bi", False),
])
def test_tung_phep_so_sanh(op, value, actual, expected):
    conds = validate_conditions([_cond(op=op, value=value)])
    assert matches_line(conds, {"product_code": actual}) is expected


def test_o_RONG_chi_khop_ne_va_not_in():
    """⚠️ Dòng YCBG chưa chốt phương án thì không có mã SP.

    Không chặn riêng ca rỗng thì `contains` với giá trị bất kỳ vẫn trượt đúng,
    nhưng `eq` với chuỗi rỗng — thứ `validate_conditions` đã cấm — và mọi phép
    so sánh về sau sẽ phải tự nhớ ngoại lệ này. Chặn một chỗ.
    """
    for op, value in (("eq", "SP-001"), ("contains", "SP"), ("in", ["SP-001"])):
        conds = validate_conditions([_cond(op=op, value=value)])
        assert not matches_line(conds, {"product_code": ""}), op
    for op, value in (("ne", "SP-001"), ("not_in", ["SP-001"])):
        conds = validate_conditions([_cond(op=op, value=value)])
        assert matches_line(conds, {"product_code": ""}), op


def test_chieu_khong_co_trong_dong_doc_ra_RONG_chu_khong_no():
    """Dòng YCBG không mang khóa `product_code` — `.get()` ra `None`, không `KeyError`."""
    conds = validate_conditions([_cond(value="SP-001")])
    assert matches_line(conds, {"item_group": "Thiết bị"}) is False


# ── Câu lý do ───────────────────────────────────────────────────────────────
def test_cau_ly_do_noi_ro_dong_nao_gay_ra():
    conds = validate_conditions([_cond(value="SP-001")])
    text = reason_of(conds, {"no": 3, "product_code": "SP-001"}, "purchase_order")
    assert "dòng 3" in text and "SP-001" in text


def test_phieu_khao_sat_khong_noi_so_dong_vi_no_khong_co_bang_dong():
    conds = validate_conditions([_cond(value="SP-001")])
    text = reason_of(conds, {"no": 1, "product_code": "SP-001"}, "survey")
    assert "dòng" not in text


def test_khong_khai_dieu_kien_thi_ly_do_noi_thang_la_ap_cho_moi_phieu():
    text = reason_of([], {}, "purchase_order")
    assert "mọi" in text.lower() and "đơn mua hàng" in text.lower()
