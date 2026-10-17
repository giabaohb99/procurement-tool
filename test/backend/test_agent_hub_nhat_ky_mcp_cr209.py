"""ai-CR-209 — nhật ký lượt gọi cổng MCP + trần tần suất + dọn 180 ngày + đường đọc (K3 doc/erp/21 §4.3 + §5.4).

Canh:
  - MỌI lượt đều có dòng: initialize / thông báo / tools/list / tools/call; chụp nhân sự + phòng ban + pháp nhân lúc gọi;
    tên ứng dụng lấy từ initialize rồi gắn cho các lượt sau của cùng khóa;
  - trạng thái đúng: thành công / bị từ chối (khóa đọc gọi tool ghi, tool trả denied) / lỗi (tool lỗi, method lạ);
  - khóa sai / thu hồi / hết hạn: 401 + dòng `deny_reason`, có trần ghi; dội khóa sai theo IP → 429;
  - quá tần suất theo khóa / theo IP → 429 + lỗi JSON-RPC nói rõ trần + Retry-After, ghi «quá tần suất»;
  - dọn: quá hạn gom vào bảng đếm theo ngày rồi xóa, chạy lại không đếm trùng; tổng theo ngày / top cộng cả hai bảng;
  - đường đọc: người thường chỉ xem của mình (xem người khác → 403), người có quyền quản lý bot xem hết.
"""
import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.modules.agent_hub import controller, mcp_keys, mcp_log
from app.modules.agent_hub.model import AgentMcpCall, AgentMcpCallDaily
from app.modules.user.model import User

S = mcp_log.CallStatus


@pytest.fixture(autouse=True)
def _memory_counter(monkeypatch):
    """Đếm tần suất trong bộ nhớ (không đụng Redis thật), mỗi bài một sổ đếm sạch."""
    def no_redis():
        raise ConnectionError("không có Redis trong bài kiểm")

    monkeypatch.setattr(mcp_log, "_redis", no_redis)
    monkeypatch.setattr(mcp_log, "_mem", {})
    monkeypatch.setattr(mcp_log, "_clients", {})


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def _post(client, raw: str, msg, ip: str = "203.0.113.7"):
    return client.post("/api/mcp", content=json.dumps(msg), headers={
        "Authorization": f"Bearer {raw}", "Content-Type": "application/json", "CF-Connecting-IP": ip})


def _rpc(method: str, rid=1, **params):
    return {"jsonrpc": "2.0", "id": rid, "method": method, "params": params}


def _rows(db) -> list[AgentMcpCall]:
    db.expire_all()
    return db.query(AgentMcpCall).order_by(AgentMcpCall.id).all()


@pytest.fixture
def owner(db, seed):
    return db.get(User, seed.u_req_id)


# ── Ghi mọi lượt ──────────────────────────────────────────────────────────────

def test_moi_luot_mot_dong_chup_nguoi_goi_va_ten_ung_dung(db, seed, owner, client, monkeypatch):
    from app.modules.assistant import tools as tool_registry

    monkeypatch.setattr(tool_registry, "run_tool", lambda db_, u, name, args: {"total": 1, "items": ["x"]})
    _row, raw = mcp_keys.create(db, owner.id, name="Claude", scope=mcp_keys.SCOPE_READ)
    assert _post(client, raw, _rpc("initialize", clientInfo={"name": "Claude Desktop", "version": "1.2"})).status_code == 200
    assert _post(client, raw, {"jsonrpc": "2.0", "method": "notifications/initialized"}).status_code == 202
    assert _post(client, raw, _rpc("tools/list", 2)).status_code == 200
    assert _post(client, raw, _rpc("tools/call", 3, name="product_search", arguments={"q": "x"})).status_code == 200

    rows = _rows(db)
    assert [r.method for r in rows] == ["initialize", "notifications/initialized", "tools/list", "tools/call"]
    assert {r.client_name for r in rows} == {"Claude Desktop 1.2"}
    assert all(r.status == S.OK and r.key_id == _row.id and r.ip == "203.0.113.7" for r in rows)
    r = rows[-1]
    assert r.tool == "product_search" and r.user_id == owner.id and r.employee_id == owner.employee_id
    assert (r.department_id, r.company_id) == (seed.dept_id, seed.company_id) and r.skill_id == 0


def test_ten_ung_dung_nho_qua_khoi_dong_lai_tien_trinh(db, owner, client, monkeypatch):
    _row, raw = mcp_keys.create(db, owner.id, name="Cursor")
    _post(client, raw, _rpc("initialize", clientInfo={"name": "Cursor", "version": "0.50"}))
    monkeypatch.setattr(mcp_log, "_clients", {})          # như tiến trình mới: tra dòng initialize gần nhất
    _post(client, raw, _rpc("ping", 2))
    assert _rows(db)[-1].client_name == "Cursor 0.50"


def test_trang_thai_tu_choi_va_loi(db, owner, client, monkeypatch):
    from app.modules.assistant import tools as tool_registry

    def fake(db_, u, name, args):
        if name == "employee_lookup":
            return {"denied": True, "reason": "Bạn không có quyền xem nhân sự."}
        raise RuntimeError("hỏng")

    monkeypatch.setattr(tool_registry, "run_tool", fake)
    _row, raw = mcp_keys.create(db, owner.id, scope=mcp_keys.SCOPE_READ)
    _post(client, raw, _rpc("tools/call", 1, name="draft_leave_request", arguments={}))     # khóa đọc gọi tool ghi
    _post(client, raw, _rpc("tools/call", 2, name="employee_lookup", arguments={}))         # tool trả denied
    _post(client, raw, _rpc("tools/call", 3, name="product_search", arguments={}))          # tool ném lỗi
    _post(client, raw, _rpc("resources/list", 4))                                           # method lạ
    rows = _rows(db)
    assert [r.status for r in rows] == [S.DENIED, S.DENIED, S.ERROR, S.ERROR]
    assert "không mở cho khóa" in rows[0].deny_reason and "quyền xem nhân sự" in rows[1].deny_reason
    assert "hỏng" in rows[2].deny_reason and rows[3].method == "resources/list"


def test_lo_gom_nhieu_thong_diep_moi_thong_diep_mot_dong(db, owner, client):
    _row, raw = mcp_keys.create(db, owner.id)
    res = _post(client, raw, [_rpc("ping", 1), _rpc("tools/list", 2)])
    assert res.status_code == 200 and len(res.json()) == 2
    assert [r.method for r in _rows(db)] == ["ping", "tools/list"]


# ── Khóa sai ──────────────────────────────────────────────────────────────────

def test_khoa_sai_thu_hoi_het_han_deu_ghi_ly_do(db, owner, client):
    revoked, raw_rev = mcp_keys.create(db, owner.id, name="cũ")
    mcp_keys.revoke(db, revoked)
    expired, raw_exp = mcp_keys.create(db, owner.id, name="hết hạn")
    expired.expires_at = datetime.now() - timedelta(minutes=1)
    db.commit()
    for raw in ("dego_mcp_khong_co", raw_rev, raw_exp, "rac"):
        assert _post(client, raw, _rpc("initialize")).status_code == 401
    rows = _rows(db)
    assert [(r.key_id, r.deny_reason) for r in rows] == [
        (0, mcp_log.REASON_BAD_KEY), (revoked.id, mcp_log.REASON_REVOKED), (expired.id, mcp_log.REASON_EXPIRED),
        (0, mcp_log.REASON_BAD_KEY)]
    assert all(r.status == S.DENIED and r.method == "initialize" and r.user_id == 0 for r in rows)


def test_tai_khoan_bi_khoa(db, owner, client):
    row, raw = mcp_keys.create(db, owner.id)
    owner.is_active = False
    db.commit()
    assert _post(client, raw, _rpc("tools/list")).status_code == 401
    r = _rows(db)[-1]
    assert r.key_id == row.id and r.deny_reason == mcp_log.REASON_INACTIVE


def test_doi_khoa_sai_theo_ip_bi_chan_va_co_tran_ghi(db, client, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MCP_BAD_KEY_PER_IP", 3)
    monkeypatch.setattr(mcp_log, "LOG_CAP_PER_MIN", 4)
    codes = [_post(client, "dego_mcp_sai", _rpc("initialize"), ip="198.51.100.9").status_code for _ in range(8)]
    assert codes == [401, 401, 401, 429, 429, 429, 429, 429]
    rows = _rows(db)
    assert len(rows) == 4                                       # 8 lượt nhưng chỉ ghi 4 dòng đầu của phút
    assert rows[-1].deny_reason == mcp_log.REASON_RATE_BAD
    #  IP khác không bị vạ lây.
    assert _post(client, "dego_mcp_sai", _rpc("initialize"), ip="198.51.100.10").status_code == 401


# ── Trần tần suất ─────────────────────────────────────────────────────────────

def test_qua_tan_suat_theo_khoa(db, owner, client, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MCP_RATE_PER_KEY", 2)
    row, raw = mcp_keys.create(db, owner.id)
    assert [_post(client, raw, _rpc("ping", i)).status_code for i in range(2)] == [200, 200]
    res = _post(client, raw, _rpc("ping", 9))
    assert res.status_code == 429 and int(res.headers["Retry-After"]) >= 1
    body = res.json()
    assert body["id"] == 9 and body["error"]["code"] == -32000 and "tối đa 2 lượt / phút cho mỗi khóa" in body["error"]["message"]
    last = _rows(db)[-1]
    assert (last.key_id, last.user_id, last.status, last.deny_reason) == (row.id, owner.id, S.DENIED, mcp_log.REASON_RATE_KEY)
    #  Khóa khác của cùng người vẫn gọi được (trần tính theo khóa).
    _other, raw2 = mcp_keys.create(db, owner.id, name="khác")
    assert _post(client, raw2, _rpc("ping")).status_code == 200


def test_qua_tan_suat_theo_ip(db, owner, client, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MCP_RATE_PER_IP", 1)
    _row, raw = mcp_keys.create(db, owner.id)
    assert _post(client, raw, _rpc("ping")).status_code == 200
    res = _post(client, raw, _rpc("ping"))
    assert res.status_code == 429 and "địa chỉ IP" in res.json()["error"]["message"]
    assert _rows(db)[-1].deny_reason == mcp_log.REASON_RATE_IP
    assert _post(client, raw, _rpc("ping"), ip="203.0.113.99").status_code == 200


def test_bo_dem_qua_phut_moi_thi_mo_lai():
    assert not mcp_log.over_limit("key:1", 1, now=60 * 100)
    assert mcp_log.over_limit("key:1", 1, now=60 * 100 + 30)
    assert not mcp_log.over_limit("key:1", 1, now=60 * 101)


# ── Dọn 180 ngày ──────────────────────────────────────────────────────────────

def _call(db, created_at, *, user_id=1, tool="product_search", status=S.OK, ms=10):
    db.add(AgentMcpCall(key_id=5, user_id=user_id, method="tools/call", tool=tool, status=status, duration_ms=ms,
                        created_at=created_at))


def test_don_qua_han_gom_theo_ngay_roi_xoa_chay_lai_khong_dem_trung(db):
    now = datetime(2026, 10, 17, 3, 40)
    old_day = datetime(2026, 4, 1, 9, 0)                          # hơn 180 ngày
    for _ in range(3):
        _call(db, old_day)
    _call(db, old_day + timedelta(hours=2), status=S.DENIED, ms=0)
    _call(db, datetime(2026, 10, 10, 9, 0))                       # còn trong hạn
    db.commit()

    out = mcp_log.purge(db, now=now)
    assert out["deleted"] == 4
    assert db.query(AgentMcpCall).count() == 1
    daily = {(r.day, r.status): (r.calls, r.total_ms) for r in db.query(AgentMcpCallDaily).all()}
    assert daily == {(date(2026, 4, 1), S.OK): (3, 30), (date(2026, 4, 1), S.DENIED): (1, 0)}
    assert mcp_log.purge(db, now=now) == {"days": 0, "deleted": 0}
    assert db.query(AgentMcpCallDaily).filter_by(status=S.OK).one().calls == 3

    #  Thêm dòng cũ cùng ngày (vd nhật ký nạp lại) → cộng vào dòng đếm có sẵn.
    _call(db, old_day)
    db.commit()
    mcp_log.purge(db, now=now)
    assert db.query(AgentMcpCallDaily).filter_by(status=S.OK).one().calls == 4

    #  Tổng theo ngày / top cộng cả bảng đếm đã gom.
    days = mcp_log.daily_totals(db, days=3, today=date(2026, 4, 2))
    assert [d["day"] for d in days] == ["2026-03-31", "2026-04-01", "2026-04-02"]
    assert days[1] == {"day": "2026-04-01", "total": 5, "ok": 4, "denied": 1, "error": 0}
    assert mcp_log.top(db, by="tool", days=3, today=date(2026, 4, 2)) == [{"key": "product_search", "calls": 5}]


def test_lich_beat_co_vong_don():
    from app.core.celery_app import celery_app

    entry = celery_app.conf.beat_schedule["agent-mcp-log-purge"]
    assert entry["task"] == "agent.mcp_log_purge"


# ── Đường đọc ─────────────────────────────────────────────────────────────────

def _json(resp):
    return json.loads(resp.body)["data"]


def test_duong_doc_nguoi_thuong_chi_xem_cua_minh_quan_ly_xem_het(db, cap_quyen):
    today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    _call(db, today, user_id=101, tool="product_search")
    _call(db, today, user_id=101, tool="payable_lookup", status=S.DENIED)
    _call(db, today, user_id=202, tool="product_search")
    db.commit()
    me = SimpleNamespace(id=101)

    mine = _json(controller.list_mcp_calls(user=me, db=db, date_from=None, date_to=None, user_id=None, key_id=None,
                                           tool="", status=None, page=1, size=50))
    assert mine["total"] == 2 and {i["user_id"] for i in mine["items"]} == {101}
    assert {s["label"] for s in mine["statuses"]} == {"Thành công", "Bị từ chối", "Lỗi"}
    with pytest.raises(HTTPException) as e:
        controller.list_mcp_calls(user=me, db=db, date_from=None, date_to=None, user_id=202, key_id=None, tool="",
                                  status=None, page=1, size=50)
    assert e.value.status_code == 403
    denied = _json(controller.list_mcp_calls(user=me, db=db, date_from=today.date(), date_to=today.date(), user_id=None,
                                             key_id=None, tool="", status=int(S.DENIED), page=1, size=50))
    assert [i["tool"] for i in denied["items"]] == ["payable_lookup"] and denied["items"][0]["status_label"] == "Bị từ chối"

    daily = _json(controller.mcp_calls_daily(days=14, user_id=None, user=me, db=db))["items"]
    assert len(daily) == 14 and daily[-1]["total"] == 2

    #  Người có quyền quản lý bot AI thấy mọi người, lọc được theo người, top theo người có nhãn.
    admin_user = User(email="ql-ai@test.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(admin_user)
    db.commit()
    cap_quyen(admin_user.id, controller.MCP_LOG_VIEW_ALL_ENTITY, scope="all", read=True)
    admin = SimpleNamespace(id=admin_user.id)
    every = _json(controller.list_mcp_calls(user=admin, db=db, date_from=None, date_to=None, user_id=None, key_id=None,
                                            tool="", status=None, page=1, size=2))
    assert every["total"] == 3 and len(every["items"]) == 2 and every["has_more"] is True
    only = _json(controller.list_mcp_calls(user=admin, db=db, date_from=None, date_to=None, user_id=202, key_id=None,
                                           tool="", status=None, page=1, size=50))
    assert only["total"] == 1
    top_users = _json(controller.mcp_calls_top(by="user", days=14, limit=10, user_id=None, user=admin, db=db))["items"]
    assert [(i["key"], i["calls"]) for i in top_users] == [(101, 2), (202, 1)] and "label" in top_users[0]
    top_tools = _json(controller.mcp_calls_top(by="tool", days=14, limit=10, user_id=None, user=admin, db=db))["items"]
    assert top_tools[0] == {"key": "product_search", "calls": 2}


# ── Cổng B chở phòng ban / pháp nhân ──────────────────────────────────────────

def test_cong_b_cho_phong_ban_phap_nhan(db, seed, owner):
    from app.modules.agent_hub.erp import ErpUser, _Local

    snap = _Local.snapshot(db, owner)
    assert (snap.department_id, snap.company_id) == (seed.dept_id, seed.company_id)
    back = ErpUser.from_dict(snap.to_dict())
    assert (back.department_id, back.company_id) == (seed.dept_id, seed.company_id)
    assert mcp_log.who(db, back)["department_id"] == seed.dept_id
    assert ErpUser.from_dict({"id": 3}).department_id == 0          # ERP cũ chưa trả hai trường → 0, không vỡ
