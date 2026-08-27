"""Đưa dữ liệu duyệt ra giao diện — nhãn tiếng Việt do BACKEND cấp.

Giao diện không chép cứng nhãn trạng thái: thêm một trạng thái mà quên sửa một
trong hai chỗ thì màn hình hiện số thô, và người dùng đọc "3" thay vì "Từ chối".
"""
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.employee.model import Employee

from . import flow_service
from .delegation_model import Delegation
from .flow_model import (APPROVER_KIND_LABELS, MULTI_MODE_LABELS,
                         NODE_KIND_LABELS, NO_APPROVER_LABELS, ROLE_LABELS,
                         SKIP_MODE_LABELS, ApprovalFlow, ApprovalNode)
from .instance_model import (ACTION_LABELS, INSTANCE_STATUS_LABELS,
                             TASK_STATUS_LABELS, ApprovalAction,
                             ApprovalInstance, ApprovalTask)


def _name_of(db: Session, employee_id: int | None) -> str:
    if not employee_id:
        return ""
    employee = db.get(Employee, employee_id)
    return employee.full_name if employee else f"Nhân sự #{employee_id}"


def flow_out(db: Session, flow: ApprovalFlow, with_steps: bool = False) -> dict:
    company = db.get(Company, flow.company_id) if flow.company_id else None
    data = {
        "id": flow.id,
        "entity": flow.entity,
        "code": flow.code,
        "name": flow.name,
        "description": flow.description,
        "version_no": flow.version_no,
        "is_active": flow.is_active,
        "company_id": flow.company_id,
        "company_name": company.name if company else "",
        "priority": flow.priority,
        "condition": flow.condition,
        "node_count": len(flow_service.nodes_of(db, flow.id)),
        #  Hai luồng mặc định cùng bật thì chỉ một cái chạy — nói ra ngay trên
        #  dòng danh sách, xem `flow_service.canh_bao_trung_mac_dinh`.
        "duplicate_default_warning": flow_service.default_overlap_warning(db, flow),
    }
    if with_steps:
        data["nodes"] = [node_out(db, node) for node in flow_service.nodes_of(db, flow.id)]
    return data


def node_out(db: Session, node: ApprovalNode) -> dict:
    return {
        "id": node.id,
        "flow_id": node.flow_id,
        "seq": node.seq,
        "branch_key": node.branch_key,
        "name": node.name,
        "node_kind": node.node_kind,
        "node_kind_label": NODE_KIND_LABELS.get(node.node_kind, ""),
        "flow_role": node.flow_role,
        "flow_role_label": ROLE_LABELS.get(node.flow_role, ""),
        "approver_kind": node.approver_kind,
        "approver_kind_label": APPROVER_KIND_LABELS.get(node.approver_kind, ""),
        "approver_ref": node.approver_ref,
        "approver_names": _approver_names(db, node),
        "multi_mode": node.multi_mode,
        "multi_mode_label": MULTI_MODE_LABELS.get(node.multi_mode, ""),
        "quorum_percent": node.quorum_percent,
        "condition": node.condition,
        "is_default_branch": node.is_default_branch,
        "skip_duplicate": node.skip_duplicate,
        "skip_duplicate_label": SKIP_MODE_LABELS.get(node.skip_duplicate, ""),
        "sla_hours": node.sla_hours,
        "fallback_employee_id": node.fallback_employee_id,
        "fallback_name": _name_of(db, node.fallback_employee_id),
        "on_no_approver": node.on_no_approver,
        "on_no_approver_label": NO_APPROVER_LABELS.get(node.on_no_approver, ""),
    }


def _approver_names(db: Session, node: ApprovalNode) -> str:
    """Tên hiện trên thẻ bước. Rỗng = cách chọn này chỉ tính được lúc chạy.

    Hai cách chọn dựng được tên ngay lúc khai luồng, và cả hai đều nên dựng:
    thẻ bước ghi mỗi «Người cụ thể» thì người khai phải mở bảng thuộc tính ra
    mới biết mình vừa cử ai.
    """
    from .flow_model import APPROVER_DEPT_HEAD_OF, APPROVER_EMPLOYEE

    ids = [int(part) for part in (node.approver_ref or "").split(",") if part.strip().isdigit()]
    if not ids:
        return ""

    if node.approver_kind == APPROVER_EMPLOYEE:
        return ", ".join(_name_of(db, employee_id) for employee_id in ids)

    if node.approver_kind == APPROVER_DEPT_HEAD_OF:
        #  Ghi theo dạng «Trưởng phòng Nhân sự (Nguyễn Văn A)»: người khai chọn
        #  cái GHẾ, nên cần thấy CẢ tên phòng lẫn ai đang ngồi ghế đó. Phòng bỏ
        #  trống ghế trưởng thì nói thẳng — chọn vào đó là bước kẹt lúc chạy.
        from app.modules.department.model import Department

        by_id = {row.id: row for row in
                   db.query(Department).filter(Department.id.in_(ids)).all()}
        part = []
        for department_id in ids:
            department = by_id.get(department_id)
            if department is None:
                part.append(f"#{department_id} (không còn)")
                continue
            manager_name = _name_of(db, department.manager_id) if department.manager_id else ""
            part.append(f"Trưởng {department.name}"
                        + (f" ({manager_name})" if manager_name else " (chưa có trưởng bộ phận)"))
        return " · ".join(part)

    return ""


def instance_out(db: Session, instance: ApprovalInstance, with_details: bool = False) -> dict:
    data = {
        "id": instance.id,
        "entity": instance.entity,
        "entity_id": instance.entity_id,
        "entity_code": instance.entity_code,
        "entity_title": instance.entity_title,
        "flow_id": instance.flow_id,
        "flow_version": instance.flow_version,
        "flow_name": flow_service.doc_snapshot(instance.flow_snapshot).get("name", ""),
        "status": instance.status,
        "status_label": INSTANCE_STATUS_LABELS.get(instance.status, ""),
        "current_seq": instance.current_seq,
        "started_by_name": _name_of(db, instance.started_by_employee_id),
        "started_at": instance.started_at,
        "finished_at": instance.finished_at,
        "finish_reason": instance.finish_reason,
    }
    if with_details:
        data["tasks"] = [task_out(db, row) for row in instance_service_tasks(db, instance.id)]
        data["actions"] = [action_out(db, row) for row in actions_of(db, instance.id)]
        data["steps"] = [
            {"seq": node.seq, "name": node.name, "branch_key": node.branch_key}
            for node in flow_service.steps(instance.flow_snapshot)
        ]
    return data


def instance_service_tasks(db: Session, instance_id: int) -> list[ApprovalTask]:
    from . import instance_service

    return instance_service.tasks_of_instance(db, instance_id)


def actions_of(db: Session, instance_id: int) -> list[ApprovalAction]:
    return (
        db.query(ApprovalAction)
        .filter(ApprovalAction.instance_id == instance_id)
        .order_by(ApprovalAction.id.asc())
        .all()
    )


def task_out(db: Session, task: ApprovalTask) -> dict:
    return {
        "id": task.id,
        "instance_id": task.instance_id,
        "node_seq": task.node_seq,
        "node_name": task.node_name,
        "order_no": task.order_no,
        "assignee_employee_id": task.assignee_employee_id,
        "assignee_name": _name_of(db, task.assignee_employee_id),
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, ""),
        "due_at": task.due_at,
        "decided_at": task.decided_at,
    }


def action_out(db: Session, action: ApprovalAction) -> dict:
    """Một dòng dấu vết, đã dựng sẵn CÂU đọc được cho bản in."""
    return {
        "id": action.id,
        "node_seq": action.node_seq,
        "node_name": action.node_name,
        "action": action.action,
        "action_label": ACTION_LABELS.get(action.action, ""),
        "actor_name": _name_of(db, action.actor_employee_id),
        "on_behalf_of_name": _name_of(db, action.on_behalf_of_id),
        "delegation_id": action.delegation_id,
        "comment": action.comment,
        "created_at": action.created_at,
        "sentence": audit_sentence(db, action),
    }


def audit_sentence(db: Session, action: ApprovalAction) -> str:
    """Câu cho BẢN IN dấu vết (I20).

    *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là
    một tờ giấy in ra được, không phải một ảnh chụp màn hình"* — nên câu này
    dựng ở backend, để bản in trên web và bản xuất ra tệp không bao giờ lệch chữ.
    """
    ai = _name_of(db, action.actor_employee_id) or "Hệ thống"
    task = ACTION_LABELS.get(action.action, "")

    if action.on_behalf_of_id and action.delegation_id:
        on_behalf_name = _name_of(db, action.on_behalf_of_id)
        return f"{ai} {task.lower()} thay {on_behalf_name} theo ủy quyền số {action.delegation_id}"
    if action.on_behalf_of_id:
        return f"{task}: {_name_of(db, action.on_behalf_of_id)} → {ai}"
    return f"{ai} — {task}"


def delegation_out(db: Session, row: Delegation) -> dict:
    return {
        "id": row.id,
        "from_employee_id": row.from_employee_id,
        "from_name": _name_of(db, row.from_employee_id),
        "to_employee_id": row.to_employee_id,
        "to_name": _name_of(db, row.to_employee_id),
        "entity": row.entity,
        "from_date": row.from_date,
        "to_date": row.to_date,
        "is_active": row.is_active,
        "reason": row.reason,
    }
