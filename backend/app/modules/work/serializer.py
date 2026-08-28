"""Phân hệ Công việc — hình dạng dữ liệu trả ra API.

Gom một chỗ để bốn service không mỗi nơi trả một kiểu. Mọi hàm ở đây THUẦN:
nhận đối tượng model + vài thứ tra sẵn, trả dict — không tự đi hỏi CSDL, vì gọi
trong vòng lặp là đẻ ra N+1 query.
"""
from app.modules.work.label_model import WorkLabelField, WorkLabelOption, WorkTag
from app.modules.work.model import WorkGroup, WorkList
from app.modules.work.task_model import WorkSection, WorkTask


def group_out(g: WorkGroup, my_role: int | None = None) -> dict:
    return {
        "id": g.id, "name": g.name, "description": g.description,
        "parent_id": g.parent_id, "sort_order": g.sort_order,
        "is_archived": int(g.is_archived), "my_role": my_role,
    }


def list_out(lst: WorkList, my_role: int | None = None, task_count: int = 0,
             task_done: int = 0, owner: dict | None = None,
             members: list[dict] | None = None) -> dict:
    """Một DỰ ÁN (= một danh sách công việc).

    `owner` / `members` chỉ được điền ở màn liệt kê dự án — hai khóa đó cần thêm
    query, mà cây điều hướng bên trái và payload bảng kanban thì không dùng tới.
    Vắng mặt là `None` / `[]`, KHÔNG phải thiếu dữ liệu.
    """
    return {
        "id": lst.id, "name": lst.name, "description": lst.description,
        "color": lst.color, "group_id": lst.group_id, "sort_order": lst.sort_order,
        "is_archived": int(lst.is_archived), "my_role": my_role,
        "task_count": task_count,
        #  Tử số của thanh tiến độ. Giao diện tự chia, KHÔNG trả sẵn phần trăm:
        #  dự án 0 việc phải hiện 0% chứ không phải chia cho 0 ở máy chủ.
        "task_done": task_done,
        "created_at": lst.created_at.isoformat() if lst.created_at else "",
        "owner": owner,
        "members": members or [],
    }


def member_out(m, name: str = "", code: str = "") -> dict:
    """Dòng thành viên của nhóm hoặc list — hai bảng cùng khuôn nên dùng chung."""
    return {
        "id": m.id, "employee_id": m.employee_id, "role": int(m.role),
        "department_id": m.department_id,
        "employee_name": name, "employee_code": code,
    }


def section_out(s: WorkSection) -> dict:
    return {"id": s.id, "name": s.name, "color": s.color, "sort_order": s.sort_order,
            "list_id": s.list_id}


def tag_out(t: WorkTag) -> dict:
    return {"id": t.id, "name": t.name, "color": t.color, "sort_order": t.sort_order,
            "list_id": t.list_id}


def label_option_out(o: WorkLabelOption) -> dict:
    return {"id": o.id, "name": o.name, "color": o.color, "sort_order": o.sort_order,
            "field_id": o.field_id}


def label_field_out(f: WorkLabelField, options: list[WorkLabelOption]) -> dict:
    return {"id": f.id, "name": f.name, "sort_order": f.sort_order, "list_id": f.list_id,
            "options": [label_option_out(o) for o in options]}


def task_out(t: WorkTask, *, assignees: list[dict], tag_ids: list[int],
             labels: list[dict], subtask_done: int = 0, subtask_total: int = 0,
             comment_count: int = 0) -> dict:
    """Một task cho cả kanban lẫn danh sách.

    `subtask_done/total` là tiến độ "n/m" trên thẻ (C-02) — chỉ đếm việc con,
    và chỉ task CHA mới có. Việc con không bao giờ tự đứng thành thẻ (C-05).
    """
    return {
        "id": t.id, "list_id": t.list_id, "section_id": t.section_id,
        "parent_id": t.parent_id,
        "title": t.title, "description": t.description,
        "status": int(t.status), "priority": int(t.priority),
        "start_date": t.start_date, "due_date": t.due_date,
        "sort_order": t.sort_order,
        "creator_employee_id": t.creator_employee_id,
        "completed_at": t.completed_at, "completed_by": t.completed_by,
        "created_at": t.created_at, "updated_at": t.updated_at,
        "assignees": assignees,
        "tag_ids": tag_ids,
        "labels": labels,
        "subtask_done": subtask_done, "subtask_total": subtask_total,
        "comment_count": comment_count,
    }
