from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import (apply_filters, apply_sort_from_request,
                                       pagination)
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .model import Ticket
from .schema import (AssignIn, MessageCreate, StatusIn, TicketCreate,
                     TicketUpdate)

router = APIRouter(prefix="/api/tickets", tags=["ticket"])


# ───────────────────────── helpers ─────────────────────────

def _is_handler(profile: dict) -> bool:
    """Nhóm Hỗ trợ / quản trị = có grant ticket với phạm vi dept|company|all (xử lý phiếu người khác).
    Người gửi thường chỉ có scope 'own' → không phải handler."""
    for g in profile.get("grants", []):
        p = g["perms"].get("ticket")
        if p and p.get("read") and p.get("scope") in ("dept", "company", "all"):
            return True
    return False


def _is_owner(t: Ticket, user) -> bool:
    if t.created_by == user.id:
        return True
    rid = getattr(user, "employee_id", 0) or 0
    return bool(rid and t.requester_id == rid)


def _user_info(db: Session, uid: int, cache: dict) -> dict:
    if uid in cache:
        return cache[uid]
    from app.modules.notification.service import get_user_display_name
    from app.modules.user.model import User
    u = db.get(User, uid) if uid else None
    name = get_user_display_name(db, u) if u else ""
    avatar = (u.avatar or "") if u else ""
    cache[uid] = {"name": name, "avatar": avatar}
    return cache[uid]


def _msg_files(db: Session, msg_ids: list[int]) -> dict:
    """Đính kèm của từng tin nhắn (entity 'ticket_message') — gom 1 query cho cả luồng."""
    if not msg_ids:
        return {}
    from app.modules.attachment.model import FileLink, StoredFile
    out: dict = {}
    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == "ticket_message", FileLink.entity_id.in_(msg_ids))
            .order_by(FileLink.id.asc()).all())
    for lk, f in rows:
        out.setdefault(lk.entity_id, []).append(
            {"id": lk.id, "file_id": f.id, "filename": f.filename, "url": f.url,
             "content_type": f.content_type, "size": f.size})
    return out


def _out(db: Session, t: Ticket, with_messages: bool = False) -> dict:
    cache: dict = {}
    asg = _user_info(db, t.assignee_id, cache)
    req = _user_info(db, t.created_by, cache)
    d = {
        "id": t.id, "code": t.code, "subject": t.subject, "department": t.department,
        "priority": t.priority, "priority_label": service.PRIORITY_LABELS.get(t.priority, t.priority),
        "status": t.status, "status_label": service.STATUS_LABELS.get(t.status, t.status),
        "company_id": t.company_id, "requester_id": t.requester_id,
        "assignee_id": t.assignee_id, "assignee_name": asg["name"], "assignee_avatar": asg["avatar"],
        "requester_name": req["name"], "requester_avatar": req["avatar"],
        "origin_url": t.origin_url,
        "created_at": t.created_at, "updated_at": t.updated_at, "closed_at": t.closed_at,
    }
    if with_messages:
        msgs = service.messages_of(db, t.id)
        fmap = _msg_files(db, [m.id for m in msgs])
        messages_out = []
        for m in msgs:
            aut = _user_info(db, m.created_by, cache)
            messages_out.append({
                "id": m.id, "body": m.body, "is_staff": m.is_staff,
                "author_id": m.created_by, "author_name": aut["name"], "author_avatar": aut["avatar"],
                "created_at": m.created_at, "files": fmap.get(m.id, []),
            })
        d["messages"] = messages_out
    return d


def _notify(db, users, title, body, link, creator_id, background_tasks=None, doc_code=""):
    """Ghi thông báo chuông + đẩy Web Push (best-effort) + email workflow (dev/UAT)."""
    from app.modules.notification.model import Notification
    from app.modules.user.model import User
    recipients, seen = [], set()
    for u in users:
        if u and u.id not in seen and u.id != creator_id:
            seen.add(u.id)
            recipients.append(u)
            db.add(Notification(user_id=u.id, title=title, body=body, link=link, created_by=creator_id))
    db.commit()
    if not seen:
        return
    try:
        from app.core.database import SessionLocal
        from app.modules.push import service as push_service
        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal, list(seen), title, body, link)
        else:
            push_service.send_to_users(SessionLocal, list(seen), title, body, link)
    except Exception:
        pass
    try:
        from app.modules.notification.service import _send_workflow_emails
        creator = db.query(User).filter(User.id == creator_id).first()
        creator_name = (creator.email if creator else "Hệ thống")
        _send_workflow_emails(db, background_tasks, recipients, title, body,
                              "ticket", doc_code, creator_name, "", "", False, link)
    except Exception:
        pass


def _support_users(db):
    """Người nhận việc hỗ trợ: CHỈ vai trò 'support'.
    Không lấy QL thu mua nữa — họ không phải người xử lý phiếu, gửi vào là spam.
    Fallback quản trị chỉ để phiếu không rơi vào hư không khi chưa gán ai vai trò Hỗ trợ."""
    from app.modules.notification.service import get_users_by_role_codes
    users = get_users_by_role_codes(db, ["support"])
    if not users:
        users = get_users_by_role_codes(db, ["admin", "ADMINISTRATOR"])
    return users


def _requester_users(db, t: Ticket):
    from app.modules.user.model import User
    return db.query(User).filter(User.id == t.created_by).all()


# ───────────────────────── routes ─────────────────────────

@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("ticket", "read"))):
    q = apply_filters(db.query(Ticket), Ticket, request, service.FILTERABLE)
    q = apply_scope(q, Ticket, "ticket", user, get_perm_profile(db, user))
    # mine=1: CHỈ phiếu do tôi gửi (tab "Yêu cầu hỗ trợ của tôi" ở trang cá nhân).
    # Cần vì nhóm Hỗ trợ có scope 'all' — không lọc thì tab cá nhân hiện phiếu của cả công ty.
    if (request.query_params.get("mine") or "") in ("1", "true"):
        q = q.filter(Ticket.created_by == user.id)
    # assignee=unassigned | me | <user_id>: bộ lọc của màn quản lý
    asg = (request.query_params.get("assignee") or "").strip()
    if asg == "unassigned":
        q = q.filter((Ticket.assignee_id == 0) | (Ticket.assignee_id.is_(None)))
    elif asg == "me":
        q = q.filter(Ticket.assignee_id == user.id)
    elif asg.isdigit():
        q = q.filter(Ticket.assignee_id == int(asg))
    total = q.count()
    q = apply_sort_from_request(q, Ticket, request, default=Ticket.id.desc())
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_out(db, x) for x in items]})


@router.get("/{tid}")
def get_(tid: int, db: Session = Depends(get_db), user=Depends(require("ticket", "read"))):
    prof = get_perm_profile(db, user)
    t = apply_scope(db.query(Ticket).filter(Ticket.id == tid), Ticket, "ticket", user, prof).first()
    if not t:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, t, with_messages=True))


@router.post("")
def create_(data: TicketCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("ticket", "create"))):
    if not (data.subject or "").strip():
        raise HTTPException(400, "Vui lòng nhập chủ đề")
    prof = get_perm_profile(db, user)
    company_id = data.company_id or (prof.get("company_id") or 0)
    data.company_id = company_id
    t = service.create_ticket(db, data, user.id, requester_emp_id=getattr(user, "employee_id", 0) or 0)
    _notify(db, _support_users(db),
            f"{t.code} — Phiếu hỗ trợ mới",
            f"Có phiếu hỗ trợ mới: {t.subject}",
            f"/tickets/{t.id}", user.id, background_tasks, doc_code=t.code)
    return success(_out(db, t, with_messages=True), "Đã tạo phiếu hỗ trợ", 201)


@router.patch("/{tid}")
def update_(tid: int, data: TicketUpdate, db: Session = Depends(get_db),
            user=Depends(require("ticket", "read"))):
    t = service.get_ticket(db, tid)
    prof = get_perm_profile(db, user)
    if not (_is_owner(t, user) or _is_handler(prof)):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    return success(_out(db, service.update_ticket(db, tid, data, user.id), with_messages=True), "Đã cập nhật")


@router.post("/{tid}/messages")
def reply_(tid: int, data: MessageCreate, background_tasks: BackgroundTasks,
           db: Session = Depends(get_db), user=Depends(require("ticket", "read"))):
    t = service.get_ticket(db, tid)
    prof = get_perm_profile(db, user)
    is_handler = _is_handler(prof)
    if not (_is_owner(t, user) or is_handler):
        raise HTTPException(403, "Không có quyền trả lời phiếu này")
    service.add_message(db, tid, data.body, user.id, is_staff=is_handler, file_ids=data.file_ids)
    db.refresh(t)
    # Báo phía còn lại
    if is_handler:
        _notify(db, _requester_users(db, t),
                f"{t.code} — Hỗ trợ đã trả lời",
                f"Phiếu hỗ trợ {t.code} của bạn vừa được phản hồi.",
                f"/tickets/{t.id}", user.id, background_tasks, doc_code=t.code)
    else:
        recips = _support_users(db)
        if t.assignee_id:
            from app.modules.user.model import User
            au = db.query(User).filter(User.id == t.assignee_id).all()
            recips = au or recips
        _notify(db, recips,
                f"{t.code} — Người gửi phản hồi",
                f"Người gửi vừa phản hồi phiếu hỗ trợ {t.code}.",
                f"/tickets/{t.id}", user.id, background_tasks, doc_code=t.code)
    return success(_out(db, t, with_messages=True), "Đã gửi trả lời", 201)


@router.post("/{tid}/assign")
def assign_(tid: int, data: AssignIn, background_tasks: BackgroundTasks,
            db: Session = Depends(get_db), user=Depends(require("ticket", "read"))):
    """Nhận phiếu / giao phiếu — chỉ nhóm Hỗ trợ."""
    prof = get_perm_profile(db, user)
    if not _is_handler(prof):
        raise HTTPException(403, "Chỉ nhóm Hỗ trợ mới nhận/giao được phiếu")
    t = service.assign(db, tid, data.assignee_id, user.id)
    # Giao cho NGƯỜI KHÁC thì phải báo họ; tự nhận phiếu thì _notify cũng tự loại người thao tác.
    if data.assignee_id and data.assignee_id != user.id:
        from app.modules.user.model import User
        _notify(db, db.query(User).filter(User.id == data.assignee_id).all(),
                f"{t.code} — Bạn được giao phiếu hỗ trợ",
                f"Bạn vừa được giao xử lý phiếu {t.code}: {t.subject}",
                f"/tickets/{t.id}", user.id, background_tasks, doc_code=t.code)
    return success(_out(db, t, with_messages=True),
                   "Đã nhận phiếu" if data.assignee_id else "Đã trả phiếu về hàng chờ")


@router.post("/{tid}/status")
def set_status_(tid: int, data: StatusIn, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db), user=Depends(require("ticket", "read"))):
    t = service.get_ticket(db, tid)
    prof = get_perm_profile(db, user)
    is_handler = _is_handler(prof)
    # Handler đổi mọi trạng thái + gán người xử lý; người gửi chỉ được đóng / mở lại phiếu của mình
    if not is_handler:
        if not _is_owner(t, user):
            raise HTTPException(403, "Không có quyền đổi trạng thái phiếu này")
        if data.status not in ("closed", "in_progress"):
            raise HTTPException(403, "Người gửi chỉ được đóng hoặc mở lại phiếu")
    assignee = data.assignee_id if is_handler else None
    t = service.set_status(db, tid, data.status, user.id, assignee_id=assignee)
    if data.status == "closed":
        # đóng bởi handler -> báo người gửi; đóng bởi người gửi -> báo nhóm hỗ trợ
        targets = _requester_users(db, t) if is_handler else _support_users(db)
        _notify(db, targets, f"{t.code} — Đã đóng phiếu hỗ trợ",
                f"Phiếu hỗ trợ {t.code} đã được đóng.",
                f"/tickets/{t.id}", user.id, background_tasks, doc_code=t.code)
    return success(_out(db, t, with_messages=True), "Đã cập nhật trạng thái")
