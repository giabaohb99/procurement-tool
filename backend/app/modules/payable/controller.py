from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .model import Payable

router = APIRouter(prefix="/api/payables", tags=["payable"])


def _out(db: Session, p: Payable) -> dict:
    return {
        "id": p.id, "company_id": p.company_id, "supplier_code": p.supplier_code,
        "supplier_name": p.supplier_name, "source_type": p.source_type,
        "po_id": p.po_id, "po_code": p.po_code, "invoice_no": p.invoice_no,
        "invoice_date": service.get_invoice_date(db, p),
        "incur_date": p.incur_date, "due_date": p.due_date, "created_at": p.created_at,
        "amount": float(p.amount or 0), "vat": float(p.vat or 0), "total": float(p.total or 0),
        "paid_amount": float(p.paid_amount or 0), "remaining": float(p.remaining or 0),
        # `status` là MÃ (`unpaid | partial | paid`, B-05); `status_label` là chữ để hiện.
        # Giao diện đừng tự dịch mã sang tiếng Việt — dùng nhãn gửi kèm.
        "status": p.status, "status_label": service.status_label(p.status),
        "aging": service.aging_bucket(p.due_date),
    }


def _today():
    return datetime.now().date()


def _filtered(db: Session, request: Request, user):
    """Lọc ở DB (không nạp toàn bộ). Mặc định theo năm hiện tại để giới hạn dữ liệu."""
    q = apply_filters(db.query(Payable), Payable, request, service.FILTERABLE)
    q = apply_scope(q, Payable, "payable", user, get_perm_profile(db, user))
    company_id = request.query_params.get("company_id")
    if company_id:
        q = q.filter(Payable.company_id == int(company_id))
    # CR-025: lấy đúng các khoản đã tick (màn "Tạo yêu cầu thanh toán" mở lại sau F5).
    # Có `ids` thì bỏ luôn giới hạn theo năm — khoản được tick có thể là nợ năm trước.
    ids = request.query_params.get("ids")
    if ids:
        id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
        q = q.filter(Payable.id.in_(id_list or [-1]))
    year = request.query_params.get("year")
    if year is None:
        year = "all" if ids else str(_today().year)
    if year and year != "all":
        q = q.filter(Payable.period == year)

    # Khoảng ngày phát sinh (từ - đến)
    incur_from = request.query_params.get("incur_from")
    if incur_from:
        q = q.filter(Payable.incur_date != "", Payable.incur_date >= incur_from)
    incur_to = request.query_params.get("incur_to")
    if incur_to:
        q = q.filter(Payable.incur_date != "", Payable.incur_date <= incur_to)
    # Khoảng HẠN TRẢ (từ - đến) — câu hỏi thường gặp nhất của kế toán: "kỳ này
    # phải trả NCC nào, bao nhiêu". `due_date` rỗng (chưa có hạn) bị loại khỏi
    # khoảng, giống cách `incur_date` xử ở trên: so chuỗi rỗng với ngày thì "" bé
    # hơn mọi ngày, không chặn thì mọi khoản chưa có hạn đều lọt vào "từ ngày".
    due_from = request.query_params.get("due_from")
    if due_from:
        q = q.filter(Payable.due_date != "", Payable.due_date >= due_from)
    due_to = request.query_params.get("due_to")
    if due_to:
        q = q.filter(Payable.due_date != "", Payable.due_date <= due_to)
    # Khoảng số tiền theo TỔNG NỢ (từ A - đến B)
    for key, op in (("amount_from", "ge"), ("amount_to", "le")):
        val = request.query_params.get(key)
        if val:
            try:
                v = float(val)
                q = q.filter(Payable.total >= v if op == "ge" else Payable.total <= v)
            except ValueError:
                pass

    aging = request.query_params.get("aging")
    if aging:
        t = _today()
        def s(days): return (t - timedelta(days=days)).strftime("%Y-%m-%d")
        today = t.strftime("%Y-%m-%d")
        if aging == "Chưa đến hạn":
            q = q.filter((Payable.due_date == "") | (Payable.due_date >= today))
        elif aging == "1-30":
            q = q.filter(Payable.due_date >= s(30), Payable.due_date <= s(1))
        elif aging == "31-60":
            q = q.filter(Payable.due_date >= s(60), Payable.due_date <= s(31))
        elif aging == "61-90":
            q = q.filter(Payable.due_date >= s(90), Payable.due_date <= s(61))
        elif aging == ">90":
            q = q.filter(Payable.due_date != "", Payable.due_date <= s(91))
    return q


@router.get("")
def list_payables(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("payable", "read"))):
    q = _filtered(db, request, user)
    total = q.count()
    rows = (q.order_by(Payable.due_date.asc(), Payable.id.desc())
            .offset(pg["offset"]).limit(pg["limit"]).all())
    return success({"total": total, "items": [_out(db, p) for p in rows]})


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user=Depends(require("payable", "read"))):
    today = _today().strftime("%Y-%m-%d")
    q = _filtered(db, request, user)
    overdue_case = case(
        (((Payable.status != service.ST_PAID) & (Payable.due_date != "") & (Payable.due_date < today)), Payable.remaining),
        else_=0,
    )
    row = q.with_entities(
        func.coalesce(func.sum(Payable.total), 0),
        func.coalesce(func.sum(Payable.paid_amount), 0),
        func.coalesce(func.sum(Payable.remaining), 0),
        func.coalesce(func.sum(overdue_case), 0),
    ).one()
    return success({"total": float(row[0]), "paid": float(row[1]),
                    "remaining": float(row[2]), "overdue": float(row[3])})


@router.post("/{pid}/offset-prepay")
def offset_prepay_(pid: int, data: dict, db: Session = Depends(get_db),
                   user=Depends(require("payable", "write"))):
    """CR-268 — kế toán cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước không gắn đơn)
    vào khoản công nợ này. Body: {amount} — bỏ trống/0 nghĩa là trừ tối đa
    min(treo còn lại, nợ còn lại). Treo GẮN ĐƠN thì hệ thống đã tự trừ lúc nhận
    hàng, không đi qua nút này."""
    from fastapi import HTTPException
    p = apply_scope(db.query(Payable).filter(Payable.id == pid),
                    Payable, "payable", user, get_perm_profile(db, user)).first()
    if not p:
        raise HTTPException(403, "Ngoài phạm vi được phép thao tác")
    from app.modules.payment_request import service as prq_service
    taken = prq_service.offset_supplier_hanging(db, p, float(data.get("amount") or 0), user.id)
    return success(_out(db, p), f"Đã cấn trừ {taken:,.0f} đ tiền treo vào khoản nợ")


@router.get("/export/xlsx")
def export_xlsx(request: Request, cols: str = "", db: Session = Depends(get_db),
                user=Depends(require("payable", "export"))):
    """Ticket #16 — xuất Excel danh sách Công nợ đúng bộ lọc + phạm vi màn hình.

    Tham số `ids` (khoản người dùng tick chọn) đã được `_filtered` xử lý sẵn — có `ids`
    thì chỉ xuất các khoản đó và bỏ giới hạn theo năm, rỗng thì theo bộ lọc đang đặt.
    `cols` = các cột đang hiện trên bảng, xuất đúng thứ tự người dùng thấy.
    """
    from app.core.export_xlsx import check_row_limit, pick_columns, xlsx_response

    from . import export as ex

    q = _filtered(db, request, user)
    items = q.order_by(Payable.due_date.asc(), Payable.id.desc()).all()
    check_row_limit(len(items))
    columns = pick_columns(ex.COLS, cols)
    return xlsx_response(ex.FILE_NAME, columns, ex.build_rows(db, items), ex.SHEET_TITLE)
