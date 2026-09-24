"""Công nợ: sinh ngầm khi nhận hàng (2 luồng goods/shipping) + tính lại trạng thái trả."""
import re
from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.status_codes import PAYABLE_STATUS

from .model import Payable

FILTERABLE = ["supplier_code", "po_code", "invoice_no", "source_type", "status"]

# Ba giá trị của `Payable.status` (B-05). Đặt tên ở đây vì NĂM chỗ ngoài phân hệ này so sánh
# với `paid` để loại nợ đã tất toán — cảnh báo, hai khối Trang chủ, thẻ tổng hợp công nợ và
# báo cáo mua hàng. Gõ thẳng chuỗi ở từng chỗ là lần sau đổi mã sẽ sót đúng một chỗ, mà chỗ
# sót đó im lặng trả ra số tiền sai chứ không nổ.
ST_UNPAID = "unpaid"
ST_PARTIAL = "partial"
ST_PAID = "paid"


def debt_days(payment_terms: str) -> int:
    """Suy ra số ngày công nợ từ hình thức thanh toán của NCC (vd 'Công nợ 30 ngày')."""
    m = re.search(r"(\d+)\s*ng[aà]y", payment_terms or "", re.IGNORECASE)
    return int(m.group(1)) if m else 0


def invoice_date_map(db: Session, items: list[Payable]) -> dict[int, str]:
    """Ngày hóa đơn của NHIỀU khoản nợ, HAI lượt truy vấn. Khóa = id khoản nợ.

    Ngày hóa đơn không có cột trên `tab_payable`: phải dò dọc chuỗi chứng từ, đợt
    giao hàng trước rồi mới tới dòng hàng. Hỏi theo từng khoản nợ là mỗi dòng danh
    sách tới hai lượt vào cơ sở dữ liệu — đo trên 192 khoản nợ thật: 346 lượt và
    238 ms, gom lại còn 2 lượt.

    Đây là bản Python DUY NHẤT của luật dò ngày; `get_invoice_date` chỉ là lối vào
    cho một khoản. Vẫn còn bản SQL `invoice_date_expr()` dùng để lọc và sắp xếp —
    **sửa luật thì phải sửa CẢ HAI**, xem chú thích của hàm đó.
    """
    from app.modules.purchase_order.model import PODelivery, POItem

    rows = [p for p in items if p is not None]
    if not rows:
        return {}
    result: dict[int, str] = {}
    #  Chỉ khoản nợ sinh từ một đợt giao mới có đường dò; khoản khác rơi thẳng xuống
    #  nhánh lùi ở dưới.
    ref_ids = {p.ref_id for p in rows if p.ref_type == "delivery" and p.ref_id}
    deliveries: dict[int, tuple[str, int]] = {}
    if ref_ids:
        deliveries = {
            did: ((inv or "").strip(), int(item_id or 0))
            for did, inv, item_id in db.query(PODelivery.id, PODelivery.invoice_date,
                                              PODelivery.po_item_id)
            .filter(PODelivery.id.in_(ref_ids)).all()
        }
    #  Chỉ hỏi dòng hàng của những đợt giao KHÔNG tự khai ngày — đợt đã khai thì
    #  không đi tiếp, y như bản dò từng khoản.
    item_ids = {iid for inv, iid in deliveries.values() if not inv and iid}
    item_dates: dict[int, str] = {}
    if item_ids:
        item_dates = {
            iid: (inv or "").strip()
            for iid, inv in db.query(POItem.id, POItem.invoice_date)
            .filter(POItem.id.in_(item_ids)).all()
        }
    for p in rows:
        found = ""
        if p.ref_type == "delivery" and p.ref_id and p.ref_id in deliveries:
            inv, item_id = deliveries[p.ref_id]
            found = inv or (item_dates.get(item_id, "") if item_id else "")
        if not found and (p.invoice_no or "").strip() and (p.incur_date or "").strip():
            found = p.incur_date
        result[p.id] = found
    return result


def get_invoice_date(db: Session, p: Payable) -> str:
    """Ngày hóa đơn của MỘT khoản nợ.

    ⚠️ **Cho một khoản thôi.** Cần cả một trang thì gọi `invoice_date_map` — đặt hàm
    này vào vòng lặp là mỗi dòng danh sách tới hai lượt vào cơ sở dữ liệu.
    """
    return invoice_date_map(db, [p]).get(getattr(p, "id", 0), "") if p else ""


def join_invoice_date(q):
    """Gắn sẵn hai outer-join mà `invoice_date_expr()` cần vào một query trên Payable.

    Cả hai đều 1-1 (`ref_id` trỏ đúng một đợt giao, `po_item_id` trỏ đúng một dòng) nên
    KHÔNG nhân dòng — gọi trước `count`/`sum`/`group_by` vẫn ra đúng số.
    """
    from app.modules.purchase_order.model import PODelivery, POItem

    return (q.outerjoin(PODelivery,
                        (Payable.ref_type == "delivery") & (Payable.ref_id == PODelivery.id))
             .outerjoin(POItem, POItem.id == PODelivery.po_item_id))


def invoice_date_expr():
    """Bản SQL của `invoice_date_map` — dùng để LỌC/SẮP ngay trong câu truy vấn.

    Ngày hóa đơn không có cột trên `tab_payable`, phải dò dọc chuỗi chứng từ, nên tồn tại
    hai bản: bản Python dựng dữ liệu (`invoice_date_map`) và bản SQL này. **Sửa luật thì
    phải sửa CẢ HAI** — lệch nhau là màn hình hiện một ngày còn bộ lọc hiểu một ngày khác,
    đúng kiểu lỗi bao-CR-305 vừa phải vá. Phải `join_invoice_date(q)` trước khi dùng.
    """
    from app.modules.purchase_order.model import PODelivery, POItem

    return func.coalesce(
        func.nullif(PODelivery.invoice_date, ""),
        func.nullif(POItem.invoice_date, ""),
        case((Payable.invoice_no != "", func.nullif(Payable.incur_date, "")), else_=None),
    )


def misa_code_by_po(db: Session, items: list[Payable]) -> dict[int, str]:
    """Ticket #18 — map po_id -> mã MISA của ĐMH, gom một truy vấn cho cả trang (tránh N+1).

    Payable không lưu misa_code (nhập/sửa trên ĐMH sau khi nợ đã sinh) nên phải join lúc đọc.
    """
    from app.modules.purchase_order.model import PurchaseOrder

    po_ids = {p.po_id for p in items if p.po_id}
    if not po_ids:
        return {}
    rows = db.query(PurchaseOrder.id, PurchaseOrder.misa_code).filter(
        PurchaseOrder.id.in_(po_ids)).all()
    return {pid: (code or "") for pid, code in rows}


def calc_due(incur_date: str, days: int) -> str:
    if not incur_date:
        incur_date = datetime.now().strftime("%Y-%m-%d")
    try:
        d = datetime.strptime(incur_date, "%Y-%m-%d")
    except ValueError:
        return incur_date
    return (d + timedelta(days=days or 0)).strftime("%Y-%m-%d")


def recalc_status(p: Payable):
    """Tính lại trạng thái + số còn lại từ hai con số tiền. Gọi sau MỖI lần phân bổ thanh toán.

    Trạng thái ở đây là HÀM của (paid, total), không phải máy trạng thái: sửa `total` của một
    khoản đã tất toán là nó tự lùi về `partial`. Vì vậy `paid` không phải trạng thái kết.
    """
    paid = float(p.paid_amount or 0)
    total = float(p.total or 0)
    p.remaining = round(total - paid, 2)   # tính sẵn, không sum lúc đọc
    if paid <= 0:
        p.status = ST_UNPAID
    elif paid + 0.01 < total:
        p.status = ST_PARTIAL
    else:
        p.status = ST_PAID


def status_label(v: str) -> str:
    """Nhãn tiếng Việt của mã trạng thái. Mã lạ thì trả về chính nó, không nuốt mất."""
    return PAYABLE_STATUS.label_of(v) or (v or "")


def upsert(db: Session, *, source_type: str, ref_id: int, company_id: int, supplier_code: str,
           supplier_name: str, po_id: int, po_code: str, invoice_no: str, incur_date: str,
           amount: float, vat: float, due_days: int, user_id: int,
           ref_type: str = "delivery", due_date: str = "", department_id: int = 0):
    """Tạo/cập nhật 1 khoản nợ (idempotent theo source_type + ref_type + ref_id).

    `ref_type = "delivery"` (mặc định): `ref_id` là id lần giao — hai luồng goods/shipping.
    `ref_type = "import_cost"` (bao-CR-319 P5): `ref_id` là id dòng chi phí thu mua (`tab_po_cost`).
    `due_date` có giá trị thì dùng thẳng (dòng chi phí có ô *Hạn thanh toán* riêng),
    rỗng thì tính từ ngày phát sinh + số ngày công nợ của NCC như trước.
    `department_id` (bao-CR-414 GĐ4): phòng đang xử lý đơn — người gọi tính sẵn bằng
    `handling_dept_of(po)`; cập nhật lại mỗi lần lưu đơn để đổi phòng xử lý là nợ đi theo.
    """
    p = db.query(Payable).filter(
        Payable.source_type == source_type, Payable.ref_type == ref_type, Payable.ref_id == ref_id
    ).first()
    if not p:
        p = Payable(source_type=source_type, ref_type=ref_type, ref_id=ref_id, created_by=user_id)
        db.add(p)
    p.company_id = company_id
    p.department_id = int(department_id or 0)
    p.supplier_code = supplier_code
    p.supplier_name = supplier_name
    p.po_id = po_id
    p.po_code = po_code
    p.invoice_no = invoice_no
    p.incur_date = incur_date
    p.period = (incur_date or "")[:4]
    p.due_date = (due_date or "").strip() or calc_due(incur_date, due_days)
    p.amount = round(amount, 2)
    p.vat = round(vat, 2)
    p.total = round(amount + vat, 2)
    p.updated_by = user_id
    recalc_status(p)
    db.flush()
    return p


def remove(db: Session, source_type: str, ref_id: int, ref_type: str = "delivery"):
    p = db.query(Payable).filter(
        Payable.source_type == source_type, Payable.ref_type == ref_type, Payable.ref_id == ref_id
    ).first()
    if p:
        db.delete(p)
        db.flush()


def aging_bucket(due_date: str) -> str:
    if not due_date:
        return "Chưa đến hạn"
    try:
        d = datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return "Chưa đến hạn"
    overdue = (datetime.now().date() - d).days
    if overdue <= 0:
        return "Chưa đến hạn"
    if overdue <= 30:
        return "1-30"
    if overdue <= 60:
        return "31-60"
    if overdue <= 90:
        return "61-90"
    return ">90"
