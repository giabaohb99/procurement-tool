"""ai-CR-189 — đợt 3 xóa mềm (đại ca 13/10): danh mục đang được tham chiếu thì CHẶN xóa, chỉ cho ngưng dùng; chưa ai dùng
thì xóa được. Sổ đăng ký chung `core/reference_guard` + `make_crud_router` tự gọi theo entity."""
import pytest
from fastapi import HTTPException

from app.core import reference_guard as rg


def test_chua_dang_ky_thi_khong_chan_va_dang_ky_roi_thi_dem_dung(db, seed):
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.supplier.model import Supplier

    sup = db.get(Supplier, seed.sup_id)
    rg.ensure_deletable(db, "khong_ton_tai", sup)                 # chưa đăng ký: hành vi cũ, không chặn
    rg._REGISTRY.pop("thu_nghiem", None)
    rg.register("thu_nghiem", "Nhà cung cấp thử", [rg.Reference(PurchaseOrder, "supplier_code", "đơn mua hàng", key_attr="code")])
    assert rg.count_references(db, "thu_nghiem", sup) == []
    db.add(PurchaseOrder(code="POX1", supplier_code=sup.code, status="draft"))
    db.add(PurchaseOrder(code="POX2", supplier_code=sup.code, status="approved"))
    db.commit()
    assert rg.count_references(db, "thu_nghiem", sup) == [("đơn mua hàng", 2)]
    with pytest.raises(HTTPException) as e:
        rg.ensure_deletable(db, "thu_nghiem", sup)
    assert e.value.status_code == 400 and "2 chỗ" in e.value.detail and "ngưng dùng" in e.value.detail \
        and "Nhà cung cấp thử" in e.value.detail and "\"" in e.value.detail
    #  Điều kiện thêm: chỉ đếm đơn còn hiệu lực.
    rg._REGISTRY["thu_nghiem"] = [rg.Reference(PurchaseOrder, "supplier_code", "đơn mua hàng", key_attr="code",
                                               extra=lambda m: [m.status != "draft"])]
    assert rg.count_references(db, "thu_nghiem", sup) == [("đơn mua hàng", 1)]
    rg._REGISTRY.pop("thu_nghiem", None)


def test_crud_chung_tu_goi_chot(db, seed, monkeypatch):
    """`make_crud_router.delete_item` gọi `ensure_deletable` theo entity — danh mục CRUD chỉ cần đăng ký."""
    import inspect

    from app.core import crud

    src = inspect.getsource(crud)
    assert src.count("reference_guard.ensure_deletable(db, entity,") == 2       # nút xóa + dòng CSV «xóa»
