"""Thời gian dự kiến có hàng trên YCMH mặc định = NGÀY QĐ CÓ HÀNG của phân loại (CR-065).

Ngày QĐ = Ngày tiếp nhận phiếu + số ngày QĐ; số ngày QĐ lấy mốc DÀI NHẤT (không sẵn hàng),
thiếu thì mốc có sẵn, thiếu cả hai thì 15 ngày.

Đây là GIÁ TRỊ KHỞI TẠO lúc TẠO dòng. Sau đó ngày này thuộc quyền NSTM: đổi giá trị đã có
vẫn phải kèm lý do (update_item_status), và lưu lại phiếu KHÔNG được điền đè.
"""
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ItemStatusIn, PRItemIn
from app.modules.purchase_request.service import _save_items, update_item_status


def _pr(db, code="PYC1", request_date="2026-08-10"):
    db.add_all([ItemGroup(code="PL1", name="NL", std_days="10", std_days_unavail="14"),
                ItemGroup(code="PL2", name="Chỉ có sẵn", std_days="6", std_days_unavail=""),
                ItemGroup(code="PL3", name="Vận chuyển", std_days="", std_days_unavail="")])
    pr = PurchaseRequest(code=code, status="draft", created_by=1, request_date=request_date)
    db.add(pr)
    db.commit()
    return pr


def _items(db, pr):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).order_by(
        PurchaseRequestItem.id).all()


def _luu(db, pr, **kw):
    kw.setdefault("product_name", "Hàng A")
    kw.setdefault("product_code", "SP1")
    kw.setdefault("qty", 10)
    kw.setdefault("required_date", "2026-08-14")
    _save_items(db, pr.id, [PRItemIn(**kw)], user_id=1)
    return _items(db, pr)


def test_dong_moi_lay_ngay_qd_theo_phan_loai(db):
    """Mốc "không sẵn hàng" (14) chứ không phải "có sẵn" (10): 10/08 + 14 = 24/08."""
    pr = _pr(db)
    assert _luu(db, pr, item_group="NL")[0].expected_date == "2026-08-24"


def test_thieu_moc_khong_san_thi_lay_moc_co_san(db):
    pr = _pr(db)
    assert _luu(db, pr, item_group="Chỉ có sẵn")[0].expected_date == "2026-08-16"   # +6


def test_phan_loai_chua_khai_bao_thi_15_ngay(db):
    pr = _pr(db)
    assert _luu(db, pr, item_group="Vận chuyển")[0].expected_date == "2026-08-25"   # +15


def test_chua_chon_phan_loai_cung_lay_moc_mac_dinh(db):
    pr = _pr(db)
    assert _luu(db, pr)[0].expected_date == "2026-08-25"                            # +15


def test_khong_co_ngay_tiep_nhan_thi_de_trong(db):
    pr = _pr(db, request_date="")
    assert _luu(db, pr, item_group="NL")[0].expected_date == ""


def test_luu_lai_phieu_khong_ghi_de_ngay_nstm_da_sua(db):
    pr = _pr(db)
    row = _luu(db, pr, item_group="NL")[0]
    update_item_status(db, pr.id, ItemStatusIn(items=[{"id": row.id, "expected_date": "2026-09-05",
                                                       "expected_date_reason": "NCC báo trễ"}]),
                       user_id=1, emp_code="", is_manager=True)
    # Lưu lại phiếu (đổi số lượng) — ngày dự kiến phải giữ nguyên, không tụt về ngày QĐ
    _luu(db, pr, id=row.id, qty=20, item_group="NL")
    assert _items(db, pr)[0].expected_date == "2026-09-05"


def test_doi_ngay_can_hang_khong_keo_ngay_du_kien_theo(db):
    """Ngày cần hàng là việc của bộ phận yêu cầu — không dính gì tới ngày QĐ có hàng."""
    pr = _pr(db)
    row = _luu(db, pr, item_group="NL")[0]
    _luu(db, pr, id=row.id, required_date="2026-08-25", item_group="NL")
    assert _items(db, pr)[0].expected_date == "2026-08-24"
