"""Thời gian dự kiến có hàng trên YCMH mặc định lấy theo Ngày cần hàng của dòng.

Đây là GIÁ TRỊ KHỞI TẠO lúc TẠO dòng. Sau đó ngày này thuộc quyền NSTM: đổi giá trị đã có
vẫn phải kèm lý do (update_item_status), và lưu lại phiếu KHÔNG được điền đè.
"""
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ItemStatusIn, PRItemIn
from app.modules.purchase_request.service import _save_items, update_item_status


def _pr(db, code="PYC1"):
    pr = PurchaseRequest(code=code, status="draft", created_by=1)
    db.add(pr)
    db.commit()
    return pr


def _items(db, pr):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).order_by(
        PurchaseRequestItem.id).all()


def test_dong_moi_lay_theo_ngay_can_hang(db):
    pr = _pr(db)
    _save_items(db, pr.id, [PRItemIn(product_name="Hàng A", product_code="SP1", qty=10,
                                     required_date="2026-08-10")], user_id=1)
    assert _items(db, pr)[0].expected_date == "2026-08-10"


def test_khong_co_ngay_can_hang_thi_de_trong(db):
    pr = _pr(db)
    _save_items(db, pr.id, [PRItemIn(product_name="Hàng A", product_code="SP1", qty=10)], user_id=1)
    assert _items(db, pr)[0].expected_date == ""


def test_luu_lai_phieu_khong_ghi_de_ngay_nstm_da_sua(db):
    pr = _pr(db)
    _save_items(db, pr.id, [PRItemIn(product_name="Hàng A", product_code="SP1", qty=10,
                                     required_date="2026-08-10")], user_id=1)
    row = _items(db, pr)[0]
    update_item_status(db, pr.id, ItemStatusIn(items=[{"id": row.id, "expected_date": "2026-09-05",
                                                       "expected_date_reason": "NCC báo trễ"}]),
                       user_id=1, emp_code="", is_manager=True)
    # Lưu lại phiếu (đổi số lượng) — ngày dự kiến phải giữ nguyên, không tụt về Ngày cần hàng
    _save_items(db, pr.id, [PRItemIn(id=row.id, product_name="Hàng A", product_code="SP1", qty=20,
                                     required_date="2026-08-10")], user_id=1)
    assert _items(db, pr)[0].expected_date == "2026-09-05"


def test_doi_ngay_can_hang_khong_keo_ngay_du_kien_theo(db):
    """Ngày cần hàng đổi sau đó là việc của bộ phận yêu cầu — không được tự dời ngày dự kiến."""
    pr = _pr(db)
    _save_items(db, pr.id, [PRItemIn(product_name="Hàng A", product_code="SP1", qty=10,
                                     required_date="2026-08-10")], user_id=1)
    row = _items(db, pr)[0]
    _save_items(db, pr.id, [PRItemIn(id=row.id, product_name="Hàng A", product_code="SP1", qty=10,
                                     required_date="2026-08-25")], user_id=1)
    assert _items(db, pr)[0].expected_date == "2026-08-10"
