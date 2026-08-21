"""CR-111 — 7 trường bổ sung cho dòng khảo sát SẢN PHẨM (phiếu hỗ trợ TK20082604).

Hai thứ cần khoá lại bằng test:

1. `_price_hint` — hai ô "Giá mua gần nhất" / "Giá mua max" được điền sẵn từ Lịch sử mua hàng
   theo mã VTBB ở đầu phiếu. Đây là chỗ dễ vỡ nhất vì nó phụ thuộc bảng KHÁC module.
2. Vòng lưu — trường mới phải đi được từ payload FE (`ProductLineIn`) xuống DB rồi quay ra
   `_out`. `ProductLineIn` để `extra='ignore'` nên trường nào quên khai báo sẽ bị NUỐT im lặng,
   không báo lỗi — đúng loại lỗi chỉ test mới bắt được.
"""
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.survey.controller import _out, _price_hint
from app.modules.survey.model import Survey
from app.modules.survey.schema import ProductLineIn


def _ph(code: str, date: str, price: float, **kw) -> PurchaseHistory:
    base = dict(product_code=code, order_date=date, price=price, unit="cái",
                supplier_code="NX", source="legacy")
    base.update(kw)
    return PurchaseHistory(**base)


def _survey(db, **kw) -> Survey:
    base = dict(code="KS111", survey_type="product", status="draft")
    base.update(kw)
    s = Survey(**base)
    db.add(s)
    db.commit()
    return s


# ── _price_hint ────────────────────────────────────────────────────────────────
def test_lay_dung_gia_gan_nhat_va_gia_cao_nhat(db):
    """Gần nhất = theo NGÀY (không phải giá lớn nhất), max = giá cao nhất trong cả lịch sử."""
    db.add_all([
        _ph("VT01", "2026-01-10", 10000),
        _ph("VT01", "2026-05-20", 12000, unit="thùng"),   # mới nhất
        _ph("VT01", "2026-03-15", 25000),                 # đắt nhất
    ])
    db.commit()

    h = _price_hint(db, _survey(db, item_code="VT01"))
    assert h["last"] == 12000
    assert h["max"] == 25000
    assert h["count"] == 3
    assert h["unit"] == "thùng"        # ĐVT của dòng gần nhất, để FE cảnh báo lệch ĐVT
    assert h["date"] == "2026-05-20"


def test_khong_lay_nham_ma_khac(db):
    """Lọc theo `product_code`; mã khác có giá cao hơn cũng không được lọt vào."""
    db.add_all([_ph("VT01", "2026-01-10", 10000), _ph("VT02", "2026-06-01", 99000)])
    db.commit()

    h = _price_hint(db, _survey(db, item_code="VT01"))
    assert (h["last"], h["max"], h["count"]) == (10000, 10000, 1)


def test_bo_qua_dong_gia_bang_0(db):
    """Dòng lịch sử cũ nhập thiếu giá (=0) không phải "giá mua" — lấy vào là gợi ý sai."""
    db.add_all([_ph("VT01", "2026-06-01", 0), _ph("VT01", "2026-01-10", 8000)])
    db.commit()

    h = _price_hint(db, _survey(db, item_code="VT01"))
    assert h["last"] == 8000           # dòng 0đ mới hơn nhưng bị loại
    assert h["count"] == 1


def test_khong_co_ma_hoac_khong_co_lich_su_thi_tra_rong(db):
    """Phiếu khảo sát hàng chưa có mã trong hệ thống vẫn phải mở được, không nổ."""
    rong = {"last": 0.0, "max": 0.0, "count": 0, "unit": "", "date": ""}
    assert _price_hint(db, _survey(db, item_code="")) == rong
    assert _price_hint(db, _survey(db, code="KS111B", item_code="   ")) == rong
    assert _price_hint(db, _survey(db, code="KS111C", item_code="CHUA-MUA")) == rong


def test_payload_chi_tiet_co_san_price_hint(db):
    """`_out` phải kèm `price_hint` — FE đọc thẳng khối này để điền sẵn, không gọi API riêng."""
    db.add(_ph("VT01", "2026-02-02", 7000))
    db.commit()

    out = _out(db, _survey(db, item_code="VT01"))
    assert out["price_hint"]["last"] == 7000


# ── Vòng lưu 7 trường mới ──────────────────────────────────────────────────────
CR111 = {
    "invoice_name": "Thùng carton 5 lớp - loại A",
    "active_ingredient": "Không có",
    "last_purchase_price": 12000,
    "max_purchase_price": 25000,
    "extra_shipping_cost": 350000,
    "shipping_policy": "NCC giao tận kho, đơn dưới 5 triệu tính phí",
    "debt_policy": "Công nợ 30 ngày",
}


def test_bay_truong_moi_khong_bi_nuot_khi_luu(db, seed):
    """`ProductLineIn` bỏ qua field lạ, nên quên khai một trường là mất dữ liệu trong im lặng."""
    from app.modules.survey import service

    s = _survey(db, code="KS111-SAVE", item_group="Thùng")
    line = ProductLineIn(supplier_code="NX", product_name="Thùng Carton A",
                         price_by_volume=8000, request_qty=10, vat=8, **CR111)

    # Field lạ phải bị bỏ, nhưng 7 field CR-111 thì không.
    assert line.model_dump()["invoice_name"] == CR111["invoice_name"]

    service._save_product_lines(db, s.id, [line], user_id=1)
    dong = _out(db, s)["product_lines"][0]
    for k, v in CR111.items():
        assert dong[k] == v, f"trường {k} không lưu đúng"


def test_mac_dinh_rong_khong_lam_vo_dong_cu(db, seed):
    """Dòng cũ (5090 dòng trên prod) không có 7 trường này — đọc ra phải là rỗng/0, không None.

    Cột DB đặt NOT NULL + default nên `_dict` luôn trả giá trị; FE format số sẽ nổ nếu gặp None.
    """
    from app.modules.survey.model import SurveyProductLine

    s = _survey(db, code="KS111-CU")
    db.add(SurveyProductLine(survey_id=s.id, supplier_code="NX", product_name="Dòng cũ"))
    db.commit()

    dong = _out(db, s)["product_lines"][0]
    assert dong["invoice_name"] == "" and dong["active_ingredient"] == ""
    assert dong["shipping_policy"] == "" and dong["debt_policy"] == ""
    assert dong["last_purchase_price"] == 0 and dong["max_purchase_price"] == 0
    assert dong["extra_shipping_cost"] == 0


def test_phi_vc_phat_sinh_tach_khoi_phi_van_chuyen(db, seed):
    """Hai khoản phí thương lượng riêng — phải là HAI cột, không được đè lên nhau."""
    from app.modules.survey import service

    s = _survey(db, code="KS111-PHI")
    line = ProductLineIn(supplier_code="NX", product_name="X",
                         shipping_cost=100000, extra_shipping_cost=350000)
    service._save_product_lines(db, s.id, [line], user_id=1)

    dong = _out(db, s)["product_lines"][0]
    assert dong["shipping_cost"] == 100000
    assert dong["extra_shipping_cost"] == 350000
