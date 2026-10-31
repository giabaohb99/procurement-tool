"""duoc-CR-706 — phiếu đặt xe chọn sẵn «Người phê duyệt»: người CÙNG QUYỀN duyệt đặt xe cũng duyệt được.

- Bộ máy BẬT, bước «Người có quyền duyệt»: giao người được chọn (đứng đầu) ∪ mọi người giữ quyền mà phạm vi phủ phiếu.
- Chuông + thư «chờ bạn duyệt» chỉ gửi người được chọn.
- Bộ máy TẮT: người có quyền duyệt với phạm vi phủ phiếu duyệt được; thư vẫn chỉ tới người được chọn.
- Phiếu đang chờ đã giao trước CR-706: `approver_expand.expand_pending_approvers` (idempotent, không gửi thư).
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.approval import action_service
from app.modules.approval.flow_model import (APPROVER_PERMISSION, SKIP_NONE, ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED, TASK_PENDING, ApprovalInstance,
                                                 ApprovalTask)
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.notification.model import EmailLog, Notification
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking import approver_expand
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.controller import _scoped_or_404
from app.modules.vehicle_booking.schema import VehicleBookingCreate
from app.modules.vehicle_booking.service import approve_booking, create_booking


@pytest.fixture(autouse=True)
def _fresh_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _role(db, code, *, scope="all", approve=True):
    role = Role(code=code, name=f"Vai trò {code}")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="vehicle_booking", can_read=True, can_create=True,
                      can_approve=approve, scope=scope))
    db.flush()
    return role


def _account(db, code, *roles, company_id=3):
    emp = Employee(code=code, full_name=f"Nhân sự {code}", email=f"{code.lower()}@dego.vn",
                   company_id=company_id, department_id=7, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return user


@pytest.fixture()
def org(db):
    for cid in (3, 5, 7):
        if db.get(Company, cid) is None:
            db.add(Company(id=cid, code=f"CT{cid}", name=f"Công ty {cid}"))
    db.flush()
    company_role = _role(db, "dispatcher_company", scope="company")
    all_role = _role(db, "dispatcher_all", scope="all")
    own_role = _role(db, "pur_manager", scope="own")
    creator = _account(db, "NV01", _role(db, "staff", approve=False))
    picked = _account(db, "DP05", company_role, company_id=5)         # phạm vi công ty 5, KHÔNG phủ phiếu công ty 3
    same_all = _account(db, "DP99", all_role)                         # cùng quyền, phạm vi Tất cả
    same_co3 = _account(db, "DP03", company_role, company_id=3)       # cùng quyền, phạm vi công ty 3 (phủ phiếu)
    other_co7 = _account(db, "DP07", company_role, company_id=7)      # cùng quyền nhưng công ty 7 (không phủ)
    own_only = _account(db, "TM01", own_role)
    admin = _account(db, "AD01", _role(db, "admin"))
    db.commit()
    return SimpleNamespace(creator=creator, picked=picked, same_all=same_all, same_co3=same_co3,
                           other_co7=other_co7, own_only=own_only, admin=admin)


def _payload(**over):
    data = dict(request_type=1, purpose="Đi công tác", start_location="VP", end_location="Q7",
                start_time="2026-11-01T08:00", end_time="2026-11-01T10:00", passenger_count=1, company_id=3)
    data.update(over)
    return VehicleBookingCreate(**data)


def _engine(db, multi_mode=None):
    db.add(ApprovalSwitch(entity="vehicle_booking", is_enabled=True))
    flow = ApprovalFlow(entity="vehicle_booking", code="DX-Q", name="Duyệt theo quyền", is_active=True,
                        created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    node = ApprovalNode(flow_id=flow.id, seq=1, name="Điều phối duyệt", approver_kind=APPROVER_PERMISSION,
                        approver_ref="vehicle_booking", skip_duplicate=SKIP_NONE, created_by=1, updated_by=1)
    if multi_mode is not None:
        node.multi_mode = multi_mode
    db.add(node)
    db.commit()


def _instance(db, booking):
    return db.query(ApprovalInstance).filter_by(entity="vehicle_booking", entity_id=booking.id).one()


def _pending(db, booking):
    return [t.assignee_employee_id for t in db.query(ApprovalTask)
            .filter(ApprovalTask.instance_id == _instance(db, booking).id, ApprovalTask.status == TASK_PENDING)
            .order_by(ApprovalTask.order_no.asc())]


def _booking_links(db):
    return db.query(Notification).filter(Notification.link.like("%/vehicle-booking/%"))


# ─────────────────────────── Bộ máy BẬT ───────────────────────────

def test_may_bat_giao_nguoi_duoc_chon_va_moi_nguoi_cung_quyen_phu_pham_vi(db, org):
    _engine(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    pending = _pending(db, booking)
    assert pending[0] == org.picked.employee_id          # người được chọn đứng đầu
    #  Người được chọn giữ dù phạm vi không phủ; người cùng quyền chỉ khi phạm vi phủ phiếu công ty 3.
    assert set(pending) == {org.picked.employee_id, org.same_all.employee_id, org.same_co3.employee_id}
    assert org.other_co7.employee_id not in pending
    assert org.own_only.employee_id not in pending
    assert org.admin.employee_id not in pending


def test_may_bat_chi_nguoi_duoc_chon_nhan_thu_va_chuong(db, org):
    _engine(db)
    create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert [e.to_email for e in db.query(EmailLog).filter_by(event="dx_submitted")] == [org.picked.email]
    assert {n.user_id for n in _booking_links(db)} == {org.picked.id}


def test_may_bat_phieu_khong_chon_thi_bao_het_nhu_cu(db, org):
    _engine(db)
    booking = create_booking(db, _payload(), org.creator, submit=True)
    assert set(_pending(db, booking)) == {org.same_all.employee_id, org.same_co3.employee_id}
    assert {n.user_id for n in _booking_links(db)} == {org.same_all.id, org.same_co3.id}


def test_may_bat_nguoi_cung_quyen_duyet_duoc_phieu(db, org):
    _engine(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    instance = _instance(db, booking)
    action_service.approve(db, instance, org.same_co3.employee_id, org.same_co3.id, {})
    db.commit()
    db.refresh(instance)
    db.refresh(booking)
    assert instance.status == INSTANCE_APPROVED
    assert booking.status == m.BK_APPROVED
    assert booking.approved_by == org.same_co3.id


def test_may_bat_nguoi_khac_phamvi_khong_phu_khong_duyet_duoc(db, org):
    _engine(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    with pytest.raises(HTTPException) as err:
        action_service.approve(db, _instance(db, booking), org.other_co7.employee_id, org.other_co7.id, {})
    assert err.value.status_code == 403


def test_may_bat_admin_khong_tu_thanh_nguoi_giu_quyen_va_khong_co_cua_ngang(db, org):
    """Giữ luật cũ: admin không được giao việc; bộ máy không có ngoại lệ admin → 403 (chỉ qua ủy quyền)."""
    _engine(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert org.admin.employee_id not in _pending(db, booking)
    with pytest.raises(HTTPException) as err:
        action_service.approve(db, _instance(db, booking), org.admin.employee_id, org.admin.id, {})
    assert err.value.status_code == 403


def test_may_bat_nguoi_duoc_chon_mat_quyen_thi_bo_lua_chon_va_bao_het(db, org):
    _engine(db)
    db.query(UserRole).filter_by(user_id=org.picked.id).delete()
    db.commit()
    perm_cache_clear()
    booking = m.VehicleBooking(code="DX-T", company_id=3, department_id=0, created_by=1, purpose="x",
                               first_approver_id=org.picked.id, status=m.BK_DRAFT)
    db.add(booking)
    db.commit()
    from app.modules.vehicle_booking.approval_bridge import submit_for_approval

    booking.status = m.BK_PENDING
    submit_for_approval(db, booking, org.creator.id)
    db.commit()
    assert set(_pending(db, booking)) == {org.same_all.employee_id, org.same_co3.employee_id}
    #  Người được chọn không còn việc ở chặng → bộ lọc báo hết, chặng không im lặng.
    assert {n.user_id for n in _booking_links(db)} == {org.same_all.id, org.same_co3.id}


# ─────────────────────────── Bộ máy TẮT ───────────────────────────

def test_may_tat_nguoi_cung_quyen_phu_pham_vi_duyet_duoc_va_thu_chi_toi_nguoi_chon(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert booking.status == m.BK_PENDING
    assert [e.to_email for e in db.query(EmailLog).filter_by(event="dx_submitted")] == [org.picked.email]
    assert {n.user_id for n in _booking_links(db)} == {org.picked.id}
    for user in (org.same_all, org.same_co3):
        assert _scoped_or_404(db, booking.id, user, "approve").id == booking.id
    #  Người được chọn qua cửa riêng; khác phạm vi / chỉ «Của mình» → 404.
    assert _scoped_or_404(db, booking.id, org.picked, "approve").id == booking.id
    for user in (org.other_co7, org.own_only):
        with pytest.raises(HTTPException) as err:
            _scoped_or_404(db, booking.id, user, "approve")
        assert err.value.status_code == 404


def test_may_tat_nguoi_cung_quyen_bam_duyet_that(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    obj = _scoped_or_404(db, booking.id, org.same_co3, "approve")
    approve_booking(db, obj, org.same_co3)
    assert booking.status == m.BK_APPROVED
    assert booking.approved_by == org.same_co3.id


def test_may_tat_admin_duyet_duoc_theo_pham_vi_tat_ca_cua_ma_tran(db, org):
    """Đường cũ không có chốt admin riêng: ma trận cho admin ô Duyệt «Tất cả» nên `get_scoped` cho qua."""
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert _scoped_or_404(db, booking.id, org.admin, "approve").id == booking.id


# ─────────────────────────── Phiếu đang chờ đã giao trước CR-706 ───────────────────────────

def _shrink_to_picked_only(db, booking, picked_employee_id):
    """Dựng lại trạng thái trước CR-706: chặng chỉ còn việc của người được chọn."""
    db.query(ApprovalTask).filter(ApprovalTask.instance_id == _instance(db, booking).id,
                                  ApprovalTask.assignee_employee_id != picked_employee_id).delete()
    db.commit()


def test_script_mo_rong_xem_thu_khong_ghi_apply_ghi_va_idempotent_khong_gui_thu(db, org):
    _engine(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    _shrink_to_picked_only(db, booking, org.picked.employee_id)
    assert _pending(db, booking) == [org.picked.employee_id]
    notes_before = db.query(Notification).count()
    mails_before = db.query(EmailLog).count()

    dry = approver_expand.expand_pending_approvers(db)
    assert len(dry) == 1 and set(dry[0]["added_employee_ids"]) == {org.same_all.employee_id, org.same_co3.employee_id}
    assert _pending(db, booking) == [org.picked.employee_id]          # xem thử: chưa ghi

    done = approver_expand.expand_pending_approvers(db, apply=True)
    assert len(done) == 1
    assert set(_pending(db, booking)) == {org.picked.employee_id, org.same_all.employee_id,
                                          org.same_co3.employee_id}
    assert approver_expand.expand_pending_approvers(db, apply=True) == []   # chạy lại: không đẻ thêm
    assert db.query(ApprovalTask).filter_by(instance_id=_instance(db, booking).id).count() == 3
    assert (db.query(Notification).count(), db.query(EmailLog).count()) == (notes_before, mails_before)


def test_script_mo_rong_bo_qua_phieu_khong_chon_nguoi_va_chang_khong_phai_buoc_theo_quyen(db, org):
    _engine(db)
    booking = create_booking(db, _payload(), org.creator, submit=True)   # không chọn người
    _shrink_to_picked_only(db, booking, org.same_all.employee_id)
    assert approver_expand.expand_pending_approvers(db, apply=True) == []
