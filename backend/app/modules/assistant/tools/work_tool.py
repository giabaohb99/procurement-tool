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
    title = " ".join(str(args.get("title") or "").split())[:500]
    if not title:
        return {"error": "thiếu tên công việc"}
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
    draft = {"list_id": lst.id, "list_name": lst.name, "title": title,
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
        "description": {"type": "string", "description": "Mô tả thêm (tùy chọn)."}},
        "required": ["title"]},
    handler=_draft_work_task,
)


def _my_work_tasks(ctx: ToolContext, args: dict) -> dict:
    """ai-CR-140: việc ĐANG MỞ mình phụ trách (hoặc theo dõi) ở phân hệ Dự án, hạn tới `until` (mặc định hôm nay) —
    gồm cả việc quá hạn. Chỉ trong các dự án người hỏi thấy được; bỏ việc đã xóa mềm."""
    from datetime import date

    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    if not ctx.can("work_task", "read"):
        return denied("xem công việc ở phân hệ Dự án")
    actor = resolve_actor(ctx.db, ctx.user)
    if not actor.employee_id:
        return {"total": 0, "items": [], "note": "tài khoản chưa gắn hồ sơ nhân sự nên không có việc Dự án"}
    today = date.today().isoformat()
    until = str(args.get("until") or "").strip() or today
    if not _DATE.match(until):
        return {"error": "until phải dạng YYYY-MM-DD"}
    kinds = [int(WorkAssigneeKind.PIC)] + ([int(WorkAssigneeKind.FOLLOWER)] if args.get("include_following") else [])
    lists = visible_list_ids(ctx.db, actor.employee_id)
    if not lists:
        return {"total": 0, "items": []}
    q = (ctx.db.query(WorkTask, WorkList.name)
         .join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
         .join(WorkList, WorkList.id == WorkTask.list_id)
         .filter(WorkTaskAssignee.employee_id == actor.employee_id, WorkTaskAssignee.kind.in_(kinds),
                 WorkTask.status == int(WorkTaskStatus.OPEN), WorkTask.deleted_at.is_(None),
                 WorkTask.list_id.in_(lists), WorkTask.due_date != "", WorkTask.due_date <= until)
         .order_by(WorkTask.due_date, WorkTask.id))
    rows = q.limit(int(args.get("limit") or 30)).all()
    items = [{"id": t.id, "title": t.title, "project": name, "due_date": t.due_date,
              "overdue": t.due_date < today, "subtask": t.parent_id is not None} for t, name in rows]
    return {"total": len(items), "today": today, "items": items}


MY_WORK_TASKS_SPEC = ToolSpec(
    name="my_work_tasks",
    description=("Liệt kê VIỆC ĐANG MỞ người hỏi PHỤ TRÁCH ở phân hệ Dự án có hạn tới một ngày (mặc định hôm nay), gồm cả "
                 "việc quá hạn: 'hôm nay anh có việc gì', 'việc nào sắp tới hạn', 'việc quá hạn của tôi'."),
    parameters={"type": "object", "properties": {
        "until": {"type": "string", "description": "Lấy việc có hạn tới ngày này (YYYY-MM-DD, giờ VN); bỏ trống = hôm nay."},
        "include_following": {"type": "boolean", "description": "Gồm cả việc mình chỉ theo dõi (mặc định không)."},
        "limit": {"type": "integer", "description": "Tối đa bao nhiêu việc (mặc định 30)."}}},
    handler=_my_work_tasks,
)
