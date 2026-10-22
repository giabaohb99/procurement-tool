"""kh-AI1-3 (doc/erp/tai-lieu-ai/22 §5.2) — đề xuất kế hoạch AI chờ duyệt: AI chỉ đề xuất, người quyết.

A1 chốt 22/10: người duyệt là chính người hỏi AI; công tắc `ai_plan_review_enabled` mặc định TẮT (tạo thẳng như
bao-CR-616 nhưng ghi đề xuất trạng thái riêng «Tạo thẳng», không lẫn với lần người thật duyệt); chỉ đổi nhánh
`work_plan` của lớp nháp dùng chung, các loại phiếu khác giữ nguyên hành vi.
"""
import pytest
from pydantic import ValidationError

from app.core.ai_plan_codes import AiPlanStatus
from app.modules.agent_hub import draft_create
from app.modules.ai_plan import controller as C
from app.modules.ai_plan import service as S
from app.modules.ai_plan.model import AiPlanProposal
from app.modules.ai_plan.schema import PlanApproveIn, PlanEditIn, PlanRejectIn
from app.modules.work.task_type_model import WorkTaskType

from test_agent_hub_ke_hoach_viec_cr616 import _args, _draft, world  # noqa: F401 — dùng lại khung dựng bao-CR-616


@pytest.fixture
def review_on(monkeypatch):
    monkeypatch.setattr(S, "review_enabled", lambda: True)


@pytest.fixture
def task_type(db, world):  # noqa: F811
    tt = WorkTaskType(company_id=world["an"].company_id, code="HC", name="Hậu cần", is_active=True)
    db.add(tt)
    db.commit()
    return tt


def _args_with_effort():
    args = _args()
    t = args["phases"][0]["tasks"][0]
    t.update(estimate_hours=2.5, task_type="hậu cần", assignee_reason="Ít việc đang ôm nhất phòng")
    args["phases"][0]["tasks"][1].update(estimate_hours=5000, task_type="không có loại này")
    return args


def _body(resp):
    import json

    return json.loads(resp.body)


def test_tool_soan_nhap_co_gio_loai_viec_ly_do(db, world, task_type):  # noqa: F811
    d = _draft(db, world["boss"], _args_with_effort())["draft"]
    t1, t2 = d["phases"][0]["tasks"]
    assert t1["estimate_hours"] == 2.5 and t1["task_type"] == {"id": task_type.id, "name": "Hậu cần"}
    assert t1["assignee_reason"] == "Ít việc đang ôm nhất phòng"
    assert t2["estimate_hours"] is None and t2["task_type"] is None
    assert any("loại việc không khớp" in a for a in d["assumptions"]) and any("giờ ước lượng" in a for a in d["assumptions"])


def test_cong_tac_tat_tao_thang_va_ghi_de_xuat_rieng(db, world, task_type):  # noqa: F811
    from app.modules.work.task_model import WorkTask

    d = _draft(db, world["boss"], _args_with_effort())["draft"]
    code, list_id = draft_create.create(db, world["boss"], "work_plan", d)
    assert code == f"kế hoạch #{list_id}"                                     # hành vi bao-CR-616 giữ nguyên
    row = db.query(AiPlanProposal).one()
    assert row.status == AiPlanStatus.DIRECT and row.list_id == list_id and row.owner_user_id == world["boss"].id
    assert row.plan_ai["phases"][0]["tasks"][0]["key"] == "p1t1"
    assert row.plan_ai["phases"][0]["tasks"][0]["subtasks"][1]["key"] == "p1t1s2"
    t = db.query(WorkTask).filter(WorkTask.list_id == list_id, WorkTask.title == "Tạm ứng chi phí").one()
    assert t.task_type_id == task_type.id and float(t.estimate_hours) == 2.5          # đi tới tận việc thật


def test_cong_tac_bat_chi_luu_cho_duyet_chua_tao_viec(db, world, review_on):  # noqa: F811
    from app.modules.work.model import WorkList

    d = _draft(db, world["boss"], _args())["draft"]
    with pytest.raises(draft_create.DraftError) as e:
        draft_create.create(db, world["boss"], "work_plan", d)
    row = db.query(AiPlanProposal).one()
    assert row.status == AiPlanStatus.PENDING and f"#{row.id}" in str(e.value) and f"/project/ai-plans/{row.id}" in str(e.value)
    assert "CHƯA tạo việc" in str(e.value) and db.query(WorkList).count() == 0


def test_cong_tac_bat_khong_doi_loai_phieu_khac(db, world, review_on, monkeypatch):  # noqa: F811
    """A1 22/10: chỉ nhánh work_plan đổi — loại khác không bao giờ đi qua bước giữ đề xuất."""
    def boom(*a, **kw):
        raise AssertionError("loại phiếu khác không được đi qua bước giữ đề xuất kế hoạch")

    monkeypatch.setattr(draft_create, "_hold_plan_for_review", boom)
    monkeypatch.setattr(draft_create, "_create_work_task", lambda db, user, draft: ("VIEC-1", 1))
    assert draft_create.create(db, world["boss"], "work_task", {"title": "Gọi khách"}) == ("VIEC-1", 1)
    assert db.query(AiPlanProposal).count() == 0


def _pending(db, world):  # noqa: F811
    d = _draft(db, world["boss"], _args())["draft"]
    row = S.record(db, world["boss"], d, status=AiPlanStatus.PENDING)
    db.commit()
    return row


def test_api_chi_chu_de_xuat_thay_nguoi_khac_404(db, world):  # noqa: F811
    from fastapi import HTTPException

    row = _pending(db, world)
    out = _body(C.list_ai_plans(status=None, page=1, page_size=20, db=db, user=world["boss"]))["data"]
    assert out["total"] == 1 and out["items"][0]["status_label"] == "Chờ duyệt"
    detail = _body(C.get_ai_plan(row.id, db=db, user=world["boss"]))["data"]
    assert detail["plan"]["phases"][0]["tasks"][0]["key"] == "p1t1" and detail["plan_final"] is None
    msgs = []
    for pid in (row.id, 999_999):
        with pytest.raises(HTTPException) as e:
            C.get_ai_plan(pid, db=db, user=world["u_an"])
        msgs.append((e.value.status_code, e.value.detail))
    assert msgs[0] == msgs[1] == (404, C.NOT_FOUND)
    assert _body(C.list_ai_plans(status=None, page=1, page_size=20, db=db, user=world["u_an"]))["data"]["total"] == 0


def test_sua_roi_duyet_tao_viec_va_ghi_khac_nhau(db, world, task_type):  # noqa: F811
    from fastapi import HTTPException

    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    row = _pending(db, world)
    plan = _body(C.get_ai_plan(row.id, db=db, user=world["boss"]))["data"]["plan"]
    t1 = plan["phases"][0]["tasks"][0]
    t1["assignees"] = [{"employee_id": world["binh"].id}]                     # đổi người
    t1["estimate_hours"] = 3
    t1["task_type"] = {"id": task_type.id}
    plan["phases"][0]["tasks"].append({"title": "Việc người thêm", "assignees": []})   # dòng mới không key
    plan["phases"][1]["tasks"] = []                                           # bỏ cả giai đoạn 2
    saved = _body(C.edit_ai_plan(row.id, PlanEditIn(plan=plan), db=db, user=world["boss"]))["data"]
    new_row = saved["plan_final"]["phases"][0]["tasks"][-1]
    assert new_row["key"] == "n1" and saved["plan_ai"]["phases"][0]["tasks"][0]["assignees"][0]["code"] == "NV-AN"
    out = _body(C.approve_ai_plan(row.id, PlanApproveIn(), db=db, user=world["boss"]))["data"]
    assert out["list_url"] == f"/project/lists/{out['list_id']}"
    db.refresh(row)
    assert row.status == AiPlanStatus.APPROVED and row.decided_by == world["boss"].id
    assert row.diff["assignee_changed"] == 1 and row.diff["hours_changed"] == 1 and row.diff["added"] == 1
    assert row.diff["removed"] == 1
    t = db.query(WorkTask).filter(WorkTask.list_id == row.list_id, WorkTask.title == "Tạm ứng chi phí").one()
    assert t.task_type_id == task_type.id and float(t.estimate_hours) == 3
    assert {a.employee_id for a in db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id == t.id)} == {world["binh"].id}
    with pytest.raises(HTTPException) as e:
        C.approve_ai_plan(row.id, PlanApproveIn(), db=db, user=world["boss"])
    assert e.value.status_code == 409


def test_khuon_sai_tra_422_kem_tung_loi_va_khong_tao_gi(db, world):  # noqa: F811
    from app.modules.employee.model import Employee
    from app.modules.work.model import WorkList

    row = _pending(db, world)
    plan = dict(row.plan_ai)
    bad = {**plan, "phases": [{"name": "A", "tasks": [
        {"title": "X", "assignees": [{"employee_id": 987654}], "due_date": "22/10/2026", "estimate_hours": 0,
         "task_type": {"id": 4242}}]}]}
    resp = C.approve_ai_plan(row.id, PlanApproveIn(plan=bad), db=db, user=world["boss"])
    body = _body(resp)
    assert resp.status_code == 422 and body["error"]["code"] == "PLAN_INVALID"
    problems = body["error"]["details"]["problems"]
    probs = " | ".join(p["message"] for p in problems)
    assert "#987654" in probs and "YYYY-MM-DD" in probs and "999" in probs and "#4242" in probs
    #  Mỗi lỗi chỉ đúng ô để màn duyệt tô (A3 hỏi 22/10).
    assert {(p["phase"], p["task"], p["subtask"], p["field"]) for p in problems} == {
        (0, 0, None, "assignees"), (0, 0, None, "due_date"), (0, 0, None, "estimate_hours"), (0, 0, None, "task_type")}
    db.refresh(row)
    assert row.status == AiPlanStatus.PENDING and db.query(WorkList).count() == 0
    #  Người đã nghỉ việc không được giao.
    db.query(Employee).filter(Employee.id == world["an"].id).update({"status": "resigned"})
    db.commit()
    with pytest.raises(S.PlanInvalid):
        S.normalize(db, row.plan_ai)


def test_tu_choi_va_tran_o_vao(db, world):  # noqa: F811
    from fastapi import HTTPException

    row = _pending(db, world)
    with pytest.raises(ValidationError):
        PlanRejectIn(reason="x" * 501)
    with pytest.raises(ValidationError):
        PlanEditIn(plan={"title": "x" * (S.MAX_PLAN_BYTES + 1)})
    out = _body(C.reject_ai_plan(row.id, PlanRejectIn(reason="Chưa cần"), db=db, user=world["boss"]))["data"]
    assert out["status"] == AiPlanStatus.REJECTED and out["reject_reason"] == "Chưa cần"
    with pytest.raises(HTTPException) as e:
        C.edit_ai_plan(row.id, PlanEditIn(plan=row.plan_ai), db=db, user=world["boss"])
    assert e.value.status_code == 409


def test_plan_context_goi_boi_canh_va_ke_hoach_tuong_tu(db, world, task_type):  # noqa: F811
    from app.modules.assistant import tools as T

    row = _pending(db, world)
    row.diff = {"assignee_changed": 2}
    db.commit()
    out = T.run_tool(db, world["boss"], "plan_context", {"goal": "Tiếp khách Trung Quốc tuần sau"})
    assert any(t["name"] == "Hậu cần" for t in out["task_types"])
    assert out["similar_plans"][0]["id"] == row.id and out["similar_plans"][0]["diff"] == {"assignee_changed": 2}
    assert out["team"].get("denied") is True                                 # chủ không phải trưởng phòng, không khóa 16
    #  Người không có quyền tạo việc Dự án không dùng được; kế hoạch của người khác không lọt sang.
    assert T.run_tool(db, world["u_an"], "plan_context", {"goal": "Tiếp khách Trung Quốc"}).get("denied") is True
