"""ai-CR-183 (phase 16.4, đại ca 13/10: «phản hồi chậm quá») — đo trên dev: một lượt soạn nháp 150k–200k token vào,
0,35–0,44 USD, 28–32 giây. Ba việc: (1) gói tri thức nạp theo chủ đề (cả 7 gói ≈ 77.000 ký tự, riêng nhà máy 46.000, trước
đây đi kèm MỌI câu); (2) câu nối tiếp giữ nhóm công cụ cũ thay vì gửi đủ 72; (3) tool soạn nháp trả nháp thì dừng, không gọi
model viết câu chốt (kênh Telegram tự gửi thẻ)."""
from app.modules.assistant import knowledge as kn
from app.modules.assistant import tool_router as tr


def test_goi_tri_thuc_nap_theo_chu_de():
    full = kn.build_system()
    core = kn.build_system(topics=set())
    assert len(core) < len(full) / 2                      # bỏ gói nhà máy + 5 gói phân hệ
    assert "Quy trình thu mua" in core                     # tri thức nền luôn có
    FACTORY = "Bản cô đọng để trợ lý AI tra cứu nhanh"       # câu trong thân gói nhà máy
    DOC = "# Văn thư — quản lý văn bản"
    assert FACTORY in full and FACTORY not in core
    leave = kn.build_system(topics={"leave"})
    assert "# Nghỉ phép" in leave and DOC not in leave and FACTORY not in leave
    assert kn.build_system(topics=None) == full
    titles = kn.omitted_titles({"leave"})
    assert any("NHÀ MÁY" in t for t in titles) and not any("Nghỉ phép" in t for t in titles)
    assert kn.omitted_titles(None) == []


def test_chu_de_goi_theo_nhom_cong_cu_va_tu_khoa():
    assert tr.pack_topics("cho anh nghỉ thứ 6", {"leave"}) == {"leave"}
    assert tr.pack_topics("hôm nay anh có việc gì", {"work"}) == {"work"}
    assert "factory" in tr.pack_topics("quy định hệ thống công việc nhà máy nói gì", {"document"})
    assert tr.pack_topics("đặt phòng họp chiều nay", set()) == {"room"}
    assert tr.pack_topics("chào em", None) is None                        # không rõ → nạp đủ như cũ
    assert "work" in tr.pack_topics("em tạo luôn nhé", set(), recent_text="tạo task trong dự án ERP v2")


def test_cau_noi_tiep_giu_nhom_cu_khong_gui_du():
    assert tr.select("hạn là từ ngày 13 tới thứ 6 tuần sau nhé. em tạo luôn nhé") is None
    follow = tr.select("hạn là từ ngày 13 tới thứ 6 tuần sau nhé. em tạo luôn nhé", recent_tools=["draft_work_task"])
    assert follow is not None and {"draft_work_task", "my_work_tasks"} <= follow and len(follow) < 20


def test_dung_som_khi_tool_soan_nhap_xong(monkeypatch):
    from app.modules.assistant.provider.base import ToolDef
    from app.modules.assistant.provider.openai_compat import DeepSeekProvider

    p = DeepSeekProvider.__new__(DeepSeekProvider)
    monkeypatch.setattr(DeepSeekProvider, "is_configured", lambda self: True)
    monkeypatch.setattr(DeepSeekProvider, "default_model", property(lambda self: "m"))
    posts: list[dict] = []
    first = {"choices": [{"message": {"content": None, "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "draft_work_task", "arguments": "{\"title\": \"A\"}"}}]}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 5}, "model": "m"}
    second = {"choices": [{"message": {"content": "Em soạn xong rồi"}}], "usage": {"prompt_tokens": 60, "completion_tokens": 8}}
    monkeypatch.setattr(DeepSeekProvider, "_post", lambda self, payload: posts.append(payload) or (first if len(posts) == 1 else second))
    from app.modules.assistant.provider.base import ChatMessage

    tool = ToolDef(name="draft_work_task", description="x", parameters={"type": "object", "properties": {}})
    run = lambda **kw: p.run_tools([ChatMessage(role="user", content="tạo task A")], tools=[tool],
                                   execute=lambda n, a: {"draft": {"title": "A"}}, system="s", **kw)
    out = run(stop_when=lambda name, result: isinstance(result.get("draft"), dict))
    assert len(posts) == 1 and out.text == "" and out.tool_calls[0]["draft"] == {"title": "A"} and out.input_tokens == 50
    posts.clear()
    out = run()
    assert len(posts) == 2 and out.text == "Em soạn xong rồi" and out.input_tokens == 110


def test_ask_truyen_stop_on_draft_va_ghi_chu_goi_chua_nap(db, seed, monkeypatch):
    from app.modules.assistant import service
    from app.modules.assistant.provider.base import ChatResult
    from app.modules.user.model import User

    seen: list[dict] = []

    class P:
        name = "fake"
        supports_tools = True

        def run_tools(self, msgs, *, tools, execute, system, stop_when=None, **kw):
            seen.append({"n": len(tools), "system": system, "stop": stop_when})
            return ChatResult(text="ok", provider="fake", model="m", input_tokens=1, output_tokens=1)

    monkeypatch.setattr(service, "get_provider", lambda name=None: P())
    user = db.get(User, seed.u_req_id)
    service.ask("cho anh nghỉ thứ 6 tuần này", db=db, user=user, stop_on_draft=True)
    s = seen[-1]
    assert s["stop"] is not None and s["stop"]("draft_leave_request", {"draft": {}}) and not s["stop"]("payable_lookup", {"draft": {}})
    FACTORY = "Bản cô đọng để trợ lý AI tra cứu nhanh"
    assert "# Nghỉ phép" in s["system"] and FACTORY not in s["system"] and "CHƯA nạp" in s["system"]
    #  ai-CR-192: «chào em» là xã giao → không gói chủ đề, có ghi chú gói chưa nạp; câu lạ không khớp nhóm cũng không nạp gói.
    service.ask("chào em", db=db, user=user)
    assert seen[-1]["stop"] is None and FACTORY not in seen[-1]["system"] and "CHƯA nạp" in seen[-1]["system"]
    assert seen[-1]["n"] == len(__import__("app.modules.assistant.tool_router", fromlist=["CORE"]).CORE)


def test_telegram_goi_ask_voi_stop_on_draft(db, monkeypatch):
    """Kênh Telegram tự gửi thẻ nháp nên luôn xin dừng sớm; tool soạn nháp không còn câu chữ thì sổ vẫn có một dòng bot."""
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import chat_link, service
    from app.modules.agent_hub.constants import ACT_ANSWER, DIR_IN
    from app.modules.agent_hub.model import AgentMessage
    from app.modules.assistant import service as assistant_service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7, is_active=True))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda chat_id: None)
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: None)
    monkeypatch.setattr(service, "deliver_tool_results", lambda db, chat_id, user, calls: None)
    seen: list[dict] = []

    def fake_ask(question, **kw):
        seen.append(kw)
        return {"text": "", "tool_calls": [{"name": "draft_work_task", "args": {}, "draft": {"title": "A"}}], "usage": {}}

    monkeypatch.setattr(assistant_service, "ask", fake_ask)
    row = service.log_message(db, DIR_IN, "12345", 1, "tạo task A")
    db.commit()
    service.answer_question(db, "12345", "tạo task A", before_id=row.id, ledger=False)
    assert seen and seen[-1].get("stop_on_draft") is True
    logged = db.query(AgentMessage).filter(AgentMessage.action == ACT_ANSWER).order_by(AgentMessage.id.desc()).first()
    assert logged is not None and "đã soạn bản nháp" in logged.body


def test_provider_cua_bot_nhan_stop_when(monkeypatch):
    """Vá 13/10 15:20: AgentGeminiProvider (provider Telegram) quên nối `stop_when` → mọi lượt chết TypeError."""
    import inspect

    from app.modules.agent_hub import manager

    p = manager.AgentGeminiProvider()
    seen: list[dict] = []
    monkeypatch.setattr(p, "_call", lambda method, *a, **kw: seen.append({"method": method, **kw}) or "ok")
    marker = lambda n, r: True
    assert p.run_tools([], tools=[], execute=lambda n, a: {}, stop_when=marker) == "ok"
    assert seen[-1]["method"] == "run_tools" and seen[-1]["stop_when"] is marker
    #  Mọi provider thật cũng phải nhận tham số này — khỏi quên lần nữa.
    from app.modules.assistant.provider import claude, gemini, openai_compat

    for cls in (claude.ClaudeProvider, gemini.GeminiProvider, openai_compat.OpenAICompatProvider, manager.AgentGeminiProvider):
        assert "stop_when" in inspect.signature(cls.run_tools).parameters, cls.__name__


def test_loi_goi_ai_kem_ma_luot_va_loai_loi(db, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import chat_link, service
    from app.modules.agent_hub.constants import DIR_IN
    from app.modules.assistant import service as assistant_service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7, is_active=True))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda chat_id: None)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))

    def boom(question, **kw):
        raise TypeError("run_tools() got an unexpected keyword argument 'stop_when'")

    monkeypatch.setattr(assistant_service, "ask", boom)
    row = service.log_message(db, DIR_IN, "12345", 1, "tạo task A")
    db.commit()
    service.answer_question(db, "12345", "tạo task A", before_id=row.id, ledger=False)
    assert "Em gặp lỗi khi gọi AI" in sent[-1] and "Mã lượt #" in sent[-1] and "TypeError" in sent[-1]
