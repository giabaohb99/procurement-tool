from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import AssignIn, ItemStatusIn, PRCreate, PRUpdate

FILTERABLE = ["code", "status", "requester", "department", "is_urgent"]
ENTITY = "purchase_request"

# Trạng thái xử lý theo DÒNG hàng
LINE_STATUS = ["Chưa đặt hàng", "Đã đặt hàng", "Đã gửi ĐMH cho KT",
               "Đã nhận hàng", "Hoàn thành", "Hủy đơn", "Tạm ngưng"]


def find_dept_head(db: Session, department_name: str) -> str:
    """Tên Trưởng bộ phận của 1 phòng ban (theo field manager_id chọn cứng). '' nếu chưa gán."""
    if not department_name:
        return ""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    dep = db.query(Department).filter(Department.name == department_name).first()
    if not dep or not dep.manager_id:
        return ""
    head = db.get(Employee, dep.manager_id)
    return head.full_name if head else ""


def has_cancelled_line(db: Session, pr_id: int) -> bool:
    return db.query(PurchaseRequestItem).filter(
        PurchaseRequestItem.pr_id == pr_id, PurchaseRequestItem.line_status == "Hủy đơn").first() is not None


def recompute_status(db: Session, pr: PurchaseRequest) -> None:
    """Tự suy trạng thái phiếu từ trạng thái các dòng (chỉ khi đã duyệt / đang xử lý / hoàn thành)."""
    if pr.status not in ("approved", "processing", "completed"):
        return
    st = [(i.line_status or "Chưa đặt hàng") for i in items_of(db, pr.id)]
    if not st:
        return
    was_completed = pr.status == "completed"
    # Dòng đã Hủy KHÔNG tính vào điều kiện hoàn thành (1 dòng hủy + các dòng còn lại đủ = vẫn hoàn thành)
    active = [s for s in st if s != "Hủy đơn"]
    if active and all(s == "Hoàn thành" for s in active):
        pr.status = "completed"
    elif any(s not in ("Chưa đặt hàng", "Hủy đơn") for s in st):
        pr.status = "processing"
    else:
        pr.status = "approved"
    db.commit()
    if pr.status == "completed" and not was_completed:
        _notify_survey_request_done(db, pr.id, pr.updated_by or 0)


# Thứ tự tiến độ dòng (đồng bộ với ĐMH); dòng YCMH = mức KÉM TIẾN NHẤT trong các dòng ĐMH liên kết
_PROGRESS_ORDER = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng", "Đã gửi ĐMH cho KT", "Hoàn thành"]


def sync_from_purchase_orders(db: Session, pr_code: str) -> None:
    """Suy trạng thái từng dòng YCMH từ các dòng ĐMH liên kết (khớp product_code), rồi suy lại trạng thái phiếu.
    - Chỉ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/bị trả lại/đã từ chối).
    - Bỏ dòng ĐMH đang Hủy/Tạm ngưng khi gom.
    - Dòng YCMH bị Hủy/Tạm ngưng THỦ CÔNG thì giữ nguyên (không đè)."""
    if not pr_code:
        return
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    lines = (db.query(POItem).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
             .filter(PurchaseOrder.pr_code == pr_code,
                     PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]))
             .all())
    active_idx: dict[str, int] = {}   # sp -> mức kém tiến nhất trong các dòng ĐANG chạy
    has_cancel: set[str] = set()      # sp có dòng Hủy đơn
    has_pause: set[str] = set()       # sp có dòng Tạm ngưng
    for ln in lines:
        ps = ln.progress_status or "Chưa đặt hàng"
        if ps == "Hủy đơn":
            has_cancel.add(ln.product_code); continue
        if ps == "Tạm ngưng":
            has_pause.add(ln.product_code); continue
        idx = _PROGRESS_ORDER.index(ps) if ps in _PROGRESS_ORDER else 0
        cur = active_idx.get(ln.product_code)
        active_idx[ln.product_code] = idx if cur is None else min(cur, idx)
    for it in items_of(db, pr.id):
        if (it.line_status or "") in ("Hủy đơn", "Tạm ngưng"):
            continue  # ngoại lệ đặt thủ công trên YCMH thì giữ nguyên
        p = it.product_code
        if p in active_idx:
            it.line_status = _PROGRESS_ORDER[active_idx[p]]           # còn dòng đang chạy → mức kém tiến nhất
        elif p in has_cancel:
            it.line_status = "Hủy đơn"                                 # mọi dòng ĐMH của sp đều hủy
        elif p in has_pause:
            it.line_status = "Tạm ngưng"
        else:
            it.line_status = "Chưa đặt hàng"                           # chưa có ĐMH nào
    db.commit()
    recompute_status(db, pr)


def update_item_status(db: Session, pid: int, data: ItemStatusIn, user_id: int, emp_code: str, is_manager: bool) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")
    rows = {i.id: i for i in items_of(db, pid)}
    for it in data.items:
        row = rows.get(it.id)
        if row is None:
            continue
        if not is_manager and (row.assignee or "") != (emp_code or "__none__"):
            continue  # NSTM chỉ sửa dòng được giao cho mình
        if it.line_status is not None:
            row.line_status = it.line_status
        if it.progress_note is not None:
            row.progress_note = it.progress_note
        if it.note is not None:
            row.note = it.note
    pr.updated_by = user_id
    db.commit()
    recompute_status(db, pr)
    record(db, user_id, ENTITY, pid, "line_status", "Cập nhật trạng thái dòng")
    db.refresh(pr)
    return pr


def cancel_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = "cancelled"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "cancelled", reason)
    db.refresh(pr)
    return pr


def return_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    """Trả phiếu về "Bị trả lại" (rejected) — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCKS).
    Xóa nhân sự phụ trách + reset trạng thái mọi dòng về 'Chưa đặt hàng'."""
    pr = get_pr(db, pid)
    for it in items_of(db, pid):
        it.assignee = ""
        it.line_status = "Chưa đặt hàng"
    pr.assignee_id = 0
    pr.status = "rejected"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "returned", reason)
    db.refresh(pr)
    return pr


def complete_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = "completed"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "completed", "")
    _notify_survey_request_done(db, pid, user_id)
    db.refresh(pr)
    return pr


def _notify_survey_request_done(db: Session, pr_id: int, user_id: int) -> None:
    """Kích hoạt tự hoàn thành Yêu cầu khảo sát liên quan (nếu mọi PR của nó đã hoàn thành)."""
    try:
        from app.modules.survey_request import service as sr_service
        sr_service.auto_complete_from_pr(db, pr_id, user_id)
    except Exception:
        pass


def assign(db: Session, pid: int, data: AssignIn, user_id: int) -> PurchaseRequest:
    """Phân bổ NSTM cho từng dòng — chạy được cả khi phiếu đã gửi duyệt (không bị khóa như sửa)."""
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed", "done"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không phân bổ được")
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
    rows = {i.id: i for i in items_of(db, pid)}
    for it in data.items:
        row = rows.get(it.id)
        if row is not None:
            row.assignee = it.assignee
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "assign", "Phân bổ NSTM")
    return pr


def _save_items(db: Session, pr_id: int, items, user_id: int):
    db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).delete()
    for it in items or []:
        data = it.model_dump()
        data["amount"] = round((data.get("qty") or 0) * (data.get("price") or 0), 2)
        db.add(PurchaseRequestItem(pr_id=pr_id, created_by=user_id, updated_by=user_id, **data))
    db.commit()


def items_of(db: Session, pr_id: int):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).all()


def get_pr(db: Session, pid: int) -> PurchaseRequest:
    obj = db.query(PurchaseRequest).filter(
        PurchaseRequest.id == pid,
        PurchaseRequest.is_deleted == False,
    ).first()
    if not obj:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return obj


def list_pr(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def copy_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    """Nhân bản phiếu thành 1 phiếu Nháp mới: giữ dòng hàng, reset mã/trạng thái/NSTM/trạng thái dòng."""
    src = get_pr(db, pid)
    pr = PurchaseRequest(
        code="", company_id=src.company_id, requester=src.requester,
        requester_position=src.requester_position, department=src.department,
        head_of_dept=src.head_of_dept, purpose=src.purpose, request_date=src.request_date,
        need_date=src.need_date, is_urgent=src.is_urgent, note=src.note,
        status="draft", assignee_id=0, created_by=user_id, updated_by=user_id,
        show_code_on_print=src.show_code_on_print, suggested_supplier=src.suggested_supplier,
        suggested_supplier_tax_code=src.suggested_supplier_tax_code,
        suggested_supplier_contact=src.suggested_supplier_contact,
        quote_filename=src.quote_filename, quote_file_url=src.quote_file_url,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        from datetime import datetime
        date_str = datetime.now().strftime("%d%m%y")
        prefix = f"PYC{date_str}"
        last = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        seq = 1
        if last and last.code.startswith(prefix):
            try:
                seq = int(last.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _COPY = ["product_code", "product_name", "item_group", "group_desc", "qty", "unit",
             "price", "amount", "warehouse", "required_date", "note"]
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _COPY}
        db.add(PurchaseRequestItem(pr_id=pr.id, created_by=user_id, updated_by=user_id,
                                   assignee="", line_status="Chưa đặt hàng", progress_note="", **data))
    db.commit()
    record(db, user_id, ENTITY, pr.id, "create", f"Nhân bản từ {src.code}")
    db.refresh(pr)
    return pr


def create_pr(db: Session, data: PRCreate, user_id: int) -> PurchaseRequest:
    pr = PurchaseRequest(
        code=data.code or "", company_id=data.company_id, requester=data.requester,
        requester_position=data.requester_position, department=data.department,
        head_of_dept=data.head_of_dept, purpose=data.purpose, request_date=data.request_date,
        need_date=data.need_date, is_urgent=data.is_urgent, vat_rate=data.vat_rate,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        show_code_on_print=data.show_code_on_print,
        suggested_supplier=data.suggested_supplier,
        suggested_supplier_tax_code=data.suggested_supplier_tax_code,
        suggested_supplier_contact=data.suggested_supplier_contact,
        quote_filename=data.quote_filename,
        quote_file_url=data.quote_file_url,
    )
    # Tự điền Trưởng bộ phận theo phòng ban của người yêu cầu (nếu phòng có trưởng)
    if not pr.head_of_dept and pr.department:
        pr.head_of_dept = find_dept_head(db, pr.department)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        date_str = ""
        if pr.request_date and len(pr.request_date) >= 10 and "-" in pr.request_date:
            parts = pr.request_date.split("-")
            if len(parts) == 3:
                date_str = f"{parts[2]}{parts[1]}{parts[0][-2:]}"
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%d%m%y")
            
        prefix = f"PYC{date_str}"
        last_pr = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        
        seq = 1
        if last_pr and last_pr.code.startswith(prefix):
            try:
                seq = int(last_pr.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
                
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _save_items(db, pr.id, data.items, user_id)
    record(db, user_id, ENTITY, pr.id, "create")
    return pr


def update_pr(db: Session, pid: int, data: PRUpdate, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại "
                                 "(phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới).")
    for key, value in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(pr, key, value)
    pr.updated_by = user_id
    db.commit()
    if data.items is not None:
        _save_items(db, pid, data.items, user_id)
    record(db, user_id, ENTITY, pid, "update")
    db.refresh(pr)
    return pr


def delete_pr(db: Session, pid: int, user_id: int) -> None:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected", "cancelled"):
        raise HTTPException(400, "Chỉ xóa được phiếu ở trạng thái Nháp, Bị trả lại hoặc Đã từ chối")
    pr.is_deleted = True
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = status
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    db.refresh(pr)
    return pr
