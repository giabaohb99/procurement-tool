from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.scoping import apply_scope
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.notification.service import trigger_notification

from sqlalchemy import func, select
from . import service
from .model import PurchaseRequest, PurchaseRequestItem
from .schema import ApproveIn, AssignIn, ItemStatusIn, PRCreate, PRUpdate, ReasonIn, RejectIn

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase_request"])

HEADER_COLS = ["id", "code", "company_id", "requester", "requester_id", "requester_position",
               "department", "head_of_dept", "purpose", "request_date", "need_date",
               "status", "is_urgent", "vat_rate", "assignee_id", "note",
               "show_code_on_print", "suggested_supplier", "suggested_supplier_tax_code",
               "suggested_supplier_contact", "quote_filename", "quote_file_url"]


def _out(db: Session, pr) -> dict:
    from app.core.audit import resolve_actor
    d = {c: getattr(pr, c) for c in HEADER_COLS}
    d["vat_rate"] = float(pr.vat_rate or 0)
    d["created_at"] = pr.created_at
    d["created_by_name"] = resolve_actor(db, pr.created_by)
    
    # Fetch company name safely to avoid permission issues on the frontend
    d["company_name"] = ""
    if pr.company_id:
        from app.modules.company.model import Company
        comp = db.query(Company).filter(Company.id == pr.company_id).first()
        if comp:
            d["company_name"] = comp.name

    items = service.items_of(db, pr.id)
    d["items"] = [
        {"id": i.id, "product_code": i.product_code, "product_name": i.product_name,
         "item_group": i.item_group, "group_desc": i.group_desc, "qty": float(i.qty or 0),
         "unit": i.unit, "price": float(i.price or 0), "amount": float(i.amount or 0),
         "warehouse": i.warehouse, "required_date": i.required_date, "assignee": i.assignee,
         "line_status": i.line_status, "progress_note": i.progress_note, "note": i.note}
        for i in items
    ]
    subtotal = round(sum(x["amount"] for x in d["items"]), 2)
    d["subtotal"] = subtotal
    d["vat"] = 0            # Yêu cầu mua KHÔNG tính VAT (thuế tính ở PO/hóa đơn)
    d["total"] = subtotal
    return d


@router.get("")
def list_pr(
    request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("purchase_request", "read")),
):
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
    query = apply_scope(query, PurchaseRequest, "purchase_request", user, get_perm_profile(db, user))
    total, items = service.list_pr(db, query, pg)
    
    pr_ids = [p.id for p in items]
    subtotals = {}
    if pr_ids:
        subtotals = {
            pr_id: float(amount or 0) for pr_id, amount in db.query(
                PurchaseRequestItem.pr_id,
                func.sum(PurchaseRequestItem.amount)
            ).filter(PurchaseRequestItem.pr_id.in_(pr_ids)).group_by(PurchaseRequestItem.pr_id).all()
        }
        
    cancelled_ids = set()
    if pr_ids:
        cancelled_ids = {r[0] for r in db.query(PurchaseRequestItem.pr_id).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids), PurchaseRequestItem.line_status == "Hủy đơn").distinct().all()}

    out_items = []
    for p in items:
        d = {c: getattr(p, c) for c in HEADER_COLS}
        d["total"] = round(subtotals.get(p.id, 0.0), 2)   # Yêu cầu mua không tính VAT
        d["has_cancelled_line"] = p.id in cancelled_ids
        out_items.append(d)

    return success({"total": total, "items": out_items})


def _see_all_items(profile: dict, pr, user) -> bool:
    """Người tạo / quản lý (dept/company/all) / người duyệt → thấy mọi dòng.
    Nhân viên thu mua (được giao) → chỉ thấy dòng phân bổ cho mình."""
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
        if p.get("read") and p.get("scope") in ("dept", "company", "all"):
            return True
    return False


@router.get("/meta/dept-head")
def dept_head(department: str = "", db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP."""
    return success({"head_of_dept": service.find_dept_head(db, department)})


@router.get("/{pid}")
def get_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    data = _out(db, pr)
    if not _see_all_items(profile, pr, user):
        code = profile.get("emp_code") or ""
        data["items"] = [it for it in data["items"] if (it.get("assignee") or "") == code]
    return success(data)


@router.get("/{pid}/order-progress")
def order_progress(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ mọi ĐMH cùng mã PYC (bỏ PO bị từ chối).
    Dùng để prefill 'số lượng còn thiếu' khi tạo ĐMH mới + cảnh báo đặt vượt."""
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    rows = (db.query(POItem.product_code, func.coalesce(func.sum(POItem.qty_order), 0))
            .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
            .filter(PurchaseOrder.pr_code == pr.code, PurchaseOrder.status.notin_(["rejected", "cancelled"]))
            .group_by(POItem.product_code).all())
    ordered = {code: float(qty or 0) for code, qty in rows if code}
    return success({"ordered": ordered})


@router.post("")
def create_pr(data: PRCreate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.create_pr(db, data, user.id)), "Đã tạo yêu cầu mua", 201)


@router.post("/{pid}/copy")
def copy_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.copy_pr(db, pid, user.id)), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.post("/{pid}/clone")   # alias để nút Nhân bản ở danh sách (CrudList) dùng chung 1 đường dẫn
def clone_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.copy_pr(db, pid, user.id)), "Đã nhân bản thành phiếu Nháp mới", 201)


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
    return success(_out(db, pr), "Đã lưu phân bổ NSTM")


@router.patch("/{pid}/item-status")
def update_item_status(pid: int, data: ItemStatusIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    prof = get_perm_profile(db, user)
    pr_perm = prof["perms_union"].get("purchase_request", {})
    is_manager = bool(pr_perm.get("cancel") or pr_perm.get("approve"))   # quản lý/admin sửa mọi dòng
    emp_code = prof.get("emp_code") or ""
    return success(_out(db, service.update_item_status(db, pid, data, user.id, emp_code, is_manager)), "Đã cập nhật trạng thái")


def _ensure_can_return_or_reject(db: Session, user, pr: PurchaseRequest):
    """Trả về / Từ chối: Quản lý (quyền cancel) làm được mọi giai đoạn;
    Người duyệt (quyền approve) chỉ làm được ở bước Chờ duyệt (submitted)."""
    if user_has_permission(db, user, "purchase_request", "cancel"):
        return
    if pr.status == "submitted" and user_has_permission(db, user, "purchase_request", "approve"):
        return
    raise HTTPException(403, "Bạn không có quyền trả về / từ chối phiếu này")


@router.post("/{pid}/cancel")
def cancel_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.cancel_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_cancelled", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr), "Đã hủy phiếu")


@router.post("/{pid}/return")
def return_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.return_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_returned", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr), "Đã trả phiếu về (Bị trả lại)")


@router.post("/{pid}/complete")
def complete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "cancel"))):
    return success(_out(db, service.complete_pr(db, pid, user.id)), "Đã hoàn thành phiếu")


def _can_edit_own(db: Session, pr, user) -> bool:
    """Chủ phiếu (người tạo) được sửa/gửi duyệt phiếu của mình; hoặc người có quyền write."""
    return pr.created_by == user.id or user_has_permission(db, user, "purchase_request", "write")


@router.patch("/{pid}")
def update_pr(pid: int, data: PRUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    pr = service.get_pr(db, pid)
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    return success(_out(db, service.update_pr(db, pid, data, user.id)), "Đã cập nhật")


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
    return success(_out(db, pr), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_pr(pid: int, data: ApproveIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    pr = service.set_status(db, pid, "approved", user.id)
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    # Tự động phân bổ NSTM phụ trách cho từng dòng theo phân loại (Task 4)
    from app.modules.category_assignee.service import auto_assign_by_category
    auto_assign_by_category(db, pr)
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
    return success(_out(db, pr), "Đã duyệt")


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
    return success(_out(db, pr), "Đã từ chối")
