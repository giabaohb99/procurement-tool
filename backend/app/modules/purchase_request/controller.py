from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.scoping import apply_scope
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.notification.service import trigger_notification

from sqlalchemy import func, select
from . import service
from .model import PurchaseRequest, PurchaseRequestItem
from .schema import ApproveIn, AssignIn, ItemStatusIn, PRCreate, PRUpdate, ReasonIn, RejectIn, UrgentIn

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase_request"])

HEADER_COLS = ["id", "code", "company_id", "requester", "requester_id", "requester_position",
               "department", "head_of_dept", "head_of_dept_id", "purpose", "request_date", "need_date",
               "status", "is_urgent", "vat_rate", "assignee_id", "note",
               "show_code_on_print", "suggested_supplier", "suggested_supplier_tax_code",
               "suggested_supplier_contact", "quote_filename", "quote_file_url"]


_SUPPLIER_FIELDS = ("suggested_supplier", "suggested_supplier_tax_code", "suggested_supplier_contact")


def _blank_supplier(d: dict) -> None:
    """Task 5: che NCC đề xuất khi user không có quyền supplier.read."""
    for k in _SUPPLIER_FIELDS:
        d[k] = ""


def _can_dispatch(profile: dict) -> bool:
    """CR-034 — ai được ĐIỀU PHỐI (duyệt lần 2). Điều kiện: có quyền `approve` trên YCMH VỚI
    phạm vi thu mua/toàn bộ ('proc'/'all'). Trưởng phòng có approve nhưng phạm vi 'dept' →
    chỉ duyệt lần 1, không điều phối. Cùng lối đọc grant với `_see_all_items`."""
    for g in profile.get("grants", []):
        p = g["perms"].get("purchase_request")
        if p and p.get("approve") and p.get("scope") in ("proc", "all"):
            return True
    return False


def _in_approve_scope(db: Session, user, pid: int) -> bool:
    """Phiếu có nằm trong phạm vi DUYỆT của người này không.
    CR-034: Admin thu mua có `approve` phạm vi 'proc' (để duyệt điều phối) — phạm vi đó không
    thấy phiếu 'submitted' nên họ tự động bị loại khỏi bước duyệt 1, không cần luật riêng."""
    return apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                       PurchaseRequest, "purchase_request", user, get_perm_profile(db, user)).first() is not None


def _notify_assigned(db: Session, pr, user, background_tasks: BackgroundTasks) -> None:
    """Báo "được phân công phụ trách" cho NSTM vừa được gán tự động.
    Gọi ở bước điều phối (công tắc BẬT) hoặc ngay khi duyệt (công tắc TẮT) — nội dung y như nhau."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User as _User
    emp_ids = set()
    if pr.assignee_id:
        emp_ids.add(pr.assignee_id)
    codes = [it.assignee for it in service.items_of(db, pr.id) if it.assignee]
    if codes:
        emp_ids.update(e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all())
    if not emp_ids:
        return
    uids = [u.id for u in db.query(_User).filter(_User.employee_id.in_(emp_ids), _User.is_active == True).all()]
    if uids:
        trigger_notification(db=db, event="pr_assigned", doc_type="purchase_request", doc_code=pr.code,
                             creator_id=user.id, background_tasks=background_tasks,
                             link=f"/purchase-requests/{pr.id}", recipient_ids=uids)


# Chữ ký 2 bước duyệt trên phiếu in chỉ có hiệu lực từ mốc trạng thái tương ứng trở đi.
# Phiếu bị TRẢ VỀ (Nháp / Chờ duyệt) sẽ KHÔNG in lại chữ ký duyệt của lần trước.
_AFTER_APPROVE = ("approved", "dispatched", "processing", "completed", "done")
_AFTER_DISPATCH = ("dispatched", "processing", "completed", "done")


def _approval_signers(db: Session, pr) -> dict:
    """Người ký 2 bước duyệt của phiếu — tra từ nhật ký thao tác (audit log).

    Bước 1 `approved`  (trưởng phòng duyệt)  -> ô "TP/BP đề xuất" trên phiếu in.
    Bước 2 `dispatched` (thu mua điều phối)  -> ô "TP/BP mua hàng".
    Công tắc `pr_dispatch_enabled` TẮT: một người làm cả 2 bước -> 2 ô cùng một chữ ký, đúng thực tế.
    """
    from app.core.audit import resolve_actor, resolve_signature
    from app.modules.audit.model import AuditLog

    out = {"approver_name": "", "approver_signature": "",
           "dispatcher_name": "", "dispatcher_signature": ""}
    want = ([("approved", "approver")] if pr.status in _AFTER_APPROVE else []) + \
           ([("dispatched", "dispatcher")] if pr.status in _AFTER_DISPATCH else [])
    if not want:
        return out
    actions = [a for a, _ in want]
    rows = (db.query(AuditLog.action, AuditLog.created_by)
            .filter(AuditLog.entity == service.ENTITY, AuditLog.entity_id == pr.id,
                    AuditLog.action.in_(actions))
            .order_by(AuditLog.id.desc()).all())
    latest: dict[str, int] = {}
    for action, uid in rows:
        latest.setdefault(action, uid)        # dòng đầu = lần duyệt GẦN NHẤT
    for action, key in want:
        uid = latest.get(action)
        if uid:
            out[f"{key}_name"] = resolve_actor(db, uid)
            out[f"{key}_signature"] = resolve_signature(db, uid)
    return out


def _out(db: Session, pr, user=None) -> dict:
    from app.core.audit import (resolve_actor, resolve_signature,
                                resolve_signature_by_employee)
    d = {c: getattr(pr, c) for c in HEADER_COLS}
    d["vat_rate"] = float(pr.vat_rate or 0)
    # Trưởng bộ phận: phiếu lập lúc phòng chưa gán trưởng sẽ lưu rỗng và ở rỗng vĩnh viễn.
    # Rỗng thì lấy theo Department.manager_id hiện tại để HIỂN THỊ (không ghi đè dữ liệu đã lưu).
    if not d.get("head_of_dept") and pr.department:
        d["head_of_dept"] = service.find_dept_head(db, pr.department)
    # Task 4: NCC 2 cụm. Cụm 'req' (bộ phận đề xuất) MỌI người xem/sửa được — sửa bug người
    # yêu cầu không nhập nổi NCC của chính mình. Cụm 'pur' (khảo sát/thu mua) cần supplier.read
    # để xem, supplier.write để sửa.
    can_sup_read = user is None or user_has_permission(db, user, "supplier", "read")
    cl = service.clusters_of(pr)
    d["supplier_req"] = cl["req"]
    d["supplier_pur"] = cl["pur"] if can_sup_read else service._empty_cluster()
    d["supplier_from_survey"] = cl["from_survey"]
    d["can_edit_supplier_pur"] = user is not None and user_has_permission(db, user, "supplier", "write")
    # CR-034: nút duyệt lần 2 (điều phối) — quyền tính ở server (phạm vi grant không có ở map
    # quyền phía FE). Công tắc tắt thì không ai thấy nút, vì phiếu không dừng ở 'approved' nữa.
    d["dispatch_enabled"] = service.dispatch_enabled()
    d["can_dispatch"] = bool(user is not None and pr.status == "approved" and d["dispatch_enabled"]
                             and _can_dispatch(get_perm_profile(db, user)))
    # Duyệt bước 1: cũng phải tính ở server vì có quyền `approve` chưa chắc đúng PHẠM VI —
    # Admin thu mua (phạm vi 'proc') có approve để duyệt điều phối nhưng không duyệt bước 1.
    # CR-071: ô TBP (`head_of_dept_id`) CHỈ để lưu + in, KHÔNG khóa quyền duyệt — chọn ai
    # thì ai có quyền trong phạm vi vẫn duyệt được như trước.
    d["can_approve"] = bool(user is not None and pr.status == "submitted"
                            and user_has_permission(db, user, "purchase_request", "approve")
                            and _in_approve_scope(db, user, pr.id))
    # NCC "hiệu lực" ở cột cũ (suggested_supplier*) — che nếu không có supplier.read (giữ Task 5).
    if not can_sup_read:
        _blank_supplier(d)
    d["created_at"] = pr.created_at
    d["created_by_name"] = resolve_actor(db, pr.created_by)
    # Chữ ký ô "Người lập" trên phiếu in. Tra theo NHÂN SỰ người yêu cầu (đúng cái TÊN đang in);
    # phiếu cũ chưa có requester_id thì mới lấy chữ ký người tạo, và chỉ khi tên trùng nhau —
    # tránh in chữ ký người A dưới tên người B khi thu mua lập phiếu hộ bộ phận khác.
    d["requester_signature"] = resolve_signature_by_employee(db, pr.requester_id)
    if not d["requester_signature"] and not pr.requester_id:
        if (d["created_by_name"] or "").strip() == (pr.requester or "").strip():
            d["requester_signature"] = resolve_signature(db, pr.created_by)
    # Chữ ký + họ tên 2 ô duyệt trên phiếu in (TP/BP đề xuất · TP/BP mua hàng)
    d.update(_approval_signers(db, pr))

    # Fetch company name safely to avoid permission issues on the frontend
    d["company_name"] = ""
    if pr.company_id:
        from app.modules.company.model import Company
        comp = db.query(Company).filter(Company.id == pr.company_id).first()
        if comp:
            d["company_name"] = comp.name

    items = service.items_of(db, pr.id)
    # Batch resolve ảnh gốc theo product_code (2 query/phiếu, tránh N+1).
    from app.modules.product.model import Product
    from app.modules.attachment.model import FileLink, StoredFile
    codes = {i.product_code for i in items if i.product_code}
    prod_by_code: dict[str, int] = {}
    if codes:
        for pid_, code_ in db.query(Product.id, Product.code).filter(Product.code.in_(codes)):
            prod_by_code.setdefault(code_, pid_)   # code catalog duy nhất
    thumb_by_pid: dict[int, str] = {}
    if prod_by_code:
        q = (db.query(FileLink.entity_id, StoredFile.url)
             .join(StoredFile, StoredFile.id == FileLink.file_id)
             .filter(FileLink.entity == "product", FileLink.entity_id.in_(prod_by_code.values()))
             .order_by(FileLink.entity_id, FileLink.sort_order.asc(), FileLink.id.desc()))
        for eid, url in q:
            thumb_by_pid.setdefault(eid, url)      # ảnh sort_order nhỏ nhất mỗi SP
    d["items"] = []
    for i in items:
        pid_ = prod_by_code.get(i.product_code or "")
        d["items"].append(
            {"id": i.id, "product_code": i.product_code, "product_name": i.product_name,
             "item_group": i.item_group, "group_desc": i.group_desc, "qty": float(i.qty or 0),
             "unit": i.unit, "price": float(i.price or 0), "vat_pct": float(i.vat_pct or 0),
             "amount": float(i.amount or 0),
             "warehouse": i.warehouse, "required_date": i.required_date, "assignee": i.assignee,
             "expected_date": i.expected_date,
             "line_status": i.line_status, "progress_note": i.progress_note, "note": i.note,
             "qty_ordered": float(i.qty_ordered or 0), "qty_received": float(i.qty_received or 0),
             "product_id": pid_ or 0,                          # 0 = code không khớp catalog
             "product_thumbnail_url": thumb_by_pid.get(pid_, "") if pid_ else ""}
        )
    # Task 4: PYC tính VAT lại theo dòng — tiền hàng (chưa VAT) · VAT · tổng cộng (gồm VAT)
    subtotal = round(sum(x["qty"] * x["price"] for x in d["items"]), 2)   # chưa VAT
    total = round(sum(x["amount"] for x in d["items"]), 2)                # gồm VAT
    d["subtotal"] = subtotal
    d["vat"] = round(total - subtotal, 2)
    d["total"] = total
    return d


def _list_query(request: Request, db: Session, user):
    """Câu truy vấn danh sách (lọc + phạm vi + sắp xếp) — dùng chung cho màn danh sách và xuất Excel,
    để file xuất luôn ra ĐÚNG những phiếu người dùng đang thấy."""
    query = apply_filters(db.query(PurchaseRequest).filter(PurchaseRequest.is_deleted == False), PurchaseRequest, request, service.FILTERABLE)
    query = apply_range_filters(query, PurchaseRequest, request, ["request_date", "need_date"])
    query = apply_equals(query, PurchaseRequest, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.item_group.like(f"%{item_group}%"))
        query = query.filter(PurchaseRequest.id.in_(sub))
    assignee = (request.query_params.get("assignee") or "").strip()
    if assignee:
        sub2 = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == assignee)
        query = query.filter(PurchaseRequest.id.in_(sub2))
    # CR-069 — tìm phiếu theo MÃ HÀNG / TÊN HÀNG ở dòng hàng (bảng con). Khớp MỘT PHẦN:
    # gõ "5155" ra cả HOP5155 lẫn NHG5155. Cùng lối với ô tìm nhanh của màn Tiến độ mua hàng.
    product = (request.query_params.get("product") or "").strip()
    if product:
        like = f"%{product}%"
        sub3 = select(PurchaseRequestItem.pr_id).where(
            (PurchaseRequestItem.product_code.like(like)) | (PurchaseRequestItem.product_name.like(like)))
        query = query.filter(PurchaseRequest.id.in_(sub3))
    query = apply_scope(query, PurchaseRequest, "purchase_request", user, get_perm_profile(db, user))
    # Sort theo cột người dùng bấm (tiebreak id desc do service thêm); cột 'total' là tính toán -> bỏ qua
    return apply_sort_from_request(query, PurchaseRequest, request)


@router.get("")
def list_pr(
    request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("purchase_request", "read")),
):
    query = _list_query(request, db, user)
    total, items = service.list_pr(db, query, pg)
    
    pr_ids = [p.id for p in items]
    subtotals = {}
    need_dates = {}
    if pr_ids:
        subtotals = {
            pr_id: float(amount or 0) for pr_id, amount in db.query(
                PurchaseRequestItem.pr_id,
                func.sum(PurchaseRequestItem.amount)
            ).filter(PurchaseRequestItem.pr_id.in_(pr_ids)).group_by(PurchaseRequestItem.pr_id).all()
        }
        need_rows = db.query(
            PurchaseRequestItem.pr_id,
            func.min(PurchaseRequestItem.required_date)
        ).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids),
            PurchaseRequestItem.required_date != "",
            PurchaseRequestItem.required_date.isnot(None),
            PurchaseRequestItem.line_status != "Hủy đơn"
        ).group_by(PurchaseRequestItem.pr_id).all()
        need_dates = {r[0]: r[1] for r in need_rows if r[1]}

    cancelled_ids = set()
    if pr_ids:
        cancelled_ids = {r[0] for r in db.query(PurchaseRequestItem.pr_id).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids), PurchaseRequestItem.line_status == "Hủy đơn").distinct().all()}

    can_see_supplier = user_has_permission(db, user, "supplier", "read")   # Task 5
    out_items = []
    for p in items:
        d = {c: getattr(p, c) for c in HEADER_COLS}
        d["created_at"] = p.created_at   # thời điểm tạo (có giờ) — hiển thị giờ VN ở list
        d["need_date"] = need_dates.get(p.id) or p.need_date or ""
        d["total"] = round(subtotals.get(p.id, 0.0), 2)   # gồm VAT (tính từ amount dòng)
        d["has_cancelled_line"] = p.id in cancelled_ids
        if not can_see_supplier:
            _blank_supplier(d)   # ẩn NCC đề xuất
        out_items.append(d)

    return success({"total": total, "items": out_items})


@router.get("/export/xlsx")
def export_xlsx(
    request: Request, ids: str = "", cols: str = "",
    db: Session = Depends(get_db), user=Depends(require("purchase_request", "export")),
):
    """CR-068 — xuất Excel danh sách YCMH, mỗi dòng hàng một hàng.

    `ids` = các phiếu người dùng tự tick (ưu tiên); bỏ trống thì xuất theo đúng bộ lọc đang đặt.
    `cols` = danh sách cột đang hiện trên bảng, để file khớp với những gì họ nhìn thấy.
    Phải khai báo TRƯỚC route `/{pid}` kẻo 'export' bị nuốt thành id.
    """
    from app.core.export_xlsx import check_row_limit, parse_ids, pick_columns, xlsx_response
    from . import export as ex

    query = _list_query(request, db, user)
    id_list = parse_ids(ids)
    if id_list:
        query = query.filter(PurchaseRequest.id.in_(id_list))
    prs = query.order_by(PurchaseRequest.id.desc()).all()
    check_row_limit(len(prs))
    rows = ex.build_rows(db, prs)
    check_row_limit(len(rows))
    columns = pick_columns(ex.HEADER_COLS, cols) + list(ex.LINE_COLS)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


def _see_all_items(profile: dict, pr, user) -> bool:
    """Người tạo / người duyệt / xem toàn bộ chứng từ thu mua (scope proc/dept/company/all)
    → thấy mọi dòng. Nhân viên thu mua scope 'assigned/own' → chỉ thấy dòng phân bổ cho mình."""
    if pr.created_by == user.id:
        return True
    # Người YÊU CẦU (dù admin tạo giùm) cũng thấy mọi dòng của phiếu mình
    rid = getattr(user, "employee_id", 0) or 0
    if rid and getattr(pr, "requester_id", 0) == rid:
        return True
    for g in profile.get("grants", []):
        p = g["perms"].get("purchase_request")
        if not p:
            continue
        if p.get("approve"):
            return True
        if p.get("read") and p.get("scope") in ("proc", "dept", "company", "all"):
            return True
    return False


@router.get("/meta/dept-head")
def dept_head(department: str = "", db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP."""
    return success({"head_of_dept": service.find_dept_head(db, department)})


@router.get("/meta/dept-head-candidates")
def dept_head_candidates_meta(department: str = "", company_id: int = 0, db: Session = Depends(get_db),
                              user=Depends(require("purchase_request", "read"))):
    """CR-071 — cùng danh sách nhưng tra theo PHÒNG BAN, cho màn TẠO MỚI (chưa có id phiếu).

    Phải khai TRƯỚC `/{pid}` nếu không FastAPI nuốt "meta" thành pid.
    """
    return success({"items": service.dept_head_candidates_by_department(db, department, company_id)})


@router.get("/{pid}/dept-head-candidates")
def dept_head_candidates(pid: int, db: Session = Depends(get_db),
                         user=Depends(require("purchase_request", "read"))):
    """CR-071 — những người duyệt được bước 1 phiếu này, để ô "Trưởng bộ phận" cho chọn.

    Ô này CHỈ để lưu + in (xem ghi chú ở `service.py`), không khóa quyền duyệt của ai.
    Danh sách rỗng = chưa ai đủ điều kiện; lúc đó FE để ô ở dạng chữ như cũ.
    """
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success({"items": service.dept_head_candidates(db, pr)})


@router.get("/{pid}")
def get_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    data = _out(db, pr, user)
    if not _see_all_items(profile, pr, user):
        code = profile.get("emp_code") or ""
        data["items"] = [it for it in data["items"] if (it.get("assignee") or "") == code]
    return success(data)


@router.get("/{pid}/order-progress")
def order_progress(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ các ĐMH cùng mã PYC.
    CHỈ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/hủy/từ chối) — phiếu nháp KHÔNG tính là đã đặt,
    khớp với logic đồng bộ trạng thái dòng (sync_from_purchase_orders).
    Dùng để prefill 'số lượng còn thiếu' khi tạo ĐMH mới + cảnh báo đặt vượt."""
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    rows = (db.query(POItem.product_code, func.coalesce(func.sum(POItem.qty_order), 0))
            .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
            .filter(PurchaseOrder.pr_code == pr.code,
                    PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]),
                    POItem.progress_status.notin_(["Chưa đặt hàng", "Hủy đơn"]))
            .group_by(POItem.product_code).all())
    ordered = {code: float(qty or 0) for code, qty in rows if code}
    return success({"ordered": ordered})


@router.post("")
def create_pr(data: PRCreate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: chỉ QL/Admin sửa cụm NCC thu mua
    return success(_out(db, service.create_pr(db, data, user.id, can_pur), user), "Đã tạo yêu cầu mua", 201)


@router.post("/{pid}/copy")
def copy_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.post("/{pid}/clone")   # alias để nút Nhân bản ở danh sách (CrudList) dùng chung 1 đường dẫn
def clone_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.patch("/{pid}/assign")
def assign_pr(pid: int, data: AssignIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    pr = service.assign(db, pid, data, user.id)
    # Thông báo "được phân công phụ trách" cho NSTM (NSTM header + NSTM từng dòng)
    from app.modules.employee.model import Employee
    from app.modules.user.model import User as _User
    emp_ids = set()
    if pr.assignee_id:
        emp_ids.add(pr.assignee_id)
    codes = [it.assignee for it in service.items_of(db, pid) if it.assignee]
    if codes:
        emp_ids.update(e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all())
    if emp_ids:
        uids = [u.id for u in db.query(_User).filter(_User.employee_id.in_(emp_ids), _User.is_active == True).all()
                if u.id != user.id]   # không tự báo mình
        if uids:
            trigger_notification(db=db, event="pr_assigned", doc_type="purchase_request", doc_code=pr.code,
                                 creator_id=user.id, background_tasks=background_tasks,
                                 link=f"/purchase-requests/{pr.id}", recipient_ids=uids)
    return success(_out(db, pr, user), "Đã lưu phân bổ NSTM")


@router.patch("/{pid}/urgent")
def set_urgent(pid: int, data: UrgentIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "write"))):
    """Bật/tắt cờ Đơn gấp (cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH cùng pr_code."""
    pr = service.set_urgent(db, pid, data.is_urgent, user.id)
    return success(_out(db, pr, user))


@router.patch("/{pid}/item-status")
def update_item_status(pid: int, data: ItemStatusIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    prof = get_perm_profile(db, user)
    pr_perm = prof["perms_union"].get("purchase_request", {})
    is_manager = bool(pr_perm.get("cancel") or pr_perm.get("approve"))   # quản lý/admin sửa mọi dòng
    emp_code = prof.get("emp_code") or ""
    return success(_out(db, service.update_item_status(db, pid, data, user.id, emp_code, is_manager), user), "Đã cập nhật trạng thái")


def _ensure_can_return_or_reject(db: Session, user, pr: PurchaseRequest):
    """Trả về / Từ chối: Quản lý (quyền cancel) làm được mọi giai đoạn;
    Người duyệt (quyền approve) chỉ làm được ở bước Chờ duyệt (submitted) VÀ trong phạm vi của mình."""
    if user_has_permission(db, user, "purchase_request", "cancel"):
        return
    if pr.status == "submitted" and user_has_permission(db, user, "purchase_request", "approve") \
            and _in_approve_scope(db, user, pr.id):
        return
    raise HTTPException(403, "Bạn không có quyền trả về / từ chối phiếu này")


@router.post("/{pid}/cancel")
def cancel_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.cancel_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_cancelled", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã hủy phiếu")


@router.post("/{pid}/return")
def return_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.return_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_returned", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã trả phiếu về (Bị trả lại)")


@router.post("/{pid}/complete")
def complete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "cancel"))):
    return success(_out(db, service.complete_pr(db, pid, user.id), user), "Đã hoàn thành phiếu")


def _can_edit_own(db: Session, pr, user) -> bool:
    """Người TẠO / người YÊU CẦU (admin tạo giùm) / người có quyền write được sửa & gửi duyệt."""
    rid = getattr(user, "employee_id", 0) or 0
    if pr.created_by == user.id or (rid and getattr(pr, "requester_id", 0) == rid):
        return True
    return user_has_permission(db, user, "purchase_request", "write")


@router.patch("/{pid}")
def update_pr(pid: int, data: PRUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    pr = service.get_pr(db, pid)
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: cụm NCC thu mua chỉ QL/Admin sửa
    return success(_out(db, service.update_pr(db, pid, data, user.id, can_pur), user), "Đã cập nhật")


@router.delete("/{pid}")
def delete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    service.delete_pr(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_prs(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for pid in id_list:
        try:
            service.delete_pr(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {pid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


@router.post("/{pid}/submit")
def submit_pr(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    pr = service.get_pr(db, pid)
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền gửi duyệt phiếu này")
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt được phiếu ở trạng thái Nháp hoặc Bị trả lại")
    # CR-082: chốt cờ Đơn gấp trước khi gửi duyệt — phiếu cũ (tạo trước luật này) hoặc phiếu
    # sửa dòng bằng đường khác vẫn được đánh dấu đúng, và thông báo duyệt đi kèm mức ưu tiên thật.
    service.apply_auto_urgent(db, pr, user.id)
    pr = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(
        db=db,
        event="pr_submitted",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        link=f"/purchase-requests/{pr.id}",
        department=pr.department or "",
    )
    return success(_out(db, pr, user), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_pr(pid: int, data: ApproveIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    # Duyệt lần 1 (trưởng phòng) — chỉ trong phạm vi được phép duyệt. Phạm vi 'proc' (Admin thu mua)
    # không thấy phiếu 'submitted' nên tự động bị loại: họ chỉ điều phối, không duyệt thay trưởng phòng.
    if not _in_approve_scope(db, user, pid):
        raise HTTPException(403, "Ngoài phạm vi được phép duyệt")
    # CR-071 — KHÔNG chặn theo `head_of_dept_id`: ô TBP chỉ để lưu + in, luật duyệt giữ như cũ.
    pr = service.set_status(db, pid, "approved", user.id)
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    # CR-034: mặc định KHÔNG tự động phân bổ NSTM ở đây — phiếu dừng ở "Đã duyệt", chờ Quản lý/Admin
    # thu mua duyệt lần 2 (/dispatch). Nếu công tắc `pr_dispatch_enabled` bị TẮT thì chạy luôn bước
    # điều phối ngay tại đây (luồng cũ: duyệt phát là có nhân sự phụ trách).
    n = con_trong = 0
    if not service.dispatch_enabled():
        pr, n, con_trong = service.dispatch_pr(db, pid, user.id)
        _notify_assigned(db, pr, user, background_tasks)
    trigger_notification(
        db=db,
        event="pr_approved",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        approve_note=pr.note or "",
        link=f"/purchase-requests/{pr.id}"
    )
    if not service.dispatch_enabled():
        msg = f"Đã duyệt — tự động phân bổ {n} dòng"
        if con_trong:
            msg += f" · còn {con_trong} dòng chưa có người phụ trách, hãy chọn tay"
        return success(_out(db, pr, user), msg)
    return success(_out(db, pr, user), "Đã duyệt — phiếu chờ thu mua duyệt điều phối")


@router.post("/{pid}/dispatch")
def dispatch_pr(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                user=Depends(require("purchase_request", "approve"))):
    """CR-034 — Duyệt lần 2 phía thu mua (điều phối): tự động phân bổ NSTM rồi mở khóa tạo ĐMH."""
    if not service.dispatch_enabled():
        raise HTTPException(400, "Bước duyệt điều phối đang TẮT — phiếu được phân bổ nhân sự "
                                 "ngay khi trưởng bộ phận duyệt.")
    if not _can_dispatch(get_perm_profile(db, user)):
        raise HTTPException(403, "Chỉ Quản lý / Admin thu mua mới duyệt điều phối được phiếu")
    pr, n, con_trong = service.dispatch_pr(db, pid, user.id)
    # Thông báo "được phân công phụ trách" cho NSTM vừa được gán (trước CR-034 nằm ở bước duyệt)
    _notify_assigned(db, pr, user, background_tasks)
    msg = f"Đã duyệt điều phối — tự động phân bổ {n} dòng"
    if con_trong:
        msg += f" · còn {con_trong} dòng chưa có người phụ trách, hãy chọn tay"
    return success(_out(db, pr, user), msg)


@router.post("/{pid}/reject")
def reject_pr(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    pr = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(
        db=db,
        event="pr_rejected",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        reason=data.reason or "",
        link=f"/purchase-requests/{pr.id}"
    )
    return success(_out(db, pr, user), "Đã từ chối")
