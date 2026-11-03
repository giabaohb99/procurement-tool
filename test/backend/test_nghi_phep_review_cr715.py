"""duoc-CR-715 — bài hồi quy cho đợt SỬA THEO REVIEW (phiếu nghỉ bù, báo cáo quỹ, ô gợi ý ứng phép).

Mỗi bài khóa một lỗi đã dựng lại được: chiếm phiếu nguyên tử (409), chốt loại + năm quỹ, dải ngày, khóa "một ngày
một phiếu" ở tầng dữ liệu, `HookVeto` ở bộ máy duyệt, báo cáo quỹ trừ phần chưa tới tháng với số truy vấn cố định.
"""
import time
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core import app_settings
from app.core.report_period import parse_period
from app.core.vn_time import vn_today
from app.modules.approval import action_service, instance_service
from app.modules.approval.entity_hooks import HookVeto
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalFlow, ApprovalNode, ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_RUNNING
from app.modules.employee.model import Employee
from app.modules.leave import balance_report_service, balance_service, comp_approval_bridge as bridge
from app.modules.leave import comp_request_controller as ctl, comp_request_service as service
from app.modules.leave import request_controller
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.comp_request_schema import LeaveCompRequestCreate, LeaveCompRequestUpdate
from app.modules.leave.constants import LeaveAccrualMode, LeaveCompStatus as S
from app.modules.setting.model import Setting

ACTOR = 1
ENTITY = "leave_comp_request"
TODAY = vn_today()


def _sunday_on_or_before(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


#  Một ngày nghỉ theo lịch mặc định (Chủ nhật), đã qua, thuộc NĂM NAY / NĂM NGOÁI / HAI NĂM TRƯỚC.
SUN_THIS_YEAR = _sunday_on_or_before(TODAY)
SUN_LAST_YEAR = _sunday_on_or_before(date(TODAY.year - 1, 12, 31))
SUN_OLD = _sunday_on_or_before(date(TODAY.year - 2, 12, 31))


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
    obj = LeaveType(code="comp", name="Nghỉ bù", counts_balance=True, is_compensatory=True,
                    annual_quota_days=0.0, sort_order=5)
    db.add(obj)
    db.flush()
    return obj


def _emp(db, code, hire=date(2020, 1, 1)):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=1, department_id=7, is_active=True, hire_date=hire)
    db.add(obj)
    db.flush()
    return obj


def _user(emp, uid=50):
    return SimpleNamespace(id=uid, employee_id=emp.id)


def _flow(db, approver):
    row = ApprovalFlow(entity=ENTITY, code="NB-716", name="Duyệt nghỉ bù", is_active=True,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(approver.id), created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _create(db, emp, work_date=SUN_THIS_YEAR, days=1.0):
    return service.create(db, LeaveCompRequestCreate(work_date=work_date, days=days, reason="Trực kho"), _user(emp))


def _submit(db, obj, emp):
    user = _user(emp)
    service.prepare_submit(db, obj, user)
    return service.mark_submitted(db, obj, user, bridge.start_approval(db, obj, user))


def _stale_set_status(db, obj, status):
    """Giả lập "lượt khác vừa đổi trạng thái" mà đối tượng đang cầm trong phiên vẫn là bản cũ."""
    db.query(LeaveCompRequest).filter(LeaveCompRequest.id == obj.id).update(
        {"status": int(status)}, synchronize_session=False)
    db.commit()


def _comp_days(db, emp, leave_type, year):
    row = balance_service.get_balance(db, emp.id, year, leave_type.id)
    return row.comp_days if row else 0.0


# ── 2. Chiếm phiếu nguyên tử ────────────────────────────────────────────────

def test_double_direct_approve_second_gets_409_and_credits_once(db, comp_type):
    emp = _emp(db, "R1")
    obj = _submit(db, _create(db, emp), emp)
    bridge.approve_now(db, obj, ACTOR)
    db.commit()
    stale = db.get(LeaveCompRequest, obj.id)
    stale.status = int(S.PENDING)     # bản nhớ cũ của lượt bấm thua — DB đã Đã duyệt
    with pytest.raises(HTTPException) as err:
        bridge.approve_now(db, stale, ACTOR)
    assert err.value.status_code == 409 and "lượt khác" in err.value.detail
    db.rollback()
    assert _comp_days(db, emp, comp_type, TODAY.year) == 1.0


def test_stale_direct_approve_reject_cancel_submit_all_get_409(db, comp_type):
    emp = _emp(db, "R2")
    obj = _submit(db, _create(db, emp), emp)
    _stale_set_status(db, obj, S.CANCELLED)      # lượt khác hủy trước
    stale = obj
    stale.status = int(S.PENDING)                # đối tượng trong phiên của lượt thua vẫn là bản cũ
    for fn in (lambda: service.claim(db, stale, (S.PENDING,), S.APPROVED),
               lambda: service.claim(db, stale, (S.PENDING,), S.REJECTED),
               lambda: service.claim(db, stale, (S.DRAFT, S.RETURNED), S.PENDING)):
        with pytest.raises(HTTPException) as err:
            fn()
        assert err.value.status_code == 409
    assert _comp_days(db, emp, comp_type, TODAY.year) == 0.0


def test_double_submit_second_gets_409_without_second_instance(db, comp_type):
    emp, approver = _emp(db, "R3"), _emp(db, "R4")
    _flow(db, approver)
    obj = _create(db, emp)
    service.prepare_submit(db, obj, _user(emp))
    bridge.start_approval(db, obj, _user(emp))
    stale = obj
    stale.status = int(S.DRAFT)                  # lượt bấm thứ hai vẫn thấy "Nháp"
    with pytest.raises(HTTPException) as err:
        service.prepare_submit(db, stale, _user(emp))
    assert err.value.status_code == 409


def test_cancel_loses_to_concurrent_cancel_and_does_not_revoke_twice(db, comp_type):
    emp = _emp(db, "R5")
    obj = _submit(db, _create(db, emp), emp)
    bridge.approve_now(db, obj, ACTOR)
    db.commit()
    stale = db.get(LeaveCompRequest, obj.id)
    service.cancel(db, stale, "A", ACTOR)
    assert _comp_days(db, emp, comp_type, TODAY.year) == 0.0
    stale.status = int(S.APPROVED)      # lượt B vẫn nghĩ là Đã duyệt
    with pytest.raises(HTTPException) as err:
        service.cancel(db, stale, "B", ACTOR)
    assert err.value.status_code == 409
    db.rollback()
    assert _comp_days(db, emp, comp_type, TODAY.year) == 0.0     # không trừ âm lần hai


# ── 3. Loại nhận ngày bù chốt lúc gửi ───────────────────────────────────────

def test_submit_stores_type_and_later_catalog_change_does_not_move_credit(db, comp_type):
    emp = _emp(db, "T1")
    obj = _submit(db, _create(db, emp), emp)
    assert obj.comp_leave_type_id == comp_type.id
    other = LeaveType(code="comp0", name="Nghỉ bù mới", counts_balance=True, is_compensatory=True, sort_order=0)
    db.add(other)
    db.commit()
    assert service.get_comp_type(db).id == other.id        # danh mục giờ ưu tiên loại khác…
    bridge.approve_now(db, obj, ACTOR)
    db.commit()
    assert _comp_days(db, emp, comp_type, TODAY.year) == 1.0     # …nhưng ngày bù vẫn vào loại đã chốt
    assert _comp_days(db, emp, other, TODAY.year) == 0.0
    service.cancel(db, obj, "", ACTOR)
    assert _comp_days(db, emp, comp_type, TODAY.year) == 0.0     # hủy trừ đúng loại đã chốt


def test_engine_approval_with_invalid_stored_type_is_vetoed_even_if_caller_commits(db, comp_type):
    emp, approver = _emp(db, "T2"), _emp(db, "T3")
    _flow(db, approver)
    obj = _submit(db, _create(db, emp), emp)
    comp_type.is_compensatory = False       # ai đó tắt loại nhận ngày bù giữa lúc chờ duyệt
    db.commit()
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    with pytest.raises(HookVeto) as err:
        action_service.approve(db, instance, approver.id, ACTOR, {})
    assert err.value.status_code == 422 and "Loại nhận ngày nghỉ bù" in err.value.detail
    db.commit()     # caller kiểu MCP vẫn commit — `fire` đã cuộn lại
    db.refresh(obj)
    assert obj.status == int(S.PENDING)
    assert instance_service.running_instance(db, ENTITY, obj.id).status == INSTANCE_RUNNING


# ── 4. Năm quỹ ──────────────────────────────────────────────────────────────

def test_work_date_last_year_credits_current_year_and_cancel_uses_stored_year(db, comp_type):
    emp = _emp(db, "Y1")
    obj = _submit(db, _create(db, emp, work_date=SUN_LAST_YEAR), emp)
    assert obj.balance_year == 0
    bridge.approve_now(db, obj, ACTOR)
    db.commit()
    db.refresh(obj)
    assert obj.balance_year == TODAY.year
    assert _comp_days(db, emp, comp_type, TODAY.year) == 1.0
    assert _comp_days(db, emp, comp_type, TODAY.year - 1) == 0.0
    service.cancel(db, obj, "", ACTOR)
    assert _comp_days(db, emp, comp_type, TODAY.year) == 0.0


# ── 5. Dải ngày ─────────────────────────────────────────────────────────────

def test_schema_rejects_year_outside_2000_2100():
    for bad in (date(1999, 12, 31), date(2101, 1, 1)):
        with pytest.raises(ValidationError):
            LeaveCompRequestCreate(work_date=bad, days=1, reason="x")
        with pytest.raises(ValidationError):
            LeaveCompRequestUpdate(work_date=bad)


def test_service_rejects_work_date_older_than_start_of_last_year(db, comp_type):
    with pytest.raises(HTTPException) as err:
        _create(db, _emp(db, "O1"), work_date=SUN_OLD)
    assert err.value.status_code == 422 and "quá cũ" in err.value.detail
    assert _create(db, _emp(db, "O2"), work_date=SUN_LAST_YEAR).work_date == SUN_LAST_YEAR


# ── 12. Khóa "một ngày một phiếu" ở tầng dữ liệu ─────────────────────────────

def test_unique_active_key_blocks_duplicate_insert_that_skips_service_check(db, comp_type):
    emp = _emp(db, "K1")
    first = _create(db, emp)
    assert first.active_key == f"{emp.id}:{first.work_date.isoformat()}"
    db.add(LeaveCompRequest(code="NBX1", employee_id=emp.id, work_date=first.work_date, days=1.0,
                            active_key=first.active_key, status=int(S.DRAFT)))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_active_key_released_by_cancel_reject_and_delete(db, comp_type):
    emp = _emp(db, "K2")
    first = _create(db, emp)
    service.soft_delete(db, first, _user(emp))
    assert first.active_key is None
    second = _create(db, emp)                       # ngày đã nhả → lập lại được
    service.cancel(db, second, "", ACTOR)
    assert second.active_key is None
    third = _create(db, emp)
    third = _submit(db, third, emp)
    bridge.block_legacy_path(db, third)
    service.claim(db, third, (S.PENDING,), S.REJECTED)
    db.commit()
    assert third.active_key is None
    assert _create(db, emp).active_key is not None


def test_edit_into_taken_date_is_409(db, comp_type):
    emp = _emp(db, "K3")
    a = _create(db, emp, work_date=SUN_THIS_YEAR)
    b = _create(db, emp, work_date=SUN_THIS_YEAR - timedelta(days=7))
    with pytest.raises(HTTPException) as err:
        service.update(db, b, LeaveCompRequestUpdate(work_date=a.work_date), _user(emp))
    assert err.value.status_code == 409
    db.rollback()


# ── 7. Báo cáo quỹ trừ phần chưa tới tháng ──────────────────────────────────

def _monthly_world(db, world, n_people):
    world.grant("a1", "leave_balance", scope="all", actions=("read",))
    world.grant("a1", "employee", scope="all", actions=("read",))
    db.query(Employee).update({Employee.status: "resigned"})
    lt = LeaveType(code="MON", name="Phép cộng dần", counts_balance=True, accrual_mode=int(LeaveAccrualMode.MONTHLY))
    db.add(lt)
    db.flush()
    rows = []
    for i in range(n_people):
        emp = Employee(code=f"M{i}", full_name=f"NV M{i}", company_id=world.co["A"],
                       department_id=world.dept["A.kt"], hire_date=date(2020, 1, 1))
        db.add(emp)
        db.flush()
        row = LeaveBalance(employee_id=emp.id, year=TODAY.year, leave_type_id=lt.id, company_id=world.co["A"],
                           allocated_days=12.0, used_days=1.0)
        db.add(row)
        rows.append(row)
    db.commit()
    return rows


def _report(db, world):
    actor = world.actor("a1")
    period = parse_period({"preset": "custom", "date_from": f"{TODAY.year}-01-01",
                           "date_to": f"{TODAY.year}-12-31", "compare": "none"})
    return balance_report_service.build_summary(db, actor.user, actor.profile(), period, None)


def test_balance_report_remaining_matches_available_days(db, world):
    rows = _monthly_world(db, world, 2)
    expected = round(sum(balance_service.available_days(db, r) for r in rows), 2)
    totals = _report(db, world)["totals"]["current"]
    assert totals["remaining"] == expected
    if TODAY.month < 12:
        assert expected < sum(r.remaining_days for r in rows)     # có phần bị giữ lại thật


def test_balance_report_query_count_is_constant(db, world):
    from lich_lam_viec_factory import count_queries
    _monthly_world(db, world, 2)
    _report(db, world)      # chạy nóng một lần: nạp người dùng / hồ sơ quyền vào phiên, không tính vào số đếm
    _, few = count_queries(db, lambda: _report(db, world))
    _monthly_world_more(db, world)
    _report(db, world)
    _, many = count_queries(db, lambda: _report(db, world))
    assert len(many) == len(few)


def _monthly_world_more(db, world):
    lt = db.query(LeaveType).filter_by(code="MON").one()
    for i in range(10, 16):
        emp = Employee(code=f"M{i}", full_name=f"NV M{i}", company_id=world.co["A"],
                       department_id=world.dept["A.kt"], hire_date=date(2021, 3, 1))
        db.add(emp)
        db.flush()
        db.add(LeaveBalance(employee_id=emp.id, year=TODAY.year, leave_type_id=lt.id, company_id=world.co["A"],
                            allocated_days=12.0))
    db.commit()


# ── 8. available_days: hằng số + nạp sẵn ────────────────────────────────────

def test_available_days_map_matches_single_calls_with_constant_queries(db, world):
    from lich_lam_viec_factory import count_queries
    rows = _monthly_world(db, world, 5)
    single = {r.id: balance_service.available_days(db, r) for r in rows}
    db.expire_all()
    result, queries = count_queries(db, lambda: balance_service.available_days_map(
        db, db.query(LeaveBalance).all()))
    assert result == single
    assert len(queries) <= 3        # quỹ + loại nghỉ + ngày vào làm, không theo số dòng


# ── 9. my-balance trả max_negative_days ─────────────────────────────────────

def test_my_balance_returns_max_negative_days(db, world):
    world.grant("a1", "leave_request", scope="own", actions=("read",))
    lt = LeaveType(code="UNG", name="Phép ứng", counts_balance=True, annual_quota_days=5.0, max_negative_days=2.0)
    db.add(lt)
    db.flush()
    actor = world.actor("a1")
    emp = db.get(Employee, world.emp["a1"])
    out = request_controller.my_balance(lt.id, TODAY.year, emp.id, db=db, user=actor.user)
    import json
    body = json.loads(out.body)["data"]
    assert body["max_negative_days"] == 2.0 and "remaining_days" in body
