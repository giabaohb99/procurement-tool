"""duoc-CR-681 — phiếu đặt xe tự chọn Công ty và Người duyệt; thư «Gửi duyệt» tới đúng người được chọn.

- Danh sách người duyệt = người có quyền Duyệt đặt xe (Phòng ban / Công ty / Tất cả, không admin) — CR-680.
- Công ty và Người duyệt ĐỘC LẬP: chọn điều phối phạm vi công ty 5 cho phiếu công ty 3 vẫn hợp lệ.
- Bộ máy TẮT: thư + chuông `dx_submitted` chỉ tới người được chọn. Bộ máy BẬT, bước «Người có quyền
  duyệt»: chỉ người được chọn nhận việc + có thư (`EmailLog`).
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.approval.flow_model import (APPROVER_PERMISSION, SKIP_NONE, ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import TASK_PENDING, ApprovalTask
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.notification.model import EmailLog, Notification
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking import approver_picker
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import VehicleBookingCreate, VehicleBookingUpdate
from app.modules.vehicle_booking.service import create_booking, update_booking


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


def _account(db, code, *roles, company_id=3, active=True):
    emp = Employee(code=code, full_name=f"Nhân sự {code}", email=f"{code.lower()}@dego.vn",
                   company_id=company_id, department_id=7, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@dego.vn", employee_id=emp.id, is_active=active)
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return user


@pytest.fixture()
def org(db):
    for cid in (3, 5):
        if db.get(Company, cid) is None:
            db.add(Company(id=cid, code=f"CT{cid}", name=f"Công ty {cid}"))
    db.flush()
    dispatch_company = _role(db, "dispatcher_company", scope="company")
    dispatch_all = _role(db, "dispatcher_all", scope="all")
    own = _role(db, "pur_manager", scope="own")
    creator = _account(db, "NV01", _role(db, "staff", approve=False))
    picked = _account(db, "DP05", dispatch_company, company_id=5)   # phạm vi công ty KHÁC phiếu
    other = _account(db, "DP99", dispatch_all)
    own_only = _account(db, "TM01", own)
    admin = _account(db, "AD01", _role(db, "admin"))
    db.commit()
    return SimpleNamespace(creator=creator, picked=picked, other=other, own_only=own_only, admin=admin)


def _payload(**over):
    data = dict(request_type=1, purpose="Đi công tác", start_location="VP", end_location="Q7",
                start_time="2026-11-01T08:00", end_time="2026-11-01T10:00", passenger_count=1)
    data.update(over)
    return VehicleBookingCreate(**data)


# ─────────────────────────── Danh sách người duyệt ───────────────────────────

def test_o_chon_tren_phieu_trung_dung_danh_sach_man_khai_luong(db, org):
    """Anh Được 26/10 (dev): bước «Người có quyền duyệt» hiện 3 người mà ô chọn trên phiếu hiện nhiều hơn (bản 24/10
    nới ra mọi phạm vi + Quản trị). Hai nơi phải ra CÙNG một danh sách: không Quản trị, không phạm vi «Của mình»."""
    from app.modules.approval import permission_approvers

    rows = approver_picker.approver_options(db)
    assert {r["user_id"] for r in rows} == {org.picked.id, org.other.id}
    assert [r["employee_id"] for r in rows] == [
        r["employee_id"] for r in permission_approvers.holder_profiles(db, "vehicle_booking")]
    picked = next(r for r in rows if r["user_id"] == org.picked.id)
    assert picked["employee_id"] == org.picked.employee_id
    assert picked["roles"][0]["scope_label"] == "Công ty"


def test_danh_sach_cong_ty_bo_cong_ty_ngung_dung_va_tra_mac_dinh(db, org):
    db.add(Company(id=9, code="CT9", name="Công ty đã đóng", is_active=False))
    db.commit()
    data = approver_picker.pick_options(db, 3)
    assert {c["id"] for c in data["companies"]} == {3, 5}
    assert data["default_company_id"] == 3
    assert {a["user_id"] for a in data["approvers"]} == {org.picked.id, org.other.id}


def test_cong_ty_ngung_dung_thi_422_nhung_phieu_cu_giu_cong_ty_do_van_sua_duoc(db, org):
    db.add(Company(id=9, code="CT9", name="Công ty đã đóng", is_active=True))
    db.commit()
    booking = create_booking(db, _payload(company_id=9), org.creator, submit=False)
    db.get(Company, 9).is_active = False
    db.commit()
    with pytest.raises(HTTPException):
        create_booking(db, _payload(company_id=9), org.creator, submit=False)
    update_booking(db, booking, VehicleBookingUpdate(company_id=9, purpose="Sửa"), org.creator, submit=False)
    assert booking.company_id == 9


def test_tai_khoan_khoa_khong_vao_danh_sach(db, org):
    org.other.is_active = False
    db.commit()
    assert org.other.id not in [r["user_id"] for r in approver_picker.approver_options(db)]


# ─────────────────────────── Chốt lúc lưu / gửi ───────────────────────────

def test_luu_phieu_chon_cong_ty_va_nguoi_duyet_doc_lap(db, org):
    booking = create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator,
                             submit=False)
    assert (booking.company_id, booking.first_approver_id) == (3, org.picked.id)


def test_tu_chon_minh_thi_422(db, org):
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(first_approver_id=org.creator.id), org.creator, submit=False)
    assert err.value.status_code == 422


def test_nguoi_khong_co_o_duyet_thi_422(db, org):
    plain = _account(db, "NV02", _role(db, "staff2", approve=False))
    db.commit()
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(first_approver_id=plain.id), org.creator, submit=False)
    assert err.value.status_code == 422


@pytest.mark.parametrize("who", ["own_only", "admin"])
def test_quan_tri_hoac_pham_vi_cua_minh_khong_chon_duoc(db, org, who):
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(first_approver_id=getattr(org, who).id), org.creator, submit=False)
    assert err.value.status_code == 422

def test_id_tai_khoan_khong_ton_tai_hoac_am_thi_422(db, org):
    for bad in (987654, -5):
        with pytest.raises(HTTPException) as err:
            create_booking(db, _payload(first_approver_id=bad), org.creator, submit=False)
        assert err.value.status_code == 422


def test_cong_ty_khong_ton_tai_thi_422(db, org):
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(company_id=424242), org.creator, submit=False)
    assert err.value.status_code == 422


def test_gui_phieu_nhap_khi_nguoi_duyet_da_mat_quyen_thi_422(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=False)
    db.query(UserRole).filter_by(user_id=org.picked.id).delete()
    db.commit()
    perm_cache_clear()
    with pytest.raises(HTTPException) as err:
        update_booking(db, booking, VehicleBookingUpdate(purpose="Đổi mục đích"), org.creator, submit=True)
    assert err.value.status_code == 422
    db.refresh(booking)
    assert booking.status == m.BK_DRAFT


def test_sua_nhap_khong_doi_nguoi_duyet_khong_kiem_lai(db, org):
    """Lưu nháp sửa ô khác không bắt chọn lại người duyệt — chỉ kiểm khi đổi ô đó hoặc gửi."""
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=False)
    db.query(UserRole).filter_by(user_id=org.picked.id).delete()
    db.commit()
    update_booking(db, booking, VehicleBookingUpdate(purpose="Sửa"), org.creator, submit=False)
    assert booking.purpose == "Sửa"


# ─────────────────────────── Bộ máy TẮT: thư đường cũ ───────────────────────────

def test_bo_may_tat_chuong_va_thu_chi_toi_nguoi_duoc_chon(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert booking.status == m.BK_PENDING
    assert {n.user_id for n in db.query(Notification).filter(Notification.link.like("%/vehicle-booking/%"))} == {
        org.picked.id}
    assert [e.to_email for e in db.query(EmailLog).filter_by(event="dx_submitted")] == [org.picked.email]


def test_bo_may_tat_chua_chon_thi_giu_duong_cu(db, org):
    booking = create_booking(db, _payload(), org.creator, submit=True)
    assert booking.first_approver_id == 0
    #  Không TBP phòng 7 → lùi về người có quyền duyệt đặt xe (luật cũ, gồm cả admin / «Của mình»).
    assert org.picked.id in {n.user_id for n in db.query(Notification)}


# ─────────────────────────── Bộ máy BẬT: bước cách 9 ───────────────────────────

def _engine_with_permission_step(db):
    db.add(ApprovalSwitch(entity="vehicle_booking", is_enabled=True))
    flow = ApprovalFlow(entity="vehicle_booking", code="DX-Q", name="Duyệt theo quyền", is_active=True,
                        created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Điều phối duyệt", approver_kind=APPROVER_PERMISSION,
                        approver_ref="vehicle_booking", skip_duplicate=SKIP_NONE, created_by=1, updated_by=1))
    db.commit()


def _pending_assignees(db, booking):
    from app.modules.approval.instance_model import ApprovalInstance

    instance_ids = [i.id for i in db.query(ApprovalInstance).filter_by(entity="vehicle_booking",
                                                                       entity_id=booking.id)]
    return [t.assignee_employee_id for t in db.query(ApprovalTask)
            .filter(ApprovalTask.instance_id.in_(instance_ids), ApprovalTask.status == TASK_PENDING)]


def test_bo_may_bat_buoc_theo_quyen_chi_giao_nguoi_duoc_chon_va_gui_thu(db, org):
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator,
                             submit=True)
    #  Người được chọn phạm vi CÔNG TY 5, phiếu công ty 3 — vẫn nhận vì hai ô độc lập.
    assert _pending_assignees(db, booking) == [org.picked.employee_id]
    assert [e.to_email for e in db.query(EmailLog).filter_by(event="dx_submitted")] == [org.picked.email]


def test_bo_may_bat_chua_chon_thi_buoc_theo_quyen_tinh_nhu_cu(db, org):
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(company_id=3), org.creator, submit=True)
    #  Không chọn → mọi người giữ quyền mà phạm vi phủ phiếu công ty 3: chỉ điều phối «Tất cả».
    assert _pending_assignees(db, booking) == [org.other.employee_id]
    assert [e.to_email for e in db.query(EmailLog).filter_by(event="dx_submitted")] == [org.other.email]


def test_nguoi_duoc_chon_mat_quyen_giua_chung_thi_bo_lua_chon_khong_ket_phieu(db, org):
    from app.modules.approval import permission_approvers

    db.query(UserRole).filter_by(user_id=org.picked.id).delete()
    db.commit()
    booking = m.VehicleBooking(code="DX-T", company_id=3, department_id=0, created_by=1, purpose="x")
    db.add(booking)
    db.flush()
    subject = {"id": booking.id, "picked_approver_employee_id": org.picked.employee_id}
    assert permission_approvers.resolve(db, "vehicle_booking", subject) == [org.other.employee_id]


def test_thu_chi_gui_mot_lan_khi_ai_cung_khong_co_email(db, org):
    org.picked.email = ""
    db.commit()
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert _pending_assignees(db, booking) == [org.picked.employee_id]
    assert db.query(EmailLog).filter_by(event="dx_submitted").count() == 0


# ─────────────────────────── Review CR-681 ───────────────────────────

def test_review_h1_duong_cu_nguoi_duoc_chon_xem_va_duyet_duoc_du_ngoai_pham_vi(db, org):
    """Review H1: thư chỉ tới người được chọn mà họ (phạm vi công ty 5) mở phiếu công ty 3 ra 404, bấm Duyệt 404."""
    from app.modules.vehicle_booking import approval_bridge
    from app.modules.vehicle_booking.controller import _scoped_or_404
    from app.modules.vehicle_booking.service import approve_booking

    booking = create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator, submit=True)
    assert approval_bridge.booking_for_approver(db, booking.id, org.picked) is booking
    assert approval_bridge._can_read_booking(db, booking.id, org.picked)
    obj = _scoped_or_404(db, booking.id, org.picked, "approve")
    approve_booking(db, obj, org.picked)
    assert booking.status == m.BK_APPROVED
    #  Duyệt xong là cửa nới đóng lại.
    assert approval_bridge.booking_for_approver(db, booking.id, org.picked) is None


def test_review_h1_cua_noi_chi_cho_dung_nguoi_duoc_chon(db, org):
    from app.modules.vehicle_booking import approval_bridge
    from app.modules.vehicle_booking.controller import _scoped_or_404

    other_company5 = _account(db, "DP06", db.query(Role).filter_by(code="dispatcher_company").one(), company_id=5)
    db.commit()
    booking = create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator, submit=True)
    assert approval_bridge.booking_for_approver(db, booking.id, other_company5) is None
    with pytest.raises(HTTPException) as err:
        _scoped_or_404(db, booking.id, other_company5, "approve")
    assert err.value.status_code == 404
    #  Cửa nới chỉ cho hành động duyệt, không cho sửa / điều phối.
    with pytest.raises(HTTPException):
        _scoped_or_404(db, booking.id, org.picked, "write")


def test_review_h1_bo_may_dang_chay_thi_khong_noi_theo_duong_cu(db, org):
    from app.modules.vehicle_booking import approval_bridge

    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator, submit=True)
    assert not approval_bridge.is_picked_legacy_approver(db, booking, org.picked)
    #  …nhưng vẫn đọc được qua việc đang treo.
    assert approval_bridge.booking_for_approver(db, booking.id, org.picked) is booking


def test_review_m1_ho_so_da_nghi_viec_khong_chon_duoc_va_khong_vao_danh_sach(db, org):
    db.query(Employee).filter_by(id=org.picked.employee_id).one().is_active = False
    db.commit()
    assert org.picked.id not in {r["user_id"] for r in approver_picker.approver_options(db)}
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=False)
    assert err.value.status_code == 422


def test_review_m2_nguoi_sua_ho_tu_chon_minh_roi_gui_thi_422(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.other.id), org.creator, submit=False)
    with pytest.raises(HTTPException) as err:
        update_booking(db, booking, VehicleBookingUpdate(first_approver_id=org.picked.id), org.picked, submit=True)
    assert err.value.status_code == 422


def test_review_m2_hai_tai_khoan_cung_mot_ho_so_van_la_tu_chon(db, org):
    second = User(email="nv01-2@dego.vn", employee_id=org.picked.employee_id, is_active=True)
    db.add(second)
    db.commit()
    with pytest.raises(HTTPException) as err:
        create_booking(db, _payload(first_approver_id=org.picked.id), second, submit=False)
    assert err.value.status_code == 422


def test_review_m4_luu_nhap_gui_lai_dung_nguoi_cu_da_mat_quyen_khong_chan(db, org):
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=False)
    db.query(UserRole).filter_by(user_id=org.picked.id).delete()
    db.commit()
    update_booking(db, booking, VehicleBookingUpdate(first_approver_id=org.picked.id, purpose="Sửa"), org.creator,
                   submit=False)
    assert booking.purpose == "Sửa"


def test_ten_nguoi_duyet_da_chon_tach_khoi_nguoi_da_ky(db, org):
    from app.modules.vehicle_booking.service import serialize_booking

    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=False)
    booking.approved_by = org.other.id
    db.commit()
    out = serialize_booking(db, booking)
    assert out["first_approver_name"] == "Nhân sự DP05"
    assert out["approver_name"] == "Nhân sự DP99"


# ─────────── Anh Được 24/10: chọn công ty khác thì CẢ HAI bên vẫn thấy phiếu (luồng «Người có quyền duyệt») ───────────

def _can_see(db, user, booking_id, action="read"):
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped

    perm_cache_clear()
    return get_scoped(db, m.VehicleBooking, "vehicle_booking", booking_id, user,
                      get_perm_profile(db, user), action) is not None


def test_chon_cong_ty_khac_thi_pham_vi_cong_ty_o_ca_hai_ben_deu_thay(db, org):
    """Người tạo công ty 3 chọn công ty 5: điều phối phạm vi công ty ở 3 LẪN 5 đều thấy và duyệt được; công ty 7 thì không."""
    db.add(Company(id=7, code="CT7", name="Công ty 7"))
    viewer_role = db.query(Role).filter_by(code="dispatcher_company").one()
    in_creator_company = _account(db, "DP03", viewer_role, company_id=3)
    in_other = _account(db, "DP07", viewer_role, company_id=7)
    db.commit()
    _engine_with_permission_step(db)

    booking = create_booking(db, _payload(company_id=5, first_approver_id=org.picked.id), org.creator, submit=True)
    assert (booking.company_id, booking.requester_company_id) == (5, 3)
    assert _can_see(db, in_creator_company, booking.id)
    assert _can_see(db, org.picked, booking.id)               # phạm vi công ty 5 = công ty chọn trên phiếu
    assert _can_see(db, in_creator_company, booking.id, "approve")
    assert not _can_see(db, in_other, booking.id)
    #  Bước «Người có quyền duyệt» vẫn giao ĐÚNG người được chọn, có thư.
    assert _pending_assignees(db, booking) == [org.picked.employee_id]


def test_chua_chon_nguoi_thi_buoc_theo_quyen_giao_ca_hai_cong_ty(db, org):
    viewer_role = db.query(Role).filter_by(code="dispatcher_company").one()
    in_creator_company = _account(db, "DP03", viewer_role, company_id=3)
    db.commit()
    _engine_with_permission_step(db)

    booking = create_booking(db, _payload(company_id=5), org.creator, submit=True)
    assert set(_pending_assignees(db, booking)) == {
        org.picked.employee_id, in_creator_company.employee_id, org.other.employee_id}


def test_danh_sach_dat_xe_cua_dieu_phoi_hai_ben_deu_co_phieu(db, org):
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope

    viewer_role = db.query(Role).filter_by(code="dispatcher_company").one()
    in_creator_company = _account(db, "DP03", viewer_role, company_id=3)
    db.commit()
    booking = create_booking(db, _payload(company_id=5, first_approver_id=org.picked.id), org.creator, submit=False)
    for user in (in_creator_company, org.picked):
        perm_cache_clear()
        ids = [b.id for b in apply_scope(db.query(m.VehicleBooking), m.VehicleBooking, "vehicle_booking", user,
                                         get_perm_profile(db, user))]
        assert booking.id in ids


def test_o_chon_cong_ty_cua_nguoi_dung_khop_ca_cong_ty_nguoi_tao(db, org):
    """Giới hạn «chọn công ty» gán riêng cho người (UserScope) cũng khớp cột pháp nhân người tạo."""
    from app.modules.user.model import UserScope

    role = db.query(Role).filter_by(code="dispatcher_all").one()
    limited = _account(db, "DPL", role, company_id=9)
    db.add(UserScope(user_id=limited.id, role_id=role.id, dim="company", value="3", is_exclude=False))
    db.commit()
    booking = create_booking(db, _payload(company_id=5), org.creator, submit=False)
    assert _can_see(db, limited, booking.id)


# ─────────── Anh Được 24/10: thư cho MỌI chặng + người nhận ủy quyền ───────────

def _two_stage_flow(db, second_employee_id):
    from app.modules.approval.flow_model import APPROVER_EMPLOYEE

    db.add(ApprovalSwitch(entity="vehicle_booking", is_enabled=True))
    flow = ApprovalFlow(entity="vehicle_booking", code="DX-2", name="Hai chặng", is_active=True,
                        created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add_all([
        ApprovalNode(flow_id=flow.id, seq=1, name="Điều phối duyệt", approver_kind=APPROVER_PERMISSION,
                     approver_ref="vehicle_booking", skip_duplicate=SKIP_NONE, created_by=1, updated_by=1),
        ApprovalNode(flow_id=flow.id, seq=2, name="Giám đốc duyệt", approver_kind=APPROVER_EMPLOYEE,
                     approver_ref=str(second_employee_id), skip_duplicate=SKIP_NONE, created_by=1, updated_by=1),
    ])
    db.commit()


def _mails(db, to):
    return db.query(EmailLog).filter_by(event="dx_submitted", to_email=to).count()


def test_thu_toi_chang_sau_khi_chang_truoc_duyet_xong(db, org, email_queue_sent):
    from app.modules.approval import action_service
    from app.modules.approval.instance_model import ApprovalInstance

    director = _account(db, "GD01", company_id=3)
    db.commit()
    _two_stage_flow(db, director.employee_id)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert (_mails(db, org.picked.email), _mails(db, director.email)) == (1, 0)

    instance = db.query(ApprovalInstance).filter_by(entity="vehicle_booking", entity_id=booking.id).one()
    action_service.approve(db, instance, org.picked.employee_id, org.picked.id, {})
    db.commit()
    assert _pending_assignees(db, booking) == [director.employee_id]
    assert _mails(db, director.email) == 1
    #  Đẩy sang worker SAU commit, đúng một lần mỗi thư.
    assert sorted(j["to_email"] for j in email_queue_sent) == sorted([org.picked.email, director.email])


def test_thu_toi_ca_nguoi_nhan_uy_quyen(db, org):
    from datetime import date, timedelta

    from app.modules.approval.delegation_model import Delegation

    deputy = _account(db, "PGD01", company_id=3)
    db.add(Delegation(from_employee_id=org.picked.employee_id, to_employee_id=deputy.employee_id,
                      entity="vehicle_booking", from_date=date.today() - timedelta(days=1),
                      to_date=date.today() + timedelta(days=1), is_active=True, created_by=1, updated_by=1))
    db.commit()
    _engine_with_permission_step(db)
    create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert (_mails(db, org.picked.email), _mails(db, deputy.email)) == (1, 1)


def test_mau_thu_tat_thi_bo_may_khong_xep_thu(db, org, email_queue_sent):
    from app.modules.notification import email_template_service as ets

    ets.upsert(db, "dx_submitted", enabled=False, subject="x", body_html="x", user=SimpleNamespace(id=1))
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert _pending_assignees(db, booking) == [org.picked.employee_id]   # việc vẫn giao, chuông vẫn có
    assert db.query(EmailLog).count() == 0 and email_queue_sent == []


def test_giao_dich_huy_thi_khong_day_thu_nao(db, org, email_queue_sent):
    from app.modules.notification.email_queue import queue_event_email

    queue_event_email(db, "dx_submitted", [org.picked], {"code": "DX1"})
    db.rollback()
    db.commit()
    assert email_queue_sent == [] and db.query(EmailLog).count() == 0


def test_day_sang_worker_loi_khong_lam_hong_nghiep_vu(db, org, monkeypatch):
    from app.modules.notification import email_queue

    def boom(_job):
        raise ConnectionError("redis chết")

    monkeypatch.setattr(email_queue, "dispatch", boom)
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(first_approver_id=org.picked.id), org.creator, submit=True)
    assert _pending_assignees(db, booking) == [org.picked.employee_id]
    assert db.query(EmailLog).filter_by(to_email=org.picked.email).one().status == "pending"


# ─────────── Review lượt 2 ───────────

def test_review2_nha_savepoint_khong_day_thu_truoc_commit_ngoai(db, org, email_queue_sent):
    from app.modules.notification.email_queue import queue_event_email

    queue_event_email(db, "dx_submitted", [org.picked], {"code": "DX-OUT"})
    with db.begin_nested():
        queue_event_email(db, "dx_submitted", [org.other], {"code": "DX-IN"})
    assert email_queue_sent == []          # mới nhả savepoint, giao dịch ngoài chưa commit
    db.commit()
    assert sorted(j["to_email"] for j in email_queue_sent) == sorted([org.picked.email, org.other.email])


def test_review2_huy_savepoint_khong_xoa_thu_cua_giao_dich_ngoai(db, org, email_queue_sent):
    from app.modules.notification.email_queue import queue_event_email

    queue_event_email(db, "dx_submitted", [org.picked], {"code": "DX-OUT"})
    nested = db.begin_nested()
    queue_event_email(db, "dx_submitted", [org.other], {"code": "DX-IN"})
    nested.rollback()
    db.commit()
    sent = {j["to_email"]: j["log_id"] for j in email_queue_sent}
    assert org.picked.email in sent
    #  Thư của savepoint đã hủy có thể vẫn được đẩy, nhưng dòng EmailLog của nó không còn → worker bỏ qua.
    if org.other.email in sent:
        assert db.get(EmailLog, sent[org.other.email]) is None
    assert db.query(EmailLog).filter_by(to_email=org.picked.email).count() == 1


def test_review2_tieu_de_mau_qua_dai_khong_lam_hong_luot_duyet(db, org):
    from app.modules.notification import email_template_service as ets

    ets.upsert(db, "dx_submitted", enabled=True, subject="YCĐX {{ code }} — {{ purpose }}",
               body_html="<p>{{ purpose }}</p>", user=SimpleNamespace(id=1))
    _engine_with_permission_step(db)
    booking = create_booking(db, _payload(purpose="x" * 600, first_approver_id=org.picked.id), org.creator,
                             submit=True)
    assert _pending_assignees(db, booking) == [org.picked.employee_id]
    assert len(db.query(EmailLog).filter_by(to_email=org.picked.email).one().subject) == 255


def test_review2_hai_tai_khoan_chung_hop_thu_chi_mot_thu(db, org, email_queue_sent):
    from app.modules.notification.email_queue import queue_event_email

    twin = User(email=org.picked.email, employee_id=org.picked.employee_id, is_active=True)
    db.add(twin)
    db.flush()
    assert queue_event_email(db, "dx_submitted", [org.picked, twin], {"code": "DX1"}) == 1


def test_review2_pham_vi_phong_ban_thay_phieu_chon_cong_ty_khac(db, org):
    from app.modules.department.model import Department

    db.add(Department(id=7, code="P7", name="Phòng 7", company_id=3))
    dept_role = _role(db, "booking_dept", scope="dept", approve=False)
    colleague = _account(db, "NV07", dept_role, company_id=3)     # cùng phòng 7, công ty 3 với người tạo
    db.commit()
    booking = create_booking(db, _payload(company_id=5), org.creator, submit=False)
    assert (booking.company_id, booking.requester_company_id, booking.department_id) == (5, 3, 7)
    assert _can_see(db, colleague, booking.id)


def test_review2_dong_bo_app_cu_khong_ghi_de_cong_ty_nguoi_tao():
    from app.modules.legacy_datxe.builder import LEGACY_READONLY_FIELDS

    assert "requester_company_id" in LEGACY_READONLY_FIELDS


def test_chi_tiet_phieu_tra_nguoi_phe_duyet_va_cong_ty_de_hien_tren_trang(db, org):
    """Anh Được 26/10: chi tiết phiếu hiện người phê duyệt («Mã - Tên» + ảnh) và công ty (logo)."""
    from app.modules.vehicle_booking.service import serialize_booking

    booking = create_booking(db, _payload(company_id=5, first_approver_id=org.picked.id), org.creator, submit=False)
    out = serialize_booking(db, booking)
    assert (out["first_approver_code"], out["first_approver_name"]) == ("DP05", "Nhân sự DP05")
    assert out["company_name"] == "Công ty 5"
    assert "first_approver_avatar" in out and "company_logo" in out

    empty = serialize_booking(db, create_booking(db, _payload(), org.creator, submit=False))
    assert empty["first_approver_code"] == "" and empty["first_approver_name"] == ""
