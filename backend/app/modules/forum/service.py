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
import re
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
# MỘT bộ lọc cho cả hệ (nguyên tắc content_sanitize.py của văn thư) — forum
# không viết bộ lọc thứ hai, sai sót vá một chỗ là vá cho tất cả.
from app.modules.help_center.import_service import sanitize_html

from .model import (ForumAudience, ForumBoard, ForumBoardStatus,
                    ForumBodyFormat, ForumModerationAction, ForumModerationLog,
                    ForumPost, ForumPostKind, ForumPostStatus, ForumPrefix,
                    ForumReaction, ForumReactionKind)

MAX_BODY = 10_000        # chữ trơn — bài cũ + bình luận (mục 3 của `01`)
# CR-261: bài rich lưu HTML nên trần đo trên MARKUP — thẻ mở/đóng ăn cỡ 3-4
# lần chữ nhìn thấy, 40k markup xấp xỉ trần 10k chữ trơn cũ về lượng nội dung.
MAX_BODY_HTML = 40_000
MAX_TITLE = 255     # tiêu đề thread trong box (F13a) — khớp VARCHAR(255)
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


# ── Tìm kiếm bài viết (CR-263) ─────────────────────────────────────────────────
#
# MỘT endpoint cho cả người thường lẫn quản trị: người thường bị ép qua
# `_visible_cond` ngay trong SQL (tìm gì cũng chỉ ra bài mình vốn được xem),
# quản trị thấy cả bài ẩn + lọc thêm theo trạng thái. Không đẻ hai bộ máy.


def escape_like(q: str) -> str:
    """Thoát ký tự đại diện của LIKE — người dùng gõ `%`/`_` là tìm ĐÚNG ký tự
    đó, không phải mở toang mọi bài (khuôn hacker-test của rules/testing)."""
    return (q or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _author_ids_subquery(db: Session, author_q: str):
    """Subquery user_id có tên nhân sự / email / mã NV khớp `author_q` — lọc
    "người tạo" bằng CHỮ người dùng gõ, không cần endpoint danh bạ riêng
    (người thường không có quyền đọc danh mục nhân sự). Subquery chứ không
    IN-list (bài học rà soát API hiệu năng)."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    like = f"%{escape_like(author_q)}%"
    return (db.query(User.id)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(or_(Employee.full_name.like(like, escape="\\"),
                        Employee.code.like(like, escape="\\"),
                        User.email.like(like, escape="\\")))
            .scalar_subquery())


def search_posts(db: Session, user, profile: dict, q: str = "",
                 author_q: str = "", company_id: int = 0, dept_id: int = 0,
                 board_id: int = 0, status: int = 0,
                 page: int = 1, per_page: int = PAGE_SIZE):
    """Một trang kết quả tìm kiếm, mới → cũ, phân trang số trang (người ta đảo
    trang kết quả như đảo trang thread — con trỏ id không cần thiết ở đây).

    `q` khớp LIKE trên tiêu đề + nội dung. Bài rich lưu HTML nên chữ trong
    markup (tên thẻ/thuộc tính) có thể khớp oan — chấp nhận ở đợt đầu, dữ
    liệu nhỏ và từ khóa tiếng Việt gần như không đụng tên thẻ tiếng Anh.
    `company_id`/`dept_id` lọc theo ngữ cảnh ĐÓNG BĂNG trên bài (đúng nghĩa
    "bài của người thuộc công ty/phòng đó lúc đăng"). `status` chỉ quản trị
    dùng được (1=đang hiện, 2=đang ẩn, 0=cả hai); người thường bị bỏ qua.
    Trả (rows, total) để controller đóng phong bì phân trang.
    """
    qy = db.query(ForumPost)
    if can_moderate(db, user):
        allowed = [int(ForumPostStatus.PUBLISHED), int(ForumPostStatus.HIDDEN)]
        if int(status) in allowed:
            qy = qy.filter(ForumPost.status == int(status))
        else:
            qy = qy.filter(ForumPost.status.in_(allowed))
    else:
        qy = qy.filter(_visible_cond(user, profile))
    q = (q or "").strip()
    if q:
        like = f"%{escape_like(q)}%"
        qy = qy.filter(or_(ForumPost.body.like(like, escape="\\"),
                           ForumPost.title.like(like, escape="\\")))
    author_q = (author_q or "").strip()
    if author_q:
        qy = qy.filter(ForumPost.created_by.in_(_author_ids_subquery(db, author_q)))
    if company_id:
        qy = qy.filter(ForumPost.company_id == int(company_id))
    if dept_id:
        qy = qy.filter(ForumPost.dept_id == int(dept_id))
    if board_id:
        qy = qy.filter(ForumPost.board_id == int(board_id))
    total = qy.count()
    page = max(1, page)
    rows = (qy.order_by(ForumPost.id.desc())
            .offset((page - 1) * per_page).limit(max(1, per_page)).all())
    return rows, total


def list_search_filter_options(db: Session) -> dict:
    """Hai danh sách cho ô lọc của màn tìm kiếm: công ty + phòng ban ĐÃ XUẤT
    HIỆN trên bài (distinct từ chính bảng bài viết) — không mở endpoint danh
    mục công ty/phòng ban cho người thường (họ không có grant hai entity đó),
    và lọc theo đơn vị chưa có bài nào thì đằng nào cũng rỗng."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    comp_ids = [i for (i,) in db.query(ForumPost.company_id)
                .filter(ForumPost.company_id > 0).distinct().all()]
    dept_ids = [i for (i,) in db.query(ForumPost.dept_id)
                .filter(ForumPost.dept_id > 0).distinct().all()]
    companies = (db.query(Company.id, Company.name)
                 .filter(Company.id.in_(comp_ids)).order_by(Company.name.asc()).all()
                 if comp_ids else [])
    departments = (db.query(Department.id, Department.name)
                   .filter(Department.id.in_(dept_ids)).order_by(Department.name.asc()).all()
                   if dept_ids else [])
    return {"companies": [{"id": i, "name": n} for i, n in companies],
            "departments": [{"id": i, "name": n} for i, n in departments]}


# ── Chuyên mục kiểu VOZ (F13a, QĐ-D7) ──────────────────────────────────────────
#
# Đợt đầu mọi box ép PUBLIC (QĐ-D7a) nên thread list vẫn đi qua `_visible_cond`
# như feed — luật một chỗ, sau này mở box theo phòng/pháp nhân không phải sửa.

def get_postable_board(db: Session, board_id: int) -> ForumBoard:
    """Box NHẬN ĐƯỢC bài — tồn tại, là box (có nhóm cha), cả box lẫn nhóm cha
    đang mở. 400 GỘP mọi nhánh: FE tử tế không bao giờ gửi tới box ẩn, tới đây
    là gõ tay id, không cần phân biệt lý do."""
    board = db.get(ForumBoard, board_id)
    if (board is None or board.parent_id is None
            or int(board.status) != int(ForumBoardStatus.ACTIVE)):
        raise HTTPException(400, "Box không tồn tại hoặc đã ẩn")
    parent = db.get(ForumBoard, board.parent_id)
    if parent is None or int(parent.status) != int(ForumBoardStatus.ACTIVE):
        raise HTTPException(400, "Box không tồn tại hoặc đã ẩn")
    return board


def _last_comment_subquery(db: Session):
    """(post_id, mốc + id bình luận CUỐI của bài) — nửa "comment" của công thức
    hoạt động cuối = max(bài đăng, bình luận cuối)."""
    from app.modules.comment.model import Comment

    return (db.query(Comment.entity_id.label("post_id"),
                     func.max(Comment.created_at).label("last_at"))
            .filter(Comment.entity == "forum_post")
            .group_by(Comment.entity_id).subquery())


def last_comment_at_map(db: Session, post_ids: list[int]) -> dict[int, datetime]:
    """{post_id: mốc bình luận CUỐI} cho các bài trong trang — controller ghép
    với `created_at` thành cột «hoạt động cuối» của thread list (F13b)."""
    from app.modules.comment.model import Comment

    if not post_ids:
        return {}
    rows = (db.query(Comment.entity_id, func.max(Comment.created_at))
            .filter(Comment.entity == "forum_post",
                    Comment.entity_id.in_(post_ids))
            .group_by(Comment.entity_id).all())
    return dict(rows)


def list_board_threads(db: Session, user, profile: dict, board_id: int,
                       page: int = 1, per_page: int = PAGE_SIZE):
    """Một trang thread của box, sắp theo HOẠT ĐỘNG CUỐI (max giữa lúc đăng và
    bình luận cuối) — box tự vận hành, admin không xếp tay (chốt 03/09/2026).
    Thread ghim nổi lên đầu (`pinned_at` lọc theo box — QĐ-D7).

    Phân trang SỐ TRANG `page/per_page` chứ không con trỏ: người ta nhảy thẳng
    trang 5 như VOZ; thứ tự theo hoạt động thì con trỏ id không diễn đạt được.
    Trả (rows, total) để controller đóng phong bì phân trang.
    """
    sq = _last_comment_subquery(db)
    # max(bài, comment cuối) viết bằng CASE chứ không GREATEST — SQLite của bộ
    # test không có GREATEST, mà hai cách cho cùng kết quả.
    last_at = func.coalesce(sq.c.last_at, ForumPost.created_at)
    activity = case((last_at > ForumPost.created_at, last_at),
                    else_=ForumPost.created_at)
    q = (db.query(ForumPost)
         .outerjoin(sq, sq.c.post_id == ForumPost.id)
         .filter(ForumPost.board_id == board_id))
    if can_moderate(db, user):
        q = q.filter(ForumPost.status.in_([int(ForumPostStatus.PUBLISHED),
                                           int(ForumPostStatus.HIDDEN)]))
    else:
        q = q.filter(_visible_cond(user, profile))
    total = q.count()
    page = max(1, page)
    rows = (q.order_by(ForumPost.pinned_at.isnot(None).desc(),
                       activity.desc(), ForumPost.id.desc())
            .offset((page - 1) * per_page).limit(max(1, per_page)).all())
    return rows, total


HIGHLIGHT_LIMIT = 5        # mỗi khối sidebar 5 dòng — vừa một tầm mắt (F13c)
HIGHLIGHT_WINDOW_DAYS = 7  # «Đang sôi nổi» đếm bình luận + reaction trong 7 ngày


def _visible_box_ids(db: Session, user) -> list[int]:
    """Các box NGƯỜI NÀY thấy được — box ACTIVE thuộc nhóm ACTIVE; admin thấy
    hết. Đếm trên bảng board (vài chục dòng) nên lọc bằng Python cho dễ đọc,
    cùng luật rơi-theo-nhóm với `list_boards`."""
    boards = db.query(ForumBoard).all()
    if can_moderate(db, user):
        return [b.id for b in boards if b.parent_id]
    active = int(ForumBoardStatus.ACTIVE)
    groups = {b.id for b in boards if not b.parent_id and int(b.status) == active}
    return [b.id for b in boards
            if b.parent_id and int(b.status) == active and b.parent_id in groups]


def list_highlight_threads(db: Session, user, profile: dict,
                           limit: int = HIGHLIGHT_LIMIT):
    """(«Đang sôi nổi», «Mới nhất») cho sidebar màn «Diễn đàn» (F13c).

    Sôi nổi = top thread theo TỔNG bình luận + reaction 7 ngày gần nhất — máy
    tự xếp, không ai chọn tay (chốt 03/09/2026); khối «Nổi bật» thì đi API bài
    ghim sẵn có, không nằm ở đây. Hai khối đều chỉ lấy THREAD trong box còn
    nhìn thấy, nguyên luật status/audience của `list_board_threads`.
    """
    from app.modules.comment.model import Comment

    box_ids = _visible_box_ids(db, user)
    if not box_ids:
        return [], []

    def thread_query():
        q = db.query(ForumPost).filter(ForumPost.board_id.in_(box_ids))
        if can_moderate(db, user):
            return q.filter(ForumPost.status.in_([int(ForumPostStatus.PUBLISHED),
                                                  int(ForumPostStatus.HIDDEN)]))
        return q.filter(_visible_cond(user, profile))

    latest = (thread_query().order_by(ForumPost.id.desc())
              .limit(max(1, limit)).all())

    # Điểm sôi nổi gom theo bài trên CẢ diễn đàn (2 query GROUP BY), rồi mới
    # ép về thread-được-thấy bằng `id.in_` — bài feed thuần lẫn trong điểm
    # không sao, vòng lọc sau loại chúng vì không có board_id hợp lệ.
    cutoff = datetime.now() - timedelta(days=HIGHLIGHT_WINDOW_DAYS)
    scores: dict[int, int] = {}
    comment_rows = (db.query(Comment.entity_id, func.count(Comment.id))
                    .filter(Comment.entity == "forum_post",
                            Comment.created_at >= cutoff)
                    .group_by(Comment.entity_id).all())
    reaction_rows = (db.query(ForumReaction.post_id, func.count(ForumReaction.id))
                     .filter(ForumReaction.created_at >= cutoff)
                     .group_by(ForumReaction.post_id).all())
    for pid, n in [*comment_rows, *reaction_rows]:
        scores[pid] = scores.get(pid, 0) + int(n)

    trending: list[ForumPost] = []
    if scores:
        rows = thread_query().filter(ForumPost.id.in_(list(scores))).all()
        # điểm bằng nhau thì bài mới hơn đứng trước — cùng chiều với «Mới nhất»
        rows.sort(key=lambda p: (-scores[p.id], -p.id))
        trending = rows[:max(1, limit)]
    return trending, latest


def _last_post_map(db: Session, box_ids: list[int]) -> dict[int, dict]:
    """{box_id: khối bài-mới-nhất} — thread + mốc + NGƯỜI VIẾT CUỐI của mỗi box.

    "Mới nhất" theo cùng công thức hoạt động cuối với `list_board_threads`:
    so bài đăng mới nhất với bình luận mới nhất, bên nào muộn hơn thắng. Bốn
    query cho CẢ CÂY, không đổi theo số box. Tên/avatar người viết cuối do
    controller tra qua `_authors` (`last_user_id`)."""
    from app.modules.comment.model import Comment

    if not box_ids:
        return {}
    pub = ForumPost.status == int(ForumPostStatus.PUBLISHED)
    newest = dict(db.query(ForumPost.board_id, func.max(ForumPost.id))
                  .filter(ForumPost.board_id.in_(box_ids), pub)
                  .group_by(ForumPost.board_id).all())
    last_cids = dict(db.query(ForumPost.board_id, func.max(Comment.id))
                     .join(Comment, and_(Comment.entity == "forum_post",
                                         Comment.entity_id == ForumPost.id))
                     .filter(ForumPost.board_id.in_(box_ids), pub)
                     .group_by(ForumPost.board_id).all())
    comments = {}
    if last_cids:
        comments = {c.id: c for c in db.query(Comment)
                    .filter(Comment.id.in_(list(last_cids.values()))).all()}
    pids = set(newest.values()) | {c.entity_id for c in comments.values()}
    posts = {p.id: p for p in db.query(ForumPost)
             .filter(ForumPost.id.in_(list(pids))).all()} if pids else {}

    out: dict[int, dict] = {}
    for bid, pid in newest.items():
        post = posts.get(pid)
        if post is None:
            continue
        thread, last_at, actor = post, post.created_at, post.created_by
        cmt = comments.get(last_cids.get(bid, 0))
        if cmt is not None and cmt.created_at and cmt.created_at > last_at:
            thread = posts.get(cmt.entity_id) or thread
            last_at, actor = cmt.created_at, cmt.created_by
        out[bid] = {"post_id": thread.id, "title": thread.title or "",
                    "prefix": int(thread.prefix or 0),
                    "last_at": last_at, "last_user_id": actor}
    return out


def list_boards(db: Session, user) -> list[dict]:
    """Cây nhóm → box kèm bộ đếm + khối bài-mới-nhất (`GET /boards`).

    COUNT trực tiếp, chưa denormalize (chốt F13a — vài chục box, mỗi lần mở tab
    đếm lại vẫn rẻ). Người thường chỉ thấy nhóm/box ACTIVE; admin thấy cả ẩn
    (kèm `status` để FE dán nhãn) — thấy hết mới dọn được, cùng luật với feed.
    Box thuộc nhóm bị ẩn thì biến theo nhóm với người thường.
    """
    from app.modules.comment.model import Comment

    q = db.query(ForumBoard)
    if not can_moderate(db, user):
        q = q.filter(ForumBoard.status == int(ForumBoardStatus.ACTIVE))
    boards = q.order_by(ForumBoard.sort_order.asc(), ForumBoard.id.asc()).all()
    box_ids = [b.id for b in boards if b.parent_id]

    pub = ForumPost.status == int(ForumPostStatus.PUBLISHED)
    thread_counts, comment_counts = {}, {}
    if box_ids:
        thread_counts = dict(db.query(ForumPost.board_id, func.count(ForumPost.id))
                             .filter(ForumPost.board_id.in_(box_ids), pub)
                             .group_by(ForumPost.board_id).all())
        comment_counts = dict(db.query(ForumPost.board_id, func.count(Comment.id))
                              .join(Comment, and_(Comment.entity == "forum_post",
                                                  Comment.entity_id == ForumPost.id))
                              .filter(ForumPost.board_id.in_(box_ids), pub)
                              .group_by(ForumPost.board_id).all())
    last_map = _last_post_map(db, box_ids)

    def render_board(b: ForumBoard) -> dict:
        return {"id": b.id, "parent_id": b.parent_id or 0, "name": b.name,
                "description": b.description, "icon": b.icon,
                "sort_order": int(b.sort_order), "status": int(b.status),
                "audience": int(b.audience),
                "thread_count": thread_counts.get(b.id, 0),
                "comment_count": comment_counts.get(b.id, 0),
                "last_post": last_map.get(b.id)}

    groups = [render_board(b) for b in boards if not b.parent_id]
    by_group = {g["id"]: g for g in groups}
    for g in groups:
        g["children"] = []
    for b in boards:
        # nhóm cha không trong danh sách (đã ẩn) thì box rơi theo — không mồ côi
        if b.parent_id and b.parent_id in by_group:
            by_group[b.parent_id]["children"].append(render_board(b))
    return groups


def create_board(db: Session, user, data) -> ForumBoard:
    """Tạo nhóm (parent_id=0) hoặc box (parent_id=nhóm) — chỉ `forum_admin`.
    Đúng HAI tầng: cha của box phải là nhóm tiêu đề, không lồng sâu hơn."""
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(400, "Tên nhóm/box không được để trống")
    if len(name) > MAX_TITLE:
        raise HTTPException(400, f"Tên tối đa {MAX_TITLE} ký tự")
    parent_id = int(data.parent_id or 0) or None
    if parent_id:
        parent = db.get(ForumBoard, parent_id)
        if parent is None or parent.parent_id is not None:
            raise HTTPException(400, "Nhóm cha không tồn tại hoặc không phải nhóm tiêu đề")
    try:
        status = ForumBoardStatus(int(data.status))
    except ValueError:
        raise HTTPException(400, f"Trạng thái không hợp lệ: {data.status}")
    board = ForumBoard(parent_id=parent_id, name=name,
                       description=(data.description or "").strip(),
                       icon=(data.icon or "").strip()[:50],
                       sort_order=int(data.sort_order or 0), status=int(status),
                       # đợt đầu ÉP PUBLIC (QĐ-D7a) — không nhận từ client
                       audience=int(ForumAudience.PUBLIC),
                       created_by=user.id, updated_by=user.id)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def update_board(db: Session, user, board: ForumBoard, data) -> ForumBoard:
    """Sửa nhóm/box. Nhóm ĐANG chứa box thì không hạ xuống làm box được —
    hạ là đẻ ra tầng ba."""
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(400, "Tên nhóm/box không được để trống")
    if len(name) > MAX_TITLE:
        raise HTTPException(400, f"Tên tối đa {MAX_TITLE} ký tự")
    parent_id = int(data.parent_id or 0) or None
    if parent_id:
        if parent_id == board.id:
            raise HTTPException(400, "Không thể tự làm nhóm cha của chính mình")
        parent = db.get(ForumBoard, parent_id)
        if parent is None or parent.parent_id is not None:
            raise HTTPException(400, "Nhóm cha không tồn tại hoặc không phải nhóm tiêu đề")
        if db.query(ForumBoard.id).filter(ForumBoard.parent_id == board.id).first():
            raise HTTPException(400, "Nhóm đang chứa box — gỡ hết box con trước khi hạ xuống làm box")
    try:
        status = ForumBoardStatus(int(data.status))
    except ValueError:
        raise HTTPException(400, f"Trạng thái không hợp lệ: {data.status}")
    board.name = name
    board.description = (data.description or "").strip()
    board.icon = (data.icon or "").strip()[:50]
    board.parent_id = parent_id
    board.sort_order = int(data.sort_order or 0)
    board.status = int(status)
    board.updated_by = user.id
    db.commit()
    db.refresh(board)
    return board


def delete_board(db: Session, board: ForumBoard) -> None:
    """Xóa nhóm/box — chỉ khi RỖNG. Nhóm còn box hay box còn bài thì 400:
    lịch sử thread không được bốc hơi theo một cú xóa nhầm; muốn rút khỏi mắt
    thì ẨN (`status=HIDDEN`)."""
    if db.query(ForumBoard.id).filter(ForumBoard.parent_id == board.id).first():
        raise HTTPException(400, "Nhóm còn box con — gỡ hết box trước khi xóa")
    if db.query(ForumPost.id).filter(ForumPost.board_id == board.id).first():
        raise HTTPException(400, "Box còn bài viết — chỉ ẩn được, không xóa")
    db.delete(board)
    db.commit()


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

def strip_html_text(html: str) -> str:
    """Bóc thẻ lấy chữ trơn — chỉ để KIỂM RỖNG bài rich, không phải bộ lọc
    an toàn (việc đó của `sanitize_html`). `&nbsp;` là "chữ" duy nhất mà
    trình soạn thảo chèn vào đoạn trống nên phải quy về khoảng trắng."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    return text.replace("&nbsp;", " ").strip()


def create_post(db: Session, user, profile: dict, body: str, audience: int,
                file_ids: list[int] | None = None, kind: int = 0,
                board_id: int = 0, title: str = "", prefix: int = 0,
                body_format: int = 0) -> ForumPost:
    """Đăng bài — không qua duyệt (QĐ-D1), `dept_id`/`company_id` ĐÓNG BĂNG
    theo hồ sơ tác giả lúc đăng (chuyển phòng thì bài cũ giữ ngữ cảnh cũ).

    F13a: `board_id` > 0 = thread trong box — `title` bắt buộc, `audience` ÉP
    theo box (đợt đầu toàn PUBLIC, QĐ-D7a); bài vẫn ra feed như thường (QĐ-D7b).
    Bài feed thuần thì `title`/`prefix` client gửi kèm bị BỎ QUA, không 400 —
    hai trường đó không có nghĩa ngoài box.

    CR-261: `body_format` = RICH_HTML thì `body` là HTML từ `RichTextField` —
    lọc `sanitize_html` NGAY TẠI ĐÂY (cửa ghi duy nhất), trần đo trên markup
    (`MAX_BODY_HTML`), kiểm rỗng bằng chữ đã bóc thẻ. Áp cho cả Bảng tin lẫn
    chủ đề trong box; bình luận vẫn chữ trơn.
    """
    body = (body or "").strip()
    file_ids = [int(i) for i in (file_ids or []) if i]
    title = (title or "").strip()
    board = None
    if board_id:
        board = get_postable_board(db, board_id)
        if not title:
            raise HTTPException(400, "Chủ đề trong box phải có tiêu đề")
        if len(title) > MAX_TITLE:
            raise HTTPException(400, f"Tiêu đề tối đa {MAX_TITLE} ký tự")
        try:
            post_prefix = ForumPrefix(int(prefix))
        except ValueError:
            raise HTTPException(400, f"Prefix không hợp lệ: {prefix}")
        audience = int(board.audience)   # ép theo box — client gửi gì cũng kệ
    else:
        title, post_prefix = "", ForumPrefix.NONE
    try:
        post_kind = ForumPostKind(int(kind))
    except ValueError:
        raise HTTPException(400, f"Loại bài không hợp lệ: {kind}")
    # Bài đổi avatar (F10): ảnh là NHÂN VẬT CHÍNH — đúng 1 tấm (chính avatar
    # mới), caption có hay không tùy; thiếu ảnh thì dòng hệ thống thành nói suông.
    if post_kind == ForumPostKind.AVATAR_UPDATE and len(file_ids) != 1:
        raise HTTPException(400, "Bài đổi ảnh đại diện phải kèm đúng 1 ảnh")
    try:
        fmt = ForumBodyFormat(int(body_format))
    except ValueError:
        raise HTTPException(400, f"Định dạng nội dung không hợp lệ: {body_format}")
    if fmt == ForumBodyFormat.RICH_HTML:
        # Trần đo TRƯỚC khi lọc — chặn markup khổng lồ ngay cửa, khỏi tốn
        # công sanitize một cục 10MB rồi mới chê dài.
        if len(body) > MAX_BODY_HTML:
            raise HTTPException(400, f"Bài viết tối đa {MAX_BODY_HTML} ký tự (tính cả định dạng)")
        body = sanitize_html(body)
        # Toàn thẻ rỗng (`<p></p>`) quy về chuỗi rỗng — bài chỉ có ảnh không
        # lưu xác HTML vào cột, FE khỏi vẽ một đoạn trống trên thẻ bài.
        if not strip_html_text(body):
            body = ""
    elif len(body) > MAX_BODY:
        raise HTTPException(400, f"Bài viết tối đa {MAX_BODY} ký tự")
    if not body and not file_ids:
        raise HTTPException(400, "Bài viết không được để trống")
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

    post = ForumPost(body=body, body_format=int(fmt),
                     audience=int(aud), kind=int(post_kind),
                     dept_id=profile.get("dept_id") or 0,
                     company_id=profile.get("company_id") or 0,
                     board_id=board.id if board else None,
                     title=title or None, prefix=int(post_prefix),
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


def list_moderation_logs(db: Session, page: int = 1, per_page: int = PAGE_SIZE):
    """Một trang nhật ký kiểm duyệt, mới → cũ (CR-263) — bảng này ghi từ F5
    nhưng tới giờ mới có mắt đọc. Chỉ quản trị (controller gác `forum_post.read`).
    Trả (rows, total); tên quản trị viên + nhãn bài do controller tự tra."""
    qy = db.query(ForumModerationLog)
    total = qy.count()
    page = max(1, page)
    rows = (qy.order_by(ForumModerationLog.id.desc())
            .offset((page - 1) * per_page).limit(max(1, per_page)).all())
    return rows, total


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
