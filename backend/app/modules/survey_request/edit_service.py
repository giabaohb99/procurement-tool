"""YCBG — tạo, sửa, nhân bản, xóa phiếu; lưu dòng (bao-CR-715 tách từ service.py)."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.base_model import mark_deleted
from app.core.central_purchasing import normalize_handler_dept_id

from .model import SurveyRequest, SurveyRequestLine, SurveyRequestOption
from .base_service import ENTITY, HEADER_FIELDS, get_sr, lines_of
from .line_service import visible_lines_for


def _gen_code(db: Session) -> str:
    ddmmyy = datetime.now().strftime("%d%m%y")
    prefix = f"YCBG{ddmmyy}"
    # Lấy MAX hậu tố hiện có + 1 (không dùng count để tránh trùng khi có khoảng trống do xóa).
    # ai-CR-170: CỐ Ý đếm cả phiếu đã xóa mềm — mã phiếu không tái dùng (cột `code` UNIQUE,
    # và nhật ký / đính kèm của phiếu đã xóa vẫn trỏ theo mã đó).
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
    # bao-CR-480: phòng tự mua hàng lập phiếu thì phòng xử lý là chính phòng đó (như YCMH).
    # bao-CR-488: chỉ khi người lập KHÔNG chọn (None); gửi 0 là chủ ý nhờ phòng thu mua mặc định.
    if data.handler_dept_id is None:
        from app.modules.purchase_request.service import default_handler_dept_id
        s.handler_dept_id = default_handler_dept_id(db, s.department_id)
    # bao-CR-524: 0 → id thật của phòng thu mua mặc định (PBA017), không còn phòng ảo.
    s.handler_dept_id = normalize_handler_dept_id(db, s.handler_dept_id)
    # Tự điền Trưởng bộ phận theo Department.manager_id (parity với PYC).
    # Phòng chưa gán trưởng thì để rỗng — lúc đọc sẽ tự lấy lại (xem `_out` ở controller).
    if not s.head_of_dept_id and not s.head_of_dept and (s.department_id or s.department):
        s.head_of_dept_id = find_dept_head_id(db, s.department, s.department_id)
    sync_employee_ref(db, s, "head_of_dept_id", "head_of_dept")   # CR-087
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(s)           # bao-CR-499: mặc định = Trưởng bộ phận
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
    old_head = int(s.head_of_dept_id or 0)     # bao-CR-499
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(s, k, v)
    if data.handler_dept_id is not None:   # bao-CR-524: 0 → phòng thu mua mặc định
        s.handler_dept_id = normalize_handler_dept_id(db, data.handler_dept_id)
    # CR-086: FE cũ chỉ gửi TÊN phòng → bỏ id cũ rồi tra lại từ tên; gửi kèm id thì id thắng.
    if data.department is not None or data.department_id is not None:
        if data.department_id is None:
            s.department_id = 0
        sync_department_ref(db, s)
    # Đổi Bộ phận YC ở bản nháp → cập nhật lại Trưởng bộ phận. NHƯNG người lập nay
    # được chọn đích danh TBP (kể cả TBP phòng khác — QA 29/08): client gửi kèm
    # `head_of_dept_id` thì tôn trọng lựa chọn đó, không tra đè. FE cũ (v1) chỉ gửi
    # TÊN, không bao giờ gửi id, nên nhánh tra tự động vẫn chạy như trước với v1.
    sent_fields = data.model_dump(exclude_unset=True)
    picked_head = bool(sent_fields.get("head_of_dept_id"))
    if not picked_head and (s.department_id or s.department):
        s.head_of_dept_id = find_dept_head_id(db, s.department, s.department_id) or s.head_of_dept_id
    sync_employee_ref(db, s, "head_of_dept_id", "head_of_dept")   # CR-087
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(s, old_head)        # bao-CR-499
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
    header["handler_dept_id"] = normalize_handler_dept_id(db, src.handler_dept_id)   # bao-CR-524
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
    """Xóa MỀM phiếu (ai-CR-170): chỉ đánh dấu `is_deleted` + thời điểm + người xóa.

    Dòng / phương án / dây nối YCMH / đính kèm GIỮ NGUYÊN — phiếu chỉ biến mất khỏi danh sách,
    màn chi tiết, báo cáo, tool Trợ lý (lọc tập trung ở `core/scoping` + các chỗ đọc thẳng).
    Luật trạng thái giữ như cũ: Nháp / Bị trả lại / Đã từ chối."""
    s = get_sr(db, sid)
    if s.status not in ("draft", "rejected", "cancelled"):
        raise HTTPException(400, "Chỉ xóa được phiếu ở trạng thái Nháp, Bị trả lại hoặc Đã từ chối")
    mark_deleted(s, user_id)
    db.commit()
    record(db, user_id, ENTITY, sid, "delete", f"Xóa mềm phiếu {s.code}")
