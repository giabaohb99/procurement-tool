"""ai-CR-213 — giảm tải erp_read (mặc định 1 trang × 50 dòng + ngân sách dòng / phút / khóa) và backend màn «AI của tôi» +
Tổng quan (K6 doc/erp/21 §6.2 G1 / G8).

Canh:
  - erp_read mặc định page_size 50; quá ngân sách dòng trong phút → denied + lời dặn lọc hẹp, nhật ký «Quá ngân sách dữ
    liệu», tool KHÔNG chạy; phút sau mở lại;
  - mcp-setup: Claude Desktop đi cầu `npx -y mcp-remote … --header Authorization:${DEGO_MCP_KEY}` (không url / headers
    thẳng), Claude Code là lệnh `claude mcp add --transport http … --header`, Cursor / Gemini CLI đúng khóa tệp; claude.ai /
    ChatGPT nói rõ chưa nhận khóa; ứng dụng lạ → 404;
  - last-call: chỉ chủ khóa; `connected` chỉ khi có lượt thành công;
  - ai-overview: gác agent_group.read; số 7 ngày + % so kỳ trước, từ chối / lỗi, người đã nối, khóa sắp hết hạn, số skill
    từ ERP (ERP lỗi → skills None, phần còn lại vẫn có).
"""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.agent_hub import controller, erp, mcp, mcp_keys, mcp_log
from app.modules.agent_hub.model import AgentMcpCall

S = mcp_log.CallStatus


def _json(resp):
    return json.loads(resp.body)["data"]


@pytest.fixture(autouse=True)
def _memory_counter(monkeypatch):
    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})


# ── Giảm tải erp_read ─────────────────────────────────────────────────────────

def test_erp_read_mac_dinh_mot_trang_50_dong():
    from app.modules.assistant.tools import erp_read_tool as er

    assert er.DEFAULT_PAGE_SIZE == 50 and er.MAX_PAGES == 5 and er.MAX_PAGE_SIZE == 100
    props = er.ERP_READ_SPEC.parameters["properties"]
    assert "mặc định 50" in props["page_size"]["description"] and "mặc định 1" in props["pages"]["description"]


def test_ngan_sach_dong_moi_phut_moi_khoa(db, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AGENT_MCP_ROW_BUDGET_PER_MIN", 3)
    calls: list = []
    monkeypatch.setattr(mcp, "call_tool", lambda db_, u, scope, name, args: calls.append(name) or
                        {"total": 9, "items": [{"id": 1}, {"id": 2}]})
    key = SimpleNamespace(id=77, scope=mcp_keys.SCOPE_READ)
    user = SimpleNamespace(id=5, is_active=True)
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "erp_read", "arguments": {"resource": "x"}}}
    traces = []
    for _ in range(3):
        t: dict = {}
        out = mcp.handle(db, user, key, msg, t)
        traces.append((t, out))
    assert calls == ["erp_read", "erp_read"]                              # 2 + 2 = 4 ≥ 3 → lượt ba không chạy
    t3, out3 = traces[2]
    assert t3["status"] == S.DENIED and t3["reason"] == mcp_log.REASON_ROW_BUDGET
    assert "lọc hẹp" in out3["result"]["content"][0]["text"] and out3["result"]["isError"] is True
    assert "status" not in traces[0][0]
    #  Tool khác không tính ngân sách; khóa khác có ngân sách riêng.
    other = dict(msg, params={"name": "product_search", "arguments": {}})
    mcp.handle(db, user, key, other, {})
    mcp.handle(db, user, SimpleNamespace(id=78, scope=0), msg, {})
    assert calls == ["erp_read", "erp_read", "product_search", "erp_read"]
    #  Sang phút sau thì mở lại.
    assert mcp_log.rows_spent(77, now=60 * 10**8) == 0


# ── mcp-setup ─────────────────────────────────────────────────────────────────

def _setup(client=""):
    return _json(controller.mcp_setup(client=client, user=SimpleNamespace(id=1)))


def test_doan_cau_hinh_dung_tung_ung_dung(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    url = "https://deverp.degoholding.vn/api/mcp"
    cat = _setup()
    assert cat["endpoint"] == url and len(cat["clients"]) == 6
    assert all(c["supported"] for c in cat["clients"])                       # ai-CR-218: claude.ai / ChatGPT qua OAuth
    assert {c["client"] for c in cat["clients"] if c["auth"] == "oauth"} == {"claude_ai", "chatgpt"}

    desk = _setup("claude_desktop")
    server = json.loads(desk["snippet"])["mcpServers"]["dego-erp"]
    assert server["command"] == "npx" and server["args"] == ["-y", "mcp-remote", url, "--header",
                                                             "Authorization:${DEGO_MCP_KEY}"]
    assert server["env"] == {"DEGO_MCP_KEY": f"Bearer {desk['placeholder']}"} and "url" not in server
    assert "headers" not in server and any("Node.js" in r for r in desk["requires"])
    assert "claude_desktop_config.json" in desk["files"]["windows"]

    code = _setup("claude_code")["snippet"]
    assert code.startswith("claude mcp add --transport http") and url in code and '--header "Authorization: Bearer ' in code
    cur = json.loads(_setup("cursor")["snippet"])["mcpServers"]["dego-erp"]
    assert cur == {"url": url, "headers": {"Authorization": "Bearer <KHÓA_CỦA_BẠN>"}}
    gem = json.loads(_setup("gemini_cli")["snippet"])["mcpServers"]["dego-erp"]
    assert gem["httpUrl"] == url and gem["headers"]["Authorization"].startswith("Bearer ")
    web = _setup("claude_ai")
    assert web["supported"] and web["auth"] == "oauth" and web["snippet"] == url and "Cho phép" in " ".join(web["steps"])
    assert _setup("chatgpt")["format"] == "url" and "OAuth" in " ".join(_setup("chatgpt")["steps"])
    assert "«" not in _setup("chatgpt")["note"] and "Connectors" in desk["note"]
    with pytest.raises(HTTPException) as e:
        _setup("notepad")
    assert e.value.status_code == 404


# ── last-call ─────────────────────────────────────────────────────────────────

def test_luot_goi_gan_nhat_chi_chu_khoa(db):
    row, _raw = mcp_keys.create(db, 41, name="Claude")
    me = SimpleNamespace(id=41)
    first = _json(controller.my_mcp_key_last_call(row.id, user=me, db=db))
    assert first == {"key_id": row.id, "connected": False, "last_call": None, "last_ok_call": None}
    db.add(AgentMcpCall(key_id=row.id, user_id=41, method="tools/list", status=S.DENIED, deny_reason="x",
                        created_at=datetime.now() - timedelta(minutes=5)))
    db.commit()
    assert _json(controller.my_mcp_key_last_call(row.id, user=me, db=db))["connected"] is False
    db.add(AgentMcpCall(key_id=row.id, user_id=41, method="initialize", client_name="Claude Desktop 1.2", status=S.OK,
                        created_at=datetime.now()))
    db.commit()
    out = _json(controller.my_mcp_key_last_call(row.id, user=me, db=db))
    assert out["connected"] and out["last_call"]["client_name"] == "Claude Desktop 1.2"
    assert out["last_call"]["status_label"] == "Thành công"
    with pytest.raises(HTTPException) as e:
        controller.my_mcp_key_last_call(row.id, user=SimpleNamespace(id=42), db=db)
    assert e.value.status_code == 404


# ── ai-overview ───────────────────────────────────────────────────────────────

def test_tong_quan_so_lieu_va_quyen(db, cap_quyen, monkeypatch):
    from app.modules.user.model import User

    now = datetime.now()
    active, _ = mcp_keys.create(db, 101, name="đang dùng")
    soon, _ = mcp_keys.create(db, 102, name="sắp hết", days=3)
    for i in range(4):
        db.add(AgentMcpCall(key_id=active.id, user_id=101, method="tools/call", tool="erp_read", status=S.OK,
                            created_at=now - timedelta(days=1, minutes=i)))
    db.add(AgentMcpCall(key_id=active.id, user_id=101, method="tools/call", tool="erp_read", status=S.DENIED,
                        created_at=now - timedelta(days=2)))
    db.add(AgentMcpCall(key_id=0, user_id=0, method="initialize", status=S.DENIED, created_at=now - timedelta(days=2)))
    db.add(AgentMcpCall(key_id=active.id, user_id=101, method="tools/call", tool="read_skill", skill_id=9, status=S.ERROR,
                        created_at=now - timedelta(days=3)))
    for i in range(2):
        db.add(AgentMcpCall(key_id=active.id, user_id=101, method="tools/list", status=S.OK,
                            created_at=now - timedelta(days=10, minutes=i)))
    db.commit()

    viewer = User(email="ql-tq@test.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(viewer)
    db.commit()
    with pytest.raises(HTTPException):
        controller.ai_overview(user=SimpleNamespace(id=viewer.id), db=db)
    cap_quyen(viewer.id, controller.MCP_LOG_VIEW_ALL_ENTITY, scope="all", read=True)
    monkeypatch.setattr(erp, "skill_stats", lambda db_: {"skill_sets": 2, "skills": 7})
    out = _json(controller.ai_overview(user=SimpleNamespace(id=viewer.id), db=db))
    assert (out["calls_7d"], out["calls_prev_7d"], out["calls_change_pct"]) == (7, 2, 250.0)
    assert (out["denied_7d"], out["error_7d"], out["connected_users"]) == (2, 1, 1)
    assert out["skills"] == {"skill_sets": 2, "skills": 7} and len(out["daily"]) == 14
    assert out["top_tools"][0] == {"key": "erp_read", "calls": 5} and out["top_users"][0]["key"] == 101
    assert out["top_skills"] == [{"skill_id": 9, "calls": 1}]
    assert [k["key_id"] for k in out["expiring_keys"]] == [soon.id]
    assert {s["label"]: s["count"] for s in out["keys_by_state"]}["Đang dùng"] == 2

    monkeypatch.setattr(erp, "skill_stats", lambda db_: (_ for _ in ()).throw(RuntimeError("ERP không trả lời")))
    assert _json(controller.ai_overview(user=SimpleNamespace(id=viewer.id), db=db))["skills"] is None


def test_dem_skill_dang_dung_phia_erp(db):
    from app.modules.agent_gateway.key_admin import skill_stats
    from app.modules.ai_skill.constants import SkillSetStatus, SkillStatus
    from app.modules.ai_skill.model import AiSkill, AiSkillSet

    live = AiSkillSet(code="B1", name="Bộ dùng", status=int(SkillSetStatus.ACTIVE))
    draft = AiSkillSet(code="B2", name="Bộ nháp", status=int(SkillSetStatus.DRAFT))
    db.add_all([live, draft])
    db.flush()
    db.add_all([AiSkill(skill_set_id=live.id, slug="a", status=int(SkillStatus.ACTIVE)),
                AiSkill(skill_set_id=live.id, slug="b", status=int(SkillStatus.DRAFT)),
                AiSkill(skill_set_id=live.id, slug="c", status=int(SkillStatus.ACTIVE), is_deleted=True),
                AiSkill(skill_set_id=draft.id, slug="d", status=int(SkillStatus.ACTIVE))])
    db.commit()
    assert skill_stats(db) == {"skill_sets": 1, "skills": 1}


# ── ai-CR-219: lọc lượt gọi công cụ + nhãn khóa sai + đếm riêng tools/call ──────

def test_nhat_ky_loc_luot_goi_cong_cu_va_nhan_khoa_sai(db, monkeypatch):
    from app.modules.agent_hub import erp

    now = datetime.now()
    for method in ("initialize", "tools/list", "notifications/initialized", "tools/call", "tools/call"):
        db.add(AgentMcpCall(key_id=9, user_id=55, method=method, tool="erp_read" if method == "tools/call" else "",
                            status=S.OK, created_at=now - timedelta(hours=1)))
    db.add(AgentMcpCall(key_id=0, user_id=0, method="initialize", status=S.DENIED, deny_reason="Khóa sai",
                        created_at=now - timedelta(hours=1)))
    db.commit()
    monkeypatch.setattr(controller, "_mcp_log_subject", lambda db_, user, uid: uid)
    monkeypatch.setattr(controller, "_user_labels", lambda db_, ids: {55: "Người 55"})
    args = dict(date_from=None, date_to=None, user_id=None, key_id=None, tool="", status=None, page=1, size=50)
    every = _json(controller.list_mcp_calls(**args, kind="", user=SimpleNamespace(id=1), db=db))
    assert every["total"] == 6 and {i["user_label"] for i in every["items"]} == {"Người 55", "(khóa sai)"}
    tools = _json(controller.list_mcp_calls(**args, kind="tools", user=SimpleNamespace(id=1), db=db))
    assert tools["total"] == 2 and {i["method"] for i in tools["items"]} == {"tools/call"}

    monkeypatch.setattr(erp, "skill_stats", lambda db_: {"skill_sets": 0, "skills": 0})
    from app.modules.agent_hub import ai_overview

    out = ai_overview.build(db, now=now)
    assert (out["calls_7d"], out["tool_calls_7d"], out["tool_calls_prev_7d"]) == (6, 2, 0)
