"""Bóng đỏ đếm phiếu chờ duyệt trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Canh ba điều:
  - chỉ đếm trạng thái Chờ duyệt (`submitted`), không đếm nháp / đã duyệt;
  - khóa của mục người xem không có quyền DUYỆT phải VẮNG MẶT (giao diện dựa vào đó để không vẽ bóng);
  - chỉ đếm phiếu CHỜ MÌNH DUYỆT: phạm vi DUYỆT, không theo phạm vi xem (lượt e, 07/11/2026);
  - YCMH cộng phiếu chờ duyệt điều phối cho người điều phối được.
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
    cap_quyen(user.id, "purchase_order", scope="all", read=True, approve=True)
    cap_quyen(user.id, "purchase_request", scope="all", read=True, approve=True)
    #  Xem được YCBG nhưng KHÔNG duyệt được: không có bóng.
    cap_quyen(user.id, "survey_request", scope="all", read=True)

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
    #  Không có quyền duyệt YCBG / phiếu khảo sát thì khóa vắng mặt — không trả 0 (bóng 0 vẫn là nhiễu).
    assert "survey_request" not in data
    assert "survey" not in data


def test_khong_quyen_gi_thi_khong_co_bong_nao(db, seed):
    user = db.get(User, seed.u_req_id)
    db.add(SurveyRequest(code="YCBG-CHO", purpose="khảo sát", status="submitted", created_by=user.id, updated_by=user.id))
    db.commit()

    assert _badges(db, user) == {}


def test_so_tren_menu_khop_the_don_mua_hang_cho_duyet_o_trang_chu(db, seed, cap_quyen):
    """Thẻ "Đơn mua hàng chờ duyệt (POs)" thay "Đơn hàng hoạt động" — cùng số với bóng menu KHI phạm vi
    xem = phạm vi duyệt (người duyệt toàn hệ)."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True, approve=True)
    _po(db, seed, "PO-CHO-1", "submitted")
    _po(db, seed, "PO-NHAN", "received")
    db.commit()

    kpi = json.loads(overview(db=db, user=user).body)["data"]["kpi"]

    assert kpi["po_pending"] == 1 == _badges(db, user)["purchase_order"]
    #  `po_ordered` vẫn giữ cho chỗ khác còn đọc (giao diện v2, báo cáo).
    assert kpi["po_ordered"] == 1


def test_chi_xem_khong_duyet_thi_khong_co_bong(db, seed, cap_quyen):
    """Lượt e: người lập phiếu chỉ có quyền xem thì không thấy bóng cho phiếu mình không duyệt được."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_request", scope="all", read=True, create=True)
    db.add(PurchaseRequest(code="YCMH-CHO", purpose="mua giấy", status="submitted", created_by=user.id, updated_by=user.id))
    db.commit()

    assert _badges(db, user) == {}


def test_dem_theo_pham_vi_duyet_khong_theo_pham_vi_xem(db, seed, cap_quyen):
    """Xem toàn hệ nhưng chỉ duyệt phiếu của mình (phạm vi `own`): bóng chỉ đếm phiếu mình duyệt được."""
    user = db.get(User, seed.u_req_id)
    other = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "purchase_request", scope="all", read=True)
    cap_quyen(user.id, "purchase_request", scope="own", approve=True)
    db.add(PurchaseRequest(code="YCMH-CUA-MINH", purpose="a", status="submitted", created_by=user.id, updated_by=user.id))
    db.add(PurchaseRequest(code="YCMH-NGUOI-KHAC", purpose="b", status="submitted", created_by=other.id, updated_by=other.id))
    db.commit()

    assert _badges(db, user) == {"purchase_request": 1}


def test_ycmh_dem_ca_phieu_cho_duyet_dieu_phoi_cho_nguoi_dieu_phoi(db, seed, cap_quyen, monkeypatch):
    """Quản lý thu mua (duyệt phạm vi `all`) điều phối được: phiếu `approved` cũng là việc chờ họ.
    Tắt bước điều phối thì không đếm phiếu `approved` nữa (phiếu đã đi thẳng sang dispatched)."""
    from app.modules.dashboard import menu_badge_service

    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_request", scope="all", read=True, approve=True)
    db.add(PurchaseRequest(code="YCMH-CHO-DUYET", purpose="a", status="submitted", created_by=user.id, updated_by=user.id))
    db.add(PurchaseRequest(code="YCMH-CHO-DIEU-PHOI", purpose="b", status="approved", created_by=user.id, updated_by=user.id))
    db.add(PurchaseRequest(code="YCMH-DA-DIEU-PHOI", purpose="c", status="dispatched", created_by=user.id, updated_by=user.id))
    db.commit()

    monkeypatch.setattr(menu_badge_service, "dispatch_enabled", lambda: True)
    assert _badges(db, user)["purchase_request"] == 2
    monkeypatch.setattr(menu_badge_service, "dispatch_enabled", lambda: False)
    assert _badges(db, user)["purchase_request"] == 1


def test_truong_phong_khong_dieu_phoi_thi_khong_dem_phieu_cho_dieu_phoi(db, seed, cap_quyen, monkeypatch):
    """Trưởng phòng duyệt phạm vi phòng (`dept`) chỉ duyệt bước 1 — phiếu chờ điều phối không phải việc của họ."""
    from app.modules.dashboard import menu_badge_service

    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_request", scope="own", read=True, approve=True)
    db.add(PurchaseRequest(code="YCMH-CHO-DUYET", purpose="a", status="submitted", created_by=user.id, updated_by=user.id))
    db.add(PurchaseRequest(code="YCMH-CHO-DIEU-PHOI", purpose="b", status="approved", created_by=user.id, updated_by=user.id))
    db.commit()

    monkeypatch.setattr(menu_badge_service, "dispatch_enabled", lambda: True)
    assert _badges(db, user)["purchase_request"] == 1
