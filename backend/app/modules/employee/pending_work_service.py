"""Việc DUYỆT một nhân sự đang giữ — màn kiểm trước khi khóa tài khoản (duoc-CR-665, V0-4).

Khóa tài khoản / chuyển hồ sơ sang nghỉ việc (`lock_linked_users`) KHÔNG đụng tới bảng việc
của bộ máy duyệt: phiếu đang chờ người đó vẫn mang tên họ, mà họ thì không còn đăng nhập
được → phiếu kẹt, không chỗ nào đỏ lên. Hàm ở đây chỉ ĐỌC, để người thao tác thấy trước
và chuyển đi (đường chuyển có sẵn: `PATCH /api/approvals/tasks/{id}/reassign`, `POST
/api/approvals/handover`).

Liệt kê hai loại:
  * `tasks`      — việc duyệt CÒN TREO (chờ hoặc chưa tới lượt) trên phiên duyệt đang mở;
  * `flow_steps` — bước của luồng duyệt ĐANG BẬT chỉ đích danh người này (người duyệt cụ thể
                   hoặc người dự phòng). Không chuyển được từ đây: sửa luồng là việc của
                   quản trị luồng, màn này chỉ nói ra và dẫn tới luồng.

KHÔNG liệt kê (ngoài phạm vi): ủy quyền, người xử lý YCMH/YCBG, vị trí trưởng bộ phận.
"""
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalFlow, ApprovalNode
from app.modules.approval.instance_model import (INSTANCE_OPEN_STATUSES, TASK_OPEN_STATUSES,
                                                 TASK_PENDING, TASK_STATUS_LABELS,
                                                 ApprovalInstance, ApprovalTask)

from .model import Employee

#  Trần số dòng trả về — người đang giữ cả trăm phiếu vẫn thấy tổng thật qua `total_*`.
MAX_ROWS = 200


def _node_names_employee(node: ApprovalNode, employee_id: int) -> str | None:
    """`pick` = người duyệt cụ thể, `fallback` = người dự phòng, None = không nhắc tới."""
    if node.approver_kind == APPROVER_EMPLOYEE:
        refs = {part.strip() for part in (node.approver_ref or "").split(",")}
        if str(employee_id) in refs:
            return "approver"
    if node.fallback_employee_id == employee_id:
        return "fallback"
    return None


def pending_work_of(db: Session, employee_id: int,
                    can_see: Callable[[ApprovalInstance], bool] | None = None) -> dict:
    """`can_see(instance)` = người XEM có được đọc chứng từ của phiếu không (thường là
    `entity_hooks.can_read`). Không được thì vẫn đếm + vẫn chuyển được việc, nhưng mã/tên
    phiếu và người trình bị xóa trắng: `employee.read` không phải quyền đọc văn bản mật,
    đơn nghỉ phép hay HĐLĐ của người khác. `None` = không lọc (quản trị toàn hệ / test).
    """
    now = datetime.now()
    task_rows = (
        db.query(ApprovalTask, ApprovalInstance)
        .join(ApprovalInstance, ApprovalInstance.id == ApprovalTask.instance_id)
        .filter(ApprovalTask.assignee_employee_id == employee_id,
                ApprovalTask.status.in_(TASK_OPEN_STATUSES),
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .order_by(ApprovalTask.due_at.is_(None), ApprovalTask.due_at.asc(), ApprovalTask.id.asc())
        .all()
    )
    starters = {i.started_by_employee_id for _, i in task_rows if i.started_by_employee_id}
    names = ({row.id: row.full_name for row in
              db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(starters)).all()}
             if starters else {})
    tasks = [_task_out(task, inst, names, now, can_see) for task, inst in task_rows[:MAX_ROWS]]
    return _with_flow_steps(db, employee_id, tasks, len(task_rows))


def _task_out(task: ApprovalTask, inst: ApprovalInstance, names: dict, now: datetime,
              can_see: Callable[[ApprovalInstance], bool] | None) -> dict:
    visible = can_see is None or can_see(inst)
    return {
        "task_id": task.id,
        "instance_id": inst.id,
        "entity": inst.entity,
        "entity_id": inst.entity_id,
        "entity_code": inst.entity_code if visible else "",
        "entity_title": inst.entity_title if visible else "",
        "hidden": not visible,
        "node_name": task.node_name,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, ""),
        "due_at": task.due_at,
        "is_overdue": bool(task.status == TASK_PENDING and task.due_at and task.due_at < now),
        "started_by_employee_id": inst.started_by_employee_id if visible else 0,
        "started_by_name": names.get(inst.started_by_employee_id, "") if visible else "",
    }


def _with_flow_steps(db: Session, employee_id: int, tasks: list, total_tasks: int) -> dict:
    flow_rows = (
        db.query(ApprovalNode, ApprovalFlow)
        .join(ApprovalFlow, ApprovalFlow.id == ApprovalNode.flow_id)
        .filter(ApprovalFlow.is_active.is_(True))
        .order_by(ApprovalFlow.entity, ApprovalFlow.id, ApprovalNode.seq)
        .all()
    )
    flow_steps = []
    for node, flow in flow_rows:
        role = _node_names_employee(node, employee_id)
        if role:
            flow_steps.append({
                "flow_id": flow.id, "flow_code": flow.code, "flow_name": flow.name,
                "entity": flow.entity, "node_id": node.id, "node_seq": node.seq,
                "node_name": node.name, "role": role,
            })
    return {
        "employee_id": employee_id,
        "tasks": tasks,
        "total_tasks": total_tasks,
        "flow_steps": flow_steps[:MAX_ROWS],
        "total_flow_steps": len(flow_steps),
    }
