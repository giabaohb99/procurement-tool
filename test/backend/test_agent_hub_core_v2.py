"""ai-CR-198 — lõi hội thoại mới (doc/agent-hub/20) bước B1: vòng tác tử + ngữ cảnh đủ + công cụ nháp.

Chạy bằng provider giả: ghi lại system / lịch sử / công cụ model nhận, trả lời theo kịch bản, gọi công cụ qua `execute`.
"""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.modules.agent_hub import core_v2, service
from app.modules.agent_hub.constants import ACT_ANSWER, ACT_ASKED, ACT_DRAFT_WAIT, DIR_IN, DIR_OUT, RUN_ERROR, RUN_OK
from app.modules.agent_hub.model import AgentMessage, AgentRun
from app.modules.assistant.provider.base import ChatResult

CHAT = "5551"


class FakeProvider:
    """Ghi lại những gì model nhận; `script` = hàm (msgs, tools, execute) -> ChatResult."""

    name = "agent_gemini"
    supports_tools = True

    def __init__(self, script):
        self.script = script
        self.seen = {}

    def run_tools(self, msgs, *, tools, execute, system=None, **kw):
        self.seen = {"system": system or "", "msgs": msgs, "tools": [t.name for t in tools], "kw": kw}
        return self.script(msgs, tools, execute)


def _result(text, tool_calls=None):
    return ChatResult(text=text, provider="openai_compat", model="claude-sonnet-5-5", input_tokens=120, output_tokens=30,
                      tool_calls=tool_calls or [])


@pytest.fixture
def chat(db, monkeypatch):
    """Chat đã liên kết, khóa sẵn, mọi đường ra ngoài (Telegram, ERP) đều giả."""
    monkeypatch.setattr(settings, "AGENT_CORE_V2_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_CORE_V2_CHATS", "")
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    user = SimpleNamespace(id=275, is_active=True, email="duoc@dego.com", name="Trần Minh Được")
    monkeypatch.setattr(service, "_assistant_user", lambda db_, chat_id="": user)
    monkeypatch.setattr(core_v2.user_keys, "active_key", lambda: "khoa-gia")
    monkeypatch.setattr(core_v2.erp, "describe", lambda db_, u: ("Trần Minh Được", "Nhân viên IT"))
    monkeypatch.setattr(core_v2.erp, "tool_defs", lambda db_, u=None: [])
    monkeypatch.setattr(core_v2.erp, "caller_context", lambda db_, u: None)
    monkeypatch.setattr(core_v2.erp, "glossary_block", lambda db_, texts: None)
    monkeypatch.setattr(core_v2.erp, "run_tool", lambda db_, u, name, args: {"ok": True, "tool": name})
    sent: list[str] = []
    monkeypatch.setattr(core_v2.telegram, "send", lambda text, buttons=None, chat_id="": sent.append(text) or 1)
    monkeypatch.setattr(core_v2.telegram, "send_chat_action", lambda *a, **k: None)
    return SimpleNamespace(user=user, sent=sent)


def _incoming(db, text, minutes_ago=0):
    row = service.log_message(db, DIR_IN, CHAT, 0, text, action="")
    row.created_at = datetime.now() - timedelta(minutes=minutes_ago)
    db.commit()
    return row


def _install(monkeypatch, script):
    prov = FakeProvider(script)
    monkeypatch.setattr(core_v2.manager, "get_provider", lambda: prov)
    return prov


def test_enabled_for_theo_co_va_danh_sach_chat(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_CORE_V2_ENABLED", False)
    assert not core_v2.enabled_for("1")
    monkeypatch.setattr(settings, "AGENT_CORE_V2_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_CORE_V2_CHATS", "")
    assert core_v2.enabled_for("1")
    monkeypatch.setattr(settings, "AGENT_CORE_V2_CHATS", " 12345, 5551 ")
    assert core_v2.enabled_for("5551") and not core_v2.enabled_for("999")


def test_model_nhin_thay_ngay_nguoi_va_dang_do_lich_su_du(db, chat, monkeypatch):
    #  Lịch sử cũ: 2 lượt hỏi đáp trong 24 giờ, 1 lượt quá cũ phải bị bỏ.
    old = service.log_message(db, DIR_IN, CHAT, 0, "câu hỏi hôm kia", action=ACT_ASKED)
    old.created_at = datetime.now() - timedelta(days=2)
    service.log_message(db, DIR_IN, CHAT, 0, "nháp hồi nãy đâu", action=ACT_ASKED)
    service.log_message(db, DIR_OUT, CHAT, 0, "Em còn giữ, anh muốn đổi gì?", action=ACT_ANSWER)
    db.commit()
    row = _incoming(db, "tạo cho anh task nghiên cứu luồng agent")
    prov = _install(monkeypatch, lambda msgs, tools, execute: _result("Task này thuộc dự án nào, giao ai, hạn khi nào ạ?"))

    core_v2.handle(db, CHAT, row, "tạo cho anh task nghiên cứu luồng agent")

    sysm = prov.seen["system"]
    assert f"Năm hiện tại là {datetime.now().year}" in sysm                 # hôm 14/10 model ghi hạn năm 2025 vì thiếu ngày
    assert "Trần Minh Được" in sysm and "KHÔNG gọi «đại ca»" in sysm       # biết đang nói với ai
    assert "ĐANG DỞ" in sysm and "(không có)" in sysm
    assert "KHÔNG dùng emoji" in sysm
    #  Lịch sử: 2 lượt gần + câu hiện tại; câu hôm kia bị bỏ.
    contents = [m.content for m in prov.seen["msgs"]]
    assert contents == ["nháp hồi nãy đâu", "Em còn giữ, anh muốn đổi gì?", "tạo cho anh task nghiên cứu luồng agent"]
    assert set(prov.seen["tools"]) >= {"update_draft", "commit_draft", "drop_draft"}
    #  Tin vào đóng dấu «hỏi» (không thành vé sửa mã), trả lời ghi «tra_loi», sổ chạy đóng OK và đánh dấu lõi v2.
    assert row.action == ACT_ASKED
    answer = db.query(AgentMessage).filter(AgentMessage.action == ACT_ANSWER).order_by(AgentMessage.id.desc()).first()
    assert answer is not None and "dự án nào" in answer.body
    run = db.query(AgentRun).order_by(AgentRun.id.desc()).first()
    assert run.status == RUN_OK and run.artifact["core"] == "v2" and run.input_tokens == 120
    assert chat.sent and "dự án nào" in chat.sent[-1]


def test_nhap_dang_cho_xuat_hien_trong_dang_do_va_commit_qua_duong_cu(db, chat, monkeypatch):
    pending = service.log_message(db, DIR_OUT, CHAT, 0, json.dumps({
        "tool": "draft_work_task", "kind": "work_task", "user_id": 275,
        "draft": {"title": "Kiểm tra tài khoản ERP dev", "due_date": "2026-10-17"}}, ensure_ascii=False),
        action=ACT_DRAFT_WAIT)
    db.commit()
    row = _incoming(db, "tao task đó giúp anh đi")
    called = {}

    def fake_draft_by_text(db_, chat_id, row_, phrase):
        called["phrase"] = phrase
        row_.action = "lenh"                                   # đường cũ đổi dấu tin; lõi phải trả lại «hỏi»
        p = db_.get(AgentMessage, pending.id)
        p.action = "da_tao"
        p.body = json.dumps({**json.loads(p.body), "created": {"id": 9, "code": "WT-9"}}, ensure_ascii=False)
        return True
    monkeypatch.setattr(service, "_draft_by_text", fake_draft_by_text)

    def script(msgs, tools, execute):
        out = execute("commit_draft", {})
        assert out["ok"] and out["created"]["code"] == "WT-9"
        return _result("Dạ xong, em đã tạo việc rồi.", [{"name": "commit_draft", "result": out}])
    prov = _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "tao task đó giúp anh đi")

    assert "Nháp việc Dự án đang chờ" in prov.seen["system"] or "Nháp" in prov.seen["system"]
    assert "Kiểm tra tài khoản ERP dev" in prov.seen["system"]
    assert called["phrase"] == "tạo"
    assert row.action == ACT_ASKED


def test_update_draft_gui_lai_the_voi_o_da_doi(db, chat, monkeypatch):
    service.log_message(db, DIR_OUT, CHAT, 0, json.dumps({
        "tool": "draft_work_task", "kind": "work_task", "user_id": 275,
        "draft": {"title": "Việc A", "due_date": "2026-10-17", "assignee": "Được"}}, ensure_ascii=False),
        action=ACT_DRAFT_WAIT)
    db.commit()
    row = _incoming(db, "đổi hạn thứ năm 16/10")
    offered = {}
    monkeypatch.setattr(service, "_offer_draft", lambda db_, chat_id, user, call: offered.update(call))

    def script(msgs, tools, execute):
        out = execute("update_draft", {"changes": {"due_date": "2026-10-16"}})
        assert out["ok"] and out["draft"]["due_date"] == "2026-10-16" and out["draft"]["assignee"] == "Được"
        return _result("Em đổi hạn sang 16/10 rồi, anh xem thẻ bên dưới.", [{"name": "update_draft", "result": out}])
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "đổi hạn thứ năm 16/10")

    assert offered["name"] == "draft_work_task" and offered["draft"]["due_date"] == "2026-10-16"
    assert offered["draft"]["title"] == "Việc A"


def test_model_hong_thi_bao_ma_luot_khong_im_lang(db, chat, monkeypatch):
    row = _incoming(db, "hello")

    def script(msgs, tools, execute):
        raise TimeoutError("trạm quá tải")
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "hello")

    run = db.query(AgentRun).order_by(AgentRun.id.desc()).first()
    assert run.status == RUN_ERROR and "TimeoutError" in run.error
    assert chat.sent and f"mã lượt #{run.id}" in chat.sent[-1] and "TimeoutError" in chat.sent[-1]


def test_khong_khoa_thi_huong_dan_khong_goi_model(db, chat, monkeypatch):
    monkeypatch.setattr(core_v2.user_keys, "active_key", lambda: "")
    row = _incoming(db, "hello")
    prov = _install(monkeypatch, lambda *a: pytest.fail("không được gọi model khi chưa có khóa"))

    core_v2.handle(db, CHAT, row, "hello")

    assert not prov.seen and chat.sent and "khóa AI" in chat.sent[-1]


def test_tram_tra_500_hai_lan_thi_nhay_sang_khoa_ke(monkeypatch):
    """ai-CR-198 (14/10 15:36): khóa Gemini-trạm ở ưu tiên 1 trả 500 «upstream error» hai lần → bot báo lỗi dù đại ca còn
    Kimi / Claude / DeepSeek phía sau. Quá tải SAU khi đã thử lại thì phải nhảy khóa kế."""
    from app.modules.agent_hub import manager, user_keys
    from app.modules.agent_hub.ai_keys import KeyRef
    from app.modules.assistant.provider.base import ChatMessage, ProviderError

    monkeypatch.setattr(manager, "TRANSIENT_WAIT_SEC", 0)
    seen = []

    class Flaky:
        def ask(self, msgs, *, model=None, **kw):
            key = user_keys.active_key()
            seen.append((key[-4:], model))
            if key.endswith("1111"):
                raise ProviderError('openai_compat trả lỗi 500: {"error":{"message":"upstream error: do request failed"}}')
            return _result("chào anh")
    monkeypatch.setitem(manager._DELEGATES, "openai_compat", Flaky())
    chain = [KeyRef(provider="openai_compat", key="sk-tram-gemini-lite-1111", model="gemini-3.1-flash-lite", row_id=8,
                    hint="1111", base_url="https://modelapi.vn/v1"),
             KeyRef(provider="openai_compat", key="sk-tram-kimi-2222", model="kimi-k3", row_id=9, hint="2222",
                    base_url="https://modelapi.vn/v1")]
    with user_keys.use_chain(chain, 238):
        out = manager.get_provider().ask([ChatMessage(role="user", content="hello em")])
    assert out.text == "chào anh"
    assert [k for k, _ in seen] == ["1111", "1111", "2222"]        # thử lại một lần rồi nhảy khóa


def test_claude_the_he_5_qua_tram_khong_gui_temperature():
    """ai-CR-198 lượt #205: trạm trả 400 «claude-sonnet-5-5 does not support non-default temperature»."""
    from app.modules.assistant.provider.openai_compat import _no_temperature

    assert _no_temperature("claude-sonnet-5-5") and _no_temperature("claude-opus-5-5") and _no_temperature("gpt-5-mini")
    assert not _no_temperature("kimi-k3") and not _no_temperature("deepseek-v4.1-flash")


def test_hello_em_la_xa_giao_khong_nap_cong_cu_erp():
    """«hello em» lượt #205 vẫn nạp 76 công cụ."""
    from app.modules.assistant import tool_router

    for t in ("hello em", "hi em", "chào em", "alo em", "em ơi", "cảm ơn em nhé"):
        assert tool_router.is_smalltalk(t), t


def test_lich_su_cat_tin_dai_va_xa_giao_chi_6_luot(db):
    """Lượt #206: «hello em» nạp 39k token vì lịch sử chứa nguyên các bản tra giá dài."""
    for i in range(10):
        service.log_message(db, DIR_IN, CHAT, 0, f"hỏi {i}", action=ACT_ASKED)
        service.log_message(db, DIR_OUT, CHAT, 0, "báo cáo dài " + "x" * 5000, action=ACT_ANSWER)
    db.commit()
    row = _incoming(db, "hello em")
    full = core_v2.history(db, CHAT, row.id, row.created_at)
    assert all(len(t["content"]) <= core_v2.HISTORY_MSG_CHARS + 20 for t in full)
    assert sum(len(t["content"]) for t in full) <= core_v2.HISTORY_MAX_CHARS
    small = core_v2.history(db, CHAT, row.id, row.created_at, smalltalk=True)
    assert len(small) == 2 * core_v2.SMALLTALK_TURNS          # 6 lượt hỏi–đáp = 12 tin


def test_phan_luong_model_bang_luat():
    """ai-CR-199: chọn luồng bằng luật, không gọi model."""
    assert core_v2.lane_of("hello em") == core_v2.LANE_SMALLTALK
    assert core_v2.lane_of("giá vàng hôm nay") == core_v2.LANE_QUICK
    assert core_v2.lane_of("tạo cho anh task nghiên cứu luồng agent") == core_v2.LANE_NORMAL
    assert core_v2.lane_of("lập kế hoạch thử bot, hạn 15/10") == core_v2.LANE_HEAVY
    assert core_v2.lane_of("viết báo cáo tổng kết tuần") == core_v2.LANE_HEAVY
    #  14/10: nhóm công cụ «work» luôn kèm draft_work_plan — không được đẩy câu tạo task thường sang Claude.
    assert core_v2.lane_of("tạo cho anh task nghiên cứu luồng agent", {"draft_work_plan", "draft_work_task"}) == core_v2.LANE_NORMAL
    assert core_v2.lane_of("x " * 400) == core_v2.LANE_HEAVY
    assert core_v2.route_providers(core_v2.LANE_SMALLTALK)[0] == "deepseek"
    assert core_v2.route_providers(core_v2.LANE_NORMAL)[0] == "kimi"
    assert core_v2.route_providers(core_v2.LANE_HEAVY)[0] == "claude"


def test_prefer_tach_kimi_deepseek_claude_cung_mot_tram():
    """Ba gói cùng trạm (openai_compat) phải xếp được theo hãng của MODEL."""
    from app.modules.agent_hub import user_keys
    from app.modules.agent_hub.ai_keys import KeyRef

    tram = "https://modelapi.vn/v1"
    chain = [KeyRef(provider="openai_compat", key="k-deepseek-0001", model="deepseek-v4.1-flash", base_url=tram, row_id=1),
             KeyRef(provider="openai_compat", key="k-kimi-0002", model="kimi-k3", base_url=tram, row_id=2),
             KeyRef(provider="openai_compat", key="k-claude-0003", model="claude-sonnet-5-5", base_url=tram, row_id=3)]
    with user_keys.use_chain(chain, 238):
        for lane, first in ((core_v2.LANE_SMALLTALK, "deepseek-v4.1-flash"), (core_v2.LANE_NORMAL, "kimi-k3"),
                            (core_v2.LANE_HEAVY, "claude-sonnet-5-5")):
            with user_keys.prefer(core_v2.route_providers(lane)):
                assert user_keys.active_ref().model == first, lane
                assert len(user_keys.chain()) == 3                 # các khóa còn lại vẫn làm dự phòng


def test_tra_nhanh_di_duong_tra_mang_tren_model_nhanh(db, chat, monkeypatch):
    seen = {}
    monkeypatch.setattr(service, "run_research", lambda db_, chat_id, text, mode: seen.update(text=text))
    row = _incoming(db, "giá vàng hôm nay")
    _install(monkeypatch, lambda *a: pytest.fail("tra nhanh không qua vòng tác tử"))
    core_v2.handle(db, CHAT, row, "giá vàng hôm nay")
    assert seen["text"] == "giá vàng hôm nay" and row.action == ACT_ASKED
