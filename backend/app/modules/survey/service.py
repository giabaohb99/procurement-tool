from fastapi import HTTPException
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Survey, SurveyProductLine, SurveySupplierLine

# Cột KHÔNG copy khi nhân bản dòng (id/khóa/nhật ký/kết quả duyệt → làm mới)
_LINE_SKIP = {"id", "survey_id", "created_by", "updated_by", "created_at", "updated_at",
              "line_approve", "approve_note"}

ENTITY = "survey"
FILTERABLE = ["code", "pr_code", "sr_code", "status", "item_group", "nspt", "main_content"]
HEADER_FIELDS = ["pr_code", "survey_request_id", "sr_code", "received_date", "result_due_date", "item_group",
                 "main_content", "requirement_detail", "request_qty", "market_price", "nspt",
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


def _reconcile_sr_link(db: Session, s: Survey) -> None:
    """Đồng bộ liên kết YCKS: điền cái còn thiếu (survey_request_id <-> sr_code) từ cái đã có."""
    from app.modules.survey_request.model import SurveyRequest
    if s.survey_request_id and not s.sr_code:
        sr = db.get(SurveyRequest, s.survey_request_id)
        if sr:
            s.sr_code = sr.code
    elif s.sr_code and not s.survey_request_id:
        sr = db.query(SurveyRequest).filter(SurveyRequest.code == s.sr_code).first()
        if sr:
            s.survey_request_id = sr.id


def create_survey(db: Session, data, user_id: int) -> Survey:
    s = Survey(code=data.code or "", survey_type="combined", status="draft",
               created_by=user_id, updated_by=user_id,
               **{f: getattr(data, f) for f in HEADER_FIELDS})
    db.add(s)
    db.commit()
    db.refresh(s)
    if not s.code:
        s.code = f"KS{s.id:05d}"
    _reconcile_sr_link(db, s)
    db.commit()
    _save_supplier_lines(db, s.id, data.supplier_lines, user_id)
    _save_product_lines(db, s.id, data.product_lines, user_id)
    record(db, user_id, ENTITY, s.id, "create")
    return s


def copy_survey(db: Session, sid: int, user_id: int) -> Survey:
    """Nhân bản phiếu khảo sát thành phiếu NHÁP mới: copy header + dòng NCC + dòng SP.
    KHÔNG copy liên kết YCKS/PYC (survey_request_id/sr_code/pr_code) và kết quả duyệt → độc lập."""
    src = get_survey(db, sid)
    link_fields = {"pr_code", "survey_request_id", "sr_code"}
    header = {f: getattr(src, f) for f in HEADER_FIELDS if f not in link_fields}
    s = Survey(code="", survey_type="combined", status="draft",
               created_by=user_id, updated_by=user_id, **header)
    db.add(s)
    db.commit()
    db.refresh(s)
    s.code = f"KS{s.id:05d}"
    db.commit()

    def _copy_line(ln, model):
        data = {c.key: getattr(ln, c.key) for c in sa_inspect(ln).mapper.column_attrs
                if c.key not in _LINE_SKIP}
        db.add(model(survey_id=s.id, created_by=user_id, updated_by=user_id, **data))

    for ln in supplier_lines_of(db, sid):
        _copy_line(ln, SurveySupplierLine)
    for ln in product_lines_of(db, sid):
        _copy_line(ln, SurveyProductLine)
    db.commit()
    record(db, user_id, ENTITY, s.id, "create", f"Nhân bản từ {src.code}")
    db.refresh(s)
    return s


def update_survey(db: Session, sid: int, data, user_id: int) -> Survey:
    s = get_survey(db, sid)
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại")
    for k, v in data.model_dump(exclude_unset=True, exclude={"supplier_lines", "product_lines"}).items():
        setattr(s, k, v)
    s.updated_by = user_id
    _reconcile_sr_link(db, s)
    db.commit()
    if data.supplier_lines is not None:
        _save_supplier_lines(db, sid, data.supplier_lines, user_id)
    if data.product_lines is not None:
        _save_product_lines(db, sid, data.product_lines, user_id)
    record(db, user_id, ENTITY, sid, "update")
    db.refresh(s)
    return s


def _purge_yc_options(db: Session, product_line_ids: list[int]) -> int:
    """Gỡ các option Yêu cầu khảo sát (YCKS) đang tham chiếu dòng khảo sát SP KHÔNG còn hợp lệ
    (dòng bị 'Không duyệt' hoặc phiếu khảo sát bị hủy). Tránh option lỗi vẫn hiện/gắn được.
    Dùng delete_option để tự cập nhật trạng thái YCKS. Trả số option đã gỡ."""
    ids = [i for i in product_line_ids if i]
    if not ids:
        return 0
    from app.modules.survey_request.model import SurveyRequestOption
    from app.modules.survey_request.service import delete_option
    opts = (db.query(SurveyRequestOption)
            .filter(SurveyRequestOption.product_survey_line_id.in_(ids)).all())
    for o in opts:
        delete_option(db, o.survey_request_line_id, o.id)
    return len(opts)


def approve_lines(db: Session, sid: int, data, user_id: int) -> Survey:
    """Quản lý/Admin duyệt TỪNG dòng (cả 2 bảng) khi phiếu đã gửi duyệt.
    Dòng SP chuyển sang KHÔNG duyệt -> gỡ mọi option YCKS đang tham chiếu dòng đó."""
    s = get_survey(db, sid)
    if s.status in ("cancelled", "rejected"):
        raise HTTPException(400, "Phiếu đã bị từ chối/trả lại — không thể duyệt dòng")
    sup = {r.id: r for r in supplier_lines_of(db, sid)}
    prod = {r.id: r for r in product_lines_of(db, sid)}
    for it in data.supplier_lines:
        row = sup.get(it.id)
        if row:
            if it.line_approve is not None:
                row.line_approve = it.line_approve
            if it.line_approve_note is not None:
                row.line_approve_note = it.line_approve_note
    stale_product_ids = []
    for it in data.product_lines:
        row = prod.get(it.id)
        if row:
            if it.line_approve is not None:
                row.line_approve = it.line_approve
            if it.line_approve_note is not None:
                row.line_approve_note = it.line_approve_note
            if row.line_approve == "Không duyệt":   # chỉ TỪ CHỐI DỨT KHOÁT mới xóa cứng option
                stale_product_ids.append(row.id)     # (trạng thái tạm để valid_options_of ẩn tạm)
    s.updated_by = user_id
    db.commit()
    _purge_yc_options(db, stale_product_ids)   # dòng bị Không duyệt -> gỡ option YCKS tham chiếu
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


MISSING = "Thiếu thông tin"
_LINE_AUDIT = {"id", "survey_id", "created_at", "created_by", "updated_at", "updated_by"}


def _line_model(table: str):
    return SurveySupplierLine if table == "supplier" else SurveyProductLine


def fill_missing_line(db: Session, sid: int, table: str, line_id: int, data: dict, user_id: int) -> Survey:
    """Ngoại lệ có kiểm soát: nhân sự phụ trách bổ sung 1 DÒNG đang 'Thiếu thông tin',
    bất kể phiếu đang Chờ duyệt hay Đã duyệt (không mở khóa toàn phiếu, không trả lại đơn).
    Bổ sung xong → dòng tự về 'Chờ duyệt' để duyệt lại."""
    if table not in ("supplier", "product"):
        raise HTTPException(400, "Loại bảng không hợp lệ")
    LM = _line_model(table)
    row = db.query(LM).filter(LM.id == line_id, LM.survey_id == sid).first()
    if not row:
        raise HTTPException(404, "Không tìm thấy dòng khảo sát")
    if (row.line_approve or "") != MISSING:
        raise HTTPException(403, "Chỉ được bổ sung dòng đang ở trạng thái 'Thiếu thông tin'")
    for k, v in (data or {}).items():
        if k in _LINE_AUDIT or k in ("line_approve", "line_approve_note"):
            continue
        if hasattr(row, k):
            setattr(row, k, v)
    if table == "product":
        amt = round(float(row.request_qty or 0) * float(row.price_by_volume or 0)
                    * (1 + float(row.vat or 0) / 100), 2)
        row.amount = amt
        if not row.amount_converted:
            row.amount_converted = amt
    row.line_approve = "Chờ duyệt"
    row.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "fill_line", f"Bổ sung dòng {table}#{line_id}")
    return get_survey(db, sid)


def report_rows(db: Session, base_survey_query):
    """Chuẩn hóa TẤT CẢ dòng khảo sát (NCC + SP) trong phạm vi cho phép → list dict (theo dòng)."""
    surveys = {s.id: s for s in base_survey_query.all()}
    if not surveys:
        return []
    sids = list(surveys.keys())
    rows = []
    for x in db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id.in_(sids)).all():
        s = surveys[x.survey_id]
        rows.append({"survey_id": s.id, "survey_code": s.code, "kind": "supplier", "line_id": x.id,
                     "content": x.supplier_name or x.supplier_code or "", "supplier_code": x.supplier_code or "",
                     "item_group": s.item_group or "", "nspt": s.nspt or "",
                     "date": x.contact_date or s.received_date or "",
                     "line_approve": x.line_approve or "Chờ duyệt", "line_approve_note": x.line_approve_note or "",
                     "survey_status": s.status})
    for x in db.query(SurveyProductLine).filter(SurveyProductLine.survey_id.in_(sids)).all():
        s = surveys[x.survey_id]
        rows.append({"survey_id": s.id, "survey_code": s.code, "kind": "product", "line_id": x.id,
                     "content": x.product_name or "", "supplier_code": x.supplier_code or "",
                     "item_group": s.item_group or "", "nspt": s.nspt or "",
                     "date": x.contact_date or s.received_date or "",
                     "line_approve": x.line_approve or "Chờ duyệt", "line_approve_note": x.line_approve_note or "",
                     "survey_status": s.status})
    return rows


def lines_by_supplier(db: Session, tax_code: str, supplier_code: str):
    """Task 9: dòng khảo sát của 1 NCC. KSNCC match theo tax_code (fallback supplier_code);
    KSSP match theo supplier_code (product line không có tax_code)."""
    from sqlalchemy import or_
    sup = []
    conds = []
    if tax_code:
        conds.append(SurveySupplierLine.tax_code == tax_code)
    if supplier_code:
        conds.append(SurveySupplierLine.supplier_code == supplier_code)
    if conds:
        sup = db.query(SurveySupplierLine).filter(or_(*conds)).order_by(SurveySupplierLine.id.desc()).all()
    prod = []
    if supplier_code:
        prod = (db.query(SurveyProductLine).filter(SurveyProductLine.supplier_code == supplier_code)
                .order_by(SurveyProductLine.id.desc()).all())
    sids = {x.survey_id for x in sup} | {x.survey_id for x in prod}
    codes = {s.id: s.code for s in db.query(Survey).filter(Survey.id.in_(sids)).all()} if sids else {}
    sup_rows = [{"survey_id": x.survey_id, "survey_code": codes.get(x.survey_id, ""), "line_id": x.id,
                 "supplier_code": x.supplier_code, "supplier_name": x.supplier_name, "tax_code": x.tax_code,
                 "contact_date": x.contact_date, "contact_person": x.contact_person, "contact_phone": x.contact_phone,
                 "line_approve": x.line_approve or "Chờ duyệt", "note": x.note or ""} for x in sup]
    prod_rows = [{"survey_id": x.survey_id, "survey_code": codes.get(x.survey_id, ""), "line_id": x.id,
                  "supplier_code": x.supplier_code, "internal_code": x.internal_code, "product_name": x.product_name,
                  "quote_unit": x.quote_unit, "price_by_volume": float(x.price_by_volume or 0),
                  "moq": float(x.moq or 0), "line_approve": x.line_approve or "Chờ duyệt", "note": x.note or ""}
                 for x in prod]
    return sup_rows, prod_rows


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
    if status == "cancelled":   # phiếu khảo sát bị hủy -> gỡ option YCKS tham chiếu mọi dòng SP của phiếu
        _purge_yc_options(db, [ln.id for ln in product_lines_of(db, sid)])
    record(db, user_id, ENTITY, sid, status, msg)
    db.refresh(s)
    return s
