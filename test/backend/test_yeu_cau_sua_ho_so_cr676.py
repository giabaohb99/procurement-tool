"""
test_yeu_cau_sua_ho_so_cr676.py — duoc-CR-676 (HR2-2 / C6): nhân viên TỰ KHAI sửa hồ sơ, phòng
Nhân sự DUYỆT. Nhóm Liên hệ vẫn áp ngay ở `/me/contact` (không thuộc bộ này).

Cố làm cửa mới SAI, xếp theo mức thiệt hại nếu vỡ:
  1. Ghi lọt ô ngoài danh sách cho phép (phòng ban, điện thoại…) qua cửa mở cho mọi tài khoản.
  2. Nhân sự ngoài phạm vi thấy / duyệt được yêu cầu của người khác; tự duyệt chính mình.
  3. Duyệt hay xem giá trị nhạy cảm (TK ngân hàng, CCCD, người thân) mà thiếu `employee_sensitive.read`.
  4. Giá trị nhạy cảm lọt vào nhật ký yêu cầu / nhật ký thay đổi.
"""
import json
import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.logging_codes import ACTOR_KIND_USER
from app.core.logging_policy import MASKED
from app.core.request_context import RequestContext, reset_context, set_context
from app.core.request_middleware import RequestContextMiddleware
from app.main import validation_exception_handler
from app.modules.audit.model import AuditLog
from app.modules.employee import change_request_service as svc
from app.modules.employee.change_request_model import EmployeeChangeRequest
from app.modules.employee.contact_model import EmployeeFamily
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.request_log.model import RequestLog
from hdld_factory import client_as  # noqa: F401 — fixture TestClient đăng nhập giả

BASE = "/api/employees"
SECRET_BANK = "9704229999888877"
SECRET_ID = "079199001234"
ALL_RW = ("read", "write")


def _ok(res, code=200):
    assert res.status_code == code, res.text
    return res.json()["data"]


@pytest.fixture
def w(world, db):
    """a1 = người gửi (không quyền gì) · a2 = nhân sự duyệt (employee.write phạm vi pháp nhân A)
    · b1 = nhân sự pháp nhân B (ngoài phạm vi của a2)."""
    emp = db.get(Employee, world.emp["a1"])
    emp.place_of_birth, emp.ethnicity = "Hà Nội", "Kinh"
    emp.bank_account_no, emp.bank_name = "OLD-BANK", "ACB"
    db.commit()
    world.grant("a2", "employee", "company", actions=ALL_RW)
    return world


def _grant_sensitive(world, key):
    world.grant(key, "employee_sensitive", "all", actions=("read",))


def _submit(client, **body):
    return client.post(f"{BASE}/me/change-requests", json=body)


FULL = {"personal": {"place_of_birth": "Hà Nội", "ethnicity": "Tày"},
        "bank": {"bank_name": "VCB", "bank_account_no": SECRET_BANK},
        "families": [{"full_name": "Nguyễn Mẹ", "relation": 1, "phone": "0909123456",
                      "id_number": SECRET_ID}],
        "note": "Cập nhật theo CCCD mới"}


# ── 1. Gửi: chỉ giữ ô khác thật ─────────────────────────────────────────────

def test_submit_stores_only_changed_fields(w, client_as):
    me = client_as(w.actor("a1"))
    data = _ok(_submit(me, **FULL))
    keys = {(i["group"], i["field"]) for i in data["items"]}
    #  place_of_birth giống hồ sơ → không có; ethnicity/bank_name/bank_account_no đổi thật.
    assert keys == {("personal", "ethnicity"), ("bank", "bank_name"), ("bank", "bank_account_no")}
    eth = next(i for i in data["items"] if i["field"] == "ethnicity")
    assert (eth["before"], eth["after"], eth["current"], eth["masked"]) == ("Kinh", "Tày", "Kinh", False)
    assert data["status"] == 1 and data["note"] == "Cập nhật theo CCCD mới"
    assert data["families"]["before"] == [] and data["families"]["after"][0]["full_name"] == "Nguyễn Mẹ"
    assert data["has_sensitive"] is True and data["can_decide"] is False


def test_submit_without_any_difference_is_400(w, client_as):
    res = _submit(client_as(w.actor("a1")), personal={"ethnicity": "Kinh"}, families=[])
    assert res.status_code == 400 and "Không có thay đổi nào để gửi" in res.text


def test_submit_account_without_employee_is_400(world, db, client_as):
    from app.modules.user.model import User
    u = User(email="chua.gan@dego.vn", employee_id=0, is_active=True)
    db.add(u)
    db.commit()
    assert _submit(client_as(u), personal={"ethnicity": "Tày"}).status_code == 400


@pytest.mark.parametrize("body", [
    {"personal": {"department_id": 3}},
    {"personal": {"phone": "0900000000"}},
    {"bank": {"company_id": 2}},
    {"documents": {"bank_name": "VCB"}},
    {"contact": {"phone": "1"}},
    {"personal": {"ethnicity": None}},
    {"personal": {"gender": 9}},
    {"personal": {"marital_status": 99}},
])
def test_unknown_or_forbidden_field_is_422_and_nothing_stored(w, db, client_as, body):
    res = _submit(client_as(w.actor("a1")), **body)
    assert res.status_code == 422, res.text
    assert db.query(EmployeeChangeRequest).count() == 0


def test_nullable_date_can_be_cleared(w, db, client_as):
    emp = db.get(Employee, w.emp["a1"])
    from datetime import date
    emp.date_of_birth = date(1990, 1, 2)
    db.commit()
    data = _ok(_submit(client_as(w.actor("a1")), personal={"date_of_birth": None}))
    assert data["items"][0]["before"] == "1990-01-02" and data["items"][0]["after"] is None


def test_second_pending_is_409(w, client_as):
    me = client_as(w.actor("a1"))
    _ok(_submit(me, personal={"ethnicity": "Tày"}))
    assert _submit(me, personal={"ethnicity": "Mường"}).status_code == 409


# ── 2. Giới hạn độ dài ──────────────────────────────────────────────────────

@pytest.mark.parametrize("body", [
    {"note": "x" * 501},
    {"personal": {"place_of_birth": "x" * 256}},
    {"bank": {"bank_account_no": "9" * 51}},
    {"documents": {"id_number": "9" * 21}},
    {"families": [{"full_name": "x" * 256}]},
    {"families": [{"full_name": f"Người {i}"} for i in range(31)]},
])
def test_over_length_is_422(w, db, client_as, body):
    assert _submit(client_as(w.actor("a1")), **body).status_code == 422
    assert db.query(EmployeeChangeRequest).count() == 0


# ── 3. Rút lại / danh sách của mình ─────────────────────────────────────────

def test_withdraw_then_submit_again(w, client_as):
    me = client_as(w.actor("a1"))
    rid = _ok(_submit(me, personal={"ethnicity": "Tày"}))["id"]
    assert _ok(me.post(f"{BASE}/me/change-requests/{rid}/withdraw"))["status"] == 4
    assert me.post(f"{BASE}/me/change-requests/{rid}/withdraw").status_code == 409
    _ok(_submit(me, personal={"ethnicity": "Mường"}))
    items = _ok(me.get(f"{BASE}/me/change-requests"))["items"]
    assert [i["status"] for i in items] == [1, 4]   # mới nhất trước


def test_cannot_withdraw_someone_elses_request(w, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))["id"]
    assert client_as(w.actor("a3")).post(f"{BASE}/me/change-requests/{rid}/withdraw").status_code == 404
    assert _ok(client_as(w.actor("a3")).get(f"{BASE}/me/change-requests"))["items"] == []


# ── 4. Nhân sự: phạm vi ─────────────────────────────────────────────────────

def test_hr_list_detail_and_count_are_scoped(w, client_as):
    w.grant("b1", "employee", "company", actions=ALL_RW)
    rid = _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))["id"]
    hr, other = client_as(w.actor("a2")), client_as(w.actor("b1"))

    page = _ok(hr.get(f"{BASE}/change-requests"))
    assert page["total"] == 1 and page["items"][0]["employee_code"] == "A1"
    assert _ok(hr.get(f"{BASE}/change-requests/{rid}"))["id"] == rid
    assert _ok(hr.get(f"{BASE}/change-requests/pending-count")) == {"count": 1}
    assert _ok(hr.get(f"{BASE}/change-requests?q=Nhân sự a1"))["total"] == 1
    assert _ok(hr.get(f"{BASE}/change-requests?status=2"))["total"] == 0

    assert _ok(other.get(f"{BASE}/change-requests"))["total"] == 0
    assert _ok(other.get(f"{BASE}/change-requests/pending-count")) == {"count": 0}
    assert other.get(f"{BASE}/change-requests/{rid}").status_code == 404
    assert other.post(f"{BASE}/change-requests/{rid}/approve").status_code == 404
    assert other.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": "x"}).status_code == 404


def test_hr_routes_need_employee_write(w, client_as):
    assert client_as(w.actor("a1")).get(f"{BASE}/change-requests").status_code == 403
    w.grant("a3", "employee", "company", actions=("read",))
    assert client_as(w.actor("a3")).get(f"{BASE}/change-requests/pending-count").status_code == 403


# ── 5. Duyệt ────────────────────────────────────────────────────────────────

def test_approve_applies_fields_families_and_notifies(w, db, client_as):
    _grant_sensitive(w, "a2")
    rid = _ok(_submit(client_as(w.actor("a1")), **FULL))["id"]
    hr = client_as(w.actor("a2"))
    assert _ok(hr.get(f"{BASE}/change-requests/{rid}"))["can_decide"] is True

    data = _ok(hr.post(f"{BASE}/change-requests/{rid}/approve"))
    assert data["status"] == 2 and data["decided_by_name"] == "Nhân sự a2" and data["decided_at"]

    db.expire_all()
    emp = db.get(Employee, w.emp["a1"])
    assert (emp.ethnicity, emp.bank_name, emp.bank_account_no) == ("Tày", "VCB", SECRET_BANK)
    fam = db.query(EmployeeFamily).filter_by(employee_id=emp.id).all()
    assert [(f.full_name, f.id_number) for f in fam] == [("Nguyễn Mẹ", SECRET_ID)]
    note = db.query(Notification).filter_by(user_id=w.user_id("a1")).one()
    assert note.title == "Yêu cầu sửa hồ sơ đã được duyệt"
    msg = [a.message for a in db.query(AuditLog).filter_by(entity="employee", entity_id=emp.id)]
    assert any("Duyệt yêu cầu sửa hồ sơ" in m for m in msg) and any("Gửi yêu cầu" in m for m in msg)
    #  Không chép GIÁ TRỊ nhạy cảm vào dòng nhật ký thao tác.
    assert not any(SECRET_BANK in m or SECRET_ID in m for m in msg)
    assert hr.post(f"{BASE}/change-requests/{rid}/approve").status_code == 409


def test_apply_request_writes_field_level_change_log(w, db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    ctx = RequestContext(request_id=uuid.uuid4().bytes, user_id=7, actor_kind=ACTOR_KIND_USER)
    token = set_context(ctx)
    try:
        emp = db.get(Employee, w.emp["a1"])
        req = EmployeeChangeRequest(
            employee_id=emp.id, status=1, created_by=1, updated_by=1,
            changes=[{"group": "personal", "field": "ethnicity", "before": "Kinh", "after": "Tày"},
                     {"group": "bank", "field": "bank_name", "before": "ACB", "after": "VCB"}])
        db.add(req)
        db.commit()
        ctx.changes = []
        svc.apply_request(db, req, emp, 9)
        db.commit()
        fields = {e.field: e for e in ctx.changes if e.table_name == "tab_employee"}
        assert fields["ethnicity"].before_value == "Kinh" and fields["ethnicity"].after_value == "Tày"
        assert fields["bank_name"].is_masked and fields["bank_name"].after_value is None
    finally:
        reset_context(token)


def test_self_approve_is_blocked(w, db, client_as):
    _grant_sensitive(w, "a2")
    me_hr = client_as(w.actor("a2"))
    rid = _ok(_submit(me_hr, personal={"ethnicity": "Tày"}))["id"]
    detail = _ok(me_hr.get(f"{BASE}/change-requests/{rid}"))
    assert detail["can_decide"] is False
    for url, kw in ((f"approve", {}), ("reject", {"json": {"reason": "x"}})):
        res = me_hr.post(f"{BASE}/change-requests/{rid}/{url}", **kw)
        assert res.status_code == 403 and "tự duyệt" in res.text
    db.expire_all()
    assert db.get(Employee, w.emp["a2"]).ethnicity != "Tày"


def test_sensitive_request_cannot_be_approved_without_sensitive_read(w, db, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), **FULL))["id"]
    hr = client_as(w.actor("a2"))
    assert _ok(hr.get(f"{BASE}/change-requests/{rid}"))["can_decide"] is False
    res = hr.post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 403 and "employee_sensitive.read" in res.text
    db.expire_all()
    assert db.get(Employee, w.emp["a1"]).bank_name == "ACB"
    assert db.get(EmployeeChangeRequest, rid).status == 1


def test_non_sensitive_request_can_be_approved_without_sensitive_read(w, db, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))["id"]
    hr = client_as(w.actor("a2"))
    assert _ok(hr.get(f"{BASE}/change-requests/{rid}"))["can_decide"] is True
    assert _ok(hr.post(f"{BASE}/change-requests/{rid}/approve"))["status"] == 2


def test_approve_is_atomic_when_apply_fails(w, db, client_as, monkeypatch):
    _grant_sensitive(w, "a2")
    rid = _ok(_submit(client_as(w.actor("a1")), **FULL))["id"]

    def boom(*a, **k):
        raise RuntimeError("hỏng giữa chừng")
    monkeypatch.setattr("app.modules.employee.contact_service.set_families", boom)
    res = TestClient(client_as(w.actor("a2")).app, raise_server_exceptions=False,
                     headers=client_as(w.actor("a2")).headers).post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 500
    db.expire_all()
    assert db.get(Employee, w.emp["a1"]).bank_name == "ACB"        # hồ sơ nguyên vẹn
    assert db.get(EmployeeChangeRequest, rid).status == 1          # yêu cầu vẫn chờ


# ── 6. Che nhạy cảm theo người xem ──────────────────────────────────────────

def test_detail_masks_sensitive_for_hr_without_sensitive_read(w, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), **FULL))["id"]
    data = _ok(client_as(w.actor("a2")).get(f"{BASE}/change-requests/{rid}"))
    by = {i["field"]: i for i in data["items"]}
    assert by["ethnicity"]["after"] == "Tày" and by["ethnicity"]["masked"] is False
    for f in ("bank_name", "bank_account_no"):
        assert by[f]["masked"] is True
        assert by[f]["before"] is by[f]["after"] is by[f]["current"] is None
    assert data["families"] == {"before": None, "after": None, "current": None, "masked": True}
    assert SECRET_BANK not in json.dumps(data) and SECRET_ID not in json.dumps(data)
    #  Danh sách cũng che.
    page = _ok(client_as(w.actor("a2")).get(f"{BASE}/change-requests"))
    assert SECRET_BANK not in json.dumps(page) and SECRET_ID not in json.dumps(page)


def test_owner_and_sensitive_reader_see_values(w, client_as):
    me = client_as(w.actor("a1"))
    rid = _ok(_submit(me, **FULL))["id"]
    own = _ok(me.get(f"{BASE}/me/change-requests"))["items"][0]
    assert any(i["after"] == SECRET_BANK and not i["masked"] for i in own["items"])
    assert own["families"]["after"][0]["id_number"] == SECRET_ID

    _grant_sensitive(w, "a2")
    seen = _ok(client_as(w.actor("a2")).get(f"{BASE}/change-requests/{rid}"))
    assert any(i["after"] == SECRET_BANK and i["current"] == "OLD-BANK" for i in seen["items"])
    assert seen["families"]["masked"] is False


# ── 7. Từ chối ──────────────────────────────────────────────────────────────

def test_reject_needs_reason_and_notifies(w, db, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))["id"]
    hr = client_as(w.actor("a2"))
    for body in ({}, {"reason": ""}, {"reason": "   "}, {"reason": "x" * 501}):
        assert hr.post(f"{BASE}/change-requests/{rid}/reject", json=body).status_code == 422
    data = _ok(hr.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": "Thiếu bản sao CCCD"}))
    assert data["status"] == 3 and data["reject_reason"] == "Thiếu bản sao CCCD"
    note = db.query(Notification).filter_by(user_id=w.user_id("a1")).one()
    assert "từ chối" in note.title and "Thiếu bản sao CCCD" in note.body
    db.expire_all()
    assert db.get(Employee, w.emp["a1"]).ethnicity == "Kinh"
    assert hr.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": "x"}).status_code == 409
    mine = _ok(client_as(w.actor("a1")).get(f"{BASE}/me/change-requests"))["items"][0]
    assert mine["reject_reason"] == "Thiếu bản sao CCCD"


# ── 8. /me/families (C5) ────────────────────────────────────────────────────

def test_my_families_returns_only_own(w, db, client_as):
    db.add_all([EmployeeFamily(employee_id=w.emp["a1"], full_name="Mẹ của a1", relation=1,
                               id_number=SECRET_ID),
                EmployeeFamily(employee_id=w.emp["a3"], full_name="Mẹ của a3", relation=1)])
    db.commit()
    items = _ok(client_as(w.actor("a1")).get(f"{BASE}/me/families"))["items"]
    assert [i["full_name"] for i in items] == ["Mẹ của a1"] and items[0]["id_number"] == SECRET_ID
    assert [i["full_name"] for i in _ok(client_as(w.actor("a3")).get(f"{BASE}/me/families"))["items"]] \
        == ["Mẹ của a3"]


def test_my_families_account_without_employee_is_400(world, db, client_as):
    from app.modules.user.model import User
    u = User(email="chua.gan2@dego.vn", employee_id=0, is_active=True)
    db.add(u)
    db.commit()
    assert client_as(u).get(f"{BASE}/me/families").status_code == 400


# ── 9. Rò rỉ qua nhật ký ────────────────────────────────────────────────────

@pytest.fixture
def log_client(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    async def echo(request: Request):
        return {"success": True, "message": "ok", "data": {"id": 5, "echo": await request.json()}}

    app.add_api_route(f"{BASE}/me/change-requests", echo, methods=["POST"])
    return TestClient(app)


def test_request_log_masks_nested_sensitive_values(log_client, db):
    log_client.post(f"{BASE}/me/change-requests", json=FULL)
    row = db.query(RequestLog).order_by(RequestLog.id.desc()).first()
    raw = json.dumps([row.request_body, row.response_body], ensure_ascii=False)
    for secret in (SECRET_BANK, SECRET_ID, "0909123456", "Nguyễn Mẹ"):
        assert secret not in raw
    assert row.request_body["bank"]["bank_account_no"] == MASKED
    assert row.request_body["families"] == MASKED
    #  Ô thường vẫn giữ để tra «ai đổi gì».
    assert row.request_body["personal"]["ethnicity"] == "Tày"


def test_change_tracker_masks_change_request_content(w, db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    ctx = RequestContext(request_id=uuid.uuid4().bytes, user_id=7, actor_kind=ACTOR_KIND_USER)
    token = set_context(ctx)
    try:
        ctx.changes = []
        req = EmployeeChangeRequest(
            employee_id=w.emp["a1"], status=1, created_by=7, updated_by=7, note="ghi chú riêng",
            changes=[{"group": "bank", "field": "bank_account_no", "before": "a", "after": SECRET_BANK}],
            families={"before": [], "after": [{"full_name": "Nguyễn Mẹ", "id_number": SECRET_ID}]})
        db.add(req)
        db.commit()
        entry = next(e for e in ctx.changes if e.table_name == "tab_employee_change_request")
        raw = json.dumps(entry.snapshot, ensure_ascii=False)
        assert SECRET_BANK not in raw and SECRET_ID not in raw and "Nguyễn Mẹ" not in raw
        assert "ghi chú riêng" not in raw
        assert entry.snapshot["employee_id"] == str(w.emp["a1"]) and entry.snapshot["status"] == "1"
        ctx.changes = []
        req.status = 2
        req.reject_reason = "bí mật"
        db.commit()
        fields = {e.field: e for e in ctx.changes if e.table_name == "tab_employee_change_request"}
        assert fields["status"].after_value == "2"
        assert fields["reject_reason"].is_masked and fields["reject_reason"].after_value is None
    finally:
        reset_context(token)


# ── 10. Dọn khi xóa hồ sơ ───────────────────────────────────────────────────

def test_delete_all_of_removes_requests(w, db, client_as):
    from app.modules.employee import contact_service
    _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))
    contact_service.delete_all_of(db, w.emp["a1"])
    assert db.query(EmployeeChangeRequest).count() == 0


# ── 11. Vòng review: race, hộ gia đình cũ, lọc, thông báo lỗi, nhật ký ─────

def test_unique_pending_key_blocks_double_pending_even_if_check_passes(w, db, client_as, monkeypatch):
    """Hai lượt gửi đồng thời cùng qua bước kiểm → chỉ mục duy nhất giữ một, lượt sau nhận 409."""
    me = client_as(w.actor("a1"))
    _ok(_submit(me, personal={"ethnicity": "Tày"}))
    monkeypatch.setattr("app.modules.employee.change_request_service.pending_of", lambda *a, **k: None)
    res = _submit(me, personal={"ethnicity": "Mường"})
    assert res.status_code == 409 and "chờ duyệt" in res.text
    assert db.query(EmployeeChangeRequest).count() == 1


def test_pending_slot_is_released_on_withdraw_approve_reject(w, db, client_as):
    me, hr = client_as(w.actor("a1")), client_as(w.actor("a2"))
    for action in ("withdraw", "approve", "reject"):
        rid = _ok(_submit(me, personal={"ethnicity": f"Dân tộc {action}"}))["id"]
        if action == "withdraw":
            _ok(me.post(f"{BASE}/me/change-requests/{rid}/withdraw"))
        elif action == "approve":
            _ok(hr.post(f"{BASE}/change-requests/{rid}/approve"))
        else:
            _ok(hr.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": "không"}))
        assert db.get(EmployeeChangeRequest, rid).pending_employee_id is None


def test_withdraw_does_not_overwrite_decided_request(w, db, client_as):
    me = client_as(w.actor("a1"))
    rid = _ok(_submit(me, personal={"ethnicity": "Tày"}))["id"]
    _ok(client_as(w.actor("a2")).post(f"{BASE}/change-requests/{rid}/approve"))
    assert me.post(f"{BASE}/me/change-requests/{rid}/withdraw").status_code == 409
    assert db.get(EmployeeChangeRequest, rid).status == 2


def test_approve_is_409_when_families_changed_after_submit_and_detail_shows_current(w, db, client_as):
    _grant_sensitive(w, "a2")
    rid = _ok(_submit(client_as(w.actor("a1")), families=[{"full_name": "Người mới", "relation": 1}]))["id"]
    #  Nhân sự sửa danh sách hộ gia đình SAU lúc gửi.
    db.add(EmployeeFamily(employee_id=w.emp["a1"], full_name="HR vừa thêm", relation=2))
    db.commit()
    hr = client_as(w.actor("a2"))
    fam = _ok(hr.get(f"{BASE}/change-requests/{rid}"))["families"]
    assert fam["before"] == [] and [r["full_name"] for r in fam["current"]] == ["HR vừa thêm"]
    res = hr.post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 409 and "hộ gia đình đã bị sửa" in res.text
    db.expire_all()
    assert db.get(EmployeeChangeRequest, rid).status == 1
    assert [f.full_name for f in db.query(EmployeeFamily).filter_by(employee_id=w.emp["a1"])] == ["HR vừa thêm"]
    assert hr.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": "Gửi lại"}).status_code == 200


def test_families_current_is_masked_without_sensitive_read(w, client_as):
    rid = _ok(_submit(client_as(w.actor("a1")), families=[{"full_name": "Mẹ", "relation": 1}]))["id"]
    fam = _ok(client_as(w.actor("a2")).get(f"{BASE}/change-requests/{rid}"))["families"]
    assert fam == {"before": None, "after": None, "current": None, "masked": True}


def test_employee_id_filter_is_exact(w, client_as):
    _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))
    _ok(_submit(client_as(w.actor("a3")), personal={"ethnicity": "Tày"}))
    hr = client_as(w.actor("a2"))
    w.grant("a2", "employee", "all", actions=ALL_RW)
    assert _ok(hr.get(f"{BASE}/change-requests"))["total"] == 2
    page = _ok(hr.get(f"{BASE}/change-requests?employee_id={w.emp['a1']}"))
    assert page["total"] == 1 and page["items"][0]["employee_id"] == w.emp["a1"]
    assert _ok(hr.get(f"{BASE}/change-requests?employee_id=999999"))["total"] == 0


def test_search_escapes_like_wildcards(w, client_as):
    _ok(_submit(client_as(w.actor("a1")), personal={"ethnicity": "Tày"}))
    hr = client_as(w.actor("a2"))
    assert _ok(hr.get(f"{BASE}/change-requests?q=%25"))["total"] == 0    # '%' không phải ký tự đại diện
    assert _ok(hr.get(f"{BASE}/change-requests?q=A_"))["total"] == 0     # '_' không khớp 1 ký tự bất kỳ
    assert _ok(hr.get(f"{BASE}/change-requests?q=A1"))["total"] == 1


def test_nested_validation_error_message_is_clean(w, client_as):
    res = _submit(client_as(w.actor("a1")), personal={"children_count": 99})
    assert res.status_code == 422
    raw = res.text
    assert "Số con nhận từ 0 đến 30" in raw
    assert "input_value" not in raw and "errors.pydantic.dev" not in raw


def test_audit_actions_for_submit_withdraw_reject_and_approve(w, db, client_as):
    me, hr = client_as(w.actor("a1")), client_as(w.actor("a2"))
    r1 = _ok(_submit(me, personal={"ethnicity": "Tày"}))["id"]
    _ok(me.post(f"{BASE}/me/change-requests/{r1}/withdraw"))
    r2 = _ok(_submit(me, personal={"ethnicity": "Mường"}))["id"]
    _ok(hr.post(f"{BASE}/change-requests/{r2}/reject", json={"reason": "không"}))
    r3 = _ok(_submit(me, personal={"ethnicity": "Thái"}))["id"]
    _ok(hr.post(f"{BASE}/change-requests/{r3}/approve"))
    acts = [a.action for a in db.query(AuditLog).filter_by(entity="employee", entity_id=w.emp["a1"]).order_by(AuditLog.id)]
    assert acts == ["submit", "withdraw", "submit", "reject", "submit", "update"]
