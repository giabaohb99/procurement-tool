"""Bóng đỏ đếm phiếu chờ duyệt trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Canh ba điều:
  - chỉ đếm trạng thái Chờ duyệt (`submitted`), không đếm nháp / đã duyệt;
  - khóa của mục người xem không có quyền đọc phải VẮNG MẶT (giao diện dựa vào đó để không vẽ bóng);
  - phạm vi dữ liệu áp như mọi màn danh sách — số trên menu phải khớp số thẻ Trang chủ.
"""
import json

from app.modules.dashboard.controller import menu_badges, overview
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User


def _badges(db, user):
    return json.loads(menu_badges(db=db, user=user).body)["data"]


def _po(db, seed, code, status):
    db.add(PurchaseOrder(code=code, company_id=seed.company_id, order_date="2026-11-01", status=status))


def test_chi_dem_phieu_cho_duyet_va_chi_khoa_co_quyen(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    cap_quyen(user.id, "purchase_request", scope="all", read=True)

    _po(db, seed, "PO-CHO-1", "submitted")
    _po(db, seed, "PO-CHO-2", "submitted")
    _po(db, seed, "PO-NHAP", "draft")
    _po(db, seed, "PO-DUYET", "approved")
    db.add(PurchaseRequest(code="YCMH-CHO", purpose="mua giấy", status="submitted", created_by=user.id, updated_by=user.id))
    db.add(PurchaseRequest(code="YCMH-NHAP", purpose="nháp", status="draft", created_by=user.id, updated_by=user.id))
    db.add(SurveyRequest(code="YCBG-CHO", purpose="khảo sát", status="submitted", created_by=user.id, updated_by=user.id))
    db.commit()

    data = _badges(db, user)

    assert data["purchase_order"] == 2
    assert data["purchase_request"] == 1
    #  Không có quyền đọc YCBG / phiếu khảo sát thì khóa vắng mặt — không trả 0 (0 vẫn lộ là có màn đó).
    assert "survey_request" not in data
    assert "survey" not in data


def test_khong_quyen_gi_thi_khong_co_bong_nao(db, seed):
    user = db.get(User, seed.u_req_id)
    db.add(SurveyRequest(code="YCBG-CHO", purpose="khảo sát", status="submitted", created_by=user.id, updated_by=user.id))
    db.commit()

    assert _badges(db, user) == {}


def test_so_tren_menu_khop_the_don_mua_hang_cho_duyet_o_trang_chu(db, seed, cap_quyen):
    """Thẻ "Đơn mua hàng chờ duyệt (POs)" thay "Đơn hàng hoạt động" — cùng một con số với bóng menu."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    _po(db, seed, "PO-CHO-1", "submitted")
    _po(db, seed, "PO-NHAN", "received")
    db.commit()

    kpi = json.loads(overview(db=db, user=user).body)["data"]["kpi"]

    assert kpi["po_pending"] == 1 == _badges(db, user)["purchase_order"]
    #  `po_ordered` vẫn giữ cho chỗ khác còn đọc (giao diện v2, báo cáo).
    assert kpi["po_ordered"] == 1
