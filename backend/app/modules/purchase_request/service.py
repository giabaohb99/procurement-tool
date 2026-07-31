import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import AssignIn, ItemStatusIn, PRCreate, PRUpdate

FILTERABLE = ["code", "status", "requester", "department", "is_urgent"]
ENTITY = "purchase_request"

# Task 4 — NCC 2 cụm (req = bộ phận đề xuất · pur = khảo sát/thu mua) lưu JSON ở cột supplier_info.
_AUTO_NOTE_PREFIX = "Sinh tự động từ Yêu cầu báo giá"   # dấu hiệu phiếu tạo từ YCKS (fallback dữ liệu cũ)


def _empty_cluster() -> dict:
    return {"name": "", "tax_code": "", "contact": ""}


def _norm_cluster(c) -> dict:
    """Chuẩn hóa 1 cụm về đúng 3 khóa string (chống dữ liệu JSON lỗi)."""
    c = c if isinstance(c, dict) else {}
    return {"name": (c.get("name") or ""), "tax_code": (c.get("tax_code") or ""),
            "contact": (c.get("contact") or "")}


def clusters_of(pr) -> dict:
    """Trả về {req, pur, from_survey}. Ưu tiên supplier_info JSON; nếu trống thì suy từ dữ liệu cũ:
    phiếu sinh từ YCKS -> cụm 'pur', còn lại -> cụm 'req' (giữ nguyên cột suggested_supplier*)."""
    raw = (getattr(pr, "supplier_info", "") or "").strip()
    if raw:
        try:
            d = json.loads(raw)
            if isinstance(d, dict):
                return {"req": _norm_cluster(d.get("req")), "pur": _norm_cluster(d.get("pur")),
                        "from_survey": bool(d.get("from_survey"))}
        except Exception:
            pass
    # Dữ liệu cũ (trước Task 4): cột suggested_supplier* xưa CHỈ phía thu mua/nhập liệu điền được
    # (người yêu cầu bị khóa ở Task 5) -> luôn đưa vào cụm 'pur', KHÔNG cho bộ phận yêu cầu thấy.
    legacy = {"name": getattr(pr, "suggested_supplier", "") or "",
              "tax_code": getattr(pr, "suggested_supplier_tax_code", "") or "",
              "contact": getattr(pr, "suggested_supplier_contact", "") or ""}
    from_survey = (getattr(pr, "note", "") or "").startswith(_AUTO_NOTE_PREFIX)
    return {"req": _empty_cluster(), "pur": legacy, "from_survey": from_survey}


def apply_supplier_info(pr, clusters: dict) -> None:
    """Ghi supplier_info (JSON) + đồng bộ 'NCC hiệu lực' xuống cột suggested_supplier* cũ
    (ĐMH/list/mẫu in cũ vẫn dùng). Hiệu lực = cụm pur nếu có tên, ngược lại cụm req."""
    req = _norm_cluster(clusters.get("req"))
    pur = _norm_cluster(clusters.get("pur"))
    fs = bool(clusters.get("from_survey"))
    pr.supplier_info = json.dumps({"req": req, "pur": pur, "from_survey": fs}, ensure_ascii=False)
    eff = pur if pur["name"] else req
    pr.suggested_supplier = eff["name"]
    pr.suggested_supplier_tax_code = eff["tax_code"]
    pr.suggested_supplier_contact = eff["contact"]


def build_clusters(prev: dict, data, can_write_pur: bool, from_survey=None) -> dict:
    """Ghép cụm NCC khi lưu: cụm req ai sửa cũng được; cụm pur chỉ khi có quyền supplier.write.
    Cụm không được gửi/không đủ quyền -> giữ nguyên giá trị cũ (prev)."""
    req = _norm_cluster(prev.get("req"))
    pur = _norm_cluster(prev.get("pur"))
    fs = bool(prev.get("from_survey")) if from_survey is None else bool(from_survey)
    if getattr(data, "supplier_req", None) is not None:
        req = _norm_cluster(data.supplier_req.model_dump())
    if getattr(data, "supplier_pur", None) is not None and can_write_pur:
        pur = _norm_cluster(data.supplier_pur.model_dump())
    return {"req": req, "pur": pur, "from_survey": fs}

# Trạng thái xử lý theo DÒNG hàng (rút gọn — CR-007 #3): gộp 2 mức chứng từ kế toán
# ("Chưa gửi ĐMH cho KT"/"Đã gửi ĐMH cho KT") vào "Đã nhận hàng"; bỏ "Tạm ngưng".
LINE_STATUS = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng", "Hoàn thành", "Hủy đơn"]


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
        # Thông báo cho Người tạo PYC khi YCMH hoàn thành toàn bộ
        if pr.created_by:
            from app.modules.notification.service import trigger_notification
            trigger_notification(
                db=db, event="pr_completed", doc_type="purchase_request", doc_code=pr.code,
                creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
                recipient_ids=[pr.created_by]
            )


# Thứ tự tiến độ dòng (đồng bộ với ĐMH); dòng YCMH = mức KÉM TIẾN NHẤT trong các dòng ĐMH liên kết
# Phải KHỚP PROGRESS_ORDER của ĐMH (Task 8 chèn "Chưa gửi ĐMH cho KT"); thiếu sẽ khiến
# sync đặt nhầm dòng về "Chưa đặt hàng".
_PROGRESS_ORDER = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng",
                   "Chưa gửi ĐMH cho KT", "Đã gửi ĐMH cho KT", "Hoàn thành"]


def sync_from_purchase_orders(db: Session, pr_code: str) -> None:
    """Suy trạng thái + tiến độ SL từng dòng YCMH từ các dòng ĐMH liên kết (khớp product_code),
    rồi suy lại trạng thái phiếu.
    - Chỉ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/bị trả lại/đã từ chối).
    - Dòng ĐMH Hủy: không cộng SL; dòng Tạm ngưng: dùng mức tiến độ trước khi tạm ngưng.
    - Trạng thái dòng YCMH rút gọn còn 5 mức; dòng bị Hủy THỦ CÔNG trên YCMH thì giữ nguyên.
    - qty_ordered/qty_received: tổng SL đặt/nhận theo product_code (đồng bộ vào DB)."""
    if not pr_code:
        return
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return
    from sqlalchemy import func
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    lines = (db.query(POItem).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
             .filter(PurchaseOrder.pr_code == pr_code,
                     PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]))
             .all())
    # Tổng SL đã nhận theo từng dòng ĐMH (gom các lần giao).
    recv_by_item: dict[int, float] = {}
    item_ids = [ln.id for ln in lines]
    if item_ids:
        rows = (db.query(PODelivery.po_item_id, func.coalesce(func.sum(PODelivery.received_qty), 0))
                .filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all())
        recv_by_item = {r[0]: float(r[1] or 0) for r in rows}
    ordered_min: dict[str, int] = {}      # sp -> mức KÉM TIẾN NHẤT trong các dòng ĐÃ ĐẶT (>= "Đã đặt hàng")
    has_cancel: set[str] = set()          # sp có dòng Hủy đơn
    ordered_by_prod: dict[str, float] = {}   # sp -> tổng SL đã đặt
    received_by_prod: dict[str, float] = {}  # sp -> tổng SL đã nhận
    for ln in lines:
        p = ln.product_code
        ps = ln.progress_status or "Chưa đặt hàng"
        if ps == "Hủy đơn":
            has_cancel.add(p); continue      # dòng hủy: không tính SL, không tính tiến độ
        if ps == "Tạm ngưng":
            ps = ln.status_before_pause or "Đã đặt hàng"   # dùng mức trước khi tạm ngưng
        idx = _PROGRESS_ORDER.index(ps) if ps in _PROGRESS_ORDER else 0
        # Dòng ĐMH CHƯA đặt (kể cả đơn đã duyệt nhưng chưa bấm đặt, hoặc đơn nháp mới tạo)
        # KHÔNG kéo trạng thái/tiến độ YCMH xuống — bỏ qua hoàn toàn.
        if idx < 1:
            continue
        ordered_by_prod[p] = ordered_by_prod.get(p, 0.0) + float(ln.qty_order or 0)
        received_by_prod[p] = received_by_prod.get(p, 0.0) + recv_by_item.get(ln.id, 0.0)
        cur = ordered_min.get(p)
        ordered_min[p] = idx if cur is None else min(cur, idx)
    _DONE = _PROGRESS_ORDER.index("Hoàn thành")
    
    prev_statuses = {it.id: (it.line_status or "") for it in items_of(db, pr.id)}
    new_receives = False

    for it in items_of(db, pr.id):
        p = it.product_code
        ordered = ordered_by_prod.get(p, 0.0)
        received = received_by_prod.get(p, 0.0)
        it.qty_ordered = round(ordered, 3)
        it.qty_received = round(received, 3)
        old_st = prev_statuses.get(it.id, "")
        if (it.line_status or "") == "Hủy đơn":
            continue  # ngoại lệ đặt thủ công trên YCMH thì giữ nguyên
        # Suy trạng thái theo SL/tiến độ THỰC (không bị dòng ĐMH chưa đặt làm sai):
        if p not in ordered_min:
            it.line_status = "Hủy đơn" if p in has_cancel else "Chưa đặt hàng"
        elif ordered_min[p] >= _DONE:
            it.line_status = "Hoàn thành"        # mọi dòng ĐMH đã đặt đều Hoàn thành
        elif received > 0:
            it.line_status = "Đã nhận hàng"      # đã nhận (một phần trở lên)
        else:
            it.line_status = "Đã đặt hàng"       # đã đặt, chưa nhận

        if (it.line_status in ("Đã nhận hàng", "Hoàn thành")) and (old_st not in ("Đã nhận hàng", "Hoàn thành")):
            new_receives = True

    db.commit()
    recompute_status(db, pr)

    # Thông báo cho Người tạo PYC khi dòng hàng vừa được nhận đủ / hoàn thành
    if new_receives and pr.created_by:
        from app.modules.notification.service import trigger_notification
        trigger_notification(
            db=db, event="pr_items_received", doc_type="purchase_request", doc_code=pr.code,
            creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
            recipient_ids=[pr.created_by]
        )


def update_item_status(db: Session, pid: int, data: ItemStatusIn, user_id: int, emp_code: str, is_manager: bool) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")
    rows = {i.id: i for i in items_of(db, pid)}
    _expected_changes: list[str] = []
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
        # Thời gian dự kiến có hàng: rỗng → cập nhật tự do; ĐÃ có giá trị → đổi phải kèm lý do.
        if it.expected_date is not None:
            old = (row.expected_date or "").strip()
            new = (it.expected_date or "").strip()
            if new != old:
                reason = (it.expected_date_reason or "").strip()
                if old and not reason:
                    raise HTTPException(400, f"Đổi 'thời gian dự kiến có hàng' của '{row.product_name}' "
                                             f"(từ {old}) phải kèm lý do.")
                row.expected_date = new
                _expected_changes.append(f"{row.product_name}: {old or '—'} → {new or '—'}"
                                         + (f" · lý do: {reason}" if reason else ""))
    pr.updated_by = user_id
    db.commit()
    recompute_status(db, pr)
    record(db, user_id, ENTITY, pid, "line_status", "Cập nhật trạng thái dòng")
    for msg in _expected_changes:
        record(db, user_id, ENTITY, pid, "expected_date", msg)
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
    # Chỉ hoàn thành phiếu khi MỌI dòng đã ở điểm cuối ("Hoàn thành"/"Hủy đơn") —
    # tránh bấm Hoàn thành khi sản phẩm còn chưa đặt hàng/đang xử lý.
    items = items_of(db, pid)
    pending = [it for it in items if (it.line_status or "Chưa đặt hàng") not in ("Hoàn thành", "Hủy đơn")]
    if not items or pending:
        raise HTTPException(400, "Chưa có sản phẩm đặt hàng hoàn tất — chỉ hoàn thành phiếu khi mọi sản phẩm đã Hoàn thành hoặc Hủy.")
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
    """Upsert dòng THEO id — dòng có id thì cập nhật TẠI CHỖ (giữ nguyên id), dòng không id
    thêm mới, dòng cũ không còn trong danh sách thì xóa. GIỮ id để ảnh đối chiếu
    (đính kèm entity 'purchase_request_line_image' theo id dòng) không bị mồ côi khi lưu lại phiếu."""
    existing = {i.id: i for i in db.query(PurchaseRequestItem)
                .filter(PurchaseRequestItem.pr_id == pr_id).all()}
    keep: set[int] = set()
    for it in items or []:
        data = it.model_dump()
        rid = data.pop("id", None)
        # Task 4: thành tiền dòng GỒM VAT (qty × giá × (1 + vat%/100))
        _vp = data.get("vat_pct") or 0
        data["amount"] = round((data.get("qty") or 0) * (data.get("price") or 0) * (1 + _vp / 100), 2)
        row = existing.get(rid) if rid else None
        if row is not None:                       # cập nhật tại chỗ -> id không đổi
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = user_id
            keep.add(row.id)
        else:                                     # dòng mới
            db.add(PurchaseRequestItem(pr_id=pr_id, created_by=user_id, updated_by=user_id, **data))
    for rid, row in existing.items():             # dòng bị bỏ khỏi danh sách -> xóa
        if rid not in keep:
            db.delete(row)
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
    # NGƯỜI YÊU CẦU của bản sao = người BẤM NHÂN BẢN (không giữ người yêu cầu phiếu gốc): nếu giữ
    # nguyên thì created_by=người clone + requester=người gốc -> lệch danh + cả hai đều có quyền YC.
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    _u = db.get(User, user_id) if user_id else None
    _emp = db.get(Employee, getattr(_u, "employee_id", 0) or 0) if _u and getattr(_u, "employee_id", 0) else None
    if _emp:
        _requester, _requester_id = (_emp.full_name or ""), _emp.id
        _requester_position, _department = (_emp.position or ""), (_emp.department_name or "")
        _head_of_dept = _emp.manager_name or ""
    else:
        _requester, _requester_id = "", 0
        _requester_position, _department, _head_of_dept = "", src.department, src.head_of_dept
    pr = PurchaseRequest(
        code="", company_id=src.company_id, requester=_requester,
        requester_id=_requester_id,
        requester_position=_requester_position, department=_department,
        head_of_dept=_head_of_dept, purpose=src.purpose, request_date=src.request_date,
        need_date=src.need_date, is_urgent=src.is_urgent, note=src.note,
        status="draft", assignee_id=0, created_by=user_id, updated_by=user_id,
        show_code_on_print=src.show_code_on_print, suggested_supplier=src.suggested_supplier,
        suggested_supplier_tax_code=src.suggested_supplier_tax_code,
        suggested_supplier_contact=src.suggested_supplier_contact,
        quote_filename=src.quote_filename, quote_file_url=src.quote_file_url,
        supplier_info=src.supplier_info or "",   # Task 4: giữ 2 cụm NCC khi nhân bản
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
             "price", "vat_pct", "amount", "warehouse", "required_date", "note"]
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _COPY}
        db.add(PurchaseRequestItem(pr_id=pr.id, created_by=user_id, updated_by=user_id,
                                   assignee="", line_status="Chưa đặt hàng", progress_note="", **data))
    db.commit()
    record(db, user_id, ENTITY, pr.id, "create", f"Nhân bản từ {src.code}")
    db.refresh(pr)
    return pr


def create_pr(db: Session, data: PRCreate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = PurchaseRequest(
        code=data.code or "", company_id=data.company_id, requester=data.requester,
        requester_id=data.requester_id,
        requester_position=data.requester_position, department=data.department,
        head_of_dept=data.head_of_dept, purpose=data.purpose, request_date=data.request_date,
        need_date=data.need_date, is_urgent=data.is_urgent, vat_rate=data.vat_rate,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        show_code_on_print=data.show_code_on_print,
        quote_filename=data.quote_filename,
        quote_file_url=data.quote_file_url,
    )
    # Task 4: NCC 2 cụm. Back-compat: body cũ gửi suggested_supplier* -> vào cụm 'req'.
    prev = {"req": {"name": data.suggested_supplier, "tax_code": data.suggested_supplier_tax_code,
                    "contact": data.suggested_supplier_contact},
            "pur": _empty_cluster(), "from_survey": False}
    apply_supplier_info(pr, build_clusters(prev, data, can_write_pur, from_survey=False))
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


def update_pr(db: Session, pid: int, data: PRUpdate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại "
                                 "(phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới).")
    old_urgent = bool(pr.is_urgent)
    # supplier_req/supplier_pur xử lý riêng bên dưới (không phải cột của model)
    for key, value in data.model_dump(exclude_unset=True,
                                      exclude={"items", "supplier_req", "supplier_pur"}).items():
        setattr(pr, key, value)
    # Task 4: cập nhật cụm NCC (req do người yêu cầu · pur cần quyền supplier.write)
    if data.supplier_req is not None or data.supplier_pur is not None:
        apply_supplier_info(pr, build_clusters(clusters_of(pr), data, can_write_pur))
    pr.updated_by = user_id
    db.commit()
    if data.items is not None:
        _save_items(db, pid, data.items, user_id)
    # Cờ Đơn gấp đổi → YCMH đè lên tất cả ĐMH cùng pr_code (đồng bộ nhóm)
    if bool(pr.is_urgent) != old_urgent and pr.code:
        from app.modules.purchase_order.service import sync_urgent_group
        sync_urgent_group(db, pr.code, bool(pr.is_urgent))
    record(db, user_id, ENTITY, pid, "update")
    db.refresh(pr)
    return pr


def set_urgent(db: Session, pid: int, is_urgent: bool, user_id: int) -> PurchaseRequest:
    """Bật/tắt cờ Đơn gấp trực tiếp (mọi trạng thái trừ đã hủy) + đồng bộ xuống các ĐMH cùng pr_code."""
    pr = get_pr(db, pid)
    if pr.status == "cancelled":
        raise HTTPException(400, "Phiếu đã hủy — không đổi được cờ Đơn gấp.")
    pr.is_urgent = bool(is_urgent)
    pr.updated_by = user_id
    db.commit()
    from app.modules.purchase_order.service import sync_urgent_group
    sync_urgent_group(db, pr.code, bool(is_urgent))
    record(db, user_id, ENTITY, pid, "update", f"Đơn gấp = {is_urgent}")
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
