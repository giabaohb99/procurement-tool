"""duoc-CR-784 — ba công cụ Giá bao bì cho Trợ lý / bot / cổng MCP: `packaging_price_impact`, `packaging_price_lookup`,
`packaging_product_cost`. Kiểm: thiếu `packaging_cost.read` thì từ chối; phạm vi pháp nhân trên sổ giá như màn web; số khớp
dịch vụ của màn (công thức chi phí, giá cũ / mới, n lần mua); tham số lạ không vỡ; số truy vấn cố định; khai đủ chỗ ở
cổng MCP / bộ lọc công cụ / nhãn ý định."""
import pytest

from app.modules.assistant import tool_router as tr
from app.modules.assistant import tools as T
from app.modules.assistant.tools.base import ToolContext
from app.modules.packaging_cost.model import PackagingBom
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom

TOOLS = ("packaging_price_impact", "packaging_price_lookup", "packaging_product_cost")


def _bom(db, fg="HH0417.1", **over):
    base = dict(fg_code=fg, fg_name=f"Sản phẩm {fg}", bottle_code="CPT0105", cap_code="NAP0085", label_code="NHG0001",
                carton_label_code="NDT0001", carton_code="THU0001", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    db.add(build_bom(**base))
    db.commit()


@pytest.fixture
def world(db, seed):
    """Chai 1000 → 1100 · nắp 200 · nhãn 300 · nhãn thùng 400 · thùng 8000; một sản phẩm quy cách 40 (như màn web)."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("NDT0001", "Nhãn thùng", "Cái"), ("THU0001", "Thùng", "Cái"))
    db.add(Supplier(code="NCC01", name="Công ty Bao Bì Một - VTBB"))
    db.commit()
    add_ledger(db, "CPT0105", 1000, "2026-01-01", company_id=seed.company_id)
    add_ledger(db, "CPT0105", 1100, "2026-06-01", company_id=seed.company_id)
    for code, price in (("NAP0085", 200), ("NHG0001", 300), ("NDT0001", 400), ("THU0001", 8000)):
        add_ledger(db, code, price, "2026-02-01", company_id=seed.company_id)
    _bom(db)


@pytest.fixture
def ctx(db, seed, cap_quyen, world):
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    return ToolContext(db=db, user=db.get(User, seed.u_req_id))


def _run(ctx, name, args):
    return T.run_tool(ctx.db, ctx.user, name, args)


def test_thieu_quyen_ca_ba_cong_cu_bi_tu_choi(db, seed, world):
    user = db.get(User, seed.u_req_id)
    for name, args in zip(TOOLS, ({"codes": ["CPT0105"]}, {"codes": ["CPT0105"]}, {"fg_codes": ["HH0417.1"]})):
        out = T.run_tool(db, user, name, args)
        assert out.get("denied") is True and "giá bao bì" in out["reason"], name


def test_tac_dong_gia_dung_cong_thuc_man_web(ctx):
    out = _run(ctx, "packaging_price_impact", {"codes": ["CPT0105"], "assumed_prices": [{"code": "CPT0105", "price": 1500}]})
    sel = out["selected"][0]
    assert (sel["old_price"], sel["new_price"], sel["assumed_price"], sel["applied_price"]) == (1000, 1100, 1500, 1500)
    assert (sel["price_diff"], sel["pct_change"], sel["products_using"]) == (500, 50.0, 1)
    assert out["kpis"]["affected_products"] == 1 and out["kpis"]["increased"] == 1 and out["kpis"]["decreased"] == 0
    row = out["items"][0]
    assert (row["cost_old_bottle"], row["cost_applied_bottle"], row["diff_bottle"]) == (1710, 2210, 500)  # 1000+200+300+8400/40
    assert (row["diff_carton"], row["trend_label"]) == (20000, "Tăng")
    assert row["selected_parts"] == [{"role": 1, "role_label": "Chai", "code": "CPT0105", "name": "Chai 450ml",
                                      "old_price": 1000, "new_price": 1100, "applied_price": 1500}]
    assert out["currency"] == "VND" and "trước VAT" in out["price_basis"] and out["url"].startswith("/procurement/")
    assert (out["total"], out["has_more"]) == (1, False)
    #  mã chỉ có giá giả định (không truyền codes) vẫn tính là mã đã chọn; dạng {mã: giá} cũng nhận
    only = _run(ctx, "packaging_price_impact", {"assumed_prices": {"CPT0105": 900}})
    assert only["items"][0]["diff_bottle"] == -100 and only["kpis"]["decreased"] == 1


def test_tra_gia_vtbb_lan_mua_gan_nhat_va_bao_gia(ctx, db):
    out = _run(ctx, "packaging_price_lookup", {"codes": ["CPT0105"]})
    it = out["items"][0]
    assert (it["old_price"], it["new_price"], it["new_price_source"], it["price_diff"]) == (1000, 1100, "Lần mua gần nhất", 100)
    assert it["last_purchase"]["date"] == "2026-06-01" and it["last_purchase"]["price"] == 1100
    assert it["last_purchase"]["supplier"] == "Công ty Bao Bì Một"            # bỏ đuôi " - VTBB" như màn Giá mua gần nhất
    assert it["prev_purchase"]["price"] == 1000 and it["purchase_count"] == 2 and it["products_using"] == 1
    assert [p["price"] for p in it["recent_purchases"]] == [1100, 1000] and it["recent_purchases"][0]["qty"] == 100
    assert (it["min_price"], it["max_price"]) == (1000, 1100) and "codes=CPT0105" in it["history_url"]
    one = _run(ctx, "packaging_price_lookup", {"codes": "CPT0105", "purchases": 1})["items"][0]
    assert len(one["recent_purchases"]) == 1
    add_quote(db, "CPT0105", 1250, "2026-12-01", supplier="NCC01")
    quoted = _run(ctx, "packaging_price_lookup", {"codes": ["CPT0105"]})["items"][0]
    assert (quoted["old_price"], quoted["new_price"], quoted["new_price_source"]) == (1100, 1250, "Báo giá")
    assert quoted["quote"]["valid_from"] == "2026-12-01"


def test_tra_gia_bang_chu_tim_va_ma_khong_co(ctx):
    found = _run(ctx, "packaging_price_lookup", {"q": "450ml"})
    assert [i["code"] for i in found["items"]] == ["CPT0105"]
    none = _run(ctx, "packaging_price_lookup", {"q": "khongcomanao"})
    assert none["items"] == [] and "Không có mã" in none["note"]
    ghost = _run(ctx, "packaging_price_lookup", {"codes": ["ZZ0000"]})
    assert ghost["no_data_codes"] == ["ZZ0000"] and ghost["items"][0]["new_price"] is None


def test_chi_phi_bao_bi_theo_san_pham(ctx, db):
    out = _run(ctx, "packaging_product_cost", {"fg_codes": ["HH0417.1", "HH9999"]})
    row = out["items"][0]
    assert (row["cost_old_bottle"], row["cost_new_bottle"], row["diff_bottle"]) == (1710, 1810, 100)
    assert (row["cost_old_carton"], row["cost_new_carton"], row["trend_label"]) == (68400, 72400, "Tăng")
    assert [p["role_label"] for p in row["parts"]] == ["Chai", "Nắp", "Nhãn", "Nhãn thùng", "Thùng"]
    assert out["no_bom_codes"] == ["HH9999"] and "fg=HH0417.1" in row["history_url"]
    _bom(db, fg="HH0500", bottle_code="CPT0999")                              # chai chưa có giá → missing
    up = _run(ctx, "packaging_product_cost", {"trend": "up"})
    assert [r["fg_code"] for r in up["items"]] == ["HH0417.1"] and up["counts"]["missing"] == 1
    assert _run(ctx, "packaging_product_cost", {"trend": "missing"})["items"][0]["warnings"] == ["Thiếu giá chai"]


def test_pham_vi_phap_nhan_ca_ba_cong_cu(db, seed, cap_quyen, world):
    """Giá của pháp nhân khác (mới nhất, 5000) không lọt vào bất kỳ công cụ nào khi người hỏi chỉ có phạm vi công ty."""
    add_ledger(db, "CPT0105", 5000, "2026-09-01", company_id=seed.company_id + 99)
    add_products(db, ("CPT0200", "Chai khác", "Cái"))
    add_ledger(db, "CPT0200", 777, "2026-09-01", company_id=seed.company_id + 99)
    cap_quyen(seed.u_req_id, "packaging_cost", scope="company", read=True)
    ctx = ToolContext(db=db, user=db.get(User, seed.u_req_id))
    impact = _run(ctx, "packaging_price_impact", {"codes": ["CPT0105"]})
    assert impact["selected"][0]["new_price"] == 1100 and impact["selected"][0]["max_price"] == 1100
    look = _run(ctx, "packaging_price_lookup", {"codes": ["CPT0105", "CPT0200"]})
    mine, other = look["items"]
    assert mine["new_price"] == 1100 and 5000 not in [p["price"] for p in mine["recent_purchases"]]
    #  mã chỉ có giá ở pháp nhân khác: cùng hình với mã chưa có giá nào (không lộ 777)
    assert (other["new_price"], other["last_purchase"], other["recent_purchases"], other["purchase_count"]) == (None, None, [], 0)
    assert "777" not in str(look)
    cost = _run(ctx, "packaging_product_cost", {"fg_codes": ["HH0417.1"]})
    assert cost["items"][0]["cost_new_bottle"] == 1810
    assert _run(ctx, "packaging_product_cost", {})["items"][0]["cost_new_bottle"] == 1810


@pytest.mark.parametrize("name,args,hint", [
    ("packaging_price_impact", {}, "Thiếu mã"),
    ("packaging_price_impact", {"codes": ["X" * 51]}, "tối đa 50"),
    ("packaging_price_impact", {"codes": [f"C{i}" for i in range(51)]}, "Tối đa 50"),
    ("packaging_price_impact", {"codes": ["CPT0105"], "assumed_prices": [{"code": "CPT0105", "price": -1}]}, ">= 0"),
    ("packaging_price_impact", {"codes": ["CPT0105"], "assumed_prices": [{"code": "CPT0105", "price": "abc"}]}, "không phải số"),
    ("packaging_price_impact", {"codes": {"a": 1}}, "danh sách"),
    ("packaging_price_lookup", {}, "Cần mã"),
    ("packaging_price_lookup", {"codes": [f"C{i}" for i in range(21)]}, "Tối đa 20"),
    ("packaging_product_cost", {"trend": "lung tung"}, "trend chỉ nhận"),
    ("packaging_product_cost", {"fg_codes": ["H" * 60]}, "Mã hàng hóa"),
])
def test_tham_so_sai_tra_loi_ro_khong_vo(ctx, name, args, hint):
    out = _run(ctx, name, args)
    assert hint in out.get("error", ""), out


def test_tham_so_la_van_chay(ctx):
    assert _run(ctx, "packaging_price_impact", {"codes": ["CPT0105"], "top_n": "abc", "sort_dir": "ngang"})["page_size"] == 20
    long_q = _run(ctx, "packaging_price_lookup", {"q": "chai " * 2000, "purchases": 999})   # cắt còn 100 ký tự, n kẹp 10
    assert "error" not in long_q and [i["code"] for i in long_q["items"]] == ["CPT0105"]
    assert _run(ctx, "packaging_product_cost", {"limit": 10 ** 9, "page": -5})["page_size"] == 50


def test_so_truy_van_co_dinh_khong_theo_so_ma(ctx):
    _run(ctx, "packaging_price_lookup", {"codes": ["CPT0105"]})          # nạp sẵn hồ sơ quyền (bộ đệm 60 giây)
    _, one = count_queries(ctx.db, lambda: _run(ctx, "packaging_price_lookup", {"codes": ["CPT0105"]}))
    _, many = count_queries(ctx.db, lambda: _run(ctx, "packaging_price_lookup",
                                                 {"codes": ["CPT0105", "NAP0085", "NHG0001", "NDT0001", "THU0001"]}))
    assert len(one) == len(many)


@pytest.mark.parametrize("q,tool", [
    ("chai CPT0075 lên 2.600 thì sản phẩm nào tăng chi phí bao bì bao nhiêu", "packaging_price_impact"),
    ("giá mua gần nhất của nhãn NHG0713", "packaging_price_lookup"),
    ("5 lần mua gần nhất của CPT0075", "packaging_price_lookup"),
    ("chi phí bao bì của HH0417.1 là bao nhiêu", "packaging_product_cost"),
    ("tác động giá nắp NAP0085", "packaging_price_impact"),
])
def test_bo_loc_cong_cu_nap_nhom_gia_bao_bi(q, tool):
    picked = tr.select(q)
    assert picked is not None and tool in picked, (q, sorted(picked or []))


def test_cau_nhan_hang_khong_keo_nhom_gia_bao_bi():
    picked = tr.select("PO00045 đã nhận hàng chưa") or set()
    assert not set(TOOLS) & picked


def test_cong_mcp_chi_doc_nhom_rieng_tat_mac_dinh_va_nhan_y_dinh():
    from app.modules.agent_hub import intent_ledger as il
    from app.modules.agent_hub import mcp, mcp_settings

    for name in TOOLS:
        assert not mcp.is_write_tool(name) and name in mcp.ROW_BUDGET_TOOLS and name in mcp.STRUCTURED_TOOLS
        group = mcp_settings.GROUP_OF[name]
        assert group.key == "packaging" and group.default_on is False      # giá vốn: quản trị chủ động bật ở G7
        assert il.TOOL_SUB[name] == il.Sub.LOOKUP_PRODUCT

