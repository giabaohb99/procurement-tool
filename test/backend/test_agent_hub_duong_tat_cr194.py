"""ai-CR-194 (13/10, đại ca: «hồi trước trả lời gần như tức thì»; Agent 1 đo: 06/10 trung bình 5,8 s, 13/10 23,8 s; lời nhắc
phân loại phình 1,5k → 3,6k token). Nay: tra nhanh / xã giao đi thẳng (bỏ bước đọc ý định); lời nhắc phân loại rút gọn;
ngữ cảnh việc tối đa 5 dòng."""
from types import SimpleNamespace


def test_loi_dan_phan_loai_gon_ma_du_y():
    from app.modules.agent_hub import manager

    s = manager.INTENT_SYSTEM
    assert len(s) <= 4500
    for must in ('"hoi"', '"viec"', '"thao_tac"', '"tra_cuu"', '"du_lieu"', '"mo_ho"', "lên task gọi NCC", "PHÂN HỆ DỰ ÁN",
                 "tao task do di", "scope", "CHỈ trả JSON", "kiem_chung", "sua_ke_hoach"):
        assert must in s, must


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


def test_tra_nhanh_va_xa_giao_bo_qua_buoc_doc_y_dinh(db, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import ACT_ASKED, DIR_IN

    calls = _chat(db, monkeypatch, service)

    def say(text):
        row = service.log_message(db, DIR_IN, "12345", 1, text)
        db.commit()
        service._route_plain_text(db, "12345", row, text)
        return row

    row = say("giá vàng hôm nay")
    assert calls["research"] == [("giá vàng hôm nay", "web")] and calls["intent"] == [] and row.action == ACT_ASKED
    row = say("chào em")
    assert calls["answer"] == ["chào em"] and calls["intent"] == [] and row.action == ACT_ASKED
    say("công nợ Hòa Phát còn bao nhiêu")
    assert calls["intent"] == ["công nợ Hòa Phát còn bao nhiêu"]        # câu thường vẫn qua bước đọc ý định


def test_chat_nguoi_lien_ket_cung_di_duong_tat(db, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    calls = _chat(db, monkeypatch, service)
    monkeypatch.setattr(service.telegram, "is_allowed_chat", lambda chat_id: False)
    row = service.log_message(db, DIR_IN, "999", 1, "tỷ giá USD hôm nay")
    db.commit()
    service._route_linked_text(db, "999", row, "tỷ giá USD hôm nay")
    assert calls["research"] == [("tỷ giá USD hôm nay", "web")] and calls["intent"] == []


def test_tat_buoc_doc_y_dinh_thi_di_thang_tro_ly(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import ACT_ASKED, DIR_IN

    calls = _chat(db, monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_INTENT_ENABLED", False)
    row = service.log_message(db, DIR_IN, "12345", 1, "công nợ Hòa Phát còn bao nhiêu")
    db.commit()
    service._route_plain_text(db, "12345", row, "công nợ Hòa Phát còn bao nhiêu")
    assert calls["intent"] == [] and calls["answer"] == ["công nợ Hòa Phát còn bao nhiêu"] and row.action == ACT_ASKED
    monkeypatch.setattr(service.telegram, "is_allowed_chat", lambda chat_id: False)
    row = service.log_message(db, DIR_IN, "999", 2, "đơn nghỉ của tôi")
    db.commit()
    service._route_linked_text(db, "999", row, "đơn nghỉ của tôi")
    assert calls["intent"] == [] and calls["answer"][-1] == "đơn nghỉ của tôi"


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
