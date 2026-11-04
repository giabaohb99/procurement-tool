"""NỐI PHIẾU NGHỈ BÙ VÀO BỘ MÁY DUYỆT DÙNG CHUNG (duoc-CR-715 C). Khuôn của `approval_bridge` (đơn nghỉ).

    approved  →  cộng `days` vào `comp_days` (loại đã chốt lúc gửi, năm = max(năm đi làm, năm nay)), phiếu Đã duyệt
    rejected / returned / withdrawn  →  chỉ đổi trạng thái (phiếu không giữ chỗ gì)

Cờ "Bật bộ máy duyệt" của entity TẮT, hoặc chưa khai luồng → phiếu vẫn vào *Chờ duyệt* với `approval_instance_id = 0`
và người có quyền `leave_comp_request.approve` duyệt thẳng (`/approve`) — cùng đường lùi với đơn nghỉ.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.approval import entity_hooks, flow_service, instance_service
from app.modules.approval.entity_hooks import HookVeto

from . import comp_request_service
from .comp_request_model import LeaveCompRequest
from .constants import LeaveCompStatus

ENTITY = comp_request_service.ENTITY


def entity_context(obj: LeaveCompRequest) -> dict:
    """Bối cảnh chọn người duyệt / rẽ nhánh. `department_id` là của NGƯỜI đi làm."""
    return {"id": obj.id, "employee_id": obj.employee_id, "company_id": obj.company_id,
            "department_id": obj.department_id, "days": obj.days}


def is_enabled(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, request_id: int):
    return instance_service.running_instance(db, ENTITY, request_id)


def block_legacy_path(db: Session, obj: LeaveCompRequest) -> None:
    """Phiếu đang chạy trong luồng nhiều bước thì KHÔNG cho duyệt / từ chối thẳng (không đi vòng luồng).
    Đừng gọi ở đường HỦY — xem `approval_bridge.block_legacy_path`."""
    if running_instance(db, obj.id) is not None:
        raise HTTPException(400, "Phiếu này đang chạy trong luồng phê duyệt nhiều bước. "
                                 "Duyệt ở màn Phê duyệt, đừng bấm duyệt thẳng ở đây.")


def withdraw_running_approval(db: Session, obj: LeaveCompRequest, user, reason: str = "") -> None:
    """RÚT phiên duyệt đang chạy để phiếu hủy được (luật "đã có người ký thì không rút" nằm ở `action_service`)."""
    instance = running_instance(db, obj.id)
    if instance is None:
        return
    from app.modules.approval import action_service

    note = (reason or "").strip()
    action_service.withdraw(db, instance, getattr(user, "employee_id", 0) or 0, user.id,
                            f"Hủy phiếu nghỉ bù: {note}" if note else "Người nộp hủy phiếu nghỉ bù")


def cancel_request(db: Session, obj: LeaveCompRequest, reason: str, user) -> LeaveCompRequest:
    """HỦY: rút phiên duyệt (nếu còn) rồi hủy; phiếu đã duyệt thì trừ lại `comp_days` nếu còn đủ."""
    withdraw_running_approval(db, obj, user, reason)
    db.refresh(obj)
    return comp_request_service.cancel(db, obj, reason, user.id)


def start_approval(db: Session, obj: LeaveCompRequest, user) -> int:
    """Trình phiếu vào bộ máy. Trả id phiên, `0` khi cờ TẮT / không luồng nào áp."""
    if not is_enabled(db):
        return 0
    instance = instance_service.start(
        db, ENTITY, obj.id, entity_context(obj), submitter_employee_id=obj.employee_id, actor=user.id,
        entity_code=obj.code, entity_title=f"Phiếu nghỉ bù {obj.code} — {obj.days:g} ngày")
    return instance.id if instance is not None else 0


def _get(db: Session, request_id: int) -> LeaveCompRequest | None:
    obj = db.get(LeaveCompRequest, request_id)
    return obj if obj is not None and not obj.is_deleted else None


def approve_now(db: Session, obj: LeaveCompRequest, actor: int, error_cls=HTTPException) -> None:
    """DUYỆT thật: chiếm phiếu (Chờ duyệt → Đã duyệt, chốt `balance_year`) rồi cộng `comp_days` vào loại + năm đã chốt.

    `error_cls` = `HookVeto` khi gọi từ bộ máy duyệt (lỗi thường bị `fire` NUỐT → phiên "Đã duyệt" mà phiếu vẫn
    Chờ duyệt), `HTTPException` khi duyệt thẳng. Kiểm loại nhận ngày bù TRƯỚC khi chiếm.
    """
    try:
        comp_request_service.resolve_credit_type(db, obj)
    except HTTPException as error:
        raise error_cls(error.status_code, error.detail) from error
    year = max(obj.work_date.year, vn_today().year)
    if not comp_request_service.try_claim(
            db, obj, (LeaveCompStatus.PENDING,), LeaveCompStatus.APPROVED, balance_year=year,
            decided_at=datetime.now(), decision_note="", updated_by=actor):
        raise error_cls(409, comp_request_service.CONFLICT_MESSAGE)
    try:
        comp_request_service.grant_days(db, obj, actor)
    except Exception as error:   # noqa: BLE001 — đã chiếm phiếu: hỏng ở đây phải làm cả giao dịch cuộn lại
        raise error_cls(getattr(error, "status_code", 500),
                        getattr(error, "detail", "Không cộng được ngày nghỉ bù vào quỹ")) from error


def _on_approved(db: Session, request_id: int, instance) -> None:
    obj = _get(db, request_id)
    if obj is None:
        return
    db.refresh(obj)      # đọc trạng thái THẬT, không tin bản nhớ của phiên
    if obj.status == int(LeaveCompStatus.APPROVED):
        return
    approve_now(db, obj, instance.updated_by or 0, HookVeto)


def _set_status(db: Session, request_id: int, instance, status: LeaveCompStatus, default_reason: str) -> None:
    """Rút / từ chối / trả về từ bộ máy: chiếm Chờ duyệt → `status`. Thua (phiếu đã sang trạng thái khác) thì bỏ qua."""
    obj = _get(db, request_id)
    if obj is None:
        return
    comp_request_service.try_claim(
        db, obj, (LeaveCompStatus.PENDING,), status,
        decision_note=((getattr(instance, "finish_reason", "") or default_reason))[:500],
        decided_at=datetime.now(), updated_by=instance.updated_by or 0)


def _on_rejected(db: Session, request_id: int, instance) -> None:
    _set_status(db, request_id, instance, LeaveCompStatus.REJECTED, "Bị từ chối")


def _on_returned(db: Session, request_id: int, instance) -> None:
    _set_status(db, request_id, instance, LeaveCompStatus.RETURNED, "Trả về chỉnh sửa")


def _on_withdrawn(db: Session, request_id: int, instance) -> None:
    """Người nộp tự rút → về **Nháp** (không ai trả gì cho họ)."""
    _set_status(db, request_id, instance, LeaveCompStatus.DRAFT, "")


entity_hooks.register(ENTITY, on_approved=_on_approved, on_rejected=_on_rejected,
                      on_returned=_on_returned, on_withdrawn=_on_withdrawn)


def _context_by_id(db: Session, request_id: int) -> dict:
    obj = _get(db, request_id)
    return entity_context(obj) if obj else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def can_read_request(db: Session, request_id: int, user) -> bool:
    """Trong phạm vi dữ liệu, HOẶC đang có việc duyệt treo trên phiếu (như đơn nghỉ — CR-260)."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped
    from app.modules.approval import steps_service

    if get_scoped(db, LeaveCompRequest, ENTITY, request_id, user, get_perm_profile(db, user)) is not None:
        return True
    return steps_service.has_pending_task(db, ENTITY, request_id, getattr(user, "employee_id", 0) or 0)


entity_hooks.register_reader(ENTITY, can_read_request)
