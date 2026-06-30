from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Survey, SurveyProductLine, SurveySupplierLine

ENTITY = "survey"
FILTERABLE = ["code", "pr_code", "status", "item_group", "nspt"]
HEADER_FIELDS = ["pr_code", "received_date", "result_due_date", "item_group",
                 "requirement_detail", "request_qty", "market_price", "nspt"]


def line_model(survey_type: str):
    return SurveySupplierLine if survey_type == "supplier" else SurveyProductLine


def get_survey(db: Session, sid: int) -> Survey:
    o = db.get(Survey, sid)
    if not o:
        raise HTTPException(404, "Không tìm thấy phiếu khảo sát")
    return o


def lines_of(db: Session, survey_type: str, sid: int):
    LM = line_model(survey_type)
    return db.query(LM).filter(LM.survey_id == sid).order_by(LM.id).all()


def _save_lines(db: Session, survey_type: str, sid: int, lines, user_id: int):
    LM = line_model(survey_type)
    db.query(LM).filter(LM.survey_id == sid).delete()
    for it in lines or []:
        data = it.model_dump()
        if survey_type == "product":
            amount = round((data.get("request_qty") or 0) * (data.get("price_by_volume") or 0)
                           * (1 + (data.get("vat") or 0) / 100), 2)
            data["amount"] = amount
            if not data.get("amount_converted"):
                data["amount_converted"] = amount
        db.add(LM(survey_id=sid, created_by=user_id, updated_by=user_id, **data))
    db.commit()


def list_surveys(db: Session, survey_type: str, base_query, pg: dict):
    q = base_query.filter(Survey.survey_type == survey_type)
    total = q.count()
    items = q.order_by(Survey.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def create_survey(db: Session, data, survey_type: str, user_id: int) -> Survey:
    s = Survey(code=data.code or "", survey_type=survey_type, status="draft",
               created_by=user_id, updated_by=user_id,
               **{f: getattr(data, f) for f in HEADER_FIELDS})
    db.add(s)
    db.commit()
    db.refresh(s)
    if not s.code:
        s.code = f"KS{s.id:05d}"
        db.commit()
    _save_lines(db, survey_type, s.id, data.lines, user_id)
    record(db, user_id, ENTITY, s.id, "create")
    return s


def update_survey(db: Session, sid: int, data, survey_type: str, user_id: int) -> Survey:
    s = get_survey(db, sid)
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi ở trạng thái Nháp/Từ chối")
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(s, k, v)
    s.updated_by = user_id
    db.commit()
    if data.lines is not None:
        _save_lines(db, survey_type, sid, data.lines, user_id)
    record(db, user_id, ENTITY, sid, "update")
    db.refresh(s)
    return s


def delete_survey(db: Session, sid: int, survey_type: str, user_id: int):
    s = get_survey(db, sid)
    LM = line_model(survey_type)
    db.query(LM).filter(LM.survey_id == sid).delete()
    db.delete(s)
    db.commit()
    record(db, user_id, ENTITY, sid, "delete")


def set_status(db: Session, sid: int, status: str, user_id: int, msg: str = "") -> Survey:
    s = get_survey(db, sid)
    s.status = status
    s.updated_by = user_id
    if status == "approved":
        s.approve_status = "Duyệt"
    elif status == "rejected":
        s.approve_status = "Không duyệt"
    if msg:
        s.approve_note = msg
    db.commit()
    record(db, user_id, ENTITY, sid, status, msg)
    db.refresh(s)
    return s
