"""duoc-CR-662 (kh-TM1-1) — ĐMH / YCTT gửi duyệt phải làm chuông kêu ở NGƯỜI DUYỆT đúng.

Phát hiện 21/10 khi lập bộ AGC: gửi duyệt ĐMH và YCTT mà không thấy chuông. Các bài kiểm cũ đều
chặn `trigger_notification`, nên đường báo thật chưa từng được chạy. Bài này chạy ĐƯỜNG THẬT
(controller → trigger_notification → bảng thông báo) và soi ai nhận.

Nguyên nhân gốc (`get_approvers_for_entity`):
  1. Người vừa có vai trò quản trị vừa có vai trò duyệt bị loại (cả người có admin lẫn quản lý
     thu mua) — bộ tài khoản dựng bởi quản trị không bao giờ nhận chuông.
  2. Chỉ quản trị có quyền duyệt (hoặc vai trò duyệt chưa ai giữ) thì người nhận RỖNG, không rơi
     về đâu.
  3. Không xét phạm vi: báo cả người không duyệt được (thu mua trừ phòng tự mua), người đúng phạm
     vi lẫn trong đám đông.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.core.auth import perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.payment_request import controller as pay_ctl
from app.modules.payment_request import service as pay_service
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_order import controller as po_ctl
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole

ACTIONS = dict(can_read=True, can_write=True, can_approve=True)


def _role(db, code):
    role = db.query(Role).filter(Role.code == code).first()
    if not role:
        role = Role(code=code, name=code)
        db.add(role)
        db.flush()
    return role


def _grant(db, user, role_code, entity, scope="all", approve=True):
    """Gán `role_code` cho user; vai trò có quyền `entity` (approve tùy chọn) ở phạm vi `scope`."""
    role = _role(db, role_code)
    if not db.query(Permission).filter(Permission.role_id == role.id, Permission.entity == entity).first():
        db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                          **{**ACTIONS, "can_approve": approve}))
    if not db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first():
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    perm_cache_clear(user.id)


def _user(db, seed, code, dept_id=None):
    emp = Employee(code=code, full_name=code, company_id=seed.company_id,
                   department_id=dept_id or seed.dept_id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=code, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


def _po(db, seed, submitter, dept_id=None):
    po = PurchaseOrder(code="PO662%d" % (db.query(PurchaseOrder).count() + 1), status="draft",
                       supplier_code="NX", supplier_name="NCC", company_id=seed.company_id,
                       department_id=dept_id or seed.dept_id, created_by=submitter.id)
    db.add(po)
    db.commit()
    db.add(POItem(po_id=po.id, progress_status="Chưa đặt hàng", product_code="SP1", product_name="Hàng",
                  item_group="NL", invoice_name="Hàng", required_date="2026-10-25",
                  expected_date="2026-10-25", unit="Cái", warehouse_code="K1",
                  qty_request=1, qty_order=1, price=10))
    db.commit()
    return po


def _submit_po(db, po, submitter):
    return po_ctl.submit_po(po.id, BackgroundTasks(), db=db, user=submitter)


@pytest.fixture
def submitter(db, seed, cap_quyen):
    u = db.get(User, seed.u_req_id)
    cap_quyen(u.id, "purchase_order", scope="all", read=True, write=True)
    cap_quyen(u.id, "payment_request", scope="all", read=True, write=True)
    return u


# --- ĐMH -----------------------------------------------------------------------------

def test_dmh_nguoi_duyet_thuong_nhan_chuong(db, seed, submitter):
    """Đường cơ bản: quản lý thu mua có quyền duyệt ĐMH nhận chuông."""
    ql = _user(db, seed, "QL1")
    _grant(db, ql, "pur_manager", "purchase_order")
    po = _po(db, seed, submitter)
    _submit_po(db, po, submitter)
    notes = db.query(Notification).filter(Notification.user_id == ql.id).all()
    assert len(notes) == 1 and notes[0].link == f"/purchase-orders/{po.id}"
    assert po.code in notes[0].title


def test_dmh_nguoi_vua_admin_vua_quan_ly_van_nhan_chuong(db, seed, submitter):
    """Lỗi 1: có thêm vai trò admin là bị loại oan."""
    u = _user(db, seed, "ADMQL")
    _grant(db, u, "admin", "purchase_order")
    _grant(db, u, "pur_manager", "purchase_order")
    _submit_po(db, _po(db, seed, submitter), submitter)
    assert u.id in {n.user_id for n in db.query(Notification).all()}


def test_dmh_chi_quan_tri_co_quyen_duyet_thi_roi_ve_quan_tri(db, seed, submitter):
    """Lỗi 2: không có vai trò thường nào giữ quyền duyệt → trước đây người nhận RỖNG."""
    adm = _user(db, seed, "ADM1")
    _grant(db, adm, "admin", "purchase_order")
    _submit_po(db, _po(db, seed, submitter), submitter)
    assert adm.id in {n.user_id for n in db.query(Notification).all()}


def test_dmh_phong_tu_mua_chi_bao_quan_ly_phong_do(db, seed, submitter):
    """Lỗi 3: phòng tự mua — báo đúng quản lý phòng mua, không báo người thu mua trừ phòng đó."""
    dept_nm = Department(code="NM", name="Nhà máy", company_id=seed.company_id, is_active=True)
    db.add(dept_nm)
    db.commit()
    nm = _user(db, seed, "NMQL", dept_id=dept_nm.id)
    tm = _user(db, seed, "TMQL")   # thu mua chung, phạm vi phòng khác
    _grant(db, nm, "pur_dept_manager", "purchase_order", scope="dept")
    _grant(db, tm, "pur_manager", "purchase_order", scope="dept")
    po = _po(db, seed, submitter, dept_id=dept_nm.id)
    _submit_po(db, po, submitter)
    got = {n.user_id for n in db.query(Notification).all()}
    assert nm.id in got
    assert tm.id not in got


def test_dmh_khong_ai_trong_pham_vi_van_roi_ve_quan_tri(db, seed, submitter):
    """Người duyệt thường ngoài phạm vi hết → quản trị (phạm vi tất cả) vẫn nhận."""
    dept_nm = Department(code="NM2", name="Nhà máy 2", company_id=seed.company_id, is_active=True)
    db.add(dept_nm)
    db.commit()
    tm = _user(db, seed, "TMQL2")
    adm = _user(db, seed, "ADM2")
    _grant(db, tm, "pur_manager", "purchase_order", scope="dept")
    _grant(db, adm, "admin", "purchase_order")
    _submit_po(db, _po(db, seed, submitter, dept_id=dept_nm.id), submitter)
    got = {n.user_id for n in db.query(Notification).all()}
    assert adm.id in got and tm.id not in got


# --- YCTT ----------------------------------------------------------------------------

def _yctt(db, seed, submitter):
    data = PRequestCreate(supplier_code="NX", company_id=seed.company_id, request_date="2026-10-22",
                          prepay=1, lines=[LineIn(po_code="PO-CR662", invoice_no="HD1", amount=1000)])
    return pay_service.create_requests(db, data, submitter.id)[0]


def test_yctt_gui_duyet_bao_nguoi_duyet(db, seed, submitter):
    ql = _user(db, seed, "QLP")
    _grant(db, ql, "pur_manager", "payment_request")
    r = _yctt(db, seed, submitter)
    pay_ctl.submit_(r.id, BackgroundTasks(), db=db, user=submitter)
    notes = db.query(Notification).filter(Notification.user_id == ql.id).all()
    assert len(notes) == 1 and "YCTT" in notes[0].title and notes[0].link == f"/payment-requests/{r.id}"


def test_yctt_nguoi_vua_admin_vua_quan_ly_van_nhan(db, seed, submitter):
    u = _user(db, seed, "ADMQLP")
    _grant(db, u, "admin", "payment_request")
    _grant(db, u, "pur_manager", "payment_request")
    r = _yctt(db, seed, submitter)
    pay_ctl.submit_(r.id, BackgroundTasks(), db=db, user=submitter)
    assert db.query(Notification).filter(Notification.user_id == u.id).count() == 1


def test_yctt_chi_quan_tri_duyet_thi_roi_ve_quan_tri(db, seed, submitter):
    adm = _user(db, seed, "ADMP")
    _grant(db, adm, "admin", "payment_request")
    r = _yctt(db, seed, submitter)
    pay_ctl.submit_(r.id, BackgroundTasks(), db=db, user=submitter)
    assert db.query(Notification).filter(Notification.user_id == adm.id).count() == 1


# --- Giữ NGUYÊN hành vi cũ cho Duyệt dấu / Đặt xe (review CR-662) ---------------------------

def test_o_chon_duyet_dau_khong_doi_admin_kiem_quan_ly_van_bi_loai(db, seed):
    from app.modules.seal_request import service as seal_service
    both = _user(db, seed, "SEALBOTH")
    plain = _user(db, seed, "SEALPLAIN")
    _grant(db, both, "admin", "seal_request")
    _grant(db, both, "pur_manager", "seal_request")
    _grant(db, plain, "seal_approver", "seal_request")
    ids = {i["id"] for i in seal_service.approver_options(db, plain)["items"]}
    assert plain.id in ids and both.id not in ids


def test_o_chon_duyet_dau_chi_admin_co_quyen_thi_van_rong(db, seed):
    from app.modules.seal_request import service as seal_service
    adm = _user(db, seed, "SEALADM")
    _grant(db, adm, "admin", "seal_request")
    assert seal_service.approver_options(db, adm)["items"] == []


def test_loi_tinh_pham_vi_duoc_ghi_log(db, seed, monkeypatch, caplog):
    import app.core.scoping as scoping
    from app.modules.notification.service import get_approvers_for_entity
    ql = _user(db, seed, "QLERR")
    _grant(db, ql, "pur_manager", "purchase_order")

    def boom(*a, **k):
        raise RuntimeError("hong")
    monkeypatch.setattr(scoping, "get_scoped", boom)
    with caplog.at_level("WARNING", logger="app.scoping"):
        assert get_approvers_for_entity(db, "purchase_order", 1, new_rules=True) == []
    assert any("pham vi duyet" in r.message for r in caplog.records)
