"""ai-CR-194 (13/10, đại ca: «hồi trước trả lời gần như tức thì»; Agent 1 đo: 06/10 trung bình 5,8 s, 13/10 23,8 s; lời nhắc
phân loại phình 1,5k → 3,6k token). Nay: tra nhanh / xã giao đi thẳng (bỏ bước đọc ý định); lời nhắc phân loại rút gọn;
ngữ cảnh việc tối đa 5 dòng."""
from types import SimpleNamespace



def _chat(db, monkeypatch, service):
    from app.core.config import settings
    from app.modules.agent_hub import chat_link

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7, is_active=True))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: None)
    calls: dict[str, list] = {"research": [], "answer": [], "intent": []}
    monkeypatch.setattr(service, "run_research", lambda db, chat_id, q, mode: calls["research"].append((q, mode)))
    monkeypatch.setattr(service, "answer_question", lambda db, chat_id, q, **kw: calls["answer"].append(q))
    monkeypatch.setattr(service.manager, "run_intent", lambda text, **kw: calls["intent"].append(text) or (
        {"intent": "hoi", "scope": 1}, SimpleNamespace(text="", provider="p", model="m", input_tokens=0, output_tokens=0,
                                                       thinking_tokens=0, cache_read_tokens=0)))
    return calls



def test_bao_nhan_tuc_thi_roi_xoa(monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service

    sent: list[str] = []
    deleted: list[int] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, chat_id="", **kw: sent.append(text) or 77)
    monkeypatch.setattr(service.telegram, "delete_message", lambda chat_id, mid: deleted.append(mid) or True)
    monkeypatch.setattr(service.channels, "is_telegram", lambda chat_id: True)
    monkeypatch.setattr(settings, "AGENT_ACK_ENABLED", True)
    with service._instant_ack("12345", "công nợ Hòa Phát"):
        assert sent == ["Em nhận rồi, đang xử lý…"] and deleted == []
    assert deleted == [77]
    sent.clear(); deleted.clear()
    with service._instant_ack("12345", "/hoi x"):             # lệnh / không báo nhận
        pass
    monkeypatch.setattr(settings, "AGENT_ACK_ENABLED", False)
    with service._instant_ack("12345", "chào em"):
        pass
    assert sent == [] and deleted == []
