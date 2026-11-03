"""ĐMH — truy vấn đọc cho controller / serializer, điều khoản in, cắt phiếu YCMH theo đơn (bao-CR-715 tách từ
service.py; phần lớn dời từ controller ở bao-CR-711).
"""
from sqlalchemy.orm import Session

from app.modules.payable.model import Payable
from app.modules.supplier.model import Supplier

from .model import PODelivery, POItem, PurchaseOrder
from .base_service import ENTITY, FILTERABLE, PROG_COMPLETED, normalize_rate


# bao-CR-321 — mặc định của ba điều khoản in trên Đơn đặt hàng (mục 2 và mục 5 của
# "Thoả thuận khác"). Đây là các số từng chốt cứng trong bản in, giữ nguyên để đơn cũ và
# NCC chưa khai in ra y hệt trước.
DEFAULT_INSPECTION_DAYS = 15
DEFAULT_RETURN_DAYS = 7
DEFAULT_INVOICE_DEADLINE = "Chậm nhất 24h kể từ khi nhận hàng"


def resolve_print_terms(po, sup=None) -> dict:
    """Điều khoản in trên đơn: ưu tiên giá trị trên ĐƠN, trống thì lấy của NCC, vẫn trống thì
    mặc định. Ba mức để đơn cũ (chưa có cột) và NCC chưa khai vẫn in đúng như trước.
    `days` trả về dạng chuỗi hai chữ số ("07") vì bản in ghi "trong vòng 07 ngày".
    """
    def _pick(field: str, default):
        for obj in (po, sup):
            v = getattr(obj, field, None) if obj is not None else None
            if isinstance(v, str):
                v = v.strip()
            if v:
                return v
        return default

    inspection = int(_pick("inspection_days", DEFAULT_INSPECTION_DAYS))
    return_ = int(_pick("return_days", DEFAULT_RETURN_DAYS))
    return {
        "inspection_days": inspection,
        "return_days": return_,
        "inspection_days_label": f"{inspection:02d}",
        "return_days_label": f"{return_:02d}",
        "invoice_deadline": str(_pick("invoice_deadline", DEFAULT_INVOICE_DEADLINE)),
    }


def order_amount_map(db: Session, po_ids: list[int]) -> dict[int, float]:
    """Giá trị ĐẶT HÀNG đã quy đổi của NHIỀU đơn, gom MỘT lượt truy vấn. Khóa = id đơn.

    Đúng con số cột *Tiền hàng* ở màn danh sách: số lượng đặt × đơn giá × VAT × tỷ giá,
    cộng hết các dòng của đơn. Tính theo số lượng ĐẶT (không phải số thực nhận) nên cột
    không tụt về 0 khi dòng chuyển sang đã đặt mà chưa nhận hàng; nhân tỷ giá vì đơn ngoại
    tệ đứng chung bảng với đơn trong nước (bao-CR-319, đơn VNĐ có tỷ giá 1 nên số cũ y nguyên).

    Hỏi dòng hàng theo từng đơn là mỗi dòng danh sách một lượt vào cơ sở dữ liệu — đo trên
    97 đơn thật: 97 lượt và 79 ms. Đơn không có dòng hàng nào vẫn có mặt trong kết quả với
    giá trị 0, để người gọi khỏi phải phân biệt "không có dòng" với "thiếu khóa".
    """
    ids = [int(i) for i in po_ids if i]
    if not ids:
        return {}
    result: dict[int, float] = dict.fromkeys(ids, 0.0)
    rows = (db.query(POItem.po_id, POItem.qty_order, POItem.price, POItem.vat,
                     POItem.exchange_rate)
            .filter(POItem.po_id.in_(ids)).all())
    for po_id, qty, price, vat, rate in rows:
        #  Giữ NGUYÊN biểu thức của bản tính từng đơn (kể cả luật đọc tỷ giá trống thành 1);
        #  viết lại gọn hơn là số tiền trôi một cách im lặng.
        result[po_id] = result.get(po_id, 0.0) + (
            float(qty or 0) * float(price or 0) * (1 + float(vat or 0) / 100)
            * normalize_rate(rate))
    return {k: round(v, 2) for k, v in result.items()}


def list_po(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseOrder.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def list_display_names(db: Session, pos) -> dict[int, dict]:
    """bao-CR-705 — tên để HIỂN THỊ cho các cột thêm ở danh sách ĐMH (và tệp Excel cùng màn).

    Mỗi loại tên tra MỘT lượt cho cả trang (không N+1): phòng xử lý (`0` cũ = phòng thu mua mặc
    định, như màn chi tiết bao-CR-524), trưởng phòng phê duyệt, công ty nhận hóa đơn, người tạo.
    Trả `{po_id: {...}}`; thiếu danh mục thì tên rỗng chứ không lỗi.
    """
    from app.core.central_purchasing import get_central_dept_id
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    pos = list(pos or [])
    if not pos:
        return {}
    central = get_central_dept_id(db)
    handler = {p.id: int(p.handler_dept_id or 0) or central for p in pos}

    def names(model, label_col, ids):
        ids = {i for i in ids if i}
        return dict(db.query(model.id, label_col).filter(model.id.in_(ids)).all()) if ids else {}

    dept = names(Department, Department.name, handler.values())
    emp = names(Employee, Employee.full_name, [p.approver_employee_id for p in pos])
    comp = names(Company, Company.name, [p.company_id for p in pos])
    creator_ids = {p.created_by for p in pos if p.created_by}
    creators: dict[int, str] = {}
    if creator_ids:
        rows = (db.query(User.id, User.email, Employee.full_name)
                .outerjoin(Employee, Employee.id == User.employee_id)
                .filter(User.id.in_(creator_ids)).all())
        creators = {uid: (full or email or "") for uid, email, full in rows}
    return {p.id: {
        "handler_dept_id": handler[p.id],
        "handler_dept_name": dept.get(handler[p.id], ""),
        "approver_employee_id": int(p.approver_employee_id or 0),
        "approver_name": emp.get(p.approver_employee_id, ""),
        "company_name": comp.get(p.company_id, ""),
        "created_by_name": creators.get(p.created_by, ""),
        "exchange_rate": float(p.exchange_rate or 1),
    } for p in pos}


def pr_items_for_po(pr_data: dict, po_items) -> dict:
    """Cắt phiếu YCMH (đã serialize) còn ĐÚNG các dòng hàng có trên đơn mua hàng — bao-CR-314.

    Một phiếu YCMH được chia cho nhiều NSTM phụ trách rồi tách thành nhiều đơn, nên bản in
    kèm theo một đơn chỉ được mang phần hàng của đơn đó. Ghép bằng `product_code` vì giữa
    hai bảng dòng KHÔNG có khóa ngoại — cùng cầu nối `pr_expected_map` đang dùng. Mã hàng là
    duy nhất trên YCMH (`assert_unique_product_codes`) nên tra ngược trúng đúng một dòng;
    ĐMH được phép trùng mã (bao-CR-308) thì các dòng trùng cùng chiếu về một dòng nguồn và
    chỉ in một lần.

    Tổng tiền tính LẠI tại đây: `_out` của YCMH cộng từ danh sách dòng chứ không đọc cột lưu
    sẵn, nên cắt dòng mà giữ nguyên tổng là in ra 3 dòng kèm tổng của 10 dòng.

    `po_lines_unmatched` = số dòng trên ĐƠN không đối chiếu được (bỏ trống mã hàng, hoặc mã
    không có trên phiếu). Giao diện báo con số này ở thanh công cụ, KHÔNG in vào tờ giấy —
    người in phải biết bản in thiếu, nhưng tờ phiếu thì giữ nguyên khuôn cũ.
    """
    pr_codes = {(i.get("product_code") or "").strip() for i in pr_data.get("items", [])}
    pr_codes.discard("")
    keep, unmatched = set(), 0
    for it in po_items or []:
        code = (getattr(it, "product_code", "") or "").strip()
        if code and code in pr_codes:
            keep.add(code)
        else:
            unmatched += 1
    items = [i for i in pr_data.get("items", [])
             if (i.get("product_code") or "").strip() in keep]
    subtotal = round(sum(i["qty"] * i["price"] for i in items), 2)   # chưa VAT
    total = round(sum(i["amount"] for i in items), 2)                # gồm VAT
    pr_data["items"] = items
    pr_data["subtotal"] = subtotal
    pr_data["vat"] = round(total - subtotal, 2)
    pr_data["total"] = total
    pr_data["po_lines_unmatched"] = unmatched
    return pr_data


# ═══════════════ Truy vấn dời từ controller (bao-CR-711, không đổi hành vi) ═══════════════
#
# Controller chỉ còn gác quyền + phạm vi rồi gọi xuống đây. Các hàm `query_*` / `build_*`
# trả câu truy vấn CHƯA lọc phạm vi — chỗ gọi phải tự `apply_scope(...)`, đúng action của route.


def query_by_id(db: Session, pid: int):
    """Một ĐMH theo id, CHƯA lọc phạm vi — nền của `_in_scope` và hai cổng đọc ở controller."""
    return db.query(PurchaseOrder).filter(PurchaseOrder.id == pid)


def query_by_ids(db: Session, ids: list[int]):
    """Nhiều ĐMH theo id — nền của xóa hàng loạt (lọc phạm vi `delete` ở controller)."""
    return db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(ids))


def build_list_query(db: Session, request):
    """Bộ lọc màn danh sách ĐMH (CHƯA lọc phạm vi, CHƯA sắp xếp) — dùng chung cho danh sách và
    xuất Excel (CR-068) qua `controller._list_query`."""
    from sqlalchemy import or_, select

    from app.core.base_controller import apply_equals, apply_filters, apply_range_filters
    from app.core.ref_filter import apply_ref_filters

    # `code` chỉ bị loại khỏi lọc TRẦN (nhường cho ô tìm kiếm đa trường), bộ lọc điều kiện
    # `code__contains=...` vẫn phải chạy -> truyền FILTERABLE đầy đủ cho vế operator.
    filterable = [f for f in FILTERABLE if f != "code"]
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, request, filterable,
                      operator_filterable=FILTERABLE)
    q = apply_ref_filters(q, PurchaseOrder, request, db)      # CR-088: `nspt_id` / `department_id`
    q = apply_range_filters(q, PurchaseOrder, request, ["order_date"])
    q = apply_equals(q, PurchaseOrder, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(POItem.po_id).where(POItem.item_group.like(f"%{item_group}%"))
        q = q.filter(PurchaseOrder.id.in_(sub))
    invoice_no = (request.query_params.get("invoice_no") or "").strip()
    if invoice_no:
        sub2_item = select(POItem.po_id).where(POItem.invoice_no.like(f"%{invoice_no}%"))
        sub2_deliv = select(PODelivery.po_id).where(PODelivery.invoice_no.like(f"%{invoice_no}%"))
        q = q.filter(or_(PurchaseOrder.id.in_(sub2_item), PurchaseOrder.id.in_(sub2_deliv)))
    # Ô tìm kiếm nhanh: Tìm theo Mã ĐMH, Mã MISA, Mã PYC, Nhà cung cấp, Mã SP hoặc Tên SP ở dòng hàng
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product") or "").strip()
    if search:
        like = f"%{search}%"
        matching_ids = [
            r[0] for r in db.query(POItem.po_id)
            .filter(or_(POItem.product_code.like(like), POItem.product_name.like(like))).all()
            if r[0]
        ]
        conds = [
            PurchaseOrder.code.like(like),
            PurchaseOrder.pr_code.like(like),
            PurchaseOrder.misa_code.like(like),
            PurchaseOrder.supplier_name.like(like),
            PurchaseOrder.supplier_code.like(like),
        ]
        if matching_ids:
            conds.append(PurchaseOrder.id.in_(matching_ids))
        q = q.filter(or_(*conds))
    return q


def build_line_query(db: Session, request, wh: str):
    """Bộ lọc màn DÒNG HÀNG theo kho (CHƯA lọc phạm vi): `(ĐMH, dòng)`; `wh` = mã kho đang xem —
    lấy dòng có kho nhận mặc định là kho này HOẶC có lần giao về kho này."""
    from sqlalchemy import or_, select

    q = db.query(PurchaseOrder, POItem).join(POItem, POItem.po_id == PurchaseOrder.id)
    if wh:
        by_delivery = select(PODelivery.po_item_id).where(PODelivery.warehouse_code == wh)
        q = q.filter(or_(POItem.warehouse_code == wh, POItem.id.in_(by_delivery)))
    kw = (request.query_params.get("q") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter(or_(PurchaseOrder.code.like(like), POItem.product_code.like(like),
                         POItem.product_name.like(like)))
    progress = (request.query_params.get("progress_status") or "").strip()
    if progress:
        q = q.filter(POItem.progress_status == progress)
    return q


def received_by_warehouse(db: Session, item_ids: list[int], wh: str) -> dict[int, tuple[float, float]]:
    """SL nhận theo lần giao, gom theo dòng: `{id dòng: (nhận tại kho `wh`, nhận đã gắn kho bất kỳ)}`."""
    from sqlalchemy import case, func
    return {
        iid: (float(here or 0), float(assigned or 0)) for iid, here, assigned in
        db.query(
            PODelivery.po_item_id,
            func.sum(case((PODelivery.warehouse_code == wh, PODelivery.received_qty), else_=0)),
            func.sum(case((PODelivery.warehouse_code != "", PODelivery.received_qty), else_=0)),
        ).filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all()
    }


def pr_ids_by_code(db: Session, codes: set) -> dict:
    """`{mã YCMH: id}` cho các mã PYC trên một trang danh sách ĐMH (bấm Mã PYC sang chi tiết)."""
    from app.modules.purchase_request.model import PurchaseRequest
    return {c: i for i, c in db.query(PurchaseRequest.id, PurchaseRequest.code)
            .filter(PurchaseRequest.code.in_(codes)).all()}


def delivery_payables_of(db: Session, po_id: int) -> list:
    """Công nợ theo LẦN GIAO của đơn (hàng + vận chuyển)."""
    return db.query(Payable).filter(Payable.po_id == po_id, Payable.ref_type == "delivery").all()


def invoice_names_by_code(db: Session, codes: set) -> dict:
    """"Tên trên hóa đơn" ở danh mục sản phẩm cho các dòng đang trống — một truy vấn cho cả đơn."""
    if not codes:
        return {}
    from app.modules.product.model import Product
    return {p.code: (p.invoice_name or "")
            for p in db.query(Product).filter(Product.code.in_(codes)).all()}


def latest_approved_actor(db: Session, po_id: int):
    """Dòng nhật ký `approved` GẦN NHẤT của đơn (`(created_by,)` hoặc None) — người ký ô duyệt
    trên bản in. Đơn có thể bị hủy duyệt rồi duyệt lại nên lấy dòng mới nhất."""
    from app.modules.audit.model import AuditLog
    return (db.query(AuditLog.created_by)
            .filter(AuditLog.entity == ENTITY, AuditLog.entity_id == po_id,
                    AuditLog.action == "approved")
            .order_by(AuditLog.id.desc()).first())


def company_by_id(db: Session, company_id: int):
    """Pháp nhân của đơn — tra tên / địa chỉ / MST để in, đơn đã qua cổng phạm vi `print` ở route."""
    from app.modules.company.model import Company
    return db.get(Company, company_id)


def supplier_by_code(db: Session, code: str):
    return db.query(Supplier).filter(Supplier.code == code).first()


def warehouse_by_code(db: Session, code: str):
    from app.modules.catalog.model import Warehouse
    return db.query(Warehouse).filter(Warehouse.code == code).first()


def warehouses_by_codes(db: Session, codes: list[str]) -> list:
    from app.modules.catalog.model import Warehouse
    return db.query(Warehouse).filter(Warehouse.code.in_(codes)).all()


def live_pr_by_code(db: Session, pr_code: str):
    """YCMH nguồn của đơn theo mã PYC, bỏ phiếu đã xóa mềm."""
    from app.modules.purchase_request.model import PurchaseRequest
    return db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code,
                                            PurchaseRequest.is_deleted == False).first()  # noqa: E712


def has_completed_item(db: Session, po_id: int) -> bool:
    """Đơn có dòng đã Hoàn thành chưa — có thì không được hủy đơn."""
    return db.query(POItem).filter(POItem.po_id == po_id,
                                   POItem.progress_status == PROG_COMPLETED).first() is not None


def items_unsorted_of(db: Session, po_id: int) -> list:
    """Mọi dòng của đơn, KHÔNG sắp xếp (đúng câu truy vấn cũ của cổng Hoàn thành đơn)."""
    return db.query(POItem).filter(POItem.po_id == po_id).all()
