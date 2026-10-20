"""ai-CR-230 — đưa hoạt động AI vào hồ sơ cách làm việc (doc/erp/22 §5, đợt A0).

Canh:
  - nhật ký thao tác (`tab_audit_log.ai_channel`): người tự bấm = 0; trong lượt AI làm hộ = số kênh; ra khỏi lượt thì về 0;
  - chế độ tách: kênh đi theo header ký của cổng B, dòng nhật ký ở DB ERP mang đúng kênh; số kênh lạ bị bỏ qua;
  - sổ ý định đếm lượt gọi công cụ + lượt bị từ chối;
  - bộ gom: một dòng mỗi (người, kênh) mỗi ngày giờ VN — web / Telegram / Zalo từ sổ ý định, MCP từ nhật ký cổng (ứng dụng,
    từ chối, lỗi, nháp tạo / xác nhận, nhóm công cụ); dòng không có người bị bỏ;
  - ERP nhận: có rồi thay, chưa có thêm (gom lại không nhân đôi), điền mã nhân sự, dòng sai bị bỏ và đếm;
  - đẩy qua cổng B: thân chỉ có số đếm + mã; gửi kèm trường lạ (vd. câu hỏi) → 422.
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import audit
from app.core.config import settings
from app.core.database import get_db
from app.core.logging_codes import AI_CHANNEL_MCP, AI_CHANNEL_TELEGRAM, AI_CHANNEL_WEB, AI_CHANNEL_ZALO
from app.core.request_context import ai_channel_scope, current_ai_channel
from app.modules.agent_hub import ai_usage, erp, intent_ledger
from app.modules.agent_hub.mcp_log import CallStatus
from app.modules.agent_hub.model import AgentIntent, AgentMcpCall
from app.modules.ai_usage.model import AiUsageDaily
from app.modules.ai_usage.service import upsert_rows
from app.modules.audit.model import AuditLog
from app.modules.user.model import User

DAY = date(2026, 10, 19)
#  Giờ UTC trong ngày 19/10 giờ VN: 18/10 17:00 UTC = 19/10 00:00 VN; 19/10 16:59 UTC = 19/10 23:59 VN.
IN_DAY = datetime(2026, 10, 19, 3, 0)
VN_MIDNIGHT = datetime(2026, 10, 18, 17, 0)
NEXT_DAY = datetime(2026, 10, 19, 17, 0)


def _last_audit(db) -> AuditLog:
    db.expire_all()
    return db.query(AuditLog).order_by(AuditLog.id.desc()).first()


# ── Nhật ký thao tác mang kênh AI ─────────────────────────────────────────────

def test_nguoi_tu_bam_la_0_trong_luot_ai_la_so_kenh(db, seed):
    audit.record(db, seed.u_req_id, "purchase_request", 1, "update", "tự sửa")
    db.commit()
    assert _last_audit(db).ai_channel == 0
    with ai_channel_scope(AI_CHANNEL_MCP):
        assert current_ai_channel() == AI_CHANNEL_MCP
        audit.record(db, seed.u_req_id, "purchase_request", 1, "update", "nhờ AI")
        db.commit()
    assert _last_audit(db).ai_channel == AI_CHANNEL_MCP
    assert current_ai_channel() == 0
    audit.record(db, seed.u_req_id, "purchase_request", 1, "update", "tự sửa lại")
    db.commit()
    assert _last_audit(db).ai_channel == 0


@pytest.fixture
def gateway(db, monkeypatch):
    from app.modules.agent_gateway.controller import router as gw_router

    gw = FastAPI()
    gw.include_router(gw_router)
    gw.dependency_overrides[get_db] = lambda: db
    client = TestClient(gw)
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "khoa-ky-thu-nghiem")
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(erp, "_remote", None)
    sent: list[dict] = []

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, **kw):
        path = url.replace("http://erp.test", "")
        sent.append({"method": method, "path": path, "headers": dict(headers or {}), "data": data})
        return client.request(method, path, params=params, content=data, headers=headers)

    monkeypatch.setattr(erp.requests, "request", fake_request)
    yield SimpleClient(client, sent)
    monkeypatch.setattr(erp, "_remote", None)


class SimpleClient:
    def __init__(self, client, sent):
        self.client, self.sent = client, sent


def test_che_do_tach_kenh_di_theo_header_cong_b(db, seed, gateway):
    with ai_channel_scope(AI_CHANNEL_TELEGRAM):
        assert erp.audit(db, seed.u_req_id, "assistant", 0, "tool:x", "qua bot")
    assert gateway.sent[-1]["headers"].get("x-agent-ai-channel") == str(AI_CHANNEL_TELEGRAM)
    assert _last_audit(db).ai_channel == AI_CHANNEL_TELEGRAM
    #  Ngoài lượt AI: không gửi header, dòng = 0.
    assert erp.audit(db, seed.u_req_id, "assistant", 0, "tool:y", "không kênh")
    assert "x-agent-ai-channel" not in gateway.sent[-1]["headers"]
    assert _last_audit(db).ai_channel == 0


def test_cong_b_bo_qua_so_kenh_la():
    from starlette.requests import Request

    from app.modules.agent_gateway.controller import _take_ai_channel

    for raw in (b"99", b"-1", b"abc", b""):
        req = Request({"type": "http", "headers": [(b"x-agent-ai-channel", raw)]})
        _take_ai_channel(req)
        assert current_ai_channel() == 0


# ── Sổ ý định đếm lượt ────────────────────────────────────────────────────────

def test_so_y_dinh_dem_luot_goi_va_tu_choi(db, seed):
    calls = [{"name": "product_search", "result": {"items": []}},
             {"name": "product_search", "result": {"denied": True, "error": "không có quyền"}},
             {"name": "draft_purchase_request", "result": {"draft": {}}}]
    row = intent_ledger.record(db, user_id=seed.u_req_id, channel=intent_ledger.Channel.WEB, scope_key="web",
                               intent=intent_ledger.Intent.ASK, tool_calls=calls, question="tìm giá bút bi",
                               answer="ok")
    assert row is not None and row.tool_calls_n == 3 and row.denied_n == 1
    assert intent_ledger.denied_count(None) == 0


# ── Bộ gom theo người × ngày × kênh ──────────────────────────────────────────

def _intent(db, user_id, channel, tools, *, at=IN_DAY, n=None, denied=0, outcome=1):
    db.add(AgentIntent(user_id=user_id, channel=channel, tools=tools, tool_calls_n=len(tools) if n is None else n,
                       denied_n=denied, outcome=outcome, created_at=at))


def _mcp(db, user_id, tool, status=CallStatus.OK, *, client="Claude Desktop", at=IN_DAY, method="tools/call"):
    db.add(AgentMcpCall(user_id=user_id, key_id=1, client_name=client, method=method, tool=tool, status=int(status),
                        created_at=at))


def test_gom_mot_ngay_theo_nguoi_va_kenh(db, seed):
    u = seed.u_req_id
    _intent(db, u, 1, ["product_search", "draft_purchase_request", "commit_draft"], denied=1)
    _intent(db, u, 1, [], outcome=int(intent_ledger.Outcome.ERROR), at=VN_MIDNIGHT)
    _intent(db, u, 2, ["my_work_tasks"])
    _intent(db, u, 3, ["my_work_tasks"])
    _intent(db, u, 1, ["product_search"], at=NEXT_DAY)                 # đã sang ngày 20/10 giờ VN
    _intent(db, 0, 1, ["product_search"])                              # không có người → bỏ
    _mcp(db, u, "product_search")
    _mcp(db, u, "draft_leave_request", client="ChatGPT")
    _mcp(db, u, "confirm_draft", client="ChatGPT")
    _mcp(db, u, "confirm_draft", CallStatus.ERROR, client="ChatGPT")
    _mcp(db, u, "payable_lookup", CallStatus.DENIED)
    _mcp(db, u, "", method="tools/list")                                # không phải lượt gọi công cụ
    db.commit()

    rows = {r["channel"]: r for r in ai_usage.collect(db, DAY)}
    assert set(rows) == {AI_CHANNEL_WEB, AI_CHANNEL_TELEGRAM, AI_CHANNEL_ZALO, AI_CHANNEL_MCP}
    web = rows[AI_CHANNEL_WEB]
    assert (web["turns"], web["tool_calls"], web["denied"], web["errors"]) == (2, 3, 1, 1)
    assert (web["drafts_created"], web["drafts_confirmed"]) == (1, 1)
    assert web["clients"] == {} and sum(web["tool_groups"].values()) == 3
    assert rows[AI_CHANNEL_TELEGRAM]["turns"] == 1 and rows[AI_CHANNEL_ZALO]["turns"] == 1
    m = rows[AI_CHANNEL_MCP]
    assert (m["turns"], m["tool_calls"], m["denied"], m["errors"]) == (5, 5, 1, 1)
    assert (m["drafts_created"], m["drafts_confirmed"]) == (1, 1)
    assert m["clients"] == {"Claude Desktop": 2, "ChatGPT": 3}
    #  Chỉ số đếm + mã: không trường nào mang chữ người dùng gõ.
    assert set(m) == {"day", "user_id", "channel", "turns", "tool_calls", "denied", "errors", "drafts_created",
                      "drafts_confirmed", "clients", "tool_groups"}
    assert ai_usage.collect(db, DAY + timedelta(days=1))[0]["turns"] == 1


# ── ERP nhận ──────────────────────────────────────────────────────────────────

def _row(user_id, channel=AI_CHANNEL_WEB, turns=3, **kw):
    return {"day": DAY.isoformat(), "user_id": user_id, "channel": channel, "turns": turns, "tool_calls": 4,
            "clients": {}, "tool_groups": {"mua_hang": 4}, **kw}


def test_erp_nhan_co_roi_thay_dien_ma_nhan_su_bo_dong_sai(db, seed):
    u = db.get(User, seed.u_req_id)
    out = upsert_rows(db, [_row(u.id), _row(u.id, AI_CHANNEL_MCP, clients={"Claude": 2}),
                           _row(u.id, channel=0), _row(u.id, channel=99), _row(0), {"day": "sai"}])
    assert out == {"written": 2, "skipped": 4}
    out = upsert_rows(db, [_row(u.id, turns=7)])                         # gom lại cùng ngày → thay, không cộng dồn
    assert out["written"] == 1
    rows = db.query(AiUsageDaily).filter_by(user_id=u.id).order_by(AiUsageDaily.channel).all()
    assert [(r.channel, r.turns) for r in rows] == [(AI_CHANNEL_WEB, 7), (AI_CHANNEL_MCP, 3)]
    assert rows[0].employee_id == int(u.employee_id or 0) and rows[1].clients == {"Claude": 2}


def test_day_che_do_nhung_ghi_thang(db, seed):
    _intent(db, seed.u_req_id, 1, ["product_search"])
    db.commit()
    out = ai_usage.push_days(db, 2, today=DAY + timedelta(days=1))
    assert out["rows_sent"] == 1 and out["rows_written"] == 1
    assert db.query(AiUsageDaily).filter_by(user_id=seed.u_req_id, day=DAY).count() == 1


def test_day_qua_cong_b_chi_so_dem(db, seed, gateway):
    _mcp(db, seed.u_req_id, "product_search")
    db.commit()
    out = ai_usage.push_days(db, 1, today=DAY + timedelta(days=1))
    assert out == {"days": 1, "rows_sent": 1, "rows_written": 1}
    assert gateway.sent[-1]["path"] == "/api/agent-gw/ai-usage"
    assert db.query(AiUsageDaily).filter_by(user_id=seed.u_req_id, channel=AI_CHANNEL_MCP).one().turns == 1


def test_cong_b_tu_choi_truong_la(seed, gateway):
    from app.core import agent_signature
    import json

    body = json.dumps({"rows": [{**_row(seed.u_req_id), "question": "lương của sếp bao nhiêu"}]}).encode()
    headers = agent_signature.sign_headers("POST", "/api/agent-gw/ai-usage", body, 0)
    headers["content-type"] = "application/json"
    resp = gateway.client.post("/api/agent-gw/ai-usage", content=body, headers=headers)
    assert resp.status_code == 422
