"""ai-CR-229 — prod đợt hai 19/10/2026 (đại ca chốt): dịch vụ AI tách trên prod chỉ bật chat / Trợ lý web / MCP / nhắc hạn
việc; mọi vòng chạy nền TỐN TIỀN MODEL phải tắt được bằng cờ. Trước đây bản tin, tóm tắt cuối buổi và vòng gom vé sửa mã
không có cờ riêng (chỉ có AGENT_HUB_ENABLED tắt cả bot).
"""
import pytest

from app.core.config import settings
from app.modules.agent_hub import tasks

CASES = [("triage_inbox_task", "AGENT_TRIAGE_ENABLED"), ("pull_tickets_task", "AGENT_TRIAGE_ENABLED"),
         ("learning_tick_task", "AGENT_TRIAGE_ENABLED"), ("briefs_due_task", "AGENT_BRIEFS_ENABLED"),
         ("meeting_reminders_task", "AGENT_BRIEFS_ENABLED"), ("session_summary_task", "AGENT_SESSION_SUMMARY_ENABLED")]


@pytest.mark.parametrize("fn,flag", CASES)
def test_co_tat_thi_vong_bo_qua_khong_mo_db(fn, flag, monkeypatch):
    monkeypatch.setattr(tasks, "_off", lambda: None)                   # bot đang bật
    monkeypatch.setattr(settings, flag, False)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: pytest.fail("cờ tắt mà vẫn mở DB / gọi model"))
    out = getattr(tasks, fn).run() if hasattr(getattr(tasks, fn), "run") else getattr(tasks, fn)()
    assert out == {"status": "skipped", "reason": f"{flag}=false"}


def test_mac_dinh_bat_de_dev_giu_nguyen():
    for _fn, flag in CASES:
        assert type(settings).model_fields[flag].default is True
    #  Nhắc hạn việc Dự án và chuông KHÔNG bị cờ nào ở đây chặn (đại ca giữ trên prod).
    import inspect

    for keep in ("work_due_task", "forward_bells_task", "fire_reminders_task"):
        src = inspect.getsource(getattr(tasks, keep))
        assert "_flag_off" not in src, keep
