"""ai-CR-148 — đại ca 09/10/2026 (ảnh chat): bot nói tool chưa sửa được dòng hàng / đơn nghỉ; đại ca nhắn «oke phát triển
tính năng», rồi «em bắt đầu sửa luôn chưa» → bot trả «em không phải bên sửa phần mềm, chỉ ghi đề xuất». Ở chat GIAO ĐƯỢC việc
sửa mã thì câu đó phải thành VIỆC sửa phần mềm, mô tả lấy từ mạch trước."""
import pytest

from app.core.config import settings


@pytest.fixture
def owner(db, monkeypatch):
    from app.modules.agent_hub import service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    acks: list[int] = []
    monkeypatch.setattr(service, "ack_task_message", lambda db, chat_id, row: acks.append(row.id))
    return service, acks


def _talk(db, service, chat_id="12345"):
    from app.modules.agent_hub.constants import ACT_ANSWER, ACT_ASKED, DIR_IN, DIR_OUT

    service.log_message(db, DIR_IN, chat_id, 1, "bot sửa được đơn nghỉ phép chưa", action=ACT_ASKED)
    service.log_message(db, DIR_OUT, chat_id, 0, "Chưa: tool propose_document_update chỉ sửa phần đầu YCMH/YCBG; "
                        "đơn nghỉ phép, dòng hàng, số lượng thì bot chưa sửa được.", action=ACT_ANSWER)
    db.commit()


@pytest.mark.parametrize("text", ["oke phát triển tính năng", "Ok em phát triển tính năng này luôn nhé",
                                  "em bắt đầu sửa luôn chưa", "làm tính năng đó đi em", "code luôn đi"])
def test_cau_nho_phat_trien_thanh_viec_kem_ngu_canh(db, owner, text):
    from app.modules.agent_hub.constants import DIR_IN

    service, acks = owner
    _talk(db, service)
    row = service.log_message(db, DIR_IN, "12345", 9, text)
    db.commit()
    assert service._dev_request_by_text(db, "12345", row, text)
    assert acks == [row.id] and row.action == ""                      # nằm INBOX cho vòng gom
    assert row.body.startswith(text) and "đơn nghỉ phép" in row.body and "propose_document_update" in row.body


def test_chat_khong_giao_duoc_viec_va_cau_thuong_khong_bi_nuot(db, owner):
    from app.modules.agent_hub.constants import DIR_IN

    service, acks = owner
    row = service.log_message(db, DIR_IN, "999", 9, "oke phát triển tính năng")
    assert service._dev_request_by_text(db, "999", row, "oke phát triển tính năng") is False   # người thường
    for text in ("tính năng sửa đơn có chưa", "sửa đơn NP011 giúp anh", "phát triển kinh doanh quý 4 thế nào"):
        row = service.log_message(db, DIR_IN, "12345", 9, text)
        assert service._dev_request_by_text(db, "12345", row, text) is False, text
    assert acks == []


def test_chat_giao_duoc_viec_thi_tro_ly_khong_choi(db, owner, monkeypatch):
    from app.modules.agent_hub.constants import BOT_CODE_FACT

    service, _ = owner
    assert service._can_order_code(db, "12345") and not service._can_order_code(db, "999")
    assert "KHÔNG nói «em không sửa được phần mềm»" in BOT_CODE_FACT
