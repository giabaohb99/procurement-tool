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
from .model import (ForumBoard, ForumBoardStatus, ForumModerationAction,
                    ForumPost, ForumPostStatus)

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
         comments: dict, images: dict, moderator: bool, hidden_reasons: dict,
         board_names: dict | None = None) -> dict:
    a = authors.get(p.created_by) or {}
    lk = likes.get(p.id) or {}
    return {
        "id": p.id, "body": p.body,
        # CR-261: FE chọn đường vẽ theo cột này (1 = HTML đã lọc), không ngửi chuỗi.
        "body_format": int(p.body_format or 0),
        "status": int(p.status), "audience": int(p.audience),
        "kind": int(p.kind),
        # F13a — thread trong box: title/prefix chỉ có nghĩa khi board_id > 0;
        # board_name để thẻ bài trên feed dẫn "đăng trong box X" (QĐ-D7b).
        "board_id": p.board_id or 0,
        "title": p.title or "",
        "prefix": int(p.prefix or 0),
        "board_name": (board_names or {}).get(p.board_id or 0, ""),
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
        # CR-206: cảm xúc kiểu Facebook — {kind: n} chỉ chứa kind có người bấm;
        # `my_reaction` = 0 khi người xem chưa bấm. JSON hóa key số thành chuỗi,
        # FE đọc qua Record<number, number> vẫn khớp.
        "my_reaction": lk.get("my_reaction", 0),
        "reactions": lk.get("reactions", {}),
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
    board_names = _board_names(db, [p.board_id for p in rows if p.board_id])
    return [_out(p, authors, user.id, likes, comments, images, moderator, hidden_reasons,
                 board_names)
            for p in rows]


def _board_names(db: Session, board_ids: list[int]) -> dict[int, str]:
    """{board_id: tên box} cho các bài trong trang — 1 query, thường rỗng."""
    from .model import ForumBoard
    ids = [i for i in set(board_ids) if i]
    if not ids:
        return {}
    return {b.id: b.name for b in
            db.query(ForumBoard).filter(ForumBoard.id.in_(ids)).all()}


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


@router.get("/posts/search")
def search_posts(q: str = Query("", max_length=255),
                 author_q: str = Query("", max_length=255),
                 company_id: int = Query(0, ge=0),
                 dept_id: int = Query(0, ge=0),
                 board_id: int = Query(0, ge=0),
                 status: int = Query(0, ge=0),
                 page: int = Query(1, ge=1),
                 per_page: int = Query(service.PAGE_SIZE, ge=1, le=50),
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tìm bài viết (CR-263) — mở cho MỌI người đăng nhập, kết quả tự lọc qua
    luật audience trong SQL nên người thường tìm gì cũng chỉ ra bài mình vốn
    được xem; quản trị thấy cả bài ẩn + lọc `status`. PHẢI khai TRƯỚC
    `GET /posts/{pid}` — khuôn static-trước-dynamic của `/posts/pinned`."""
    profile = get_perm_profile(db, user)
    rows, total = service.search_posts(db, user, profile, q=q, author_q=author_q,
                                       company_id=company_id, dept_id=dept_id,
                                       board_id=board_id, status=status,
                                       page=page, per_page=per_page)
    return success({"items": _pack(db, rows, user),
                    "total": total, "page": page, "per_page": per_page,
                    "has_more": page * per_page < total})


@router.get("/search/filters")
def list_search_filters(db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    """Danh sách công ty + phòng ban cho ô lọc màn tìm kiếm — lấy distinct từ
    chính bảng bài viết, không đụng grant danh mục của người thường."""
    return success(service.list_search_filter_options(db))


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
                               data.file_ids, data.kind,
                               board_id=data.board_id, title=data.title,
                               prefix=data.prefix, body_format=data.body_format)
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
def toggle_like(pid: int, data: schema.ReactionIn | None = None,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Bấm cảm xúc (CR-206) — không sinh chuông (D-Q6, cùng lý do CR-030).
    Body `{kind}` tùy chọn; thiếu hoặc `{}` = LIKE, giữ tương thích client cũ."""
    service.get_visible_post(db, user, pid)
    kind = data.kind if data else int(schema.ForumReactionKind.LIKE)
    return success(service.toggle_like(db, pid, user.id, kind))


@router.get("/posts/{pid}/likes")
def list_likes(pid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ai đã bày tỏ cảm xúc với bài — hiện khi bấm vào con số, kèm `kind` để FE lọc."""
    service.get_visible_post(db, user, pid)
    rows = service.reaction_users(db, pid)
    names = _authors(db, [u for u, _ in rows])
    return success([{"user_id": u, "name": (names.get(u) or {}).get("name", ""), "kind": k}
                    for u, k in rows])


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


@router.get("/moderation-logs")
def list_moderation_logs(page: int = Query(1, ge=1),
                         per_page: int = Query(service.PAGE_SIZE, ge=1, le=50),
                         db: Session = Depends(get_db),
                         user=Depends(require("forum_post", "read"))):
    """Nhật ký kiểm duyệt (CR-263) — bảng ghi từ F5, giờ mới có màn đọc.
    Mỗi dòng kèm nhãn bài (tiêu đề hoặc trích nội dung) + tên quản trị viên;
    bài REMOVED không mở được nữa nên FE dựa `post_status` mà tắt link."""
    rows, total = service.list_moderation_logs(db, page=page, per_page=per_page)
    posts = {}
    pids = [r.post_id for r in rows if r.post_id]
    if pids:
        posts = {p.id: p for p in
                 db.query(ForumPost).filter(ForumPost.id.in_(pids)).all()}
    actors = _authors(db, [r.created_by for r in rows])

    def label_post(p: ForumPost | None) -> str:
        if p is None:
            return ""
        if p.title:
            return p.title
        text = service.strip_html_text(p.body) if int(p.body_format or 0) else (p.body or "")
        return text[:120] or "(bài chỉ có ảnh/video)"

    items = []
    for r in rows:
        p = posts.get(r.post_id)
        a = actors.get(r.created_by) or {}
        items.append({"id": r.id, "post_id": r.post_id,
                      "post_label": label_post(p),
                      "post_status": int(p.status) if p else 0,
                      "action": int(r.action), "reason": r.reason,
                      "actor_id": r.created_by,
                      "actor_name": a.get("name", ""),
                      "created_at": r.created_at, "notified_at": r.notified_at})
    return success({"items": items, "total": total, "page": page,
                    "per_page": per_page, "has_more": page * per_page < total})


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


# ── Chuyên mục kiểu VOZ (F13a, QĐ-D7) ──────────────────────────────────────────
# Đọc chỉ đòi đăng nhập (đợt đầu box toàn PUBLIC — QĐ-D7a); CRUD cấu trúc đi
# cổng `forum_board` — grant riêng của `forum_admin`, tách khỏi kiểm duyệt bài.

@router.get("/boards")
def list_boards(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Cây nhóm → box kèm bộ đếm + khối bài-mới-nhất — màn «Diễn đàn» (F13b)."""
    groups = service.list_boards(db, user)
    # tra tên/avatar người viết cuối cho mọi khối bài-mới-nhất — 2 query cho cả cây
    last_blocks = [b["last_post"] for g in groups
                   for b in [g, *g["children"]] if b.get("last_post")]
    authors = _authors(db, [lp["last_user_id"] for lp in last_blocks])
    for lp in last_blocks:
        a = authors.get(lp["last_user_id"]) or {}
        lp["last_author_name"] = a.get("name", "")
        lp["last_author_avatar"] = a.get("avatar", "")
    return success(groups)


@router.get("/boards/highlights")
def list_board_highlights(db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    """Sidebar phải màn «Diễn đàn» (F13c): «Đang sôi nổi» (auto 7 ngày) +
    «Mới nhất». Khối «Nổi bật» FE gọi `GET /posts/pinned` sẵn có.

    PHẢI khai TRƯỚC nhóm route `/boards/{board_id}` — khuôn static-trước-dynamic
    (cùng lý do `GET /posts/pinned` đứng trước `GET /posts/{pid}`).
    Trả bản GỌN từng thread (không body/ảnh/reaction) — sidebar chỉ cần tiêu đề
    dẫn đường, phình bằng thẻ bài đầy đủ là trả dư dữ liệu cho mọi lần mở tab.
    """
    profile = get_perm_profile(db, user)
    trending, latest = service.list_highlight_threads(db, user, profile)
    threads = {p.id: p for p in [*trending, *latest]}
    comments = service.comment_count_map(db, list(threads))
    board_names = _board_names(db, [p.board_id for p in threads.values()])

    def slim(p: ForumPost) -> dict:
        return {"id": p.id, "title": p.title or "", "prefix": int(p.prefix or 0),
                "board_id": p.board_id or 0,
                "board_name": board_names.get(p.board_id or 0, ""),
                "comment_count": comments.get(p.id, 0),
                "created_at": p.created_at}

    return success({"trending": [slim(p) for p in trending],
                    "latest": [slim(p) for p in latest]})


def _get_visible_box(db: Session, user, board_id: int) -> ForumBoard:
    """Box đọc được: tồn tại, là box; ẩn thì chỉ admin thấy — 404 GỘP để người
    thường không dò ra box ẩn có thật hay không (cùng triết lý bài kín)."""
    board = db.get(ForumBoard, board_id)
    if board is None or board.parent_id is None:
        raise HTTPException(404, "Box không tồn tại")
    if (int(board.status) != int(ForumBoardStatus.ACTIVE)
            and not service.can_moderate(db, user)):
        raise HTTPException(404, "Box không tồn tại")
    return board


@router.get("/boards/{board_id}/threads")
def list_board_threads(board_id: int,
                       page: int = Query(1, ge=1),
                       per_page: int = Query(service.PAGE_SIZE, ge=1, le=50),
                       db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Danh sách thread của một box — phân trang số trang, sắp theo hoạt động
    cuối, thread ghim nổi lên đầu (F13a)."""
    board = _get_visible_box(db, user, board_id)
    profile = get_perm_profile(db, user)
    rows, total = service.list_board_threads(db, user, profile, board_id,
                                             page=page, per_page=per_page)
    items = _pack(db, rows, user)
    # cột «hoạt động cuối» của từng thread = max(lúc đăng, bình luận cuối) —
    # cùng công thức với thứ tự sắp ở service, thêm đúng 1 query cho cả trang.
    last_comments = service.last_comment_at_map(db, [p.id for p in rows])
    for item, p in zip(items, rows):
        last = last_comments.get(p.id)
        item["last_activity_at"] = last if last and last > p.created_at else p.created_at
    return success({
        "items": items,
        "total": total, "page": page, "per_page": per_page,
        "has_more": page * per_page < total,
        "board": {"id": board.id, "name": board.name, "icon": board.icon,
                  "description": board.description, "status": int(board.status)},
    })


@router.post("/boards")
def create_board(data: schema.BoardIn, db: Session = Depends(get_db),
                 user=Depends(require("forum_board", "create"))):
    """Tạo nhóm/box — cấu trúc chuyên mục do admin quyết thủ công (chốt 03/09)."""
    board = service.create_board(db, user, data)
    return success({"id": board.id}, "Đã tạo nhóm/box", 201)


@router.put("/boards/{board_id}")
def update_board(board_id: int, data: schema.BoardIn, db: Session = Depends(get_db),
                 user=Depends(require("forum_board", "write"))):
    """Sửa tên/mô tả/icon/thứ tự/trạng thái — ẩn box là rút khỏi mắt, không xóa."""
    board = db.get(ForumBoard, board_id)
    if board is None:
        raise HTTPException(404, "Nhóm/box không tồn tại")
    service.update_board(db, user, board, data)
    return success({"id": board.id}, "Đã cập nhật nhóm/box")


@router.delete("/boards/{board_id}")
def delete_board(board_id: int, db: Session = Depends(get_db),
                 user=Depends(require("forum_board", "delete"))):
    """Xóa nhóm/box RỖNG — còn box con hay còn bài thì service chặn 400."""
    board = db.get(ForumBoard, board_id)
    if board is None:
        raise HTTPException(404, "Nhóm/box không tồn tại")
    service.delete_board(db, board)
    return success(None, "Đã xóa nhóm/box")
