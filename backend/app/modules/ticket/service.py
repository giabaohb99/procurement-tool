from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Ticket, TicketMessage

ENTITY = "ticket"
FILTERABLE = ["code", "subject", "status", "priority", "department"]

# Trạng thái phiếu hỗ trợ
STATUSES = ("open", "in_progress", "answered", "closed")
STATUS_LABELS = {
    "open": "Mới", "in_progress": "Đang xử lý",
    "answered": "Đã trả lời", "closed": "Đã đóng",
}
PRIORITIES = ("low", "normal", "high", "urgent")
PRIORITY_LABELS = {"low": "Thấp", "normal": "Trung bình", "high": "Cao", "urgent": "Khẩn"}


def get_ticket(db: Session, tid: int) -> Ticket:
    o = db.get(Ticket, tid)
    if not o:
        raise HTTPException(404, "Không tìm thấy phiếu hỗ trợ")
    return o


def messages_of(db: Session, tid: int):
    return (db.query(TicketMessage).filter(TicketMessage.ticket_id == tid)
            .order_by(TicketMessage.id.asc()).all())


def _gen_code(db: Session) -> str:
    ddmmyy = datetime.now().strftime("%d%m%y")
    prefix = f"TK{ddmmyy}"
    mx = 0
    for (c,) in db.query(Ticket.code).filter(Ticket.code.like(prefix + "%")).all():
        suf = (c or "")[len(prefix):]
        if suf.isdigit():
            mx = max(mx, int(suf))
    return f"{prefix}{mx + 1:02d}"


def _register_files(db: Session, entity: str, entity_id: int, file_ids, user_id: int):
    """Gắn các file đã upload trước (file_id) vào entity — tái dùng bảng đính kèm chung."""
    if not file_ids:
        return
    from app.modules.attachment.model import FileLink, StoredFile
    for fid in file_ids:
        if not db.get(StoredFile, fid):
            continue
        db.add(FileLink(file_id=fid, entity=entity, entity_id=entity_id,
                        created_by=user_id, updated_by=user_id))
    db.commit()


def create_ticket(db: Session, data, user_id: int, requester_emp_id: int = 0) -> Ticket:
    priority = data.priority if data.priority in PRIORITIES else "normal"
    t = Ticket(
        code=_gen_code(db), subject=(data.subject or "").strip(),
        department=(data.department or "").strip(), priority=priority,
        status="open", company_id=data.company_id or 0,
        requester_id=requester_emp_id or 0,
        origin_url=(getattr(data, "origin_url", "") or "")[:500],
        created_by=user_id, updated_by=user_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    # Tin nhắn đầu tiên = nội dung mô tả của người gửi
    if (data.body or "").strip():
        db.add(TicketMessage(ticket_id=t.id, body=data.body.strip(), is_staff=False,
                             created_by=user_id, updated_by=user_id))
        db.commit()
    _register_files(db, ENTITY, t.id, getattr(data, "file_ids", None) or [], user_id)
    record(db, user_id, ENTITY, t.id, "create")
    return t


def update_ticket(db: Session, tid: int, data, user_id: int) -> Ticket:
    t = get_ticket(db, tid)
    if t.status == "closed":
        raise HTTPException(400, "Phiếu đã đóng — không sửa được")
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "priority" and v not in PRIORITIES:
            continue
        setattr(t, k, (v or "").strip() if isinstance(v, str) else v)
    t.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, tid, "update")
    db.refresh(t)
    return t


def add_message(db: Session, tid: int, body: str, user_id: int, is_staff: bool,
                file_ids=None) -> TicketMessage:
    t = get_ticket(db, tid)
    body = (body or "").strip()
    if not body and not file_ids:
        raise HTTPException(400, "Nội dung trả lời trống")
    m = TicketMessage(ticket_id=tid, body=body, is_staff=is_staff,
                      created_by=user_id, updated_by=user_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    _register_files(db, "ticket_message", m.id, file_ids or [], user_id)
    # Tự chuyển trạng thái theo người trả lời
    if is_staff:
        t.status = "answered"
        t.closed_at = None
    else:
        if t.status in ("answered", "closed"):
            t.status = "in_progress"
            t.closed_at = None
    t.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, tid, "reply")
    return m


def assign(db: Session, tid: int, assignee_id: int, user_id: int) -> Ticket:
    """Nhóm Hỗ trợ nhận phiếu (assignee_id = user) hoặc trả phiếu về hàng chờ (0).
    Nhận phiếu mà phiếu còn 'Mới' thì chuyển luôn sang 'Đang xử lý' cho khỏi phải bấm 2 lần."""
    t = get_ticket(db, tid)
    t.assignee_id = assignee_id or 0
    if assignee_id and t.status == "open":
        t.status = "in_progress"
    t.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, tid, "assign" if assignee_id else "unassign")
    db.refresh(t)
    return t


def set_status(db: Session, tid: int, status: str, user_id: int,
               assignee_id: int | None = None) -> Ticket:
    if status not in STATUSES:
        raise HTTPException(400, "Trạng thái không hợp lệ")
    t = get_ticket(db, tid)
    t.status = status
    t.closed_at = datetime.now() if status == "closed" else None
    if assignee_id is not None:
        t.assignee_id = assignee_id
    t.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, tid, status)
    db.refresh(t)
    return t
