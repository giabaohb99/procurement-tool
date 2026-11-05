"""NỐI PHIẾU THANH TOÁN NGHỈ PHÉP VÀO BỘ MÁY DUYỆT DÙNG CHUNG (duoc-CR-719). Khuôn của `comp_approval_bridge`.

    approved                        ->  chuyển ngày giữ chỗ sang đã thanh toán + sinh YCTT Nháp (`encashment_transitions.approve_now`)
    rejected / returned / withdrawn ->  trả giữ chỗ, đổi trạng thái (`release_and_set`)

Cờ "Bật bộ máy duyệt" của entity TẮT, hoặc chưa khai luồng -> phiếu vẫn vào *Chờ duyệt* với `approval_instance_id = 0`
và người có quyền `leave_encashment.approve` duyệt thẳng (`/approve`). Phiếu thanh toán nghỉ phép LUÔN chặn tự duyệt.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service
from app.modules.approval.entity_hooks import HookVeto

from . import encashment_service, encashment_transitions as transitions
from .constants import LeaveEncashmentStatus as S
from .encashment_model import LeaveEncashment

ENTITY = encashment_service.ENTITY


def entity_context(obj: LeaveEncashment) -> dict:
    """Bối cảnh chọn người duyệt / rẽ nhánh. `department_id` là của NGƯỜI nhận thanh toán. Không có số tiền."""
    return {"id": obj.id, "employee_id": obj.employee_id, "company_id": obj.company_id,
            "department_id": obj.department_id, "days": obj.days}


def is_enabled(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, request_id: int):
    return instance_service.running_instance(db, ENTITY, request_id)


def block_legacy_path(db: Session, obj: LeaveEncashment) -> None:
    """Phiếu đang chạy trong luồng nhiều bước thì KHÔNG cho duyệt / từ chối thẳng. Đừng gọi ở đường HỦY."""
    if running_instance(db, obj.id) is not None:
        raise HTTPException(400, "Phiếu này đang chạy trong luồng phê duyệt nhiều bước. "
                                 "Duyệt ở màn Phê duyệt, đừng bấm duyệt thẳng ở đây.")


def withdraw_running_approval(db: Session, obj: LeaveEncashment, user, reason: str = "") -> None:
    """RÚT phiên duyệt đang chạy để phiếu hủy được (luật "đã có người ký thì không rút" nằm ở `action_service`)."""
    instance = running_instance(db, obj.id)
    if instance is None:
        return
    from app.modules.approval import action_service

    note = (reason or "").strip()
    caller_emp = getattr(user, "employee_id", 0) or 0
    submitter_emp = instance.started_by_employee_id or 0
    #  L3: `action_service.withdraw` chỉ cho NGƯỜI TRÌNH rút. Người trình ở đây là chính nhân sự nhận thanh toán, còn
    #  người hủy thường là Nhân sự -> luôn 403. Đường HỦY đã qua cổng `leave_encashment.cancel` + phạm vi ở controller,
    #  nên người có quyền đó rút HỘ người trình (vẫn bị chặn nếu đã có người ký — luật của `withdraw`).
    on_behalf = bool(submitter_emp) and caller_emp != submitter_emp
    who = f"Người có quyền hủy (tài khoản #{user.id}) hủy hộ" if on_behalf else "Người nộp hủy"
    action_service.withdraw(db, instance, submitter_emp if on_behalf else caller_emp, user.id,
                            f"{who} phiếu thanh toán nghỉ phép: {note}" if note
                            else f"{who} phiếu thanh toán nghỉ phép")


def cancel_request(db: Session, obj: LeaveEncashment, reason: str, user) -> LeaveEncashment:
    """HỦY: rút phiên duyệt (nếu còn) rồi hủy; phiếu đã duyệt thì trả ngày nếu kế toán chưa đụng YCTT."""
    withdraw_running_approval(db, obj, user, reason)
    db.refresh(obj)
    return transitions.cancel(db, obj, reason, user.id)


def start_approval(db: Session, obj: LeaveEncashment, user) -> int:
    """Trình phiếu vào bộ máy. Trả id phiên, `0` khi cờ TẮT / không luồng nào áp."""
    if not is_enabled(db):
        return 0
    instance = instance_service.start(
        db, ENTITY, obj.id, entity_context(obj), submitter_employee_id=obj.employee_id, actor=user.id,
        entity_code=obj.code, entity_title=f"Thanh toán nghỉ phép {obj.code} — {obj.days:g} ngày")
    return instance.id if instance is not None else 0


def _get(db: Session, request_id: int) -> LeaveEncashment | None:
    obj = db.get(LeaveEncashment, request_id)
    return obj if obj is not None and not obj.is_deleted else None


def _on_approved(db: Session, request_id: int, instance) -> None:
    obj = _get(db, request_id)
    if obj is None:
        return
    db.refresh(obj)      # đọc trạng thái THẬT, không tin bản nhớ của phiên
    if obj.status == int(S.APPROVED):
        return
    transitions.approve_now(db, obj, instance.updated_by or 0, HookVeto)


def _set_status(db: Session, request_id: int, instance, status: S, default_reason: str) -> None:
    obj = _get(db, request_id)
    if obj is None:
        return
    transitions.release_and_set(
        db, obj, status, strict=False, actor=instance.updated_by or 0,
        decision_note=getattr(instance, "finish_reason", "") or default_reason)


def _on_rejected(db: Session, request_id: int, instance) -> None:
    _set_status(db, request_id, instance, S.REJECTED, "Bị từ chối")


def _on_returned(db: Session, request_id: int, instance) -> None:
    _set_status(db, request_id, instance, S.RETURNED, "Trả về chỉnh sửa")


def _on_withdrawn(db: Session, request_id: int, instance) -> None:
    """Người nộp tự rút -> về **Nháp** (trả giữ chỗ)."""
    _set_status(db, request_id, instance, S.DRAFT, "")


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

    if get_scoped(db, LeaveEncashment, ENTITY, request_id, user, get_perm_profile(db, user)) is not None:
        return True
    return steps_service.has_pending_task(db, ENTITY, request_id, getattr(user, "employee_id", 0) or 0)


entity_hooks.register_reader(ENTITY, can_read_request)
