from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import assert_unique_product_codes

from .model import (LINE_STATUSES, LS_COMPLETED, LS_RESURVEY, SurveyRequest,
                    SurveyRequestLine, SurveyRequestOption, SurveyRequestPr)

ENTITY = "survey_request"
# request_date: cho bộ lọc điều kiện lọc theo ngày (apply_range_filters vẫn lo _from/_to)
FILTERABLE = ["code", "status", "requester", "department", "request_date",
              "department_id", "head_of_dept_id", "requester_id", "company_id", "purpose"]
MAX_OPTIONS_PER_LINE = 5   # mỗi sản phẩm (dòng YCKS) tối đa 5 phương án khảo sát
HEADER_FIELDS = ["company_id", "requester", "requester_id", "requester_position",
                 "department_id", "department",
                 "head_of_dept_id", "head_of_dept", "purpose", "request_date", "note"]


VN_OFFSET = timedelta(hours=7)   # container chạy giờ UTC — ngày phải quy về giờ Việt Nam


def _stamp_result_date(ln: SurveyRequestLine) -> None:
    """CR-075: ghi "ngày trả kết quả thực tế" cho dòng khảo sát, MỘT LẦN duy nhất.

    Đã có mốc rồi thì giữ nguyên — dòng bị trả về "cần khảo sát lại" rồi chốt lần hai không
    được phép xóa dấu trễ của lần đầu."""
    if not (ln.result_date or "").strip():
        ln.result_date = (datetime.utcnow() + VN_OFFSET).strftime("%Y-%m-%d")


def get_sr(db: Session, sid: int) -> SurveyRequest:
    o = db.get(SurveyRequest, sid)
    if not o:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu báo giá")
    return o


def lines_of(db: Session, sid: int):
    return (db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid)
            .order_by(SurveyRequestLine.id).all())


def options_of(db: Session, line_id: int):
    return (db.query(SurveyRequestOption).filter(SurveyRequestOption.survey_request_line_id == line_id)
            .order_by(SurveyRequestOption.public_id).all())


def valid_options_of(db: Session, line_id: int):
    """Option hợp lệ để hiển thị/chọn. Option là SNAPSHOT tự đủ (đã copy thông số).
    Chỉ LOẠI option khi dòng khảo sát nguồn CÒN TỒN TẠI nhưng bị 'Không duyệt'
    (line_approve != 'Đã duyệt'). Nguồn đã BỊ XÓA (phiếu KS xóa) → GIỮ snapshot,
    vì snapshot vẫn đầy đủ và có thể đã được chọn/tạo YCMH. Option không gắn nguồn cũng giữ."""
    opts = options_of(db, line_id)
    if not opts:
        return opts
    from app.modules.survey.model import SurveyProductLine
    pids = [o.product_survey_line_id for o in opts if o.product_survey_line_id]
    existing: set[int] = set()
    approved: set[int] = set()
    if pids:
        for pid, appr in (db.query(SurveyProductLine.id, SurveyProductLine.line_approve)
                          .filter(SurveyProductLine.id.in_(pids)).all()):
            existing.add(pid)
            if appr == "Đã duyệt":
                approved.add(pid)
    return [o for o in opts
            if (not o.product_survey_line_id)              # option nhập tay, không gắn nguồn
            or (o.product_survey_line_id not in existing)  # nguồn đã bị xóa → giữ snapshot
            or (o.product_survey_line_id in approved)]     # nguồn còn & Đã duyệt


def _gen_code(db: Session) -> str:
    ddmmyy = datetime.now().strftime("%d%m%y")
    prefix = f"YCBG{ddmmyy}"
    # Lấy MAX hậu tố hiện có + 1 (không dùng count để tránh trùng khi có khoảng trống do xóa)
    mx = 0
    for (c,) in db.query(SurveyRequest.code).filter(SurveyRequest.code.like(prefix + "%")).all():
        suf = (c or "")[len(prefix):]
        if suf.isdigit():
            mx = max(mx, int(suf))
    return f"{prefix}{mx + 1:02d}"


def _copy_pr_line_images(db: Session, pairs: list[tuple[int, int]], user_id: int,
                         user=None, profile=None) -> int:
    """CR-027: kéo ảnh đối chiếu từ DÒNG YCMH nguồn sang DÒNG YCBG vừa tạo.
    `pairs` = [(id dòng YCMH, id dòng YCBG)]. Chỉ thêm FileLink mới trỏ vào CÙNG file gốc
    (không tải lại lên R2). Chỉ chép dòng thuộc YCMH mà người dùng có quyền xem."""
    pairs = [(a, b) for a, b in pairs if a and b]
    if not pairs:
        return 0
    from app.core.scoping import apply_scope
    from app.modules.attachment.model import FileLink
    from app.modules.purchase_request.model import (PurchaseRequest,
                                                    PurchaseRequestItem)
    q = (db.query(PurchaseRequestItem.id)
         .join(PurchaseRequest, PurchaseRequest.id == PurchaseRequestItem.pr_id)
         .filter(PurchaseRequestItem.id.in_({a for a, _ in pairs})))
    if user is not None and profile is not None:
        q = apply_scope(q, PurchaseRequest, "purchase_request", user, profile)
    allowed = {r[0] for r in q.all()}
    n = 0
    for src_id, new_id in pairs:
        if src_id not in allowed:
            continue
        for lk in (db.query(FileLink)
                   .filter(FileLink.entity == "purchase_request_line_image",
                           FileLink.entity_id == src_id).all()):
            db.add(FileLink(file_id=lk.file_id, entity="survey_request_line", entity_id=new_id,
                            created_by=user_id, updated_by=user_id))
            n += 1
    if n:
        db.commit()
    return n


def _save_lines(db: Session, sid: int, lines, user_id: int, user=None, profile=None) -> list[int]:
    """UPSERT dòng theo id (KHÔNG xóa+tạo lại) để đính kèm file (trỏ theo line id) không bị mất.
    - dòng có id đã tồn tại: cập nhật tại chỗ.
    - dòng id=0 (mới): thêm mới.
    - dòng cũ không còn trong payload: xóa cả option + file đính kèm.
    Trả danh sách id theo ĐÚNG thứ tự gửi lên (để FE map hình chờ upload)."""
    existing = {ln.id: ln for ln in db.query(SurveyRequestLine)
                .filter(SurveyRequestLine.survey_request_id == sid).all()}
    seen: set[int] = set()
    ordered_ids: list[int] = []
    img_pairs: list[tuple[int, int]] = []     # (dòng YCMH nguồn, dòng YCBG mới) — xem _copy_pr_line_images
    for it in lines or []:
        data = it.model_dump()
        lid = int(data.pop("id", 0) or 0)
        src_pr_item = int(data.pop("src_pr_item_id", 0) or 0)   # không phải cột — chỉ dùng để kéo ảnh
        if lid and lid in existing:
            ln = existing[lid]
            for k, v in data.items():
                setattr(ln, k, v)
            ln.updated_by = user_id
            seen.add(lid)
        else:
            ln = SurveyRequestLine(survey_request_id=sid, created_by=user_id, updated_by=user_id, **data)
            db.add(ln)
            db.flush()
            ln.internal_line_code = f"YCBGL{ln.id:06d}"
            if src_pr_item:
                img_pairs.append((src_pr_item, ln.id))
        ordered_ids.append(ln.id)
    stale = [lid for lid in existing if lid not in seen]
    if stale:
        db.query(SurveyRequestOption).filter(
            SurveyRequestOption.survey_request_line_id.in_(stale)).delete(synchronize_session=False)
        from app.modules.attachment.service import delete_attachments_for
        delete_attachments_for(db, [("survey_request_line", lid) for lid in stale])
        db.query(SurveyRequestLine).filter(
            SurveyRequestLine.id.in_(stale)).delete(synchronize_session=False)
    db.commit()
    _copy_pr_line_images(db, img_pairs, user_id, user, profile)
    return ordered_ids


def create_sr(db: Session, data, user_id: int, user=None, profile=None) -> SurveyRequest:
    from app.modules.department.service import sync_department_ref
    from app.modules.employee.service import sync_employee_ref
    from app.modules.purchase_request.service import find_dept_head_id
    header = {f: getattr(data, f) for f in HEADER_FIELDS}
    s = SurveyRequest(code=(data.code or _gen_code(db)), status="draft", created_by=user_id, updated_by=user_id,
                      **header)
    sync_department_ref(db, s)   # CR-086: neo phòng ban bằng id ngay từ lúc lập phiếu
    # Tự điền Trưởng bộ phận theo Department.manager_id (parity với PYC).
    # Phòng chưa gán trưởng thì để rỗng — lúc đọc sẽ tự lấy lại (xem `_out` ở controller).
    if not s.head_of_dept_id and not s.head_of_dept and (s.department_id or s.department):
        s.head_of_dept_id = find_dept_head_id(db, s.department, s.department_id)
    sync_employee_ref(db, s, "head_of_dept_id", "head_of_dept")   # CR-087
    db.add(s)
    db.commit()
    db.refresh(s)
    ordered = _save_lines(db, s.id, data.lines, user_id, user, profile)
    record(db, user_id, ENTITY, s.id, "create")
    s._ordered_line_ids = ordered
    return s


def update_sr(db: Session, sid: int, data, user_id: int, user=None, profile=None) -> SurveyRequest:
    from app.modules.department.service import sync_department_ref
    from app.modules.employee.service import sync_employee_ref
    from app.modules.purchase_request.service import find_dept_head_id
    s = get_sr(db, sid)
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại "
                                 "(phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới).")
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(s, k, v)
    # CR-086: FE cũ chỉ gửi TÊN phòng → bỏ id cũ rồi tra lại từ tên; gửi kèm id thì id thắng.
    if data.department is not None or data.department_id is not None:
        if data.department_id is None:
            s.department_id = 0
        sync_department_ref(db, s)
    # Đổi Bộ phận YC ở bản nháp → cập nhật lại Trưởng bộ phận (ô này người dùng không tự nhập).
    if s.department_id or s.department:
        s.head_of_dept_id = find_dept_head_id(db, s.department, s.department_id) or s.head_of_dept_id
    sync_employee_ref(db, s, "head_of_dept_id", "head_of_dept")   # CR-087
    s.updated_by = user_id
    db.commit()
    ordered = None
    if data.lines is not None:
        ordered = _save_lines(db, sid, data.lines, user_id, user, profile)
    record(db, user_id, ENTITY, sid, "update")
    db.refresh(s)
    if ordered is not None:
        s._ordered_line_ids = ordered
    return s


def clone_sr(db: Session, sid: int, user, profile: dict) -> SurveyRequest:
    """Nhân bản 1 YCKS thành phiếu NHÁP mới: sao chép header + các dòng (kèm ảnh đính kèm dòng,
    dùng chung file). CHỈ copy dòng NGƯỜI DÙNG ĐƯỢC XEM (tránh lộ dòng của NSTM khác).
    KHÔNG sao chép NSTM/option/PYC/tình trạng (làm mới hoàn toàn)."""
    from app.modules.attachment.model import FileLink
    from app.modules.department.service import sync_department_ref
    from app.modules.employee.model import Employee
    user_id = getattr(user, "id", 0)
    src = get_sr(db, sid)
    header = {f: getattr(src, f) for f in HEADER_FIELDS}
    # NGƯỜI YÊU CẦU của bản sao = người BẤM NHÂN BẢN (KHÔNG giữ người yêu cầu phiếu gốc).
    # Nếu giữ nguyên: created_by=người clone + requester_id=người gốc -> CẢ HAI đều có quyền phía
    # yêu cầu, và phiếu hiển thị sai người yêu cầu. Đặt lại theo hồ sơ NV của người clone.
    emp = db.get(Employee, getattr(user, "employee_id", 0) or 0) if getattr(user, "employee_id", 0) else None
    if emp:
        header["requester"] = emp.full_name or ""
        header["requester_id"] = emp.id
        header["requester_position"] = emp.position or ""
        header["department_id"] = emp.department_id or 0    # CR-086
        header["department"] = emp.department_name or ""
        header["head_of_dept_id"] = 0                       # CR-087: lấy lại theo phòng bên dưới
        header["head_of_dept"] = emp.manager_name or ""
    else:
        header["requester"] = getattr(user, "full_name", "") or ""
        header["requester_id"] = 0
    s = SurveyRequest(code=_gen_code(db), status="draft", created_by=user_id, updated_by=user_id,
                      **header)
    sync_department_ref(db, s)      # CR-086
    if not s.head_of_dept_id and (s.department_id or s.department):
        from app.modules.purchase_request.service import find_dept_head_id
        s.head_of_dept_id = find_dept_head_id(db, s.department, s.department_id)
    from app.modules.employee.service import sync_employee_ref
    sync_employee_ref(db, s, "head_of_dept_id", "head_of_dept")   # CR-087
    db.add(s)
    db.commit()
    db.refresh(s)
    src_lines = visible_lines_for(db, src, lines_of(db, sid), user, profile)
    for ln in src_lines:
        nl = SurveyRequestLine(
            survey_request_id=s.id, created_by=user_id, updated_by=user_id,
            received_date="", result_due_date=ln.result_due_date or "",
            department_requester=ln.department_requester or "", item_group=ln.item_group or "",
            requirement_detail=ln.requirement_detail or "", other_requirement=ln.other_requirement or "",
            request_qty=ln.request_qty or 0, uom=ln.uom or "", proposed_price=ln.proposed_price or 0,
            image_file=ln.image_file or "")
        db.add(nl)
        db.flush()
        nl.internal_line_code = f"YCBGL{nl.id:06d}"
        # sao chép đính kèm của dòng (chỉ thêm liên kết mới, dùng chung file gốc)
        for lk in (db.query(FileLink)
                   .filter(FileLink.entity == "survey_request_line", FileLink.entity_id == ln.id).all()):
            db.add(FileLink(file_id=lk.file_id, entity="survey_request_line", entity_id=nl.id,
                            created_by=user_id, updated_by=user_id))
    db.commit()
    record(db, user_id, ENTITY, s.id, "create", f"Nhân bản từ {src.code}")
    return s


def delete_sr(db: Session, sid: int, user_id: int):
    s = get_sr(db, sid)
    if s.status not in ("draft", "rejected", "cancelled"):
        raise HTTPException(400, "Chỉ xóa được phiếu ở trạng thái Nháp, Bị trả lại hoặc Đã từ chối")
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


# Task 2: trạng thái dòng do người YC/phòng ban cập nhật — hằng số gốc nằm ở model.py


def set_line_status(db: Session, sid: int, line_id: int, new_status: str, user_id: int) -> SurveyRequestLine:
    """Đổi trạng thái 1 dòng khảo sát (người YC / cùng phòng ban). Đồng bộ is_completed."""
    new_status = (new_status or "").strip()
    if new_status not in LINE_STATUSES:
        raise HTTPException(400, "Trạng thái dòng không hợp lệ")
    ln = get_line(db, sid, line_id)
    # Chỉ được chốt HOÀN THÀNH sau khi dòng đã chọn 1 phương án (Đã chọn PA).
    # "Cần khảo sát lại" thì KHÔNG cần chọn phương án — đây là lúc kết quả khảo sát
    # chưa đạt, người YC muốn yêu cầu khảo sát lại mà không phải chọn phương án nào.
    if new_status == LS_COMPLETED:
        if not any(o.is_chosen for o in options_of(db, line_id)):
            raise HTTPException(400, "Cần chọn 1 phương án (Đã chọn PA) trước khi chốt Hoàn thành")
    ln.line_status = new_status
    ln.is_completed = (new_status == LS_COMPLETED)
    # Hướng B: gắn cờ "Cần khảo sát lại" thì TỰ BỎ CHỌN mọi phương án — cờ khảo sát lại
    # và "đã chọn PA" là hai trạng thái loại trừ nhau (không cho vừa chê vừa tạo YCMH).
    if new_status == LS_RESURVEY:
        for o in options_of(db, line_id):
            if o.is_chosen:
                o.is_chosen = False
                o.updated_by = user_id
        # Phiếu đã "Đã khảo sát" mà 1 dòng cần khảo sát lại thì phiếu chưa xong khảo sát
        # → hạ về "Đang xử lý" (KHÔNG hạ phiếu đã tạo YCMH/hoàn thành). Chốt lại sẽ đưa về Đã khảo sát.
        sr = get_sr(db, sid)
        if sr.status == "survey_done":
            sr.status = "processing"
            sr.updated_by = user_id
    ln.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "line_status",
           f"Dòng #{line_id} -> {new_status or 'chưa xác định'}")
    db.refresh(ln)
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


def _has_scope_all(profile: dict | None) -> bool:
    if not profile or not isinstance(profile, dict):
        return True
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


def _see_all_lines(profile: dict, s, user) -> bool:
    """Ai thấy HẾT dòng (để phân bổ): người TẠO / người DUYỆT (Admin·Quản lý TM) /
    quản lý theo phạm vi dept·company·all. (Đồng bộ với purchase_request._see_all_items.)"""
    if getattr(user, "id", 0) == getattr(s, "created_by", None):
        return True
    # Người YÊU CẦU (dù admin tạo giùm) cũng thấy HẾT dòng của phiếu mình
    rid = getattr(user, "employee_id", 0) or 0
    if rid and getattr(s, "requester_id", 0) == rid:
        return True
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if not p:
            continue
        if p.get("approve"):
            return True
        if p.get("read") and p.get("scope") in ("dept", "company", "all"):
            return True
        # Admin thu mua = đọc-chỉ phạm vi 'proc' (KHÔNG có 'write') -> giám sát toàn quá trình,
        # thấy HẾT dòng. NSTM (có 'write', 'proc') vẫn chỉ thấy dòng được giao để xử lý.
        if p.get("read") and p.get("scope") == "proc" and not p.get("write"):
            return True
    return False


def visible_lines_for(db: Session, s, lines, user, profile: dict):
    """Lọc dòng theo NGƯỜI XEM:
    - Người tạo / người duyệt (Admin·Quản lý TM) / quản lý dept·company·all -> thấy HẾT dòng
      (để phân bổ NSTM cho từng dòng).
    - NSTM -> chỉ thấy dòng mình xử lý được (được giao / phụ trách phân loại)."""
    if _see_all_lines(profile, s, user):
        return list(lines)
    return [ln for ln in lines if can_process_line(db, ln, profile)]


def available_survey_lines(db: Session, supplier_code: str = "", item_group: str = "",
                           search: str = "", page: int = 1, page_size: int = 8,
                           sort_by: str = "", sort_dir: str = "desc"):
    """Dòng khảo sát SẢN PHẨM đã DUYỆT (line_approve='Đã duyệt') — nguồn để tạo option.
    Dùng cho CHỌN NCC THỦ CÔNG: lọc mở theo nhiều tiêu chí (tùy chọn, KHÔNG giới hạn liên kết YCKS):
    - supplier_code: theo NCC (tùy chọn).
    - item_group: theo PHÂN LOẠI của Survey cha (mặc định = phân loại dòng, đổi được).
    - search: khớp Tên SP hoặc Mã SP theo NCC (LIKE).
    Cần ít nhất 1 tiêu chí (controller đã chặn rỗng).
    Phân trang phía server (kết quả có thể vài trăm dòng) -> trả (items, total)."""
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
    total = q.count()
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    # Sắp xếp theo cột (whitelist khớp các cột hiển thị ở FE; Mã VTBB nằm ở Survey cha)
    sort_cols = {
        "supplier_code": SurveyProductLine.supplier_code,
        "product_name": SurveyProductLine.product_name,
        "result_date": SurveyProductLine.result_date,
        "spec": SurveyProductLine.spec,
        "origin": SurveyProductLine.origin,
        "price_by_volume": SurveyProductLine.price_by_volume,
        "moq": SurveyProductLine.moq,
        "quote_unit": SurveyProductLine.quote_unit,
        "lab_result": SurveyProductLine.lab_result,
        "survey_item_code": Survey.item_code,
    }
    col = sort_cols.get(sort_by or "")
    if col is not None:
        order = col.desc() if str(sort_dir).lower() == "desc" else col.asc()
    else:
        order = SurveyProductLine.id.desc()   # mặc định: mới nhất trước
    items = (q.order_by(order)
             .offset((page - 1) * page_size).limit(page_size).all())
    return items, total


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
    line.no_option = False   # đã có phương án -> bỏ cờ chốt rỗng (nếu trước đó chốt rỗng)
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
    if not already:
        ln = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id).first()
        if ln and ln.line_status == LS_RESURVEY:
            ln.line_status = ""
            ln.updated_by = user_id
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
    from app.modules.purchase_request.service import (apply_supplier_info,
                                                     find_dept_head,
                                                     find_dept_head_id)
    from app.modules.supplier.model import Supplier
    s = get_sr(db, sid)
    # Cho tạo YCMH khi: Đang xử lý (mua trước dòng đã khảo sát xong), Đã khảo sát, Đã tạo YCMH, Hoàn thành.
    if s.status not in ("processing", "survey_done", "pr_created", "done"):
        raise HTTPException(400, "Chỉ tạo YCMH khi phiếu đang xử lý trở đi")

    # Dòng TÁI SỬ DỤNG: 1 dòng có thể tạo NHIỀU YCMH (mua lại). KHÔNG bỏ qua dòng đã completed;
    # chỉ tạo cho dòng ĐANG chọn PA. Sau khi tạo sẽ tự bỏ chọn (tránh tạo trùng lần sau).
    groups: dict[str, list] = {}
    for ln in lines_of(db, sid):
        chosen = [o for o in options_of(db, ln.id) if o.is_chosen]
        if not chosen:
            continue
        groups.setdefault(chosen[0].supplier_code or "", []).append((ln, chosen[0]))
    if not groups:
        raise HTTPException(400, "Chưa chọn phương án nào để tạo YCMH")
    # Mỗi NCC ra 1 YCMH → 2 dòng khảo sát cùng gắn 1 mã VTBB sẽ đẻ ra 2 dòng trùng mã trên
    # YCMH, làm sai tiến độ SL khi đồng bộ từ ĐMH. Chặn TRƯỚC vòng lặp vì vòng lặp commit theo
    # từng NCC — báo lỗi giữa chừng sẽ để lại vài YCMH đã tạo dở.
    for group_items in groups.values():
        assert_unique_product_codes(
            [(o.system_product_code or "") for _, o in group_items],
            message=("Nhiều dòng khảo sát của cùng một nhà cung cấp đang gắn trùng mã VTBB: "
                     "{codes}. Mỗi mã chỉ được 1 dòng trên YCMH — hãy gắn lại mã cho đúng "
                     "hoặc gộp các dòng khảo sát đó làm một."))

    today = datetime.now().strftime("%Y-%m-%d")
    created = []
    for sup_code, items in groups.items():
        sup = db.query(Supplier).filter(Supplier.code == sup_code).first() if sup_code else None
        first_opt = items[0][1]
        pr = PurchaseRequest(
            code=_gen_pr_code(db, today), company_id=s.company_id, requester=s.requester,
            requester_id=s.requester_id,
            requester_position=s.requester_position, department=s.department,
            department_id=s.department_id,      # CR-086: PYC sinh ra thừa kế id phòng của YCBG
            head_of_dept=s.head_of_dept or find_dept_head(db, s.department or "", s.department_id),
            # CR-087: YCBG nay đã có id TBP → thừa kế thẳng, chỉ suy lại từ phòng khi phiếu
            # nguồn chưa có (phiếu cũ). 0 = không chỉ định ai, chạy theo luật duyệt cũ.
            head_of_dept_id=(s.head_of_dept_id
                             or find_dept_head_id(db, s.department or "", s.department_id)),
            purpose=s.purpose, request_date=today, status="draft",
            note=f"Sinh tự động từ Yêu cầu báo giá {s.code}",
            suggested_supplier=first_opt.supplier_name or "",
            suggested_supplier_tax_code=(sup.tax_code if sup else ""),
            suggested_supplier_contact=(sup.address if sup else ""),   # Liên hệ NCC lấy Địa chỉ từ bảng NCC
            created_by=user_id, updated_by=user_id,
        )
        # Task 4: NCC từ khảo sát -> cụm 'pur' (khóa với người yêu cầu; QL/Admin thu mua sửa được)
        apply_supplier_info(pr, {
            "req": {"name": "", "tax_code": "", "contact": ""},
            "pur": {"name": first_opt.supplier_name or "",
                    "tax_code": (sup.tax_code if sup else ""),
                    "contact": (sup.address if sup else "")},
            "from_survey": True,
        })
        db.add(pr)
        db.commit()
        db.refresh(pr)
        for ln, opt in items:
            qty = float(ln.request_qty or 0)
            price = float(opt.snap_price_by_volume or 0)
            # VAT của phương án đã chọn phải theo sang YCMH (CR-058). Trước đây không gán
            # `vat_pct` nên dòng nhận mặc định 0% — NCC báo giá 8% mà YCMH ghi 0%, người lập
            # phải sửa tay từng dòng, quên thì ĐMH prefill sai và thiếu luôn tiền thuế.
            vat = float(opt.snap_vat or 0)
            db.add(PurchaseRequestItem(
                pr_id=pr.id,
                product_code=(opt.system_product_code or "").strip(),   # mã SP hệ thống gắn ở option
                product_name=opt.snap_product_name or ln.requirement_detail or "Sản phẩm",
                item_group=ln.item_group or "", qty=qty, unit=opt.snap_quote_unit or ln.uom or "",
                price=price, vat_pct=vat,
                # Thành tiền GỒM VAT — cùng công thức với khi lưu YCMH (purchase_request/service.py)
                amount=round(qty * price * (1 + vat / 100), 2), note="",
                line_status="Chưa tạo đơn mua hàng", created_by=user_id, updated_by=user_id,   # CR-074
            ))
            # Liên kết YCKS-dòng <-> YCMH (đếm được nhiều lần tạo) + tự BỎ CHỌN option
            db.add(SurveyRequestPr(
                survey_request_id=sid, survey_request_line_id=ln.id, option_id=opt.id,
                product_survey_line_id=opt.product_survey_line_id or 0,
                pr_id=pr.id, pr_code=pr.code, created_by=user_id, updated_by=user_id))
            opt.is_chosen = False          # tự bỏ chọn sau khi tạo
            ln.pr_id = pr.id               # giữ YCMH gần nhất (tương thích + auto-complete)
            ln.pr_code = pr.code
            ln.is_completed = True         # cờ "đã từng tạo YCMH" (KHÔNG còn khoá tạo thêm)
            ln.updated_by = user_id
        db.commit()
        created.append(pr)

    # Chỉ nâng cấp từ 'Đã khảo sát' → 'Đã tạo YCMH'; KHÔNG hạ cấp phiếu đã Hoàn thành (done).
    if s.status == "survey_done":
        s.status = "pr_created"
    s.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "pr_created")
    return created


def finalize_sr(db: Session, sid: int, user_id: int) -> SurveyRequest:
    """Admin/QL chuyển Hoàn thành (dừng hẳn). Cho phép từ 'Đã khảo sát' hoặc 'Đã tạo YCMH'."""
    s = get_sr(db, sid)
    if s.status not in ("survey_done", "pr_created"):
        raise HTTPException(400, "Chỉ hoàn thành phiếu ở trạng thái Đã khảo sát hoặc Đã tạo Yêu cầu mua hàng")
    return set_status(db, sid, "done", user_id)


def auto_complete_from_pr(db: Session, pr_id: int, user_id: int = 0) -> None:
    """Khi 1 Yêu cầu mua hàng (PR) hoàn thành: nếu Yêu cầu khảo sát liên quan (qua line.pr_id)
    đang ở 'pr_created' VÀ tất cả các PR sinh ra từ nó đều đã 'completed' -> tự chuyển YCKS sang 'done'."""
    from app.modules.purchase_request.model import PurchaseRequest
    sr_ids = [r[0] for r in db.query(SurveyRequestPr.survey_request_id)
              .filter(SurveyRequestPr.pr_id == pr_id).distinct().all()]
    for sid in sr_ids:
        s = db.get(SurveyRequest, sid)
        if not s or s.status != "pr_created":
            continue
        pr_ids = [r[0] for r in db.query(SurveyRequestPr.pr_id)
                  .filter(SurveyRequestPr.survey_request_id == sid).distinct().all()]
        prs = [db.get(PurchaseRequest, pid) for pid in pr_ids]
        prs = [p for p in prs if p]
        if prs and all(p.status == "completed" for p in prs):
            set_status(db, sid, "done", user_id or s.created_by or 0)
            record(db, user_id or s.created_by or 0, ENTITY, sid, "auto_done",
                   "Tự hoàn thành: mọi Yêu cầu mua hàng liên quan đã hoàn thành")


def complete_sr(db: Session, sid: int, user, profile: dict = None, empty_line_ids=None):
    """Chốt PHẦN KHẢO SÁT CỦA NGƯỜI GỌI. Dòng phụ trách phải có option HOẶC được 'chốt rỗng'
    (no_option, không có NCC phù hợp). Phiếu -> 'survey_done' khi MỌI dòng có option hoặc chốt rỗng.
    empty_line_ids: các dòng (mình phụ trách, chưa option) tick chốt rỗng. Trả (phiếu, fully_done)."""
    empty_ids = {int(x) for x in (empty_line_ids or [])}
    s = get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ chốt được phiếu đang xử lý hoặc đã khảo sát")
    lns = lines_of(db, sid)
    if not lns:
        raise HTTPException(400, "Phiếu không có dòng nào")
    # Quản lý/Admin TM (scope all) & người tạo -> chốt cả phiếu; NSTM -> chỉ dòng mình phụ trách
    see_all = _has_scope_all(profile) or getattr(user, "id", 0) == s.created_by
    my_lines = lns if see_all else [ln for ln in lns if can_process_line(db, ln, profile)]
    # Cập nhật cờ chốt rỗng: có option -> bỏ cờ; không option + được tick -> chốt rỗng.
    # Đồng thời: dòng đang "Cần khảo sát lại" mà NSTM đã khảo sát lại xong (nay có option)
    # -> GỠ cờ, dòng về "Đã khảo sát". (Trước đây cờ chỉ gỡ khi người YC bấm chọn PA.)
    resurveyed = 0
    for ln in my_lines:
        if options_of(db, ln.id):
            ln.no_option = False
            if ln.line_status == LS_RESURVEY:
                ln.line_status = ""
                ln.updated_by = getattr(user, "id", 0)
                resurveyed += 1
            _stamp_result_date(ln)
        elif ln.id in empty_ids:
            ln.no_option = True
            ln.updated_by = getattr(user, "id", 0)
            _stamp_result_date(ln)   # chốt rỗng cũng là trả kết quả — "khảo sát rồi, không có NCC phù hợp"
    db.flush()
    missing_mine = [ln.internal_line_code or str(ln.id) for ln in my_lines
                    if not options_of(db, ln.id) and not ln.no_option]
    if missing_mine:
        raise HTTPException(400, f"Còn {len(missing_mine)} dòng chưa có phương án — hãy khảo sát hoặc chốt rỗng")
    all_done = all(options_of(db, ln.id) or ln.no_option for ln in lns)   # đủ mọi dòng của mọi NSTM?
    if all_done:
        if s.status != "survey_done":
            s = set_status(db, sid, "survey_done", getattr(user, "id", 0))
        return s, True, resurveyed
    db.refresh(s)
    return s, False, resurveyed   # phần của mình xong, còn dòng NSTM khác


def auto_assign(db: Session, s: SurveyRequest) -> int:
    """Sau khi trưởng phòng duyệt: tự gán NSTM cho TỪNG DÒNG theo phân loại (tái dùng Task 4).
    KHÔNG ghi NSTM ở đầu phiếu — một phiếu có thể do nhiều NSTM khảo sát, việc thuộc về dòng."""
    from app.modules.category_assignee.service import resolve_for_group
    assigned = 0
    for ln in lines_of(db, s.id):
        if ln.assignee:
            continue
        emp = resolve_for_group(db, ln.item_group)
        if emp and emp.code:
            ln.assignee = emp.code
            if not ln.received_date:                          # Ngày tiếp nhận = ngày NSTM được gán
                ln.received_date = datetime.now().strftime("%Y-%m-%d")
            assigned += 1
    if assigned:
        db.commit()
    return assigned
