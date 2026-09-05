"""Task 7 — Trang "Tiến độ mua hàng".

Nguồn: join tab_purchase_order -> tab_po_item -> tab_po_delivery, hiển thị theo LẦN GIAO.
Quyền: cho phép nếu có `purchase_order.read` HOẶC `purchase_request.read`
(phòng yêu cầu thường chỉ có cái sau).

**Hai quyền RỜI nhau, đừng gộp lại** (bản vá CR-071):
- `purchase_order.read` quyết định PHẠM VI dữ liệu — thấy mọi ĐMH theo scope của mình,
  hay chỉ những ĐMH sinh từ YCMH của phòng mình;
- `supplier.read` quyết định CỘT NCC + khối vận chuyển hiện hay bị che.

Trước đây cả hai cùng đọc `purchase_order.read`, nên vai trò Trưởng phòng (được cấp
`supplier.read` phạm vi "Tất cả" nhưng không có quyền nào trên ĐMH) vẫn bị xóa trắng cột
Nhà cung cấp cả trên bảng lẫn file Excel.

Bản 1: CHỈ dùng cột đã có trong DB. Các cột theo Mapping còn thiếu master
(product.legal_name...) để bản 2 bổ sung migration — xem
`doc/yeu-cau/Mapping_Sheet06_TienDoMuaHang.md`.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.filter_operators import apply_operator_filters_map
from app.core.ref_filter import apply_ref_filters
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

from . import export as ex

router = APIRouter(prefix="/api/purchase-progress", tags=["purchase_progress"])

# Cột nhạy cảm — ẩn với người không có `supplier.read`
_SUPPLIER_HIDDEN = ex.SUPPLIER_HIDDEN_KEYS

# P6-6 (bao-CR-284): màn Tiến độ mua hàng GỘP — mỗi "bước" là một NHÓM mã tiến độ dòng
# (`PO_PROGRESS_STATUS`, app/core/status_codes.py). Bước "Đang so giá" KHÔNG nằm ở đây:
# dữ liệu của nó là dòng YCBG chưa lên đơn, màn gộp gọi `/api/survey-progress?phase=quoting`.
# `paused`/`cancelled` là ngoại lệ ngoài luồng nên chỉ hiện ở "Tất cả".
STEP_STATUS = {
    "purchasing": ("not_ordered", "ordered"),
    "receiving": ("received", "doc_pending", "doc_sent"),
}


def _sort_map():
    """Key cột (FE) -> cột DB thật để sort tại server. Các cột tính toán
    (STT, thành tiền, tên công ty) không có ở đây -> bỏ qua, dùng thứ tự mặc định."""
    return {
        # Đơn mua hàng
        "po_code": PurchaseOrder.code, "misa_code": PurchaseOrder.misa_code,
        "pr_code": PurchaseOrder.pr_code,
        # P6-5 (bao-CR-283): nguồn thứ hai của đơn — phiếu YCBG gộp (đơn LÊN THẲNG,
        # pr_code rỗng). Vào `_sort_map` là tự chảy xuống `_cond_map` (CR-080).
        "survey_code": PurchaseOrder.survey_code,
        "company_id": PurchaseOrder.company_id,
        "department": PurchaseOrder.department, "supplier_code": PurchaseOrder.supplier_code,
        "supplier_name": PurchaseOrder.supplier_name, "nspt": PurchaseOrder.nspt,
        "order_date": PurchaseOrder.order_date, "document_status": PurchaseOrder.document_status,
        # Dòng hàng
        "product_code": POItem.product_code, "product_name": POItem.product_name,
        "invoice_name": POItem.invoice_name, "item_group": POItem.item_group,
        "spec": POItem.spec, "fg_code": POItem.fg_code, "invoice_no": POItem.invoice_no,
        "required_date": POItem.required_date, "unit": POItem.unit,
        # Dự kiến nhận nằm ở DÒNG HÀNG (không ở lần giao) — xem migration e2c5a81f7b60
        "expected_date": POItem.expected_date,
        "qty_request": POItem.qty_request, "qty_order": POItem.qty_order,
        "price": POItem.price, "vat": POItem.vat, "progress_status": POItem.progress_status,
        # Lần giao
        "delivery_no": PODelivery.delivery_no, "warehouse_code": PODelivery.warehouse_code,
        "carrier_code": PODelivery.carrier_code, "carrier_name": PODelivery.carrier_name,
        "ship_qty": PODelivery.ship_qty, "received_qty": PODelivery.received_qty,
        "promised_date": PODelivery.promised_date,
        "received_date": PODelivery.received_date, "std_days": PODelivery.std_days,
        "regulated_date": PODelivery.regulated_date, "diff_promise": PODelivery.diff_promise,
        "diff_regulated": PODelivery.diff_regulated, "diff_required": PODelivery.diff_required,
        "delivery_invoice_no": PODelivery.invoice_no,
        "shipping_unit_price": PODelivery.shipping_unit_price,
        "shipping_amount": PODelivery.shipping_amount, "qc_result": PODelivery.qc_result,
        "delivery_status": PODelivery.status,
    }


def _cond_map(show_supplier: bool) -> dict:
    """CR-080 — whitelist cho BỘ LỌC ĐIỀU KIỆN (`<field>__<op>`).

    Lấy thẳng `_sort_map()`: cột nào sort được tại server thì lọc được, khỏi phải giữ hai danh
    sách lệch nhau. Bỏ `company_id` vì thanh lọc cơ bản đã có ô Công ty (chọn theo tên), gõ số id
    trong bộ lọc điều kiện chẳng ai dùng.

    Người KHÔNG có `supplier.read` thì cột NCC/vận chuyển bị gỡ khỏi map — cột đã bị che trên
    bảng thì cũng không được lọc theo, kẻo lọc rồi đếm số dòng còn lại là mò ra được tên NCC.
    """
    m = {k: v for k, v in _sort_map().items() if k != "company_id"}
    # CR-088: cho lọc theo ID ô tham chiếu. Không nhét vào `_sort_map()` vì sắp xếp theo id là ra
    # thứ tự số, chẳng ai đọc được; đây chỉ mở đường cho `department_id__eq=` / `nspt_id__eq=`.
    # Lối này khớp id THẲNG, không có nhánh lùi — nhánh lùi nằm ở `apply_ref_filters` bên dưới.
    m["department_id"] = PurchaseOrder.department_id
    m["nspt_id"] = PurchaseOrder.nspt_id
    if not show_supplier:
        for k in _SUPPLIER_HIDDEN:
            m.pop(k, None)
    return m


def _require_progress(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Gate OR: purchase_order.read HOẶC purchase_request.read HOẶC survey_request.read.

    Vế thứ ba là P6-5 (bao-CR-283): luồng YCBG gộp không còn YCMH, người yêu cầu chỉ
    có quyền trên phiếu — không mở thì họ ăn 403 dù đơn sinh từ phiếu của chính họ.
    """
    if (user_has_permission(db, user, "purchase_order", "read")
            or user_has_permission(db, user, "purchase_request", "read")
            or user_has_permission(db, user, "survey_request", "read")):
        return user
    raise HTTPException(403, "Không có quyền xem tiến độ mua hàng")


# Một hàng của bảng = đơn + dòng hàng + lần giao. Thân hàm nằm ở `export.row_values` vì file xuất
# của màn Đơn mua hàng cũng dùng lại (CR-068) — giữ một chỗ tính tiền/chênh lệch cho cả ba nơi.
_row = ex.row_values


def _po_scope(db: Session, user) -> bool:
    """Có `purchase_order.read` = đi theo phạm vi ĐMH của mình; không có = chỉ ĐMH sinh từ YCMH."""
    return user_has_permission(db, user, "purchase_order", "read")


def _show_supplier(db: Session, user) -> bool:
    """Cột NCC + khối vận chuyển đi theo quyền `supplier.read`, KHÔNG theo quyền ĐMH."""
    return user_has_permission(db, user, "supplier", "read")


def _build_query(request: Request, db: Session, user, prof: dict, po_scope: bool,
                 show_supplier: bool = False):
    """Bộ lọc + phạm vi + sắp xếp của màn Tiến độ — dùng chung cho danh sách và xuất Excel (CR-068),
    để file xuất luôn khớp đúng những gì đang bày trên bảng."""
    q = (db.query(PurchaseOrder, POItem, PODelivery)
         .join(POItem, POItem.po_id == PurchaseOrder.id)
         .outerjoin(PODelivery, PODelivery.po_item_id == POItem.id))

    # ----- Filter -----
    company_id = (request.query_params.get("company_id") or "").strip()
    if company_id.isdigit():
        q = q.filter(PurchaseOrder.company_id == int(company_id))
    # CR-088: ô Bộ phận lọc theo ID (`department_id=`), kèm nhánh lùi cho ĐMH chưa điền lùi được id.
    # Vẫn nhận `department=<tên>` cho giao diện cũ và các đường dẫn đã lưu sẵn.
    q = apply_ref_filters(q, PurchaseOrder, request, db)
    department = (request.query_params.get("department") or "").strip()
    if department:
        q = q.filter(PurchaseOrder.department == department)
    month = (request.query_params.get("month") or "").strip()   # YYYY-MM theo ngày đặt hàng
    if month:
        q = q.filter(PurchaseOrder.order_date.like(f"{month}%"))
    status = (request.query_params.get("status") or "").strip()  # theo tiến độ dòng
    if status:
        q = q.filter(POItem.progress_status == status)
    # P6-6 (bao-CR-284): lọc theo BƯỚC (đang mua / đang nhận hàng). Giá trị lạ bỏ qua —
    # người dùng sửa tay URL thì coi như không lọc, hơn là bảng rỗng khó hiểu.
    step = (request.query_params.get("step") or "").strip()
    if step in STEP_STATUS:
        q = q.filter(POItem.progress_status.in_(STEP_STATUS[step]))
    # Khoảng NGÀY ĐẶT HÀNG (chuỗi YYYY-MM-DD so sánh vẫn đúng thứ tự)
    od_from = (request.query_params.get("order_date_from") or "").strip()
    od_to = (request.query_params.get("order_date_to") or "").strip()
    if od_from:
        q = q.filter(PurchaseOrder.order_date != "", PurchaseOrder.order_date >= od_from)
    if od_to:
        q = q.filter(PurchaseOrder.order_date != "", PurchaseOrder.order_date <= od_to)
    # Khoảng NGÀY NHẬN thực tế của lần giao
    rd_from = (request.query_params.get("received_date_from") or "").strip()
    rd_to = (request.query_params.get("received_date_to") or "").strip()
    if rd_from:
        q = q.filter(PODelivery.received_date != "", PODelivery.received_date >= rd_from)
    if rd_to:
        q = q.filter(PODelivery.received_date != "", PODelivery.received_date <= rd_to)
    kw = (request.query_params.get("q") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter((PurchaseOrder.code.like(like))
                     | (PurchaseOrder.misa_code.like(like))
                     | (PurchaseOrder.pr_code.like(like))
                     | (PurchaseOrder.survey_code.like(like))
                     | (PurchaseOrder.supplier_name.like(like))
                     | (PurchaseOrder.supplier_code.like(like))
                     | (PurchaseOrder.department.like(like))
                     | (PurchaseOrder.nspt.like(like))
                     | (POItem.product_code.like(like))
                     | (POItem.product_name.like(like))
                     | (POItem.item_group.like(like))
                     # `POItem` KHÔNG có cột nspt (NSPT nằm trên đơn, đã tìm ở trên) —
                     # vế `POItem.nspt` cũ làm MỌI tìm kiếm q= của màn này ăn 500,
                     # phát hiện khi viết test P6-5 (bao-CR-283).
                     | (PODelivery.progress_note.like(like)))

    # ----- Bộ lọc điều kiện (CR-080) -----
    # Các ô lọc cố định phía trên chỉ còn Công ty / Tìm kiếm / Trạng thái tiến độ / Tình trạng
    # nhận; mọi cột còn lại (bộ phận, NSPT, ngày đặt, ngày nhận, số lượng, tiền…) lọc qua đây với
    # đủ phép so sánh. Param cũ của thanh lọc (month, order_date_from/_to…) vẫn được đọc ở trên
    # để link cũ không chết, chỉ là FE không còn ô nhập cho chúng.
    q = apply_operator_filters_map(q, _cond_map(show_supplier), request)

    # ----- Lọc theo SỐ LƯỢNG NHẬN (tổng đã nhận trên MỌI lần giao của dòng hàng) -----
    # Mục đích: sáng lọc nhanh đơn "chưa giao" / "giao thiếu" để hối thúc NCC.
    # Dùng tổng theo DÒNG (không theo từng lần giao) để không đếm sót khi có nhiều lần giao.
    recv_sum = (db.query(func.coalesce(func.sum(PODelivery.received_qty), 0))
                .filter(PODelivery.po_item_id == POItem.id)
                .correlate(POItem).scalar_subquery())
    recv_state = (request.query_params.get("recv_state") or "").strip()
    if recv_state == "unreceived":       # Chưa giao: đã đặt nhưng chưa nhận gì
        q = q.filter(POItem.qty_order > 0, recv_sum == 0)
    elif recv_state == "under":          # Chưa đủ: nhận < đặt (gồm cả chưa giao)
        q = q.filter(POItem.qty_order > 0, recv_sum < POItem.qty_order)
    elif recv_state == "full":           # Đã đủ: nhận >= đặt
        q = q.filter(POItem.qty_order > 0, recv_sum >= POItem.qty_order)

    def _num(s):
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    rmin = _num(request.query_params.get("recv_min"))
    rmax = _num(request.query_params.get("recv_max"))
    if rmin is not None:
        q = q.filter(recv_sum >= rmin)
    if rmax is not None:
        q = q.filter(recv_sum <= rmax)

    # ----- Phạm vi dữ liệu -----
    if po_scope:
        q = apply_scope(q, PurchaseOrder, "purchase_order", user, prof)
    else:
        # Không có `purchase_order.read` → chỉ thấy ĐMH LIÊN KẾT với chứng từ nguồn
        # trong phạm vi của mình. P6-5 (bao-CR-283): nguồn nay là HAI — YCMH cũ qua
        # `pr_code` VÀ phiếu YCBG gộp qua `survey_code` (đơn lên thẳng, pr_code rỗng).
        # HỢP hai vế theo nguồn, còn "của ai" vẫn do apply_scope từng entity quyết —
        # nới nguồn không được nới người.
        from app.modules.purchase_request.model import PurchaseRequest
        from app.modules.survey_request.model import SurveyRequest
        pr_q = apply_scope(db.query(PurchaseRequest.code), PurchaseRequest,
                           "purchase_request", user, prof)
        pr_codes = [c for (c,) in pr_q.all() if c]
        sr_q = apply_scope(db.query(SurveyRequest.code), SurveyRequest,
                           "survey_request", user, prof)
        sr_codes = [c for (c,) in sr_q.all() if c]
        conds = []
        if pr_codes:
            conds.append(PurchaseOrder.pr_code.in_(pr_codes))
        if sr_codes:
            conds.append(PurchaseOrder.survey_code.in_(sr_codes))
        if conds:
            cond = conds[0]
            for extra in conds[1:]:
                cond = cond | extra
            q = q.filter(cond)
        else:
            q = q.filter(PurchaseOrder.id == -1)

    # ----- Sort -----
    # Cột do người dùng chọn (nếu là cột thật) đứng trước, thứ tự mặc định làm tiebreak
    sort_by = (request.query_params.get("sort_by") or "").strip()
    sort_dir = (request.query_params.get("sort_dir") or "asc").strip().lower()
    col = _sort_map().get(sort_by)
    if col is not None:
        q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    return q.order_by(PurchaseOrder.code, POItem.id, PODelivery.delivery_no)


@router.get("")
def list_progress(request: Request, pg: dict = Depends(pagination),
                  db: Session = Depends(get_db), user=Depends(_require_progress)):
    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    q = _build_query(request, db, user, prof, _po_scope(db, user), show_supplier)
    total = q.count()
    rows = q.offset(pg["offset"]).limit(pg["limit"]).all()
    # STT liên tục theo trang
    base = pg["offset"]
    out = [{"stt": base + i + 1, **_row(po, it, dl, show_supplier)}
           for i, (po, it, dl) in enumerate(rows)]
    return success({"total": total, "items": out, "show_supplier": show_supplier})


def _require_progress_export(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Gate OR cho việc XUẤT: `export` trên ĐMH / YCMH / YCBG — cùng lối gộp quyền của trang
    (vế YCBG là P6-5, bao-CR-283)."""
    if (user_has_permission(db, user, "purchase_order", "export")
            or user_has_permission(db, user, "purchase_request", "export")
            or user_has_permission(db, user, "survey_request", "export")):
        return user
    raise HTTPException(403, "Không có quyền xuất dữ liệu tiến độ mua hàng")


@router.get("/export/xlsx")
def export_xlsx(request: Request, cols: str = "", db: Session = Depends(get_db),
                user=Depends(_require_progress_export)):
    """CR-068 — xuất Excel màn Tiến độ mua hàng theo đúng bộ lọc + cột đang hiện.

    Không có tham số `ids`: bảng này không cho tick chọn từng dòng, người dùng lọc rồi xuất.
    """
    from app.core.export_xlsx import check_row_limit, pick_columns, xlsx_response
    from app.modules.company.model import Company
    from . import export as ex

    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    q = _build_query(request, db, user, prof, _po_scope(db, user), show_supplier)
    check_row_limit(q.count())
    company_name = {c.id: c.name for c in db.query(Company).all()}
    rows = []
    for i, (po, it, dl) in enumerate(q.all(), start=1):
        r = _row(po, it, dl, show_supplier)
        r["stt"] = i
        r["company"] = company_name.get(po.company_id, "")
        rows.append(ex.translate_codes(r))   # B-06: cột trạng thái lưu MÃ, file xuất hiện chữ
    columns = pick_columns(ex.columns_for(show_supplier), cols)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)
