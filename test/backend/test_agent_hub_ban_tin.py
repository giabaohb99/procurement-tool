"""ai-CR-140 — bản tin bật / tắt ngay trong chat: bản tin sáng (lịch, việc riêng, việc Dự án tới hạn, chờ duyệt) và bản
tin chủ đề (câu hỏi bot tự hỏi hộ theo lịch). Người nối Google chưa tự đặt = bật 07:30 như cũ; bot không tự gửi gì người
dùng chưa bật; mỗi ngày một lần; chỉ chủ của bản tin bật / tắt được."""
from datetime import datetime, timedelta

import pytest

from app.modules.agent_hub import brief_subs as bs
from app.modules.agent_hub.timeutil import LOCAL_OFFSET


def _link(db, user_id: int, chat_id: str, notify_mode: int = 1):
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat_id, linked_at=datetime.now(), notify_mode=notify_mode,
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()


def _utc(local: datetime) -> datetime:
    return local - LOCAL_OFFSET


@pytest.fixture
def sent(monkeypatch):
    from app.modules.agent_hub import service

    out: list[tuple[str, str]] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: out.append((chat_id, text)))
    monkeypatch.setattr(bs, "daily_text", lambda db, user: f"BẢN TIN SÁNG của {user.id}")
    asked: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(service, "answer_question", lambda db, chat_id, q, **kw: asked.append((chat_id, q, kw)))
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    out_asked = (out, asked)
    return out_asked


def test_doc_gio_va_thu():
    assert bs.parse_time("lúc 6h45") == (6, 45) and bs.parse_time("07:30") == (7, 30)
    assert bs.parse_time("luc 07 30") == (7, 30) and bs.parse_time("8 giờ") == (8, 0)
    assert bs.parse_time("25h") is None and bs.parse_time("không giờ nào") is None
    assert bs.parse_days(["thứ hai"]) == 1 and bs.parse_days(["T7", "chủ nhật"]) == 32 | 64
    assert bs.parse_days("ngày thường") == 31 and bs.parse_days([]) == bs.ALL_DAYS
    assert bs.days_text(31) == "thứ hai → thứ sáu" and bs.days_text(1 | 4) == "thứ hai, thứ tư"


def test_khong_ai_bat_thi_khong_gui_gi(db, seed, sent):
    out, asked = sent
    _link(db, seed.u_req_id, "777")
    monday_0730 = datetime(2026, 10, 12, 7, 31)
    assert bs.tick(db, now=_utc(monday_0730)) == {"sent": 0, "failed": 0} and out == [] and asked == []


def test_nguoi_noi_google_chua_dat_thi_van_nhan_0730_nhu_cu_va_tat_duoc(db, seed, sent):
    from app.modules.agent_hub.model import AgentGoogleLink

    out, _ = sent
    uid = seed.u_req_id
    _link(db, uid, "777")
    db.add(AgentGoogleLink(user_id=uid, email="a@x", created_by=0, updated_by=0))
    db.commit()
    day = datetime(2026, 10, 12, 7, 0)
    assert bs.tick(db, now=_utc(day))["sent"] == 0                         # chưa tới 07:30
    assert bs.tick(db, now=_utc(day + timedelta(minutes=31)))["sent"] == 1
    assert out == [("777", f"BẢN TIN SÁNG của {uid}")]
    assert bs.tick(db, now=_utc(day + timedelta(minutes=50)))["sent"] == 0  # mỗi ngày một lần
    bs.set_daily(db, uid, enabled=False)
    assert bs.tick(db, now=_utc(day + timedelta(days=1, minutes=31)))["sent"] == 0
    #  Chuông chat tắt: bản tin NGẦM theo luật cũ không gửi (người tự bật thì vẫn gửi).
    from app.modules.agent_hub.model import AgentBriefSub

    db.query(AgentBriefSub).delete()
    db.commit()
    from app.modules.agent_hub.model import AgentChatLink

    db.query(AgentChatLink).update({"notify_mode": 0})
    db.commit()
    assert bs.tick(db, now=_utc(day + timedelta(days=2, minutes=31)))["sent"] == 0


def test_bat_tat_doi_gio_bang_lenh_chat(db, seed, sent, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    out, _ = sent
    uid = seed.u_req_id
    _link(db, uid, "777")

    def say(text):
        row = service.log_message(db, DIR_IN, "777", 1, text)
        return service._brief_by_text(db, "777", row, text)

    assert say("Bật bản tin lúc 6h45 ngày thường")
    st = bs.daily_state(db, uid)
    assert st["enabled"] and (st["hour"], st["minute"], st["days"]) == (6, 45, 31) and "06:45" in out[-1][1]
    saturday = datetime(2026, 10, 17, 6, 50)
    assert bs.tick(db, now=_utc(saturday))["sent"] == 0                   # thứ bảy không thuộc ngày thường
    assert bs.tick(db, now=_utc(saturday + timedelta(days=2)))["sent"] == 1
    #  Quá cửa sổ 3 giờ (máy chết cả sáng) thì thôi, không gửi bản tin sáng lúc chiều.
    assert bs.tick(db, now=_utc(datetime(2026, 10, 20, 10, 0)))["sent"] == 0
    assert say("bản tin lúc 07:15") and bs.daily_state(db, uid)["minute"] == 15
    assert say("tắt bản tin") and not bs.daily_state(db, uid)["enabled"]
    assert say("bản tin của tôi?") and "đang tắt" in out[-1][1]
    assert say("bản tin hôm nay") and out[-1] == ("777", f"BẢN TIN SÁNG của {uid}")    # gửi ngay, kể cả khi đang tắt
    assert say("bản tin lúc trưa") and "chưa đọc được giờ" in out[-1][1]
    assert not say("bản tin thị trường thép tuần này thế nào")                 # câu hỏi thường → Trợ lý


def test_ban_tin_chu_de_hoi_ho_theo_lich_khong_dem_vao_thoi_quen(db, seed, sent):
    out, asked = sent
    uid = seed.u_req_id
    _link(db, uid, "777")
    row = bs.add_topic(db, uid, "công nợ quá hạn của DEGO", hour=8, minute=0, days=bs.day_bit(0), sub_code="tra_cuu.cong_no")
    monday = datetime(2026, 10, 12, 8, 2)
    assert bs.tick(db, now=_utc(monday))["sent"] == 1
    assert asked == [("777", "công nợ quá hạn của DEGO", {"intent": "hoi", "ledger": False})]
    assert "Bản tin:" in out[-1][1]
    assert bs.tick(db, now=_utc(monday + timedelta(days=1)))["sent"] == 0       # thứ ba: không
    assert bs.set_enabled(db, uid, row.id, False)
    assert bs.tick(db, now=_utc(monday + timedelta(days=7)))["sent"] == 0
    with pytest.raises(ValueError, match="mật khẩu"):
        bs.add_topic(db, uid, "mật khẩu email của anh là gì")
    with pytest.raises(ValueError):
        bs.add_topic(db, uid, "   ")


def test_chi_chu_ban_tin_bat_tat_duoc_va_tool_khong_chon_duoc_nguoi_khac(db, seed):
    from types import SimpleNamespace

    from app.modules.assistant.tools.base import ToolContext
    from app.modules.assistant.tools.brief_tool import MANAGE_BRIEFS_SPEC

    a, b = seed.u_req_id, seed.u_nstm_id
    row_b = bs.add_topic(db, b, "báo cáo mua hàng tuần")
    assert not bs.set_enabled(db, a, row_b.id, False) and not bs.remove(db, a, row_b.id)
    ctx = ToolContext(db=db, user=SimpleNamespace(id=a))
    out = MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "disable", "id": row_b.id})
    assert "error" in out and db.get(type(row_b), row_b.id).enabled is True
    out = MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "add_topic", "question": "công nợ quá hạn", "time": "8h",
                                           "days": ["thứ hai"]})
    mine = [x for x in out["briefs"] if x["kind"] == bs.Kind.TOPIC]
    assert len(mine) == 1 and mine[0]["hour"] == 8 and mine[0]["days"] == 1 and "thứ hai" in mine[0]["when"]
    assert all(x["topic"] != "báo cáo mua hàng tuần" for x in out["briefs"])
    assert "error" in MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "enable_daily", "time": "trưa"})


def test_thu_hoi_tai_khoan_bo_ban_tin(db, seed):
    from app.modules.agent_hub.model import AgentBriefSub
    from app.modules.agent_hub.service import revoke_user_access

    bs.add_topic(db, seed.u_req_id, "công nợ")
    bs.set_daily(db, seed.u_req_id, enabled=True)
    bs.add_topic(db, seed.u_nstm_id, "đơn hàng")
    revoke_user_access(db, seed.u_req_id)
    db.commit()
    assert db.query(AgentBriefSub).filter_by(user_id=seed.u_req_id).count() == 0
    assert db.query(AgentBriefSub).filter_by(user_id=seed.u_nstm_id).count() == 1


def test_viec_du_an_toi_han_cua_toi(db, seed):
    """Tool `my_work_tasks`: chỉ việc ĐANG MỞ mình phụ trách, hạn tới hôm nay (gồm quá hạn), trong dự án mình thấy."""
    from datetime import date

    from app.modules.assistant.tools.base import ToolContext
    from app.modules.assistant.tools.work_tool import MY_WORK_TASKS_SPEC
    from app.modules.user.model import User
    from app.modules.work.model import WorkList, WorkListMember, WorkTaskStatus
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    user = db.get(User, seed.u_req_id)
    emp = user.employee_id
    lst = WorkList(name="Dự án A", company_id=0)
    other = WorkList(name="Dự án người khác", company_id=0)
    db.add_all([lst, other])
    db.flush()
    db.add(WorkListMember(list_id=lst.id, employee_id=emp))
    today = date.today()
    rows = [("quá hạn", (today - timedelta(days=2)).isoformat(), lst.id, WorkTaskStatus.OPEN),
            ("hôm nay", today.isoformat(), lst.id, WorkTaskStatus.OPEN),
            ("mai", (today + timedelta(days=1)).isoformat(), lst.id, WorkTaskStatus.OPEN),
            ("xong rồi", today.isoformat(), lst.id, WorkTaskStatus.DONE),
            ("dự án không thấy", today.isoformat(), other.id, WorkTaskStatus.OPEN),
            ("ZZNOIDUNGPHONGKHAC của người khác", today.isoformat(), lst.id, WorkTaskStatus.OPEN)]
    for title, due, list_id, status in rows:
        t = WorkTask(title=title, due_date=due, list_id=list_id, status=int(status))
        db.add(t)
        db.flush()
        #  Việc cùng dự án nhưng người khác phụ trách: không được lọt ra (ca rò rỉ của `test_assistant_pham_vi_doc`).
        db.add(WorkTaskAssignee(task_id=t.id, employee_id=emp + 999 if title.startswith("ZZ") else emp))
    db.commit()
    ctx = ToolContext(db=db, user=user)
    import app.modules.assistant.tools.work_tool as wt

    orig = ctx.can
    ctx.can = lambda entity, action="read": True if entity == "work_task" else orig(entity, action)
    out = MY_WORK_TASKS_SPEC.handler(ctx, {})
    assert [x["title"] for x in out["items"]] == ["quá hạn", "hôm nay"]
    assert "ZZNOIDUNGPHONGKHAC" not in str(out)
    assert out["items"][0]["overdue"] is True and out["items"][1]["overdue"] is False
    assert [x["title"] for x in MY_WORK_TASKS_SPEC.handler(ctx, {"until": (today + timedelta(days=1)).isoformat()})["items"]] \
        == ["quá hạn", "hôm nay", "mai"]
    ctx.can = lambda entity, action="read": False
    assert "error" in MY_WORK_TASKS_SPEC.handler(ctx, {}) or MY_WORK_TASKS_SPEC.handler(ctx, {}).get("denied")
    assert wt is not None
