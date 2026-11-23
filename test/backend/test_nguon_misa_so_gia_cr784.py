"""duoc-CR-784 — nguồn giá TẠM từ sổ chi tiết mua hàng Misa (`PriceSourceType.MISA = 3`): nạp idempotent, mốc cắt chống đếm
trùng, gỡ (`purge`) trả hành vi cũ, tên nhà cung cấp theo dòng sổ, số truy vấn cố định không đổi."""
import json
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func
from sqlalchemy.dialects import mysql

from app.core.packaging_price_codes import PRICE_SOURCE_TYPE_LABELS, PriceSourceType
from app.modules.assistant.tools.packaging_cost_format import purchase_point
from app.modules.packaging_cost.history_service import build_history
from app.modules.packaging_cost.last_prices_service import build_last_prices
from app.modules.product_price.latest_priced_query import latest_priced_by_code
from app.modules.product_price.misa_cutoff import get_misa_cutoff, set_misa_cutoff
from app.modules.product_price.misa_ledger_import import (MisaSourceError, build_misa_rows, import_misa_rows,
                                                          load_misa_source, purge_misa_rows)
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.price_state_service import get_price_states
from app.modules.setting.model import Setting
from app.modules.supplier.model import Supplier
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products

MISA = int(PriceSourceType.MISA)
SRC = {"vtbb": {"NAP0056": ["Nắp 56", "Nắp", "Cái"], "CPT0075": ["Chai 75", "Chai", "Cái"]},
       "mua": [[1, "2025-09-20", "CÔNG TY A - VTBB", "NAP0056", 1000, 623, "NCC0019", "KHO1", None],
               [2, "2025-11-07", "CÔNG TY B - VTBB", "NAP0056", 500, 700, "NCC116", "KHO1", None],
               [3, "2026-02-01", "CÔNG TY B - VTBB", "NAP0056", 100, None, "NCC116", "KHO1", None],
               [4, "2026-06-30", "CÔNG TY A", "CPT0075", 10, 4000.5, "NCC0019", "KHO2", None]]}


def _rows(data=None, company=1):
    return build_misa_rows(data or SRC, company)


def _import(db, data=None):
    rows, parsed = _rows(data)
    stats = import_misa_rows(db, rows)
    db.commit()
    return stats, parsed


def _states(db, codes, **kw):
    return get_price_states(db, set(codes), also=set(codes), **kw)


# ---------------------------------------------------------------------------------------------------------- nạp tệp
def test_nhan_nguon_misa_co_trong_bo_ma_va_nhan_tieng_viet():
    assert int(PriceSourceType.MISA) == 3 and PRICE_SOURCE_TYPE_LABELS[PriceSourceType.MISA] == "Sổ Misa"


def test_doc_html_va_json_cho_cung_du_lieu(tmp_path):
    payload = json.dumps(SRC, ensure_ascii=False)
    html = tmp_path / "bao-cao.html"
    html.write_text(f"<html><script>var a=1;</script><script>\nwindow.VTBB_DEMO = {payload};\nvar x=2;</script></html>", "utf-8")
    js = tmp_path / "bao-cao.json"
    js.write_text(payload, "utf-8")
    assert load_misa_source(html) == load_misa_source(js) == SRC


@pytest.mark.parametrize("content,suffix", [("<html>không có dữ liệu</html>", ".html"), ("{hỏng", ".json"),
                                            ('{"vtbb": {}}', ".json")])
def test_tep_sai_cau_truc_bao_loi_tieng_viet(tmp_path, content, suffix):
    path = tmp_path / f"x{suffix}"
    path.write_text(content, "utf-8")
    with pytest.raises(MisaSourceError):
        load_misa_source(path)
    with pytest.raises(MisaSourceError):
        load_misa_source(tmp_path / "khong-co.html")


def test_dung_dong_so_gia_tu_dong_misa():
    rows, stats = _rows(company=7)
    assert [r["source_id"] for r in rows] == [1, 2, 3, 4] and {r["source_type"] for r in rows} == {MISA}
    first = rows[0]
    assert first["supplier_name"] == "CÔNG TY A" and first["supplier_code"] == "NCC0019"       # bỏ đuôi " - VTBB"
    assert (first["unit"], first["company_id"], first["doc_id"], first["vat"]) == ("Cái", 7, 0, Decimal("0"))
    assert rows[2]["price"] == 0 and stats["zero_price"] == 1                                  # None -> 0, vẫn nạp để đếm lần mua
    assert rows[3]["price"] == Decimal("4000.5") and rows[3]["supplier_name"] == "CÔNG TY A"
    assert stats["max_date"] == date(2026, 6, 30) and stats["min_date"] == date(2025, 9, 20)


def test_dong_hong_bi_bo_va_dem_khong_lam_hong_ca_lo():
    data = {"vtbb": {}, "mua": [[1, "2026-01-01", "A", "X1", 1, 5, "N1", "K", None], [2, "không-phải-ngày", "A", "X1", 1, 5, "N", "K", None],
                                [3, "2026-01-01", "A", "", 1, 5, "N", "K", None], [4, "2026-01-01", "A", "X1", "abc", 5, "N", "K", None],
                                "rác", [1, "2026-01-02", "A", "X1", 1, 6, "N", "K", None], [5, "2026-01-01", "A", "X1", 1, -3, "N", "K", None]]}
    rows, stats = _rows(data)
    assert [r["source_id"] for r in rows] == [1, 5] and rows[1]["price"] == 0                  # giá âm coi như chưa có giá
    assert stats["skipped_bad_row"] == 4 and stats["skipped_duplicate_id"] == 1


# ---------------------------------------------------------------------------------------------------------- idempotent
def test_nap_lai_nhieu_lan_khong_nhan_doi_va_dat_moc(db):
    first, _ = _import(db)
    assert first == {"inserted": 4, "updated": 0, "unchanged": 0, "deleted_stale": 0, "cutoff": date(2026, 6, 30)}
    again, _ = _import(db)
    assert again["inserted"] == again["updated"] == 0 and again["unchanged"] == 4
    assert db.query(L).filter(L.source_type == MISA).count() == 4
    assert get_misa_cutoff(db) == date(2026, 6, 30)
    assert db.query(Setting).filter(Setting.skey == "misa_price_cutoff").count() == 1


def test_tep_doi_thi_cap_nhat_va_xoa_dong_khong_con(db):
    _import(db)
    changed = json.loads(json.dumps(SRC))
    changed["mua"][1][5] = 710                         # đổi giá dòng 2
    del changed["mua"][3]                              # bỏ dòng 4 (mốc lùi về 2026-02-01)
    stats, _ = _import(db, changed)
    assert (stats["updated"], stats["deleted_stale"], stats["unchanged"]) == (1, 1, 2) and stats["cutoff"] == date(2026, 2, 1)
    assert float(db.query(L.price).filter(L.source_type == MISA, L.source_id == 2).scalar()) == 710
    assert get_misa_cutoff(db) == date(2026, 2, 1)


def test_thu_tu_id_so_gia_theo_id_misa(db):
    _import(db)
    ids = [i for (i,) in db.query(L.id).filter(L.source_type == MISA).order_by(L.source_id).all()]
    assert ids == sorted(ids)


# ---------------------------------------------------------------------------------------------------------- mốc cắt
@pytest.fixture
def mixed(db):
    """Mã A: Misa 100 (2026-01-10), 120 (2026-05-01); lịch sử cũ TRƯỚC mốc 999 (2026-03-01, phải bị bỏ); ĐMH SAU mốc 150 (2026-07-15)."""
    add_products(db, ("A", "Chai A", "Cái"))
    data = {"vtbb": {"A": ["Chai A", "Chai", "Cái"]},
            "mua": [[1, "2026-01-10", "NCC X - VTBB", "A", 10, 100, "MX", "K", None],
                    [2, "2026-05-01", "NCC X - VTBB", "A", 20, 120, "MX", "K", None],
                    [3, "2026-06-30", "NCC Y", "B", 5, 50, "MY", "K", None]]}
    legacy = add_ledger(db, "A", 999, "2026-03-01", source_type=PriceSourceType.PURCHASE_HISTORY, supplier="NCC01")
    erp = add_ledger(db, "A", 150, "2026-07-15", source_type=PriceSourceType.PO_LINE, supplier="NCC01")
    return data, legacy, erp


def test_chua_co_moc_thi_hanh_vi_nhu_cu(db, mixed):
    _, _, _ = mixed
    st = _states(db, ["A"])["A"]
    assert (st.new, st.old, st.purchase_count) == (150, 999, 2)
    assert db.query(Setting).filter(Setting.skey == "misa_price_cutoff").count() == 0


def test_moc_cat_bo_lich_su_truoc_moc_va_giu_dmh_sau_moc(db, mixed):
    data, legacy, erp = mixed
    _import(db, data)
    st = _states(db, ["A"])["A"]
    assert (st.p1.price, st.p1.source_type, st.p2.price, st.p2.source_type) == (150, 2, 120, MISA)
    assert (st.new, st.old, st.purchase_count, st.min, st.max) == (150, 120, 3, 100, 150)       # 999 trước mốc: không vào số nào
    assert st.last_date == date(2026, 7, 15)
    only_misa = _states(db, ["B"])["B"]
    assert (only_misa.new, only_misa.old, only_misa.p1.source_type) == (50, 50, MISA)


def test_lich_su_cu_sau_moc_bi_bo_con_dong_he_thong_sau_moc_duoc_tinh(db, mixed):
    data, _, _ = mixed
    _import(db, data)
    add_ledger(db, "A", 555, "2026-12-03", source_type=PriceSourceType.PURCHASE_HISTORY, doc_id=0)      # lịch sử cũ, ngày tương lai sai
    add_ledger(db, "A", 160, "2026-09-01", source_type=PriceSourceType.PURCHASE_HISTORY, doc_id=42)     # lịch sử hệ thống (có ĐMH)
    st = _states(db, ["A"])["A"]
    assert (st.new, st.old, st.p1.source_type, st.p1.doc_id) == (160, 150, 1, 42)
    assert st.purchase_count == 4 and st.max == 160 and st.last_date == date(2026, 9, 1)             # 100, 120, 150, 160 (không có 555 / 999)
    hist = build_history(db, mode="code", codes=["A"], page=1, page_size=50)
    assert [i["price"] for i in hist["items"]] == [160, 150, 120, 100]
    last = next(r for r in build_last_prices(db, n=5, scope="all")["rows"] if r["code"] == "A")
    assert [p["price"] for p in last["purchases"]] == [160, 150, 120, 100]
    purge_misa_rows(db)
    db.commit()
    assert _states(db, ["A"])["A"].purchase_count == 4                                               # gỡ mốc: lịch sử cũ trở lại


def test_dong_misa_sau_moc_bi_loai_dong_nguon_khac_dung_moc_duoc_tinh(db, mixed):
    data, _, _ = mixed
    _import(db, data)
    add_ledger(db, "A", 777, "2026-08-01", source_type=PriceSourceType.MISA, source_id=500, supplier="MX")   # Misa nằm SAU mốc
    add_ledger(db, "A", 888, "2026-06-30", source_type=PriceSourceType.PO_LINE, supplier="N")                 # nguồn khác đúng ngày mốc
    st = _states(db, ["A"])["A"]
    assert (st.new, st.old, st.purchase_count) == (150, 120, 3)
    set_misa_cutoff(db, date(2026, 8, 1))                                                                      # nới mốc
    db.commit()
    st = _states(db, ["A"])["A"]
    assert (st.new, st.old) == (777, 120) and st.purchase_count == 3                                           # 150 (07-15) bị loại vì <= mốc


def test_purge_tra_hanh_vi_cu_va_xoa_moc(db, mixed):
    data, _, _ = mixed
    before = _states(db, ["A"])["A"]
    _import(db, data)
    assert _states(db, ["A"])["A"].new == 150
    assert purge_misa_rows(db) == {"deleted": 3}
    db.commit()
    after = _states(db, ["A"])["A"]
    assert (after.new, after.old, after.purchase_count, after.min, after.max) == \
        (before.new, before.old, before.purchase_count, before.min, before.max)
    assert get_misa_cutoff(db) is None and db.query(L).filter(L.source_type == MISA).count() == 0


def test_moc_ap_cho_ma_tran_gia_gan_nhat_va_lich_su(db, mixed):
    data, _, _ = mixed
    _import(db, data)
    rows = build_last_prices(db, n=5, scope="all")["rows"]
    a = next(r for r in rows if r["code"] == "A")
    assert [p["price"] for p in a["purchases"]] == [150, 120, 100] and a["purchase_count"] == 3
    hist = build_history(db, mode="code", codes=["A"], page=1, page_size=50)
    assert [i["price"] for i in hist["items"]] == [150, 120, 100] and hist["total"] == 3 == hist["stats"]["purchase_count"]
    assert hist["stats"]["first_date"] == "2026-01-10" and [p["price"] for p in hist["series"]] == [100, 120, 150]


def test_moc_ap_trong_cau_lateral_cua_mysql(db):
    captured: list[str] = []

    class Spy:
        def get_bind(self):
            return db.get_bind()

        def execute(self, stmt):
            captured.append(str(stmt.compile(dialect=mysql.dialect())))
            return []

    latest_priced_by_code(Spy(), 5, codes={"A"}, rank_conds=[L.price > 0], agg_cols=[func.count(L.id)], strategy="lateral")
    sql = captured[0].lower()
    assert "tab_setting" in sql and "misa_price_cutoff" not in sql          # khóa là tham số bind, không dán chữ vào SQL


# ---------------------------------------------------------------------------------------------------------- tên nhà cung cấp
def test_ten_ncc_theo_dong_so_cho_ma_khong_co_trong_tab_supplier(db, mixed):
    data, _, _ = mixed
    _import(db, data)
    st = _states(db, ["A"])["A"]
    assert st.p2.supplier_code == "MX" and st.p2.supplier_name == "NCC X"
    last = next(r for r in build_last_prices(db, n=5, scope="all")["rows"] if r["code"] == "A")
    assert [(p["supplier_code"], p["supplier"]) for p in last["purchases"]] == [("NCC01", "NCC01"), ("MX", "NCC X"), ("MX", "NCC X")]
    hist = build_history(db, mode="code", codes=["A"], page=1, page_size=50)
    assert [i["supplier"] for i in hist["items"]] == ["NCC01", "NCC X", "NCC X"]
    assert {o["code"]: o["name"] for o in hist["suppliers"]} == {"MX": "NCC X", "NCC01": "NCC01"}
    assert {s["code"] for s in build_last_prices(db, n=5, scope="all")["suppliers"]} == {"MX", "MY", "NCC01"}
    found = build_history(db, mode="code", codes=["A"], q="ncc x")                   # tìm chữ cũng thấy tên chép theo dòng
    assert found["total"] == 2
    by_name = build_history(db, mode="code", codes=["A"], sort_by="supplier", sort_dir="asc")
    assert [i["supplier"] for i in by_name["items"]] == ["NCC X", "NCC X", "NCC01"]


def test_ten_theo_dong_thang_ten_o_danh_muc_nha_cung_cap_khi_trung_ma(db, mixed):
    data, _, _ = mixed
    db.add(Supplier(code="MX", name="Tên khác trong danh mục"))
    db.commit()
    _import(db, data)
    hist = build_history(db, mode="code", codes=["A"], page=1, page_size=50)
    assert [i["supplier"] for i in hist["items"]][1:] == ["NCC X", "NCC X"]


def test_dinh_dang_mcp_dung_ten_theo_dong(db, mixed):
    data, _, _ = mixed
    _import(db, data)
    st = _states(db, ["A"])["A"]
    out = purchase_point(st.p2, {"MX": "Tên tra theo mã"})
    assert out["supplier"] == "NCC X" and out["source_label"] == "Sổ Misa"
    assert purchase_point(st.p1, {"NCC01": "Nhựa 01"})["supplier"] == "Nhựa 01"           # dòng không có tên theo dòng: tra theo mã


# ---------------------------------------------------------------------------------------------------------- kho
def test_nap_kho_tu_chi_so_7_cua_dong_misa(db):
    data = {"vtbb": {}, "mua": [[1, "2026-01-10", "NCC X", "A", 1, 5, "MX", "  KHO NCC HÀ LONG ", None],
                                [2, "2026-01-11", "NCC X", "A", 1, 5, "MX", "", None],
                                [3, "2026-01-12", "NCC X", "A", 1, 5, "MX", None, None],
                                [4, "2026-01-13", "NCC X", "A", 1, 5, "MX"],                       # dòng cũ không có cột kho
                                [5, "2026-01-14", "NCC X", "A", 1, 5, "MX", "K" * 300, None]]}
    rows, _ = _rows(data)
    assert [r["warehouse_name"] for r in rows] == ["KHO NCC HÀ LONG", None, None, None, "K" * 200]
    _import(db, data)
    assert {r.source_id: r.warehouse_name for r in db.query(L).filter(L.source_type == MISA)}[1] == "KHO NCC HÀ LONG"


def test_kho_theo_dong_tra_ve_tim_duoc_xep_duoc_va_nap_lai_cap_nhat(db, mixed):
    data, _, _ = mixed
    data["mua"][0][7], data["mua"][1][7] = "KHO NCC HÀ LONG", "Kho DEGO Cần Thơ"
    _import(db, data)
    hist = build_history(db, mode="code", codes=["A"], page=1, page_size=50)
    assert {i["date"]: i["warehouse"] for i in hist["items"]} == {
        "2026-07-15": "", "2026-05-01": "Kho DEGO Cần Thơ", "2026-01-10": "KHO NCC HÀ LONG"}
    assert build_history(db, mode="code", codes=["A"], q="HÀ LONG")["total"] == 1
    asc = build_history(db, mode="code", codes=["A"], sort_by="warehouse", sort_dir="asc")
    assert [i["warehouse"] for i in asc["items"]] == ["KHO NCC HÀ LONG", "Kho DEGO Cần Thơ", ""]
    data["mua"][0][7] = "Kho khác"                                   # tệp đổi kho -> nạp lại cập nhật đúng dòng
    stats, _ = _import(db, data)
    assert stats["updated"] == 1 and stats["unchanged"] == 2
    assert build_history(db, mode="code", codes=["A"], q="khác")["total"] == 1


# ---------------------------------------------------------------------------------------------------------- số truy vấn
def test_so_truy_van_khong_doi_khi_co_moc(db, mixed):
    data, _, _ = mixed
    add_products(db, ("B", "Chai B", "Cái"))
    probes = {
        "states": lambda: get_price_states(db, {"A", "B"}, also={"A", "B"}),
        "states_new_only": lambda: get_price_states(db, {"A", "B"}, new_only=True),
        "last_prices": lambda: build_last_prices(db, n=5, scope="all"),
        "history": lambda: build_history(db, mode="code", codes=["A"], page=1, page_size=50),
    }
    baseline = {k: len(count_queries(db, fn)[1]) for k, fn in probes.items()}
    _import(db, data)
    assert get_misa_cutoff(db) is not None
    with_cutoff = {k: len(count_queries(db, fn)[1]) for k, fn in probes.items()}
    assert with_cutoff == baseline and baseline["states"] <= 5
