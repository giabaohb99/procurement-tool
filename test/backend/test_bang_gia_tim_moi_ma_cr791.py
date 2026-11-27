"""bao-CR-791 — ô tìm của Bảng giá VTBB tìm trên MỌI mã có trong sổ giá, kể cả mã đã mua nhưng chưa nằm trong định mức nào.

CHỈ kiểm phần vừa làm: không gõ gì thì danh sách vẫn theo phạm vi định mức; gõ mã / tên thì ra cả mã ngoài định mức (màn hình và
đường xuất Excel); ô chọn mã của màn Tác động (chế độ nhẹ) giữ nguyên phạm vi định mức.
"""
from app.core.packaging_price_codes import PriceSourceType
from app.modules.packaging_cost.price_list_service import build_price_list, build_price_list_page, search_scope
from so_gia_factory_cr784 import add_ledger, add_products, build_bom


def _world(db):
    """CPT0105 nằm trong định mức; CHT0230 đã mua hai lần (4.150 rồi 5.105 qua ĐMH) nhưng chưa có trong định mức nào."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("CHT0230", "Chai HDPE 550ml Gruratee", "Cái"))
    db.add(build_bom(fg_code="HH0417.1", fg_name="Sản phẩm HH0417.1", bottle_code="CPT0105", carton_qty=40,
                     created_by=1, updated_by=1))
    db.commit()
    add_ledger(db, "CPT0105", 1000, "2026-05-01")
    add_ledger(db, "CHT0230", 4150, "2026-03-30")
    add_ledger(db, "CHT0230", 5105, "2026-11-19", source_type=PriceSourceType.PO_LINE, doc_id=1260)


def test_search_scope_rule():
    assert search_scope("", "bom") == "bom" and search_scope("   ", "bom") == "bom"
    assert search_scope("CHT0230", "bom") == "all" and search_scope("", "all") == "all"


def test_without_search_the_list_stays_on_bom_codes(db):
    _world(db)
    rows, total = build_price_list_page(db, page=1, page_size=50)
    assert ([r["code"] for r in rows], total) == (["CPT0105"], 1)


def test_search_finds_purchased_code_outside_bom(db):
    _world(db)
    for term in ("cht0230", "gruratee"):
        rows, total = build_price_list_page(db, page=1, page_size=50, q=term)
        assert total == 1
        assert [(r["code"], r["old"], r["new"], r["usage"], r["purchase_count"]) for r in rows] == [("CHT0230", 4150, 5105, 0, 2)]
    assert [r["code"] for r in build_price_list(db, q="CHT0230")] == ["CHT0230"]          # đường xuất Excel


def test_code_picker_keeps_bom_scope(db):
    _world(db)
    assert build_price_list(db, q="CHT0230", new_only=True) == []
    assert [r["code"] for r in build_price_list(db, q="CPT", new_only=True)] == ["CPT0105"]
