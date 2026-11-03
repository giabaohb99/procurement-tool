"""duoc-CR-713 — Cài đặt nhân sự, tab Nghỉ phép: chặn đơn lùi ngày · chặn tự duyệt đơn nghỉ.

Bật công tắc bằng ĐÚNG đường lưu thật (`setting.service.save`) để chốt luôn cửa lưu (kiểm mã vai trò).
Ngày "hôm nay" ghim bằng cách thay `leave_policy.vn_today` — không viết khẳng định phụ thuộc ngày chạy.

⚠️ Bài quan trọng nhất là nhóm tự duyệt ở bước KHAI ĐÍCH DANH: luật I08 cũ CỐ Ý bỏ qua bước đó (CR-113, NP022),
nên công tắc mới phải gạt được người nghỉ ở đó — và KHÔNG được làm đổi hành vi khi công tắc tắt.
"""
import time
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, APPROVER_ROLE, NO_APPROVER_BLOCK,
                                             NO_APPROVER_FALLBACK,
                                             ApprovalFlow, ApprovalNode, ApprovalSwitch)
from app.modules.approval.instance_model import INSTANCE_BLOCKED, TASK_PENDING, ApprovalInstance
from app.modules.approval.self_approval_policy import ensure_not_self_approval
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, leave_policy, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_RETURNED
from app.modules.leave.schema import LeaveRequestCreate, LeaveRequestUpdate
from app.modules.role.model import Role
from app.modules.setting import service as setting_service
from app.modules.setting.model import Setting
from app.modules.user.model import UserRole

ACTOR = 1
ENTITY = "leave_request"
TODAY = date(2026, 11, 2)


@pytest.fixture(autouse=True)
def _settings_from_test_db(db, monkeypatch):
    """`app_settings` đọc DB của bài kiểm (bản thật mở MySQL), dọn đệm quanh mỗi bài; ghim ngày hôm nay."""
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    monkeypatch.setattr(leave_policy, "vn_today", lambda: TODAY)
    app_settings.refresh()
    yield
    app_settings.refresh()


@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="unpaid", name="Không lương", counts_balance=False)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, code):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=1, department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


def _user(employee, uid):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _grant_role(db, user_id, code):
    role = db.query(Role).filter(Role.code == code).first() or Role(code=code, name=code)
    db.add(role)
    db.flush()
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    return role


def _create(db, leave_type, user, employee, start):
    return request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id, employee_id=employee.id,
        from_date=start, to_date=start, reason="Việc riêng"), user)


# ── Cửa lưu ─────────────────────────────────────────────────────────────────

def test_save_rejects_unknown_role_codes_and_normalizes_the_list(db):
    db.add(Role(code="hr_profile", name="Nhân sự"))
    db.commit()
    with pytest.raises(HTTPException) as err:
        setting_service.save(db, {"leave_backdated_roles": "hr_profile, khong_co"}, user_id=ACTOR)
    assert err.value.status_code == 400 and "khong_co" in err.value.detail
    #  Trùng + khoảng trắng + dấu phẩy thừa → một chuỗi sạch.
    setting_service.save(db, {"leave_backdated_roles": " hr_profile ,,hr_profile "}, user_id=ACTOR)
    assert app_settings.get("leave_backdated_roles") == "hr_profile"


def test_hr_fields_default_off_so_existing_behaviour_is_unchanged(db):
    assert app_settings.get("leave_restrict_backdated") is False
    assert app_settings.get("leave_prevent_self_approval") is False
    groups = {f["key"]: f["group"] for f in setting_service.get_all()["fields"]}
    assert {groups[k] for k in ("leave_restrict_backdated", "leave_backdated_roles",
                                "leave_prevent_self_approval")} == {"hr"}


# ── Chặn đơn lùi ngày ───────────────────────────────────────────────────────

def test_backdated_allowed_while_switch_is_off(db, leave_type):
    emp = _employee(db, "A1")
    obj = _create(db, leave_type, _user(emp, 11), emp, TODAY - timedelta(days=3))
    assert obj.id


def test_backdated_create_is_blocked_but_today_and_future_pass(db, leave_type):
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=ACTOR)
    emp = _employee(db, "A2")
    user = _user(emp, 12)
    with pytest.raises(HTTPException) as err:
        _create(db, leave_type, user, emp, TODAY - timedelta(days=1))
    assert err.value.status_code == 422 and "01/11/2026" in err.value.detail
    #  Biên: hôm nay KHÔNG phải ngày đã qua.
    assert _create(db, leave_type, user, emp, TODAY).id
    assert _create(db, leave_type, user, emp, TODAY + timedelta(days=5)).id


def test_whitelisted_role_and_admin_may_backdate(db, leave_type):
    db.add(Role(code="hr_profile", name="Nhân sự"))
    db.commit()
    setting_service.save(db, {"leave_restrict_backdated": True, "leave_backdated_roles": "hr_profile"},
                         user_id=ACTOR)
    #  Mỗi người tự lập đơn của mình — chốt "lập hộ" (phạm vi) là chuyện khác, không trộn vào bài này.
    hr = _employee(db, "HR1")
    _grant_role(db, 21, "hr_profile")
    assert _create(db, leave_type, _user(hr, 21), hr, TODAY - timedelta(days=10)).id
    admin = _employee(db, "AD1")
    _grant_role(db, 22, "admin")
    assert _create(db, leave_type, _user(admin, 22), admin, TODAY - timedelta(days=10)).id
    #  Vai trò KHÔNG có trong danh sách thì vẫn bị chặn.
    staff = _employee(db, "A3")
    _grant_role(db, 23, "nhan_vien")
    with pytest.raises(HTTPException):
        _create(db, leave_type, _user(staff, 23), staff, TODAY - timedelta(days=1))


def test_editing_dates_into_the_past_is_blocked(db, leave_type):
    emp = _employee(db, "A4")
    user = _user(emp, 14)
    obj = _create(db, leave_type, user, emp, TODAY + timedelta(days=2))
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=ACTOR)
    with pytest.raises(HTTPException) as err:
        request_service.update(db, obj, LeaveRequestUpdate(
            from_date=TODAY - timedelta(days=2), to_date=TODAY - timedelta(days=2)), user)
    assert err.value.status_code == 422


def test_draft_that_became_backdated_cannot_be_submitted(db, leave_type, monkeypatch):
    """Nháp lập khi còn hợp lệ (nghỉ hôm nay), để qua ngày mới bấm gửi — lúc gửi đã là đơn lùi ngày."""
    emp = _employee(db, "A5")
    user = _user(emp, 15)
    obj = _create(db, leave_type, user, emp, TODAY)
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=ACTOR)
    monkeypatch.setattr(leave_policy, "vn_today", lambda: TODAY + timedelta(days=1))
    with pytest.raises(HTTPException) as err:
        request_service.prepare_submit(db, obj, user)
    assert err.value.status_code == 422


def test_unchanged_stale_role_code_does_not_block_unrelated_saves(db):
    """Rà mã CR-713: màn Cấu hình hệ thống gửi lại MỌI ô — vai trò miễn bị xóa về sau không được chặn cả lần lưu."""
    role = Role(code="hcns_cu", name="HCNS cũ")
    db.add(role)
    db.commit()
    setting_service.save(db, {"leave_backdated_roles": "hcns_cu"}, user_id=ACTOR)
    db.delete(role)
    db.commit()
    setting_service.save(db, {"smtp_host": "smtp.example.com", "leave_backdated_roles": "hcns_cu"}, user_id=ACTOR)
    assert app_settings.get("smtp_host") == "smtp.example.com"
    #  Nhưng THÊM một mã không có thật thì vẫn bị chặn.
    with pytest.raises(HTTPException):
        setting_service.save(db, {"leave_backdated_roles": "hcns_cu,ma_bia"}, user_id=ACTOR)


def test_backdated_draft_can_still_edit_reason_without_touching_dates(db, leave_type):
    emp = _employee(db, "A6")
    user = _user(emp, 16)
    obj = _create(db, leave_type, user, emp, TODAY - timedelta(days=2))   # lập trước khi bật công tắc
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=ACTOR)
    request_service.update(db, obj, LeaveRequestUpdate(reason="Bổ sung giấy khám bệnh"), user)
    assert obj.reason == "Bổ sung giấy khám bệnh"


def test_returned_leave_with_past_dates_can_be_resubmitted(db, leave_type):
    emp = _employee(db, "A7")
    user = _user(emp, 17)
    #  Thứ Sáu 30/10 (TODAY là thứ Hai 02/11; Chủ nhật 01/11 không có ngày làm việc để gửi).
    obj = _create(db, leave_type, user, emp, TODAY - timedelta(days=3))
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=ACTOR)
    obj.status = LR_RETURNED   # đã gửi một lần (lúc đó hợp lệ), người duyệt trả về
    db.commit()
    request_service.prepare_submit(db, obj, user)   # không ném lỗi


def test_taker_may_submit_a_backdated_leave_that_exempt_hr_created(db, leave_type):
    db.add(Role(code="hr_profile", name="Nhân sự"))
    db.commit()
    setting_service.save(db, {"leave_restrict_backdated": True, "leave_backdated_roles": "hr_profile"},
                         user_id=ACTOR)
    hr = _employee(db, "HR2")
    _grant_role(db, 41, "hr_profile")
    obj = _create(db, leave_type, _user(hr, 41), hr, TODAY - timedelta(days=4))
    #  Giả lập "lập hộ": người nghỉ là nhân viên khác, người lập là HR được miễn.
    taker = _employee(db, "A8")
    obj.employee_id = taker.id
    db.commit()
    request_service.prepare_submit(db, obj, _user(taker, 42))   # không ném lỗi


# ── Chặn tự duyệt ───────────────────────────────────────────────────────────

def _flow(db, approver_ref, kind=APPROVER_EMPLOYEE, fallback_id=0):
    row = ApprovalFlow(entity=ENTITY, code="NP-713", name="Duyệt nghỉ (713)", is_active=True,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt", approver_kind=kind,
                        approver_ref=str(approver_ref),
                        on_no_approver=NO_APPROVER_FALLBACK if fallback_id else NO_APPROVER_BLOCK,
                        fallback_employee_id=fallback_id or None,
                        created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return row


def _start(db, leave_type, employee, uid):
    user = _user(employee, uid)
    obj = _create(db, leave_type, user, employee, TODAY + timedelta(days=3))
    request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    assert instance_id, "luồng phải được áp (cờ bật + có luồng)"
    return db.get(ApprovalInstance, instance_id)


def _assignees(db, instance):
    return [t.assignee_employee_id for t in instance_service.tasks_of_instance(db, instance.id)
            if t.status == TASK_PENDING]


def test_named_step_on_the_taker_keeps_old_behaviour_when_switch_off(db, leave_type):
    taker = _employee(db, "S1")
    _flow(db, taker.id)
    instance = _start(db, leave_type, taker, 31)
    #  Luật I08 cũ: bước khai đích danh giữ đúng người đã khai — kể cả là người nghỉ.
    assert _assignees(db, instance) == [taker.id]


def test_named_step_on_the_taker_goes_to_fallback_when_switch_on(db, leave_type):
    setting_service.save(db, {"leave_prevent_self_approval": True}, user_id=ACTOR)
    taker = _employee(db, "S2")
    backup = _employee(db, "S2B")
    _flow(db, taker.id, fallback_id=backup.id)
    instance = _start(db, leave_type, taker, 32)
    assert _assignees(db, instance) == [backup.id]


def test_named_step_with_taker_as_fallback_too_blocks_instead_of_self_approving(db, leave_type):
    setting_service.save(db, {"leave_prevent_self_approval": True}, user_id=ACTOR)
    taker = _employee(db, "S3")
    _flow(db, taker.id, fallback_id=taker.id)
    instance = _start(db, leave_type, taker, 33)
    db.refresh(instance)
    assert _assignees(db, instance) == []
    assert instance.status == INSTANCE_BLOCKED


def test_task_opened_before_switch_on_cannot_be_approved_by_the_taker(db, leave_type):
    taker = _employee(db, "S4")
    _flow(db, taker.id)
    instance = _start(db, leave_type, taker, 34)
    assert _assignees(db, instance) == [taker.id]
    setting_service.save(db, {"leave_prevent_self_approval": True}, user_id=ACTOR)
    with pytest.raises(HTTPException) as err:
        action_service.approve(db, instance, taker.id, 34, {})
    assert err.value.status_code == 403


def test_other_approvers_and_other_entities_are_untouched(db):
    setting_service.save(db, {"leave_prevent_self_approval": True}, user_id=ACTOR)
    #  Người khác duyệt đơn nghỉ: qua.
    ensure_not_self_approval(ENTITY, 5, 9)
    #  Chứng từ khác (văn bản) tự duyệt: luật này không đụng tới.
    ensure_not_self_approval("document", 9, 9)
    #  Không gắn nhân sự (0) không bao giờ bị coi là "chính mình".
    ensure_not_self_approval(ENTITY, 0, 0)
    with pytest.raises(HTTPException):
        ensure_not_self_approval(ENTITY, 9, 9)


def test_strict_flag_only_widens_exclusion_for_named_steps():
    ids = [3, 9]
    assert instance_service.exclude_submitter_ids(APPROVER_EMPLOYEE, 9, ids) == [3, 9]
    assert instance_service.exclude_submitter_ids(APPROVER_EMPLOYEE, 9, ids, strict=True) == [3]
    #  Bước suy ra thì luật cũ đã gạt sẵn — strict không đổi gì.
    assert instance_service.exclude_submitter_ids(APPROVER_ROLE, 9, ids) == [3]
    assert instance_service.exclude_submitter_ids(APPROVER_ROLE, 9, ids, strict=True) == [3]
    assert instance_service.exclude_submitter_ids(APPROVER_EMPLOYEE, None, ids, strict=True) == ids


# ── Tab Nhân viên ───────────────────────────────────────────────────────────

def test_code_prefix_is_validated_uppercased_and_used_for_new_employees(db):
    from app.modules.employee.service import employee_code_prefix

    assert employee_code_prefix() == "NSU"   # mặc định = giá trị từng viết cứng
    for bad in ("N", "NS1", "NSU-", "QUÁ", "ABCDEFGHIJK"):
        with pytest.raises(HTTPException):
            setting_service.save(db, {"employee_code_prefix": bad}, user_id=ACTOR)
    setting_service.save(db, {"employee_code_prefix": " dg "}, user_id=ACTOR)
    assert app_settings.get("employee_code_prefix") == "DG"
    assert employee_code_prefix() == "DG"
    #  Để trống = về mặc định.
    setting_service.save(db, {"employee_code_prefix": ""}, user_id=ACTOR)
    assert employee_code_prefix() == "NSU"


def test_anniversary_years_normalize_and_feed_monthly_reminders(db):
    from app.modules.employee.monthly_reminders_service import anniversary_years

    assert anniversary_years() == (1, 3, 5, 10)
    setting_service.save(db, {"employee_anniversary_years": "10; 2, 2 ,20"}, user_id=ACTOR)
    assert app_settings.get("employee_anniversary_years") == "2,10,20"
    assert anniversary_years() == (2, 10, 20)
    for bad in ("0", "61", "a,b", ",".join(str(n) for n in range(1, 12))):
        with pytest.raises(HTTPException):
            setting_service.save(db, {"employee_anniversary_years": bad}, user_id=ACTOR)


def _org_chart_status(db, actor):
    import uuid

    from fastapi.testclient import TestClient

    from app.core.auth import get_current_user
    from app.core.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: actor.user
    try:
        client = TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})
        return client.get("/api/org-chart").status_code
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_org_chart_switch_off_closes_it_to_scoped_viewers_only(db, world):
    world.grant("a1", "employee", scope="company", inc_company=("A",))
    world.grant("a2", "employee", scope="all")
    assert _org_chart_status(db, world.actor("a1")) == 200   # mặc định BẬT: như cũ
    setting_service.save(db, {"org_chart_visible_to_all": False}, user_id=ACTOR)
    assert _org_chart_status(db, world.actor("a1")) == 403
    assert _org_chart_status(db, world.actor("a2")) == 200   # xem được toàn bộ hồ sơ thì vẫn mở


# ── Tab Hợp đồng lao động ───────────────────────────────────────────────────

def test_contract_alert_days_validate_range_and_order(db):
    from app.modules.labor_contract import expiry_service

    assert (expiry_service.warn_days(), expiry_service.danger_days()) == (30, 15)
    with pytest.raises(HTTPException):   # dưới mốc luật 15 ngày
        setting_service.save(db, {"labor_contract_danger_days": 10}, user_id=ACTOR)
    with pytest.raises(HTTPException):   # trên trần cửa sổ API
        setting_service.save(db, {"labor_contract_warn_days": 181}, user_id=ACTOR)
    with pytest.raises(HTTPException):   # mức gấp lớn hơn số ngày báo (gửi lẻ một ô cũng không lách được)
        setting_service.save(db, {"labor_contract_danger_days": 40}, user_id=ACTOR)
    setting_service.save(db, {"labor_contract_warn_days": 60, "labor_contract_danger_days": 20}, user_id=ACTOR)
    assert (expiry_service.warn_days(), expiry_service.danger_days()) == (60, 20)
    assert expiry_service.level_of(20) == "danger" and expiry_service.level_of(21) == "warn"
