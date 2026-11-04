"""duoc-CR-715 giai đoạn C — PHIẾU XIN NGHỈ BÙ (tab_leave_comp_request).

Vòng đời qua BỘ MÁY DUYỆT THẬT: lập → gửi → duyệt → `comp_days` + còn lại tăng; từ chối / rút → quỹ không đổi;
hủy sau duyệt trừ lại, và bị chặn khi ngày bù đã được dùng. Chốt ngày: ngày làm việc thường bị chặn, ngày lễ /
ngày nghỉ theo lịch được nhận, trùng ngày và ngày tương lai bị chặn. Phạm vi + chặn tự duyệt (CR-713).
"""
import time
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.core.vn_time import vn_today
from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalFlow, ApprovalNode, ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_APPROVED
from app.modules.approval.self_approval_policy import strict_self_exclusion
from app.modules.employee.model import Employee
from app.modules.leave import balance_service, comp_approval_bridge as bridge
from app.modules.leave import comp_request_controller as ctl, comp_request_service as service
from app.modules.leave.catalog_model import Holiday, LeaveType
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.comp_request_schema import LeaveCompRequestCreate, LeaveCompRequestUpdate
from app.modules.leave.constants import LeaveCompStatus as S
from app.modules.setting import service as setting_service
from app.modules.setting.model import Setting

ACTOR = 1
ENTITY = "leave_comp_request"
SUN = date(2026, 1, 11)      # Chủ nhật — nghỉ theo lịch mặc định
MON = date(2026, 1, 12)      # ngày làm việc thường
HOLIDAY = date(2026, 1, 19)  # thứ Hai nhưng là ngày lễ (nạp trong bài)


@pytest.fixture(autouse=True)
def _settings_from_test_db(db, monkeypatch):
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


@pytest.fixture()
def comp_type(db):
    obj = LeaveType(code="comp", name="Nghỉ bù", counts_balance=True, is_compensatory=True, annual_quota_days=0.0)
    db.add(obj)
    db.flush()
    return obj


def _emp(db, code, company=1, dept=7):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=company, department_id=dept, is_active=True)
    db.add(obj)
    db.flush()
    return obj


def _user(emp, uid=50):
    return SimpleNamespace(id=uid, employee_id=emp.id)


def _flow(db, approver):
    row = ApprovalFlow(entity=ENTITY, code="NB-715", name="Duyệt nghỉ bù", is_active=True,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(approver.id), created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _create(db, emp, work_date=SUN, days=1.0, reason="Trực kho"):
    return service.create(db, LeaveCompRequestCreate(work_date=work_date, days=days, reason=reason), _user(emp))


def _submit(db, obj, emp):
    user = _user(emp)
    service.prepare_submit(db, obj)
    instance_id = bridge.start_approval(db, obj, user)
    return service.mark_submitted(db, obj, user, instance_id)


def _row(db, emp, year=2026):
    return balance_service.get_balance(db, emp.id, year, db.query(LeaveType).filter_by(code="comp").one().id)


def _remaining(db, emp):
    row = _row(db, emp)
    return balance_service.available_days(db, row) if row else 0.0


def _approve_via_engine(db, obj, approver):
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, approver.id, ACTOR, {})
    db.refresh(obj)
    return instance


# ── Vòng đời qua bộ máy duyệt ───────────────────────────────────────────────

def test_lifecycle_engine_approve_adds_comp_days(db, comp_type):
    emp, approver = _emp(db, "N1"), _emp(db, "N2")
    _flow(db, approver)
    obj = _create(db, emp)
    assert obj.status == int(S.DRAFT) and obj.code.startswith("NB")
    obj = _submit(db, obj, emp)
    assert obj.status == int(S.PENDING) and obj.approval_instance_id > 0
    assert _row(db, emp) is None or _row(db, emp).comp_days == 0
    instance = _approve_via_engine(db, obj, approver)
    assert instance.status == INSTANCE_APPROVED
    assert obj.status == int(S.APPROVED) and obj.decided_at is not None
    row = _row(db, emp)
    assert row.comp_days == 1.0 and row.total_days == 1.0 and _remaining(db, emp) == 1.0


def test_half_day_adds_half(db, comp_type):
    emp, approver = _emp(db, "N3"), _emp(db, "N4")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp, days=0.5), emp)
    _approve_via_engine(db, obj, approver)
    assert _row(db, emp).comp_days == 0.5


def test_engine_reject_changes_nothing(db, comp_type):
    emp, approver = _emp(db, "N5"), _emp(db, "N6")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.reject(db, instance, approver.id, ACTOR, "Không đủ chứng từ")
    db.refresh(obj)
    assert obj.status == int(S.REJECTED) and _remaining(db, emp) == 0.0


def test_engine_return_then_editable_and_resubmit(db, comp_type):
    emp, approver = _emp(db, "N7"), _emp(db, "N8")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.send_back(db, instance, approver.id, ACTOR, "Ghi rõ việc", {})
    db.refresh(obj)
    assert obj.status == int(S.RETURNED) and _remaining(db, emp) == 0.0
    obj = service.update(db, obj, LeaveCompRequestUpdate(reason="Trực kho cuối tuần"), _user(emp))
    assert _submit(db, obj, emp).status == int(S.PENDING)


def test_withdraw_back_to_draft_no_change(db, comp_type):
    emp, approver = _emp(db, "N9"), _emp(db, "N10")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    bridge.withdraw_running_approval(db, obj, _user(emp, 51))
    db.refresh(obj)
    assert obj.status == int(S.DRAFT) and _remaining(db, emp) == 0.0


def test_cancel_pending_withdraws_instance(db, comp_type):
    emp, approver = _emp(db, "N11"), _emp(db, "N12")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    obj = bridge.cancel_request(db, obj, "Đổi ý", _user(emp))
    assert obj.status == int(S.CANCELLED) and instance_service.running_instance(db, ENTITY, obj.id) is None


def test_cancel_after_approve_subtracts(db, comp_type):
    emp, approver = _emp(db, "N13"), _emp(db, "N14")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    _approve_via_engine(db, obj, approver)
    assert _remaining(db, emp) == 1.0
    obj = bridge.cancel_request(db, obj, "Nhập nhầm", _user(emp))
    assert obj.status == int(S.CANCELLED) and _row(db, emp).comp_days == 0.0 and _remaining(db, emp) == 0.0


def test_cancel_after_approve_blocked_when_days_used(db, comp_type):
    emp, approver = _emp(db, "N15"), _emp(db, "N16")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    _approve_via_engine(db, obj, approver)
    row = _row(db, emp)
    row.used_days = 1.0     # ngày bù đã dùng để nghỉ
    db.commit()
    with pytest.raises(HTTPException) as err:
        bridge.cancel_request(db, obj, "", _user(emp))
    assert err.value.status_code == 422
    db.rollback()
    db.refresh(obj)
    assert obj.status == int(S.APPROVED) and _row(db, emp).comp_days == 1.0


# ── Duyệt thẳng (không luồng) ───────────────────────────────────────────────

def test_direct_approve_when_engine_off(db, comp_type):
    emp = _emp(db, "N17")
    obj = _submit(db, _create(db, emp), emp)
    assert obj.status == int(S.PENDING) and obj.approval_instance_id == 0

    class Direct:
        updated_by = ACTOR
        finish_reason = ""

    bridge.block_legacy_path(db, obj)     # không có phiên chạy → không chặn
    bridge._on_approved(db, obj.id, Direct())
    db.commit()
    assert _row(db, emp).comp_days == 1.0


# ── Chốt ngày / số ngày ─────────────────────────────────────────────────────

def test_working_day_rejected(db, comp_type):
    with pytest.raises(HTTPException) as err:
        _create(db, _emp(db, "W1"), work_date=MON)
    assert err.value.status_code == 422


def test_holiday_on_weekday_accepted(db, comp_type):
    db.add(Holiday(company_id=0, date=HOLIDAY, name="Lễ", is_recurring=False, is_active=True))
    db.flush()
    assert _create(db, _emp(db, "W2"), work_date=HOLIDAY).work_date == HOLIDAY


def test_recurring_company_holiday_accepted(db, comp_type):
    db.add(Holiday(company_id=1, date=date(2020, 1, 19), name="Lễ lặp", is_recurring=True, is_active=True))
    db.flush()
    assert _create(db, _emp(db, "W3", company=1), work_date=HOLIDAY).status == int(S.DRAFT)


def test_schedule_rest_day_accepted(db, comp_type):
    from lich_lam_viec_factory import assign, make_schedule, make_world, week_t2_t6_sat_am
    from app.core.work_schedule_codes import WorkScheduleLevel as L
    _, dept, emp = make_world(db, "SCH1")
    assign(db, L.DEPARTMENT, dept.id, make_schedule(db, "T7 nửa ngày", week_t2_t6_sat_am()).id, date(2026, 1, 1))
    #  CN 11/01 nghỉ theo lịch → được. T2 12/01 làm → chặn.
    assert _create(db, emp, work_date=SUN).status == int(S.DRAFT)
    with pytest.raises(HTTPException):
        _create(db, emp, work_date=MON)


def test_duplicate_date_rejected_but_cancelled_does_not_count(db, comp_type):
    emp = _emp(db, "D1")
    first = _create(db, emp)
    with pytest.raises(HTTPException) as err:
        _create(db, emp)
    assert err.value.status_code == 409
    service.cancel(db, first, "", ACTOR)
    assert _create(db, emp).status == int(S.DRAFT)


def test_future_date_rejected(db, comp_type):
    with pytest.raises(HTTPException) as err:
        _create(db, _emp(db, "F1"), work_date=vn_today() + timedelta(days=1))
    assert err.value.status_code == 422 and "tương lai" in err.value.detail


def test_days_must_be_half_or_one(db, comp_type):
    with pytest.raises(HTTPException) as err:
        _create(db, _emp(db, "H1"), days=0.7)
    assert err.value.status_code == 422


def test_missing_comp_type_is_422(db):
    db.add(LeaveType(code="annual", name="Phép năm", counts_balance=True))   # chưa bật is_compensatory
    db.flush()
    with pytest.raises(HTTPException) as err:
        _create(db, _emp(db, "M1"))
    assert err.value.status_code == 422 and "Loại nhận ngày nghỉ bù" in err.value.detail


def test_comp_type_picks_lowest_sort_order_and_skips_non_balance(db):
    db.add_all([LeaveType(code="c3", name="C3", counts_balance=True, is_compensatory=True, sort_order=3),
                LeaveType(code="c1", name="C1", counts_balance=True, is_compensatory=True, sort_order=1),
                LeaveType(code="c0", name="C0", counts_balance=False, is_compensatory=True, sort_order=0)])
    db.flush()
    assert service.get_comp_type(db).code == "c1"


def test_reason_required_at_submit_and_only_draft_editable(db, comp_type):
    emp = _emp(db, "R1")
    obj = _create(db, emp, reason="")
    with pytest.raises(HTTPException) as err:
        service.prepare_submit(db, obj)
    assert err.value.status_code == 422
    obj.reason = "Trực"
    obj = _submit(db, obj, emp)
    with pytest.raises(HTTPException):
        service.update(db, obj, LeaveCompRequestUpdate(reason="x"), _user(emp))
    with pytest.raises(HTTPException):
        service.soft_delete(db, obj, _user(emp))


def test_delete_draft_soft(db, comp_type):
    emp = _emp(db, "R2")
    obj = _create(db, emp)
    service.soft_delete(db, obj, _user(emp))
    assert obj.is_deleted is True


def test_create_for_other_needs_wider_scope(db, comp_type):
    a, b = _emp(db, "O1"), _emp(db, "O2")
    with pytest.raises(HTTPException) as err:
        service.create(db, LeaveCompRequestCreate(employee_id=b.id, work_date=SUN, days=1, reason="x"), _user(a))
    assert err.value.status_code == 403


# ── Phạm vi ─────────────────────────────────────────────────────────────────

def _scoped_create(world, key, comp_type_row=None):
    emp = world.db.get(Employee, world.emp[key])
    return service.create(world.db, LeaveCompRequestCreate(work_date=SUN, days=1, reason="Trực"),
                          world.actor(key).user)


def test_scope_other_department_user_gets_404(db, world, comp_type):
    for k in ("a1", "a3"):
        world.grant(k, ENTITY, scope="own", actions=("read", "create", "write"))
    world.grant("a2", ENTITY, scope="own", actions=("read",))
    world.grant("b1", ENTITY, scope="dept", actions=("read",))
    rid = _scoped_create(world, "a1").id
    assert ctl._get_or_404(db, rid, world.actor("a1").user).id == rid          # chính chủ
    for other in ("a2", "a3", "b1"):                                              # cùng phòng nhưng own / phòng khác
        with pytest.raises(HTTPException) as err:
            ctl._get_or_404(db, rid, world.actor(other).user)
        assert err.value.status_code == 404


def test_scope_dept_head_sees_department_requests(db, world, comp_type):
    world.grant("a1", ENTITY, scope="own", actions=("read", "create", "write"))
    world.grant("a2", ENTITY, scope="dept", actions=("read",))
    rid = _scoped_create(world, "a1").id
    assert ctl._get_or_404(db, rid, world.actor("a2").user).id == rid


# ── Chặn tự duyệt (CR-713) ──────────────────────────────────────────────────

def test_strict_self_exclusion_covers_comp_entity(db):
    #  Phiếu nghỉ bù LUÔN chặn tự duyệt; đơn nghỉ thường theo công tắc.
    assert strict_self_exclusion(ENTITY) is True and strict_self_exclusion("leave_request") is False
    setting_service.save(db, {"leave_prevent_self_approval": True}, user_id=ACTOR)
    assert strict_self_exclusion(ENTITY) is True and strict_self_exclusion("leave_request") is True
    assert strict_self_exclusion("document") is False


def test_direct_approve_blocked_for_self_regardless_of_setting(db, world, comp_type):
    world.grant("a1", ENTITY, scope="own", actions=("read", "create", "write", "approve"))
    obj = _scoped_create(world, "a1")
    user = world.actor("a1").user
    service.prepare_submit(db, obj)
    service.mark_submitted(db, obj, user, 0)
    for flag in (False, True):      # công tắc TẮT cũng chặn — tự duyệt là tự cộng ngày phép
        setting_service.save(db, {"leave_prevent_self_approval": flag}, user_id=ACTOR)
        with pytest.raises(HTTPException) as err:
            ctl.approve_request(obj.id, db=db, user=user)
        assert err.value.status_code == 403
    db.refresh(obj)
    assert obj.status == int(S.PENDING)


def test_engine_named_step_on_taker_goes_to_fallback_even_when_setting_off(db, comp_type):
    assert not app_settings.get("leave_prevent_self_approval")
    emp = _emp(db, "SA1")
    _flow(db, emp)       # bước đích danh chính là người nộp
    obj = _submit(db, _create(db, emp), emp)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    assert instance is not None
    with pytest.raises(HTTPException) as err:
        action_service.approve(db, instance, emp.id, 77, {})
    assert err.value.status_code in (400, 403)


# ── Quỹ: mọi màn cùng một công thức ─────────────────────────────────────────

def test_comp_days_in_total_and_balance_report(db, comp_type):
    from app.modules.leave import balance_report_spec
    emp = _emp(db, "B1")
    row = balance_service.ensure_balance(db, emp, 2026, comp_type, ACTOR)
    row.comp_days = 1.5
    row.adjusted_days = 1.0
    db.commit()
    assert row.total_days == 2.5 and row.remaining_days == 2.5
    assert "comp_days" in [c.key for c in balance_report_spec.BAL_COLS]
