"""Mở rộng người duyệt cho phiếu đặt xe ĐANG CHỜ đã giao trước duoc-CR-706.

Trước CR-706, phiếu chọn sẵn "Người phê duyệt" chỉ giao việc cho ĐÚNG người được chọn. Từ CR-706 bước
"Người có quyền duyệt" giao cho người được chọn ∪ mọi người cùng quyền mà phạm vi phủ phiếu
(`approval/permission_approvers.resolve`). Phiếu đang chờ đã mở việc từ trước thì vẫn một người — hàm
này thêm việc cho những người còn thiếu ở CHẶNG ĐANG CHẠY.

Idempotent: ai đã có dòng việc (bất kỳ trạng thái) ở chặng đó thì bỏ qua, chạy lại không đẻ thêm. KHÔNG gửi
chuông / thư (người cùng quyền chỉ thấy việc ở "Việc chờ duyệt", đúng luật thông báo của CR-706). Chỉ đụng
phiếu có người được chọn và chặng đang chạy là bước kiểu "Người có quyền duyệt"; không sửa việc cũ nào.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.approval import approver_resolver, flow_service, instance_service
from app.modules.approval.flow_model import APPROVER_PERMISSION, MULTI_SEQUENTIAL
from app.modules.approval.instance_model import (ACTION_REASSIGN, INSTANCE_RUNNING, TASK_PENDING,
                                                 TASK_WAITING, ApprovalInstance, ApprovalTask)

from .approval_bridge import ENTITY, entity_context
from .model import BK_PENDING, VehicleBooking


def _expand_one(db: Session, instance: ApprovalInstance, booking: VehicleBooking) -> list[int]:
    """Thêm việc cho người còn thiếu ở chặng đang chạy của MỘT phiên. Trả employee_id vừa thêm."""
    subject = entity_context(booking)
    node = flow_service.step_of_stage(instance.flow_snapshot, instance.current_seq, subject)
    if node is None or node.approver_kind != APPROVER_PERMISSION:
        return []
    rows = [row for row in instance_service.tasks_of_instance(db, instance.id)
            if row.node_seq == instance.current_seq]
    pending = [row for row in rows if row.status == TASK_PENDING]
    if not pending:
        return []
    wanted = approver_resolver.resolve(db, node, subject, instance.started_by_employee_id)
    wanted = instance_service.exclude_submitter_ids(
        node.approver_kind, instance.started_by_employee_id, wanted)
    have = {row.assignee_employee_id for row in rows}
    missing = [employee_id for employee_id in wanted if employee_id not in have]
    if not missing:
        return []
    sequential = node.multi_mode == MULTI_SEQUENTIAL
    order_no = max(row.order_no for row in rows)
    for employee_id in missing:
        order_no += 1
        db.add(ApprovalTask(
            instance_id=instance.id, node_seq=instance.current_seq, node_name=node.name or "",
            order_no=order_no, assignee_employee_id=employee_id,
            #  Bước "lần lượt": người thêm xếp SAU, chờ tới lượt. Còn lại mở ngay như người được chọn.
            status=TASK_WAITING if sequential else TASK_PENDING,
            due_at=pending[0].due_at, created_by=0, updated_by=0))
    instance_service.record_audit(
        db, instance, ACTION_REASSIGN, 0, node_seq=instance.current_seq, node_name=node.name or "",
        comment="duoc-CR-706: thêm người cùng quyền duyệt đặt xe vào bước đang chờ")
    return missing


def expand_pending_approvers(db: Session, apply: bool = False) -> list[dict]:
    """Quét phiếu đặt xe Chờ duyệt đang chạy bộ máy; `apply=False` chỉ báo, không ghi.

    Trả `[{booking_id, code, added_employee_ids}]` cho mỗi phiếu có người cần thêm.
    """
    report: list[dict] = []
    instances = (db.query(ApprovalInstance)
                 .filter(ApprovalInstance.entity == ENTITY, ApprovalInstance.status == INSTANCE_RUNNING)
                 .order_by(ApprovalInstance.id.asc()).all())
    for instance in instances:
        booking = db.get(VehicleBooking, instance.entity_id)
        if (booking is None or booking.is_deleted or booking.status != BK_PENDING
                or not booking.first_approver_id):
            continue
        added = _expand_one(db, instance, booking)
        if added:
            report.append({"booking_id": booking.id, "code": booking.code, "added_employee_ids": added})
    if apply:
        db.commit()
    else:
        db.rollback()
    return report
