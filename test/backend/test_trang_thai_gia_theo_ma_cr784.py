"""duoc-CR-784 phase 04 — `get_price_states`: luật giá cũ / mới, báo giá (kể cả tương lai), dòng giá 0, min / max theo ngày,
phạm vi pháp nhân, và SỐ TRUY VẤN cố định (4; 5 khi chia hai tầng số gộp) bất kể số mã."""
from datetime import date
from decimal import Decimal

from app.core.packaging_price_codes import PriceSourceType
from app.modules.product_price.price_state_service import derive_old_new, get_price_states
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_limit, add_products, add_quote

D = Decimal


def _states(db, codes, **kw):
    return get_price_states(db, set(codes) if codes is not None else None, **kw)


def test_khong_co_bao_gia_moi_la_lan_mua_gan_nhat_cu_la_lan_truoc(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_ledger(db, "A", 120, "2026-06-01")
    add_ledger(db, "A", 90, "2026-03-01")
    st = _states(db, {"A"})["A"]
    assert (st.new, st.old) == (D(120), D(90))
    assert (st.p1.date, st.p2.date) == (date(2026, 6, 1), date(2026, 3, 1))


def test_chi_mot_lan_mua_thi_cu_bang_moi(db):
    add_ledger(db, "A", 100, "2026-01-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new, st.p2) == (D(100), D(100), None)


def test_co_bao_gia_moi_la_bao_gia_cu_la_lan_mua_gan_nhat(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_ledger(db, "A", 110, "2026-06-01")
    add_quote(db, "A", 150, "2026-07-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new) == (D(110), D(150))
    assert st.quote.valid_from == date(2026, 7, 1)


def test_bao_gia_hieu_luc_o_tuong_lai_tinh_ngay_la_gia_moi_q2(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_quote(db, "A", 200, "2099-01-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new) == (D(100), D(200))


def test_nhieu_bao_gia_lay_cai_valid_from_muon_nhat_hoa_ngay_lay_id_lon(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_quote(db, "A", 120, "2026-05-01", supplier="NCC01")
    add_quote(db, "A", 130, "2026-05-01", supplier="NCC02")     # cùng ngày, khác NCC (cùng NCC bị khóa duy nhất chặn) → id lớn hơn
    add_quote(db, "A", 999, "2026-04-01")
    assert _states(db, {"A"})["A"].new == D(130)


def test_chi_co_bao_gia_khong_co_lan_mua_thi_cu_bang_moi(db):
    add_quote(db, "A", 77, "2026-05-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new, st.p1) == (D(77), D(77), None)


def test_dong_gia_0_bi_bo_khoi_cu_moi_nhung_van_dem_so_lan_mua(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_ledger(db, "A", 0, "2026-06-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new, st.purchase_count) == (D(100), D(100), 2)
    assert st.last_date == date(2026, 6, 1)


def test_chi_toan_gia_0_thi_chua_co_gia(db):
    add_ledger(db, "A", 0, "2026-01-01")
    st = _states(db, {"A"})["A"]
    assert (st.old, st.new, st.purchase_count) == (None, None, 1)


def test_cung_ngay_id_lon_hon_la_gan_hon(db):
    add_ledger(db, "A", 100, "2026-05-01")
    add_ledger(db, "A", 105, "2026-05-01")
    st = _states(db, {"A"})["A"]
    assert (st.new, st.old) == (D(105), D(100))


def test_min_max_theo_khoang_ngay_chi_ap_cho_min_max_khong_ap_cho_cu_moi(db):
    add_ledger(db, "A", 50, "2025-01-01")
    add_ledger(db, "A", 100, "2026-03-01")
    add_ledger(db, "A", 200, "2026-09-01")
    st = _states(db, {"A"}, date_from=date(2026, 1, 1), date_to=date(2026, 6, 30))["A"]
    assert (st.min, st.max) == (D(100), D(100))
    assert (st.new, st.old) == (D(200), D(100))      # cũ / mới vẫn nhìn cả sổ
    whole = _states(db, {"A"})["A"]
    assert (whole.min, whole.max) == (D(50), D(200))


def test_nguong_va_ten_nhom_dvt_danh_muc_duoc_gan(db):
    add_products(db, ("A", "Chai A", "Cái"))
    add_limit(db, "A", floor=80, ceiling=300)
    add_ledger(db, "A", 100, "2026-01-01")
    st = _states(db, {"A"})["A"]
    assert (st.name, st.group, st.unit, st.floor, st.ceiling) == ("Chai A", "Chai", "Cái", D(80), D(300))


def test_also_giu_ma_chua_co_du_lieu_va_codes_none_lay_het(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_quote(db, "B", 5, "2026-01-01")
    got = _states(db, {"A"}, also={"Z"})
    assert set(got) == {"A", "Z"} and got["Z"].old is None
    assert set(_states(db, None)) == {"A", "B"}


def test_as_of_loai_dong_co_ngay_sau_moc(db):
    add_ledger(db, "A", 100, "2026-01-01")
    add_ledger(db, "A", 500, "2027-01-01")
    assert _states(db, {"A"})["A"].new == D(500)
    assert _states(db, {"A"}, as_of=date(2026, 6, 1))["A"].new == D(100)


def test_pham_vi_cong_ty_chi_tinh_tren_dong_so_nguoi_xem_duoc_thay(db):
    from sqlalchemy import true
    from app.modules.product_price.model import ProductPriceLedger as L
    add_ledger(db, "A", 100, "2026-01-01", company_id=1)
    add_ledger(db, "A", 900, "2026-06-01", company_id=2)
    st = _states(db, {"A"}, scope_cond=(L.company_id == 1))["A"]
    assert st.new == D(100) and st.purchase_count == 1
    assert _states(db, {"A"}, scope_cond=true())["A"].new == D(900)


def test_nguon_dong_sao_chep_vao_diem_gia(db):
    add_ledger(db, "A", 100, "2026-01-01", source_type=PriceSourceType.PO_LINE, doc_id=7, supplier="NCC9", unit="Kg")
    p = _states(db, {"A"})["A"].p1
    assert (p.source_type, p.doc_id, p.supplier_code, p.unit) == (2, 7, "NCC9", "Kg")


def test_so_truy_van_la_4_bat_ke_so_ma(db):
    add_products(db, *[(f"M{i}", f"Mã {i}", "Cái") for i in range(60)])
    for i in range(60):
        add_ledger(db, f"M{i}", 100 + i, "2026-01-01")
        add_ledger(db, f"M{i}", 110 + i, "2026-02-01")
        add_quote(db, f"M{i}", 120 + i, "2026-03-01")
    _, one = count_queries(db, lambda: _states(db, {"M1"}))
    _, many = count_queries(db, lambda: _states(db, {f"M{i}" for i in range(60)}))
    _, everything = count_queries(db, lambda: _states(db, None))
    assert len(one) == len(many) == len(everything) == 4      # sổ giá (một câu) · báo giá · ngưỡng · danh mục


def test_derive_old_new_thuan():
    from app.modules.product_price.price_state_service import PricePoint, QuotePoint
    p1, p2 = PricePoint(D(10), date(2026, 2, 1)), PricePoint(D(8), date(2026, 1, 1))
    assert derive_old_new(None, None, None) == (None, None)
    assert derive_old_new(p1, p2, None) == (D(8), D(10))
    assert derive_old_new(p1, None, QuotePoint(D(12), date(2026, 3, 1))) == (D(10), D(12))


# ── Chế độ nhẹ + hai tầng số gộp (hiệu năng khi sổ giá lớn) ─────────────────────────
def _world(db):
    add_products(db, ("A", "Chai A", "Cái"), ("B", "Nắp B", "Cái"), ("C", "Nhãn C", "Cái"))
    for code, rows in {"A": [(100, "2026-01-01"), (120, "2026-02-01"), (0, "2026-03-01")],
                       "B": [(50, "2026-01-05")], "C": [(10, "2026-01-01"), (30, "2026-04-01")]}.items():
        for price, on in rows:
            add_ledger(db, code, price, on)
    add_quote(db, "B", 70, "2026-06-01")


def test_new_only_cho_dung_gia_moi_khong_so_gop_va_it_truy_van_hon(db):
    _world(db)
    full = _states(db, {"A", "B", "C"})
    light = _states(db, {"A", "B", "C"}, new_only=True)
    assert {c: s.new for c, s in light.items()} == {c: s.new for c, s in full.items()} == {"A": D(120), "B": D(70), "C": D(30)}
    assert all(s.old is None and s.purchase_count == 0 and s.min is None and s.floor is None for s in light.values())
    assert light["A"].name == "Chai A" and light["B"].quote.price == D(70)       # tên + báo giá vẫn có
    _, full_sql = count_queries(db, lambda: _states(db, {"A", "B", "C"}))
    _, light_sql = count_queries(db, lambda: _states(db, {"A", "B", "C"}, new_only=True))
    assert len(light_sql) == len(full_sql) - 1                                    # bỏ truy vấn ngưỡng


def test_stats_codes_chi_ma_duoc_chon_co_so_gop_con_lai_van_dung_cu_moi(db):
    _world(db)
    full = _states(db, {"A", "B", "C"})
    tiered = _states(db, {"A", "B", "C"}, stats_codes={"A"})
    for code in "ABC":
        assert (tiered[code].old, tiered[code].new) == (full[code].old, full[code].new)
        assert (tiered[code].p1 == full[code].p1) and (tiered[code].p2 == full[code].p2)
    assert (tiered["A"].purchase_count, tiered["A"].min, tiered["A"].max) == (3, D(100), D(120))
    assert (tiered["C"].purchase_count, tiered["C"].min, tiered["C"].max) == (0, None, None)     # mã tầng nhẹ: không số gộp
    _, sqls = count_queries(db, lambda: _states(db, {"A", "B", "C"}, stats_codes={"A"}))
    assert len(sqls) == 5                                                                        # hai tầng sổ giá + báo giá + ngưỡng + danh mục


def test_stats_codes_rong_hoac_ngoai_tap_khong_vo_loi(db):
    _world(db)
    assert _states(db, {"A"}, stats_codes=set())["A"].purchase_count == 0
    assert _states(db, {"A"}, stats_codes={"ZZZ"})["A"].new == D(120)
    assert _states(db, {"A", "B"}, stats_codes={"A", "B"})["B"].purchase_count == 1
