"""Tự bật Đơn gấp khi ngày cần hàng sớm hơn thời gian quy định của phân loại (CR-082).

Luật chốt với khách: chỉ cần MỘT dòng có (ngày cần hàng − ngày tiếp nhận) NHỎ HƠN số ngày QĐ
của phân loại là cả phiếu thành Đơn gấp — thiếu đúng 1 ngày cũng tính, không có ngưỡng dung sai.
Hệ thống chỉ BẬT, không bao giờ tự tắt: bỏ gấp là quyết định của người dùng.
"""
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.schema import PRItemIn, PRUpdate
from app.modules.purchase_request import service as pr_service

BASE = "2026-08-10"
QD_NL = "2026-08-24"      # BASE + 14 ngày (mốc "không sẵn hàng" của phân loại NL)


def _groups(db):
    db.add_all([ItemGroup(code="PL1", name="NL", std_days="10", std_days_unavail="14"),
                ItemGroup(code="PL2", name="Vận chuyển", std_days="", std_days_unavail="")])
    db.commit()


def _pr(db, code="PYC1", request_date=BASE, status="draft", **kw):
    _groups(db)
    pr = PurchaseRequest(code=code, status=status, created_by=1, request_date=request_date, **kw)
    db.add(pr)
    db.commit()
    return pr


def _line(**kw):
    kw.setdefault("product_code", "SP1")
    kw.setdefault("product_name", "Hàng A")
    kw.setdefault("qty", 1)
    kw.setdefault("item_group", "NL")
    return PRItemIn(**kw)


def _luu(db, pr, *lines):
    pr_service._save_items(db, pr.id, list(lines), user_id=1)
    db.refresh(pr)
    return pr


def test_dung_ngay_qd_thi_khong_gap(db):
    pr = _pr(db)
    _luu(db, pr, _line(required_date=QD_NL))
    assert pr.is_urgent is False


def test_thieu_dung_mot_ngay_van_la_gap(db):
    """15 ngày mà cần trong 14 ngày rưỡi cũng gấp — ngày lưu theo ngày nên sớm 1 ngày là gấp."""
    pr = _pr(db)
    _luu(db, pr, _line(required_date="2026-08-23"))
    assert pr.is_urgent is True


def test_mot_dong_vi_pham_la_ca_phieu_gap(db):
    pr = _pr(db)
    _luu(db, pr,
         _line(product_code="SP1", required_date="2026-09-30"),
         _line(product_code="SP2", required_date="2026-08-12"))
    assert pr.is_urgent is True


def test_phan_loai_la_lay_moc_15_ngay(db):
    pr = _pr(db)
    _luu(db, pr, _line(item_group="Vận chuyển", required_date="2026-08-24"))   # < 25/08
    assert pr.is_urgent is True


def test_dong_trong_ngay_can_hang_khong_xet(db):
    pr = _pr(db)
    _luu(db, pr, _line(required_date=""))
    assert pr.is_urgent is False


def test_dong_huy_don_khong_xet(db):
    pr = _pr(db)
    _luu(db, pr, _line(required_date="2026-08-12", line_status="Hủy đơn"))
    assert pr.is_urgent is False


def test_phieu_chua_co_ngay_tiep_nhan_thi_bo_qua(db):
    pr = _pr(db, request_date="")
    _luu(db, pr, _line(required_date="2026-08-12"))
    assert pr.is_urgent is False


def test_khong_tu_tat_co_da_bat(db):
    """Sửa lại cho đúng hạn KHÔNG làm phiếu hết gấp — tắt là việc của người dùng."""
    pr = _pr(db, is_urgent=True)
    _luu(db, pr, _line(required_date="2026-09-30"))
    assert pr.is_urgent is True


def test_phieu_da_huy_khong_dung_toi(db):
    pr = _pr(db, status="cancelled")
    assert pr_service.apply_auto_urgent(db, pr, user_id=1) is False
    assert pr.is_urgent is False


def test_tu_bat_thi_dong_bo_xuong_don_mua_hang(db):
    pr = _pr(db)
    db.add_all([PurchaseOrder(code="PO1", pr_code="PYC1", is_urgent=False, status="approved"),
                PurchaseOrder(code="PO9", pr_code="PYC-KHAC", is_urgent=False, status="approved")])
    db.commit()
    _luu(db, pr, _line(required_date="2026-08-12"))
    po1 = db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO1").first()
    po9 = db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO9").first()
    assert pr.is_urgent is True and po1.is_urgent is True
    assert po9.is_urgent is False


def test_ghi_nhat_ky_ly_do(db):
    from app.modules.audit.model import AuditLog
    pr = _pr(db)
    _luu(db, pr, _line(required_date="2026-08-12"))
    logs = [x.message for x in db.query(AuditLog).filter(AuditLog.entity == "purchase_request").all()]
    assert any("Tự bật Đơn gấp" in (m or "") and "ngày QĐ" in (m or "") for m in logs)


def test_nhan_ban_phieu_cung_tu_gap(db):
    pr = _pr(db)
    _luu(db, pr, _line(required_date="2026-09-30"))
    pr.is_urgent = False
    items = pr_service.items_of(db, pr.id)
    items[0].required_date = "2026-08-12"       # dữ liệu cũ chưa qua luật này
    db.commit()
    moi = pr_service.copy_pr(db, pr.id, user_id=1)
    assert moi.is_urgent is True


def test_tat_tay_ngay_trong_lan_luu_do_thi_ton_trong(db):
    pr = _pr(db, is_urgent=True)
    pr_service.update_pr(db, pr.id, PRUpdate(is_urgent=False,
                                             items=[_line(required_date="2026-08-12")]), user_id=1)
    db.refresh(pr)
    assert pr.is_urgent is False


def test_lan_luu_ke_tiep_thi_bat_lai(db):
    """Đã tắt tay nhưng ngày cần hàng vẫn sớm hơn quy định → lần lưu sau hệ thống bật lại."""
    pr = _pr(db, is_urgent=True)
    pr_service.update_pr(db, pr.id, PRUpdate(is_urgent=False,
                                             items=[_line(required_date="2026-08-12")]), user_id=1)
    pr_service.update_pr(db, pr.id, PRUpdate(items=[_line(required_date="2026-08-12")]), user_id=1)
    db.refresh(pr)
    assert pr.is_urgent is True
