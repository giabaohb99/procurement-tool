"""Loại việc · giờ ước lượng · giờ thực tế · kết quả của task (duoc-CR-656, D1b).

Tách khỏi `task_service.py` (đã gần 500 dòng). Hai nơi gọi vào đây: `create_task`/`update_task`
(`apply_effort_fields`, `on_status_changed`) và đường `POST /tasks/{id}/outcome` (`set_outcome`).

Luật:
- `actual_hours` và `outcome` chỉ có nghĩa khi task đã xong. Đặt khi chưa xong là 422.
- `outcome = 0` = chưa đánh giá. Task xong lần nữa thì phải được đánh giá lại: mọi lần đổi sang
  DONE xóa kết quả cũ. "Phải làm lại" GIỮ nguyên trong lúc task đã mở lại, để người làm thấy mình
  đang sửa theo lời chê; chuyển sang Hủy thì xóa.
- "Làm lại" để đếm thì D1a đọc từ lịch sử trạng thái (xong → mở lại), không cần cột đếm riêng.
- Người đặt kết quả: người TẠO task hoặc quản lý của dự án (khuôn xóa task).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.capability_codes import WorkTaskOutcome
from app.modules.work.audit_entity import AUDIT_TASK
from app.modules.work.membership_service import (CAN_EDIT, CAN_MANAGE, Actor,
                                                 block_if_archived, effective_role,
                                                 get_list_or_403)
from app.modules.work.model import WorkTaskStatus
from app.modules.work.task_model import WorkTask
from app.modules.work.task_type_service import require_active_type


def _hours(value):
    """`0` coi như xóa giờ (NULL) — "0 giờ" và "chưa khai" không phân biệt được ở đây."""
    return value if value else None


def apply_effort_fields(db: Session, t: WorkTask, data) -> None:
    """Gán `task_type_id`, `estimate_hours`, `actual_hours` từ schema (trường `None` = không đổi).

    Gọi SAU khi đã áp trạng thái, để một lượt PATCH vừa "xong" vừa nhập giờ thực tế vẫn hợp lệ.
    """
    type_id = getattr(data, "task_type_id", None)
    if type_id is not None and int(type_id) != int(t.task_type_id or 0):
        if type_id:
            require_active_type(db, int(type_id))
        t.task_type_id = int(type_id)

    estimate = getattr(data, "estimate_hours", None)
    if estimate is not None:
        t.estimate_hours = _hours(estimate)

    actual = getattr(data, "actual_hours", None)
    if actual is not None:
        if actual and int(t.status) != int(WorkTaskStatus.DONE):
            raise HTTPException(422, "Chỉ nhập giờ thực tế khi công việc đã hoàn thành")
        t.actual_hours = _hours(actual)


def on_status_changed(t: WorkTask, new_status: int) -> None:
    """Móc vào `task_service._apply_status`: giữ cột `outcome` khớp trạng thái."""
    if new_status == int(WorkTaskStatus.DONE):
        t.outcome = 0                      # xong lần nữa → đánh giá lại
    elif new_status == int(WorkTaskStatus.CANCELLED):
        t.outcome = 0
    elif int(t.outcome or 0) == int(WorkTaskOutcome.PASSED):
        t.outcome = 0                      # mở lại một việc đã "Đạt" thì kết quả cũ hết nghĩa


def set_outcome(db: Session, actor: Actor, task_id: int, outcome: int,
                background_tasks=None) -> dict:
    from app.modules.work import task_enrich, task_service  # nhập muộn: tránh vòng import

    if outcome not in (int(WorkTaskOutcome.PASSED), int(WorkTaskOutcome.REWORK)):
        raise HTTPException(422, "Kết quả chỉ nhận 1 (Đạt) hoặc 2 (Phải làm lại)")
    t = task_service.get_task_or_403(db, actor, task_id, CAN_EDIT)
    block_if_archived(get_list_or_403(db, actor, t.list_id, CAN_EDIT))
    if effective_role(db, actor.employee_id, t.list_id) > CAN_MANAGE and t.creator_employee_id != actor.employee_id:
        raise HTTPException(403, "Chỉ người giao việc hoặc quản lý dự án mới đánh giá được kết quả")
    if int(t.status) != int(WorkTaskStatus.DONE):
        raise HTTPException(422, "Chỉ đánh giá được khi công việc đã hoàn thành")

    if outcome == int(WorkTaskOutcome.REWORK):
        #  Mở lại TRƯỚC rồi mới đặt kết quả: `_apply_status` xóa `completed_at` và ghi lịch sử 2→1
        #  (dấu vết để D1a đếm số lần làm lại), còn "Phải làm lại" ở lại cho tới khi xong lần nữa.
        task_service._apply_status(db, actor, t, int(WorkTaskStatus.OPEN))
        t.outcome = int(WorkTaskOutcome.REWORK)
        note = "Đánh giá phải làm lại"
    else:
        t.outcome = int(WorkTaskOutcome.PASSED)
        note = "Đánh giá đạt"
    t.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, AUDIT_TASK, t.id, "update", f"{note}: {t.title}")
    if outcome == int(WorkTaskOutcome.REWORK):
        #  Mở lại vì phải làm lại = đổi trạng thái 2 -> 1: người làm phải biết (F-04).
        from app.modules.work import notify_service
        notify_service.notify_status_changed(db, actor, t, int(WorkTaskStatus.OPEN), background_tasks)
    return task_service._shape([t], task_enrich.collect(db, [t]))[0]
