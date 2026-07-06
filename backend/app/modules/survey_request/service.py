from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import SurveyRequest, SurveyRequestLine, SurveyRequestOption

ENTITY = "survey_request"
FILTERABLE = ["code", "status", "requester", "department"]
HEADER_FIELDS = ["company_id", "requester", "requester_position", "department",
                 "head_of_dept", "purpose", "request_date", "note"]


def get_sr(db: Session, sid: int) -> SurveyRequest:
    o = db.get(SurveyRequest, sid)
    if not o:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu khảo sát")
    return o


def lines_of(db: Session, sid: int):
    return (db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid)
            .order_by(SurveyRequestLine.id).all())


def options_of(db: Session, line_id: int):
    return (db.query(SurveyRequestOption).filter(SurveyRequestOption.survey_request_line_id == line_id)
            .order_by(SurveyRequestOption.public_id).all())


def _gen_code(db: Session) -> str:
    ddmmyy = datetime.now().strftime("%d%m%y")
    prefix = f"YCKS{ddmmyy}"
    n = db.query(SurveyRequest).filter(SurveyRequest.code.like(prefix + "%")).count()
    return f"{prefix}{n + 1:02d}"


def _save_lines(db: Session, sid: int, lines, user_id: int):
    db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid).delete()
    db.commit()
    for it in lines or []:
        ln = SurveyRequestLine(survey_request_id=sid, created_by=user_id, updated_by=user_id, **it.model_dump())
        db.add(ln)
        db.flush()
        ln.internal_line_code = f"YCKSL{ln.id:06d}"
    db.commit()


def create_sr(db: Session, data, user_id: int) -> SurveyRequest:
    s = SurveyRequest(code=data.code or "", status="draft", created_by=user_id, updated_by=user_id,
                      **{f: getattr(data, f) for f in HEADER_FIELDS})
    db.add(s)
    db.commit()
    db.refresh(s)
    if not s.code:
        s.code = _gen_code(db)
        db.commit()
    _save_lines(db, s.id, data.lines, user_id)
    record(db, user_id, ENTITY, s.id, "create")
    return s


def update_sr(db: Session, sid: int, data, user_id: int) -> SurveyRequest:
    s = get_sr(db, sid)
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi ở trạng thái Nháp/Từ chối")
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(s, k, v)
    s.updated_by = user_id
    db.commit()
    if data.lines is not None:
        _save_lines(db, sid, data.lines, user_id)
    record(db, user_id, ENTITY, sid, "update")
    db.refresh(s)
    return s


def delete_sr(db: Session, sid: int, user_id: int):
    s = get_sr(db, sid)
    line_ids = [ln.id for ln in lines_of(db, sid)]
    if line_ids:
        db.query(SurveyRequestOption).filter(SurveyRequestOption.survey_request_line_id.in_(line_ids)).delete(synchronize_session=False)
    db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid).delete()
    db.delete(s)
    db.commit()
    record(db, user_id, ENTITY, sid, "delete")


def set_status(db: Session, sid: int, status: str, user_id: int, reason: str = "") -> SurveyRequest:
    s = get_sr(db, sid)
    s.status = status
    s.updated_by = user_id
    if status == "rejected":
        s.reject_reason = reason
    db.commit()
    record(db, user_id, ENTITY, sid, status, reason)
    db.refresh(s)
    return s


def auto_assign(db: Session, s: SurveyRequest) -> int:
    """Sau khi trưởng phòng duyệt: tự gán NSTM cho từng dòng theo phân loại (tái dùng Task 4).
    Header.assignee_id = NSTM của dòng đầu tiên có phân loại được cấu hình."""
    from app.modules.category_assignee.service import resolve_for_group
    assigned = 0
    header_emp = None
    for ln in lines_of(db, s.id):
        if ln.assignee:
            continue
        emp = resolve_for_group(db, ln.item_group)
        if emp and emp.code:
            ln.assignee = emp.code
            assigned += 1
            if header_emp is None:
                header_emp = emp
    if header_emp and not s.assignee_id:
        s.assignee_id = header_emp.id
    if assigned or header_emp:
        db.commit()
    return assigned
