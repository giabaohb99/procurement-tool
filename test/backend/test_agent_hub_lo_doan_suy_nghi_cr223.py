"""ai-CR-223 — vá 19/10/2026: đại ca gửi Lạc Lạc tệp kế hoạch (.md) kèm câu hỏi, bot trả nguyên đoạn «suy nghĩ» tiếng Anh
(«The user wants me to review the plan…», lượt #358 trên dev: deepseek-v4.1-flash, ra đủ 8192 token, chưa có câu trả lời).

Gốc: đường hỏi về TỆP (`service.answer_question(kind="document")`) không đi core_v2 nên không có phân luồng model — chuỗi
khóa rơi vào khóa trạm đầu tiên. Canh:
  - đường này nay chọn hãng / model theo ĐÚNG luật luồng của core_v2 (Claude đứng đầu, Haiku luồng thường), tính trên
    câu NGƯỜI DÙNG hỏi chứ không trên nội dung tệp (tệp dài không được tự đẩy sang luồng nặng);
  - lớp chặn thứ hai: câu trả về là đoạn suy nghĩ (mở bằng «The user / Let me / Okay,…», phần đầu không có chữ tiếng Việt
    có dấu) thì KHÔNG gửi, thay bằng câu xin lỗi kèm mã lượt; câu tiếng Việt bình thường không bao giờ bị chặn.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.modules.agent_hub import chat_link, core_v2, service
from app.modules.agent_hub.constants import DIR_IN
from app.modules.assistant import service as assistant_service

LEAKED = ("The user wants me to review the plan and then create calendar events. Let me think about what to do.\n\n"
          "They asked: \"a có viết lại kế hoạch nè, em thấy tốt hơn không\"")


def test_nhan_dien_doan_suy_nghi_lo_ra():
    #  Đúng câu lượt #358: đoạn suy nghĩ trích lại lời người dùng TIẾNG VIỆT ngay đoạn thứ hai — vẫn phải bắt.
    assert service.looks_like_leaked_reasoning(LEAKED)
    for t in ("Okay, so the plan has five days.", "Let me check the calendar first.", "  I need to create events"):
        assert service.looks_like_leaked_reasoning(t), t
    for t in ("Kế hoạch mới tốt hơn anh ạ: ngày 19/11 xuất phát…", "OK anh, em đã tạo 5 sự kiện.", "",
              "The plan looks good — Phan Rang 2 đêm.",           # tiếng Anh nhưng không mở kiểu suy nghĩ
              "The user wants em tạo lịch — đã tạo xong ạ."):       # có chữ tiếng Việt có dấu → là câu trả lời thật
        assert not service.looks_like_leaked_reasoning(t), t


@pytest.fixture
def bot(db, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7, is_active=True))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda chat_id: None)
    monkeypatch.setattr(service, "deliver_tool_results", lambda db, chat_id, user, calls: None)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    routed: list[tuple] = []

    @contextmanager
    def prefer(providers, *, model=""):
        routed.append((tuple(providers), model))
        yield

    monkeypatch.setattr(service.user_keys, "prefer", prefer)
    return SimpleNamespace(sent=sent, routed=routed)


def test_hoi_ve_tep_chon_model_theo_luong_cua_core_v2(db, bot, monkeypatch):
    monkeypatch.setattr(assistant_service, "ask", lambda q, **kw: {"text": "Kế hoạch ổn anh ạ.", "tool_calls": [], "usage": {}})
    row = service.log_message(db, DIR_IN, "12345", 1, "[tệp kế hoạch.md] em thấy tốt hơn không")
    db.commit()
    content = "Ngày 1: Cần Thơ → Phan Rang.\n" * 400          # tệp DÀI — không được tự đẩy câu sang luồng nặng
    question = f"a có viết lại kế hoạch nè, em thấy tốt hơn không\n\n{service.DOC_GUIDE}\n\nNỘI DUNG TỆP «k.md»:\n{content}"
    service.answer_question(db, "12345", question, before_id=row.id, kind="document", ledger=False)
    lane = core_v2.lane_of("a có viết lại kế hoạch nè, em thấy tốt hơn không")
    assert lane == core_v2.LANE_NORMAL
    assert bot.routed == [(tuple(core_v2.route_providers(lane)), core_v2.lane_model(lane))]
    assert bot.routed[0][0][0] == "claude" and bot.sent == ["Kế hoạch ổn anh ạ."]


def test_doan_suy_nghi_khong_bao_gio_toi_nguoi_dung(db, bot, monkeypatch):
    monkeypatch.setattr(assistant_service, "ask", lambda q, **kw: {"text": LEAKED * 20,
                                                                   "tool_calls": [], "usage": {"output_tokens": 8192}})
    row = service.log_message(db, DIR_IN, "12345", 1, "xem giúp kế hoạch")
    db.commit()
    service.answer_question(db, "12345", "xem giúp kế hoạch", before_id=row.id, kind="document", ledger=False)
    assert len(bot.sent) == 1 and "The user wants" not in bot.sent[0]
    assert "nháp suy nghĩ" in bot.sent[0] and "Mã lượt #" in bot.sent[0]
