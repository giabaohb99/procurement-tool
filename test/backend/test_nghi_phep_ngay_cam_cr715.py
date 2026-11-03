"""duoc-CR-715 giai đoạn B — NGÀY CẤM NGHỈ (tab_leave_block_period).

Chốt: khớp pháp nhân / phòng / «mọi» · giao một phần · đơn nhiều khoảng có KHE không dính · cảnh báo không chặn lưu ·
duyệt chặng cuối bị chặn (cả bộ máy lẫn duyệt thẳng) · giao dịch cuộn lại sạch · vai trò miễn / quản trị qua · tắt dòng
cấm thì hết chặn · cửa lưu cài đặt · kẹp ngày ở cửa CRUD.

⚠️ Bài quan trọng nhất là `test_engine_final_approval_is_vetoed_and_rolled_back`: `entity_hooks.fire` NUỐT lỗi hook,
nên nếu chốt chặn chỉ ném HTTPException thường thì phiếu vẫn thành «Đã duyệt» còn đơn kẹt Chờ duyệt.
"""
import time
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core import app_settings
from app.modules.approval import action_service, instance_service
from app.modules.approval.entity_hooks import HookVeto
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalFlow, ApprovalNode, ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_APPROVED, INSTANCE_RUNNING
from app.modules.employee.model import Employee
from app.modules.leave import (approval_bridge, balance_service, block_period_service, catalog_controller,
                               request_controller, request_service)
from app.modules.leave.catalog_model import LeaveBlockPeriod, LeaveType
from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.period_spans import PeriodView
from app.modules.leave.schema import (LeaveBlockPeriodCreate, LeaveBlockPeriodUpdate, LeaveEstimateIn,
                                      LeaveRequestCreate)
from app.modules.role.model import Role
from app.modules.setting import service as setting_service
from app.modules.setting.model import Setting
from app.modules.user.model import UserRole

ACTOR = 1
ENTITY = "leave_request"
MON = date(2026, 1, 5)


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
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


def _emp(db, code, company=1, dept=7):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=company, department_id=dept, is_active=True)
    db.add(obj)
    db.flush()
    return obj


def _block(db, start, end, company=0, dept=0, reason="Chốt sổ", active=True):
    row = LeaveBlockPeriod(company_id=company, department_id=dept, from_date=start, to_date=end,
                           reason=reason, is_active=active, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.commit()
    return row


def _view(start, end=None):
    return PeriodView(from_date=start, to_date=end or start)


def _ids(rows):
    return [r.id for r in rows]


def _grant(db, user_id, code):
    role = db.query(Role).filter(Role.code == code).first() or Role(code=code, name=code)
    db.add(role)
    db.flush()
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()


def _user(emp, uid=ACTOR):
    return SimpleNamespace(id=uid, employee_id=emp.id)


# ── find_conflicts ──────────────────────────────────────────────────────────

def test_matches_taker_company_department_or_all(db):
    emp = _emp(db, "A1", company=1, dept=7)
    everyone = _block(db, MON, MON)
    my_company = _block(db, MON, MON, company=1)
    my_dept = _block(db, MON, MON, company=1, dept=7)
    other_company = _block(db, MON, MON, company=2)
    other_dept = _block(db, MON, MON, dept=8)
    got = _ids(block_period_service.find_conflicts(db, emp, [_view(MON)]))
    assert got == [everyone.id, my_company.id, my_dept.id]
    assert other_company.id not in got and other_dept.id not in got


def test_partial_overlap_counts_and_adjacent_day_does_not(db):
    emp = _emp(db, "A2")
    row = _block(db, date(2026, 1, 10), date(2026, 1, 20))
    assert _ids(block_period_service.find_conflicts(db, emp, [_view(date(2026, 1, 8), date(2026, 1, 10))])) == [row.id]
    assert _ids(block_period_service.find_conflicts(db, emp, [_view(date(2026, 1, 20), date(2026, 1, 25))])) == [row.id]
    assert block_period_service.find_conflicts(db, emp, [_view(date(2026, 1, 9))]) == []
    assert block_period_service.find_conflicts(db, emp, [_view(date(2026, 1, 21))]) == []


def test_gap_between_periods_is_not_a_conflict_but_any_period_hit_is(db):
    emp = _emp(db, "A3")
    in_gap = _block(db, date(2026, 1, 7), date(2026, 1, 7))
    periods = [_view(date(2026, 1, 5)), _view(date(2026, 1, 9))]      # khe: 6-8/01
    assert block_period_service.find_conflicts(db, emp, periods) == []
    hit = _block(db, date(2026, 1, 9), date(2026, 1, 9), reason="Kiểm kê")
    assert _ids(block_period_service.find_conflicts(db, emp, periods)) == [hit.id]
    assert in_gap.id not in _ids(block_period_service.find_conflicts(db, emp, periods))


def test_inactive_row_never_matches(db):
    emp = _emp(db, "A4")
    row = _block(db, MON, MON)
    row.is_active = False
    db.commit()
    assert block_period_service.find_conflicts(db, emp, [_view(MON)]) == []


def test_find_conflicts_runs_one_query(db):
    from sqlalchemy import event
    emp = _emp(db, "A5")
    _block(db, MON, MON)
    db.refresh(emp)   # commit làm hết hạn thuộc tính — nạp lại để chỉ đếm truy vấn của chính hàm
    seen = []
    event.listen(db.get_bind(), "before_cursor_execute", lambda *a: seen.append(a[2]))
    block_period_service.find_conflicts(db, emp, [_view(MON), _view(MON + timedelta(days=7))])
    assert len(seen) == 1


# ── Lập / sửa: cảnh báo, không chặn ─────────────────────────────────────────

def _create(db, leave_type, emp, start=MON, end=None):
    return request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id, employee_id=emp.id,
        from_date=start, to_date=end or start, reason="Việc riêng"), _user(emp))


def test_create_is_not_blocked_and_detail_exposes_block_conflicts(db, leave_type):
    emp = _emp(db, "B1")
    row = _block(db, MON, MON + timedelta(days=2), reason="Kiểm kê cuối năm")
    obj = _create(db, leave_type, emp)
    data = request_controller._dump(db, obj, {emp.id: emp.full_name}, {leave_type.id: leave_type.name})
    assert data["block_conflicts"] == [{"id": row.id, "from_date": MON, "to_date": MON + timedelta(days=2),
                                        "reason": "Kiểm kê cuối năm"}]
    clean = _create(db, leave_type, emp, MON + timedelta(days=14))
    assert request_controller._dump(db, clean, {}, {})["block_conflicts"] == []


def test_estimate_periods_returns_block_conflicts_for_form_warning(db, leave_type):
    emp = _emp(db, "B2")
    row = _block(db, date(2026, 1, 9), date(2026, 1, 9))
    body = LeaveEstimateIn(employee_id=emp.id, leave_type_id=leave_type.id, periods=[
        {"from_date": date(2026, 1, 5), "to_date": date(2026, 1, 5)},
        {"from_date": date(2026, 1, 9), "to_date": date(2026, 1, 9)}])
    out = request_controller.estimate_periods(body, db, _user(emp))
    conflicts = _body(out)["data"]["block_conflicts"]
    assert [c["id"] for c in conflicts] == [row.id]


def test_estimate_days_single_period_returns_block_conflicts(db, leave_type):
    emp = _emp(db, "B3")
    row = _block(db, date(2026, 1, 5), date(2026, 1, 6))
    out = request_controller.estimate_days(from_date="2026-01-06", to_date="2026-01-07", leave_type_id=leave_type.id,
                                           employee_id=emp.id, db=db, user=_user(emp))
    assert [c["id"] for c in _body(out)["data"]["block_conflicts"]] == [row.id]
    clear = request_controller.estimate_days(from_date="2026-01-07", to_date="2026-01-07", employee_id=emp.id,
                                             db=db, user=_user(emp))
    assert _body(clear)["data"]["block_conflicts"] == []


def _body(response):
    import json
    return json.loads(response.body)


# ── Duyệt chặng cuối ────────────────────────────────────────────────────────

def _flow(db, approver):
    row = ApprovalFlow(entity=ENTITY, code="NP-715", name="Duyệt nghỉ (715)", is_active=True,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(approver.id), created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _submit(db, leave_type, emp, days=2):
    user = _user(emp, 50)
    obj = _create(db, leave_type, emp, MON, MON + timedelta(days=days - 1))
    taker = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, taker, user, instance_id)
    db.commit()
    return obj, instance_id


def _pending_used(db, emp, leave_type):
    row = balance_service.get_balance(db, emp.id, 2026, leave_type.id)
    return (row.pending_days, row.used_days)


def test_engine_final_approval_is_vetoed_and_rolled_back(db, leave_type):
    emp, approver = _emp(db, "C1"), _emp(db, "C2")
    _flow(db, approver)
    _block(db, MON, MON, reason="Chốt sổ")
    obj, instance_id = _submit(db, leave_type, emp)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    assert _pending_used(db, emp, leave_type) == (2.0, 0.0)

    with pytest.raises(HTTPException) as err:
        action_service.approve(db, instance, approver.id, ACTOR, {})
    assert err.value.status_code == 422
    assert "05/01/2026" in err.value.detail and "Chốt sổ" in err.value.detail
    db.rollback()   # đúng việc `get_db` làm khi lỗi bay ra khỏi route

    instance = db.get(type(instance), instance_id)
    db.refresh(obj)
    assert instance.status == INSTANCE_RUNNING and instance.finished_at is None
    assert obj.status == LR_PENDING and obj.document_id == 0
    assert _pending_used(db, emp, leave_type) == (2.0, 0.0)   # quỹ vẫn giữ chỗ, chưa trừ
    assert instance_service.running_instance(db, ENTITY, obj.id) is not None


def test_veto_then_caller_commits_leaves_nothing_half_approved(db, leave_type):
    """Người gọi kiểu cổng MCP: bắt lỗi rồi VẪN commit (ghi nhật ký cuộc gọi) — không được ghi nửa chừng."""
    emp, approver = _emp(db, "C1B"), _emp(db, "C2B")
    _flow(db, approver)
    _block(db, MON, MON, reason="Chốt sổ")
    obj, instance_id = _submit(db, leave_type, emp)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    with pytest.raises(HTTPException):
        action_service.approve(db, instance, approver.id, ACTOR, {})
    db.commit()     # KHÔNG rollback ở đây: chính `fire` phải đã cuộn lại
    instance = db.get(type(instance), instance_id)
    db.refresh(obj)
    assert instance.status == INSTANCE_RUNNING and instance.finished_at is None
    assert obj.status == LR_PENDING
    assert _pending_used(db, emp, leave_type) == (2.0, 0.0)
    assert instance_service.running_instance(db, ENTITY, obj.id) is not None


def test_engine_final_approval_passes_for_exempt_role_and_admin(db, leave_type):
    emp, approver = _emp(db, "C3"), _emp(db, "C4")
    _flow(db, approver)
    db.add(Role(code="hr_profile", name="Nhân sự"))
    db.commit()
    setting_service.save(db, {"leave_block_exempt_roles": "hr_profile"}, user_id=ACTOR)
    _block(db, MON, MON)
    obj, _ = _submit(db, leave_type, emp)
    _grant(db, ACTOR, "hr_profile")
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, approver.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED and instance.status == INSTANCE_APPROVED
    assert _pending_used(db, emp, leave_type) == (0.0, 2.0)


def test_admin_is_always_exempt_even_with_empty_setting(db, leave_type):
    emp = _emp(db, "C5")
    _block(db, MON, MON)
    periods = [_view(MON)]
    with pytest.raises(HookVeto):
        block_period_service.ensure_approvable(db, emp, periods, 77)
    _grant(db, 77, "admin")
    block_period_service.ensure_approvable(db, emp, periods, 77)


def test_direct_approve_is_vetoed_without_touching_balance(db, leave_type):
    emp = _emp(db, "D1")
    _block(db, MON, MON + timedelta(days=1), reason="Kiểm kê")
    obj, instance_id = _submit(db, leave_type, emp)
    assert instance_id == 0   # chưa khai luồng → duyệt thẳng

    class _Direct:
        updated_by = 60
        finish_reason = ""

    with pytest.raises(HTTPException) as err:
        approval_bridge._on_approved(db, obj.id, _Direct())
    assert err.value.status_code == 422 and "Kiểm kê" in err.value.detail
    db.rollback()
    db.refresh(obj)
    assert obj.status == LR_PENDING
    assert _pending_used(db, emp, leave_type) == (2.0, 0.0)


def test_deactivated_block_no_longer_stops_approval(db, leave_type):
    emp = _emp(db, "D2")
    row = _block(db, MON, MON)
    obj, _ = _submit(db, leave_type, emp)
    row.is_active = False
    db.commit()

    class _Direct:
        updated_by = 61
        finish_reason = ""

    approval_bridge._on_approved(db, obj.id, _Direct())
    db.refresh(obj)
    assert obj.status == LR_APPROVED


# ── Cài đặt + CRUD ──────────────────────────────────────────────────────────

def test_exempt_roles_setting_is_in_hr_leave_tab_defaults_empty_and_validates_codes(db):
    field = next(f for f in setting_service.get_all()["fields"] if f["key"] == "leave_block_exempt_roles")
    assert (field["group"], field["tab"], field["type"]) == ("hr", "leave", "roles")
    assert app_settings.get("leave_block_exempt_roles") == ""
    db.add(Role(code="hr_profile", name="Nhân sự"))
    db.commit()
    with pytest.raises(HTTPException) as err:
        setting_service.save(db, {"leave_block_exempt_roles": "hr_profile,ma_bia"}, user_id=ACTOR)
    assert err.value.status_code == 400 and "ma_bia" in err.value.detail
    setting_service.save(db, {"leave_block_exempt_roles": " hr_profile ,,hr_profile "}, user_id=ACTOR)
    assert app_settings.get("leave_block_exempt_roles") == "hr_profile"


def test_schema_clamps_range_span_and_reason_length():
    ok = LeaveBlockPeriodCreate(from_date=MON, to_date=MON)
    assert ok.company_id == 0 and ok.department_id == 0 and ok.is_active
    with pytest.raises(ValidationError):
        LeaveBlockPeriodCreate(from_date=MON, to_date=MON - timedelta(days=1))
    LeaveBlockPeriodCreate(from_date=MON, to_date=MON + timedelta(days=365))   # đúng 366 ngày
    with pytest.raises(ValidationError):
        LeaveBlockPeriodCreate(from_date=MON, to_date=MON + timedelta(days=366))
    with pytest.raises(ValidationError):
        LeaveBlockPeriodCreate(from_date=MON, to_date=MON, reason="x" * 256)
    with pytest.raises(ValidationError):
        LeaveBlockPeriodUpdate(reason="x" * 256)
    with pytest.raises(ValidationError):
        LeaveBlockPeriodCreate(from_date=date(1900, 1, 1), to_date=date(1900, 1, 2))


def test_update_validates_range_after_merging_with_current_values(db):
    row = _block(db, MON, MON + timedelta(days=3))
    with pytest.raises(HTTPException) as err:
        catalog_controller._check_block_update(db, row, {"to_date": MON - timedelta(days=1)})
    assert err.value.status_code == 422
    catalog_controller._check_block_update(db, row, {"to_date": MON + timedelta(days=9)})
