"""Đưa dữ liệu duyệt ra giao diện — nhãn tiếng Việt do BACKEND cấp.

Giao diện không chép cứng nhãn trạng thái: thêm một trạng thái mà quên sửa một
trong hai chỗ thì màn hình hiện số thô, và người dùng đọc "3" thay vì "Từ chối".
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from . import flow_service
from .delegation_model import Delegation
from .flow_model import (APPROVER_KIND_LABELS, MULTI_MODE_LABELS,
                         NODE_KIND_LABELS, NO_APPROVER_LABELS, ROLE_LABELS,
                         SKIP_MODE_LABELS, ApprovalFlow, ApprovalNode)
from .instance_model import (ACTION_LABELS, INSTANCE_STATUS_LABELS,
                             TASK_STATUS_LABELS, ApprovalAction,
                             ApprovalInstance, ApprovalTask)


def _ten(db: Session, employee_id: int | None) -> str:
    if not employee_id:
        return ""
    employee = db.get(Employee, employee_id)
    return employee.full_name if employee else f"Nhân sự #{employee_id}"


def flow_out(db: Session, flow: ApprovalFlow, kem_buoc: bool = False) -> dict:
    data = {
        "id": flow.id,
        "entity": flow.entity,
        "code": flow.code,
        "name": flow.name,
        "description": flow.description,
        "version_no": flow.version_no,
        "is_active": flow.is_active,
        "company_id": flow.company_id,
        "priority": flow.priority,
        "condition": flow.condition,
        "node_count": len(flow_service.nodes_of(db, flow.id)),
    }
    if kem_buoc:
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
        "approver_names": _ten_nguoi_duyet(db, node),
        "multi_mode": node.multi_mode,
        "multi_mode_label": MULTI_MODE_LABELS.get(node.multi_mode, ""),
        "quorum_percent": node.quorum_percent,
        "condition": node.condition,
        "is_default_branch": node.is_default_branch,
        "skip_duplicate": node.skip_duplicate,
        "skip_duplicate_label": SKIP_MODE_LABELS.get(node.skip_duplicate, ""),
        "sla_hours": node.sla_hours,
        "fallback_employee_id": node.fallback_employee_id,
        "fallback_name": _ten(db, node.fallback_employee_id),
        "on_no_approver": node.on_no_approver,
        "on_no_approver_label": NO_APPROVER_LABELS.get(node.on_no_approver, ""),
    }


def _ten_nguoi_duyet(db: Session, node: ApprovalNode) -> str:
    """Chỉ dựng được tên khi bước chỉ đích danh người; các cách khác tính lúc chạy."""
    from .flow_model import APPROVER_EMPLOYEE

    if node.approver_kind != APPROVER_EMPLOYEE:
        return ""
    ids = [int(phan) for phan in (node.approver_ref or "").split(",") if phan.strip().isdigit()]
    return ", ".join(_ten(db, employee_id) for employee_id in ids)


def instance_out(db: Session, instance: ApprovalInstance, kem_chi_tiet: bool = False) -> dict:
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
        "started_by_name": _ten(db, instance.started_by_employee_id),
        "started_at": instance.started_at,
        "finished_at": instance.finished_at,
        "finish_reason": instance.finish_reason,
    }
    if kem_chi_tiet:
        data["tasks"] = [task_out(db, row) for row in instance_service_tasks(db, instance.id)]
        data["actions"] = [action_out(db, row) for row in actions_of(db, instance.id)]
        data["steps"] = [
            {"seq": node.seq, "name": node.name, "branch_key": node.branch_key}
            for node in flow_service.cac_buoc(instance.flow_snapshot)
        ]
    return data


def instance_service_tasks(db: Session, instance_id: int) -> list[ApprovalTask]:
    from . import instance_service

    return instance_service.viec_cua_phien(db, instance_id)


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
        "assignee_name": _ten(db, task.assignee_employee_id),
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
        "actor_name": _ten(db, action.actor_employee_id),
        "on_behalf_of_name": _ten(db, action.on_behalf_of_id),
        "delegation_id": action.delegation_id,
        "comment": action.comment,
        "created_at": action.created_at,
        "sentence": cau_dau_vet(db, action),
    }


def cau_dau_vet(db: Session, action: ApprovalAction) -> str:
    """Câu cho BẢN IN dấu vết (I20).

    *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là
    một tờ giấy in ra được, không phải một ảnh chụp màn hình"* — nên câu này
    dựng ở backend, để bản in trên web và bản xuất ra tệp không bao giờ lệch chữ.
    """
    ai = _ten(db, action.actor_employee_id) or "Hệ thống"
    viec = ACTION_LABELS.get(action.action, "")

    if action.on_behalf_of_id and action.delegation_id:
        thay = _ten(db, action.on_behalf_of_id)
        return f"{ai} {viec.lower()} thay {thay} theo ủy quyền số {action.delegation_id}"
    if action.on_behalf_of_id:
        return f"{viec}: {_ten(db, action.on_behalf_of_id)} → {ai}"
    return f"{ai} — {viec}"


def delegation_out(db: Session, row: Delegation) -> dict:
    return {
        "id": row.id,
        "from_employee_id": row.from_employee_id,
        "from_name": _ten(db, row.from_employee_id),
        "to_employee_id": row.to_employee_id,
        "to_name": _ten(db, row.to_employee_id),
        "entity": row.entity,
        "from_date": row.from_date,
        "to_date": row.to_date,
        "is_active": row.is_active,
        "reason": row.reason,
    }
