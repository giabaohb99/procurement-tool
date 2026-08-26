"""Hồi quy cho `conversation.chat` — LƯU lượt hỏi + guard hạn mức.

Vì sao có bộ này: `chat` từng dính lỗi TRÙNG TÊN — biến cục bộ `usage = result.get(...)` che
mất module `usage` đã import, khiến `usage.check_daily_limit(...)` ở đầu hàm nổ
`UnboundLocalError` -> MỌI câu chat 500. Test dưới đây chạy hết thân hàm nên bắt được ngay nếu
tái diễn. KHÔNG gọi model thật: thay `service.ask` bằng hàm giả trả dict cố định.
"""
from datetime import datetime

import pytest

from app.core.config import settings
from app.modules.assistant import conversation as convo
from app.modules.assistant import usage
from app.modules.assistant.model import AssistantMessage, MessageRole
from app.modules.assistant.schema import AskIn
from app.modules.user.model import User


def _fake_ask(**kwargs):
    """Giả tầng service: bỏ qua model thật, trả đúng hình dạng `service.ask` cam kết."""
    return {
        "text": "Đây là câu trả lời mẫu.",
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "kind": kwargs.get("kind", "general"),
        "tool_calls": [],
        "usage": {
            "input_tokens": 111,
            "output_tokens": 22,
            "thinking_tokens": 3,
            "cache_read_tokens": 4,
            "cache_write_tokens": 5,
        },
    }


def test_chat_luu_luot_hoi_va_khong_dinh_unbound(db, seed, monkeypatch):
    """Câu hỏi mới -> mở hội thoại, lưu 2 tin (user + trợ lý), gắn token vào tin trợ lý.

    Nếu biến `usage` bị đặt trùng tên module trở lại, hàm sẽ nổ UnboundLocalError TRƯỚC khi tới
    đây -> test đỏ. Đó chính là chốt hồi quy.
    """
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 0)  # tắt trần cho nhánh này
    monkeypatch.setattr(convo.service, "ask", lambda *a, **k: _fake_ask(**k))
    user = db.get(User, seed.u_req_id)

    out = convo.chat(db, user, AskIn(message="Cách tạo yêu cầu mua hàng?"))

    assert out["conversation_id"] is not None
    assert out["text"] == "Đây là câu trả lời mẫu."

    msgs = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.conversation_id == out["conversation_id"])
        .order_by(AssistantMessage.id)
        .all()
    )
    assert [int(m.role) for m in msgs] == [int(MessageRole.USER), int(MessageRole.ASSISTANT)]
    assert msgs[0].content == "Cách tạo yêu cầu mua hàng?"
    # Token của lượt trả lời phải được ghi từ `usage` (chứng minh biến cục bộ đã tách tên).
    bot = msgs[1]
    assert bot.input_tokens == 111
    assert bot.output_tokens == 22
    assert bot.cache_write_tokens == 5


def test_chat_chan_khi_cham_tran_truoc_khi_goi_model(db, seed, monkeypatch):
    """Chạm hạn mức/ngày -> ném QuotaExceeded NGAY, không đụng tới `service.ask`.

    Cũng gián tiếp khẳng định module `usage` (dòng `usage.check_daily_limit`) không bị che.
    """
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 1)

    def _boom(*a, **k):
        raise AssertionError("service.ask không được gọi khi đã chạm trần")

    monkeypatch.setattr(convo.service, "ask", _boom)
    user = db.get(User, seed.u_req_id)

    # Đã có 1 câu hỏi hôm nay -> chạm trần 1/1.
    db.add(AssistantMessage(
        conversation_id=1, role=MessageRole.USER, content="x",
        created_by=user.id, updated_by=user.id, created_at=datetime.now(),
    ))
    db.commit()

    with pytest.raises(usage.QuotaExceeded):
        convo.chat(db, user, AskIn(message="Câu thứ hai bị chặn"))
