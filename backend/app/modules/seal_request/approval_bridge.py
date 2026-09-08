"""NỐI DUYỆT DẤU vào BỘ MÁY DUYỆT dùng chung (PHA 5).

Cổng 1 (Trưởng bộ phận) trước đây duyệt bằng ba nút cứng `approve/return/reject`.
Ở đây nó được nối vào bộ máy nhiều bước (`approval_flow`), **sau một cái cờ**
(`ApprovalSwitch` cho entity `seal_request`).

Giữ nguyên khi cờ TẮT hoặc chưa khai luồng nào: gửi duyệt vẫn đặt Chờ duyệt + báo
TBP; ba nút cũ vẫn chạy. Cờ BẬT và có luồng khớp thì `submit_for_approval` mở một
phiên; duyệt xong bộ máy gọi ngược `_on_approved/...`. Khi đó `block_legacy_path`
khóa ba nút cổng-1 để không có hai đường đổi trạng thái song song.

⚠️ CỔNG 2 (Văn thư đóng dấu) KHÔNG qua bộ máy — nó là bước vận hành thực tế sau khi
phiếu đã *Đã duyệt*; `block_legacy_path` chỉ áp cho nhóm endpoint cổng 1.

Mẫu: `app/modules/vehicle_booking/approval_bridge.py`.
"""
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from .model import SEAL_APPROVED, SEAL_DRAFT, SEAL_REJECTED, SEAL_RETURNED, SealRequest

ENTITY = "seal_request"


def entity_context(req: SealRequest) -> dict:
    """Bối cảnh phiếu cho điều kiện rẽ nhánh + chọn người duyệt «lấy từ ô»."""
    return {
        "id": req.id,
        "company_id": req.company_id,
        "department_id": req.department_id,
        "requester_id": req.requester_id,
    }


def is_enabled(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, req_id: int):
    return instance_service.running_instance(db, ENTITY, req_id)


def block_legacy_path(db: Session, req: SealRequest) -> None:
    """Khóa ba nút duyệt CỔNG 1 khi phiếu đang chạy trong bộ máy nhiều bước."""
    if running_instance(db, req.id) is not None:
        raise HTTPException(
            400,
            "Phiếu này đang chạy trong luồng duyệt nhiều bước — xử lý ở màn "
            "«Việc của tôi», không duyệt thẳng ở đây.",
        )


def _employee_id_of_user(db: Session, actor: int) -> int | None:
    from app.modules.user.model import User

    if not actor:
        return None
    row = db.query(User.employee_id).filter(User.id == actor).first()
    return row[0] if row and row[0] else None


def submit_for_approval(db: Session, req: SealRequest, actor: int):
    """Trình phiếu vào bộ máy. `None` = chưa khai luồng nào khớp → gọi đường cũ."""
    return instance_service.start(
        db, ENTITY, req.id, entity_context(req),
        submitter_employee_id=(_employee_id_of_user(db, actor) or req.requester_id or None),
        actor=actor,
        entity_code=req.code or "",
        entity_title=req.purpose or "",
    )


# ── Hàm chạy khi phiên duyệt kết thúc (bộ máy gọi ngược) ─────────────────────

def _write_log(db: Session, req_id: int, instance, action: str, message: str) -> None:
    from app.core.audit import record

    record(db, instance.updated_by or 0, ENTITY, req_id, action, message)


def _reason(instance, default: str) -> str:
    return (instance.finish_reason or "").strip() or default


def _actor(instance) -> SimpleNamespace:
    return SimpleNamespace(id=instance.updated_by or 0)


def _append_note(req: SealRequest, label: str, reason: str) -> None:
    from .service import _append_note as append

    append(req, label, reason)


def _on_approved(db: Session, req_id: int, instance) -> None:
    """Ký hết các bước cổng 1 → phiếu Đã duyệt (chờ Văn thư đóng dấu)."""
    from .notify import notify

    req = db.get(SealRequest, req_id)
    if req is None:
        return
    req.status = SEAL_APPROVED
    req.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, req_id, instance, "approve", "Xong hết các bước của luồng — đã duyệt")
    notify(db, "dd_approved", req, None, actor=_actor(instance))


def _on_rejected(db: Session, req_id: int, instance) -> None:
    from .notify import notify

    req = db.get(SealRequest, req_id)
    if req is None:
        return
    reason = _reason(instance, "Bị từ chối")
    req.status = SEAL_REJECTED
    _append_note(req, "Từ chối", reason)
    req.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, req_id, instance, "cancel", reason)
    notify(db, "dd_rejected", req, None, actor=_actor(instance), reason=reason)


def _on_returned(db: Session, req_id: int, instance) -> None:
    from .notify import notify

    req = db.get(SealRequest, req_id)
    if req is None:
        return
    reason = _reason(instance, "Bị trả về")
    req.status = SEAL_RETURNED
    _append_note(req, "Yêu cầu chỉnh sửa", reason)
    req.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, req_id, instance, "update", reason)
    notify(db, "dd_returned", req, None, actor=_actor(instance), reason=reason)


def _on_withdrawn(db: Session, req_id: int, instance) -> None:
    """Người nộp tự rút → phiếu VỀ NHÁP, sửa rồi gửi duyệt lại từ đầu."""
    req = db.get(SealRequest, req_id)
    if req is None:
        return
    req.status = SEAL_DRAFT
    req.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, req_id, instance, "update", _reason(instance, "Người nộp tự rút"))


entity_hooks.register(
    ENTITY,
    on_approved=_on_approved,
    on_rejected=_on_rejected,
    on_returned=_on_returned,
    on_withdrawn=_on_withdrawn,
)


def _context_by_id(db: Session, req_id: int) -> dict:
    req = db.get(SealRequest, req_id)
    return entity_context(req) if req else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def _can_read_request(db: Session, req_id: int, user) -> bool:
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped

    obj = get_scoped(db, SealRequest, ENTITY, req_id, user, get_perm_profile(db, user))
    return obj is not None and not obj.is_deleted


entity_hooks.register_reader(ENTITY, _can_read_request)
