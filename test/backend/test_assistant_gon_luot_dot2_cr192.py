"""ai-CR-192 (16.5 đợt 2, 13/10 16:27 anh Được thấy chậm): «hello» 70 s vì (1) bước đọc ý định chờ Gemini quá tải đủ 25 s
mới đổi model, (2) câu xã giao vẫn nạp đủ 73 công cụ + 7 gói tri thức (56k token). Nay: trần chờ theo lượt cho bước ý định;
xã giao → nhóm lõi + không gói; câu không khớp nhóm → đủ công cụ nhưng không gói chủ đề, model xin thêm được."""
from app.modules.assistant import tool_router as tr
from app.modules.assistant.provider import base


def test_nhan_cau_xa_giao():
    for t in ("hello", "Hi", "chào em", "Chào Lạc Lạc", "cảm ơn em nhé", "ok", "alo", "test"):
        assert tr.is_smalltalk(t), t
    for t in ("chào em, công nợ Hòa Phát còn bao nhiêu", "giá vàng hôm nay", "ok tạo luôn", "hello anh muốn hỏi về nghỉ phép"):
        assert not tr.is_smalltalk(t), t


def test_tran_cho_theo_luot():
    assert base.request_timeout(60) == 60
    with base.with_timeout(10):
        assert base.request_timeout(60) == 10
        assert base.request_timeout(5) == 5                 # không vượt trần của provider
    assert base.request_timeout(60) == 60


def test_buoc_y_dinh_cho_toi_da_theo_cau_hinh(monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import manager
    from app.modules.assistant.provider.base import ChatResult

    seen: list = []

    def fake_ask(self, messages, **kw):
        seen.append(base.REQUEST_TIMEOUT.get())
        return ChatResult(text='{"intent": "hoi", "scope": "cong_ty", "reason": "x"}', provider="p", model="m")

    monkeypatch.setattr(manager.AgentGeminiProvider, "ask", fake_ask)
    monkeypatch.setattr(settings, "AGENT_INTENT_TIMEOUT", 7)
    manager.run_intent("công nợ Hòa Phát")
    assert seen == [7] and base.REQUEST_TIMEOUT.get() is None


def test_khong_khop_nhom_thi_du_cong_cu_nhung_khong_goi_va_xin_them_duoc(db, seed, monkeypatch):
    from app.modules.assistant import service
    from app.modules.assistant.provider.base import ChatResult
    from app.modules.user.model import User

    calls: list[tuple[int, str]] = []
    FACTORY = "Bản cô đọng để trợ lý AI tra cứu nhanh"

    class P:
        name = "fake"
        supports_tools = True

        def run_tools(self, msgs, *, tools, execute, system, **kw):
            calls.append((len(tools), system))
            #  Model «cần gói nhà máy»: thiếu thì xin thêm, có thì trả lời.
            return ChatResult(text="xong" if FACTORY in system else tr.NEED_MORE_TOOLS, provider="fake", model="m")

    monkeypatch.setattr(service, "get_provider", lambda name=None: P())
    out = service.ask("cho anh hỏi quy định nhà máy về ca làm", db=db, user=db.get(User, seed.u_req_id))
    #  Câu này khớp gói nhà máy theo từ khóa dù không khớp nhóm công cụ → gói nhà máy có, không cần xin thêm.
    assert len(calls) == 1 and FACTORY in calls[0][1]
    calls.clear()
    out = service.ask("cho anh hỏi cái này được không", db=db, user=db.get(User, seed.u_req_id))
    assert FACTORY not in calls[0][1] and "CHƯA nạp" in calls[0][1] and calls[0][0] > 40
    assert len(calls) == 2 and FACTORY in calls[1][1] and out["usage"]["tools_retried"] is True   # xin thêm → nạp đủ
