"""Diễn đàn F1 — API bài viết, prefix `/api/forum`.

Mọi endpoint chỉ đòi ĐĂNG NHẬP, không `require(...)`: người thường không có
grant `forum_post` (entity đó gác cổng kiểm duyệt của `forum_admin` — F5).
Ai thấy bài nào do `service.can_view`/`_visible_cond` quyết, ngay trong SQL.

Hợp đồng vào/ra chốt ở `doc/erp/dien-dan/02-lo-trinh-phase.md` (mục F1) —
FE dựng F2 theo bảng đó, đổi hình dạng trả về là phải sửa tài liệu trước.
"""
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Query)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import schema, service
from .model import ForumModerationAction, ForumPost, ForumPostStatus

router = APIRouter(prefix="/api/forum", tags=["forum"])


def _authors(db: Session, ids: list[int]) -> dict:
    """Tên + ảnh + mã nhân sự của tác giả — khuôn `comment/controller._authors`,
    gom 2 query cho cả trang."""
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
                   "code": codes.get(u.employee_id or 0, "")}
            for u in users}


def _out(p: ForumPost, authors: dict, user_id: int, likes: dict,
         comments: dict, images: dict, moderator: bool, hidden_reasons: dict) -> dict:
    a = authors.get(p.created_by) or {}
    lk = likes.get(p.id) or {}
    return {
        "id": p.id, "body": p.body, "status": int(p.status), "audience": int(p.audience),
        "kind": int(p.kind),
        "dept_id": p.dept_id, "company_id": p.company_id,
        "author_id": p.created_by,
        "author_name": a.get("name", ""),
        "author_code": a.get("code", ""),
        "author_avatar": a.get("avatar", ""),
        "created_at": p.created_at,
        "pinned_at": p.pinned_at,   # F9a: khác None = đang ghim, FE vẽ nhãn ghim
        "can_delete": p.created_by == user_id,   # tác giả xóa bài mình; admin đi đường F5
        "can_moderate": moderator,               # F5: FE mở menu ẩn/xóa/khôi phục
        "like_count": lk.get("count", 0),
        "liked": lk.get("liked", False),
        "comment_count": comments.get(p.id, 0),
        "images": images.get(p.id, []),
        # Nhãn lý do trên thẻ bài ẩn (F5) — chỉ tác giả/admin còn thấy bài này
        # nên không lộ gì thêm cho người ngoài.
        "hidden_reason": hidden_reasons.get(p.id, ""),
    }


def _pack(db: Session, rows: list[ForumPost], user) -> list[dict]:
    """Các map gom theo trang — tổng số query không đổi theo số bài (mục 4.4 của `01`)."""
    ids = [p.id for p in rows]
    authors = _authors(db, [p.created_by for p in rows])
    likes = service.like_map(db, ids, user.id)
    comments = service.comment_count_map(db, ids)
    images = service.image_map(db, ids)
    moderator = service.can_moderate(db, user)
    hidden_ids = [p.id for p in rows if int(p.status) == int(ForumPostStatus.HIDDEN)]
    hidden_reasons = service.hidden_reason_map(db, hidden_ids)
    return [_out(p, authors, user.id, likes, comments, images, moderator, hidden_reasons)
            for p in rows]


def _page(db: Session, user, rows_plus: list[ForumPost], limit: int) -> dict:
    """Đóng một trang feed: lấy dư 1 dòng để biết còn trang sau hay không."""
    has_more = len(rows_plus) > limit
    rows = rows_plus[:limit]
    return {
        "items": _pack(db, rows, user),
        "next_before_id": rows[-1].id if rows else 0,
        "has_more": has_more,
    }


@router.get("/posts")
def feed(limit: int = Query(service.PAGE_SIZE, ge=1, le=50),
         before_id: int = Query(0, ge=0),
         db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Bảng tin — thời gian thuần mới → cũ, con trỏ `before_id`, lọc audience trong SQL."""
    profile = get_perm_profile(db, user)
    rows = service.list_posts(db, user, profile, limit + 1, before_id)
    return success(_page(db, user, rows, limit))


@router.get("/posts/pinned")
def pinned_feed(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Bài đang ghim (F9a/CR-199) — dải đầu Bảng tin + tab «Thông báo».

    PHẢI khai TRƯỚC `GET /posts/{pid}` — không thì "pinned" bị nuốt vào `pid`
    (khuôn static-trước-dynamic của router văn thư).
    """
    profile = get_perm_profile(db, user)
    rows = service.list_pinned_posts(db, user, profile)
    return success(_pack(db, rows, user))


@router.get("/users/{author_id}/posts")
def user_feed(author_id: int,
              limit: int = Query(service.PAGE_SIZE, ge=1, le=50),
              before_id: int = Query(0, ge=0),
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Trang cá nhân = tủ bài viết (QĐ-D3). Trang của CHÍNH MÌNH thấy cả bài bị ẩn."""
    profile = get_perm_profile(db, user)
    rows = service.list_posts(db, user, profile, limit + 1, before_id, author_id=author_id)
    return success(_page(db, user, rows, limit))


@router.get("/posts/{pid}")
def get_post(pid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Một bài — đích đến của chuông thông báo (`/posts/:id`)."""
    post = service.get_visible_post(db, user, pid)
    return success(_pack(db, [post], user)[0])


@router.post("/posts")
def create_post(data: schema.PostIn, db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Đăng bài — lên feed ngay, không qua duyệt (QĐ-D1)."""
    profile = get_perm_profile(db, user)
    post = service.create_post(db, user, profile, data.body, data.audience,
                               data.file_ids, data.kind)
    return success(_pack(db, [post], user)[0], "Đã đăng bài", 201)


@router.delete("/posts/{pid}")
def delete_post(pid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xóa bài của CHÍNH MÌNH. Quản trị ẩn/xóa bài người khác là chuyện F5 —
    đường đó bắt buộc lý do + chuông cho tác giả (QĐ-D1), không đi cửa này."""
    post = db.get(ForumPost, pid)
    if not post:
        raise HTTPException(404, "Bài viết không tồn tại")
    if post.created_by != user.id:
        raise HTTPException(403, "Chỉ tác giả mới xóa được bài viết này")
    # Bài đã bị kiểm duyệt XÓA thì tác giả không xóa vật lý được nữa — dòng đó
    # và nhật ký của nó là chứng cứ đối soát (F5), xóa là mất dấu.
    if int(post.status) == int(ForumPostStatus.REMOVED):
        raise HTTPException(404, "Bài viết không tồn tại")
    service.delete_post(db, post)
    return success(None, "Đã xóa bài viết")


@router.post("/posts/{pid}/like")
def toggle_like(pid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Bấm thích / bỏ thích — không sinh chuông (D-Q6, cùng lý do CR-030)."""
    service.get_visible_post(db, user, pid)
    return success(service.toggle_like(db, pid, user.id))


@router.get("/posts/{pid}/likes")
def list_likes(pid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ai đã thích bài này — hiện khi bấm vào con số."""
    service.get_visible_post(db, user, pid)
    uids = service.reaction_user_ids(db, pid)
    names = _authors(db, uids)
    return success([{"user_id": u, "name": (names.get(u) or {}).get("name", "")} for u in uids])


# ── Kiểm duyệt (F5, QĐ-D1) — chỉ vai trò có grant `forum_post` đi được ─────────

def _notify_author(db: Session, log, post: ForumPost, title: str, body: str,
                   link: str, actor_id: int, background_tasks) -> None:
    """Chuông (+ web push nền) cho TÁC GIẢ bài bị kiểm duyệt — khuôn `_push`
    của comment/controller. Admin tự xử bài mình thì thôi (không tự báo mình).
    Ghi `notified_at` lên dòng nhật ký để đối soát "đã báo chưa" (F0)."""
    from datetime import datetime

    from app.modules.notification.model import Notification
    from app.modules.user.model import User

    if post.created_by == actor_id:
        return
    author = db.query(User).filter(User.id == post.created_by,
                                   User.is_active == True).first()  # noqa: E712
    if not author:
        return
    db.add(Notification(user_id=author.id, title=title, body=body, link=link,
                        created_by=actor_id))
    log.notified_at = datetime.now()
    db.commit()
    try:
        from app.core.database import SessionLocal
        from app.modules.push import service as push_service
        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal,
                                      [author.id], title, body, link)
        else:
            push_service.send_to_users(SessionLocal, [author.id], title, body, link)
    except Exception:
        pass


def _get_post_or_404(db: Session, pid: int) -> ForumPost:
    post = db.get(ForumPost, pid)
    if not post:
        raise HTTPException(404, "Bài viết không tồn tại")
    return post


@router.post("/posts/{pid}/hide")
def hide_post(pid: int, data: schema.ModerationIn, background_tasks: BackgroundTasks,
              db: Session = Depends(get_db),
              user=Depends(require("forum_post", "write"))):
    """Ẩn bài — lý do bắt buộc, tác giả nhận chuông kèm lý do (QĐ-D1).
    Bài ẩn biến khỏi feed mọi người nhưng tác giả và admin vẫn thấy kèm nhãn."""
    post = _get_post_or_404(db, pid)
    log = service.moderate(db, user, post, ForumModerationAction.HIDE, data.reason)
    _notify_author(db, log, post, f"#{post.id} — Bài viết bị ẩn",
                   f"Quản trị viên đã ẩn bài viết của bạn. Lý do: {log.reason}",
                   f"/forum/posts/{post.id}", user.id, background_tasks)
    return success(None, "Đã ẩn bài viết")


@router.post("/posts/{pid}/restore")
def restore_post(pid: int, background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db),
                 user=Depends(require("forum_post", "write"))):
    """Khôi phục bài đã ẩn — báo tác giả để họ khỏi tưởng bài vẫn bị ẩn."""
    post = _get_post_or_404(db, pid)
    log = service.moderate(db, user, post, ForumModerationAction.RESTORE, "")
    _notify_author(db, log, post, f"#{post.id} — Bài viết được khôi phục",
                   "Quản trị viên đã khôi phục bài viết của bạn.",
                   f"/forum/posts/{post.id}", user.id, background_tasks)
    return success(None, "Đã khôi phục bài viết")


@router.post("/posts/{pid}/remove")
def remove_post(pid: int, data: schema.ModerationIn, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db),
                user=Depends(require("forum_post", "delete"))):
    """Xóa bài (kiểm duyệt) — KHÁC tác giả tự xóa: chỉ đổi trạng thái REMOVED,
    giữ dòng + nhật ký để đối soát; bài biến khỏi mọi mắt qua API. Chuông không
    kèm link vì bài không còn mở được."""
    post = _get_post_or_404(db, pid)
    log = service.moderate(db, user, post, ForumModerationAction.REMOVE, data.reason)
    _notify_author(db, log, post, f"#{post.id} — Bài viết bị xóa",
                   f"Quản trị viên đã xóa bài viết của bạn. Lý do: {log.reason}",
                   "", user.id, background_tasks)
    return success(None, "Đã xóa bài viết")


# ── Ghim bài (F9a/CR-199) — cùng cổng quyền `forum_post.write` với ẩn/khôi phục;
# ghim là ĐỀ CAO chứ không phải chế tài nên không lý do, không nhật ký kiểm
# duyệt, không chuông.

@router.post("/posts/{pid}/pin")
def pin_post(pid: int, db: Session = Depends(get_db),
             user=Depends(require("forum_post", "write"))):
    """Ghim bài lên dải Thông báo — chỉ bài đang hiển thị (service chặn 400)."""
    post = _get_post_or_404(db, pid)
    service.set_post_pinned(db, user, post, True)
    return success(_pack(db, [post], user)[0], "Đã ghim bài viết")


@router.post("/posts/{pid}/unpin")
def unpin_post(pid: int, db: Session = Depends(get_db),
               user=Depends(require("forum_post", "write"))):
    """Bỏ ghim — bài vẫn nằm nguyên trên feed theo thời gian."""
    post = _get_post_or_404(db, pid)
    service.set_post_pinned(db, user, post, False)
    return success(_pack(db, [post], user)[0], "Đã bỏ ghim bài viết")
