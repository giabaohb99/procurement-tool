"""YCMH — trả về CHỈ để sửa Công ty nhận hóa đơn (duoc-CR-803).

Luật anh Được chốt 28/11/2026:
  - Chỉ phiếu **Đang mua hàng** (`purchasing`) mới trả về kiểu này.
  - Mọi dòng của các ĐMH liên quan (cùng `pr_code`, chưa hủy) phải CHƯA nhận hàng; dòng nào đã nhận
    là chặn. ĐMH đã có Yêu cầu thanh toán / công nợ (vd tạm ứng trước) cũng chặn, vì đổi pháp nhân
    lúc đó lệch với chứng từ tiền.
  - Trả về xong: người yêu cầu chỉ sửa được Công ty nhận hóa đơn; các ĐMH liên quan bị khóa mọi thao
    tác ghi. Gửi duyệt → trưởng phòng duyệt như thường → đổi công ty trên các ĐMH, mở khóa, phiếu tự về
    lại mốc Đang mua hàng (không qua điều phối lại, giữ nguyên NSTM và trạng thái dòng).

Phiếu nằm ở `rejected` / `submitted` như trả về thường để dùng lại đường gửi duyệt, chuông báo và hộp
việc chờ duyệt; cột `return_mode` là thứ phân biệt hai kiểu.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.pr_return_codes import PrReturnMode
from app.core.status_codes import PO_PROGRESS_STATUS

from .base_service import ENTITY, get_pr, items_of
from .model import PurchaseRequest

INVOICE_COMPANY_RETURN_STATUSES = ("purchasing",)
# Tiến độ dòng ĐMH từ mốc "Đã nhận hàng" trở đi (bộ PO_PROGRESS_STATUS) — có là không cho trả về.
_ORDERED_PROGRESS = PO_PROGRESS_STATUS.ordered_values
_PO_PROGRESS_RECEIVED = _ORDERED_PROGRESS[_ORDERED_PROGRESS.index("received"):]
_PR_LINE_RECEIVED = ("received", "completed")


def is_invoice_company_return(pr: PurchaseRequest | None) -> bool:
    """Phiếu đang ở đợt trả về sửa Công ty nhận hóa đơn (chưa được duyệt lại)."""
    return bool(pr) and int(getattr(pr, "return_mode", 0) or 0) == PrReturnMode.INVOICE_COMPANY \
        and pr.status != "cancelled"


def _live_pos(db: Session, pr_code: str):
    from app.modules.purchase_order.model import PurchaseOrder
    if not pr_code:
        return []
    return (db.query(PurchaseOrder)
            .filter(PurchaseOrder.pr_code == pr_code, PurchaseOrder.is_deleted.is_(False),
                    PurchaseOrder.status != "cancelled")
            .all())


def find_invoice_company_return_blocker(db: Session, pr: PurchaseRequest) -> str:
    """Lý do KHÔNG trả về được kiểu sửa công ty; chuỗi rỗng = trả về được.

    Số truy vấn cố định (không lặp theo đơn): 1 lần lấy ĐMH, 1 lần soi dòng ĐMH, 1 lần soi dòng YCMH,
    2 lần soi chứng từ tiền."""
    if pr.status not in INVOICE_COMPANY_RETURN_STATUSES:
        return "Chỉ trả về sửa công ty nhận hóa đơn được phiếu đang ở trạng thái Đang mua hàng"
    return _find_po_document_blocker(db, pr)


def _find_po_document_blocker(db: Session, pr: PurchaseRequest) -> str:
    """Phần soi ĐMH của `find_invoice_company_return_blocker` — gọi lại lúc DUYỆT vì trong lúc khóa vẫn có thể
    phát sinh YCTT gõ tay mang mã ĐMH (dòng YCTT nhập tay không đi qua ĐMH)."""
    from app.modules.payable.model import Payable
    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
    from app.modules.purchase_order.model import POItem

    pos = _live_pos(db, pr.code)
    if not pos:
        return "Phiếu chưa có đơn mua hàng nào còn hiệu lực"
    po_ids = [p.id for p in pos]
    po_codes = [p.code for p in pos if p.code]
    received = (db.query(POItem.po_id)
                .filter(POItem.po_id.in_(po_ids),
                        POItem.progress_status != "cancelled",
                        (POItem.progress_status.in_(_PO_PROGRESS_RECEIVED)) | (POItem.qty_received > 0))
                .first())
    if received is not None:
        code = next((p.code for p in pos if p.id == received[0]), "")
        return f"Đơn mua hàng {code} đã có dòng nhận hàng — không trả về được phiếu này"
    # Dòng YCMH là bản phản chiếu tiến độ ĐMH (`_sync_pr`); soi thêm để dữ liệu cũ lệch nhau cũng không lọt.
    if any((it.line_status or "") in _PR_LINE_RECEIVED for it in items_of(db, pr.id)):
        return "Phiếu đã có dòng nhận hàng — không trả về được phiếu này"
    if po_codes:
        pay = (db.query(PaymentRequest.code)
               .join(PaymentRequestLine, PaymentRequestLine.request_id == PaymentRequest.id)
               .filter(PaymentRequestLine.po_code.in_(po_codes), PaymentRequest.is_deleted.is_(False),
                       PaymentRequest.status != "cancelled")
               .first())
        if pay:
            return f"Đơn mua hàng đã có yêu cầu thanh toán {pay[0]} — không trả về được phiếu này"
        if db.query(func.count(Payable.id)).filter(Payable.po_code.in_(po_codes)).scalar():
            return "Đơn mua hàng đã phát sinh công nợ — không trả về được phiếu này"
    return ""


def return_for_invoice_company(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    """Trả phiếu Đang mua hàng về người yêu cầu, chỉ để sửa Công ty nhận hóa đơn.

    KHÁC trả về thường: giữ nguyên NSTM, trạng thái dòng và các ĐMH; chỉ đổi phiếu sang Bị trả lại
    kèm `return_mode`. Các ĐMH tự khóa vì `is_po_locked_by_pr_return` đọc cột này."""
    pr = get_pr(db, pid)
    blocker = find_invoice_company_return_blocker(db, pr)
    if blocker:
        raise HTTPException(400, blocker)
    pr.status = "rejected"
    pr.return_mode = int(PrReturnMode.INVOICE_COMPANY)
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "returned",
           f"Trả về sửa công ty nhận hóa đơn. {(reason or '').strip()}".strip())
    db.refresh(pr)
    return pr


def update_invoice_company_only(db: Session, pr: PurchaseRequest, company_id: int | None,
                                user_id: int) -> PurchaseRequest:
    """Lưu phiếu đang trả về sửa công ty: CHỈ nhận `company_id`, mọi trường khác bị bỏ qua.

    Bỏ qua chứ không báo lỗi vì cả hai giao diện gửi nguyên biểu mẫu (kể cả dòng hàng) mỗi lần lưu."""
    from app.modules.company.model import Company
    if company_id is None or int(company_id) == int(pr.company_id or 0):
        return pr
    company = db.get(Company, int(company_id))
    if not company or not company.is_active:
        raise HTTPException(400, "Công ty nhận hóa đơn không tồn tại hoặc đã ngừng dùng")
    old = int(pr.company_id or 0)
    pr.company_id = company.id
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pr.id, "update", f"Đổi công ty nhận hóa đơn: {old} -> {company.id}")
    db.refresh(pr)
    return pr


def apply_invoice_company_approval(db: Session, pr: PurchaseRequest, user_id: int) -> int:
    """Trưởng phòng duyệt phiếu trả về sửa công ty: chép công ty xuống mọi ĐMH còn hiệu lực, mở khóa,
    đưa phiếu về lại mốc đang mua (`recompute_status` tự suy lại từ dòng + mã MISA). Trả số ĐMH đã đổi."""
    from app.modules.product_price.ledger_sync_service import sync_po_price_ledger
    from .line_status_service import recompute_status
    blocker = _find_po_document_blocker(db, pr)
    if blocker:
        raise HTTPException(400, f"{blocker}. Xử lý chứng từ đó trước rồi duyệt lại")
    changed = 0
    changed_pos = []
    for po in _live_pos(db, pr.code):
        if int(po.company_id or 0) == int(pr.company_id or 0):
            continue
        old = int(po.company_id or 0)
        po.company_id = pr.company_id
        po.updated_by = user_id
        changed += 1
        changed_pos.append(po)
        record(db, user_id, "purchase_order", po.id, "update",
               f"Đổi công ty nhận hóa đơn theo YCMH {pr.code}: {old} -> {pr.company_id}", commit=False)
    pr.return_mode = int(PrReturnMode.NONE)
    pr.status = "dispatched"          # mốc gốc của `recompute_status`; hàm tự đẩy lên processing / purchasing
    pr.updated_by = user_id
    recompute_status(db, pr)
    for po in changed_pos:   # dòng sổ giá đang mở chép `company_id` của đơn (duoc-CR-784)
        sync_po_price_ledger(db, po, commit=False)
    db.commit()
    record(db, user_id, ENTITY, pr.id, "approved",
           f"Duyệt đổi công ty nhận hóa đơn — cập nhật {changed} đơn mua hàng")
    db.refresh(pr)
    return changed


def is_po_locked_by_pr_return(db: Session, po) -> bool:
    """ĐMH thuộc một YCMH đang trả về sửa công ty thì khóa mọi thao tác ghi."""
    code = getattr(po, "pr_code", "") or ""
    if not code:
        return False
    return db.query(PurchaseRequest.id).filter(
        PurchaseRequest.code == code, PurchaseRequest.is_deleted.is_(False),
        PurchaseRequest.return_mode == int(PrReturnMode.INVOICE_COMPANY),
        PurchaseRequest.status != "cancelled").first() is not None


PO_LOCKED_MESSAGE = ("Đơn mua hàng đang bị khóa: yêu cầu mua hàng liên quan đã trả về để sửa công ty nhận "
                     "hóa đơn, chờ duyệt lại")


def ensure_po_not_locked(db: Session, po) -> None:
    """Chặn 400 mọi thao tác ghi lên ĐMH đang khóa theo YCMH trả về sửa công ty; `po` None thì bỏ qua."""
    if po is not None and is_po_locked_by_pr_return(db, po):
        raise HTTPException(400, PO_LOCKED_MESSAGE)


def ensure_not_invoice_company_return(pr: PurchaseRequest, action_label: str) -> None:
    """Chặn các thao tác khác trên phiếu đang trả về sửa công ty (xóa, đổi cờ gấp, sửa dòng...)."""
    if is_invoice_company_return(pr):
        raise HTTPException(400, f"Phiếu đang trả về chỉ để sửa công ty nhận hóa đơn — không {action_label} được")
