"""Guard chi phí Trợ lý AI (Phase 4).

Hai việc:
- CHẶN TỐN: mỗi người chỉ hỏi tối đa `AI_DAILY_MSG_LIMIT` câu/ngày (mỗi lượt nhồi cả
  gói tri thức + lịch sử nên token/lượt lớn). Kiểm TRƯỚC khi gọi model.
- THEO DÕI: tổng hợp token đã dùng theo ngày / theo người cho admin soi chi phí, đọc
  thẳng các cột *_tokens có sẵn trên `tab_assistant_message` (không thêm bảng).

Token nằm trên tin của TRỢ LÝ (role=ASSISTANT); "số câu hỏi" đếm tin của NGƯỜI DÙNG
(role=USER). Toàn bộ mốc ngày theo giờ máy chủ (`datetime.now()`), nhất quán với phần còn lại.
"""
from datetime import datetime, timedelta

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.employee.model import Employee
from app.modules.user.model import User

from .model import AssistantMessage, MessageRole


class QuotaExceeded(Exception):
    """Vượt trần số câu hỏi trong ngày — endpoint ánh xạ sang HTTP 429."""


def _start_of_today() -> datetime:
    now = datetime.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def count_today(db: Session, user_id: int) -> int:
    """Số câu hỏi (tin người dùng) mà user đã gửi kể từ đầu ngày hôm nay."""
    stmt = (
        select(func.count())
        .select_from(AssistantMessage)
        .where(
            AssistantMessage.role == MessageRole.USER,
            AssistantMessage.created_by == user_id,
            AssistantMessage.created_at >= _start_of_today(),
        )
    )
    return int(db.execute(stmt).scalar_one())


def check_daily_limit(db: Session, user) -> None:
    """Ném QuotaExceeded nếu user đã chạm trần ngày. Limit <= 0 = không giới hạn."""
    limit = settings.AI_DAILY_MSG_LIMIT
    if limit <= 0:
        return
    used = count_today(db, user.id)
    if used >= limit:
        raise QuotaExceeded(
            f"Bạn đã dùng hết {limit} câu hỏi Trợ lý AI trong hôm nay. "
            "Vui lòng thử lại vào ngày mai hoặc liên hệ quản trị để nới hạn."
        )


def my_quota(db: Session, user) -> dict:
    """Hạn mức của CHÍNH người hỏi hôm nay — để giao diện hiện 'còn bao nhiêu câu'."""
    limit = settings.AI_DAILY_MSG_LIMIT
    used = count_today(db, user.id)
    return {
        "limit": limit,                       # 0 = không giới hạn
        "used": used,
        "remaining": max(limit - used, 0) if limit > 0 else None,
    }


# Các cột token gộp chung một chỗ để câu tổng hợp khỏi lặp.
_TOKEN_COLS = (
    "input_tokens",
    "output_tokens",
    "thinking_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
)


def _token_sums():
    """Danh sách biểu thức SUM(cột token) đặt tên sẵn, dùng lại cho mọi truy vấn gộp."""
    return [
        func.coalesce(func.sum(getattr(AssistantMessage, c)), 0).label(c)
        for c in _TOKEN_COLS
    ]


def _questions_sum():
    """Đếm tin NGƯỜI DÙNG = số câu hỏi (token nằm ở tin trợ lý nên đếm riêng)."""
    return func.coalesce(
        func.sum(cast(AssistantMessage.role == MessageRole.USER, Integer)), 0
    ).label("questions")


def _row_to_dict(row) -> dict:
    return {c: int(getattr(row, c)) for c in _TOKEN_COLS}


def summary(db: Session, days: int = 30) -> dict:
    """Tổng hợp usage `days` ngày gần nhất: theo ngày, theo người, và tổng.

    Chỉ admin gọi (endpoint gác bằng `assistant.export`). Một câu SELECT cho mỗi
    chiều — quy mô vài chục người nên không cần tối ưu thêm.
    """
    days = max(1, min(days, 365))
    since = _start_of_today() - timedelta(days=days - 1)
    base_where = (AssistantMessage.created_at >= since,)

    # --- Theo ngày ---
    day_col = func.date(AssistantMessage.created_at).label("day")
    by_day_rows = db.execute(
        select(day_col, _questions_sum(), *_token_sums())
        .where(*base_where)
        .group_by(day_col)
        .order_by(day_col.asc())
    ).all()
    by_day = [
        {"date": str(r.day), "questions": int(r.questions), **_row_to_dict(r)}
        for r in by_day_rows
    ]

    # --- Theo người ---
    by_user_rows = db.execute(
        select(AssistantMessage.created_by.label("user_id"), _questions_sum(), *_token_sums())
        .where(*base_where)
        .group_by(AssistantMessage.created_by)
    ).all()
    labels = _user_labels(db, [r.user_id for r in by_user_rows])
    by_user = [
        {
            "user_id": int(r.user_id),
            "name": labels.get(int(r.user_id), f"Người dùng #{r.user_id}"),
            "questions": int(r.questions),
            **_row_to_dict(r),
        }
        for r in by_user_rows
    ]
    # Tốn token nhất lên đầu.
    by_user.sort(key=lambda u: u["input_tokens"] + u["output_tokens"], reverse=True)

    # --- Tổng ---
    total_row = db.execute(
        select(_questions_sum(), *_token_sums()).where(*base_where)
    ).one()
    totals = {"questions": int(total_row.questions), **_row_to_dict(total_row)}

    return {
        "days": days,
        "since": since.date().isoformat(),
        "daily_limit": settings.AI_DAILY_MSG_LIMIT,
        "by_day": by_day,
        "by_user": by_user,
        "totals": totals,
    }


def _user_labels(db: Session, user_ids: list[int]) -> dict[int, str]:
    """Map id người dùng -> tên nhân sự (rơi về email nếu chưa gắn nhân sự)."""
    ids = [i for i in {int(x) for x in user_ids} if i]
    if not ids:
        return {}
    rows = db.execute(
        select(User.id, User.email, Employee.full_name)
        .join(Employee, Employee.id == User.employee_id, isouter=True)
        .where(User.id.in_(ids))
    ).all()
    out: dict[int, str] = {}
    for uid, email, full_name in rows:
        out[int(uid)] = (full_name or "").strip() or (email or "").strip() or f"Người dùng #{uid}"
    return out
