"""Nghiệp vụ bình luận: đọc danh sách, resolve tên tác giả (batch), gom người nhận thông báo."""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.user.model import User

from .model import Comment

ALLOWED_ENTITIES = {"survey", "survey_line"}


def resolve_survey_id(db: Session, entity: str, entity_id: int) -> int | None:
    """Suy id phiếu khảo sát từ (entity, entity_id) — để kiểm tra phạm vi + gắn thông báo.
    entity='survey' → chính entity_id; 'survey_line' → tra 2 bảng dòng lấy survey_id."""
    if entity == "survey":
        return entity_id
    from app.modules.survey.model import SurveyProductLine, SurveySupplierLine

    row = db.get(SurveySupplierLine, entity_id) or db.get(SurveyProductLine, entity_id)
    return row.survey_id if row else None


def list_comments(db: Session, entity: str, entity_id: int) -> list[Comment]:
    # Giữ 500 bình luận MỚI NHẤT (desc + limit) rồi trả về theo thứ tự thời gian tăng dần.
    rows = (
        db.query(Comment)
        .filter(Comment.entity == entity, Comment.entity_id == entity_id)
        .order_by(Comment.id.desc())
        .limit(500)
        .all()
    )
    return list(reversed(rows))


def resolve_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Batch resolve tên (tránh N+1): user_id -> full_name / email."""
    ids = {u for u in user_ids if u}
    if not ids:
        return {}
    users = db.query(User).filter(User.id.in_(ids)).all()
    emp_ids = {u.employee_id for u in users if u.employee_id}
    emps = (
        {e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
        if emp_ids else {}
    )
    out: dict[int, str] = {}
    for u in users:
        emp = emps.get(u.employee_id) if u.employee_id else None
        out[u.id] = (emp.full_name if emp else None) or u.email or f"User #{u.id}"
    return out


def check_parent(db: Session, entity: str, entity_id: int, parent_id: int | None) -> None:
    """M1: parent phải cùng (entity, entity_id) và là comment GỐC (ép threading 1 cấp)."""
    if not parent_id:
        return
    parent = db.get(Comment, parent_id)
    if not parent or parent.entity != entity or parent.entity_id != entity_id:
        raise ValueError("Bình luận cha không thuộc cùng luồng")
    if parent.parent_id:
        raise ValueError("Chỉ hỗ trợ trả lời 1 cấp")


def valid_mention_ids(db: Session, ids: list[int] | None) -> list[int]:
    """Lọc mention còn lại các user đang hoạt động (H2: tránh spam thông báo id rác/vô hiệu)."""
    wanted = {int(i) for i in (ids or []) if i}
    if not wanted:
        return []
    rows = db.query(User.id).filter(User.id.in_(wanted), User.is_active == True).all()  # noqa: E712
    return [r[0] for r in rows]


def collect_recipients(db: Session, c: Comment, survey_created_by: int) -> list[int]:
    """Người nhận thông báo: chủ phiếu + tác giả comment cha + người được @nhắc,
    trừ chính người vừa bình luận."""
    ids: set[int] = set()
    if survey_created_by:
        ids.add(survey_created_by)
    if c.parent_id:
        parent = db.get(Comment, c.parent_id)
        if parent and parent.created_by:
            ids.add(parent.created_by)
    for uid in (c.mention_user_ids or []):
        if uid:
            ids.add(int(uid))
    ids.discard(c.created_by)   # không tự báo mình
    return list(ids)


def notify_comment(db: Session, c: Comment, background_tasks, survey_id: int | None) -> None:
    """Bắn thông báo (in-app + push) cho người liên quan. Bỏ qua nếu không tra ra phiếu.
    doc_code LẤY TỪ SERVER (survey.code) — không nhận từ FE (H1: chống giả mạo tiêu đề)."""
    from app.modules.survey.model import Survey
    from app.modules.notification.service import trigger_notification

    survey = db.get(Survey, survey_id) if survey_id else None
    if not survey:
        return
    recipients = collect_recipients(db, c, survey.created_by or 0)
    if not recipients:
        return
    trigger_notification(
        db=db, event="survey_commented", doc_type="survey",
        doc_code=survey.code, creator_id=c.created_by,
        background_tasks=background_tasks, link=f"/surveys/{survey.id}",
        recipient_ids=recipients,
    )
