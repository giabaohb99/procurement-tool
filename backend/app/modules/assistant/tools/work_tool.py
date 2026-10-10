"""Tool SOẠN NHÁP VIỆC ở phân hệ Dự án (ai-CR-080) — «lên task» từ câu nói.

Đại ca 05/10/2026 muốn thử «lên task hoặc thông báo, lên lịch». Theo quy định hỏi và làm (sửa = hỏi một lần), tool chỉ
SOẠN NHÁP: tìm dự án theo tên trong các dự án người hỏi THẤY được, tìm người phụ trách theo mã / tên nhân sự, đọc hạn.
Trên Telegram bot tóm tắt rồi chờ «tạo» (`agent_hub/draft_create.py` gọi đúng `work.task_service.create_task` của web),
tạo xong báo CHUÔNG cho người được giao — chuông chuyển tiếp sang Telegram của ai đã nối (P-01).
Mơ hồ (nhiều dự án / nhiều người cùng tên) thì trả lựa chọn để Trợ lý hỏi MỘT câu, không đoán bừa.
"""
from __future__ import annotations

import re

from sqlalchemy import or_

from . import confirm_fields
from .base import ToolContext, ToolSpec, denied

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _visible_lists(ctx: ToolContext) -> list:
    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import WorkList

    actor = resolve_actor(ctx.db, ctx.user)
    if not actor.employee_id:
        return []
    ids = visible_list_ids(ctx.db, actor.employee_id)
    if not ids:
        return []
    return list(ctx.db.query(WorkList).filter(WorkList.id.in_(ids), WorkList.is_archived == 0).order_by(WorkList.name))


def _find_people(ctx: ToolContext, names: list) -> tuple[list[dict], list[str]]:
    """Mỗi tên / mã → đúng một nhân sự đang làm. Trả (người tìm được, câu báo mơ hồ / không thấy)."""
    from app.modules.employee.model import Employee

    found, problems = [], []
    for raw in [str(n).strip() for n in names or [] if str(n).strip()][:10]:
        exact = ctx.db.query(Employee).filter(Employee.code == raw).all()
        rows = exact or ctx.db.query(Employee).filter(
            or_(Employee.full_name.ilike(f"%{raw}%"), Employee.code.ilike(f"%{raw}%"))).limit(6).all()
        rows = [e for e in rows if getattr(e, "is_active", True) is not False]
        if len(rows) == 1:
            found.append({"employee_id": rows[0].id, "name": rows[0].full_name, "code": rows[0].code})
        elif not rows:
            problems.append(f"không thấy nhân sự «{raw}»")
        else:
            problems.append(f"«{raw}» khớp nhiều người: " + "; ".join(f"{e.full_name} ({e.code})" for e in rows[:5]))
    return found, problems


def _draft_work_task(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("work_task", "create"):
        return denied("tạo công việc ở phân hệ Dự án")
    user_text, asked = confirm_fields.take_context(args)
    title = " ".join(str(args.get("title") or "").split())[:500]
    if not title:
        return {"error": "thiếu tên công việc"}
    #  Đại ca 09/10: giao cho ai mà người dùng chưa nói thì hỏi lại một lượt, không mặc định.
    if not [n for n in args.get("assignees") or [] if str(n).strip()] and "assignees" not in asked:
        return confirm_fields.need([{"field": "assignees", "question": "Giao việc này cho ai (hay chính anh/chị)?"}])
    lists = _visible_lists(ctx)
    if not lists:
        return {"error": "Người hỏi chưa là thành viên dự án nào nên không tạo việc được."}
    want = str(args.get("project") or "").strip().lower()
    picked = [w for w in lists if want and want in (w.name or "").lower()] if want else []
    if want and len(picked) != 1:
        options = [w.name for w in (picked or lists)][:8]
        return {"need_choice": "project", "options": options,
                "note": "Hỏi người dùng MỘT câu: việc này vào dự án nào (đưa danh sách đánh số)."}
    if not want:
        if len(lists) != 1:
            return {"need_choice": "project", "options": [w.name for w in lists][:8],
                    "note": "Hỏi người dùng MỘT câu: việc này vào dự án nào (đưa danh sách đánh số, đoán hợp lý nhất đầu)."}
        picked = lists
    lst = picked[0]
    people, problems = _find_people(ctx, args.get("assignees") or [])
    if problems:
        return {"need_choice": "assignee", "problems": problems,
                "note": "Hỏi người dùng MỘT câu để chọn đúng người (đưa lựa chọn đánh số)."}
    due = str(args.get("due_date") or "").strip()
    start = str(args.get("start_date") or "").strip()
    for label, val in (("due_date", due), ("start_date", start)):
        if val and not _DATE.match(val):
            return {"error": f"{label} phải dạng YYYY-MM-DD"}
    no_due = not (due or "due_date" in asked or confirm_fields.mentions(user_text, "han", "deadline"))
    assumptions = ["chưa đặt hạn"] if no_due else []
    draft = {"list_id": lst.id, "list_name": lst.name, "title": title, "assumptions": assumptions,
             "description": str(args.get("description") or "")[:4000], "due_date": due, "start_date": start,
             "assignees": people}
    return {"draft": draft,
            "note": ("Đã soạn nháp. Trên Telegram bot tự gửi bản tóm tắt để người dùng nhắn «tạo»; trên web hãy nói người "
                     "dùng tạo ở màn Dự án hoặc nhắn qua Telegram. Đừng tự báo là đã tạo.")}


DRAFT_WORK_TASK_SPEC = ToolSpec(
    name="draft_work_task",
    description=("SOẠN NHÁP một CÔNG VIỆC ở phân hệ Dự án ('lên task gọi NCC X cho anh Được hạn thứ 6', 'giao việc …', 'tạo "
                 "task …'). Tìm dự án theo tên trong các dự án người hỏi thấy được, người phụ trách theo tên / mã nhân sự. "
                 "Chưa rõ dự án hay người → tool trả lựa chọn, hỏi người dùng MỘT câu. Ngày dạng YYYY-MM-DD theo giờ VN."),
    parameters={"type": "object", "properties": {
        "title": {"type": "string", "description": "Tên việc, ngắn gọn."},
        "project": {"type": "string", "description": "Tên (một phần) của dự án / danh sách việc; bỏ trống nếu chưa nói."},
        "assignees": {"type": "array", "items": {"type": "string"},
                      "description": "Người phụ trách: tên hoặc mã nhân sự."},
        "due_date": {"type": "string", "description": "Hạn chót YYYY-MM-DD (tùy chọn)."},
        "start_date": {"type": "string", "description": "Ngày bắt đầu YYYY-MM-DD (tùy chọn)."},
        "description": {"type": "string", "description": "Mô tả thêm (tùy chọn)."},
        "asked_fields": confirm_fields.ASKED_PARAM},
        "required": ["title"]},
    handler=_draft_work_task,
)


def _pick_lists(ctx: ToolContext, want: str, lists: list[int]) -> tuple[list[int], str, dict | None]:
    """ai-CR-175: lọc dự án theo tên trong các dự án người hỏi thấy được. Trả (id dự án, tên khớp, lỗi / lựa chọn)."""
    from app.modules.work.model import WorkList

    rows = list(ctx.db.query(WorkList).filter(WorkList.id.in_(lists), WorkList.is_archived == 0).order_by(WorkList.name))
    hit = [w for w in rows if want in (w.name or "").lower()]
    if len(hit) == 1:
        return [hit[0].id], hit[0].name, None
    if not hit:
        return [], "", {"error": f"không thấy dự án «{want}» trong các dự án anh/chị tham gia",
                        "options": [w.name for w in rows][:10]}
    return [], "", {"need_choice": "project", "options": [w.name for w in hit][:8],
                    "note": "Hỏi người dùng MỘT câu: ý là dự án nào (đưa danh sách đánh số)."}


def _my_work_tasks(ctx: ToolContext, args: dict) -> dict:
    """ai-CR-140: việc ĐANG MỞ mình phụ trách (hoặc theo dõi) ở phân hệ Dự án, hạn tới `until` (mặc định hôm nay) —
    gồm cả việc quá hạn. Chỉ trong các dự án người hỏi thấy được; bỏ việc đã xóa mềm.

    ai-CR-175 (đại ca 10/10: trợ lý cá nhân liệt kê việc THEO DỰ ÁN): thêm `project` (lọc một dự án theo tên),
    `all_open` (mọi việc đang mở, kể cả chưa đặt hạn — cho câu «dự án X còn gì»), `only_mine=false` (việc của cả dự án,
    kèm tên người phụ trách); kết quả luôn có `by_project` gom theo dự án để model in theo nhóm."""
    from datetime import date

    from app.modules.employee.model import Employee
    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    if not ctx.can("work_task", "read"):
        return denied("xem công việc ở phân hệ Dự án")
    actor = resolve_actor(ctx.db, ctx.user)
    if not actor.employee_id:
        return {"total": 0, "items": [], "by_project": [],
                "note": "tài khoản chưa gắn hồ sơ nhân sự nên không có việc Dự án"}
    today = date.today().isoformat()
    until = str(args.get("until") or "").strip() or today
    if not _DATE.match(until):
        return {"error": "until phải dạng YYYY-MM-DD"}
    only_mine = args.get("only_mine", True) is not False
    all_open = bool(args.get("all_open"))
    kinds = [int(WorkAssigneeKind.PIC)] + ([int(WorkAssigneeKind.FOLLOWER)] if args.get("include_following") else [])
    lists = visible_list_ids(ctx.db, actor.employee_id)
    if not lists:
        return {"total": 0, "items": [], "by_project": []}
    project = ""
    want = " ".join(str(args.get("project") or "").split()).lower()
    if want:
        lists, project, problem = _pick_lists(ctx, want, lists)
        if problem:
            return problem
    q = (ctx.db.query(WorkTask, WorkList.name).join(WorkList, WorkList.id == WorkTask.list_id)
         .filter(WorkTask.status == int(WorkTaskStatus.OPEN), WorkTask.deleted_at.is_(None), WorkTask.list_id.in_(lists)))
    if only_mine:
        q = q.join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id).filter(
            WorkTaskAssignee.employee_id == actor.employee_id, WorkTaskAssignee.kind.in_(kinds))
    if not all_open:
        q = q.filter(WorkTask.due_date != "", WorkTask.due_date <= until)
    #  Việc chưa đặt hạn (chuỗi rỗng) xếp cuối; có hạn thì theo hạn.
    rows = q.order_by(WorkTask.due_date == "", WorkTask.due_date, WorkTask.id).limit(min(int(args.get("limit") or 30), 100)).all()
    pics: dict[int, list[str]] = {}
    if rows and not only_mine:
        for tid, name in (ctx.db.query(WorkTaskAssignee.task_id, Employee.full_name)
                          .join(Employee, Employee.id == WorkTaskAssignee.employee_id)
                          .filter(WorkTaskAssignee.task_id.in_([t.id for t, _n in rows]),
                                  WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))):
            pics.setdefault(int(tid), []).append(name)
    items = []
    for t, name in rows:
        it = {"id": t.id, "title": t.title, "project": name, "due_date": t.due_date,
              "overdue": bool(t.due_date) and t.due_date < today, "subtask": t.parent_id is not None}
        if not only_mine:
            it["assignees"] = pics.get(t.id, [])
        items.append(it)
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["project"], []).append(it)
    out = {"total": len(items), "today": today, "items": items,
           "by_project": [{"project": p, "count": len(v), "items": v} for p, v in groups.items()]}
    if project:
        out["project"] = project
    if not only_mine:
        out["note"] = "Việc của cả dự án (không chỉ của người hỏi); `assignees` = người phụ trách."
    return out


MY_WORK_TASKS_SPEC = ToolSpec(
    name="my_work_tasks",
    description=("Liệt kê VIỆC ĐANG MỞ ở phân hệ Dự án, gom theo dự án (`by_project`). Mặc định: việc người hỏi PHỤ TRÁCH "
                 "có hạn tới một ngày (mặc định hôm nay), gồm cả quá hạn: 'hôm nay anh có việc gì', 'việc nào sắp tới hạn', "
                 "'việc quá hạn của tôi', 'việc của tôi theo dự án'. Hỏi về MỘT dự án ('dự án X còn gì', 'việc dự án X') → "
                 "`project` = tên dự án, `all_open` = true (kể cả chưa đặt hạn), `only_mine` = false (việc của cả dự án, kèm "
                 "người phụ trách). Tool trả `need_choice` khi tên dự án khớp nhiều → hỏi người dùng MỘT câu."),
    parameters={"type": "object", "properties": {
        "until": {"type": "string", "description": "Lấy việc có hạn tới ngày này (YYYY-MM-DD, giờ VN); bỏ trống = hôm nay."},
        "project": {"type": "string", "description": "Tên (một phần) của dự án muốn xem; bỏ trống = mọi dự án mình thấy."},
        "all_open": {"type": "boolean", "description": "true = mọi việc đang mở kể cả chưa đặt hạn (bỏ qua `until`)."},
        "only_mine": {"type": "boolean", "description": "false = việc của cả dự án, không chỉ việc mình phụ trách (mặc định true)."},
        "include_following": {"type": "boolean", "description": "Gồm cả việc mình chỉ theo dõi (mặc định không)."},
        "limit": {"type": "integer", "description": "Tối đa bao nhiêu việc (mặc định 30, tối đa 100)."}}},
    handler=_my_work_tasks,
)
