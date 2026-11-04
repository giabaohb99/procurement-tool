"""YCMH — hủy, trả về người yêu cầu, chuyển phòng xử lý, hoàn tất, đổi trạng thái phiếu (bao-CR-715 tách từ
service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import normalize_handler_dept_id

from .model import PurchaseRequest
from .base_service import ENTITY, LINE_STATUS_CANCELLED, LINE_STATUS_DONE, LINE_STATUS_NO_PO, get_pr, items_of


def cancel_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = "cancelled"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "cancelled", reason)
    db.refresh(pr)
    return pr


#  bao-CR-554 — trả về được từ Chờ duyệt, và từ Đã duyệt / Đã điều phối khi chưa dòng nào lên ĐMH
#  (đại ca chốt 02/10/2026). Trước đây quản lý trả về phiếu đã có ĐMH vẫn lọt: dòng bị kéo về
#  `no_po` trong khi đơn vẫn còn.
def can_return_requester(db: Session, pr: PurchaseRequest) -> bool:
    if pr.status == "submitted":
        return True
    return can_transfer_dept(db, pr)   # khai bên dưới — chỉ gọi lúc chạy


def return_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    """Trả phiếu về "Bị trả lại" (rejected) — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCKS).
    Xóa nhân sự phụ trách + reset trạng thái mọi dòng về `no_po` (CR-074)."""
    pr = get_pr(db, pid)
    if not can_return_requester(db, pr):
        raise HTTPException(400, "Chỉ trả về được phiếu đang chờ duyệt, hoặc đã duyệt mà chưa dòng nào "
                                 "lên đơn mua hàng — hủy đơn liên quan trước")
    for it in items_of(db, pid):
        it.assignee = ""
        it.line_status = LINE_STATUS_NO_PO
    pr.assignee_id = 0
    pr.status = "rejected"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "returned", reason)
    db.refresh(pr)
    return pr


# ───────────── bao-CR-414 GĐ5: chuyển phòng xử lý / trả về phòng lập ─────────────

TRANSFERABLE_STATUSES = ("approved", "dispatched")


def dept_name_of(db: Session, dept_id: int, requesting_name: str = "") -> str:
    """Tên phòng xử lý để ghi nhật ký chuyển phòng.

    bao-CR-524: `0` là phòng thu mua mặc định, nên ghi tên phòng đó; danh mục chưa có phòng mặc
    định thì giữ đúng câu cũ (tên phòng lập)."""
    from app.modules.department.model import Department
    dept_id = normalize_handler_dept_id(db, dept_id)
    if not dept_id:
        return requesting_name or "phòng lập phiếu"
    dep = db.get(Department, dept_id)
    return dep.name if dep else f"#{dept_id}"


def can_transfer_dept(db: Session, pr: PurchaseRequest) -> bool:
    """Việc mua CHƯA thật sự bắt đầu ngoài đời: phiếu mới duyệt/điều phối và mọi dòng (trừ
    dòng đã Hủy tay) còn ở `no_po` — chưa dòng nào có ĐMH, kể cả ĐMH nháp/chờ duyệt.
    Dòng đã Hủy bỏ qua; ĐMH đã hủy không tính vì dòng của nó đã lùi về `no_po`."""
    if pr.status not in TRANSFERABLE_STATUSES:
        return False
    for it in items_of(db, pr.id):
        st = it.line_status or LINE_STATUS_NO_PO
        if st == LINE_STATUS_CANCELLED:
            continue
        if st != LINE_STATUS_NO_PO:
            return False
    return True


def validate_transfer_target(db: Session, ticket, handler_dept_id: int, reason: str) -> None:
    """Chốt chung cho YCMH và YCBG: lý do bắt buộc; phòng đích phải có thật, đang hoạt động
    và khác phòng đang xử lý; "Trả về thu mua" (đích = 0) chỉ khi phiếu đang ở phòng khác.

    bao-CR-524: đích `0` và phiếu cũ còn `0` đều hiểu là PHÒNG THU MUA MẶC ĐỊNH, so bằng id
    thật — nên chuyển phiếu thu mua chung về chính phòng lập (nhà máy) nay hợp lệ, còn chuyển
    sang phòng PBA017 một phiếu đang ở PBA017 thì bị chặn như trùng phòng."""
    from app.modules.department.model import Department
    if not (reason or "").strip():
        raise HTTPException(400, "Phải nêu lý do chuyển phòng / trả về")
    current = normalize_handler_dept_id(db, getattr(ticket, "handler_dept_id", 0))
    target = normalize_handler_dept_id(db, handler_dept_id)
    if not int(handler_dept_id or 0):
        if current == target:
            raise HTTPException(400, "Phiếu đang ở phòng thu mua mặc định, không có gì để trả về")
        return
    # `current == 0` chỉ còn khi danh mục chưa có phòng mặc định — giữ đúng luật cũ (0 = phòng lập).
    if target == current or (current == 0 and target == int(ticket.department_id or 0)):
        raise HTTPException(400, "Phòng đích trùng phòng đang xử lý")
    dep = db.get(Department, target)
    if not dep or not dep.is_active:
        raise HTTPException(400, "Phòng đích không tồn tại hoặc đã ngừng hoạt động")


def transfer_handler_dept(db: Session, pid: int, handler_dept_id: int, reason: str,
                          user_id: int) -> PurchaseRequest:
    """Đẩy YCMH sang phòng xử lý khác (hoặc TRẢ VỀ THU MUA khi `handler_dept_id` = 0 — bao-CR-524:
    đích là phòng thu mua mặc định, ghi id thật).

    Gỡ NSTM khỏi mọi dòng, đổi phòng, đưa phiếu về "Đã duyệt (chưa điều phối)" để phòng
    nhận điều phối lại. GIỮ `line_status` (đã kiểm là `no_po`/`cancelled`) và GIỮ cụm NCC.
    Không chuyển một phần dòng."""
    pr = get_pr(db, pid)
    if not can_transfer_dept(db, pr):
        raise HTTPException(400, "Chỉ chuyển được khi phiếu vừa duyệt/điều phối và chưa dòng nào có ĐMH")
    validate_transfer_target(db, pr, handler_dept_id, reason)
    old_id = int(pr.handler_dept_id or 0)
    new_id = normalize_handler_dept_id(db, handler_dept_id)
    for it in items_of(db, pid):
        it.assignee = ""
    pr.assignee_id = 0
    pr.handler_dept_id = new_id
    pr.status = "approved"
    pr.updated_by = user_id
    db.commit()
    action = "return_dept" if not int(handler_dept_id or 0) else "transfer_dept"
    old_name = dept_name_of(db, old_id, pr.department)
    new_name = dept_name_of(db, new_id, pr.department)
    record(db, user_id, ENTITY, pid, action, f"{reason.strip()} · {old_name} -> {new_name}")
    db.refresh(pr)
    return pr


def complete_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    # Chỉ hoàn thành phiếu khi MỌI dòng đã ở điểm cuối (`completed`/`cancelled`) —
    # tránh bấm Hoàn thành khi sản phẩm còn chưa đặt hàng/đang xử lý.
    items = items_of(db, pid)
    pending = [it for it in items
               if (it.line_status or LINE_STATUS_NO_PO) not in LINE_STATUS_DONE]
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


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "",
               audit: bool = True) -> PurchaseRequest:
    """`audit=False` (bao-CR-485): người gọi tự ghi dòng sổ — dùng khi cùng một cú bấm còn
    kéo theo bước tự động và muốn cả hai gói vào MỘT dòng, không ghi hai dòng."""
    pr = get_pr(db, pid)
    pr.status = status
    pr.updated_by = user_id
    db.commit()
    if audit:
        record(db, user_id, ENTITY, pid, status, message)
    db.refresh(pr)
    return pr
