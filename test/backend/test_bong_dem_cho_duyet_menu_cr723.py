"""Bóng đỏ đếm phiếu chờ duyệt trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).

Canh các điều:
  - chỉ đếm trạng thái Chờ duyệt (`submitted`), không đếm nháp / đã duyệt / chờ duyệt điều phối;
  - khóa của mục người xem không có quyền DUYỆT phải VẮNG MẶT (giao diện dựa vào đó để không vẽ bóng);
  - lượt f (09/11/2026): YCBG · YCMH · ĐMH chỉ đếm phiếu mà ô Trưởng phòng phê duyệt
    (`approver_employee_id`) là chính nhân sự đang đăng nhập; ô trống không đếm cho ai;
  - Phiếu khảo sát không có ô đó nên vẫn đếm theo phạm vi DUYỆT (lượt e).
"""
import json

from app.modules.dashboard.controller import menu_badges, overview
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey.model import Survey
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User


def _badges(db, user):
    return json.loads(menu_badges(db=db, user=user).body)["data"]


def _po(db, seed, code, status, approver=0):
    db.add(PurchaseOrder(code=code, company_id=seed.company_id, order_date="2026-11-01", status=status,
                         approver_employee_id=approver))


def _pr(db, user, code, status, approver=0):
    db.add(PurchaseRequest(code=code, purpose="mua", status=status, approver_employee_id=approver,
                           created_by=user.id, updated_by=user.id))


def _sr(db, user, code, status, approver=0):
    db.add(SurveyRequest(code=code, purpose="khảo sát", status=status, approver_employee_id=approver,
                         created_by=user.id, updated_by=user.id))


def test_chi_dem_phieu_cho_duyet_co_minh_la_truong_phong_phe_duyet(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    me, other = seed.emp_req_id, seed.emp_tp_id
    for entity in ("purchase_order", "purchase_request", "survey_request"):
        cap_quyen(user.id, entity, scope="all", read=True, approve=True)

    _po(db, seed, "PO-CHO-MINH-1", "submitted", me)
    _po(db, seed, "PO-CHO-MINH-2", "submitted", me)
    _po(db, seed, "PO-CHO-NGUOI-KHAC", "submitted", other)
    _po(db, seed, "PO-NHAP-MINH", "draft", me)
    _po(db, seed, "PO-DUYET-MINH", "approved", me)
    _pr(db, user, "YCMH-CHO-MINH", "submitted", me)
    _pr(db, user, "YCMH-CHO-NGUOI-KHAC", "submitted", other)
    _sr(db, user, "YCBG-CHO-MINH", "submitted", me)
    db.commit()

    assert _badges(db, user) == {"purchase_order": 2, "purchase_request": 1, "survey_request": 1}


def test_o_truong_phong_phe_duyet_trong_thi_khong_dem_cho_ai(db, seed, cap_quyen):
    """Phiếu cũ trước bao-CR-499 để trống ô người duyệt: admin duyệt toàn hệ cũng không thấy số."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_request", scope="all", read=True, approve=True)
    _pr(db, user, "YCMH-TRONG", "submitted", 0)
    db.commit()

    assert _badges(db, user) == {"purchase_request": 0}


def test_tai_khoan_khong_gan_nhan_su_thi_ba_muc_bang_0(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True, approve=True)
    _po(db, seed, "PO-CHO-TRONG", "submitted", 0)
    db.commit()
    user.employee_id = 0

    assert _badges(db, user) == {"purchase_order": 0}


def test_khong_quyen_duyet_thi_khoa_vang_mat(db, seed, cap_quyen):
    """Được chọn làm người duyệt nhưng tài khoản chỉ có quyền xem: không có bóng (bóng 0 vẫn là nhiễu)."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "survey_request", scope="all", read=True)
    _sr(db, user, "YCBG-CHO-MINH", "submitted", seed.emp_req_id)
    db.commit()

    assert _badges(db, user) == {}


def test_ngoai_pham_vi_duyet_thi_khong_dem_du_duoc_chon(db, seed, cap_quyen):
    """Được chọn ở ô Trưởng phòng phê duyệt nhưng phạm vi duyệt không phủ phiếu: không bấm Duyệt được, không đếm."""
    user = db.get(User, seed.u_req_id)
    other = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "purchase_request", scope="own", read=True, approve=True)
    _pr(db, user, "YCMH-CUA-MINH", "submitted", seed.emp_req_id)
    _pr(db, other, "YCMH-NGUOI-KHAC-LAP", "submitted", seed.emp_req_id)
    db.commit()

    assert _badges(db, user) == {"purchase_request": 1}


def test_ycmh_khong_dem_phieu_cho_duyet_dieu_phoi(db, seed, cap_quyen):
    """Lượt f bỏ phần đếm phiếu `approved` chờ điều phối: chỉ còn Chờ duyệt."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_request", scope="all", read=True, approve=True)
    _pr(db, user, "YCMH-CHO-DUYET", "submitted", seed.emp_req_id)
    _pr(db, user, "YCMH-CHO-DIEU-PHOI", "approved", seed.emp_req_id)
    db.commit()

    assert _badges(db, user)["purchase_request"] == 1


def test_phieu_khao_sat_van_dem_theo_pham_vi_duyet(db, seed, cap_quyen):
    """Phiếu khảo sát không có ô Trưởng phòng phê duyệt: đếm mọi phiếu Chờ duyệt trong phạm vi duyệt."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "survey", scope="all", read=True, approve=True)
    db.add(Survey(code="PKS-CHO", survey_type="product", status="submitted", created_by=user.id, updated_by=user.id))
    db.add(Survey(code="PKS-NHAP", survey_type="product", status="draft", created_by=user.id, updated_by=user.id))
    db.commit()

    assert _badges(db, user) == {"survey": 1}


def test_the_don_mua_hang_cho_duyet_o_trang_chu_van_dem_theo_pham_vi_xem(db, seed, cap_quyen):
    """Thẻ "Đơn mua hàng chờ duyệt (POs)" là số liệu: đếm mọi đơn chờ duyệt xem được, bóng menu chỉ đếm đơn của mình."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "purchase_order", scope="all", read=True, approve=True)
    _po(db, seed, "PO-CHO-MINH", "submitted", seed.emp_req_id)
    _po(db, seed, "PO-CHO-NGUOI-KHAC", "submitted", seed.emp_tp_id)
    _po(db, seed, "PO-NHAN", "received")
    db.commit()

    kpi = json.loads(overview(db=db, user=user).body)["data"]["kpi"]

    assert kpi["po_pending"] == 2
    assert _badges(db, user)["purchase_order"] == 1
    #  `po_ordered` vẫn giữ cho chỗ khác còn đọc (giao diện v2, báo cáo).
    assert kpi["po_ordered"] == 1
