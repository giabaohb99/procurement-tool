from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import SurveyRequest, SurveyRequestLine, SurveyRequestOption

ENTITY = "survey_request"
FILTERABLE = ["code", "status", "requester", "department"]
MAX_OPTIONS_PER_LINE = 5   # mỗi sản phẩm (dòng YCKS) tối đa 5 phương án khảo sát
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
    if status in ("rejected", "cancelled"):
        s.reject_reason = reason
    db.commit()
    record(db, user_id, ENTITY, sid, status, reason)
    db.refresh(s)
    return s


# ───────────────────────── Phase 5B: xử lý khảo sát (NSTM) ─────────────────────────

def get_line(db: Session, sid: int, line_id: int) -> SurveyRequestLine:
    ln = (db.query(SurveyRequestLine)
          .filter(SurveyRequestLine.id == line_id, SurveyRequestLine.survey_request_id == sid).first())
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng khảo sát")
    return ln


def resolve_supplier_name(db: Session, code: str) -> str:
    if not code:
        return ""
    from app.modules.supplier.model import Supplier
    sup = db.query(Supplier).filter(Supplier.code == code).first()
    return sup.name if sup else code


def is_purchaser(profile: dict) -> bool:
    """NSTM/Quản lý/Admin TM = có grant survey_request read với scope proc|all.
    Người YC (own) & trưởng BP (dept) KHÔNG phải purchaser → không xem được màn xử lý (ẩn NCC)."""
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if p and p.get("read") and p.get("scope") in ("proc", "all"):
            return True
    return False


def _has_scope_all(profile: dict) -> bool:
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if p and p.get("read") and p.get("scope") == "all":
            return True
    return False


def can_process_line(db: Session, line: SurveyRequestLine, profile: dict) -> bool:
    """Ai được gắn/xóa option cho 1 dòng:
       - Quản lý/Admin TM (scope=all): mọi dòng.
       - NSTM (scope=proc): là NSTM chính HOẶC phụ của phân loại dòng, hoặc dòng đã gán mã mình."""
    if _has_scope_all(profile):
        return True
    emp_id = profile.get("employee_id") or 0
    emp_code = profile.get("emp_code") or ""
    if emp_code and line.assignee == emp_code:
        return True
    if not emp_id:
        return False
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee
    row = (db.query(CategoryAssignee)
           .join(ItemGroup, ItemGroup.id == CategoryAssignee.item_group_id)
           .filter(ItemGroup.name == line.item_group).first())
    return bool(row and emp_id in (row.primary_employee_id, row.backup_employee_id))


def visible_lines_for(db: Session, s, lines, user, profile: dict):
    """Lọc dòng theo NGƯỜI XEM: Quản lý/Admin TM (scope=all) & người TẠO phiếu -> thấy hết;
    NSTM -> chỉ thấy dòng mình xử lý được (được giao / phụ trách phân loại)."""
    if _has_scope_all(profile) or getattr(user, "id", 0) == getattr(s, "created_by", None):
        return list(lines)
    return [ln for ln in lines if can_process_line(db, ln, profile)]


def available_survey_lines(db: Session, supplier_code: str = "", item_group: str = "", search: str = ""):
    """Dòng khảo sát SẢN PHẨM đã DUYỆT (line_approve='Đã duyệt') — nguồn để tạo option.
    Dùng cho CHỌN NCC THỦ CÔNG: lọc mở theo nhiều tiêu chí (tùy chọn, KHÔNG giới hạn liên kết YCKS):
    - supplier_code: theo NCC (tùy chọn).
    - item_group: theo PHÂN LOẠI của Survey cha (mặc định = phân loại dòng, đổi được).
    - search: khớp Tên SP hoặc Mã SP theo NCC (LIKE).
    Cần ít nhất 1 tiêu chí (controller đã chặn rỗng). Giới hạn 100 dòng."""
    from sqlalchemy import or_
    from app.modules.survey.model import Survey, SurveyProductLine
    q = (db.query(SurveyProductLine)
         .join(Survey, Survey.id == SurveyProductLine.survey_id)
         .filter(SurveyProductLine.line_approve == "Đã duyệt",
                 Survey.status.notin_(["cancelled"])))
    if supplier_code:
        q = q.filter(SurveyProductLine.supplier_code == supplier_code)
    if item_group:
        q = q.filter(Survey.item_group == item_group)
    if (search or "").strip():
        like = f"%{search.strip()}%"
        q = q.filter(or_(SurveyProductLine.product_name.ilike(like),
                         SurveyProductLine.internal_code.ilike(like)))
    return q.order_by(SurveyProductLine.id.desc()).limit(100).all()


def create_option(db: Session, line: SurveyRequestLine, psl_id: int, user_id: int) -> SurveyRequestOption:
    """Gắn 1 dòng khảo sát SP đã duyệt vào dòng yêu cầu → tạo option (snapshot + ẩn danh public_id)."""
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
    db.commit()
    db.refresh(o)
    o.display_label = f"Option {public_id} — ID {o.id}"
    db.commit()
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
                    create_option(db, ln, psl.id, user_id or 0)
                    added += 1
                except HTTPException:
                    pass
    if added:
        record(db, user_id or 0, ENTITY, sid, "sync_options",
               f"Tự gắn {added} phương án từ phiếu khảo sát đã duyệt")
    return added


def delete_option(db: Session, line_id: int, oid: int):
    o = (db.query(SurveyRequestOption)
         .filter(SurveyRequestOption.id == oid, SurveyRequestOption.survey_request_line_id == line_id).first())
    if not o:
        raise HTTPException(404, "Không tìm thấy option")
    db.delete(o)
    db.commit()

    # Tự động cập nhật trạng thái phiếu thành đang xử lý nếu không còn option nào
    line = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id).first()
    if line:
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
    for k in ("nstm_note", "system_product_code"):
        if k in fields and fields[k] is not None:
            setattr(o, k, (fields[k] or "").strip() if k == "system_product_code" else (fields[k] or ""))
    o.updated_by = user_id
    db.commit()
    db.refresh(o)
    return o


def choose_option(db: Session, line_id: int, oid: int, user_id: int) -> SurveyRequestOption:
    """Người YC chọn 1 option cho 1 dòng (bỏ chọn các option khác cùng dòng)."""
    target = (db.query(SurveyRequestOption)
              .filter(SurveyRequestOption.id == oid,
                      SurveyRequestOption.survey_request_line_id == line_id).first())
    if not target:
        raise HTTPException(404, "Không tìm thấy option")
    for o in options_of(db, line_id):
        o.is_chosen = (o.id == oid)
        if o.id == oid:
            o.chosen_by = user_id
            o.updated_by = user_id
    db.commit()
    db.refresh(target)
    return target


# ───────────────────────── Phase 5D: sinh PYC từ option đã chọn ─────────────────────────

def _gen_pr_code(db: Session, request_date: str = "") -> str:
    from app.modules.purchase_request.model import PurchaseRequest
    date_str = ""
    if request_date and len(request_date) >= 10 and "-" in request_date:
        p = request_date.split("-")
        if len(p) == 3:
            date_str = f"{p[2]}{p[1]}{p[0][-2:]}"
    if not date_str:
        date_str = datetime.now().strftime("%d%m%y")
    prefix = f"PYC{date_str}"
    last = (db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%"))
            .order_by(PurchaseRequest.code.desc()).first())
    seq = 1
    if last and last.code.startswith(prefix):
        try:
            seq = int(last.code[len(prefix):]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:02d}"


def create_prs(db: Session, sid: int, user_id: int):
    """Gom option đã chọn theo NCC → mỗi NCC 1 PYC nháp (giá từ snapshot khảo sát).
    Cập nhật dòng: pr_id/pr_code/is_completed; phiếu KS → 'pr_created'."""
    from app.modules.purchase_request.model import (PurchaseRequest,
                                                    PurchaseRequestItem)
    from app.modules.purchase_request.service import find_dept_head
    from app.modules.supplier.model import Supplier
    s = get_sr(db, sid)
    if s.status != "survey_done":
        raise HTTPException(400, "Chỉ tạo YCMH khi phiếu đã khảo sát xong")

    groups: dict[str, list] = {}
    for ln in lines_of(db, sid):
        if ln.is_completed:
            continue
        chosen = [o for o in options_of(db, ln.id) if o.is_chosen]
        if not chosen:
            raise HTTPException(400, f"Sản phẩm '{ln.item_group or ln.id}' chưa chọn phương án")
        groups.setdefault(chosen[0].supplier_code or "", []).append((ln, chosen[0]))
    if not groups:
        raise HTTPException(400, "Không có phương án nào để tạo YCMH")

    today = datetime.now().strftime("%Y-%m-%d")
    created = []
    for sup_code, items in groups.items():
        sup = db.query(Supplier).filter(Supplier.code == sup_code).first() if sup_code else None
        first_opt = items[0][1]
        pr = PurchaseRequest(
            code=_gen_pr_code(db, today), company_id=s.company_id, requester=s.requester,
            requester_position=s.requester_position, department=s.department,
            head_of_dept=s.head_of_dept or find_dept_head(db, s.department or ""),
            purpose=s.purpose, request_date=today, status="draft",
            note=f"Sinh tự động từ Yêu cầu khảo sát {s.code}",
            suggested_supplier=first_opt.supplier_name or "",
            suggested_supplier_tax_code=(sup.tax_code if sup else ""),
            suggested_supplier_contact=(sup.address if sup else ""),   # Liên hệ NCC lấy Địa chỉ từ bảng NCC
            created_by=user_id, updated_by=user_id,
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
        for ln, opt in items:
            qty = float(ln.request_qty or 0)
            price = float(opt.snap_price_by_volume or 0)
            db.add(PurchaseRequestItem(
                pr_id=pr.id,
                product_code=(opt.system_product_code or "").strip(),   # mã SP hệ thống gắn ở option
                product_name=opt.snap_product_name or ln.requirement_detail or "Sản phẩm",
                item_group=ln.item_group or "", qty=qty, unit=opt.snap_quote_unit or ln.uom or "",
                price=price, amount=qty * price, note="",
                line_status="Chưa đặt hàng", created_by=user_id, updated_by=user_id,
            ))
            ln.pr_id = pr.id
            ln.pr_code = pr.code
            ln.is_completed = True
            ln.updated_by = user_id
        db.commit()
        created.append(pr)

    s.status = "pr_created"
    s.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "pr_created")
    return created


def finalize_sr(db: Session, sid: int, user_id: int) -> SurveyRequest:
    """Admin/QL chuyển Hoàn thành (dừng hẳn). pr_created → done."""
    s = get_sr(db, sid)
    if s.status != "pr_created":
        raise HTTPException(400, "Chỉ hoàn thành phiếu đã tạo Yêu cầu mua hàng")
    return set_status(db, sid, "done", user_id)


def auto_complete_from_pr(db: Session, pr_id: int, user_id: int = 0) -> None:
    """Khi 1 Yêu cầu mua hàng (PR) hoàn thành: nếu Yêu cầu khảo sát liên quan (qua line.pr_id)
    đang ở 'pr_created' VÀ tất cả các PR sinh ra từ nó đều đã 'completed' -> tự chuyển YCKS sang 'done'."""
    from app.modules.purchase_request.model import PurchaseRequest
    sr_ids = [r[0] for r in db.query(SurveyRequestLine.survey_request_id)
              .filter(SurveyRequestLine.pr_id == pr_id).distinct().all()]
    for sid in sr_ids:
        s = db.get(SurveyRequest, sid)
        if not s or s.status != "pr_created":
            continue
        pr_ids = [r[0] for r in db.query(SurveyRequestLine.pr_id)
                  .filter(SurveyRequestLine.survey_request_id == sid,
                          SurveyRequestLine.pr_id != 0).distinct().all()]
        prs = [db.get(PurchaseRequest, pid) for pid in pr_ids]
        prs = [p for p in prs if p]
        if prs and all(p.status == "completed" for p in prs):
            set_status(db, sid, "done", user_id or s.created_by or 0)
            record(db, user_id or s.created_by or 0, ENTITY, sid, "auto_done",
                   "Tự hoàn thành: mọi Yêu cầu mua hàng liên quan đã hoàn thành")


def complete_sr(db: Session, sid: int, user, profile: dict):
    """Chốt PHẦN KHẢO SÁT CỦA NGƯỜI GỌI: chỉ validate các dòng MÌNH phụ trách phải có option.
    Phiếu chỉ chuyển 'survey_done' khi TẤT CẢ dòng (mọi NSTM) đã có option.
    Cho phép chốt lại khi đã 'survey_done'. Trả (phiếu, fully_done)."""
    s = get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ chốt được phiếu đang xử lý hoặc đã khảo sát")
    lns = lines_of(db, sid)
    if not lns:
        raise HTTPException(400, "Phiếu không có dòng nào")
    # Quản lý/Admin TM (scope all) & người tạo -> chốt cả phiếu; NSTM -> chỉ dòng mình phụ trách
    see_all = _has_scope_all(profile) or getattr(user, "id", 0) == s.created_by
    my_lines = lns if see_all else [ln for ln in lns if can_process_line(db, ln, profile)]
    missing_mine = [ln.internal_line_code or str(ln.id) for ln in my_lines if not options_of(db, ln.id)]
    if missing_mine:
        raise HTTPException(400, f"Còn {len(missing_mine)} dòng của bạn chưa có option — không thể chốt")
    all_done = all(options_of(db, ln.id) for ln in lns)   # đủ mọi dòng của mọi NSTM?
    if all_done:
        if s.status != "survey_done":
            s = set_status(db, sid, "survey_done", getattr(user, "id", 0))
        return s, True
    db.refresh(s)
    return s, False   # phần của mình xong, còn dòng NSTM khác


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
            if not ln.received_date:                          # Ngày tiếp nhận = ngày NSTM được gán
                ln.received_date = datetime.now().strftime("%Y-%m-%d")
            assigned += 1
            if header_emp is None:
                header_emp = emp
    if header_emp and not s.assignee_id:
        s.assignee_id = header_emp.id
    if assigned or header_emp:
        db.commit()
    return assigned
