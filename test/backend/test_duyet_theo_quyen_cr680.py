"""duoc-CR-680 — cách chọn người duyệt thứ chín «Người có quyền duyệt (theo phân quyền)».

Người được giao = giữ vai trò có ô «Duyệt» trên khóa quyền của loại chứng từ (vd `vehicle_booking`),
phạm vi Phòng ban / Công ty / Tất cả, KHÔNG tính vai trò `admin`, tài khoản mở + có hồ sơ, và phạm vi
của CHÍNH các grant đó phủ được phiếu. Các bài «review C1/C2/H1/H2/M1/M3» nhắc lại lỗi code review tìm ra.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.approval import permission_approvers
from app.modules.approval.approver_resolver import resolve
from app.modules.approval.flow_controller import (NodeIn, _node_values, _resync_permission_steps, options,
                                                  permission_approvers_of)
from app.modules.approval.flow_model import APPROVER_PERMISSION, APPROVER_ROLE, ApprovalFlow, ApprovalNode
from app.modules.approval.preview_service import _rule_label
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking.model import VehicleBooking


@pytest.fixture(autouse=True)
def _fresh_perm_cache():
    #  Mỗi bài một SQLite mới → id người dùng tái dùng giữa các bài, hồ sơ quyền cache 60 giây.
    perm_cache_clear()
    yield
    perm_cache_clear()


def _role(db, code, *, approve=True, scope="all", entity="vehicle_booking"):
    role = Role(code=code, name=f"Vai trò {code}")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, can_read=True, can_approve=approve, scope=scope))
    db.flush()
    return role


def _person(db, code, *roles, company_id=3, active=True, with_employee=True):
    emp = None
    if with_employee:
        emp = Employee(code=code, full_name=f"Nhân sự {code}", company_id=company_id, is_active=True)
        db.add(emp)
        db.flush()
    user = User(email=f"{code.lower()}@dego.test", employee_id=emp.id if emp else None, is_active=active)
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return emp, user


def _booking(db, company_id=3, created_by=999):
    row = VehicleBooking(code=f"XE{company_id}-{created_by}", company_id=company_id, department_id=0,
                         created_by=created_by, purpose="Đi công tác")
    db.add(row)
    db.flush()
    return row


def _subject(db, company_id=3, created_by=999):
    return {"id": _booking(db, company_id, created_by).id, "company_id": company_id}


def _node(ref="vehicle_booking"):
    return SimpleNamespace(approver_kind=APPROVER_PERMISSION, approver_ref=ref)


# ─────────────────────────── Ai được tính ───────────────────────────

def test_chi_nguoi_giu_vai_tro_co_o_duyet_moi_duoc_giao(db):
    a, _ = _person(db, "DP01", _role(db, "booking_dispatcher"))
    _person(db, "XEM01", _role(db, "booking_viewer", approve=False))
    _person(db, "DAU01", _role(db, "seal_approver", entity="seal_request"))

    assert resolve(db, _node(), _subject(db), None) == [a.id]


@pytest.mark.parametrize("scope", ["own", "assigned", "proc", "dept_proc"])
def test_pham_vi_khong_phu_phieu_moi_cua_nguoi_khac_thi_khong_tinh(db, scope):
    """Local 23/10: 7 «Quản lý thu mua» có Duyệt đặt xe phạm vi «Của mình» (seed cấp mọi khóa) hiện
    thành người giữ quyền dù không bao giờ được giao. Đặt xe «Được giao» = người tạo / tài xế được phân."""
    narrow = _role(db, f"r_{scope}", scope=scope)
    _person(db, "TM01", narrow)
    a, _ = _person(db, "DP01", _role(db, "booking_dispatcher"), narrow)

    assert resolve(db, _node(), _subject(db), None) == [a.id]
    rows = permission_approvers.holder_profiles(db, "vehicle_booking")
    assert [r["employee_id"] for r in rows] == [a.id]
    assert [g["scope"] for g in rows[0]["roles"]] == ["all"]


def test_khong_tinh_vai_tro_admin_nhung_admin_giu_them_vai_tro_duyet_thi_van_tinh(db):
    admin = _role(db, "admin")
    _person(db, "AD01", admin)
    both, _ = _person(db, "AD02", admin, _role(db, "booking_dispatcher"))

    assert resolve(db, _node(), _subject(db), None) == [both.id]


def test_review_c1_grant_admin_khong_lot_lai_qua_buoc_soi_pham_vi(db):
    """Review C1: soi phạm vi bằng NGUYÊN hồ sơ quyền thì grant admin «Tất cả» mở luôn phiếu công ty 5
    cho điều phối phạm vi công ty 3."""
    admin = _role(db, "admin")
    company_scope = _role(db, "dispatcher_company", scope="company")
    _person(db, "AD01", admin, company_scope, company_id=3)

    assert resolve(db, _node(), _subject(db, company_id=5), None) == []


def test_review_c1_grant_cua_minh_khong_mo_phieu_minh_tao_ho_cong_ty_khac(db):
    company_scope = _role(db, "dispatcher_company", scope="company")
    own = _role(db, "pur_manager", scope="own")
    _, user = _person(db, "DP01", company_scope, own, company_id=3)

    assert resolve(db, _node(), _subject(db, company_id=5, created_by=user.id), None) == []


def test_tai_khoan_khoa_chua_gan_ho_so_hoac_da_nghi_thi_bo(db):
    dispatcher = _role(db, "booking_dispatcher")
    ok, _ = _person(db, "DP01", dispatcher)
    _person(db, "DP02", dispatcher, active=False)
    _person(db, "DP03", dispatcher, with_employee=False)
    gone, _ = _person(db, "DP04", dispatcher)
    gone.is_active = False
    db.flush()

    assert resolve(db, _node(), _subject(db), None) == [ok.id]


def test_pham_vi_cong_ty_chi_nhan_phieu_cua_cong_ty_minh(db):
    company_scope = _role(db, "dispatcher_company", scope="company")
    in_a, _ = _person(db, "A01", company_scope, company_id=3)
    _person(db, "B01", company_scope, company_id=5)
    everywhere, _ = _person(db, "ALL01", _role(db, "dispatcher_all"), company_id=5)

    assert resolve(db, _node(), _subject(db, company_id=3), None) == [in_a.id, everywhere.id]


def test_review_m1_khong_co_id_phieu_thi_tra_rong_khong_doan(db):
    _person(db, "A01", _role(db, "dispatcher_company", scope="company"), company_id=3)

    assert resolve(db, _node(), {}, None) == []
    assert resolve(db, _node(), {"id": "abc"}, None) == []


@pytest.mark.parametrize("ref", ["", "khong_co_khoa_nay", "document", "seal_request", "employee"])
def test_review_h1_h2_m2_loai_chung_tu_chua_mo_thi_tra_rong(db, ref):
    _person(db, "DP01", _role(db, "r", entity=ref or "vehicle_booking"))

    assert resolve(db, _node(ref), {"id": 1}, None) == []
    assert permission_approvers.holder_profiles(db, ref) == []


def test_mot_nguoi_nhieu_vai_tro_chi_ra_mot_lan(db):
    a, _ = _person(db, "DP01", _role(db, "booking_dispatcher"), _role(db, "booking_manager"))

    assert resolve(db, _node(), _subject(db), None) == [a.id]


def test_nguoi_nop_cung_giu_quyen_duyet_thi_khong_tu_duyet_phieu_minh(db):
    from app.modules.approval.instance_service import exclude_submitter_ids

    dispatcher = _role(db, "booking_dispatcher")
    a, _ = _person(db, "DP01", dispatcher)
    b, _ = _person(db, "DP02", dispatcher)

    raw = resolve(db, _node(), _subject(db), a.id)
    assert exclude_submitter_ids(APPROVER_PERMISSION, a.id, raw) == [b.id]


# ─────────────────────────── Khai luồng ───────────────────────────

def test_luu_buoc_may_chu_tu_ghi_khoa_quyen_bang_loai_chung_tu_cua_luong():
    flow = SimpleNamespace(entity="vehicle_booking")
    values = _node_values(flow, NodeIn(seq=1, approver_kind=APPROVER_PERMISSION, approver_ref="employee"))
    assert values["approver_ref"] == "vehicle_booking"

    values = _node_values(flow, NodeIn(seq=1, approver_kind=APPROVER_ROLE, approver_ref="booking_manager"))
    assert values["approver_ref"] == "booking_manager"


@pytest.mark.parametrize("entity", ["document", "seal_request", "purchase_request", "khong_co"])
def test_review_h1_h2_luong_chua_mo_cach_9_thi_422(entity):
    with pytest.raises(HTTPException) as err:
        _node_values(SimpleNamespace(entity=entity), NodeIn(seq=1, approver_kind=APPROVER_PERMISSION))
    assert err.value.status_code == 422


def _flow_with_permission_step(db, entity="vehicle_booking"):
    flow = ApprovalFlow(entity=entity, code="LQ", name="Theo quyền", is_active=True, created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Duyệt", approver_kind=APPROVER_PERMISSION,
                        approver_ref=entity, created_by=1, updated_by=1))
    db.flush()
    return flow


def test_review_c2_doi_loai_chung_tu_cua_luong_thi_khoa_quyen_di_theo(db):
    flow = _flow_with_permission_step(db)
    _resync_permission_steps(db, flow, "leave_request")
    assert db.query(ApprovalNode).filter_by(flow_id=flow.id).one().approver_ref == "leave_request"


def test_review_c2_doi_sang_loai_chua_mo_cach_9_thi_chan(db):
    flow = _flow_with_permission_step(db)
    with pytest.raises(HTTPException) as err:
        _resync_permission_steps(db, flow, "seal_request")
    assert err.value.status_code == 422
    assert db.query(ApprovalNode).filter_by(flow_id=flow.id).one().approver_ref == "vehicle_booking"


def test_options_bay_lua_chon_thu_chin_kem_danh_sach_loai_dung_duoc():
    data = options(user=None).body.decode()
    assert "Người có quyền duyệt (theo phân quyền)" in data
    assert '"permission_approver_entities":["vehicle_booking","leave_request","room_booking"]' in data


def test_review_m3_duong_danh_sach_khong_cho_do_khoa_khac(db):
    for entity in ("employee", "labor_contract", "document"):
        with pytest.raises(HTTPException) as err:
            permission_approvers_of(entity, db=db, user=None)
        assert err.value.status_code == 404


def test_danh_sach_nguoi_giu_quyen_kem_vai_tro_va_pham_vi(db):
    a, _ = _person(db, "DP01", _role(db, "booking_dispatcher", scope="all"),
                   _role(db, "booking_manager", scope="company"))
    _person(db, "AD01", _role(db, "admin"))

    rows = permission_approvers.holder_profiles(db, "vehicle_booking")
    assert [r["employee_id"] for r in rows] == [a.id]
    assert {(g["role"], g["scope"], g["scope_label"]) for g in rows[0]["roles"]} == {
        ("Vai trò booking_dispatcher", "all", "Tất cả"), ("Vai trò booking_manager", "company", "Công ty")}


def test_nhan_quy_tac_tren_xem_truoc(db):
    assert _rule_label(db, _node()) == "Người có quyền duyệt (theo phân quyền): quyền Duyệt «Phiếu đặt xe»"


# ─────────────────────────── Chạy thật trong bộ máy ───────────────────────────

def test_phieu_dat_xe_chay_that_giao_viec_cho_dieu_phoi_cung_cong_ty_roi_duyet_xong(db):
    from app.modules.approval import action_service, instance_service
    from app.modules.approval.flow_model import SKIP_NONE
    from app.modules.approval.instance_model import INSTANCE_APPROVED, INSTANCE_RUNNING, TASK_PENDING

    company_scope = _role(db, "dispatcher_company", scope="company")
    in_a, _ = _person(db, "A01", company_scope, company_id=3)
    _person(db, "B01", company_scope, company_id=5)
    submitter, _ = _person(db, "NV01", company_id=3)
    booking = _booking(db, company_id=3)
    flow = ApprovalFlow(entity="vehicle_booking", code="LUONG-QUYEN", name="Theo quyền duyệt",
                        is_active=True, created_by=1, updated_by=1)
    db.add(flow)
    db.commit()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Điều phối duyệt", approver_kind=APPROVER_PERMISSION,
                        approver_ref="vehicle_booking", skip_duplicate=SKIP_NONE, created_by=1, updated_by=1))
    db.commit()

    instance = instance_service.start(db, "vehicle_booking", booking.id, {"id": booking.id, "company_id": 3},
                                      submitter.id, 1, entity_code=booking.code, entity_title="Thử theo quyền")
    assert instance.status == INSTANCE_RUNNING
    pending = [t for t in instance_service.tasks_of_instance(db, instance.id) if t.status == TASK_PENDING]
    assert [t.assignee_employee_id for t in pending] == [in_a.id]
    action_service.approve(db, instance, in_a.id, 1, {})
    assert instance.status == INSTANCE_APPROVED


def test_so_truy_van_khi_bo_dem_quyen_nong_khong_tang_theo_so_nguoi_giu_quyen(db):
    """Ép tải MySQL 23/10: bản đầu soi phạm vi từng người một — 200 người = 205 truy vấn. Gom một truy vấn."""
    from sqlalchemy import event

    def count_resolve(subject):
        resolve(db, _node(), subject, None)       # làm nóng bộ đệm quyền
        hits = []
        listener = lambda *_a, **_k: hits.append(1)  # noqa: E731
        event.listen(db.bind, "before_cursor_execute", listener)
        try:
            out = resolve(db, _node(), subject, None)
        finally:
            event.remove(db.bind, "before_cursor_execute", listener)
        return len(hits), out

    role = _role(db, "dispatcher_company", scope="company")
    for i in range(3):
        _person(db, f"A{i:02d}", role)
    few, out_few = count_resolve(_subject(db))
    for i in range(3, 40):
        _person(db, f"A{i:02d}", role)
    many, out_many = count_resolve(_subject(db, created_by=998))
    assert (len(out_few), len(out_many)) == (3, 40)
    assert many == few, (few, many)
