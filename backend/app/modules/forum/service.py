"""Diễn đàn F1 — luật đối tượng xem, feed con trỏ, đăng/xóa bài, like.

Bê khuôn từ `comment/service.py` (CR-033): con trỏ `before_id` không OFFSET,
số đếm gom theo trang không cột đếm sẵn, gắn ảnh tải-trước-gắn-sau với đúng
điều kiện sở hữu. Chỗ NGHĨ MỚI duy nhất là `can_view`/`_visible_cond` — luật
audience mục 4.2 của `doc/erp/dien-dan/01`:

    status = published
    AND ( audience = public
       OR (audience = company AND company_id = :cty_nguoi_xem)
       OR (audience = dept    AND dept_id    = :phong_nguoi_xem)
       OR created_by = :nguoi_xem )

Người thường KHÔNG có grant RBAC trên `forum_post` — đừng gọi `apply_scope`
ở đây; entity đó chỉ gác cổng kiểm duyệt của `forum_admin`.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission

from .model import (ForumAudience, ForumModerationAction, ForumModerationLog,
                    ForumPost, ForumPostKind, ForumPostStatus, ForumReaction,
                    ForumReactionKind)

MAX_BODY = 10_000   # chữ thuần, không rich text (mục 3 của `01`)
PAGE_SIZE = 20
MAX_FILES = 10      # 10 tệp/bài — ảnh + video tính chung (trần MB/tệp ở FILE_POLICY)


def can_moderate(db: Session, user) -> bool:
    """`forum_admin` — người duy nhất có grant `forum_post.read` (xem seed.py)."""
    return user_has_permission(db, user, "forum_post", "read")


def _visible_cond(user, profile):
    """Điều kiện SQL "bài nào NGƯỜI THƯỜNG này được thấy" — lọc ở tầng DB,
    không lọc ở FE (bài không được xem thì không được rời máy chủ).

    Vế company/dept chỉ dựng khi hồ sơ CÓ pháp nhân/phòng ban: người chưa gắn
    (`company_id=0`) mà so bằng 0 sẽ khớp nhầm mọi bài đóng băng số 0 — cùng
    triết lý "thiếu dữ liệu thì chặn, không mở" của B-07.
    """
    clauses = [ForumPost.audience == int(ForumAudience.PUBLIC),
          ForumPost.created_by == user.id]   # tác giả luôn thấy bài mình
    if profile.get("company_id"):
        clauses.append(and_(ForumPost.audience == int(ForumAudience.COMPANY),
                       ForumPost.company_id == profile["company_id"]))
    if profile.get("dept_id"):
        clauses.append(and_(ForumPost.audience == int(ForumAudience.DEPT),
                       ForumPost.dept_id == profile["dept_id"]))
    return and_(ForumPost.status == int(ForumPostStatus.PUBLISHED), or_(*clauses))


def can_view(db: Session, user, post: ForumPost | None, profile: dict | None = None) -> bool:
    """Một bài — người này có được xem không. Cổng chung cho trang chi tiết,
    comment (`resolve_doc`) và đính kèm (`_check_forum`) — ba đường một luật.

    `REMOVED` biến khỏi mọi mắt qua API (giữ dòng trong DB để đối soát);
    bài `HIDDEN` chỉ tác giả và quản trị còn thấy (QĐ-D1).
    """
    if post is None:
        return False
    if int(post.status) == int(ForumPostStatus.REMOVED):
        return False
    if post.created_by == user.id:
        return True
    if can_moderate(db, user):
        return True
    if int(post.status) != int(ForumPostStatus.PUBLISHED):
        return False
    aud = int(post.audience)
    if aud == int(ForumAudience.PUBLIC):
        return True
    profile = profile or get_perm_profile(db, user)
    if aud == int(ForumAudience.COMPANY):
        return bool(post.company_id) and post.company_id == profile.get("company_id")
    if aud == int(ForumAudience.DEPT):
        return bool(post.dept_id) and post.dept_id == profile.get("dept_id")
    return False


def get_visible_post(db: Session, user, post_id: int) -> ForumPost:
    """Lấy một bài KÈM kiểm luật audience — 403 gộp "không tồn tại hoặc không
    được xem" để id đoán mò không dò ra được bài kín có thật hay không."""
    post = db.get(ForumPost, post_id)
    if not can_view(db, user, post):
        raise HTTPException(403, "Bài viết không tồn tại hoặc bạn không được xem")
    return post


# ── Feed ────────────────────────────────────────────────────────────────────────

def list_posts(db: Session, user, profile: dict, limit: int = PAGE_SIZE,
               before_id: int = 0, author_id: int = 0) -> list[ForumPost]:
    """Một trang bài, MỚI → CŨ (khác comment: feed đọc từ trên xuống).

    Con trỏ `before_id` = id nhỏ nhất đang hiện — bài mới chen vào giữa chừng
    không làm lệch trang, không lặp bài (mục 4.3 của `01`, cấm OFFSET).
    `author_id` là feed trang cá nhân: trang CHÍNH MÌNH thấy cả bài bị ẩn
    (kèm nhãn lý do ở F5); trang người khác vẫn nguyên luật audience.
    """
    q = db.query(ForumPost)
    if author_id:
        q = q.filter(ForumPost.created_by == author_id)
    if author_id == user.id and author_id:
        q = q.filter(ForumPost.status != int(ForumPostStatus.REMOVED))
    elif can_moderate(db, user):
        # quản trị bỏ điều kiện audience và thấy cả bài ẩn — phải thấy hết mới dọn được
        q = q.filter(ForumPost.status.in_([int(ForumPostStatus.PUBLISHED),
                                           int(ForumPostStatus.HIDDEN)]))
    else:
        q = q.filter(_visible_cond(user, profile))
    if before_id:
        q = q.filter(ForumPost.id < before_id)
    return q.order_by(ForumPost.id.desc()).limit(max(1, limit)).all()


# ── Ghim bài (F9a/CR-199) ──────────────────────────────────────────────────────

MAX_PINNED = 50   # trần phòng hờ — dải ghim mà tới đây là admin đang lạm dụng ghim


def list_pinned_posts(db: Session, user, profile: dict) -> list[ForumPost]:
    """Mọi bài ĐANG GHIM người này được thấy — dải đầu Bảng tin + tab «Thông báo».

    Vẫn nguyên luật audience: thông báo ghim phạm vi phòng ban thì phòng khác
    không thấy. Không con trỏ (ghim chỉ vài bài), sắp mốc ghim mới → cũ.
    """
    q = db.query(ForumPost).filter(ForumPost.pinned_at.isnot(None))
    if can_moderate(db, user):
        # admin thấy cả bài ghim đang bị ẩn (kèm nhãn) — thấy hết mới dọn được
        q = q.filter(ForumPost.status.in_([int(ForumPostStatus.PUBLISHED),
                                           int(ForumPostStatus.HIDDEN)]))
    else:
        q = q.filter(_visible_cond(user, profile))
    return (q.order_by(ForumPost.pinned_at.desc(), ForumPost.id.desc())
            .limit(MAX_PINNED).all())


def set_post_pinned(db: Session, user, post: ForumPost, pinned: bool) -> ForumPost:
    """Ghim / bỏ ghim một bài (quyền `forum_post.write` gác ở controller).

    Chỉ ghim được bài PUBLISHED — ghim bài ẩn là treo thông báo không ai đọc
    được; bài ghim sau đó bị ẩn/gỡ thì tự biến khỏi dải nhờ lọc status ở trên.
    Bỏ ghim thì trạng thái nào cũng cho (dọn dẹp không bị kẹt luật).
    """
    if pinned:
        if int(post.status) != int(ForumPostStatus.PUBLISHED):
            raise HTTPException(400, "Chỉ ghim được bài viết đang hiển thị")
        if post.pinned_at is None:
            post.pinned_at = datetime.now()
    else:
        post.pinned_at = None
    post.updated_by = user.id
    db.commit()
    db.refresh(post)
    return post


# ── Số đếm và dữ liệu kèm bài — mỗi loại đúng 1 query cho cả trang ─────────────

def like_map(db: Session, post_ids: list[int], user_id: int) -> dict[int, dict]:
    """{post_id: {"count", "liked", "my_reaction", "reactions"}} — khuôn `comment.like_map`.

    CR-206: đếm thêm theo TỪNG cảm xúc (`reactions` = {kind: n}, chỉ chứa kind
    có người bấm) và cảm xúc của chính người xem (`my_reaction`, 0 = chưa bấm).
    Giữ `count`/`liked` tổng để chỗ nào chỉ cần "có ai thích không" khỏi tự cộng.
    """
    ids = [i for i in post_ids if i]
    if not ids:
        return {}
    rows = (db.query(ForumReaction.post_id, ForumReaction.kind, func.count(ForumReaction.id))
            .filter(ForumReaction.post_id.in_(ids))
            .group_by(ForumReaction.post_id, ForumReaction.kind).all())
    reactions: dict[int, dict[int, int]] = {}
    for pid, kind, n in rows:
        reactions.setdefault(pid, {})[int(kind)] = n
    mine = {pid: int(kind) for pid, kind in
            db.query(ForumReaction.post_id, ForumReaction.kind)
            .filter(ForumReaction.post_id.in_(ids), ForumReaction.user_id == user_id).all()}
    return {pid: {"count": sum(reactions.get(pid, {}).values()),
                  "liked": pid in mine,
                  "my_reaction": mine.get(pid, 0),
                  "reactions": reactions.get(pid, {})} for pid in ids}


def comment_count_map(db: Session, post_ids: list[int]) -> dict[int, int]:
    """Số bình luận (cả gốc lẫn phản hồi) của từng bài — feed chỉ hiện SỐ,
    khối comment nạp khi mở bài (mục 5 của `01`)."""
    from app.modules.comment.model import Comment

    ids = [i for i in post_ids if i]
    if not ids:
        return {}
    rows = (db.query(Comment.entity_id, func.count(Comment.id))
            .filter(Comment.entity == "forum_post", Comment.entity_id.in_(ids))
            .group_by(Comment.entity_id).all())
    return {pid: n for pid, n in rows}


def image_map(db: Session, post_ids: list[int]) -> dict[int, list[dict]]:
    """{post_id: [ảnh/video]} — 1 query/trang, giữ thứ tự `sort_order` người đăng
    chọn. Video (D-Q3 chốt 27/08/2026) đi chung FileLink với ảnh, FE tách theo
    `content_type` để vẽ: ảnh vào lưới, video thành khối phát riêng."""
    from app.modules.attachment.model import FileLink, StoredFile

    ids = [i for i in post_ids if i]
    if not ids:
        return {}
    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == "forum_post", FileLink.entity_id.in_(ids))
            .order_by(FileLink.sort_order.asc(), FileLink.id.asc()).all())
    out: dict[int, list[dict]] = {}
    for lk, f in rows:
        out.setdefault(lk.entity_id, []).append({
            "link_id": lk.id, "file_id": f.id, "filename": f.filename, "url": f.url,
            # Bản nhẹ cho ô lưới feed — rỗng (tệp cũ / video) thì FE fallback `url`.
            "thumb_url": f.thumb_url,
            "content_type": f.content_type, "size": f.size,
        })
    return out


# ── Ghi ─────────────────────────────────────────────────────────────────────────

def create_post(db: Session, user, profile: dict, body: str, audience: int,
                file_ids: list[int] | None = None, kind: int = 0) -> ForumPost:
    """Đăng bài — không qua duyệt (QĐ-D1), `dept_id`/`company_id` ĐÓNG BĂNG
    theo hồ sơ tác giả lúc đăng (chuyển phòng thì bài cũ giữ ngữ cảnh cũ)."""
    body = (body or "").strip()
    file_ids = [int(i) for i in (file_ids or []) if i]
    try:
        post_kind = ForumPostKind(int(kind))
    except ValueError:
        raise HTTPException(400, f"Loại bài không hợp lệ: {kind}")
    # Bài đổi avatar (F10): ảnh là NHÂN VẬT CHÍNH — đúng 1 tấm (chính avatar
    # mới), caption có hay không tùy; thiếu ảnh thì dòng hệ thống thành nói suông.
    if post_kind == ForumPostKind.AVATAR_UPDATE and len(file_ids) != 1:
        raise HTTPException(400, "Bài đổi ảnh đại diện phải kèm đúng 1 ảnh")
    if not body and not file_ids:
        raise HTTPException(400, "Bài viết không được để trống")
    if len(body) > MAX_BODY:
        raise HTTPException(400, f"Bài viết tối đa {MAX_BODY} ký tự")
    if len(file_ids) > MAX_FILES:
        raise HTTPException(400, f"Mỗi bài đính tối đa {MAX_FILES} ảnh/video")
    try:
        aud = ForumAudience(int(audience))
    except ValueError:
        raise HTTPException(400, f"Đối tượng xem không hợp lệ: {audience}")
    # Chọn phạm vi hẹp mà hồ sơ chưa gắn chiều đó thì 400 — đóng băng số 0 vào
    # bài là tạo ra bài "phòng ban" không phòng nào thấy, kể cả không lộ cũng
    # là dữ liệu rác; bắt sửa hồ sơ nhân sự trước.
    if aud == ForumAudience.DEPT and not profile.get("dept_id"):
        raise HTTPException(400, "Hồ sơ nhân sự chưa gắn phòng ban — không đăng được bài phạm vi phòng ban")
    if aud == ForumAudience.COMPANY and not profile.get("company_id"):
        raise HTTPException(400, "Hồ sơ nhân sự chưa gắn pháp nhân — không đăng được bài phạm vi công ty")

    post = ForumPost(body=body, audience=int(aud), kind=int(post_kind),
                     dept_id=profile.get("dept_id") or 0,
                     company_id=profile.get("company_id") or 0,
                     created_by=user.id, updated_by=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    attach_images(db, post, file_ids, user.id)
    return post


def attach_images(db: Session, post: ForumPost, file_ids: list[int], user_id: int) -> int:
    """Gắn ảnh ĐÃ tải lên (`POST /api/attachments/upload-file`) vào bài vừa đăng.

    Cùng điều kiện sở hữu với `comment.attach_files`: chỉ nhận file do CHÍNH
    người này tải và CHƯA gắn vào đâu — không thì đoán `file_id` của chứng từ
    mật rồi gắn vào bài public là phát tán được file kín.
    """
    from app.modules.attachment.model import FileLink, StoredFile

    if not file_ids:
        return 0
    valid = {f.id for f in db.query(StoredFile.id)
              .filter(StoredFile.id.in_(file_ids), StoredFile.created_by == user_id).all()}
    attached = {fid for (fid,) in db.query(FileLink.file_id)
              .filter(FileLink.file_id.in_(file_ids)).all()}
    n = 0
    for fid in file_ids:                      # giữ đúng thứ tự người dùng chọn
        if fid not in valid or fid in attached:
            continue
        db.add(FileLink(file_id=fid, entity="forum_post", entity_id=post.id, sort_order=n,
                        created_by=user_id, updated_by=user_id))
        n += 1
    if n:
        db.commit()
    return n


def delete_post(db: Session, post: ForumPost) -> None:
    """Xóa hẳn một bài — cuốn theo ảnh, like, TOÀN BỘ bình luận (kèm ảnh/like/
    nhắc tên của chúng) và nhật ký kiểm duyệt. File trên storage chỉ mất khi
    không còn chỗ nào dùng (`delete_attachments_for`)."""
    from app.modules.attachment.service import delete_attachments_for
    from app.modules.comment.model import Comment, CommentMention, CommentReaction

    cids = [i for (i,) in db.query(Comment.id)
            .filter(Comment.entity == "forum_post", Comment.entity_id == post.id).all()]
    delete_attachments_for(db, [("forum_post", post.id)] + [("comment", i) for i in cids])
    if cids:
        db.query(CommentReaction).filter(CommentReaction.comment_id.in_(cids)).delete(synchronize_session=False)
        db.query(CommentMention).filter(CommentMention.comment_id.in_(cids)).delete(synchronize_session=False)
        db.query(Comment).filter(Comment.id.in_(cids)).delete(synchronize_session=False)
    db.query(ForumReaction).filter(ForumReaction.post_id == post.id).delete(synchronize_session=False)
    db.query(ForumModerationLog).filter(ForumModerationLog.post_id == post.id).delete(synchronize_session=False)
    db.delete(post)
    db.commit()


def toggle_like(db: Session, post_id: int, user_id: int,
                kind: int = int(ForumReactionKind.LIKE)) -> dict:
    """Bấm cảm xúc kiểu Facebook (CR-206). Không sinh chuông (D-Q6).

    Ba đường: chưa có -> thêm dòng; CÙNG cảm xúc -> bỏ (như bỏ like cũ);
    KHÁC cảm xúc -> UPDATE `kind` trên chính dòng đó (unique bài+người).
    Trả trạng thái chung cuộc để FE vá cache: {"liked", "count", "my_reaction",
    "reactions"} — cùng hình dạng với `like_map` của một bài.
    """
    try:
        kind = int(ForumReactionKind(int(kind)))
    except ValueError:
        raise HTTPException(400, f"Cảm xúc không hợp lệ: {kind}")
    row = (db.query(ForumReaction)
           .filter(ForumReaction.post_id == post_id, ForumReaction.user_id == user_id)
           .first())
    if row and int(row.kind) == kind:
        db.delete(row)
        my_reaction = 0
    elif row:
        row.kind = kind
        row.updated_by = user_id
        my_reaction = kind
    else:
        db.add(ForumReaction(post_id=post_id, user_id=user_id, kind=kind,
                             created_by=user_id, updated_by=user_id))
        my_reaction = kind
    db.commit()
    rows = (db.query(ForumReaction.kind, func.count(ForumReaction.id))
            .filter(ForumReaction.post_id == post_id)
            .group_by(ForumReaction.kind).all())
    reactions = {int(k): n for k, n in rows}
    return {"liked": my_reaction != 0, "count": sum(reactions.values()),
            "my_reaction": my_reaction, "reactions": reactions}


def reaction_users(db: Session, post_id: int) -> list[tuple[int, int]]:
    """[(user_id, kind)] theo thứ tự bấm — hộp "ai đã bày tỏ cảm xúc" lọc theo kind ở FE."""
    return [(uid, int(kind)) for uid, kind in
            db.query(ForumReaction.user_id, ForumReaction.kind)
            .filter(ForumReaction.post_id == post_id)
            .order_by(ForumReaction.id.asc()).all()]


# ── Kiểm duyệt (F5, QĐ-D1) ─────────────────────────────────────────────────────

# Trạng thái ĐÍCH của từng hành động + trạng thái NGUỒN hợp lệ. RESTORE chỉ đi
# từ HIDDEN; REMOVE đi được từ cả PUBLISHED lẫn HIDDEN (ẩn rồi vẫn xóa hẳn được).
_MOD_TRANSITIONS = {
    ForumModerationAction.HIDE: ({ForumPostStatus.PUBLISHED}, ForumPostStatus.HIDDEN),
    ForumModerationAction.RESTORE: ({ForumPostStatus.HIDDEN}, ForumPostStatus.PUBLISHED),
    ForumModerationAction.REMOVE: ({ForumPostStatus.PUBLISHED, ForumPostStatus.HIDDEN},
                                   ForumPostStatus.REMOVED),
}


def moderate(db: Session, user, post: ForumPost,
             action: ForumModerationAction, reason: str) -> ForumModerationLog:
    """Một hành động kiểm duyệt = đổi trạng thái + MỘT dòng nhật ký, không có
    đường tắt "ẩn lặng lẽ" (QĐ-D1). Lý do bắt buộc khi ẩn/xóa — điều kiện đủ F5;
    khôi phục thì không cần (trả bài về như cũ không phải là chế tài).

    REMOVE chỉ đổi trạng thái, KHÔNG `delete_post`: giữ dòng + nhật ký để đối
    soát về sau. `can_view` đã chặn REMOVED khỏi mọi mắt qua API.
    """
    reason = (reason or "").strip()
    if action != ForumModerationAction.RESTORE and not reason:
        raise HTTPException(400, "Phải ghi lý do khi ẩn/xóa bài viết")
    source, target = _MOD_TRANSITIONS[action]
    if ForumPostStatus(int(post.status)) not in source:
        raise HTTPException(400, "Trạng thái bài viết không cho phép thao tác này")
    post.status = int(target)
    log = ForumModerationLog(post_id=post.id, action=int(action), reason=reason,
                             created_by=user.id, updated_by=user.id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def hidden_reason_map(db: Session, post_ids: list[int]) -> dict[int, str]:
    """{post_id: lý do ẨN gần nhất} — chỉ gọi cho các bài đang HIDDEN, để tác
    giả (và admin) thấy nhãn lý do ngay trên thẻ bài. 1 query/trang."""
    ids = [i for i in post_ids if i]
    if not ids:
        return {}
    rows = (db.query(ForumModerationLog)
            .filter(ForumModerationLog.post_id.in_(ids),
                    ForumModerationLog.action == int(ForumModerationAction.HIDE))
            .order_by(ForumModerationLog.id.asc()).all())
    return {r.post_id: r.reason for r in rows}   # dòng sau đè dòng trước = gần nhất
