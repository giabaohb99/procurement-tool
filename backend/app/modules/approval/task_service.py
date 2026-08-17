"""VIỆC CỦA TÔI (I17) và nhắc hạn (I18).

Màn "Việc của tôi" là màn được mở nhiều nhất của cả hệ — mỗi lần có người mở
trang chủ. Truy vấn ở đây phải bám đúng chỉ mục
`INDEX(assignee_employee_id, status)` của `tab_approval_task`.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from . import delegation_service, serializer
from .instance_model import (ACTION_ESCALATE, INSTANCE_OPEN_STATUSES,
                             TASK_PENDING, ApprovalInstance, ApprovalTask)


def viec_cua_toi(db: Session, employee_id: int, entity: str = "") -> list[dict]:
    """Mọi thứ đang chờ một người — của cả văn thư lẫn thu mua, gom một chỗ.

    Gồm hai nguồn: việc của chính họ, và việc họ được **ủy quyền bấm thay**.
    Bỏ nguồn thứ hai thì người nhận ủy quyền không thấy việc mình phải làm, và
    ủy quyền thành ra vô dụng đúng lúc cần nhất (người kia đang đi vắng).
    """
    if not employee_id:
        return []

    nguoi_can_lam = {employee_id}
    uy_quyen_theo_nguoi: dict[int, int] = {}
    for row in delegation_service.nguoi_uy_quyen_cho(db, employee_id, entity or ""):
        nguoi_can_lam.add(row.from_employee_id)
        uy_quyen_theo_nguoi[row.from_employee_id] = row.id

    query = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_employee_id.in_(nguoi_can_lam),
                ApprovalTask.status == TASK_PENDING)
    )
    #  ⚠️ KHÔNG dùng `.nulls_last()`: MySQL 8 không hiểu cú pháp `NULLS LAST` và
    #  ném lỗi ngay ở câu truy vấn — mà bài kiểm chạy trên SQLite thì lại chấp
    #  nhận, nên lỗi này chỉ lộ ra khi gọi thật. `due_at IS NULL` xếp trước cho
    #  cùng kết quả và chạy trên cả hai.
    tasks = query.order_by(ApprovalTask.due_at.is_(None), ApprovalTask.due_at.asc(),
                           ApprovalTask.id.asc()).all()
    if not tasks:
        return []

    phien = {
        row.id: row for row in
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.id.in_({task.instance_id for task in tasks}))
        .all()
    }

    bay_gio = datetime.now()
    ket_qua = []
    for task in tasks:
        instance = phien.get(task.instance_id)
        #  Phiên đã đóng mà việc còn treo là dữ liệu lệch — đừng bày ra, người
        #  dùng bấm vào không làm được gì.
        if instance is None or instance.status not in INSTANCE_OPEN_STATUSES:
            continue
        if entity and instance.entity != entity:
            continue

        dong = serializer.task_out(db, task)
        dong.update({
            "entity": instance.entity,
            "entity_id": instance.entity_id,
            "entity_code": instance.entity_code,
            "entity_title": instance.entity_title,
            "started_by_name": serializer._ten(db, instance.started_by_employee_id),
            "instance_status": instance.status,
            #  Bấm thay ai — hiện thẳng trên dòng để người dùng biết mình đang
            #  làm việc của người khác trước khi bấm, không phải sau.
            "on_behalf_of_id": (task.assignee_employee_id
                                if task.assignee_employee_id != employee_id else None),
            "on_behalf_of_name": (serializer._ten(db, task.assignee_employee_id)
                                  if task.assignee_employee_id != employee_id else ""),
            "delegation_id": uy_quyen_theo_nguoi.get(task.assignee_employee_id),
            "is_overdue": bool(task.due_at and task.due_at < bay_gio),
        })
        ket_qua.append(dong)
    return ket_qua


def dem_viec_cua_toi(db: Session, employee_id: int) -> int:
    """Con số cho chuông/huy hiệu — đếm bằng chính hàm trên để hai chỗ không lệch."""
    return len(viec_cua_toi(db, employee_id))


def viec_qua_han(db: Session, gio: int = 0) -> list[ApprovalTask]:
    """I18 — việc quá hạn, dùng cho tác vụ nền nhắc và leo cấp."""
    bay_gio = datetime.now()
    return (
        db.query(ApprovalTask)
        .filter(ApprovalTask.status == TASK_PENDING,
                ApprovalTask.due_at.isnot(None),
                ApprovalTask.due_at < bay_gio)
        .order_by(ApprovalTask.due_at.asc())
        .all()
    )


def danh_dau_da_nhac(db: Session, task: ApprovalTask) -> None:
    """Đã nhắc rồi thì thôi — nhắc lại mỗi lần chạy tác vụ nền là spam, và
    người ta tắt thông báo, rồi bỏ lỡ cả những cái quan trọng."""
    task.reminded_at = datetime.now()
    db.flush()


def leo_cap(db: Session, task: ApprovalTask, len_employee_id: int, actor: int) -> None:
    """I18 — quá lâu thì đẩy lên cấp trên, ghi rõ vào dấu vết."""
    from . import instance_service

    instance = db.get(ApprovalInstance, task.instance_id)
    nguoi_cu = task.assignee_employee_id
    task.assignee_employee_id = len_employee_id
    task.escalated_at = datetime.now()
    task.updated_by = actor

    instance_service.ghi_dau_vet(
        db, instance, ACTION_ESCALATE, actor, node_seq=task.node_seq,
        node_name=task.node_name, task_id=task.id,
        actor_employee_id=len_employee_id, on_behalf_of_id=nguoi_cu,
        comment="Quá hạn duyệt — chuyển lên cấp trên",
    )
    db.flush()
