"""bao-CR-616 (phase 24.1, doc/agent-hub/18) — bot điều phối việc theo kế hoạch, ĐỢT 1 chỉ ghi nhận việc:
tool `draft_work_plan` chuẩn hóa theo bộ luật → «tạo» dựng cả cây trong Dự án (bảng · cột = giai đoạn · việc cha / con,
trường tùy biến Tiêu chí / Nhận việc / Tiến độ / Tự chấm / Ghi nhận, mời người làm vào bảng) → nhắn hỏi từng người nhận
việc (nhân danh chủ kế hoạch) → nút / câu trả lời ghi vào việc và báo chủ → «xong việc N 8 điểm» ghi xong + giờ."""
import json
from datetime import datetime, timedelta

import pytest

from app.modules.agent_hub import draft_create, work_plan
from app.modules.agent_hub.plan_policy import A_UNREACHABLE
from app.modules.work import plan_service
from app.modules.agent_hub.constants import ACT_PLAN_ASK, ACT_PLAN_ASK_WAIT, DIR_IN
from app.modules.agent_hub.model import AgentChatLink, AgentMessage
from app.modules.user.model import User


@pytest.fixture
def world(db, seed, cap_quyen, monkeypatch):
    """Chủ kế hoạch (seed.u_req) + hai người làm: An có Telegram, Bình không. Telegram giả lập, ghi lại tin đã gửi."""
    from app.modules.agent_hub import telegram
    from app.modules.employee.model import Employee

    cap_quyen(seed.u_req_id, "work_task", scope="all", read=True, create=True, write=True)
    boss = db.get(User, seed.u_req_id)
    an = Employee(code="NV-AN", full_name="Trần Văn An", company_id=seed.company_id)
    binh = Employee(code="NV-BINH", full_name="Lê Thị Bình", company_id=seed.company_id)
    db.add_all([an, binh])
    db.flush()
    u_an = User(email="an@test", employee_id=an.id, password_hash="x", is_active=True)
    db.add(u_an)
    db.flush()
    for uid, chat in ((boss.id, "chat-boss"), (u_an.id, "chat-an")):
        db.add(AgentChatLink(user_id=uid, chat_id=chat, linked_at=datetime.now(), notify_mode=1,
                             expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()
    sent: list[tuple[str, str, list | None]] = []
    monkeypatch.setattr(telegram, "send", lambda text, *, buttons=None, chat_id="": (sent.append((chat_id, text, buttons)) or 1))
    monkeypatch.setattr(telegram, "answer_callback", lambda cb_id, text="": None)
    monkeypatch.setattr(telegram, "clear_buttons", lambda chat_id, mid: None)
    return {"boss": boss, "an": an, "binh": binh, "u_an": u_an, "sent": sent}


def _args():
    return {"title": "Tiếp khách Trung Quốc 14/10", "deadline": "2026-10-16", "refined": True, "phases": [
        {"name": "Chuẩn bị", "tasks": [
            {"title": "Tạm ứng chi phí", "assignees": ["NV-AN"], "start_date": "2026-10-13", "due_date": "2026-10-13",
             "priority": "gấp", "criteria": ["Tiền tới tay trước 7:30"],
             "subtasks": [{"title": "Lập đề nghị tạm ứng", "assignees": ["NV-AN"], "due_date": "2026-10-13"},
                          {"title": "Chuyển tiền", "assignees": ["NV-AN"], "due_date": "2026-10-13"}]},
            {"title": "Xe đưa đón", "assignees": ["Lê Thị Bình"], "due_date": "2026-10-13", "priority": "cao",
             "subtasks": [{"title": f"Việc con {i}"} for i in range(1, 10)]},
        ]},
        {"name": "Ngày tiếp khách", "tasks": [
            {"title": "Ghi chép nhu cầu khách", "assignees": [], "start_date": "2026-10-18", "due_date": "2026-10-14"},
        ]},
    ]}


def _draft(db, user, args):
    from app.modules.assistant import tools as T

    return T.run_tool(db, user, "draft_work_plan", args)


def test_tool_chuan_hoa_theo_luat_va_ghi_gia_dinh(db, world):
    out = _draft(db, world["boss"], _args())
    d = out["draft"]
    assert d["counts"] == {"phases": 2, "tasks": 3, "subtasks": 2 + 7}
    t1, t2 = d["phases"][0]["tasks"]
    assert t1["priority"] == "Gấp" and t2["priority"] == "Ưu tiên"
    assert t1["assignees"][0]["code"] == "NV-AN" and t2["assignees"][0]["name"] == "Lê Thị Bình"
    #  Việc con quá 7 → cắt còn 7, ghi giả định; thiếu tiêu chí → tiêu chí mặc định; hạn trước ngày bắt đầu → đảo.
    assert len(t2["subtasks"]) == 7 and any("quá nhiều việc con" in a and "9 → 7" in a for a in d["assumptions"])
    assert t2["criteria"] == ["Hoàn thành đúng hạn và được người giao xác nhận"]
    #  Giả định gom theo nhóm: 10 việc thiếu tiêu chí vẫn chỉ một dòng, kể 3 tên đầu.
    crit = next(a for a in d["assumptions"] if "tiêu chí mặc định" in a)
    assert "«Xe đưa đón»" in crit and "việc nữa" in crit and len(d["assumptions"]) <= 8
    t3 = d["phases"][1]["tasks"][0]
    assert (t3["start_date"], t3["due_date"]) == ("2026-10-14", "2026-10-18")
    assert any("chưa giao ai" in a for a in d["assumptions"]) and any("đảo lại" in a for a in d["assumptions"])
    #  Thẻ nháp đọc được.
    lines = draft_create.summarize("work_plan", d)
    assert lines[0].startswith("Kế hoạch:") and "2 giai đoạn" in lines[1]


def test_tool_hoi_lai_khi_nguoi_mo_ho_hoac_thieu_giai_doan(db, world):
    from app.modules.employee.model import Employee

    db.add(Employee(code="NV-AN2", full_name="Trần Văn An", company_id=world["an"].company_id))
    db.commit()
    args = _args()
    args["phases"][0]["tasks"][0]["assignees"] = ["Trần Văn An"]
    out = _draft(db, world["boss"], args)
    assert out["need_choice"] == "assignee" and "khớp nhiều người" in out["problems"][0]
    assert "need_info" in _draft(db, world["boss"], {"title": "X", "phases": []})


def test_chep_cau_nguoi_dung_thi_bat_soan_lai_co_viec_con_va_tieu_chi(db, world):
    """Thử dev 13/10: sếp gõ 3 dòng, bot chép y nguyên (0 việc con, tiêu chí mặc định). Sếp muốn bot TỰ chia bước và TỰ
    đặt tiêu chí → tool trả need_refine kể tên việc thiếu; gọi lại refined=true thì mới ra nháp. Thẻ nháp in việc con
    + tiêu chí để sếp duyệt phần bot nghĩ ra."""
    flat = {"title": "Thử bot điều phối", "deadline": "2026-10-15", "phases": [{"name": "Thực hiện", "tasks": [
        {"title": "Gửi báo giá máy in cho phòng kế toán", "assignees": ["NV-AN"], "due_date": "2026-10-14", "priority": "gấp"},
        {"title": "Dọn kho tài liệu tầng 2", "assignees": ["NV-AN"], "due_date": "2026-10-15", "criteria": ["kho trống kệ số 3"]},
    ]}]}
    out = _draft(db, world["boss"], flat)
    assert "draft" not in out and len(out["need_refine"]) == 2
    assert "«Gửi báo giá máy in cho phòng kế toán»: mới 0 việc con, chưa có tiêu chí" in out["need_refine"]
    assert "«Dọn kho tài liệu tầng 2»: mới 0 việc con" == out["need_refine"][1]       # tiêu chí người dùng đã có
    assert "refined=true" in out["note"] and "không hỏi người dùng" in out["note"]
    #  Trợ lý gọi lại đủ việc con + tiêu chí.
    flat["refined"] = True
    t1, t2 = flat["phases"][0]["tasks"]
    t1["criteria"] = ["Kế toán nhận được báo giá qua email trước 16:00 14/10"]
    t1["subtasks"] = [{"title": "Xin báo giá 2 hãng", "assignees": ["NV-AN"], "due_date": "2026-10-13",
                       "criteria": ["Có 2 báo giá PDF"]},
                      {"title": "Gửi email cho kế toán", "assignees": ["NV-AN"], "due_date": "2026-10-14"}]
    t2["subtasks"] = [{"title": "Phân loại hồ sơ"}, {"title": "Chuyển hồ sơ cũ xuống kho lưu"}]
    out = _draft(db, world["boss"], flat)
    d = out["draft"]
    assert d["counts"] == {"phases": 1, "tasks": 2, "subtasks": 4}
    assert all("_own_criteria" not in t for t in d["phases"][0]["tasks"])
    lines = work_plan.summary_lines(d)
    assert "    + Xin báo giá 2 hãng · 13/10" in lines and "    + Phân loại hồ sơ" in lines
    assert any(l.startswith("    Tiêu chí: Kế toán nhận được báo giá") for l in lines)
    assert any(l.startswith("    Tiêu chí: kho trống kệ số 3") for l in lines)
    #  Vẫn thiếu sau khi soạn lại thì không bắt vòng nữa — ra nháp, ghi giả định.
    t2["subtasks"] = []
    out = _draft(db, world["boss"], flat)
    assert "draft" in out and out["draft"]["counts"]["subtasks"] == 2


def test_tao_dung_ca_cay_trong_du_an(db, world):
    from app.modules.work.label_model import WorkLabelField
    from app.modules.work.model import WorkList, WorkListMember
    from app.modules.work.task_model import WorkSection, WorkTask, WorkTaskAssignee

    d = _draft(db, world["boss"], _args())["draft"]
    code, list_id = draft_create.create(db, world["boss"], "work_plan", d)
    lst = db.get(WorkList, list_id)
    assert code == f"kế hoạch #{list_id}" and lst.name == "Tiếp khách Trung Quốc 14/10"
    assert plan_service.PLAN_MARK in lst.description and "Hạn chót: 2026-10-16" in lst.description
    #  Cột = giai đoạn (ba cột mặc định đổi tên / bỏ bớt).
    sections = db.query(WorkSection).filter(WorkSection.list_id == list_id).order_by(WorkSection.sort_order).all()
    assert [s.name for s in sections] == ["Chuẩn bị", "Ngày tiếp khách"]
    tasks = db.query(WorkTask).filter(WorkTask.list_id == list_id).all()
    parents = [t for t in tasks if t.parent_id is None]
    assert len(parents) == 3 and len(tasks) == 3 + 9
    xe = next(t for t in parents if t.title == "Xe đưa đón")
    assert xe.section_id == sections[0].id and len([t for t in tasks if t.parent_id == xe.id]) == 7
    #  Người làm được mời vào bảng; chủ là OWNER.
    members = {m.employee_id: m.role for m in db.query(WorkListMember).filter(WorkListMember.list_id == list_id)}
    assert members[world["an"].id] == 3 and members[world["binh"].id] == 3 and members[world["boss"].employee_id] == 1
    assert {a.employee_id for a in db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id == xe.id)} == {world["binh"].id}
    #  Trường tùy biến + giá trị.
    fields = {f.name: f for f in db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id)}
    assert {plan_service.FIELD_ACCEPT, plan_service.FIELD_CRITERIA, plan_service.FIELD_PROGRESS, plan_service.FIELD_SCORE,
            plan_service.FIELD_NOTE} <= set(fields)
    tam_ung = next(t for t in parents if t.title == "Tạm ứng chi phí")
    assert plan_service._label_text(db, fields[plan_service.FIELD_CRITERIA], tam_ung.id) == "Tiền tới tay trước 7:30"
    assert plan_service._label_text(db, fields[plan_service.FIELD_ACCEPT], tam_ung.id) == plan_service.ACCEPT_NOT_ASKED
    pr = next(f for f in fields.values() if f.system_key == "priority")
    assert plan_service._label_text(db, pr, tam_ung.id).startswith("P1") and plan_service._label_text(db, pr, xe.id).startswith("P2")
    assert "3 việc cha, 9 việc con" in " ".join(draft_create.created_details(db, "work_plan", list_id))


def test_hoi_nhan_viec_nguoi_co_telegram_va_danh_dau_nguoi_khong(db, world):
    from app.modules.work.label_model import WorkLabelField
    from app.modules.work.task_model import WorkTask

    d = _draft(db, world["boss"], _args())["draft"]
    _, list_id = draft_create.create(db, world["boss"], "work_plan", d)
    out = work_plan.ask_assignees(db, world["boss"], list_id)
    assert out["asked"] == ["Trần Văn An"] and out["unreachable"] == ["Lê Thị Bình"] and out["tasks"] == 3
    asks = [s for s in world["sent"] if s[0] == "chat-an"]
    assert len(asks) == 3 and all(len(b) == 3 and b[0][1].startswith("kh_ok:") for _, _, b in asks)
    assert "của Người YC" in asks[0][1] or "Theo kế hoạch" in asks[0][1]
    assert db.query(AgentMessage).filter(AgentMessage.action == ACT_PLAN_ASK, AgentMessage.chat_id == "chat-an").count() == 3
    xe = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Xe đưa đón").one()
    accept = db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id, WorkLabelField.name == plan_service.FIELD_ACCEPT).one()
    assert plan_service._label_text(db, accept, xe.id) == plan_service.ACCEPT_UNREACHABLE
    assert "Lê Thị Bình" in work_plan.ask_summary_text(out) and "Nhắn không được" in work_plan.ask_summary_text(out)


def _incoming(db, chat_id, text):
    row = AgentMessage(task_id=0, direction=DIR_IN, chat_id=chat_id, tg_message_id=0, body=text, action="")
    db.add(row)
    db.commit()
    return row


def test_nguoi_lam_bam_nut_va_nhan_xong_viec(db, world):
    from app.modules.work.label_model import WorkLabelField
    from app.modules.work.model import WorkTaskStatus
    from app.modules.work.task_model import WorkTask

    d = _draft(db, world["boss"], _args())["draft"]
    _, list_id = draft_create.create(db, world["boss"], "work_plan", d)
    work_plan.ask_assignees(db, world["boss"], list_id)
    tam_ung = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Tạm ứng chi phí").one()
    con = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Chuyển tiền").one()
    fields = {f.name: f for f in db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id)}
    world["sent"].clear()
    #  Nhận → ghi «Nhận», báo chủ kế hoạch (chat-boss), trả lời An.
    work_plan.handle_callback(db, "chat-an", "cb1", work_plan.CB_YES, tam_ung.id)
    assert plan_service._label_text(db, fields[plan_service.FIELD_ACCEPT], tam_ung.id) == plan_service.ACCEPT_YES
    assert [s[0] for s in world["sent"]] == ["chat-an", "chat-boss"] and "đã <b>nhận</b>" in world["sent"][1][1]
    #  Từ chối → chờ lý do; câu kế tiếp thành Ghi nhận và báo chủ.
    world["sent"].clear()
    work_plan.handle_callback(db, "chat-an", "cb2", work_plan.CB_NO, con.id)
    assert db.query(AgentMessage).filter(AgentMessage.action == ACT_PLAN_ASK_WAIT).count() == 1
    row = _incoming(db, "chat-an", "Em bận đi công tác, nhờ chị Bình chuyển giúp")
    assert work_plan.handle_text(db, "chat-an", row, row.body) is True
    assert plan_service._label_text(db, fields[plan_service.FIELD_NOTE], con.id).startswith("Từ chối: Em bận")
    assert any(s[0] == "chat-boss" and "Từ chối" in s[1] for s in world["sent"])
    #  Người lạ bấm nút việc không phải của mình → không ghi gì.
    world["sent"].clear()
    work_plan.handle_callback(db, "chat-boss", "cb3", work_plan.CB_YES, con.id)
    assert plan_service._label_text(db, fields[plan_service.FIELD_ACCEPT], con.id) == plan_service.ACCEPT_NO and not world["sent"]
    #  «xong việc N 8 điểm» → trạng thái xong, tiến độ 100, tự chấm 8, có giờ; báo chủ.
    row = _incoming(db, "chat-an", f"xong việc {tam_ung.id} 8 điểm, tiền đã chuyển")
    assert work_plan.handle_text(db, "chat-an", row, row.body) is True
    db.refresh(tam_ung)
    assert tam_ung.status == int(WorkTaskStatus.DONE) and tam_ung.completed_at is not None
    assert plan_service._label_text(db, fields[plan_service.FIELD_PROGRESS], tam_ung.id) == "100"
    assert plan_service._label_text(db, fields[plan_service.FIELD_SCORE], tam_ung.id) == "8"
    assert any(s[0] == "chat-boss" and "<b>xong</b>" in s[1] for s in world["sent"])
    #  Tiến độ giữa chừng: «việc N 60% 7 điểm».
    row = _incoming(db, "chat-an", f"việc {con.id} 60% 7 điểm còn chờ kế toán")
    assert work_plan.handle_text(db, "chat-an", row, row.body) is True
    assert plan_service._label_text(db, fields[plan_service.FIELD_PROGRESS], con.id) == "60"
    #  Câu không liên quan → không bắt.
    row = _incoming(db, "chat-an", "hôm nay trời đẹp")
    assert work_plan.handle_text(db, "chat-an", row, row.body) is False


def test_luat_lap_ke_hoach_doc_tu_cau_hinh_json_va_chiu_json_hong(db, monkeypatch):
    from app.core import app_settings
    from app.modules.agent_hub import plan_policy

    monkeypatch.setattr(app_settings, "get", lambda key: '{"max_subtasks": 3, "default_priority": "Ưu tiên", "la": 1}')
    p = plan_policy.current()
    assert p["max_subtasks"] == 3 and p["default_priority"] == "Ưu tiên" and "la" not in p
    monkeypatch.setattr(app_settings, "get", lambda key: "không phải json")
    assert plan_policy.current()["max_subtasks"] == plan_policy.DEFAULTS["max_subtasks"]
    monkeypatch.setattr(app_settings, "get", lambda key: json.dumps({"default_priority": "Sai"}))
    assert plan_policy.current()["default_priority"] == plan_policy.DEFAULTS["default_priority"]



# ---------------------------------------------------------------------------------------------------------------
#  Chế độ DỊCH VỤ TÁCH (phase S): bot không đọc bảng Dự án — mọi lượt đi qua cổng B có chữ ký. Lỗi lần lên dev đầu
#  13/10: bản đầu đọc thẳng bảng Dự án từ dịch vụ AI (DB riêng) → hỏng; bài này canh để không tái diễn.
# ---------------------------------------------------------------------------------------------------------------
@pytest.fixture
def gateway(db, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.core.database import get_db
    from app.modules.agent_gateway.controller import router as gw_router
    from app.modules.agent_hub import erp

    gw = FastAPI()
    gw.include_router(gw_router)
    gw.dependency_overrides[get_db] = lambda: db
    client = TestClient(gw)
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "khoa-ky-thu-nghiem")
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(erp, "_remote", None)
    calls: list[tuple[str, str]] = []

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, **kw):
        path = url.replace("http://erp.test", "")
        calls.append((method, path))
        return client.request(method, path, params=params, content=data, headers=headers)

    monkeypatch.setattr(erp.requests, "request", fake_request)
    erp._impl()._tool_defs = (0.0, [])
    yield calls
    monkeypatch.setattr(erp, "_remote", None)


def test_che_do_dich_vu_tach_moi_luot_di_qua_cong_b(db, world, gateway):
    from app.modules.agent_hub import erp
    from app.modules.work.label_model import WorkLabelField
    from app.modules.work.model import WorkTaskStatus
    from app.modules.work.task_model import WorkTask

    #  Dựng kế hoạch ở phía ERP (như cổng /draft/create làm), rồi mọi việc còn lại chạy ở «dịch vụ AI».
    d = _draft(db, world["boss"], _args())["draft"]
    _, list_id = draft_create.create(db, world["boss"], "work_plan", d)
    boss = erp.user_by_id(db, world["boss"].id)          # ErpUser qua cổng, không phải ORM
    assert isinstance(boss, erp.ErpUser)
    out = work_plan.ask_assignees(db, boss, list_id)
    assert out["asked"] == ["Trần Văn An"] and out["unreachable"] == ["Lê Thị Bình"]
    assert ("GET", "/api/agent-gw/plan/overview") in gateway
    assert sum(1 for m, p in gateway if p == "/api/agent-gw/plan/reply") == 1      # Bình: đánh dấu Nhắn không được
    fields = {f.name: f for f in db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id)}
    xe = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Xe đưa đón").one()
    assert plan_service._label_text(db, fields[plan_service.FIELD_ACCEPT], xe.id) == plan_service.ACCEPT_UNREACHABLE
    an = erp.user_by_id(db, world["u_an"].id)
    #  Nút Nhận + «xong việc» của An đi qua POST /plan/reply, ghi đúng vào việc, báo chủ.
    tam_ung = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Tạm ứng chi phí").one()
    world["sent"].clear()
    work_plan.handle_callback(db, "chat-an", "cb1", work_plan.CB_YES, tam_ung.id)
    assert plan_service._label_text(db, fields[plan_service.FIELD_ACCEPT], tam_ung.id) == plan_service.ACCEPT_YES
    assert [s[0] for s in world["sent"]] == ["chat-an", "chat-boss"]
    row = _incoming(db, "chat-an", f"xong việc {tam_ung.id} 9 điểm")
    assert work_plan.handle_text(db, "chat-an", row, row.body) is True
    db.expire_all()
    assert db.get(WorkTask, tam_ung.id).status == int(WorkTaskStatus.DONE)
    assert plan_service._label_text(db, fields[plan_service.FIELD_SCORE], tam_ung.id) == "9"
    assert sum(1 for m, p in gateway if p == "/api/agent-gw/plan/reply") == 3
    #  Không phải chủ bảng thì không đánh dấu «Nhắn không được» được qua cổng.
    assert erp.plan_reply(db, an, xe.id, A_UNREACHABLE).get("error")
