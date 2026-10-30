"""bao-CR-696 — màn Kết nối AI / Ứng dụng OAuth / Nhật ký sử dụng: thêm cột + ô tìm (phần máy chủ).

Canh:
  - danh sách khóa / kết nối: dòng OAuth có tên ứng dụng + nơi quay về, khóa tay thì null; có mã nhân sự + email;
    `q` tìm theo họ tên / mã / email không dấu; phạm vi xem KHÔNG đổi (q trúng người ngoài phạm vi vẫn không ra);
  - ứng dụng OAuth: số người có kết nối sống + tối đa 5 tên; lọc q / có kết nối sống / đã dùng;
  - nhật ký: `q` tìm cả người lẫn tên công cụ, người thường vẫn chỉ ra dòng của mình; lượt GHI qua MCP ghi doc_code +
    doc_url (đường nội bộ), lượt đọc / bản nháp thì null.
"""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.modules.agent_hub import controller, mcp, mcp_keys, mcp_log
from app.modules.agent_hub.model import AgentMcpCall, AgentMcpKey, AgentOAuthClient
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.user.model import User


def _json(resp):
    return json.loads(resp.body)["data"]


def _person(db, code: str, name: str, company_id: int, dept_id: int) -> User:
    emp = Employee(code=code, full_name=name, company_id=company_id, department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=f"{code.lower()}@test.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def org(db, seed, cap_quyen):
    other = Department(code="DEPT-696", name="Phòng Khác", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    admin = _person(db, "QL696", "Quản Lý Kết Nối", seed.company_id, seed.dept_id)
    cap_quyen(admin.id, controller.KEY_ADMIN_ENTITY, scope="dept", read=True)
    mate = _person(db, "NV696", "Trần Thị Hồng", seed.company_id, seed.dept_id)
    outsider = _person(db, "NG696", "Trần Thị Hồng Ngoài", seed.company_id, other.id)
    app_row = AgentOAuthClient(client_id="cid-chatgpt", client_name="ChatGPT", redirect_uris=["https://chatgpt.com/cb"],
                               token_endpoint_auth_method="none", created_at=datetime.now())
    db.add(app_row)
    db.commit()
    return SimpleNamespace(admin=admin, mate=mate, outsider=outsider, app=app_row)


def _oauth_grant(db, user_id: int, app_id: int, *, live: bool = True) -> AgentMcpKey:
    row, _raw = mcp_keys.create(db, user_id, name="Qua ChatGPT")
    row.kind, row.oauth_client_id = mcp_keys.KIND_OAUTH, app_id
    row.expires_at = datetime.now() + (timedelta(days=30) if live else timedelta(days=-1))
    db.commit()
    return row


def _keys(db, admin, **kw):
    args = {"department_id": 0, "state": None, "user_id": None, "batch_id": "", "page": 1, "size": 50, **kw}
    return _json(controller.key_admin_list(user=admin, db=db, **args))


def test_ket_noi_co_ten_ung_dung_ma_email_va_tim_trong_pham_vi(db, org):
    manual, _raw = mcp_keys.create(db, org.mate.id, name="Khóa tay")
    grant = _oauth_grant(db, org.mate.id, org.app.id)
    _oauth_grant(db, org.outsider.id, org.app.id)                           # người phòng khác — ngoài phạm vi
    items = {i["id"]: i for i in _keys(db, org.admin)["items"]}
    assert set(items) == {manual.id, grant.id}
    o, k = items[grant.id], items[manual.id]
    assert (o["connection_type"], o["app_name"], o["app_redirect_uri"]) == ("oauth", "ChatGPT", "https://chatgpt.com/cb")
    assert (k["connection_type"], k["app_name"], k["app_redirect_uri"]) == ("key", None, None)
    assert (o["employee_code"], o["email"], o["owner_label"]) == ("NV696", "nv696@test.vn", "Trần Thị Hồng (NV696)")
    assert "last_used_at" in o and o["state_label"]

    assert _keys(db, org.admin, q="tran thi HONG")["total"] == 2              # không dấu, không phân biệt hoa thường
    assert _keys(db, org.admin, q="nv696")["total"] == 2
    assert _keys(db, org.admin, q="nv696@test")["total"] == 2
    assert _keys(db, org.admin, q="NG696")["total"] == 0                     # trúng người ngoài phạm vi vẫn không ra
    assert _keys(db, org.admin, q="không ai")["total"] == 0


def test_ung_dung_oauth_dem_nguoi_va_loc(db, org, cap_quyen):
    cap_quyen(org.admin.id, controller.MCP_LOG_VIEW_ALL_ENTITY, read=True)
    _oauth_grant(db, org.mate.id, org.app.id)
    _oauth_grant(db, org.mate.id, org.app.id)                               # một người nối hai lần
    _oauth_grant(db, org.outsider.id, org.app.id, live=False)               # đã hết hạn — không tính
    idle = AgentOAuthClient(client_id="cid-cursor", client_name="Cursor", redirect_uris=["http://127.0.0.1:9/cb"],
                            token_endpoint_auth_method="none", created_at=datetime.now())
    db.add(idle)
    org.app.last_used_at = datetime.now()
    db.commit()

    def apps(**kw):
        return {c["client_name"]: c for c in _json(controller.list_oauth_clients(user=org.admin, db=db, **kw))["items"]}

    every = apps()
    assert (every["ChatGPT"]["live_grants"], every["ChatGPT"]["live_users"]) == (2, 1)
    assert every["ChatGPT"]["live_user_names"] == ["Trần Thị Hồng (NV696)"] and "live_user_ids" not in every["ChatGPT"]
    assert (every["Cursor"]["live_users"], every["Cursor"]["live_user_names"]) == (0, [])
    assert set(apps(q="chat")) == {"ChatGPT"} and set(apps(q="cid-cur")) == {"Cursor"}
    assert set(apps(has_live=True)) == {"ChatGPT"} and set(apps(has_live=False)) == {"Cursor"}
    assert set(apps(used=True)) == {"ChatGPT"} and set(apps(used=False)) == {"Cursor"}


def _log(db, user: User, tool: str, **kw):
    db.add(mcp_log.new_row(key_id=1, person={"user_id": user.id, "employee_id": user.employee_id, "department_id": 0,
                                             "company_id": 0}, method="tools/call", tool=tool, **kw))
    db.commit()


def _calls(db, user, **kw):
    args = {"date_from": None, "date_to": None, "user_id": None, "key_id": None, "tool": "", "status": None, "page": 1,
            "size": 50, "kind": "", **kw}
    return _json(controller.list_mcp_calls(user=user, db=db, **args))


def test_nhat_ky_tim_nguoi_hoac_cong_cu_giu_pham_vi(db, org, cap_quyen):
    _log(db, org.mate, "product_search")
    _log(db, org.outsider, "confirm_draft", doc_code="YCMH-0001", doc_url="/procurement/requests/5")
    viewer = db.get(User, org.admin.id)
    cap_quyen(viewer.id, controller.MCP_LOG_VIEW_ALL_ENTITY, read=True)
    assert {i["tool"] for i in _calls(db, viewer, q="Hồng Ngoài")["items"]} == {"confirm_draft"}
    assert {i["tool"] for i in _calls(db, viewer, q="product")["items"]} == {"product_search"}
    assert _calls(db, viewer, q="nv696")["total"] == 1
    row = _calls(db, viewer, q="confirm")["items"][0]
    assert (row["doc_code"], row["doc_url"]) == ("YCMH-0001", "/procurement/requests/5")
    assert _calls(db, viewer, q="product")["items"][0]["doc_code"] is None
    #  Người thường chỉ xem của mình: q trúng người khác vẫn không ra dòng của họ.
    mine = _calls(db, SimpleNamespace(id=org.mate.id), q="confirm")
    assert mine["total"] == 0
    assert _calls(db, SimpleNamespace(id=org.mate.id), q="product")["total"] == 1


def test_doc_ref_lay_ma_va_duong_noi_bo():
    assert mcp.doc_ref({"ok": True, "code": "DMH-9", "url": "https://erp.x/po/9?tab=1"}) == \
        {"doc_code": "DMH-9", "doc_url": "/po/9?tab=1"}
    assert mcp.doc_ref({"ok": True, "code": "YCMH-1", "link": "/procurement/requests/1"}) == \
        {"doc_code": "YCMH-1", "doc_url": "/procurement/requests/1"}
    assert mcp.doc_ref({"ok": True, "code": "X", "url": "javascript:alert(1)"}) == {"doc_code": "X", "doc_url": ""}
    assert mcp.doc_ref({"items": []}) == {} and mcp.doc_ref(None) == {}


@pytest.fixture
def client(db, monkeypatch):
    def no_redis():
        raise ConnectionError("không có Redis trong bài kiểm")

    monkeypatch.setattr(mcp_log, "_redis", no_redis)
    monkeypatch.setattr(mcp_log, "_mem", {})
    monkeypatch.setattr(mcp_log, "_clients", {})
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def test_luot_ghi_qua_cong_ghi_ma_chung_tu_luot_doc_thi_khong(db, seed, client, monkeypatch, mcp_all_groups):
    owner = db.get(User, seed.u_req_id)
    _row, raw = mcp_keys.create(db, owner.id, name="ghi", scope=mcp_keys.SCOPE_WRITE)
    results = {"confirm_draft": {"ok": True, "code": "NP-0007", "id": 7, "link": "https://erp.x/leave/requests/7"},
               "product_search": {"total": 1, "items": [{"code": "SP-1", "url": "/products/1"}]},
               "draft_leave_request": {"draft": {"code": "chua-co"}, "code": "NP-NHAP"}}
    monkeypatch.setattr(mcp, "call_tool", lambda db_, u, scope, name, args: dict(results[name]))
    for i, name in enumerate(results, 1):
        msg = {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": {}}}
        resp = client.post("/api/mcp", content=json.dumps(msg), headers={
            "Authorization": f"Bearer {raw}", "Content-Type": "application/json", "CF-Connecting-IP": "203.0.113.9"})
        assert resp.status_code == 200, resp.text
    db.expire_all()
    rows = {r.tool: r for r in db.query(AgentMcpCall).all()}
    assert (rows["confirm_draft"].doc_code, rows["confirm_draft"].doc_url) == ("NP-0007", "/leave/requests/7")
    assert (rows["product_search"].doc_code, rows["product_search"].doc_url) == ("", "")
    assert rows["draft_leave_request"].doc_code == ""                       # bản nháp chưa ghi gì
