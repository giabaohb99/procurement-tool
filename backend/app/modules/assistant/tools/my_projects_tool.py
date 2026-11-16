"""Tool `my_projects` (duoc-CR-763): DỰ ÁN và NHÓM DỰ ÁN người hỏi đang tham gia ở phân hệ Dự án.

Lỗi gốc (prod 16/11/2026): người dùng là thành viên 14 dự án của nhóm "DX", hỏi Trợ lý **anh đang có trong những dự án
nào** thì bot trả **không có dự án nào** — nó chỉ có `my_work_tasks`, mặc định chỉ trả việc CỦA MÌNH tới hạn hôm nay. Hỏi
tiếp **anh có đang trong nhóm dự án nào** thì bot đi kể nhóm Telegram. Thiếu đúng một công cụ liệt kê dự án.

Luật thấy dự án dùng ĐÚNG hàm của màn Dự án (`/project/lists`, `work.list_service.get_lists`): `visible_list_ids` (mời
riêng ∪ kế thừa từ nhóm / nhóm cha), không có luật thứ hai. Số đếm cũng lấy đúng hàm của màn (`_task_counts` cho thanh
tiến độ, `_people_by_list` cho chủ sở hữu + thành viên). Số truy vấn cố định, không theo số dự án.
"""
from __future__ import annotations

import math

from .base import ToolContext, ToolSpec, denied

MAX_PROJECTS = 100
FILTER_MAX_LEN = 200
NO_GROUP_NAME = "Không thuộc nhóm nào"
PROJECT_URL = "/project/lists/{id}"
PROJECT_LIST_URL = "/project/lists"


def compute_progress_pct(done: int, total: int) -> int:
    """Phần trăm của thanh tiến độ — ĐÚNG công thức `ProgressCell` ở màn Dự án: `Math.round(done / total * 100)`,
    dự án chưa có việc nào = 0. `Math.round` của JS làm tròn nửa lên (khác `round` của Python làm tròn về số chẵn)."""
    if total <= 0:
        return 0
    return int(math.floor(done / total * 100 + 0.5))


def compute_effective_roles(db, employee_id: int, lists: list, groups: dict) -> dict[int, int | None]:
    """Vai trò hiệu lực trên TỪNG dự án — cùng luật `membership_service.effective_role` (min của: mời riêng ở dự án ·
    vai trò ở nhóm chứa dự án · vai trò ở nhóm cha), nhưng gom HAI truy vấn cho cả trang thay vì ba truy vấn mỗi dự án.
    `groups` = {group_id: WorkGroup} đã nạp (cần `parent_id`). Bài kiểm so từng dự án với `effective_role`."""
    from app.modules.work.model import WorkGroupMember, WorkListMember

    if not employee_id or not lists:
        return {}
    direct = {int(lid): int(role) for lid, role in db.query(WorkListMember.list_id, WorkListMember.role).filter(
        WorkListMember.employee_id == employee_id, WorkListMember.list_id.in_([x.id for x in lists]))}
    by_group: dict[int, int] = {}
    for gid, role in db.query(WorkGroupMember.group_id, WorkGroupMember.role).filter(
            WorkGroupMember.employee_id == employee_id):
        by_group[int(gid)] = min(int(role), by_group.get(int(gid), int(role)))
    out: dict[int, int | None] = {}
    for x in lists:
        roles = [direct[x.id]] if x.id in direct else []
        if x.group_id:
            chain = [x.group_id]
            grp = groups.get(x.group_id)
            if grp is not None and grp.parent_id:
                chain.append(grp.parent_id)
            roles += [by_group[g] for g in chain if g in by_group]
        out[x.id] = min(roles) if roles else None
    return out


def _load_groups(db, group_ids: set[int]) -> dict:
    """Nhóm chứa các dự án + nhóm cha của chúng (nhóm chỉ sâu 2 cấp) — tối đa hai truy vấn."""
    from app.modules.work.model import WorkGroup

    if not group_ids:
        return {}
    groups = {g.id: g for g in db.query(WorkGroup).filter(WorkGroup.id.in_(group_ids))}
    parents = {g.parent_id for g in groups.values() if g.parent_id} - set(groups)
    if parents:
        groups.update({g.id: g for g in db.query(WorkGroup).filter(WorkGroup.id.in_(parents))})
    return groups


def _group_path(groups: dict, group_id: int | None) -> str:
    """Tên nhóm hiển thị: **Nhóm cha / Nhóm con** khi nhóm nằm trong một nhóm khác."""
    grp = groups.get(group_id) if group_id else None
    if grp is None:
        return ""
    parent = groups.get(grp.parent_id) if grp.parent_id else None
    return f"{parent.name} / {grp.name}" if parent is not None else grp.name


def _open_counts(db, list_ids: list[int], employee_id: int) -> tuple[dict[int, int], dict[int, int]]:
    """(việc CHA đang mở của cả dự án, việc đang mở MÌNH phụ trách) theo từng dự án — hai truy vấn.

    Vế cả dự án đếm việc cha như `_task_counts` của màn (việc con chỉ là gạch đầu dòng trong thẻ cha); vế của mình đếm
    như `my_work_tasks` (`all_open`): mọi việc đang mở mình là người phụ trách, kể cả việc con."""
    from sqlalchemy import func

    from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    if not list_ids:
        return {}, {}
    alive = (WorkTask.list_id.in_(list_ids), WorkTask.status == int(WorkTaskStatus.OPEN), WorkTask.deleted_at.is_(None))
    open_all = {int(lid): int(n) for lid, n in db.query(WorkTask.list_id, func.count(WorkTask.id)).filter(
        *alive, WorkTask.parent_id.is_(None)).group_by(WorkTask.list_id)}
    mine = {int(lid): int(n) for lid, n in db.query(WorkTask.list_id, func.count(func.distinct(WorkTask.id)))
            .join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
            .filter(*alive, WorkTaskAssignee.employee_id == employee_id,
                    WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC)).group_by(WorkTask.list_id)}
    return open_all, mine


def _clean_filter(value) -> str:
    from app.modules.assistant.glossary import fold

    return " ".join(fold(str(value or "")[:FILTER_MAX_LEN]).split())


def _matches(text: str, want: str) -> bool:
    from app.modules.assistant.glossary import fold

    return not want or want in " ".join(fold(text or "").split())


def _my_projects(ctx: ToolContext, args: dict) -> dict:
    from app.modules.work.list_service import _people_by_list, _task_counts
    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import ENUM_LABELS, WorkList

    if not ctx.can("work_task", "read"):
        return denied("dự án ở phân hệ Dự án")
    actor = resolve_actor(ctx.db, ctx.user)
    empty = {"total": 0, "returned": 0, "has_more": False, "groups": [], "url": PROJECT_LIST_URL}
    if not actor.employee_id:
        return {**empty, "note": "Tài khoản chưa gắn hồ sơ nhân sự nên không tham gia dự án nào. Nhờ quản trị gắn nhân "
                                 "sự cho tài khoản."}
    include_archived = bool(args.get("include_archived"))
    want_group, want_name = _clean_filter(args.get("group")), _clean_filter(args.get("q"))

    #  Cùng tập dự án với màn Dự án (`list_service.get_lists`): visible_list_ids, bỏ dự án lưu trữ trừ khi xin.
    ids = visible_list_ids(ctx.db, actor.employee_id)
    rows = []
    if ids:
        q = ctx.db.query(WorkList).filter(WorkList.id.in_(ids))
        if not include_archived:
            q = q.filter(WorkList.is_archived == 0)
        rows = q.order_by(WorkList.sort_order, WorkList.id).all()
    groups = _load_groups(ctx.db, {x.group_id for x in rows if x.group_id})
    rows = [x for x in rows if _matches(x.name, want_name)
            and _matches(_group_path(groups, x.group_id) if x.group_id else NO_GROUP_NAME, want_group)]
    if not rows:
        hint = ("Không thấy dự án nào khớp bộ lọc trong các dự án người hỏi tham gia." if (want_group or want_name)
                else "Người hỏi chưa tham gia dự án nào (chưa được mời vào dự án hay nhóm dự án nào).")
        return {**empty, "note": hint}

    #  Thứ tự như màn: theo nhóm (nhóm cha → nhóm con), dự án ngoài nhóm đứng cuối; trong nhóm theo thứ tự của dự án.
    def rank(x) -> tuple:
        grp = groups.get(x.group_id) if x.group_id else None
        if grp is None:
            return (1, 0, 0, 0, 0, x.sort_order, x.id)
        parent = groups.get(grp.parent_id) if grp.parent_id else None
        top = parent or grp
        return (0, top.sort_order, top.id, 1 if parent else 0, grp.sort_order if parent else 0, x.sort_order, x.id)

    rows.sort(key=rank)
    total = len(rows)
    page = rows[:MAX_PROJECTS]
    page_ids = [x.id for x in page]
    counts = _task_counts(ctx.db, page_ids)
    people = _people_by_list(ctx.db, page_ids)
    roles = compute_effective_roles(ctx.db, actor.employee_id, page, groups)
    open_all, mine = _open_counts(ctx.db, page_ids, actor.employee_id)
    role_labels = ENUM_LABELS["work_member_role"]

    by_group: dict[int, dict] = {}
    for x in page:
        task_count, task_done = counts.get(x.id, (0, 0))
        owner = people.get(x.id, {}).get("owner") or {}
        role = roles.get(x.id)
        group_name = _group_path(groups, x.group_id) or NO_GROUP_NAME
        bucket = by_group.setdefault(x.group_id or 0, {"group_id": x.group_id or None, "name": group_name,
                                                       "project_count": 0, "projects": []})
        bucket["project_count"] += 1
        bucket["projects"].append({
            "id": x.id, "name": x.name, "group_name": group_name,
            "my_role": role, "my_role_label": role_labels.get(role, "") if role else "",
            "owner_name": owner.get("employee_name", ""),
            "member_count": len(people.get(x.id, {}).get("members", [])),
            "task_count": task_count, "task_done": task_done,
            "progress_pct": compute_progress_pct(task_done, task_count),
            "open_task_count": open_all.get(x.id, 0), "my_open_task_count": mine.get(x.id, 0),
            "archived": bool(x.is_archived), "url": PROJECT_URL.format(id=x.id)})
    out = {"total": total, "returned": len(page), "has_more": total > len(page),
           "group_count": len([g for g in by_group if g]), "my_open_task_count": sum(mine.values()),
           "groups": list(by_group.values()), "url": PROJECT_LIST_URL,
           "note": ("Dự án và NHÓM DỰ ÁN của phân hệ Dự án mà người hỏi thấy (mời riêng hoặc kế thừa từ nhóm), đúng như màn "
                    "Dự án — không phải nhóm chat Telegram. Liệt kê theo nhóm, mỗi dự án kèm vai trò, tiến độ và link. "
                    "Muốn xem VIỆC trong một dự án thì gọi my_work_tasks với project = tên dự án.")}
    if out["has_more"]:
        out["note"] += f" Mới trả {len(page)}/{total} dự án đầu: lọc thêm bằng group hoặc q."
    return out


MY_PROJECTS_SPEC = ToolSpec(
    name="my_projects",
    description=("Liệt kê DỰ ÁN và NHÓM DỰ ÁN người hỏi đang tham gia ở phân hệ Dự án, gom theo nhóm: 'anh đang có trong "
                 "những dự án nào', 'tôi tham gia dự án nào', 'danh sách dự án của tôi', 'anh có trong nhóm dự án nào "
                 "không', 'nhóm DX có những dự án gì'. **Nhóm dự án** là thư mục chứa dự án ở phân hệ Dự án, KHÔNG phải "
                 "nhóm chat Telegram — đừng dùng list_my_groups cho câu này. Cùng tập dự án với màn Dự án (mời riêng hoặc "
                 "kế thừa từ nhóm). Mỗi dự án có vai trò của tôi, chủ sở hữu, số thành viên, tiến độ %, số việc đang mở, "
                 "số việc đang mở tôi phụ trách và link. Hỏi VIỆC (việc hôm nay, việc của dự án X) thì dùng my_work_tasks."),
    parameters={"type": "object", "properties": {
        "include_archived": {"type": "boolean", "description": "true = gồm cả dự án đã lưu trữ (mặc định không)."},
        "group": {"type": "string", "description": "Tên (một phần) của nhóm dự án để lọc, vd 'DX'; bỏ trống = mọi nhóm."},
        "q": {"type": "string", "description": "Tên (một phần) của dự án để lọc; bỏ trống = mọi dự án."}}},
    handler=_my_projects,
)
