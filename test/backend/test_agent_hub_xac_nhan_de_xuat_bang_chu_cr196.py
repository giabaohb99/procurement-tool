"""ai-CR-196 (14/10) — nút bấm từ chat không phải đại ca bị cửa nút bỏ im lặng (Agent 1 phát hiện), nên người đã liên kết
không xác nhận được thẻ sửa / xóa phiếu. Nay thẻ đề xuất có ĐƯỜNG CHỮ: «xác nhận» / «đồng ý» → ghi, «không sửa» / «thôi» →
bỏ; trong 15 phút; có thẻ chờ khác mới hơn thì không nuốt."""
import json
from datetime import timedelta

from app.modules.agent_hub import service
from app.modules.agent_hub.constants import ACT_DRAFT_WAIT, ACT_PROPOSAL, DIR_IN, DIR_OUT


def _card(db, chat="999", code="NP011"):
    row = service.log_message(db, DIR_OUT, chat, 5, json.dumps({"code": code, "entity_label": "Đơn nghỉ phép", "action": "update"}),
                              action=ACT_PROPOSAL)
    db.commit()
    return row


def _say(db, text, chat="999", n=9):
    row = service.log_message(db, DIR_IN, chat, n, text)
    db.commit()
    return row


def test_xac_nhan_va_bo_bang_chu(db, monkeypatch):
    resolved: list[tuple] = []
    monkeypatch.setattr(service, "_resolve_proposal", lambda db, chat_id, cb_id, action, msg_id: resolved.append((chat_id, cb_id, action, msg_id)))
    assert not service._proposal_by_text(db, "999", _say(db, "xác nhận"), "xác nhận")      # chưa có thẻ
    card = _card(db)
    assert service._proposal_by_text(db, "999", _say(db, "Xác nhận sửa"), "Xác nhận sửa")
    assert resolved == [("999", "", "sua", card.id)]
    card2 = _card(db, code="NP012")
    assert service._proposal_by_text(db, "999", _say(db, "không sửa"), "không sửa")
    assert resolved[-1] == ("999", "", "khong_sua", card2.id)
    #  Câu thường không phải xác nhận.
    assert not service._proposal_by_text(db, "999", _say(db, "xác nhận giúp anh là đơn đã duyệt chưa"), "xác nhận giúp anh là đơn đã duyệt chưa")


def test_qua_han_hoac_co_the_cho_khac_moi_hon_thi_khong_nuot(db, monkeypatch):
    resolved: list = []
    monkeypatch.setattr(service, "_resolve_proposal", lambda *a: resolved.append(a))
    card = _card(db)
    card.created_at = card.created_at - timedelta(minutes=20)
    db.commit()
    assert not service._proposal_by_text(db, "999", _say(db, "đồng ý"), "đồng ý") and resolved == []
    card = _card(db)
    service.log_message(db, DIR_OUT, "999", 6, "{}", action=ACT_DRAFT_WAIT)        # thẻ nháp mới hơn → «đồng ý» là của nó
    db.commit()
    assert not service._proposal_by_text(db, "999", _say(db, "đồng ý"), "đồng ý") and resolved == []


def test_chat_lien_ket_di_qua_chuoi_lenh(db, monkeypatch):
    """Người liên kết (không phải chat đại ca) nhắn «xác nhận» sau thẻ → tới `_resolve_proposal`, không rơi xuống Trợ lý."""
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import chat_link

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service.telegram, "is_allowed_chat", lambda chat_id: False)
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7, is_active=True))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    answered: list = []
    monkeypatch.setattr(service, "answer_question", lambda *a, **kw: answered.append(a))
    resolved: list = []
    monkeypatch.setattr(service, "_resolve_proposal", lambda *a: resolved.append(a))
    _card(db)
    row = _say(db, "xác nhận")
    from app.modules.agent_hub import core_v2

    #  ai-CR-206: đường cũ đã xóa — chuỗi lệnh chữ của người liên kết nay là `core_v2.shortcut` (chạy trước model).
    assert core_v2.shortcut(db, "999", row, "xác nhận")
    assert len(resolved) == 1 and resolved[0][3] and answered == []
