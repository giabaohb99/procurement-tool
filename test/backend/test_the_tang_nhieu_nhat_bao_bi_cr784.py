"""duoc-CR-784 — thẻ "Tăng nhiều nhất /thùng" của màn Tác động giá: `kpis.max_increase_product` là sản phẩm tăng chi phí /thùng
nhiều nhất trên TOÀN BỘ tập bị ảnh hưởng (không theo bộ lọc / trang). Hòa → chênh /chai lớn hơn, rồi mã hàng hóa. Không sản phẩm
nào tăng → None (thẻ ghi "Không có sản phẩm tăng", không đưa số âm ra làm "tăng nhiều nhất")."""
from decimal import Decimal

import pytest

from app.modules.packaging_cost.impact_service import compute_impact
from app.modules.packaging_cost.model import PackagingBom
from so_gia_factory_cr784 import add_ledger, add_products, build_bom

D = Decimal
NO_PARTS = dict(cap_code="", label_code="", carton_label_code="", carton_code="")


def _bom(db, fg: str, qty: int, **over) -> None:
    base = dict(fg_name=f"Sản phẩm {fg}", bottle_code="CPT0105", cap_code="NAP0085", label_code="", carton_label_code="",
                carton_code="", carton_qty=qty, created_by=1, updated_by=1)
    base.update(over)
    db.add(build_bom(fg_code=fg, **base))
    db.commit()


@pytest.fixture
def world(db):
    """Chai 1000 → 1100; nắp 200 (không đổi giá)."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"))
    add_ledger(db, "CPT0105", 1000, "2026-01-01")
    add_ledger(db, "CPT0105", 1100, "2026-06-01")
    add_ledger(db, "NAP0085", 200, "2026-02-01")


def _top(db, codes, assumed=None):
    return compute_impact(db, codes, assumed or {})["kpis"]["max_increase_product"]


def test_chon_dung_san_pham_tang_nhieu_nhat_theo_thung(db, world):
    _bom(db, "HH01", 20, **NO_PARTS)
    _bom(db, "HH02", 40, **NO_PARTS)
    _bom(db, "HH03", 10, **NO_PARTS)
    out = compute_impact(db, ["CPT0105"], {})
    top = out["kpis"]["max_increase_product"]
    assert top == {"fg_code": "HH02", "fg_name": "Sản phẩm HH02", "diff_bottle": 100, "diff_carton": 4000, "carton_qty": 40}
    assert out["kpis"]["max_increase_carton"] == top["diff_carton"]      # khớp số lớn nhất đã có


def test_gia_gia_dinh_doi_san_pham_va_con_so(db, world):
    _bom(db, "HH01", 20, **NO_PARTS)
    _bom(db, "HH02", 40, **NO_PARTS)
    assert _top(db, ["CPT0105"], {"CPT0105": D(1500)})["diff_carton"] == 20000          # (1500 - 1000) x 40
    assert _top(db, ["CPT0105"], {"CPT0105": D(1500)})["diff_bottle"] == 500
    assert _top(db, ["CPT0105"])["diff_carton"] == 4000                                 # bỏ giả định → giá mới 1100


def test_hoa_theo_thung_thi_chenh_chai_lon_hon_thang_roi_toi_ma_hang_hoa(db, world):
    #  A: chai +100, 60 chai/thùng → 6000 /thùng. B: chai +100 và nắp +50 (giả định 250), 40 chai/thùng → 6000 /thùng.
    _bom(db, "HH01", 60, **NO_PARTS)
    _bom(db, "HH02", 40)
    top = _top(db, ["CPT0105", "NAP0085"], {"NAP0085": D(250)})
    assert (top["fg_code"], top["diff_bottle"], top["diff_carton"]) == ("HH02", 150, 6000)
    #  Hòa cả hai số → mã hàng hóa nhỏ hơn.
    _bom(db, "HH00", 40)
    assert _top(db, ["CPT0105", "NAP0085"], {"NAP0085": D(250)})["fg_code"] == "HH00"


def test_khong_san_pham_nao_tang_thi_none(db, world):
    _bom(db, "HH01", 40, **NO_PARTS)
    assert _top(db, ["CPT0105"], {"CPT0105": D(500)}) is None            # giả định thấp hơn giá cũ → giảm hết
    assert _top(db, ["CPT0105"], {"CPT0105": D(1000)}) is None           # bằng giá cũ nhưng mới 1100 bị đè → chênh 0, không tăng
    assert _top(db, ["KHONG_CO"]) is None                                 # mã không có trong định mức


def test_san_pham_khong_co_quy_cach_thung_khong_vao_thung_tang_nhieu_nhat(db, world):
    _bom(db, "HH01", 0, **NO_PARTS)                                       # có chênh /chai nhưng không có /thùng
    out = compute_impact(db, ["CPT0105"], {})
    assert out["kpis"]["increased"] == 1 and out["kpis"]["max_increase_product"] is None
    _bom(db, "HH02", 5, **NO_PARTS)
    assert _top(db, ["CPT0105"])["fg_code"] == "HH02"


def test_the_khong_doi_theo_bo_loc_va_trang(db, world):
    _bom(db, "HH01", 20, **NO_PARTS)
    _bom(db, "HH02", 40, **NO_PARTS)
    out = compute_impact(db, ["CPT0105"], {}, q="HH01", page=1, page_size=1)
    assert out["products_total"] == 1 and out["kpis"]["max_increase_product"]["fg_code"] == "HH02"
