"""ai-CR-175 (T-14) — trợ lý cá nhân với việc Dự án: `my_work_tasks` gom theo dự án / lọc một dự án / việc của cả dự án;
vòng nhắc hạn ba mốc (trước 1 ngày · ngày hạn · quá hạn) cho đúng người được giao, mỗi mốc một lần, 08:00, tắt / đổi giờ
bằng câu nhắn; bản tin sáng gom việc theo dự án."""
from datetime import date, datetime, timedelta

import pytest

from app.modules.agent_hub import work_due as wd
from app.modules.agent_hub.timeutil import LOCAL_OFFSET


def _utc(local: datetime) -> datetime:
    return local - LOCAL_OFFSET


def _link(db, user_id: int, chat_id: str, notify_mode: int = 1):
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat_id, linked_at=datetime.now(), notify_mode=notify_mode,
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()


def _work(db, emp: int):
    """Hai dự án mình là thành viên + một dự án không thấy; việc của mình và của người khác."""
    from app.modules.work.model import WorkList, WorkListMember, WorkTaskStatus
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    a, b, other = WorkList(name="Dự án Alpha", company_id=0), WorkList(name="Dự án Beta", company_id=0), \
        WorkList(name="Dự án kín", company_id=0)
    db.add_all([a, b, other])
    db.flush()
    db.add_all([WorkListMember(list_id=a.id, employee_id=emp), WorkListMember(list_id=b.id, employee_id=emp)])
    today = date.today()
    rows = [("A quá hạn", (today - timedelta(days=2)).isoformat(), a.id, emp),
            ("A hôm nay", today.isoformat(), a.id, emp),
            ("B mai", (today + timedelta(days=1)).isoformat(), b.id, emp),
            ("B chưa hạn", "", b.id, emp),
            ("B của người khác", today.isoformat(), b.id, emp + 999),
            ("kín", today.isoformat(), other.id, emp)]
    for title, due, list_id, who in rows:
        t = WorkTask(title=title, due_date=due, list_id=list_id, status=int(WorkTaskStatus.OPEN))
        db.add(t)
        db.flush()
        db.add(WorkTaskAssignee(task_id=t.id, employee_id=who))
    db.commit()


def _ctx(db, seed):
    from app.modules.assistant.tools.base import ToolContext
    from app.modules.user.model import User

    user = db.get(User, seed.u_req_id)
    ctx = ToolContext(db=db, user=user)
    orig = ctx.can
    ctx.can = lambda entity, action="read": True if entity == "work_task" else orig(entity, action)
    return ctx, user


def test_my_work_tasks_gom_theo_du_an_loc_mot_du_an_va_viec_ca_du_an(db, seed):
    from app.modules.assistant.tools.work_tool import MY_WORK_TASKS_SPEC

    ctx, user = _ctx(db, seed)
    _work(db, user.employee_id)
    out = MY_WORK_TASKS_SPEC.handler(ctx, {"until": (date.today() + timedelta(days=1)).isoformat()})
    assert [x["title"] for x in out["items"]] == ["A quá hạn", "A hôm nay", "B mai"]
    assert [(g["project"], g["count"]) for g in out["by_project"]] == [("Dự án Alpha", 2), ("Dự án Beta", 1)]
    #  Một dự án, mọi việc đang mở của CẢ dự án (kể cả chưa hạn), kèm người phụ trách; dự án không thấy thì không.
    out = MY_WORK_TASKS_SPEC.handler(ctx, {"project": "beta", "all_open": True, "only_mine": False})
    assert out["project"] == "Dự án Beta" and [x["title"] for x in out["items"]] == ["B của người khác", "B mai", "B chưa hạn"]
    assert all("assignees" in x for x in out["items"]) and out["items"][1]["assignees"]
    assert "error" in MY_WORK_TASKS_SPEC.handler(ctx, {"project": "kín", "all_open": True})
    assert MY_WORK_TASKS_SPEC.handler(ctx, {"project": "dự án", "all_open": True})["need_choice"] == "project"
    #  Chỉ của mình trong một dự án, không giới hạn hạn.
    out = MY_WORK_TASKS_SPEC.handler(ctx, {"project": "alpha", "all_open": True})
    assert [x["title"] for x in out["items"]] == ["A quá hạn", "A hôm nay"] and "assignees" not in out["items"][0]


def test_phan_moc_va_soan_tin():
    today = date(2026, 10, 12)
    items = [{"id": 1, "title": "mai", "project": "P", "due_date": "2026-10-13"},
             {"id": 2, "title": "hôm nay", "project": "P", "due_date": "2026-10-12"},
             {"id": 3, "title": "trễ", "project": "Q", "due_date": "2026-10-09"},
             {"id": 4, "title": "xa", "project": "Q", "due_date": "2026-10-20"},
             {"id": 5, "title": "không hạn", "project": "Q", "due_date": ""}]
    groups = wd.classify(items, today)
    assert [x["id"] for x in groups[wd.Milestone.BEFORE]] == [1]
    assert [x["id"] for x in groups[wd.Milestone.TODAY]] == [2]
    assert [x["id"] for x in groups[wd.Milestone.OVERDUE]] == [3]
    text, marks = wd.compose(groups, today)
    assert "Hạn ngày mai" in text and "Hạn hôm nay" in text and "Đã quá hạn" in text and "trễ 3 ngày" in text
    assert marks == "[vh:1:1] [vh:2:2] [vh:3:3]" and "[vh:" not in text
    assert wd.compose({m: [] for m in wd.Milestone}, today) == ("", "")


@pytest.fixture
def env(db, seed, monkeypatch):
    from app.modules.agent_hub import erp, telegram

    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(telegram, "send", lambda text, chat_id="", **kw: sent.append((chat_id, text)) or 1)
    today = date.today()
    items = {"items": [{"id": 11, "title": "Gọi NCC thép", "project": "Alpha", "due_date": (today + timedelta(days=1)).isoformat()},
                       {"id": 12, "title": "Nộp báo cáo", "project": "Alpha", "due_date": today.isoformat()},
                       {"id": 13, "title": "Ký hợp đồng", "project": "Beta", "due_date": (today - timedelta(days=1)).isoformat()}]}
    calls: list[tuple[int, dict]] = []
    monkeypatch.setattr(erp, "run_tool", lambda db, user, name, args: calls.append((user.id, args)) or dict(items))
    return sent, items, calls


def test_vong_nhac_ba_moc_moi_moc_mot_lan_va_dung_gio(db, seed, env):
    from app.modules.agent_hub.constants import ACT_WORK_DUE
    from app.modules.agent_hub.model import AgentMessage

    sent, items, calls = env
    uid = seed.u_req_id
    _link(db, uid, "777")
    _link(db, seed.u_nstm_id, "888", notify_mode=0)          # tắt chuông → không nhắc
    local = datetime.combine(date.today(), datetime.min.time())
    assert wd.tick(db, now=_utc(local.replace(hour=7, minute=55))) == {"sent": 0, "failed": 0}   # chưa tới 08:00
    out = wd.tick(db, now=_utc(local.replace(hour=8, minute=3)))
    assert out == {"sent": 1, "failed": 0} and len(sent) == 1 and sent[0][0] == "777"
    text = sent[0][1]
    assert "Hạn ngày mai" in text and "Gọi NCC thép" in text and "Nộp báo cáo" in text and "Ký hợp đồng" in text
    assert "trễ 1 ngày" in text and "[vh:" not in text
    assert calls[-1][1]["until"] == (date.today() + timedelta(days=1)).isoformat()
    row = db.query(AgentMessage).filter(AgentMessage.action == ACT_WORK_DUE).one()
    assert "[vh:11:1]" in row.body and "[vh:12:2]" in row.body and "[vh:13:3]" in row.body
    #  Cùng ngày chạy lại: không gửi nữa.
    assert wd.tick(db, now=_utc(local.replace(hour=9, minute=0))) == {"sent": 0, "failed": 0} and len(sent) == 1
    #  Hôm sau: việc 11 nay tới hạn hôm nay (mốc mới), 12 đã quá hạn (mốc mới), 13 quá hạn đã nhắc → không lặp.
    tomorrow = local + timedelta(days=1)
    sent.clear()
    assert wd.tick(db, now=_utc(tomorrow.replace(hour=8, minute=1))) == {"sent": 1, "failed": 0}
    text = sent[0][1]
    assert "Gọi NCC thép" in text and "Nộp báo cáo" in text and "Ký hợp đồng" not in text
    #  Ngày thứ ba: chỉ việc 11 vừa quá hạn là mốc mới; ngày thứ tư: mọi mốc đều đã nhắc → không có tin.
    sent.clear()
    assert wd.tick(db, now=_utc((local + timedelta(days=2)).replace(hour=8, minute=1))) == {"sent": 1, "failed": 0}
    assert "Gọi NCC thép" in sent[0][1] and "Nộp báo cáo" not in sent[0][1] and "Ký hợp đồng" not in sent[0][1]
    sent.clear()
    assert wd.tick(db, now=_utc((local + timedelta(days=3)).replace(hour=8, minute=1))) == {"sent": 0, "failed": 0}


def test_tat_doi_gio_va_nhac_ngay_bang_cau_nhan(db, seed, env, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    sent, _items, _calls = env
    replies: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: replies.append(text))
    uid = seed.u_req_id
    _link(db, uid, "777")

    def say(text):
        msg = service.log_message(db, DIR_IN, "777", 1, text)
        db.commit()
        return service._work_due_by_text(db, "777", msg, text)

    assert wd.parse_command("mai họp 9h") is None and wd.parse_command("Tắt nhắc hạn việc!") == {"op": "off"}
    assert say("tắt nhắc hạn việc") and wd.state(db, uid)["enabled"] is False and "đang tắt" in replies[-1]
    local = datetime.combine(date.today(), datetime.min.time())
    assert wd.tick(db, now=_utc(local.replace(hour=8, minute=3))) == {"sent": 0, "failed": 0}
    assert say("nhắc hạn việc lúc 7h15") and wd.state(db, uid)["enabled"] is True
    assert wd.state(db, uid)["hour"] == 7 and wd.state(db, uid)["minute"] == 15 and "07:15" in replies[-1]
    assert say("nhắc hạn việc") and "đang bật" in replies[-1]
    #  «nhắc hạn việc hôm nay»: gửi ngay, bỏ qua dấu đã nhắc, không ghi dấu mới.
    assert say("nhắc hạn việc hôm nay") and len(sent) == 1 and "Việc Dự án" in sent[0][1]
    from app.modules.agent_hub.constants import ACT_WORK_DUE
    from app.modules.agent_hub.model import AgentMessage

    assert "[vh:" not in db.query(AgentMessage).filter(AgentMessage.action == ACT_WORK_DUE).one().body
    #  Chat chưa đăng nhập.
    assert service._work_due_by_text(db, "999", service.log_message(db, DIR_IN, "999", 2, "tắt nhắc hạn việc"), "tắt nhắc hạn việc")
    assert "chưa đăng nhập" in replies[-1]


def test_vong_ban_tin_khong_nhat_dong_nhac_han(db, seed, monkeypatch):
    """Dòng kind=3 nằm chung bảng bản tin nhưng vòng bản tin không được coi nó là bản tin chủ đề."""
    from app.modules.agent_hub import brief_subs as bs

    uid = seed.u_req_id
    _link(db, uid, "777")
    wd.set_state(db, uid, enabled=True, hour=6, minute=0)
    assert [r.kind for _u, r in bs._candidates(db) if r is not None and int(r.user_id) == uid] == []
    assert "Nhắc hạn việc Dự án" in bs.render_list(db, uid)


def test_ban_tin_sang_gom_viec_theo_du_an(db, seed, monkeypatch):
    from app.modules.agent_hub import briefs, erp

    def fake_run_tool(db, user, name, args):
        if name == "my_work_tasks":
            items = [{"title": "A1", "project": "Alpha", "due_date": "2026-10-12", "overdue": False},
                     {"title": "B1", "project": "Beta", "due_date": "2026-10-10", "overdue": True}]
            return {"total": 2, "items": items, "by_project": [{"project": "Alpha", "count": 1, "items": items[:1]},
                                                                 {"project": "Beta", "count": 1, "items": items[1:]}]}
        return {"items": []}

    from app.modules.agent_hub import personal_items

    monkeypatch.setattr(erp, "run_tool", fake_run_tool)
    monkeypatch.setattr(personal_items, "today_digest", lambda db, uid: [])
    from app.modules.user.model import User

    text = briefs.morning_text(db, db.get(User, seed.u_req_id), None)
    assert "<i>Alpha</i>" in text and "<i>Beta</i>" in text and text.index("Alpha") < text.index("A1") < text.index("Beta")
    assert "• B1 (hạn 2026-10-10 · quá hạn)" in text
