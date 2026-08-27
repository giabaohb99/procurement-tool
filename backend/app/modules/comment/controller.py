from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.response import success

from . import schema, service
from .model import Comment

router = APIRouter(prefix="/api/comments", tags=["comment"])


def _authors(db: Session, ids: list[int]) -> dict:
    """Tên + ảnh + MÃ NHÂN SỰ của người viết — gom 2 query cho cả luồng, không hỏi từng dòng."""
    from app.modules.employee.model import Employee
    from app.modules.notification.service import get_user_display_name
    from app.modules.user.model import User
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    users = db.query(User).filter(User.id.in_(ids)).all()
    emp_ids = [u.employee_id for u in users if u.employee_id]
    codes = {}
    if emp_ids:
        codes = {e.id: e.code or "" for e in
                 db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
    return {u.id: {"name": get_user_display_name(db, u),
                   "avatar": getattr(u, "avatar", "") or "",
                   # Mã NV giúp phân biệt hai người trùng tên — chuyện thường gặp ở tên tiếng Việt
                   "code": codes.get(u.employee_id or 0, "")}
            for u in users}


def _out(c: Comment, authors: dict, user_id: int, likes: dict, replies: dict | None = None,
         mentions: dict | None = None, files: dict | None = None) -> dict:
    a = authors.get(c.created_by) or {}
    lk = likes.get(c.id) or {}
    d = {
        "id": c.id, "entity": c.entity, "entity_id": c.entity_id, "body": c.body,
        "parent_id": c.parent_id,
        "author_id": c.created_by,
        "author_name": a.get("name", ""),
        "author_code": a.get("code", ""),
        "author_avatar": a.get("avatar", ""),
        "created_at": c.created_at,
        "can_delete": c.created_by == user_id,   # chỉ người viết tự xóa bình luận của mình
        "like_count": lk.get("count", 0),
        "liked": lk.get("liked", False),
        # Chip "@Tên" dựng từ ID, không phải từ chữ trong nội dung — xem model.
        "reply_to_user_id": c.reply_to_user_id,
        "reply_to_name": (authors.get(c.reply_to_user_id) or {}).get("name", ""),
        # Nội dung chứa thẻ "@[12]"; FE tra tên theo bảng này để dựng chip — nhờ vậy người
        # đổi tên thì bình luận cũ cũng hiện tên mới.
        "mentions": [{"user_id": u, "name": (authors.get(u) or {}).get("name", "")}
                     for u in (mentions or {}).get(c.id, [])],
        # Đính kèm của bài (CR-033); `is_image` do backend quyết để mọi nơi hiển thị giống nhau.
        "files": (files or {}).get(c.id, []),
    }
    if replies is not None:
        d["reply_count"] = replies.get(c.id, 0)
    return d


def _pack(db: Session, rows: list[Comment], user, with_reply_count: bool) -> list[dict]:
    ids = [c.id for c in rows]
    mentions = service.mention_map(db, ids)
    authors = _authors(db, [c.created_by for c in rows] + [c.reply_to_user_id for c in rows]
                       + [u for lst in mentions.values() for u in lst])
    likes = service.like_map(db, ids, user.id)
    files = service.file_map(db, ids)
    counts = service.reply_counts(db, ids) if with_reply_count else None
    return [_out(c, authors, user.id, likes, counts, mentions, files) for c in rows]


def _push(db: Session, uids: list[int], title: str, text: str, link: str, author_id: int,
          background_tasks) -> None:
    """Ghi chuông cho danh sách tài khoản còn hoạt động + đẩy Web Push nền (best-effort)."""
    from app.modules.notification.model import Notification
    from app.modules.user.model import User
    if not uids:
        return
    users = db.query(User).filter(User.id.in_(uids), User.is_active == True).all()  # noqa: E712
    if not users:
        return
    for u in users:
        db.add(Notification(user_id=u.id, title=title, body=text, link=link, created_by=author_id))
    db.commit()
    try:
        from app.core.database import SessionLocal
        from app.modules.push import service as push_service
        ids = [u.id for u in users]
        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal, ids, title, text, link)
        else:
            push_service.send_to_users(SessionLocal, ids, title, text, link)
    except Exception:
        pass


def _notify_new(db: Session, doc, label: str, route: str, c: Comment, user, background_tasks):
    """Hai loại chuông tách bạch: "được nhắc tên" và "bình luận mới".

    Người bị @ chỉ nhận chuông nhắc tên (không nhận thêm chuông chung) — một việc một chuông.
    Không gửi email workflow: bình luận phát sinh liên tục, đẩy email sẽ thành rác hộp thư.
    """
    from app.modules.notification.service import get_user_display_name

    code = getattr(doc, "code", "") or f"#{c.entity_id}"
    who = get_user_display_name(db, user)
    # Chuông là chữ thuần, không render được chip -> đổi thẻ "@[12]" thành "@Tên"
    content = service.strip_mentions(db, c.body)
    excerpt = content if len(content) <= 140 else content[:140].rstrip() + "…"
    # Bài chỉ có file thì chuông trống trơn, người nhận không biết có gì -> ghi rõ số tệp.
    file_count = len(service.file_map(db, [c.id]).get(c.id, []))
    if file_count:
        excerpt = (excerpt + " " if excerpt else "") + f"[đính kèm {file_count} tệp]"
    link = f"{route}/{c.entity_id}"

    # Người được nhắc = chip "đang trả lời ai" + mọi người bị @ giữa câu (CR-031)
    mentioned = [u for u in service.mention_map(db, [c.id]).get(c.id, []) if u != user.id]
    if c.reply_to_user_id and c.reply_to_user_id != user.id and c.reply_to_user_id not in mentioned:
        mentioned.insert(0, c.reply_to_user_id)
    if mentioned:
        _push(db, mentioned, f"{code} — Bạn được nhắc tên",
              f"{who} đã nhắc bạn trong {label} {code}: {excerpt}", link, user.id, background_tasks)

    uids = service.recipient_ids(db, doc, c.entity, c.entity_id, user.id, exclude=set(mentioned))
    _push(db, uids, f"{code} — Bình luận mới",
          f"{who} đã bình luận trong {label} {code}: {excerpt}", link, user.id, background_tasks)


@router.get("")
def list_comments(entity: str = Query(...), entity_id: int = Query(...),
                  limit: int = Query(service.PAGE_SIZE, ge=1, le=100),
                  before_id: int = Query(0, ge=0),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Một trang bình luận GỐC (cũ → mới) + số phản hồi của từng cái.

    Phản hồi KHÔNG trả kèm ở đây — bung ra mới gọi `/{id}/replies`, để một tranh luận dài
    không đẩy các bình luận khác xuống tận đáy.
    """
    service.resolve_doc(db, user, entity, entity_id)
    rows = service.list_roots(db, entity, entity_id, limit, before_id)
    total_roots = service.count_roots(db, entity, entity_id)
    oldest = rows[0].id if rows else before_id
    older = (db.query(Comment)
             .filter(Comment.entity == entity, Comment.entity_id == entity_id,
                     Comment.parent_id == 0, Comment.id < oldest).count()) if oldest else 0
    return success({
        "items": _pack(db, rows, user, with_reply_count=True),
        "total": service.count_all(db, entity, entity_id),   # cả gốc lẫn phản hồi — số cạnh tiêu đề
        "total_roots": total_roots,
        "older_count": older,        # còn bao nhiêu bình luận cũ hơn -> nhãn nút "Xem N ... trước"
        "oldest_id": oldest,         # con trỏ cho lần tải kế tiếp
    })


@router.get("/mentionable")
def list_mentionable(entity: str = Query(...), entity_id: int = Query(...),
                     q: str = Query("", max_length=50),
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gợi ý người để `@` khi đang gõ bình luận (CR-031).

    Chưa gõ chữ: chỉ người đang dính tới phiếu. Gõ rồi: tìm trong toàn bộ nhân sự đang hoạt động.
    """
    doc, _, _ = service.resolve_doc(db, user, entity, entity_id)
    return success(service.mentionable(db, doc, entity, entity_id, user.id, q))


@router.get("/{cid}/replies")
def list_replies(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    root = db.get(Comment, cid)
    if not root:
        raise HTTPException(404, "Không tìm thấy bình luận")
    service.resolve_doc(db, user, root.entity, root.entity_id)
    rows = service.list_replies(db, cid)
    return success(_pack(db, rows, user, with_reply_count=False))


@router.post("")
def create_comment(data: schema.CommentIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    doc, label, route = service.resolve_doc(db, user, data.entity, data.entity_id)
    c = service.create_comment(db, data.entity, data.entity_id, data.body, user.id,
                               data.parent_id, data.reply_to_user_id, data.file_ids)
    _notify_new(db, doc, label, route, c, user, background_tasks)
    return success(_pack(db, [c], user, with_reply_count=False)[0], "Đã gửi bình luận", 201)


@router.post("/{cid}/like")
def toggle_like(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Bấm thích / bỏ thích. Cố ý KHÔNG sinh thông báo — nếu không chuông sẽ rất ồn."""
    c = db.get(Comment, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy bình luận")
    service.resolve_doc(db, user, c.entity, c.entity_id)
    return success(service.toggle_reaction(db, cid, user.id))


@router.get("/{cid}/likes")
def list_likes(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ai đã thích bình luận này — hiện khi bấm vào con số."""
    c = db.get(Comment, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy bình luận")
    service.resolve_doc(db, user, c.entity, c.entity_id)
    uids = service.reaction_user_ids(db, cid)
    names = _authors(db, uids)
    return success([{"user_id": u, "name": (names.get(u) or {}).get("name", "")} for u in uids])


@router.delete("/{cid}")
def delete_comment(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Comment, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy bình luận")
    service.resolve_doc(db, user, c.entity, c.entity_id)
    # Chỉ người viết được xóa. Quản trị hệ thống giữ quyền dọn nội dung không phù hợp.
    if c.created_by != user.id and not user_has_permission(db, user, "user", "delete"):
        raise HTTPException(403, "Chỉ người viết mới xóa được bình luận này")
    n = service.delete_comment(db, c)
    msg = "Đã xóa bình luận" if n == 1 else f"Đã xóa bình luận và {n - 1} phản hồi"
    return success(None, msg)
