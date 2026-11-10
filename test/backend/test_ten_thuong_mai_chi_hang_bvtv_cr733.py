"""bao-CR-733 (sửa bộ dò) — tên thương mại thuốc BVTV chỉ dò trên dòng thuộc nhóm HS 3808.

Chạy thử script gắn lại trên prod (09/11) ra 381 dòng đổi, mẫu là hàng HƯƠNG LIỆU đang mang hoạt chất thuốc BVTV và
sau khi chạy vẫn mang một hoạt chất BVTV khác. Nguyên nhân: danh mục có thuốc tên đúng bằng từ thường — GAULOIS
(Brodifacoum), ELIXIR (Chlorothalonil + Mancozeb), POWER (Cypermethrin), JASMINE (Difenoconazole + Propiconazole),
ABSOLUTE (Hexaconazole + Isoprothiolane). Tên hàng chứa hai từ như vậy: thứ tự `set` cũ chọn một, bản sửa bao-CR-728
chọn từ đứng trước — cả hai đều sai, đúng phải là rỗng vì hàng không phải thuốc BVTV.

Tên hàng dưới đây là tên GIẢ dựng sát mô tả mẫu prod (dữ liệu local / dev không có các dòng đó); hoạt chất của năm tên
thương mại chép đúng danh mục thuốc BVTV đang nạp.
"""
from app.modules.customs.ingredient import IngredientTagger, allows_trade_names, extract_formulation, retag_changed
from app.modules.customs.model import CustomsLine, CustomsPesticide

CATALOG = [
    ("GAULOIS", "Brodifacoum"),
    ("ELIXIR", "Chlorothalonil 125g/kg + Mancozeb 625g/kg"),
    ("POWER", "Cypermethrin (min 90 %)"),
    ("JASMINE", "Difenoconazole 150g/l + Propiconazole 150g/l"),
    ("ABSOLUTE", "Hexaconazole 5% + Isoprothiolane 30%"),
]
FRAGRANCES = [
    ("33021090", "MẪU HƯƠNG LIỆU GAULOIS ELIXIR 100GR", "Brodifacoum"),
    ("33029000", "HƯƠNG LIỆU DÙNG SẢN XUẤT BỘT GIẶT RED POWER DK", "Cypermethrin (min 90 %)"),
    ("33029000", "HƯƠNG LIỆU DÙNG SẢN XUẤT BỘT GIẶT RED POWER DL", "Cypermethrin (min 90 %)"),
    ("33012990", "JASMINE SAMBAC ABSOLUTE", "Difenoconazole 150g/l + Propiconazole 150g/l"),
]


def _tagger() -> IngredientTagger:
    return IngredientTagger([("CYPERMETHRIN", "CYPERMETHRIN")], CATALOG)


def test_tai_hien_khop_nham_khi_khong_biet_ma_hs():
    """Không có mã HS thì vẫn dò như cũ — đây là đúng cái khớp nhầm thấy trên prod."""
    for _, name, wrong in FRAGRANCES:
        assert _tagger().tag(name)[0] == wrong


def test_huong_lieu_ngoai_nhom_3808_khong_mang_hoat_chat_bvtv():
    for hs, name, _ in FRAGRANCES:
        assert _tagger().tag(name, hs)[0] == "", name


def test_hang_3808_van_gan_theo_ten_thuong_mai():
    assert _tagger().tag("POWER 5EC (THUỐC TRỪ SÂU)", "38089190") == ("Cypermethrin (min 90 %)", "5EC")
    assert _tagger().tag("GAULOIS 0.005%RB", "'38089990")[0] == "Brodifacoum", "dấu nháy chữ của Excel vẫn nhận"


def test_ten_hoat_chat_khong_phu_thuoc_ma_hs():
    """Bước theo TÊN HOẠT CHẤT giữ nguyên với mọi mã HS (thuốc kỹ thuật hay khai ở chương 29)."""
    assert _tagger().tag("CYPERMETHRIN 95% TECH", "29269095")[0] == "CYPERMETHRIN"


def test_nhom_ma_hs_cho_phep_do_ten_thuong_mai():
    assert allows_trade_names("38089990") and allows_trade_names("'38089190")
    assert allows_trade_names("") and allows_trade_names(None), "chưa có mã HS thì không đủ căn cứ để chặn"
    assert not allows_trade_names("33029000") and not allows_trade_names("38249999")


def _line(db, name: str, hs: str, active: str, from_file: bool = False) -> CustomsLine:
    from datetime import date
    line = CustomsLine(reg_date=date(2026, 1, 13), hs_code=hs, product_name=name, active_ingredient=active,
                       active_ingredient_from_file=from_file, formulation=extract_formulation(name), product_kind=1)
    db.add(line)
    return line


def test_gan_lai_xoa_hoat_chat_bvtv_sai_cua_hang_ngoai_3808(db):
    for trade, active in CATALOG:
        db.add(CustomsPesticide(trade_name=trade, trade_key=trade, active_ingredient=active))
    wrong = _line(db, "MẪU HƯƠNG LIỆU GAULOIS ELIXIR 100GR", "33021090", "Chlorothalonil 125g/kg + Mancozeb 625g/kg")
    typed = _line(db, "JASMINE SAMBAC ABSOLUTE", "33012990", "Tay nhập", from_file=True)
    pesticide = _line(db, "POWER 5EC", "38089190", "Cypermethrin (min 90 %)")
    db.commit()

    dry = retag_changed(db)
    assert (dry["changed"], dry["active"], dry["cleared"]) == (1, 1, 1)
    assert dry["examples"][0]["hs_code"] == "33021090"
    done = retag_changed(db, apply=True)
    assert done["cleared"] == 1
    db.expire_all()
    assert db.get(CustomsLine, wrong.id).active_ingredient == ""
    assert db.get(CustomsLine, typed.id).active_ingredient == "Tay nhập", "giá trị người nhập giữ nguyên"
    assert db.get(CustomsLine, pesticide.id).active_ingredient == "Cypermethrin (min 90 %)"
    assert retag_changed(db)["changed"] == 0, "chạy lại ra 0 — idempotent"


def test_sua_ma_hs_tren_man_thi_suy_lai_hoat_chat(db):
    from app.modules.customs.line_edit_service import update_line
    from app.modules.customs.schema import CustomsLineUpdate
    for trade, active in CATALOG:
        db.add(CustomsPesticide(trade_name=trade, trade_key=trade, active_ingredient=active))
    line = _line(db, "GAULOIS 0.005%RB", "33021090", "")
    db.commit()
    update_line(db, line.id, CustomsLineUpdate(hs_code="38089990"), user_id=1)
    assert db.get(CustomsLine, line.id).active_ingredient == "Brodifacoum"
    update_line(db, line.id, CustomsLineUpdate(hs_code="33021090"), user_id=1)
    assert db.get(CustomsLine, line.id).active_ingredient == ""
