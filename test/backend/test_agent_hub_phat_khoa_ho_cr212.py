"""ai-CR-212 — phát khóa kết nối AI HỘ (K4 doc/erp/21 §5.3 + §4.3, bỏ phần Telegram theo §7.1).

Canh:
  - phát cho người trong phạm vi (phòng mình) → khóa CHỈ ĐỌC «chờ nhận» + chuông cho chủ khóa; khóa chưa nhận KHÔNG dùng
    được (cổng MCP 401, nhật ký ghi lý do);
  - nhận: khóa thô hiện đúng MỘT lần, bản niêm phong xóa trắng; lần hai / người khác → 404;
  - phát ngoài phạm vi / không có quyền → 403, không phát khóa nào; cả phòng ≤ 50 người; bỏ qua người đã đủ 5 khóa;
  - danh sách quản trị chỉ khóa của người trong phạm vi, lọc trạng thái / lượt phát;
  - thu hồi: theo khóa / theo người / cả lượt; chủ khóa ngoài phạm vi → 403 cả lệnh; dòng giữ lại «Đã thu hồi»;
  - cổng B: không quyền → allowed false; bản gọi từ xa đọc đúng.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.modules.agent_hub import controller, mcp_keys, mcp_log
from app.modules.agent_hub.model import AgentMcpCall, AgentMcpKey
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User

ENTITY = controller.KEY_ADMIN_ENTITY


def _json(resp):
    return json.loads(resp.body)["data"]


def _person(db, code: str, company_id: int, dept_id: int) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company_id, department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=f"{code.lower()}@test.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def org(db, seed, cap_quyen):
    other = Department(code="DEPT-K4", name="Phòng Khác", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    admin = _person(db, "QLK4", seed.company_id, seed.dept_id)
    cap_quyen(admin.id, ENTITY, scope="dept", read=True, create=True, delete=True)
    mate = db.get(User, seed.u_req_id)                      # cùng phòng với người phát
    outsider = _person(db, "NGOAI4", seed.company_id, other.id)
    return SimpleNamespace(admin=admin, mate=mate, outsider=outsider, other_dept=other)


def _issue(db, admin, **body):
    return _json(controller.key_admin_issue(controller.KeyIssueIn(**body), user=admin, db=db))


# ── Phát + nhận ───────────────────────────────────────────────────────────────

def test_phat_cho_nguoi_cung_phong_cho_nhan_chuong_va_nhan_mot_lan(db, org):
    out = _issue(db, org.admin, user_ids=[org.mate.id], days=30, name="Claude của chị")
    assert len(out["issued"]) == 1 and out["skipped"] == [] and out["batch_id"]
    row = db.get(AgentMcpKey, out["issued"][0]["key_id"])
    assert (row.user_id, row.issued_by, row.scope, row.batch_id) == (org.mate.id, org.admin.id, mcp_keys.SCOPE_READ,
                                                                     out["batch_id"])
    assert mcp_keys.state_of(row) == mcp_keys.KeyState.PENDING and row.raw_sealed and row.claimed_at is None
    bell = db.query(Notification).filter_by(user_id=org.mate.id).one()
    assert "chờ nhận" in bell.title and bell.link == controller.MY_AI_LINK

    raw = app_settings._decrypt(row.raw_sealed)
    assert raw.startswith(mcp_keys.PREFIX) and mcp_keys.authenticate(db, raw) is None         # chưa nhận: chưa dùng được
    assert mcp_keys.why_rejected(db, raw) == (row.id, mcp_log.REASON_UNCLAIMED)

    me = SimpleNamespace(id=org.mate.id)
    pending = _json(controller.list_my_pending_mcp_keys(user=me, db=db))["items"]
    assert [p["id"] for p in pending] == [row.id] and pending[0]["state_label"] == "Chờ nhận"
    with pytest.raises(HTTPException) as e:
        controller.claim_my_mcp_key(row.id, user=SimpleNamespace(id=org.outsider.id), db=db)   # không phải của mình
    assert e.value.status_code == 404
    got = _json(controller.claim_my_mcp_key(row.id, user=me, db=db))
    assert got["key"] == raw and got["state_label"] == "Đang dùng"
    db.refresh(row)
    assert row.raw_sealed == "" and row.claimed_at is not None and mcp_keys.authenticate(db, raw) is row
    with pytest.raises(HTTPException) as e:
        controller.claim_my_mcp_key(row.id, user=me, db=db)                                   # lần hai: không thấy khóa
    assert e.value.status_code == 404


def test_khoa_chua_nhan_qua_cong_mcp_bi_401_va_ghi_nhat_ky(db, org, monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})
    out = _issue(db, org.admin, user_ids=[org.mate.id], days=7)
    row = db.get(AgentMcpKey, out["issued"][0]["key_id"])
    raw = app_settings._decrypt(row.raw_sealed)
    app.dependency_overrides[get_db] = lambda: db
    try:
        res = TestClient(app).post("/api/mcp", content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
                                   headers={"Authorization": f"Bearer {raw}", "Content-Type": "application/json"})
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert res.status_code == 401
    log = db.query(AgentMcpCall).order_by(AgentMcpCall.id.desc()).first()
    assert (log.key_id, log.deny_reason) == (row.id, mcp_log.REASON_UNCLAIMED)


# ── Phạm vi + trần ────────────────────────────────────────────────────────────

def test_phat_ngoai_pham_vi_hoac_khong_quyen_bi_chan_khong_phat_gi(db, org):
    with pytest.raises(HTTPException) as e:
        _issue(db, org.admin, user_ids=[org.mate.id, org.outsider.id], days=30)
    assert e.value.status_code == 403 and "ngoài phạm vi" in e.value.detail
    with pytest.raises(HTTPException) as e:
        _issue(db, org.admin, department_id=org.other_dept.id, days=30)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        _issue(db, org.mate, user_ids=[org.admin.id], days=30)                    # không có quyền ai_mcp_key_admin
    assert e.value.status_code == 403
    assert db.query(AgentMcpKey).count() == 0


def test_phat_ca_phong_bo_qua_nguoi_du_khoa_va_kiem_tham_so(db, seed, org):
    for i in range(mcp_keys.MAX_KEYS):
        mcp_keys.create(db, org.mate.id, name=f"tự tạo {i}")
    out = _issue(db, org.admin, department_id=seed.dept_id, days=90)
    issued = {i["user_id"] for i in out["issued"]}
    assert org.admin.id in issued and org.mate.id not in issued and org.outsider.id not in issued
    assert [s["user_id"] for s in out["skipped"]] == [org.mate.id] and "đủ" in out["skipped"][0]["reason"]
    for bad, code in (({"user_ids": [org.mate.id], "days": 45}, 400), ({"days": 30}, 400),
                      ({"user_ids": list(range(1, 60)), "days": 30}, 400)):
        with pytest.raises(HTTPException) as e:
            _issue(db, org.admin, **bad)
        assert e.value.status_code == code


# ── Danh sách quản trị + thu hồi ──────────────────────────────────────────────

def _list(db, admin, **kw):
    args = {"department_id": 0, "state": None, "user_id": None, "batch_id": "", "page": 1, "size": 50, **kw}
    return _json(controller.key_admin_list(user=admin, db=db, **args))


def test_danh_sach_chi_trong_pham_vi_va_loc_trang_thai(db, org):
    out = _issue(db, org.admin, user_ids=[org.mate.id], days=30)
    mcp_keys.create(db, org.outsider.id, name="của người phòng khác")
    listed = _list(db, org.admin)
    assert listed["total"] == 1
    item = listed["items"][0]
    assert item["owner_label"] == "Người YC (TESTREQ)" and item["state_label"] == "Chờ nhận"
    assert item["issued_by_label"] and item["batch_id"] == out["batch_id"] and item["department"] == "Phòng Test"
    assert _list(db, org.admin, state=int(mcp_keys.KeyState.ACTIVE))["total"] == 0
    assert _list(db, org.admin, batch_id="khong-co")["total"] == 0
    with pytest.raises(HTTPException):
        _list(db, org.mate)                                                            # không có quyền đọc


def test_thu_hoi_theo_khoa_nguoi_luot_va_ngoai_pham_vi(db, seed, org):
    out = _issue(db, org.admin, department_id=seed.dept_id, days=30)
    batch = out["batch_id"]
    outsider_key, _raw = mcp_keys.create(db, org.outsider.id, name="phòng khác")
    revoke = lambda **b: _json(controller.key_admin_revoke(controller.KeyRevokeIn(**b), user=org.admin, db=db))  # noqa: E731

    with pytest.raises(HTTPException) as e:
        controller.key_admin_revoke(controller.KeyRevokeIn(key_ids=[out["issued"][0]["key_id"], outsider_key.id]),
                                    user=org.admin, db=db)
    assert e.value.status_code == 403
    db.refresh(outsider_key)
    assert outsider_key.revoked_at is None and db.get(AgentMcpKey, out["issued"][0]["key_id"]).revoked_at is None

    first = out["issued"][0]["key_id"]
    assert revoke(key_ids=[first])["revoked"] == 1
    row = db.get(AgentMcpKey, first)
    assert mcp_keys.state_of(row) == mcp_keys.KeyState.REVOKED and row.raw_sealed == ""          # dòng còn, niêm phong bỏ
    with pytest.raises(HTTPException):
        controller.claim_my_mcp_key(first, user=SimpleNamespace(id=row.user_id), db=db)          # thu hồi rồi thì không nhận
    assert revoke(batch_id=batch)["revoked"] == len(out["issued"]) - 1
    assert revoke(user_id=org.mate.id)["revoked"] == 0                                          # khóa của mate đã thu hồi theo lượt
    assert _list(db, org.admin, state=int(mcp_keys.KeyState.REVOKED))["total"] == len(out["issued"])


# ── Cổng B ────────────────────────────────────────────────────────────────────

def test_cong_b_va_ban_goi_tu_xa(db, org, monkeypatch):
    from app.modules.agent_gateway import controller as gw
    from app.modules.agent_hub import erp

    data = _json(gw.key_admin_people(gw.KeyAdminPeopleIn(action="create"), user=org.mate, db=db))
    assert data == {"allowed": False, "people": []}
    data = _json(gw.key_admin_people(gw.KeyAdminPeopleIn(action="read"), user=org.admin, db=db))
    assert data["allowed"] and org.mate.id in {p["user_id"] for p in data["people"]}
    assert org.outsider.id not in {p["user_id"] for p in data["people"]}

    remote = erp._Remote()
    monkeypatch.setattr(remote, "_call", lambda *a, **k: {"allowed": False, "people": []})
    assert remote.key_admin_people(db, org.admin, "read") is None
    monkeypatch.setattr(remote, "_call", lambda *a, **k: {"allowed": True, "people": [{"user_id": 3}]})
    assert remote.key_admin_people(db, org.admin, "read") == [{"user_id": 3}]


# ── ai-CR-215: phát theo hồ sơ nhân sự (employee_ids) ─────────────────────────

def test_phat_theo_ho_so_nhan_su_bo_qua_nguoi_chua_co_tai_khoan(db, seed, org):
    no_user = Employee(code="CHUATK", full_name="Chưa có TK", company_id=seed.company_id, department_id=seed.dept_id,
                       is_active=True)
    db.add(no_user)
    db.commit()
    locked = _person(db, "KHOATK", seed.company_id, seed.dept_id)
    locked.is_active = False
    db.commit()
    out = _issue(db, org.admin, employee_ids=[org.mate.employee_id, no_user.id, locked.employee_id], days=30)
    assert [(i["user_id"], i["employee_id"]) for i in out["issued"]] == [(org.mate.id, org.mate.employee_id)]
    reasons = {s["employee_id"]: s["reason"] for s in out["skipped"]}
    assert reasons == {no_user.id: "chưa có tài khoản ERP", locked.employee_id: "tài khoản ERP đã bị khóa"}
    assert all(s["user_id"] == 0 for s in out["skipped"])
    #  Gộp chung user_ids + employee_ids trỏ cùng một người thì không phát hai khóa.
    out2 = _issue(db, org.admin, user_ids=[org.admin.id], employee_ids=[org.admin.employee_id], days=7)
    assert [i["user_id"] for i in out2["issued"]] == [org.admin.id]


def test_phat_theo_ho_so_ngoai_pham_vi_hoac_khong_co_that_bi_chan(db, org):
    for bad in ([org.outsider.employee_id], [org.mate.employee_id, 99999999]):
        with pytest.raises(HTTPException) as e:
            _issue(db, org.admin, employee_ids=bad, days=30)
        assert e.value.status_code == 403 and "ngoài phạm vi" in e.value.detail
    assert db.query(AgentMcpKey).count() == 0
    with pytest.raises(HTTPException) as e:
        _issue(db, org.mate, employee_ids=[org.admin.employee_id], days=30)          # không có quyền
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        _issue(db, org.admin, user_ids=list(range(1, 30)), employee_ids=list(range(1, 30)), days=30)
    assert e.value.status_code == 400                                                # tổng > 50 người


def test_cong_b_ho_so_nhan_su_va_ban_goi_tu_xa(db, org, monkeypatch):
    from app.modules.agent_gateway import controller as gw
    from app.modules.agent_hub import erp

    data = _json(gw.key_admin_employees(gw.KeyAdminEmployeesIn(action="create", employee_ids=[
        org.mate.employee_id, org.outsider.employee_id]), user=org.admin, db=db))
    assert data["allowed"] and [p["user_id"] for p in data["people"]] == [org.mate.id]
    assert data["outside"] == [org.outsider.employee_id] and data["no_account"] == []
    assert _json(gw.key_admin_employees(gw.KeyAdminEmployeesIn(action="create", employee_ids=[1]), user=org.mate,
                                        db=db))["allowed"] is False
    remote = erp._Remote()
    monkeypatch.setattr(remote, "_call", lambda *a, **k: {"allowed": False})
    assert remote.key_admin_employees(db, org.admin, "create", [1]) is None
    monkeypatch.setattr(remote, "_call", lambda *a, **k: {"allowed": True, "people": [{"user_id": 3}], "outside": [9]})
    assert remote.key_admin_employees(db, org.admin, "create", [1]) == {"people": [{"user_id": 3}], "no_account": [],
                                                                         "outside": [9]}
