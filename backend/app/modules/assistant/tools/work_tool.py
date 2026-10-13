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


def _sections_of(ctx: ToolContext, list_id: int) -> list[dict]:
    """ai-CR-181: các CỘT kanban của một dự án, theo thứ tự trên bảng (tên do từng dự án tự đặt: Todo, Đang làm…)."""
    from app.modules.work.task_model import WorkSection

    rows = (ctx.db.query(WorkSection).filter(WorkSection.list_id == int(list_id))
            .order_by(WorkSection.sort_order, WorkSection.id).all())
    return [{"id": s.id, "name": s.name} for s in rows]


def _pick_section(sections: list[dict], want: str) -> tuple[dict | None, dict | None]:
    """Tên cột người dùng nói («todo», «đang làm») → đúng MỘT cột (so không dấu, khớp trọn tên trước, rồi chứa)."""
    from app.modules.assistant.glossary import fold

    f = " ".join(fold(want).split())
    if not f:
        return None, None
    exact = [s for s in sections if " ".join(fold(s["name"]).split()) == f]
    hit = exact or [s for s in sections if f in " ".join(fold(s["name"]).split())]
    if len(hit) == 1:
        return hit[0], None
    return None, {"need_choice": "section", "options": [s["name"] for s in sections][:10],
                  "note": ("Hỏi người dùng MỘT câu: việc này vào cột nào (đưa đúng tên các cột của dự án, đánh số)."
                           if hit else f"Dự án không có cột «{want}». Hỏi người dùng chọn một trong các cột (đánh số).")}


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
    #  ai-CR-181 (đại ca 13/10): «trạng thái là todo» = CỘT kanban của dự án. Nói tên cột thì vào đúng cột; không nói
    #  thì cột đầu của dự án và ghi vào «em đang hiểu là» để người dùng sửa trước khi «tạo».
    sections = _sections_of(ctx, lst.id)
    section = None
    if want_section := " ".join(str(args.get("section") or "").split()):
        section, problem = _pick_section(sections, want_section)
        if problem:
            return problem
    elif sections:
        section = sections[0]
        assumptions.append(f"vào cột {section['name']} (cột đầu của dự án; các cột: "
                           + ", ".join(s["name"] for s in sections[:8]) + ")")
    draft = {"list_id": lst.id, "list_name": lst.name, "title": title, "assumptions": assumptions,
             "description": str(args.get("description") or "")[:4000], "due_date": due, "start_date": start,
             "assignees": people, "section_id": int(section["id"]) if section else 0,
             "section_name": section["name"] if section else ""}
    return {"draft": draft,
            "note": ("Đã soạn nháp. Trên Telegram bot tự gửi bản tóm tắt để người dùng nhắn «tạo»; trên web hãy nói người "
                     "dùng tạo ở màn Dự án hoặc nhắn qua Telegram. Đừng tự báo là đã tạo.")}


DRAFT_WORK_TASK_SPEC = ToolSpec(
    name="draft_work_task",
    description=("SOẠN NHÁP một CÔNG VIỆC ở phân hệ Dự án ('lên task gọi NCC X cho anh Được hạn thứ 6', 'giao việc …', 'tạo "
                 "task …'). Tìm dự án theo tên trong các dự án người hỏi thấy được, người phụ trách theo tên / mã nhân sự. "
                 "Chưa rõ dự án hay người → tool trả lựa chọn, hỏi người dùng MỘT câu. Ngày dạng YYYY-MM-DD theo giờ VN. "
                 "Người dùng nói 'trạng thái là todo' / 'vào cột Đang làm' → `section` = tên cột (cột kanban do từng dự án "
                 "tự đặt; trạng thái hệ thống của việc luôn là Đang mở khi tạo)."),
    parameters={"type": "object", "properties": {
        "title": {"type": "string", "description": "Tên việc, ngắn gọn."},
        "project": {"type": "string", "description": "Tên (một phần) của dự án / danh sách việc; bỏ trống nếu chưa nói."},
        "section": {"type": "string", "description": "Tên cột kanban muốn đặt việc vào (Todo, Đang làm…); bỏ trống = cột đầu."},
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
    from app.modules.work.task_model import WorkSection

    q = (ctx.db.query(WorkTask, WorkList.name, WorkSection.name).join(WorkList, WorkList.id == WorkTask.list_id)
         .outerjoin(WorkSection, WorkSection.id == WorkTask.section_id)
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
                          .filter(WorkTaskAssignee.task_id.in_([t.id for t, _n, _s in rows]),
                                  WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))):
            pics.setdefault(int(tid), []).append(name)
    items = []
    for t, name, section in rows:
        it = {"id": t.id, "title": t.title, "project": name, "section": section or "", "due_date": t.due_date,
              "start_date": t.start_date or "",      # bao-CR-616: bản tin sáng gom «đang làm hôm nay»
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
        #  ai-CR-181: hỏi về MỘT dự án thì trả luôn danh sách cột kanban («dự án X có cột nào»).
        out["sections"] = [s["name"] for s in _sections_of(ctx, lists[0])]
    if not only_mine:
        out["note"] = "Việc của cả dự án (không chỉ của người hỏi); `assignees` = người phụ trách."
    return out


MY_WORK_TASKS_SPEC = ToolSpec(
    name="my_work_tasks",
    description=("Liệt kê VIỆC ĐANG MỞ ở phân hệ Dự án, gom theo dự án (`by_project`). Mặc định: việc người hỏi PHỤ TRÁCH "
                 "có hạn tới một ngày (mặc định hôm nay), gồm cả quá hạn: 'hôm nay anh có việc gì', 'việc nào sắp tới hạn', "
                 "'việc quá hạn của tôi', 'việc của tôi theo dự án'. Hỏi về MỘT dự án ('dự án X còn gì', 'việc dự án X') → "
                 "`project` = tên dự án, `all_open` = true (kể cả chưa đặt hạn), `only_mine` = false (việc của cả dự án, kèm "
                 "người phụ trách). Hỏi về một dự án thì kết quả có `sections` = các CỘT kanban của dự án ('dự án X có cột "
                 "nào') và mỗi việc có `section` = cột đang nằm. Tool trả `need_choice` khi tên dự án khớp nhiều → hỏi người "
                 "dùng MỘT câu."),
    parameters={"type": "object", "properties": {
        "until": {"type": "string", "description": "Lấy việc có hạn tới ngày này (YYYY-MM-DD, giờ VN); bỏ trống = hôm nay."},
        "project": {"type": "string", "description": "Tên (một phần) của dự án muốn xem; bỏ trống = mọi dự án mình thấy."},
        "all_open": {"type": "boolean", "description": "true = mọi việc đang mở kể cả chưa đặt hạn (bỏ qua `until`)."},
        "only_mine": {"type": "boolean", "description": "false = việc của cả dự án, không chỉ việc mình phụ trách (mặc định true)."},
        "include_following": {"type": "boolean", "description": "Gồm cả việc mình chỉ theo dõi (mặc định không)."},
        "limit": {"type": "integer", "description": "Tối đa bao nhiêu việc (mặc định 30, tối đa 100)."}}},
    handler=_my_work_tasks,
)


#  ---------------------------------------------------------------------------------------------------------------
#  bao-CR-616 (phase 24.1, doc/agent-hub/18) — SOẠN NHÁP CẢ CÂY KẾ HOẠCH: giai đoạn → việc cha → việc con, mỗi việc
#  có người làm, khung ngày, mức ưu tiên, tiêu chí đánh giá. Tool chỉ chuẩn hóa theo bộ luật (`plan_policy`) và ghi
#  điều tự hiểu vào `assumptions`; tạo thật là việc của `agent_hub/work_plan.build` sau khi người dùng nhắn «tạo».
#  ---------------------------------------------------------------------------------------------------------------
_PRIORITY_WORDS = {
    "gap": "Gấp", "khan": "Gấp", "p1": "Gấp", "urgent": "Gấp",
    "uu tien": "Ưu tiên", "cao": "Ưu tiên", "p2": "Ưu tiên", "high": "Ưu tiên",
    "thuong": "Thường", "vua": "Thường", "p3": "Thường", "normal": "Thường", "thap": "Thường", "p4": "Thường",
}
_MAX_PHASES, _MAX_TASKS_PER_PHASE, _MAX_CRITERIA = 12, 30, 3


def _plan_priority(raw: str, default: str) -> str:
    from app.modules.assistant.glossary import fold

    key = " ".join(fold(str(raw or "")).split())
    if not key:
        return default
    for k, v in _PRIORITY_WORDS.items():
        if key == k or key.startswith(k + " ") or key.startswith(k + "-"):
            return v
    return default


def _note(assumptions: dict, key: str, label: str) -> None:
    """Giả định gom theo NHÓM (thiếu tiêu chí, chưa giao ai…) kèm tên việc — thẻ nháp in mỗi nhóm một dòng."""
    assumptions.setdefault(key, []).append(label)


_ASSUMPTION_TEXT = {
    "no_criteria": "chưa có tiêu chí, em dùng tiêu chí mặc định",
    "no_assignee": "chưa giao ai — anh/chị chỉ định hoặc để em hỏi sau",
    "swapped": "hạn trước ngày bắt đầu nên em đảo lại",
    "sunday": "có hạn rơi vào Chủ nhật — anh/chị xem có dời không",
    "long": "kéo dài hơn mức ngày công của luật mà chưa chia được thêm — anh/chị xem có tách không",
    "trimmed": "có quá nhiều việc con, em giữ đúng số tối đa của luật",
}


def _assumption_lines(assumptions: dict) -> list[str]:
    out = []
    for key, titles in assumptions.items():
        names = ", ".join(f"«{t}»" for t in titles[:3]) + (f" và {len(titles) - 3} việc nữa" if len(titles) > 3 else "")
        out.append(f"{names}: {_ASSUMPTION_TEXT.get(key, key)}")
    return out[:8]


def _plan_dates(item: dict, label: str, assumptions: dict, policy: dict) -> tuple[str, str, str]:
    """(ngày bắt đầu, hạn, lỗi). Hạn trước ngày bắt đầu thì đảo lại; hạn rơi Chủ nhật thì ghi giả định (không tự dời)."""
    from datetime import date

    start = str(item.get("start_date") or "").strip()
    due = str(item.get("due_date") or "").strip()
    for name, val in (("start_date", start), ("due_date", due)):
        if val and not _DATE.match(val):
            return "", "", f"{name} của «{label}» phải dạng YYYY-MM-DD"
    if start and due and due < start:
        start, due = due, start
        _note(assumptions, "swapped", label)
    if due and policy.get("no_sunday"):
        try:
            if date.fromisoformat(due).weekday() == 6:
                _note(assumptions, "sunday", label)
        except ValueError:
            pass
    if start and due and item.get("subtasks") is None:
        try:
            span = (date.fromisoformat(due) - date.fromisoformat(start)).days + 1
            limit = int(policy.get("max_task_days") or 0)
            if limit and span > limit:
                _note(assumptions, "long", label)
        except ValueError:
            pass
    return start, due, ""


def _plan_task(ctx: ToolContext, raw: dict, policy: dict, assumptions: dict, problems: list[str],
               allow_sub: bool) -> dict | None:
    title = " ".join(str(raw.get("title") or "").split())[:500]
    if not title:
        return None
    people, bad = _find_people(ctx, raw.get("assignees") or [])
    problems.extend(bad)
    if not people and not bad:
        _note(assumptions, "no_assignee", title)
    start, due, err = _plan_dates(raw, title, assumptions, policy)
    if err:
        problems.append(err)
    criteria = [" ".join(str(c).split())[:300] for c in (raw.get("criteria") or []) if str(c).strip()][:_MAX_CRITERIA]
    if not criteria:
        criteria = [str(policy.get("default_criteria") or "")]
        _note(assumptions, "no_criteria", title)
    out = {"title": title, "assignees": people, "start_date": start, "due_date": due,
           "priority": _plan_priority(str(raw.get("priority") or ""), str(policy.get("default_priority"))),
           "criteria": criteria, "description": str(raw.get("description") or "")[:2000],
           "_own_criteria": bool(raw.get("criteria"))}
    if allow_sub:
        subs_raw = raw.get("subtasks") or []
        if not isinstance(subs_raw, list):
            subs_raw = []
        limit = int(policy.get("max_subtasks") or 7)
        if len(subs_raw) > limit:
            _note(assumptions, "trimmed", f"{title} ({len(subs_raw)} → {limit})")
            subs_raw = subs_raw[:limit]
        subs = []
        for s in subs_raw:
            if isinstance(s, dict):
                s = dict(s)
                s.pop("subtasks", None)      # phân hệ Dự án chỉ hai tầng (C-05)
                sub = _plan_task(ctx, s, policy, assumptions, problems, allow_sub=False)
                if sub:
                    subs.append(sub)
        out["subtasks"] = subs
    return out


def _draft_work_plan(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import plan_policy

    if not ctx.can("work_task", "create"):
        return denied("lập kế hoạch việc ở phân hệ Dự án")
    user_text, asked = confirm_fields.take_context(args)
    title = " ".join(str(args.get("title") or "").split())[:200]
    if not title:
        return {"error": "thiếu tên kế hoạch"}
    phases_raw = args.get("phases") or []
    if not isinstance(phases_raw, list) or not [p for p in phases_raw if isinstance(p, dict)]:
        return confirm_fields.need([{"field": "phases",
                                     "question": "Kế hoạch gồm những giai đoạn nào, mỗi giai đoạn có việc gì, ai làm, hạn khi nào?"}])
    policy = plan_policy.current()
    assumptions: dict = {}
    problems: list[str] = []
    phases: list[dict] = []
    for i, ph in enumerate([p for p in phases_raw if isinstance(p, dict)][:_MAX_PHASES]):
        name = " ".join(str(ph.get("name") or "").split())[:100] or f"Giai đoạn {i + 1}"
        tasks = []
        for t in (ph.get("tasks") or [])[:_MAX_TASKS_PER_PHASE]:
            if isinstance(t, dict):
                task = _plan_task(ctx, t, policy, assumptions, problems, allow_sub=True)
                if task:
                    tasks.append(task)
        if tasks:
            phases.append({"name": name, "tasks": tasks})
    if problems:
        return {"need_choice": "assignee", "problems": problems[:8],
                "note": "Hỏi người dùng MỘT câu để chọn đúng người / sửa ngày (đưa lựa chọn đánh số), rồi gọi lại tool."}
    if not phases:
        return {"error": "kế hoạch chưa có việc nào có tên"}
    #  Chốt chặn (sau thử dev 13/10): sếp muốn bot TỰ chia việc con và TỰ đặt tiêu chí, không chép lại câu người dùng.
    #  Việc cha nào thiếu một trong hai thì bắt Trợ lý soạn lại MỘT lần (`refined`) trước khi đưa thẻ nháp.
    weak = _weak_tasks(phases, policy)
    if weak and not args.get("refined"):
        return {"need_refine": weak[:12],
                "note": (f"CHƯA soạn nháp. Gọi lại draft_work_plan NGAY (không hỏi người dùng) với refined=true, giữ nguyên "
                         f"các việc đã có và bổ sung cho từng việc nêu trên: {plan_policy.MIN_SUBTASKS}–"
                         f"{policy.get('max_subtasks')} việc con là các bước làm cụ thể (mỗi việc con có người làm, hạn, "
                         "1–3 tiêu chí) và 1–3 tiêu chí đo được cho việc cha (kết quả nhìn thấy được: tệp, tin nhắn, số "
                         "lượng, mốc giờ). Chỉ dùng tiêu chí mặc định khi thật sự không nghĩ ra.")}
    for p in phases:
        for t in p["tasks"]:
            t.pop("_own_criteria", None)
            for s in t.get("subtasks") or []:
                s.pop("_own_criteria", None)
    n_tasks = sum(len(p["tasks"]) for p in phases)
    n_subs = sum(len(t.get("subtasks") or []) for p in phases for t in p["tasks"])
    deadline = str(args.get("deadline") or "").strip()
    if deadline and not _DATE.match(deadline):
        return {"error": "deadline phải dạng YYYY-MM-DD"}
    draft = {"title": title, "description": str(args.get("description") or "")[:2000], "deadline": deadline,
             "phases": phases, "assumptions": _assumption_lines(assumptions),
             "counts": {"phases": len(phases), "tasks": n_tasks, "subtasks": n_subs},
             "policy": plan_policy.describe(policy)}
    return {"draft": draft,
            "note": ("Đã soạn nháp kế hoạch. Trên Telegram bot tự gửi bản tóm tắt để người dùng nhắn «tạo» (tạo bảng "
                     "trong Dự án rồi hỏi từng người nhận việc). Đừng tự báo là đã tạo.")}


def _weak_tasks(phases: list[dict], policy: dict) -> list[str]:
    """Việc cha chưa đạt luật: thiếu việc con (< MIN_SUBTASKS) hoặc chưa có tiêu chí tự đặt. Trả câu mô tả từng việc."""
    from app.modules.agent_hub import plan_policy

    out = []
    for p in phases:
        for t in p["tasks"]:
            lack = []
            if len(t.get("subtasks") or []) < plan_policy.MIN_SUBTASKS:
                lack.append(f"mới {len(t.get('subtasks') or [])} việc con")
            if not t.get("_own_criteria"):
                lack.append("chưa có tiêu chí")
            if lack:
                out.append(f"«{t['title']}»: {', '.join(lack)}")
    return out


_SUB_SCHEMA = {"type": "object", "properties": {
    "title": {"type": "string"},
    "assignees": {"type": "array", "items": {"type": "string"}, "description": "Tên hoặc mã nhân sự."},
    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
    "due_date": {"type": "string", "description": "YYYY-MM-DD"},
    "priority": {"type": "string", "description": "Gấp · Ưu tiên · Thường"},
    "criteria": {"type": "array", "items": {"type": "string"}, "description": "1–3 tiêu chí đo được."},
    "description": {"type": "string"}},
    "required": ["title"]}
_TASK_SCHEMA = {"type": "object", "properties": {**_SUB_SCHEMA["properties"],
                                                 "subtasks": {"type": "array", "items": _SUB_SCHEMA,
                                                              "description": "Việc con (tối đa 7, không lồng thêm)."}},
                "required": ["title"]}


def _plan_rules_text() -> str:
    from app.modules.agent_hub import plan_policy

    return plan_policy.describe(plan_policy.DEFAULTS)


DRAFT_WORK_PLAN_SPEC = ToolSpec(
    name="draft_work_plan",
    description=("SOẠN NHÁP CẢ KẾ HOẠCH VIỆC ở phân hệ Dự án từ một danh sách việc hoặc một mục tiêu ('lập kế hoạch tiếp "
                 "khách Trung Quốc ngày mai', 'lên plan cho việc X', 'chia việc này ra cho đội'). Tự chia thành giai đoạn → "
                 "việc cha → việc con, mỗi việc có người làm (tên / mã nhân sự), ngày bắt đầu, hạn (YYYY-MM-DD giờ VN), "
                 "mức ưu tiên (Gấp · Ưu tiên · Thường) và 1–3 tiêu chí đánh giá đo được. Người dùng chỉ liệt kê việc "
                 "thì BẠN vẫn phải tự nghĩ ra các bước làm (việc con) và tiêu chí cho từng việc — đó là phần việc của "
                 "bot, không chép lại câu người dùng. Luật: " + _plan_rules_text() +
                 " Người chưa rõ → tool trả lựa chọn, hỏi người dùng MỘT câu. Việc cha nào thiếu việc con / tiêu chí → "
                 "tool trả need_refine, gọi lại ngay với refined=true. Một việc lẻ thì dùng draft_work_task."),
    parameters={"type": "object", "properties": {
        "title": {"type": "string", "description": "Tên kế hoạch (thành tên bảng trong Dự án)."},
        "description": {"type": "string", "description": "Mục tiêu / bối cảnh (tùy chọn)."},
        "deadline": {"type": "string", "description": "Hạn chót cả kế hoạch YYYY-MM-DD (tùy chọn)."},
        "phases": {"type": "array", "description": "Các giai đoạn theo thứ tự; mỗi giai đoạn thành một cột kanban.",
                   "items": {"type": "object", "properties": {
                       "name": {"type": "string"},
                       "tasks": {"type": "array", "items": _TASK_SCHEMA}},
                       "required": ["name", "tasks"]}},
        "refined": {"type": "boolean", "description": "true khi gọi lại sau need_refine (đã tự chia việc con và đặt "
                                                       "tiêu chí cho từng việc). Lần đầu để trống."},
        "asked_fields": confirm_fields.ASKED_PARAM},
        "required": ["title", "phases"]},
    handler=_draft_work_plan,
)
