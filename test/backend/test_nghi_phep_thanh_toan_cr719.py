"""duoc-CR-719 phase 03 — PHIẾU THANH TOÁN NGHỈ PHÉP: toán, lập, gửi/duyệt qua bộ máy THẬT, hủy theo YCTT, chặn tự duyệt,
phạm vi, ẩn số tiền, chuông, nối dây và `my_leave_summary` (chỉ ngày, không tiền).
"""
import json
import time
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.core.reference_guard import count_references
from app.core.vn_time import vn_today
from app.modules.approval import action_service, instance_service
from app.modules.approval import permission_approvers, report_service, task_notification
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalFlow, ApprovalNode, ApprovalSwitch
from app.modules.approval.self_approval_policy import ensure_not_self_approval, strict_self_exclusion
from app.modules.employee.model import Employee
from app.modules.leave import balance_service, encashment_approval_bridge as bridge
from app.modules.leave import encashment_controller as ctl, encashment_math as M
from app.modules.leave import encashment_service as service, encashment_transitions as tr
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LeaveEncashmentReason as R, LeaveEncashmentStatus as S
from app.modules.leave.encashment_model import LeaveEncashment
from app.modules.leave.encashment_schema import LeaveEncashmentCreate, LeaveEncashmentUpdate
from app.modules.notification.model import Notification
from app.modules.payment_request import leave_encashment_payout as payout
from app.modules.payment_request import service as pay_service
from app.modules.payment_request.model import PaymentRequest
from app.modules.payment_request.schema import LineIn, PRequestUpdate
from app.modules.setting.model import Setting
from app.modules.user.model import User

ACTOR = 1
ENTITY = "leave_encashment"
YEAR = vn_today().year


@pytest.fixture(autouse=True)
def _settings_from_test_db(db, monkeypatch):
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


def _type(db, **kw):
    values = dict(code="annual", name="Phép năm", counts_balance=True, allow_encashment=True, annual_quota_days=12)
    values.update(kw)
    obj = LeaveType(**values)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def lt(db):
    return _type(db)


def _emp(db, code, company=1, dept=7, **kw):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=company, department_id=dept, is_active=True, **kw)
    db.add(obj)
    db.flush()
    return obj


def _user(emp, uid=50):
    return SimpleNamespace(id=uid, employee_id=emp.id)


def _balance(db, emp, lt, year=YEAR, **kw):
    values = dict(allocated_days=10.0)
    values.update(kw)
    row = LeaveBalance(employee_id=emp.id, year=year, leave_type_id=lt.id, company_id=emp.company_id or 0, **values)
    db.add(row)
    db.commit()
    return row


def _flow(db, approver):
    n = db.query(ApprovalFlow).filter(ApprovalFlow.entity == ENTITY).count()
    row = ApprovalFlow(entity=ENTITY, code=f"TTP-719-{n}", name="Duyệt thanh toán nghỉ phép", is_active=True,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(approver.id), created_by=ACTOR, updated_by=ACTOR))
    if db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == ENTITY).count() == 0:
        db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _create(db, emp, lt, days=None, **kw):
    return service.create(db, LeaveEncashmentCreate(leave_type_id=lt.id, days=days, **kw), _user(emp))


def _submit(db, obj, emp):
    user = _user(emp)
    tr.prepare_submit(db, obj, user)
    instance_id = bridge.start_approval(db, obj, user)
    obj.approval_instance_id = instance_id
    db.commit()
    db.refresh(obj)
    return obj


def _row(db, emp, lt, year=YEAR):
    return balance_service.get_balance(db, emp.id, year, lt.id)


def _engine(db, obj, approver, action="approve", reason=""):
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    if action == "approve":
        action_service.approve(db, instance, approver.id, ACTOR, {})
    elif action == "reject":
        action_service.reject(db, instance, approver.id, ACTOR, reason)
    else:
        action_service.send_back(db, instance, approver.id, ACTOR, reason, {})
    db.refresh(obj)


def _flow_case(db, lt, code="A"):
    emp, approver = _emp(db, f"E{code}"), _emp(db, f"P{code}")
    _balance(db, emp, lt)
    _flow(db, approver)
    return emp, approver, _create(db, emp, lt, days=4)


# ── toán thuần (bảng ca ERPNext) ────────────────────────────────────────────

def _enc(**kw):
    base = dict(available=10, carried_days=0, used_days=0, pending_days=0, reason_kind=int(R.YEAR_END),
                non_encashable_days=0, max_encashable_days=0, already_encashed=0)
    base.update(kw)
    return M.encashable_days(**base)


def test_toan_giu_lai_va_tran():
    assert _enc(non_encashable_days=4) == 6
    assert _enc(max_encashable_days=3) == 3
    assert _enc(non_encashable_days=4, max_encashable_days=3) == 3
    assert _enc(non_encashable_days=4, max_encashable_days=8) == 6
    assert _enc() == 10


def test_toan_mang_sang_khong_tinh_cuoi_nam_nhung_tinh_khi_nghi_viec():
    assert _enc(carried_days=5) == 5
    assert _enc(carried_days=5, used_days=3) == 8          # mang sang tiêu trước, còn 2 chưa dùng
    assert _enc(carried_days=5, reason_kind=int(R.RESIGNATION)) == 10
    assert _enc(carried_days=5, used_days=5) == 10          # mang sang đã dùng hết, không trừ gì


def test_toan_nghi_viec_bo_qua_hai_tran():
    assert _enc(reason_kind=int(R.RESIGNATION), non_encashable_days=4, max_encashable_days=3) == 10


def test_toan_tran_nam_tru_da_thanh_toan_va_lam_tron_xuong_buoc():
    assert _enc(max_encashable_days=5, already_encashed=3) == 2
    assert _enc(max_encashable_days=5, already_encashed=7) == 0
    assert _enc(available=6.25) == 6.0
    assert _enc(available=-2) == 0 and _enc(available=0) == 0      # ứng phép âm


def test_toan_cong_don_giu_phan_chua_toi_thang(db):
    from app.modules.leave.constants import LeaveAccrualMode
    t = _type(db, code="mth", accrual_mode=int(LeaveAccrualMode.MONTHLY), allow_encashment=True)
    emp = _emp(db, "MON", hire_date=date(2020, 1, 1))
    row = _balance(db, emp, t, allocated_days=12.0)
    info = service.compute(db, row, t, int(R.YEAR_END))
    assert info["available"] == balance_service.available_days(db, row)
    assert info["encashable"] <= info["available"] and info["encashable"] % 0.5 == 0


# ── lập phiếu ───────────────────────────────────────────────────────────────

def test_lap_phieu_mac_dinh_lay_so_duoc_phep(db, lt):
    lt.non_encashable_days = 4
    emp = _emp(db, "C1")
    _balance(db, emp, lt)
    obj = _create(db, emp, lt)
    assert obj.status == int(S.DRAFT) and obj.code.startswith("TTP") and obj.days == 6
    assert obj.balance_snapshot == 10 and obj.encashable_snapshot == 6
    assert obj.active_key == f"{emp.id}:{lt.id}:{YEAR}:{int(R.YEAR_END)}" and obj.encashment_date == vn_today()
    assert _row(db, emp, lt).pending_days == 0                 # nháp chưa giữ chỗ


def test_lap_phieu_chan(db, lt):
    emp = _emp(db, "C2")
    _balance(db, emp, lt)
    off = _type(db, code="off", name="Không cho", allow_encashment=False)
    no_bal = _type(db, code="nb", name="Không quỹ", counts_balance=False, allow_encashment=True)
    for kwargs, code in (({"leave_type_id": off.id}, 422), ({"leave_type_id": no_bal.id}, 422),
                         ({"leave_type_id": lt.id, "balance_year": YEAR - 2}, 422),
                         ({"leave_type_id": lt.id, "balance_year": YEAR - 1}, 422),      # năm trước chưa có quỹ
                         ({"leave_type_id": lt.id, "days": 11}, 422), ({"leave_type_id": lt.id, "days": 1.3}, 422),
                         ({"leave_type_id": lt.id, "reason_kind": int(R.RESIGNATION)}, 422)):
        with pytest.raises(HTTPException) as err:
            service.create(db, LeaveEncashmentCreate(**kwargs), _user(emp))
        assert err.value.status_code == code, kwargs
    assert db.query(LeaveEncashment).count() == 0


def test_lap_phieu_nam_truoc_khi_co_quy(db, lt):
    emp = _emp(db, "C3")
    _balance(db, emp, lt, year=YEAR - 1)
    assert _create(db, emp, lt, balance_year=YEAR - 1).balance_year == YEAR - 1


def test_nghi_viec_can_ngay_nghi_viec_va_nguoi_da_nghi_chi_nhan_ly_do_2(db, lt):
    emp = _emp(db, "C4", resign_date=date(2026, 10, 31))
    _balance(db, emp, lt)
    assert _create(db, emp, lt, reason_kind=int(R.RESIGNATION)).reason_kind == int(R.RESIGNATION)
    gone = _emp(db, "C5", status="resigned")
    _balance(db, gone, lt)
    with pytest.raises(HTTPException) as err:
        _create(db, gone, lt)                                     # lý do 1 với người đã nghỉ việc
    assert err.value.status_code == 422


def test_trung_active_key_409_va_huy_thi_lap_lai_duoc(db, lt):
    emp = _emp(db, "C6")
    _balance(db, emp, lt)
    first = _create(db, emp, lt, days=2)
    with pytest.raises(HTTPException) as err:
        _create(db, emp, lt, days=1)
    assert err.value.status_code == 409
    bridge.cancel_request(db, first, "Đổi ý", _user(emp))
    assert first.status == int(S.CANCELLED) and first.active_key is None
    assert _create(db, emp, lt, days=1).status == int(S.DRAFT)


def test_sua_xoa_chi_khi_nhap_va_xoa_mem_nha_khoa(db, lt):
    emp = _emp(db, "C7")
    _balance(db, emp, lt)
    obj = _create(db, emp, lt, days=2)
    obj = service.update(db, obj, LeaveEncashmentUpdate(days=3, note="Ghi chú"), _user(emp))
    assert obj.days == 3 and obj.note == "Ghi chú"
    with pytest.raises(HTTPException):
        service.update(db, obj, LeaveEncashmentUpdate(days=99), _user(emp))
    service.soft_delete(db, obj, _user(emp))
    assert obj.is_deleted and obj.active_key is None
    obj2 = _submit(db, _create(db, emp, lt, days=1), emp)
    for fn in (lambda: service.update(db, obj2, LeaveEncashmentUpdate(days=1), _user(emp)),
               lambda: service.soft_delete(db, obj2, _user(emp))):
        with pytest.raises(HTTPException):
            fn()


def test_lap_ho_nguoi_khac_can_pham_vi_rong(db, lt):
    a, b = _emp(db, "O1"), _emp(db, "O2")
    with pytest.raises(HTTPException) as err:
        service.create(db, LeaveEncashmentCreate(employee_id=b.id, leave_type_id=lt.id), _user(a))
    assert err.value.status_code == 403


# ── gửi duyệt + bộ máy duyệt thật ───────────────────────────────────────────

def test_gui_giu_cho_va_duyet_doi_quy_sinh_yctt(db, lt):
    emp, approver, obj = _flow_case(db, lt)
    obj = _submit(db, obj, emp)
    assert obj.status == int(S.PENDING) and obj.approval_instance_id > 0
    row = _row(db, emp, lt)
    assert row.pending_days == 4 and row.encashed_days == 0 and balance_service.available_days(db, row) == 6
    _engine(db, obj, approver)
    assert obj.status == int(S.APPROVED) and obj.decided_at is not None
    row = _row(db, emp, lt)
    assert (row.pending_days, row.encashed_days) == (0, 4) and balance_service.available_days(db, row) == 6
    req = db.get(PaymentRequest, obj.payment_request_id)
    assert (req.source_type, req.source_ref_id, req.payee_employee_id, req.created_by, req.status) == \
        ("leave_encashment", obj.id, emp.id, 0, "draft")
    assert float(req.total) == 0


def test_gui_vuot_so_duoc_phep_luc_gui_bi_422_va_khong_doi_gi(db, lt):
    emp = _emp(db, "S1")
    row = _balance(db, emp, lt)
    obj = _create(db, emp, lt, days=8)
    row.used_days = 5                                            # quỹ tụt giữa lúc nháp
    db.commit()
    with pytest.raises(HTTPException) as err:
        tr.prepare_submit(db, obj, _user(emp))
    assert err.value.status_code == 422
    db.refresh(obj)
    assert obj.status == int(S.DRAFT) and _row(db, emp, lt).pending_days == 0


def test_hai_luot_chiem_song_song_chi_mot_qua(db, lt):
    emp = _emp(db, "S2")
    _balance(db, emp, lt)
    obj = _create(db, emp, lt, days=2)
    assert service.try_claim(db, obj, (S.DRAFT,), S.PENDING) is True
    assert service.try_claim(db, obj, (S.DRAFT,), S.PENDING) is False
    with pytest.raises(HTTPException) as err:
        service.claim(db, obj, (S.DRAFT,), S.PENDING)
    assert err.value.status_code == 409


@pytest.mark.parametrize("action,status", [("reject", S.REJECTED), ("back", S.RETURNED)])
def test_tu_choi_tra_ve_deu_tra_giu_cho(db, lt, action, status):
    emp, approver, obj = _flow_case(db, lt, code=action)
    obj = _submit(db, obj, emp)
    assert _row(db, emp, lt).pending_days == 4
    _engine(db, obj, approver, action, "Lý do")
    assert obj.status == int(status) and _row(db, emp, lt).pending_days == 0
    assert (obj.active_key is None) == (status == S.REJECTED)


def test_rut_ve_nhap_tra_giu_cho(db, lt):
    emp, approver, obj = _flow_case(db, lt, code="wd")
    obj = _submit(db, obj, emp)
    bridge.withdraw_running_approval(db, obj, _user(emp, 51))
    db.refresh(obj)
    assert obj.status == int(S.DRAFT) and _row(db, emp, lt).pending_days == 0


def test_tra_ve_roi_sua_gui_lai(db, lt):
    emp, approver, obj = _flow_case(db, lt, code="rs")
    obj = _submit(db, obj, emp)
    _engine(db, obj, approver, "back", "Sửa số ngày")
    obj = service.update(db, obj, LeaveEncashmentUpdate(days=3), _user(emp))
    assert _submit(db, obj, emp).status == int(S.PENDING) and _row(db, emp, lt).pending_days == 3


def test_duyet_hong_giua_chung_thi_khong_nua_chung(db, lt, monkeypatch):
    emp, approver, obj = _flow_case(db, lt, code="veto")
    obj = _submit(db, obj, emp)

    def boom(*_a, **_k):
        raise HTTPException(400, "Hỏng lúc sinh YCTT")

    monkeypatch.setattr(payout, "create_payout_request", boom)
    with pytest.raises(HTTPException):
        _engine(db, obj, approver)
    db.rollback()
    db.refresh(obj)
    row = _row(db, emp, lt)
    assert obj.status == int(S.PENDING) and obj.payment_request_id == 0
    assert (row.pending_days, row.encashed_days) == (4, 0)


def test_duyet_thang_khi_tat_bo_may_va_chan_tu_duyet(db, lt):
    emp, other = _emp(db, "D1"), _emp(db, "D2")
    _balance(db, emp, lt)
    obj = _submit(db, _create(db, emp, lt, days=2), emp)
    assert obj.approval_instance_id == 0 and obj.status == int(S.PENDING)
    with pytest.raises(HTTPException) as err:                     # chính người nhận tiền
        ctl.approve_encashment(obj.id, db=db, user=SimpleNamespace(id=60, employee_id=emp.id))
    assert err.value.status_code in (403, 404)
    assert strict_self_exclusion(ENTITY) is True
    with pytest.raises(HTTPException) as err:
        ensure_not_self_approval(ENTITY, emp.id, emp.id)
    assert err.value.status_code == 403 and "thanh toán nghỉ phép" in err.value.detail
    bridge._on_approved(db, obj.id, SimpleNamespace(updated_by=ACTOR, finish_reason=""))
    db.commit()
    assert _row(db, emp, lt).encashed_days == 2 and obj.status == int(S.APPROVED)


# ── hủy theo bốn trạng thái YCTT (D7a) ─────────────────────────────────────

def _approved(db, lt, code):
    emp, approver, obj = _flow_case(db, lt, code=code)
    obj = _submit(db, obj, emp)
    _engine(db, obj, approver)
    return emp, obj


def test_huy_pending_rut_phien_va_tra_giu_cho(db, lt):
    emp, approver, obj = _flow_case(db, lt, code="cp")
    obj = _submit(db, obj, emp)
    obj = bridge.cancel_request(db, obj, "Đổi ý", _user(emp))
    assert obj.status == int(S.CANCELLED) and instance_service.running_instance(db, ENTITY, obj.id) is None
    assert _row(db, emp, lt).pending_days == 0


def test_huy_da_duyet_khi_yctt_nhap_tra_ngay_va_xoa_yctt(db, lt):
    emp, obj = _approved(db, lt, "ch")
    req_id = obj.payment_request_id
    obj = bridge.cancel_request(db, obj, "Nhập nhầm", _user(emp))
    assert obj.status == int(S.CANCELLED) and obj.active_key is None
    row = _row(db, emp, lt)
    assert row.encashed_days == 0 and balance_service.available_days(db, row) == 10
    assert db.get(PaymentRequest, req_id).is_deleted is True


@pytest.mark.parametrize("pay_status,text", [("submitted", "Chờ duyệt"), ("approved", "Đã duyệt"), ("paid", "đã chi")])
def test_huy_da_duyet_bi_chan_khi_ke_toan_da_vao_cuoc(db, lt, pay_status, text):
    emp, obj = _approved(db, lt, f"b{pay_status}")
    db.get(PaymentRequest, obj.payment_request_id).status = pay_status
    db.commit()
    with pytest.raises(HTTPException) as err:
        bridge.cancel_request(db, obj, "", _user(emp))
    assert err.value.status_code == 400 and text in err.value.detail
    db.rollback()
    db.refresh(obj)
    assert obj.status == int(S.APPROVED) and _row(db, emp, lt).encashed_days == 4
    assert "chi" in ctl.view.cancel_blocked_reason(db, obj) or text in ctl.view.cancel_blocked_reason(db, obj)


def test_huy_da_duyet_khi_ke_toan_tu_choi_yctt_giu_yctt_tra_ngay(db, lt):
    emp, obj = _approved(db, lt, "cc")
    req = db.get(PaymentRequest, obj.payment_request_id)
    req.status = "cancelled"
    db.commit()
    obj = bridge.cancel_request(db, obj, "Trả ngày", _user(emp))
    assert obj.status == int(S.CANCELLED) and _row(db, emp, lt).encashed_days == 0
    assert db.get(PaymentRequest, req.id).is_deleted is False        # sổ chi giữ nguyên


# ── phạm vi + chi tiết + số tiền ────────────────────────────────────────────

def test_pham_vi_chinh_chu_va_nguoi_co_viec_duyet(db, world, lt):
    a1, a2, a3 = (world.actor(k) for k in ("a1", "a2", "a3"))
    for key in ("a1", "a2", "a3"):
        world.grant(key, ENTITY, scope="own", actions=("read", "create", "write"))
    emp = db.get(Employee, world.emp["a1"])
    _balance(db, emp, lt)
    obj = service.create(db, LeaveEncashmentCreate(leave_type_id=lt.id, days=2), a1.user)
    assert ctl._get_or_404(db, obj.id, a1.user).id == obj.id
    with pytest.raises(HTTPException) as err:
        ctl._get_or_404(db, obj.id, a2.user)
    assert err.value.status_code == 404
    _flow(db, db.get(Employee, world.emp["a2"]))
    _submit(db, obj, emp)
    assert ctl._get_or_404(db, obj.id, a2.user).id == obj.id          # đang có việc duyệt treo -> đọc được


def test_payment_total_an_voi_nguoi_duyet_nhan_su_hien_voi_chinh_chu(db, world, lt):
    a1, a2 = world.actor("a1"), world.actor("a2")
    world.grant("a1", ENTITY, scope="own", actions=("read", "create", "write"))
    world.grant("a2", ENTITY, scope="all", actions=("read", "approve"))
    emp = db.get(Employee, world.emp["a1"])
    _balance(db, emp, lt)
    obj = service.create(db, LeaveEncashmentCreate(leave_type_id=lt.id, days=2), a1.user)
    _submit(db, obj, emp)
    bridge._on_approved(db, obj.id, SimpleNamespace(updated_by=a2.user.id, finish_reason=""))
    db.commit()
    pay_service.update_request(db, obj.payment_request_id, PRequestUpdate(lines=[LineIn(amount=5_000_000)]), a2.user.id)
    assert ctl.view.payment_block(db, obj, a1.user)["total"] == 5_000_000          # chính chủ
    block = ctl.view.payment_block(db, obj, a2.user)                                 # Nhân sự không có quyền YCTT
    assert block["total"] is None and block["status"] == "draft"


# ── chuông ──────────────────────────────────────────────────────────────────

def _acc(db, emp, uid):
    user = User(email=f"u{uid}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    return user


def test_chuong_da_chi_bao_nhan_su_nhan_tien_va_tu_choi_bao_nguoi_duyet(db, lt):
    emp, obj = _approved(db, lt, "bell")
    payee, boss = _acc(db, emp, 1), _acc(db, _emp(db, "BOSS"), 2)
    obj.updated_by, obj.created_by = boss.id, boss.id
    db.commit()
    req = db.get(PaymentRequest, obj.payment_request_id)
    payout.notify_payout_outcome(db, req, "pay_paid")
    payout.notify_payout_outcome(db, req, "pay_rejected", reason="Thiếu STK")
    paid = db.query(Notification).filter(Notification.user_id == payee.id).all()
    rej = db.query(Notification).filter(Notification.user_id == boss.id).all()
    assert len(paid) == 1 and "Đã chi" in paid[0].title and paid[0].link == f"/hr/leave-encashments/{obj.id}"
    assert len(rej) == 1 and "Thiếu STK" not in rej[0].body and "xem lý do ở Yêu cầu thanh toán" in rej[0].body   # L6
    for n in paid + rej:
        assert not any(ch.isdigit() for ch in n.body.replace(req.code, "").replace("Thiếu STK", ""))   # không số tiền / ngày


# ── nối dây ─────────────────────────────────────────────────────────────────

def test_noi_day_nhan_duong_dan_nguon_bao_cao_va_xoa_nhan_su(db, lt):
    assert task_notification.ENTITY_LABELS[ENTITY] == "Thanh toán nghỉ phép"
    assert task_notification.ENTITY_LINKS[ENTITY] == "/hr/leave-encashments/{id}"
    assert ENTITY in permission_approvers.SUPPORTED_ENTITIES
    assert ENTITY in report_service.APPROVAL_REPORT_SOURCES
    assert any(r.path.startswith("/api/leave-encashments") for r in ctl.router.routes)
    paths = [r.path for r in ctl.router.routes]
    assert paths.index("/api/leave-encashments/to-approve") < paths.index("/api/leave-encashments/{rid}")
    assert paths.index("/api/leave-encashments/preview") < paths.index("/api/leave-encashments/{rid}")
    emp = _emp(db, "REF")
    _balance(db, emp, lt)
    _create(db, emp, lt, days=1)
    labels = dict(count_references(db, "employee", emp))
    assert labels.get("phiếu thanh toán nghỉ phép") == 1
    payee = _emp(db, "PAYEE")
    db.add(PaymentRequest(code="YCTT-P", source_type="leave_encashment", payee_employee_id=payee.id, status="draft"))
    db.commit()
    assert dict(count_references(db, "employee", payee)).get("yêu cầu thanh toán (người nhận tiền nghỉ phép)") == 1


def test_preview_chi_doc_va_khop_so_tinh(db, lt):
    lt.non_encashable_days = 4
    emp = _emp(db, "PV")
    _balance(db, emp, lt)
    resp = ctl.preview_encashable(leave_type_id=lt.id, employee_id=0, balance_year=None, reason_kind=1,
                                  db=db, user=_user(emp))
    data = json.loads(resp.body)["data"]
    assert data["encashable"] == 6 and data["available"] == 10 and data["balance_year"] == YEAR
    assert db.query(LeaveEncashment).count() == 0


def test_my_leave_summary_co_ngay_da_thanh_toan_khong_co_tien(db, world, lt):
    from app.modules.assistant.tools.leave_tool import MY_LEAVE_SUMMARY_SPEC
    a1 = world.actor("a1")
    world.grant("a1", "leave_request", scope="own", actions=("read",))
    world.grant("a1", ENTITY, scope="own", actions=("read", "create"))
    emp = db.get(Employee, world.emp["a1"])
    _balance(db, emp, lt, encashed_days=0)
    obj = service.create(db, LeaveEncashmentCreate(leave_type_id=lt.id, days=2), a1.user)
    _submit(db, obj, emp)
    bridge._on_approved(db, obj.id, SimpleNamespace(updated_by=ACTOR, finish_reason=""))
    db.commit()
    pay_service.update_request(db, obj.payment_request_id, PRequestUpdate(lines=[LineIn(amount=9_000_000)]), 9999)   # kế toán, không phải người nhận
    from app.modules.assistant.tools.base import ToolContext
    ctx = ToolContext(db=db, user=a1.user)
    out = MY_LEAVE_SUMMARY_SPEC.handler(ctx, {"year": YEAR})
    bal = next(b for b in out["balances"] if b["leave_type_id"] == lt.id)
    assert bal["encashed_days"] == 2 and bal["allow_encashment"] is True and bal["remaining_days"] == 8
    enc = out["encashments"]
    assert len(enc) == 1 and enc[0]["days"] == 2 and enc[0]["status"] == int(S.APPROVED)
    assert enc[0]["payment_status"] == "draft"
    assert "9000000" not in repr(out) and "total" not in enc[0] and "amount" not in enc[0]


def test_chuong_ke_toan_chi_gui_sau_khi_commit_duyet(db, lt, monkeypatch):
    calls = []
    monkeypatch.setattr(payout, "notify_payout_created", lambda _db, req, background_tasks=None: calls.append(req.id))
    emp, approver, obj = _flow_case(db, lt, code="nt")
    obj = _submit(db, obj, emp)
    action_service.approve(db, instance_service.running_instance(db, ENTITY, obj.id), approver.id, ACTOR, {})
    db.refresh(obj)
    assert calls == [obj.payment_request_id] and obj.payment_request_id > 0


def test_chuong_ke_toan_khong_gui_khi_duyet_hong(db, lt, monkeypatch):
    calls = []
    monkeypatch.setattr(payout, "notify_payout_created", lambda _db, req, background_tasks=None: calls.append(req.id))

    def boom(*_a, **_k):
        raise HTTPException(400, "Hỏng")

    emp, approver, obj = _flow_case(db, lt, code="nf")
    obj = _submit(db, obj, emp)
    monkeypatch.setattr(payout, "create_payout_request", boom)
    with pytest.raises(HTTPException):
        action_service.approve(db, instance_service.running_instance(db, ENTITY, obj.id), approver.id, ACTOR, {})
    db.rollback()
    db.commit()           # commit KẾ TIẾP không được kéo chuông của lượt hỏng
    assert calls == []
