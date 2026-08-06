import re

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
from app.core.comment_registry import doc_model, policy
from app.core.scoping import apply_scope

from .model import Comment, CommentMention, CommentReaction

MAX_BODY = 5000
PAGE_SIZE = 10   # số bình luận GỐC tải mỗi lần; phản hồi luôn tải đủ khi bung
MAX_MENTIONS = 20   # nhắc quá nhiều người một lúc là spam chuông, không phải trao đổi

# Thẻ nhắc tên nằm ngay trong nội dung: "@[12] xem giúp mình" (CR-031).
# Lưu ID chứ không lưu chữ "@Tên" vì tên tiếng Việt trùng nhiều và người ta đổi tên được;
# giao diện tra tên theo ID lúc hiển thị nên đổi tên là chỗ cũ cũng hiện tên mới.
MENTION_TAG = re.compile(r"@\[(\d+)\]")


def parse_mentions(body: str) -> list[int]:
    """Rút ID người được nhắc từ nội dung, giữ thứ tự xuất hiện, bỏ trùng."""
    seen: list[int] = []
    for m in MENTION_TAG.finditer(body or ""):
        uid = int(m.group(1))
        if uid and uid not in seen:
            seen.append(uid)
    return seen


def strip_mentions(db: Session, body: str) -> str:
    """Đổi thẻ `@[12]` thành `@Tên` — dùng cho nội dung chuông/push, nơi không render được chip."""
    ids = parse_mentions(body)
    if not ids:
        return body
    from app.modules.notification.service import get_user_display_name
    from app.modules.user.model import User
    ten = {u.id: get_user_display_name(db, u)
           for u in db.query(User).filter(User.id.in_(ids)).all()}
    return MENTION_TAG.sub(lambda m: "@" + ten.get(int(m.group(1)), "?"), body)


def resolve_doc(db: Session, user, entity: str, entity_id: int):
    """Kiểm quyền bình luận rồi trả (chứng từ, nhãn loại, route FE).

    Quyền bình luận ĂN THEO CHỨNG TỪ CHA — ai mở được phiếu thì đọc và góp ý được:
    bình luận là trao đổi, không phải sửa nghiệp vụ, nên không đẻ thêm luật RBAC riêng.
    Hai lớp chặn, đúng như trang chi tiết phiếu:
      1. `user_has_permission(... , "read")` — quyền theo vai trò.
      2. `apply_scope` — phạm vi dữ liệu, để không ai bình luận vào phiếu ngoài phạm vi mình thấy.
    """
    pol = policy(entity)
    if not pol:
        raise HTTPException(400, f"Không hỗ trợ bình luận cho: {entity}")
    parent, label, route = pol
    if not user_has_permission(db, user, parent, "read"):
        raise HTTPException(403, "Không có quyền xem chứng từ này")
    model = doc_model(entity)
    if model is None:
        raise HTTPException(400, f"Không hỗ trợ bình luận cho: {entity}")
    doc = apply_scope(db.query(model).filter(model.id == entity_id), model, parent, user,
                      get_perm_profile(db, user)).first()
    if not doc:
        raise HTTPException(403, "Chứng từ không tồn tại hoặc ngoài phạm vi được phép xem")
    return doc, label, route


# ── Đọc ─────────────────────────────────────────────────────────────────────────

def _base(db: Session, entity: str, entity_id: int):
    return db.query(Comment).filter(Comment.entity == entity, Comment.entity_id == entity_id)


def count_roots(db: Session, entity: str, entity_id: int) -> int:
    return _base(db, entity, entity_id).filter(Comment.parent_id == 0).count()


def count_all(db: Session, entity: str, entity_id: int) -> int:
    """Tổng cả gốc lẫn phản hồi — con số hiện cạnh tiêu đề "Trao đổi"."""
    return _base(db, entity, entity_id).count()


def list_roots(db: Session, entity: str, entity_id: int, limit: int = PAGE_SIZE,
               before_id: int = 0) -> list[Comment]:
    """Trang bình luận GỐC, trả về theo thứ tự CŨ → MỚI.

    Lấy `limit` cái MỚI NHẤT (id giảm dần) rồi đảo lại: mở phiếu ra là thấy ngay phần
    đang bàn dở, nhưng vẫn đọc xuôi thời gian. `before_id` = id nhỏ nhất đang hiển thị,
    dùng cho nút "Xem N bình luận trước" — phân trang theo con trỏ nên thêm bình luận
    mới giữa chừng cũng không làm lệch trang như OFFSET.
    """
    q = _base(db, entity, entity_id).filter(Comment.parent_id == 0)
    if before_id:
        q = q.filter(Comment.id < before_id)
    rows = q.order_by(Comment.id.desc()).limit(max(1, limit)).all()
    return list(reversed(rows))


def list_replies(db: Session, parent_id: int) -> list[Comment]:
    """Toàn bộ phản hồi của một bình luận gốc, cũ → mới. Chỉ gọi khi người dùng bung ra."""
    return (db.query(Comment).filter(Comment.parent_id == parent_id)
            .order_by(Comment.id.asc()).all())


def reply_counts(db: Session, root_ids: list[int]) -> dict[int, int]:
    """Số phản hồi của từng gốc — 1 query cho cả trang, để hiện nhãn "N phản hồi"."""
    ids = [i for i in root_ids if i]
    if not ids:
        return {}
    rows = (db.query(Comment.parent_id, func.count(Comment.id))
            .filter(Comment.parent_id.in_(ids)).group_by(Comment.parent_id).all())
    return {pid: n for pid, n in rows}


def like_map(db: Session, comment_ids: list[int], user_id: int) -> dict[int, dict]:
    """{comment_id: {"count": n, "liked": bool}} — gom 1 query, tránh hỏi từng dòng."""
    ids = [i for i in comment_ids if i]
    if not ids:
        return {}
    counts = dict(db.query(CommentReaction.comment_id, func.count(CommentReaction.id))
                  .filter(CommentReaction.comment_id.in_(ids))
                  .group_by(CommentReaction.comment_id).all())
    mine = {cid for (cid,) in db.query(CommentReaction.comment_id)
            .filter(CommentReaction.comment_id.in_(ids), CommentReaction.user_id == user_id).all()}
    return {cid: {"count": counts.get(cid, 0), "liked": cid in mine} for cid in ids}


def mention_map(db: Session, comment_ids: list[int]) -> dict[int, list[int]]:
    """{comment_id: [user_id đã nhắc]} — 1 query cho cả trang."""
    ids = [i for i in comment_ids if i]
    if not ids:
        return {}
    out: dict[int, list[int]] = {}
    for cid, uid in (db.query(CommentMention.comment_id, CommentMention.user_id)
                     .filter(CommentMention.comment_id.in_(ids))
                     .order_by(CommentMention.id.asc()).all()):
        out.setdefault(cid, []).append(uid)
    return out


def mentionable(db: Session, doc, entity: str, entity_id: int, me_id: int,
                q: str = "", limit: int = 8) -> list[dict]:
    """Người có thể `@` trong phiếu này.

    Chưa gõ chữ nào thì chỉ gợi ý NGƯỜI ĐANG DÍNH TỚI PHIẾU (người tạo phiếu + ai đã bình luận)
    — mở ra là bấm được ngay, đúng 90% trường hợp. Gõ thêm chữ thì tìm trong TOÀN BỘ nhân sự
    đang hoạt động, để còn kéo người mới vào cuộc.

    Không lọc theo quyền xem phiếu: người bị nhắc chỉ nhận một dòng chuông, bấm vào mà không có
    quyền thì vẫn bị 403 như thường — chặn ở đây chỉ tốn thêm một vòng apply_scope cho mỗi ký tự gõ.
    """
    from app.modules.employee.model import Employee
    from app.modules.notification.service import get_user_display_name
    from app.modules.user.model import User

    lien_quan = {getattr(doc, "created_by", 0) or 0}
    lien_quan.update(uid for (uid,) in db.query(Comment.created_by)
                     .filter(Comment.entity == entity, Comment.entity_id == entity_id).distinct())
    lien_quan.discard(0)
    lien_quan.discard(me_id)

    q = (q or "").strip()
    users = db.query(User).filter(User.is_active == True)  # noqa: E712
    if q:
        # Tìm theo tên/mã nhân sự, và cả email cho tài khoản chưa gắn nhân sự
        emp_ids = [e.id for e in db.query(Employee.id).filter(
            or_(Employee.full_name.like(f"%{q}%"), Employee.code.like(f"%{q}%"))).limit(200).all()]
        cond = [User.email.like(f"%{q}%")]
        if emp_ids:
            cond.append(User.employee_id.in_(emp_ids))
        users = users.filter(or_(*cond))
    elif lien_quan:
        users = users.filter(User.id.in_(lien_quan))
    else:
        return []

    rows = users.limit(60).all()
    emp = {e.id: e for e in db.query(Employee).filter(
        Employee.id.in_([u.employee_id for u in rows if u.employee_id])).all()} if rows else {}
    ra = [{"user_id": u.id,
           "name": get_user_display_name(db, u),
           "code": (emp.get(u.employee_id or 0).code if emp.get(u.employee_id or 0) else "") or "",
           "avatar": getattr(u, "avatar", "") or "",
           "related": u.id in lien_quan}
          for u in rows if u.id != me_id]
    # Người đang dính tới phiếu luôn nổi lên đầu, phần còn lại xếp theo tên
    ra.sort(key=lambda x: (not x["related"], x["name"]))
    return ra[:limit]


# ── Ghi ─────────────────────────────────────────────────────────────────────────

def create_comment(db: Session, entity: str, entity_id: int, body: str, user_id: int,
                   parent_id: int = 0, reply_to_user_id: int = 0) -> Comment:
    body = (body or "").strip()
    if not body:
        raise HTTPException(400, "Nội dung bình luận không được để trống")
    if len(body) > MAX_BODY:
        raise HTTPException(400, f"Bình luận tối đa {MAX_BODY} ký tự")

    parent_id = int(parent_id or 0)
    if parent_id:
        parent = db.get(Comment, parent_id)
        if not parent or parent.entity != entity or parent.entity_id != entity_id:
            raise HTTPException(400, "Bình luận gốc không tồn tại trong phiếu này")
        # LUẬT 2 CẤP: trả lời một phản hồi thì vẫn nằm ở cấp 2, treo vào chính gốc của nó.
        # Ép ở backend chứ không tin FE — có vậy dữ liệu mới chắc chắn không sinh cấp 3.
        parent_id = parent.parent_id or parent.id
        # Nhắc tên mặc định là người vừa được trả lời; tự nhắc chính mình thì bỏ.
        if not reply_to_user_id and parent.parent_id:
            reply_to_user_id = parent.created_by or 0
    else:
        reply_to_user_id = 0   # bình luận gốc không nhắc ai

    if reply_to_user_id == user_id:
        reply_to_user_id = 0

    c = Comment(entity=entity, entity_id=entity_id, body=body, parent_id=parent_id,
                reply_to_user_id=int(reply_to_user_id or 0),
                created_by=user_id, updated_by=user_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    save_mentions(db, c, user_id)
    return c


def save_mentions(db: Session, c: Comment, user_id: int) -> list[int]:
    """Ghi danh sách người được `@` trong nội dung. Trả về ID những người thực sự được nhắc.

    Lọc lại ở backend chứ không tin thẻ FE gửi lên: ID không có thật hoặc tài khoản đã khóa
    thì bỏ qua (thẻ vẫn nằm trong nội dung, giao diện hiện "@?"), tự nhắc chính mình cũng bỏ.
    """
    from app.modules.user.model import User

    ids = parse_mentions(c.body)[:MAX_MENTIONS]
    ids = [i for i in ids if i != user_id]
    if not ids:
        return []
    that = [u.id for u in db.query(User.id)
            .filter(User.id.in_(ids), User.is_active == True).all()]  # noqa: E712
    for uid in that:
        db.add(CommentMention(comment_id=c.id, user_id=uid,
                              created_by=user_id, updated_by=user_id))
    db.commit()
    return that


def delete_comment(db: Session, c: Comment) -> int:
    """Xóa bình luận; nếu là GỐC thì cuốn theo toàn bộ phản hồi của nó.

    Trả về tổng số dòng đã xóa (để báo lại cho người bấm). Giữ phản hồi mồ côi khi gốc
    biến mất chỉ làm luồng khó đọc, không ai hiểu đang trả lời cái gì.
    """
    ids = [c.id]
    if not c.parent_id:
        ids += [i for (i,) in db.query(Comment.id).filter(Comment.parent_id == c.id).all()]
    db.query(CommentReaction).filter(CommentReaction.comment_id.in_(ids)).delete(synchronize_session=False)
    db.query(CommentMention).filter(CommentMention.comment_id.in_(ids)).delete(synchronize_session=False)
    db.query(Comment).filter(Comment.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(ids)


def toggle_reaction(db: Session, comment_id: int, user_id: int) -> dict:
    """Bấm thích / bỏ thích. Trả {"liked": bool, "count": n}."""
    row = (db.query(CommentReaction)
           .filter(CommentReaction.comment_id == comment_id, CommentReaction.user_id == user_id)
           .first())
    if row:
        db.delete(row)
        liked = False
    else:
        db.add(CommentReaction(comment_id=comment_id, user_id=user_id,
                               created_by=user_id, updated_by=user_id))
        liked = True
    db.commit()
    count = db.query(CommentReaction).filter(CommentReaction.comment_id == comment_id).count()
    return {"liked": liked, "count": count}


def reaction_user_ids(db: Session, comment_id: int) -> list[int]:
    return [uid for (uid,) in db.query(CommentReaction.user_id)
            .filter(CommentReaction.comment_id == comment_id)
            .order_by(CommentReaction.id.asc()).all()]


# ── Thông báo ───────────────────────────────────────────────────────────────────

def recipient_ids(db: Session, doc, entity: str, entity_id: int, author_id: int,
                  exclude: set[int] | None = None) -> list[int]:
    """Ai nhận chuông khi có bình luận mới: NGƯỜI TẠO CHỨNG TỪ + AI ĐÃ BÌNH LUẬN trong phiếu đó.

    Cố ý KHÔNG báo cho toàn bộ người liên quan (người duyệt, NV thu mua, trưởng phòng…):
    đơn nhiều người theo dõi sẽ làm chuông rất ồn. Người vừa gõ thì không tự báo cho mình.
    `exclude` để bỏ người đã nhận chuông "được nhắc tên" — tránh gửi hai chuông một việc.
    """
    ids = {getattr(doc, "created_by", 0) or 0}
    ids.update(uid for (uid,) in db.query(Comment.created_by)
               .filter(Comment.entity == entity, Comment.entity_id == entity_id).distinct())
    ids.discard(0)
    ids.discard(author_id)
    for uid in (exclude or set()):
        ids.discard(uid)
    return sorted(ids)
