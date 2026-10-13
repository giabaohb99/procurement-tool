"""ai-CR-181 (đại ca 13/10) — bot biết CỘT kanban của dự án: nháp việc nhận «trạng thái là todo» = tên cột, không nói thì cột
đầu và ghi vào «em đang hiểu là»; «dự án X có cột nào» trả danh sách cột; mỗi việc trong danh sách có cột đang nằm."""
from app.modules.user.model import User


def _setup(db, seed, cap_quyen):
    from app.modules.employee.model import Employee
    from app.modules.work import list_service, schema
    from app.modules.work.membership_service import Actor

    me = Employee(code="NV-ME", full_name="Nguyễn Văn Chủ", company_id=seed.company_id)
    db.add(me)
    db.flush()
    user = db.get(User, seed.u_req_id)
    user.employee_id = me.id
    db.commit()
    actor = Actor(user_id=user.id, employee_id=me.id, company_id=seed.company_id)
    lst = list_service.create_list(db, actor, schema.ListCreate(name="ERP v2"))
    cap_quyen(seed.u_req_id, "work_task", scope="all", read=True, create=True)
    return db.get(User, seed.u_req_id), lst, list_service.DEFAULT_SECTIONS


def test_nhap_viec_chon_cot_theo_ten_hoac_cot_dau(db, seed, cap_quyen):
    from app.modules.agent_hub import draft_create
    from app.modules.assistant import tools as T
    from app.modules.work.task_model import WorkSection, WorkTask

    user, lst, cols = _setup(db, seed, cap_quyen)
    base = {"title": "Nghiên cứu luồng agent 2 agent", "project": "erp v2", "assignees": ["NV-ME"]}
    #  Không nói cột → cột đầu + ghi vào giả định (có liệt kê các cột để người dùng sửa).
    d = T.run_tool(db, user, "draft_work_task", dict(base))["draft"]
    assert d["section_name"] == cols[0] and any("vào cột" in a and cols[1] in a for a in d["assumptions"])
    #  Nói tên cột không dấu, chữ thường → đúng cột đó; thẻ nháp có dòng Cột.
    want = cols[1]
    from app.modules.assistant.glossary import fold

    d = T.run_tool(db, user, "draft_work_task", dict(base, section=fold(want).upper()))["draft"]
    assert d["section_name"] == want and f"Cột: {want}" in draft_create.summarize("work_task", d)
    assert not any("vào cột" in a for a in d["assumptions"])
    code, tid = draft_create.create(db, user, "work_task", d)
    t = db.get(WorkTask, tid)
    assert db.get(WorkSection, t.section_id).name == want
    #  Cột không có → hỏi lại kèm đúng danh sách cột của dự án.
    out = T.run_tool(db, user, "draft_work_task", dict(base, section="Hoãn lại"))
    assert out["need_choice"] == "section" and out["options"] == list(cols)


def test_hoi_du_an_co_cot_nao_va_viec_co_cot(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.agent_hub import draft_create

    user, lst, cols = _setup(db, seed, cap_quyen)
    d = T.run_tool(db, user, "draft_work_task", {"title": "Việc A", "project": "erp", "assignees": ["NV-ME"],
                                                   "section": cols[1]})["draft"]
    draft_create.create(db, user, "work_task", d)
    out = T.run_tool(db, user, "my_work_tasks", {"project": "erp", "all_open": True})
    assert out["sections"] == list(cols) and out["items"][0]["section"] == cols[1]
    assert "sections" not in T.run_tool(db, user, "my_work_tasks", {"all_open": True})
