"""bao-CR-481 — bốn tool hải quan của trợ lý AI: so sánh · thị trường · pháp lý · «có nên mua lúc này».

Canh những chỗ mà sai là trợ lý nói sai với người sắp đặt hàng thật:

```
giá tháng gần nhất thấp/cao so với cả năm   -> chấm theo tứ phân vị các tháng ĐỦ dữ liệu
tháng gần nhất ít dòng                      -> vẫn trả nhưng reliable=False
dữ liệu cũ quá 45 ngày                      -> stale=True, trợ lý phải nói giá hôm nay có thể đã khác
thị phần / đối tác / xuất xứ                -> CHỈ trong một đơn vị tính, không cộng kg với lít
pháp lý                                      -> nặng nhất lên đầu, có câu «không có mức phạt»
```
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.customs import service as S
from app.modules.customs.constants import MIN_LINES_FOR_BEST, PartyType, RegulationList
from app.modules.customs.model import CustomsLine, CustomsParty, CustomsRegulation, CustomsTariff


def _line(db, d, name="ATRAZINE 97% TECH", unit="KGM", price=3.0, qty=100, **kw):
    db.add(CustomsLine(reg_date=d, product_name=name, unit_code=unit, price_usd=Decimal(str(price)),
                       quantity=Decimal(str(qty)), hs_code=kw.pop("hs", "38089319"), **kw))


def _ctx(db, monkeypatch, allowed: bool):
    from app.modules.assistant.tools.base import ToolContext
    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": allowed)
    return ToolContext(db=db, user=SimpleNamespace(id=1))


def _stats(prices_counts, date_to="2026-06-30"):
    """Dựng `compute_stats` giả: mỗi phần tử (wavg, count) là một tháng liên tiếp từ 01/2026."""
    series = [{"period": f"2026-{i + 1:02d}", "label": f"{i + 1:02d}/2026", "count": c, "wavg": p}
              for i, (p, c) in enumerate(prices_counts)]
    return {"series": series, "coverage": {"date_to": date_to}}


# ── Đánh giá thời điểm hiện tại ─────────────────────────────────────────────
def test_gia_thang_gan_nhat_re_nhat_nam_la_thap_va_dang_giam():
    now = S.assess_current_price(_stats([(3.0, 6), (3.2, 6), (3.4, 6), (3.6, 6), (2.8, 6)]),
                                 today=date(2026, 7, 10))
    assert now["price_level"] == "thấp" and now["pct_months_cheaper"] == 0
    assert now["trend_3_months"] == "đang giảm"
    assert now["latest_month"] == "05/2026" and now["reliable"] is True
    assert now["stale"] is False


def test_gia_thang_gan_nhat_dat_nhat_la_cao_va_dang_tang():
    now = S.assess_current_price(_stats([(3.0, 6), (3.1, 6), (3.2, 6), (3.3, 6), (3.9, 6)]),
                                 today=date(2026, 7, 10))
    assert now["price_level"] == "cao" and now["pct_months_cheaper"] == 80
    assert now["trend_3_months"] == "đang tăng"


def test_thang_gan_nhat_it_dong_khong_lat_duoc_xu_huong():
    """Dữ liệu thật 24/09: ATRAZINE 09/2026 chỉ 1 dòng giá rẻ mà suýt thành «đang giảm».
    Tháng ít dòng vẫn được chấm (reliable=False) nhưng thước đo + xu hướng chỉ lấy tháng đủ
    dữ liệu, và có `reference_month` để trợ lý nói bằng mốc đáng tin."""
    now = S.assess_current_price(_stats([(3.0, 6), (3.2, 6), (3.4, 6), (1.0, MIN_LINES_FOR_BEST - 1)]),
                                 today=date(2026, 7, 10))
    assert now["reliable"] is False and now["latest_count"] == MIN_LINES_FOR_BEST - 1
    assert now["monthly_q1"] == 3.1                   # 1.0 không lọt vào thước đo
    assert now["price_level"] == "thấp"
    assert now["trend_3_months"] == "đang tăng"       # 3.0 -> 3.4, lô lẻ 1.0 không tính
    assert now["reference_month"] == {"label": "03/2026", "wavg": 3.4, "count": 6, "price_level": "cao"}


def test_thang_gan_nhat_du_dong_thi_khong_can_moc_tham_chieu():
    now = S.assess_current_price(_stats([(3.0, 6), (3.1, 6)]), today=date(2026, 3, 1))
    assert now["reliable"] is True and now["reference_month"] is None


def test_chua_thang_nao_du_dong_thi_van_danh_gia_tren_tat_ca_nhung_khong_tin_duoc():
    now = S.assess_current_price(_stats([(3.0, 2), (3.3, 1)]), today=date(2026, 3, 1))
    assert now["reliable"] is False and now["reference_month"] is None
    assert now["price_level"] == "cao"


def test_du_lieu_cu_qua_45_ngay_thi_gan_co_stale():
    now = S.assess_current_price(_stats([(3.0, 6), (3.1, 6)], date_to="2026-06-30"), today=date(2026, 9, 24))
    assert now["stale"] is True and now["data_age_days"] == 86


def test_mot_thang_thi_noi_chua_du_de_bao_xu_huong():
    now = S.assess_current_price(_stats([(3.0, 6)]), today=date(2026, 7, 1))
    assert now["trend_3_months"] == "chưa đủ tháng để nói xu hướng"


def test_khong_co_thang_nao_co_gia_thi_khong_danh_gia():
    assert S.assess_current_price(_stats([(None, 0), (None, 0)]))["available"] is False
    assert S.assess_current_price({"series": [], "coverage": {}})["available"] is False


# ── Thị trường ──────────────────────────────────────────────────────────────
def _parties(db):
    imp = CustomsParty(party_type=PartyType.DOMESTIC, dedupe_key="0101", tax_code="0101", name="CTY A")
    sup = CustomsParty(party_type=PartyType.FOREIGN, dedupe_key="SUP-X", name="SHANDONG X")
    sup2 = CustomsParty(party_type=PartyType.FOREIGN, dedupe_key="SUP-Y", name="JIANGSU Y")
    db.add_all([imp, sup, sup2])
    db.commit()
    return imp, sup, sup2


def test_thi_truong_doi_tac_xuat_xu_chi_trong_mot_don_vi(db):
    imp, sup, sup2 = _parties(db)
    _line(db, date(2026, 1, 5), qty=300, importer_id=imp.id, partner_id=sup.id, origin_country="CN")
    _line(db, date(2026, 2, 5), qty=100, importer_id=imp.id, partner_id=sup2.id, origin_country="IN")
    #  Dòng LÍT rất lớn — không được lọt vào thị phần của đơn vị KGM.
    _line(db, date(2026, 3, 5), unit="LTR", qty=99999, partner_id=sup2.id, origin_country="IN")
    db.commit()
    mk = S.market_overview(db, {"q": "atrazine"})

    assert mk["unit"] == "KGM"
    assert [p["name"] for p in mk["partners"]] == ["SHANDONG X", "JIANGSU Y"]
    assert mk["partners"][0]["share"] == 0.75
    assert [o["country"] for o in mk["origins"]] == ["CN", "IN"] and mk["origins"][1]["qty"] == 100
    assert [x["date"] for x in mk["recent_lines"]] == ["2026-02-05", "2026-01-05"]   # mới nhất trước, bỏ LTR
    assert mk["importers"][0]["name"] == "CTY A" and mk["total_importers"] == 1


def test_thi_truong_thieu_bo_loc_thi_chan(db):
    with pytest.raises(HTTPException):
        S.market_overview(db, {})


def test_tool_thi_truong_gac_quyen_va_bo_id_noi_bo(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_MARKET_SPEC
    imp, sup, _ = _parties(db)
    _line(db, date(2026, 1, 5), importer_id=imp.id, partner_id=sup.id, origin_country="CN")
    db.commit()

    assert CUSTOMS_MARKET_SPEC.handler(_ctx(db, monkeypatch, False), {"keyword": "atrazine"})["denied"] is True
    res = CUSTOMS_MARKET_SPEC.handler(_ctx(db, monkeypatch, True), {"keyword": "atrazine", "limit": 999})
    assert "importer_id" not in res["importers"][0]
    assert "error" in CUSTOMS_MARKET_SPEC.handler(_ctx(db, monkeypatch, True), {})


# ── Pháp lý + thuế ──────────────────────────────────────────────────────────
def _reg(db, code, name, cas, **kw):
    db.add(CustomsRegulation(list_code=int(code), name=name, cas_no=cas, is_active=True, **kw))


def test_tool_phap_ly_nang_nhat_len_dau_va_noi_khong_co_muc_phat(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_LEGAL_CHECK_SPEC
    _reg(db, RegulationList.ND24_PL2, "Chlorpyrifos solution", "1-1-1")
    _reg(db, RegulationList.PUBLISH_TT01, "Chlorpyrifos", "2921-88-2")
    _reg(db, RegulationList.BANNED_TT75, "Chlorpyrifos ethyl", "2921-88-2", banned_year=2019,
         legal_basis="TT 75/2025/TT-BNNMT")
    _reg(db, RegulationList.ND24_PL4, "Chlorpyrifos methyl", "5598-13-0", threshold_kg=Decimal("100"),
         legal_basis="NĐ 24/2026/NĐ-CP Phụ lục IV")
    db.commit()
    res = CUSTOMS_LEGAL_CHECK_SPEC.handler(_ctx(db, monkeypatch, True), {"query": "chlorpyrifos"})

    names = [r["name"] for r in res["regulations"]["items"]]
    assert names == ["Chlorpyrifos ethyl", "Chlorpyrifos methyl", "Chlorpyrifos", "Chlorpyrifos solution"]
    assert "CẤM từ năm 2019" in res["regulations"]["items"][0]["obligation"]
    assert "KHÔNG có mức phạt" in res["note"]


def test_tool_phap_ly_khong_thay_thi_bao_not_found_khong_im_lang(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_LEGAL_CHECK_SPEC
    res = CUSTOMS_LEGAL_CHECK_SPEC.handler(_ctx(db, monkeypatch, True), {"query": "nuoc cat"})
    assert res["regulations"]["not_found"] is True and res["regulations"]["items"] == []


def test_tool_phap_ly_tra_thue_theo_ma_hs_va_bat_loi_dau_vao(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_LEGAL_CHECK_SPEC
    for hs, mfn in (("3808", ""), ("380893", ""), ("38089319", "3")):
        db.add(CustomsTariff(hs_code=hs, name_vn=hs, rate_mfn=mfn, fta_json='{"ACFTA": "0"}'))
    db.commit()
    ctx = _ctx(db, monkeypatch, True)

    res = CUSTOMS_LEGAL_CHECK_SPEC.handler(ctx, {"hs_code": "38089319"})
    assert [r["hs_code"] for r in res["tariff"]["rows"]] == ["3808", "380893", "38089319"]
    assert res["tariff"]["rows"][-1]["fta"] == {"ACFTA": "0"} and "regulations" not in res
    assert "error" in CUSTOMS_LEGAL_CHECK_SPEC.handler(ctx, {})
    assert "error" in CUSTOMS_LEGAL_CHECK_SPEC.handler(ctx, {"hs_code": "38"})      # dưới 4 chữ số
    assert CUSTOMS_LEGAL_CHECK_SPEC.handler(_ctx(db, monkeypatch, False), {"hs_code": "3808"})["denied"] is True


# ── So sánh + thời điểm mua qua tool ────────────────────────────────────────
def test_tool_gia_so_sanh_hai_mat_hang_cung_don_vi(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_PRICE_STATS_SPEC
    _line(db, date(2026, 1, 5), price=3.0)
    _line(db, date(2026, 1, 6), name="MESOTRIONE 98% TC", price=9.0)
    db.commit()
    ctx = _ctx(db, monkeypatch, True)

    res = CUSTOMS_PRICE_STATS_SPEC.handler(ctx, {"keyword": "atrazine", "compare_keywords": ["mesotrione"]})
    assert [t["keyword"] for t in res["compare"]["terms"]] == ["atrazine", "mesotrione"]
    assert res["compare"]["unit"] == "KGM"
    assert res["compare"]["terms"][1]["series"][0]["wavg"] == 9.0
    #  Chỉ có mã HS thì không có «mặt hàng chính» để so — báo rõ, không đem mã HS đi khớp tên hàng.
    assert "error" in CUSTOMS_PRICE_STATS_SPEC.handler(ctx, {"hs_code": "380893", "compare_keywords": ["x"]})
    assert "compare" not in CUSTOMS_PRICE_STATS_SPEC.handler(ctx, {"keyword": "atrazine"})


def test_tool_thoi_diem_mua_co_phan_hien_tai_va_cau_khong_biet_ton_kho(db, monkeypatch):
    from app.modules.assistant.tools.customs_tool import CUSTOMS_BUY_TIMING_SPEC
    for _ in range(6):
        _line(db, date(2026, 5, 3), price=3.2)
    for _ in range(6):
        _line(db, date(2026, 6, 3), price=2.9)
    db.commit()
    res = CUSTOMS_BUY_TIMING_SPEC.handler(_ctx(db, monkeypatch, True), {"keyword": "atrazine"})

    assert res["now"]["available"] is True and res["now"]["latest_month"] == "06/2026"
    assert res["now"]["price_level"] == "thấp"
    assert "tồn kho" in res["not_known"]
