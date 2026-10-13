"""ai-CR-180 (13/10) — đại ca nhắn «vậy tao task đó igups anh đi nhé.» (gõ thiếu dấu «tạo», sai chính tả «giúp») khi đang có
bản nháp công việc chờ: bot không nhận ra là xác nhận, đem đi phân loại và ghi thành việc sửa mã AI-0007. Nay xác nhận nháp
chịu được chữ không dấu, và trạm phân loại được báo «đang có nháp chờ tạo»."""
import json
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import service


def test_loose_confirm_chiu_khong_dau_nhung_khong_an_cau_khac():
    assert service._loose_confirm("vậy tao task đó igups anh đi nhé.")
    assert service._loose_confirm("tao di em") and service._loose_confirm("ok tạo luôn")
    assert not service._loose_confirm("trả lời cho tao")                  # «tao» = tôi, không phải «tạo»
    assert not service._loose_confirm("tao task khác giúp anh")           # có ý đổi → soạn lại
    assert not service._loose_confirm("tạo task hạn 15/10 cho anh Được")   # có số → nhờ soạn lại
    assert not service._loose_confirm("hiện trên nhóm task đó có bao nhiêu cột trạng thái vậy em để a biết a tạo nè")


@pytest.fixture
def chat(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import erp

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7))
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    created: list = []
    monkeypatch.setattr(erp, "create_draft", lambda db, user, kind, draft: created.append((kind, draft)) or ("", 99))
    return sent, created


def _card(db):
    from app.modules.agent_hub.constants import ACT_DRAFT_WAIT, DIR_OUT

    body = json.dumps({"kind": "work_task", "user_id": 7, "draft": {"title": "Nghiên cứu luồng agent 2 agent"}})
    row = service.log_message(db, DIR_OUT, "12345", 1, body, action=ACT_DRAFT_WAIT)
    db.commit()
    return row


def _say(db, text, n=2):
    from app.modules.agent_hub.constants import DIR_IN

    row = service.log_message(db, DIR_IN, "12345", n, text)
    db.commit()
    return row


def test_tao_khong_dau_sau_the_nhap_thi_tao_viec(db, chat):
    sent, created = chat
    _card(db)
    row = _say(db, "hiện trên nhóm task đó có bao nhiêu cột trạng thái vậy em. để a biết a tạo nè")
    assert not service._draft_by_text(db, "12345", row, row.body)          # câu hỏi xen giữa: không tạo
    row = _say(db, "vậy tao task đó igups anh đi nhé.", 3)
    assert service._draft_by_text(db, "12345", row, row.body)
    assert created == [("work_task", {"title": "Nghiên cứu luồng agent 2 agent"})] and "Đã tạo" in sent[-1]


def test_mach_phan_loai_biet_dang_co_nhap_cho(db, chat):
    row = _say(db, "vậy tao task đó igups anh đi nhé.", 3)
    assert "nháp" not in service._intent_context(db, "12345", row.id)
    _card(db)
    row = _say(db, "vậy tao task đó igups anh đi nhé.", 4)
    ctx = service._intent_context(db, "12345", row.id)
    assert "đang chờ người dùng nhắn «tạo»" in ctx and "Nghiên cứu luồng agent 2 agent" in ctx and "KHÔNG phải sửa phần mềm" in ctx
    from app.modules.agent_hub.constants import ACT_DRAFT_DONE

    pending = db.query(service.AgentMessage).filter(service.AgentMessage.action == "cho_tao").one()
    pending.action = ACT_DRAFT_DONE
    db.commit()
    assert "nháp" not in service._intent_context(db, "12345", row.id)      # thẻ đã dùng: không nhắc nữa


def test_loi_dan_phan_loai_co_vi_du_task_du_an():
    from app.modules.agent_hub import manager

    assert "lên task gọi NCC" in manager.INTENT_SYSTEM and "PHÂN HỆ DỰ ÁN" in manager.INTENT_SYSTEM
