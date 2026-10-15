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
    assert f"{datetime.now():%d/%m/%Y} (hôm nay)" in sysm                  # hôm 14/10 model ghi hạn năm 2025 vì thiếu ngày
    assert "LỊCH" in sysm and "(mai)" in sysm                              # và tính sai thứ sáu = 17/10
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
    monkeypatch.setattr(service, "_offer_draft", lambda db_, chat_id, user, call, **kw: offered.update(call, **kw))

    def script(msgs, tools, execute):
        out = execute("update_draft", {"changes": {"due_date": "2026-10-16"}})
        assert out["ok"] and out["draft"]["due_date"] == "2026-10-16" and out["draft"]["assignee"] == "Được"
        return _result("Em đổi hạn sang 16/10 rồi, anh xem thẻ bên dưới.", [{"name": "update_draft", "result": out}])
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "đổi hạn thứ năm 16/10")

    assert offered["name"] == "draft_work_task" and offered["draft"]["due_date"] == "2026-10-16"
    assert offered["silent"] is True                                        # nháp nằm trong chat, không gửi thẻ
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
    assert core_v2.route_providers(core_v2.LANE_NORMAL)[0] == "claude"
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
        for lane, first in ((core_v2.LANE_SMALLTALK, "deepseek-v4.1-flash"), (core_v2.LANE_NORMAL, "claude-sonnet-5-5"),
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


def test_tram_bao_khong_co_kenh_cho_model_thi_nhay_khoa_ke(monkeypatch):
    """Lượt #209 (14/10 16:34): khóa DeepSeek trạm trả 400 «unknown provider for model deepseek-v4.1-flash» → bot báo lỗi
    dù Kimi / Claude phía sau vẫn chạy."""
    from app.modules.agent_hub import manager, user_keys
    from app.modules.agent_hub.ai_keys import KeyRef
    from app.modules.assistant.provider.base import ChatMessage, ProviderError

    class Relay:
        def ask(self, msgs, *, model=None, **kw):
            if user_keys.active_key().endswith("0001"):
                raise ProviderError('openai_compat trả lỗi 400: {"error":{"message":"unknown provider for model '
                                    'deepseek-v4.1-flash","type":"invalid_request_error"}}')
            return _result("chào anh")
    monkeypatch.setitem(manager._DELEGATES, "openai_compat", Relay())
    tram = "https://modelapi.vn/v1"
    chain = [KeyRef(provider="openai_compat", key="k-deepseek-0001", model="deepseek-v4.1-flash", base_url=tram, row_id=1,
                    hint="0001"),
             KeyRef(provider="openai_compat", key="k-kimi-0002", model="kimi-k3", base_url=tram, row_id=2, hint="0002")]
    with user_keys.use_chain(chain, 238):
        out = manager.get_provider().ask([ChatMessage(role="user", content="hello em")])
        assert out.text == "chào anh" and user_keys.active_ref().model == "kimi-k3"


def test_noi_toi_the_ma_khong_co_nhap_thi_viet_lai(db, chat, monkeypatch):
    """Lượt #211/#212 (14/10 16:41): Kimi viết «em đang hỏi lại ở thẻ dưới» mà không gọi công cụ → không có thẻ nào."""
    row = _incoming(db, "tạo cho anh task nghiên cứu luồng agent")
    calls = []

    def script(msgs, tools, execute):
        calls.append([m.content for m in msgs])
        if len(calls) == 1:
            return _result("Còn giao ai và hạn bao giờ thì em đang hỏi lại ở thẻ dưới.")
        return _result("Anh giao cho ai làm, và hạn ngày nào ạ — thứ sáu 17/10 được không?")
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "tạo cho anh task nghiên cứu luồng agent")

    assert len(calls) == 2 and calls[1][-1] == core_v2.PHANTOM_FIX
    assert "thẻ" not in chat.sent[-1] and "giao cho ai" in chat.sent[-1]


def test_co_nhap_that_thi_noi_toi_the_khong_bi_viet_lai():
    ok = _result("Em soạn xong, anh xem thẻ bên dưới.", [{"name": "draft_work_task", "draft": {"title": "A"}}])
    assert not core_v2._phantom_card(ok)
    assert core_v2._phantom_card(_result("Em đang hỏi lại ở thẻ dưới."))


def test_lich_su_bo_tin_cu_noi_toi_the(db):
    """Đường cũ ghi «(đã soạn bản nháp, xem thẻ bên dưới)» thay cho thẻ; Kimi chép lại câu đó thay vì gọi công cụ."""
    service.log_message(db, DIR_IN, CHAT, 0, "tạo task A", action=ACT_ASKED)
    service.log_message(db, DIR_OUT, CHAT, 0, "(đã soạn bản nháp, xem thẻ bên dưới)", action=ACT_ANSWER)
    service.log_message(db, DIR_OUT, CHAT, 0, "Em đã soạn nháp công việc này rồi.", action=ACT_ANSWER)
    db.commit()
    row = _incoming(db, "hello")
    assert [t["content"] for t in core_v2.history(db, CHAT, row.id, row.created_at)] == ["tạo task A"]
    assert core_v2._phantom_card(_result("Em đã soạn nháp công việc này với thông tin gợi ý sẵn."))


def test_nhap_moi_trinh_bay_trong_chat_khong_gui_the(db, chat, monkeypatch):
    """Đại ca 14/10 16:58: «sao có 2 dòng chat… cho nó vào chat thôi» — một tin duy nhất, dòng chờ «tạo» ghi im lặng."""
    row = _incoming(db, "tạo task A, ERP v2, giao Được, hạn thứ sáu")
    monkeypatch.setattr(core_v2.erp, "run_tool", lambda db_, u, name, args: {
        "draft": {"title": "A", "due_date": "2026-10-16"}})
    seen = {}

    def script(msgs, tools, execute):
        out = execute("draft_work_task", {"title": "A"})
        seen["out"] = out
        return _result("Em soạn xong:\nViệc: A\nHạn: 16/10/2026 (thứ Sáu)\nĐổi gì không ạ?",
                       [{"name": "draft_work_task", "draft": out["draft"]}])
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "tạo task A, ERP v2, giao Được, hạn thứ sáu")

    assert seen["out"]["tom_tat_se_luu"]                                    # model nhận đúng bản tóm tắt sẽ lưu
    assert len(chat.sent) == 1 and "Việc: A" in chat.sent[0] and "BẢN NHÁP" not in chat.sent[0]
    pending = db.query(AgentMessage).filter(AgentMessage.action == ACT_DRAFT_WAIT).one()
    assert json.loads(pending.body)["draft"]["title"] == "A"


def test_lich_15_ngay_dung_thu():
    from datetime import date

    block = core_v2.calendar_block(datetime(2026, 10, 14, 9, 0))
    assert "thứ Tư 14/10/2026 (hôm nay)" in block and "thứ Năm 15/10/2026 (mai)" in block
    assert "thứ Sáu 16/10/2026" in block and "thứ Bảy 17/10/2026" in block
    assert date(2026, 10, 17).weekday() == 5


def test_doc_bao_va_tim_web_la_cong_cu_cua_loi(db, chat, monkeypatch):
    """Đại ca 14/10: «giờ bot đọc báo được chưa, hoặc tổng hợp thông tin» — lõi mới phải có công cụ đọc tin / tìm web."""
    from app.modules.agent_hub import news_digest, web_search

    monkeypatch.setattr(news_digest, "_search", lambda q: [
        {"title": f"Giá {q.split(' tin')[0]} tăng", "snippet": "tăng 2%", "url": f"https://vnexpress.net/{len(q)}"}])
    monkeypatch.setattr(news_digest, "age_hours", lambda it, now: 5)
    monkeypatch.setattr(web_search, "fetch", lambda url: "Nội dung bài: giá tăng 2% so với tuần trước.")
    monkeypatch.setattr(web_search, "gather", lambda q: ([{"title": "Trang A", "url": "https://a.vn"}], "[1] Trang A — nội dung"))
    row = _incoming(db, "đọc báo hôm nay về thép giúp anh")
    seen = {}

    def script(msgs, tools, execute):
        assert {"news_today", "search_web", "my_saved_drafts"} <= {t.name for t in tools}
        seen["news"] = execute("news_today", {"topics": ["thép", "phân bón"]})
        seen["web"] = execute("search_web", {"query": "giá thép"})
        return _result("Hôm nay giá thép tăng 2% [vnexpress].")
    _install(monkeypatch, script)

    core_v2.handle(db, CHAT, row, "đọc báo hôm nay về thép giúp anh")

    first = seen["news"]["tin"]["thép"][0]
    assert first["link"].startswith("https://vnexpress.net/") and "giá tăng 2%" in first["noi_dung"]   # có nội dung bài
    assert seen["web"]["nguon"][0]["url"] == "https://a.vn"
    assert "giá thép tăng" in chat.sent[-1]


def test_doc_bao_di_luong_viec_nang_va_noi_da_lam_ma_khong_co_cong_cu_thi_viet_lai():
    """14/10 17:16: tin tổng hợp hời hợt; 17:17 Gemini lite «em đã bỏ task đó rồi» mà không gọi drop_draft."""
    assert core_v2.lane_of("tổng hợp tin về thị trường phân bón tuần này") == core_v2.LANE_HEAVY
    assert core_v2._phantom_card(_result("Dạ, em đã bỏ task nghiên cứu đó rồi đại ca."))
    assert not core_v2._phantom_card(_result("Dạ, em đã bỏ rồi.", [{"name": "drop_draft", "result": {"ok": True}}]))


def test_cong_cu_ke_hoach_chi_khi_cau_noi_ke_hoach(db, monkeypatch):
    """Soi 88k token 15/10: draft_work_plan (3,5k ký tự) đi kèm mọi câu «tạo task» vì cùng nhóm work."""
    from types import SimpleNamespace as NS

    from app.modules.assistant.provider.base import ToolDef

    defs = [ToolDef(name=n, description="x", parameters={}) for n in ("draft_work_task", "draft_work_plan", "my_work_tasks")]
    monkeypatch.setattr(core_v2.erp, "tool_defs", lambda db_, u=None: defs)
    user = NS(id=1)
    task_tools = {t.name for t in core_v2.select_tools(db, user, "tạo cho anh task nghiên cứu luồng agent")}
    plan_tools = {t.name for t in core_v2.select_tools(db, user, "lập kế hoạch thử bot tuần này")}
    assert "draft_work_plan" not in task_tools and "draft_work_task" in task_tools
    assert "draft_work_plan" in plan_tools
    assert len(core_v2._clip("a\n" * 2000, 1200)) < 1300


# ---------------------------------------------------------------------------
# ai-CR-201 — B2: nối tính năng cũ vào lõi (lối tắt chữ chạy trước + công cụ mới cho lời nói tự nhiên)
# ---------------------------------------------------------------------------
def _no_model(monkeypatch):
    called: list = []
    _install(monkeypatch, lambda msgs, tools, execute: called.append(1) or _result("không được gọi"))
    return called


def test_bot_vua_lam_gi_di_loi_tat_hoan_tac_khong_goi_model(db, chat, monkeypatch):
    called = _no_model(monkeypatch)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db_, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(core_v2.erp, "my_changes", lambda db_, u, limit=20: [
        {"id": 9, "when": "2026-10-15T08:00:00", "entity": "leave_request", "entity_label": "Đơn nghỉ phép", "doc_code": "NP011",
         "action": 2, "action_label": "Sửa", "summary": "Sửa lý do NP011", "can_undo": True, "undo_reason": "",
         "undo_status": 0, "undo_status_label": "", "url": "/hr/leave-requests/11"}])
    row = _incoming(db, "bot vừa làm gì")
    core_v2.handle(db, CHAT, row, row.body)
    assert called == [] and sent and "NP011" in sent[-1]


@pytest.mark.parametrize("owner,fn,text", [
    (True, "_brief_by_text", "bật bản tin lúc 6h45"),
    (True, "_reminder_by_text", "nhắc anh 15h gọi NCC Hòa Phát"),
    (True, "_deep_research_by_text", "nghiên cứu sâu: giá phân bón quý 4"),
    (True, "_ok_by_text", "ok"),
    (True, "_proposal_by_text", "xác nhận sửa"),
    (True, "route_task_command", "bỏ việc AI-0007"),
    (False, "_brief_by_text", "bản tin của tôi"),
    (False, "_reminder_by_text", "nhắc gì"),
    (False, "_deep_research_by_text", "tổng hợp các tài liệu này"),
])
def test_loi_tat_chu_chay_truoc_vong_tac_tu(db, chat, monkeypatch, owner, fn, text):
    if owner:
        monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", CHAT)
    called = _no_model(monkeypatch)
    hit: list[str] = []

    def fake(db_, chat_id, row, t):
        hit.append(t)
        row.action = "lenh"
        return True

    monkeypatch.setattr(service, fn, fake)
    row = _incoming(db, text)
    core_v2.handle(db, CHAT, row, row.body)
    assert hit == [text] and called == [] and row.action == "lenh"


def test_khong_khop_loi_tat_thi_vao_mo_hinh(db, chat, monkeypatch):
    prov = _install(monkeypatch, lambda msgs, tools, execute: _result("Dạ, em xem rồi."))
    row = _incoming(db, "công nợ Hòa Phát tháng này còn bao nhiêu")
    core_v2.handle(db, CHAT, row, row.body)
    assert prov.seen and row.action == ACT_ASKED


def test_cong_cu_hoan_tac_va_so_thay_doi(db, chat, monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(core_v2.erp, "my_changes", lambda db_, u, limit=20: [
        {"id": 9, "entity_label": "Đơn nghỉ phép", "doc_code": "NP011", "action_label": "Sửa", "summary": "Sửa lý do",
         "can_undo": True, "undo_reason": "", "undo_status_label": "", "url": "/x", "when": "t"}])
    undone: list[int] = []

    def fake_undo(db_, u, change_id, source=0):
        if change_id != 9:
            raise HTTPException(409, "Phiếu đã đổi sau lúc bot ghi")
        undone.append(change_id)
        return {"summary": "Sửa lý do", "doc_code": "NP011", "url": "/hr/leave-requests/11"}

    monkeypatch.setattr(core_v2.erp, "undo_change", fake_undo)
    out: dict = {}

    def script(msgs, tools, execute):
        out["list"] = execute("bot_changes", {})
        out["ok"] = execute("undo_change", {"change_id": 9})
        out["bad"] = execute("undo_change", {"change_id": 3})
        return _result("Em rút lại rồi.", [{"name": "undo_change", "args": {"change_id": 9}}])

    prov = _install(monkeypatch, script)
    row = _incoming(db, "rút lại cái sửa đơn nghỉ lúc nãy giúp anh")
    core_v2.handle(db, CHAT, row, row.body)
    assert {"bot_changes", "undo_change", "set_reminder"} <= set(prov.seen["tools"])
    assert out["list"]["thay_doi"][0]["doc_code"] == "NP011" and "url" not in out["list"]["thay_doi"][0]
    assert out["ok"]["ok"] and undone == [9] and out["ok"]["link"].endswith("/hr/leave-requests/11")
    assert "Không hoàn tác được" in out["bad"]["error"] and "đã đổi" in out["bad"]["error"]


def test_cong_cu_dat_loi_nhac(db, chat, monkeypatch):
    from app.modules.agent_hub import chat_link
    from app.modules.agent_hub.model import AgentReminder

    monkeypatch.setattr(chat_link, "get_active_link", lambda db_, chat_id: SimpleNamespace(user_id=275))
    out: dict = {}

    def script(msgs, tools, execute):
        out["ok"] = execute("set_reminder", {"luc": "15h", "viec": "gọi NCC Hòa Phát về giá thép"})
        out["bad"] = execute("set_reminder", {"luc": "lúc nào đó", "viec": "x"})
        return _result("Dạ, 15h em nhắc anh.", [{"name": "set_reminder", "args": {}}])

    _install(monkeypatch, script)
    row = _incoming(db, "chiều nay nhớ réo anh gọi Hòa Phát hỏi giá thép nhé, tầm 3 giờ")
    core_v2.handle(db, CHAT, row, row.body)
    rem = db.query(AgentReminder).filter(AgentReminder.chat_id == CHAT).one()
    assert out["ok"]["ok"] and rem.text == "gọi NCC Hòa Phát về giá thép" and rem.user_id == 275
    assert "Chưa đọc được giờ" in out["bad"]["error"]


def test_cong_cu_ve_sua_ma_chi_cho_chat_duoc_giao(db, chat, monkeypatch):
    out: dict = {}

    def script(msgs, tools, execute):
        out["tools"] = list(t.name for t in tools)
        out["res"] = execute("create_code_task", {"mo_ta": "Màn danh sách đơn mua hàng: thêm ô lọc theo ngày giao hàng"})
        return _result("Em ghi yêu cầu rồi.", [{"name": "create_code_task", "args": {}}])

    #  Người liên kết không được cấp quyền: không có công cụ, gọi thẳng cũng bị chặn.
    _install(monkeypatch, script)
    row = _incoming(db, "màn đơn mua hàng thêm ô lọc ngày giao giúp anh")
    core_v2.handle(db, CHAT, row, row.body)
    assert "create_code_task" not in out["tools"] and "chưa được cấp quyền" in out["res"]["error"]
    #  Chat chủ bot: có công cụ, ghi một tin INBOX (dấu rỗng) cho vòng gom tạo vé.
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", CHAT)
    monkeypatch.setattr(service, "_ok_by_text", lambda *a: False)
    row = _incoming(db, "màn đơn mua hàng thêm ô lọc ngày giao giúp anh, sửa mã luôn")
    core_v2.handle(db, CHAT, row, row.body)
    assert "create_code_task" in out["tools"] and out["res"]["ok"]
    msg = db.get(AgentMessage, out["res"]["tin"])
    assert msg.direction == DIR_IN and msg.action == "" and "ô lọc theo ngày giao" in msg.body
    assert core_v2._run_local(db, CHAT, row, chat.user, "create_code_task", {"mo_ta": "ngắn"})["error"].startswith("Mô tả quá ngắn")


def test_dang_do_co_the_cho_ok_nghien_cuu(db, chat):
    from app.modules.agent_hub.constants import ACT_RESEARCH_WAIT

    service.log_message(db, DIR_OUT, CHAT, 1, "{}", action=ACT_RESEARCH_WAIT)
    db.commit()
    row = _incoming(db, "x")
    assert "nghiên cứu sâu" in core_v2.pending_block(db, CHAT, row.id, row.created_at)
