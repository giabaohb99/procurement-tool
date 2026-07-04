from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Survey, SurveyProductLine, SurveySupplierLine

ENTITY = "survey"
FILTERABLE = ["code", "pr_code", "status", "item_group", "nspt"]
HEADER_FIELDS = ["pr_code", "received_date", "result_due_date", "item_group",
                 "requirement_detail", "request_qty", "market_price", "nspt",
                 "has_product_code", "item_code", "item_name", "uom", "proposed_rate"]


def get_survey(db: Session, sid: int) -> Survey:
    o = db.get(Survey, sid)
    if not o:
        raise HTTPException(404, "Không tìm thấy phiếu khảo sát")
    return o


def supplier_lines_of(db: Session, sid: int):
    return (db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sid)
            .order_by(SurveySupplierLine.id).all())


def product_lines_of(db: Session, sid: int):
    return (db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == sid)
            .order_by(SurveyProductLine.id).all())


def _save_supplier_lines(db: Session, sid: int, lines, user_id: int):
    db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sid).delete()
    for it in lines or []:
        db.add(SurveySupplierLine(survey_id=sid, created_by=user_id, updated_by=user_id, **it.model_dump()))
    db.commit()


def _save_product_lines(db: Session, sid: int, lines, user_id: int):
    db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == sid).delete()
    for it in lines or []:
        data = it.model_dump()
        amount = round((data.get("request_qty") or 0) * (data.get("price_by_volume") or 0)
                       * (1 + (data.get("vat") or 0) / 100), 2)
        data["amount"] = amount
        if not data.get("amount_converted"):
            data["amount_converted"] = amount
        db.add(SurveyProductLine(survey_id=sid, created_by=user_id, updated_by=user_id, **data))
    db.commit()


def list_surveys(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Survey.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def create_survey(db: Session, data, user_id: int) -> Survey:
    s = Survey(code=data.code or "", survey_type="combined", status="draft",
               created_by=user_id, updated_by=user_id,
               **{f: getattr(data, f) for f in HEADER_FIELDS})
    db.add(s)
    db.commit()
    db.refresh(s)
    if not s.code:
        s.code = f"KS{s.id:05d}"
        db.commit()
    _save_supplier_lines(db, s.id, data.supplier_lines, user_id)
    _save_product_lines(db, s.id, data.product_lines, user_id)
    record(db, user_id, ENTITY, s.id, "create")
    return s


def update_survey(db: Session, sid: int, data, user_id: int) -> Survey:
    s = get_survey(db, sid)
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi ở trạng thái Nháp/Từ chối")
    for k, v in data.model_dump(exclude_unset=True, exclude={"supplier_lines", "product_lines"}).items():
        setattr(s, k, v)
    s.updated_by = user_id
    db.commit()
    if data.supplier_lines is not None:
        _save_supplier_lines(db, sid, data.supplier_lines, user_id)
    if data.product_lines is not None:
        _save_product_lines(db, sid, data.product_lines, user_id)
    record(db, user_id, ENTITY, sid, "update")
    db.refresh(s)
    return s


def approve_lines(db: Session, sid: int, data, user_id: int) -> Survey:
    """Quản lý/Admin duyệt TỪNG dòng (cả 2 bảng) khi phiếu đã gửi duyệt."""
    s = get_survey(db, sid)
    sup = {r.id: r for r in supplier_lines_of(db, sid)}
    prod = {r.id: r for r in product_lines_of(db, sid)}
    for it in data.supplier_lines:
        row = sup.get(it.id)
        if row:
            if it.line_approve is not None:
                row.line_approve = it.line_approve
            if it.line_approve_note is not None:
                row.line_approve_note = it.line_approve_note
    for it in data.product_lines:
        row = prod.get(it.id)
        if row:
            if it.line_approve is not None:
                row.line_approve = it.line_approve
            if it.line_approve_note is not None:
                row.line_approve_note = it.line_approve_note
    s.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "line_approve", "Duyệt dòng khảo sát")
    db.refresh(s)
    return s


def delete_survey(db: Session, sid: int, user_id: int):
    s = get_survey(db, sid)
    from app.modules.attachment.service import delete_attachments_for
    line_ids = ([ln.id for ln in supplier_lines_of(db, sid)]
                + [ln.id for ln in product_lines_of(db, sid)])
    delete_attachments_for(db, [("survey", sid)] + [("survey_line", lid) for lid in line_ids])
    db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sid).delete()
    db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == sid).delete()
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
