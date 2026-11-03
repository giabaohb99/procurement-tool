"""YCBG — phương án khảo sát của dòng: thêm, đồng bộ từ phiếu khảo sát, xóa, sửa ghi chú, chọn (bao-CR-715 tách từ
service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.text_limits import ensure_model_fits

from .model import LS_RESURVEY, SurveyRequest, SurveyRequestLine, SurveyRequestOption
from .base_service import ENTITY, MAX_OPTIONS_PER_LINE, lines_of, options_of
from .line_service import resolve_supplier_name


def _line_label(line: SurveyRequestLine) -> str:
    """Nhãn ngắn của dòng YCBG để ghi vào dấu vết — phân loại, không có thì lấy id."""
    return (line.item_group or "").strip() or f"dòng #{line.id}"


def create_option(db: Session, line: SurveyRequestLine, psl_id: int, user_id: int,
                  audit: bool = True) -> SurveyRequestOption:
    """Gắn 1 dòng khảo sát SP đã duyệt vào dòng yêu cầu → tạo option (snapshot + ẩn danh public_id).

    `audit=False` cho đường ĐỒNG BỘ TỰ ĐỘNG — nó đã tự ghi một dòng `sync_options`
    tổng kết cả lượt, thêm dấu vết từng option nữa là ghi đôi."""
    from app.modules.survey.model import Survey, SurveyProductLine
    psl = db.get(SurveyProductLine, psl_id)
    if not psl:
        raise HTTPException(404, "Không tìm thấy dòng khảo sát sản phẩm")
    if psl.line_approve != "Đã duyệt":
        raise HTTPException(400, "Dòng khảo sát chưa được duyệt")
    if any(o.product_survey_line_id == psl_id for o in options_of(db, line.id)):
        raise HTTPException(400, "Dòng khảo sát này đã được gắn làm option")
    if len(options_of(db, line.id)) >= MAX_OPTIONS_PER_LINE:
        raise HTTPException(400, f"Mỗi sản phẩm chỉ được tối đa {MAX_OPTIONS_PER_LINE} phương án khảo sát")
    survey = db.get(Survey, psl.survey_id)
    if survey is not None and survey.is_deleted:   # ai-CR-176
        raise HTTPException(400, "Phiếu khảo sát của dòng này đã bị xóa")
    public_id = len(options_of(db, line.id)) + 1
    o = SurveyRequestOption(
        survey_request_line_id=line.id,
        product_survey_line_id=psl.id,
        public_id=public_id,
        display_label=f"Option {public_id}",
        created_by=user_id, updated_by=user_id,
        # snapshot (hiện được với người YC)
        snap_product_name=psl.product_name or "",
        snap_spec=psl.spec or "",
        snap_origin=psl.origin or "",
        snap_quote_unit=psl.quote_unit or "",
        snap_moq=psl.moq or 0,
        snap_price_by_volume=psl.price_by_volume or 0,
        snap_volume_range=psl.volume_range or "",
        snap_vat=psl.vat or 0,
        snap_delivery_time=psl.delivery_time or "",
        snap_delivery_place=psl.delivery_place or "",
        snap_shipping_cost=psl.shipping_cost or 0,
        snap_sample_ready=bool(psl.sample_ready),
        snap_lab_result=psl.lab_result or "",
        # tự lấy Mã SP hệ thống từ HEADER phiếu khảo sát (Mã VTBB/VL) nếu có; NSTM override được sau
        system_product_code=(survey.item_code or "") if survey else "",
        # nội bộ NSTM (backend LỌC khỏi view người YC)
        snap_internal_code=psl.internal_code or "",
        supplier_code=psl.supplier_code or "",
        supplier_name=resolve_supplier_name(db, psl.supplier_code or ""),
        supplier_survey_id=psl.survey_id or 0,
        nstm_note=psl.nspt_reason or "",
    )
    db.add(o)
    line.no_option = False   # đã có phương án -> bỏ cờ chốt rỗng (nếu trước đó chốt rỗng)
    db.commit()
    db.refresh(o)
    o.display_label = f"Option {public_id} — ID {o.id}"
    db.commit()
    if audit:
        #  ⚠️ KHÔNG ghi tên NCC vào đây. Nhật ký của phiếu đọc được bằng
        #  `survey_request.read` — người YÊU CẦU có khóa đó, mà cả cơ chế option là
        #  để giấu NCC với chính họ. Tên SP thì đã hiện sẵn trên thẻ phương án.
        #  Phân loại của phiếu khảo sát nguồn ghi kèm để đối chiếu về sau — ticket
        #  07/09/2026 là một phương án "Thùng" nằm trong dòng "Chai Pet", và không
        #  có dòng nhật ký nào nói ra chuyện đó.
        sv_group = (survey.item_group or "") if survey else ""
        record(db, user_id, ENTITY, line.survey_request_id, "add_option",
               f"Gắn {o.display_label} vào dòng \"{_line_label(line)}\": "
               f"{o.snap_product_name or '—'} (khảo sát thuộc \"{sv_group or '—'}\")")
    return o


def sync_options_from_surveys(db: Session, sid: int, user_id: int = 0) -> int:
    """Tự gắn option cho các dòng YCKS từ dòng khảo sát SP ĐÃ DUYỆT (Survey.status='approved',
    line_approve='Đã duyệt') thuộc các Phiếu khảo sát ĐÃ LIÊN KẾT với YCKS này (survey_request_id).
    Khớp theo phân loại (item_group). Bỏ qua dòng đã gắn. Trả số option mới thêm."""
    from app.modules.survey.model import Survey, SurveyProductLine
    # CHỈ lấy từ phiếu khảo sát ĐÃ LIÊN KẾT với YCKS này; không cần duyệt cả phiếu,
    # chỉ cần DÒNG được duyệt (line_approve='Đã duyệt'). Bỏ phiếu đã hủy/bị từ chối.
    surveys = (db.query(Survey)
               .filter(Survey.survey_request_id == sid,
                       Survey.is_deleted.is_(False),   # ai-CR-176
                       Survey.status.notin_(["cancelled"])).all())
    if not surveys:
        return 0
    sr_lines = lines_of(db, sid)
    added = 0
    for sv in surveys:
        psls = (db.query(SurveyProductLine)
                .filter(SurveyProductLine.survey_id == sv.id,
                        SurveyProductLine.line_approve == "Đã duyệt").all())
        if not psls:
            continue
        targets = [ln for ln in sr_lines if (ln.item_group or "") == (sv.item_group or "")]
        if not targets and len(sr_lines) == 1:
            targets = sr_lines  # YCKS chỉ 1 dòng -> gắn vào dòng đó dù phân loại lệch
        for ln in targets:
            existing = {o.product_survey_line_id for o in options_of(db, ln.id)}
            for psl in psls:
                if psl.id in existing:
                    continue
                try:
                    create_option(db, ln, psl.id, user_id or 0, audit=False)
                    added += 1
                except HTTPException:
                    pass
    if added:
        record(db, user_id or 0, ENTITY, sid, "sync_options",
               f"Tự gắn {added} phương án từ phiếu khảo sát đã duyệt")
    return added


def delete_option(db: Session, line_id: int, oid: int, user_id: int = 0):
    o = (db.query(SurveyRequestOption)
         .filter(SurveyRequestOption.id == oid, SurveyRequestOption.survey_request_line_id == line_id).first())
    if not o:
        raise HTTPException(404, "Không tìm thấy option")
    label, product = o.display_label, o.snap_product_name
    db.delete(o)
    db.commit()

    # Tự động cập nhật trạng thái phiếu thành đang xử lý nếu không còn option nào
    line = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id).first()
    if line:
        record(db, user_id, ENTITY, line.survey_request_id, "del_option",
               f"Gỡ {label or f'option #{oid}'} khỏi dòng \"{_line_label(line)}\": "
               f"{product or '—'}")
        req_id = line.survey_request_id
        total_opts = (db.query(SurveyRequestOption)
                      .join(SurveyRequestLine, SurveyRequestOption.survey_request_line_id == SurveyRequestLine.id)
                      .filter(SurveyRequestLine.survey_request_id == req_id)
                      .count())
        if total_opts == 0:
            req = db.query(SurveyRequest).filter(SurveyRequest.id == req_id).first()
            if req and req.status != "processing":
                req.status = "processing"
                db.commit()


def update_option_note(db: Session, line_id: int, oid: int, note: str, user_id: int) -> SurveyRequestOption:
    return set_option_fields(db, line_id, oid, user_id, nstm_note=note or "")


def set_option_fields(db: Session, line_id: int, oid: int, user_id: int, **fields) -> SurveyRequestOption:
    """Cập nhật các field cho phép của 1 option (ghi chú NSTM, mã SP hệ thống)."""
    o = (db.query(SurveyRequestOption)
         .filter(SurveyRequestOption.id == oid, SurveyRequestOption.survey_request_line_id == line_id).first())
    if not o:
        raise HTTPException(404, "Không tìm thấy option")
    #  bao-CR-538: body là `dict` thô (không qua schema) → soi độ dài theo cột trước khi gán.
    ensure_model_fits(SurveyRequestOption, {k: (v.strip() if isinstance(v, str) else v)
                                            for k, v in fields.items() if v is not None})
    for k in ("nstm_note", "system_product_code"):
        if k in fields and fields[k] is not None:
            setattr(o, k, (fields[k] or "").strip() if k == "system_product_code" else (fields[k] or ""))
    o.updated_by = user_id
    db.commit()
    db.refresh(o)
    return o


def choose_option(db: Session, line_id: int, oid: int, user_id: int) -> SurveyRequestOption:
    """Người YC chọn 1 option cho 1 dòng. Bấm lại đúng option đang chọn -> BỎ CHỌN (toggle)."""
    target = (db.query(SurveyRequestOption)
              .filter(SurveyRequestOption.id == oid,
                      SurveyRequestOption.survey_request_line_id == line_id).first())
    if not target:
        raise HTTPException(404, "Không tìm thấy option")
    already = bool(target.is_chosen)
    for o in options_of(db, line_id):
        o.is_chosen = (o.id == oid) and not already   # bấm lại option đang chọn -> bỏ chọn cả dòng
        if o.is_chosen:
            o.chosen_by = user_id
            o.updated_by = user_id
    # Hướng B: vừa chọn 1 PA (not already) thì TỰ GỠ cờ "Cần khảo sát lại" nếu đang bật —
    # coi như người YC đã đồng ý phương án, không còn yêu cầu khảo sát lại.
    ln = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id).first()
    if not already and ln and ln.line_status == LS_RESURVEY:
        ln.line_status = ""
        ln.updated_by = user_id
    db.commit()
    db.refresh(target)
    if ln:
        note = (f"Chốt {target.display_label} cho dòng \"{_line_label(ln)}\": "
                f"{target.snap_product_name or '—'}") if not already else \
               (f"Bỏ chốt {target.display_label} của dòng \"{_line_label(ln)}\"")
        record(db, user_id, ENTITY, ln.survey_request_id,
               "unchoose_option" if already else "choose_option", note)
    return target
