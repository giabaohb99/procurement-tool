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
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.base_controller import pagination, read_multi_param
from app.core.database import get_db
from app.core.filter_operators import apply_operator_filters_map
from app.core.ref_filter import apply_ref_filters
from app.core.report_aggregate import build_report
from app.core.report_export import report_xlsx
from app.core.report_period import parse_period
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

from . import export as ex
from . import summary_service as prog_summary

router = APIRouter(prefix="/api/purchase-progress", tags=["purchase_progress"])

# Cột nhạy cảm — ẩn với người không có `supplier.read`
_SUPPLIER_HIDDEN = ex.SUPPLIER_HIDDEN_KEYS


def _search_columns():
    """Các cột ô TÌM KIẾM (`q=`) quét qua — khai thành danh sách chứ không viết thẳng vào
    câu lọc, để bài kiểm đối chiếu được với model thật.

    bao-CR-404: bản cũ viết chuỗi `|` ngay trong `_build_query` và có lẫn `POItem.nspt` —
    một cột KHÔNG tồn tại (NSPT chỉ nằm trên đơn). Mọi lượt gõ vào ô tìm kiếm ném
    AttributeError -> 500, mà giao diện v1 không tự báo lỗi cho request GET nên màn hình
    chỉ đứng im với bảng cũ. Lỗi sống lâu vì không có chỗ nào đối chiếu."""
    return (
        # Đơn mua hàng
        PurchaseOrder.code, PurchaseOrder.misa_code, PurchaseOrder.pr_code,
        PurchaseOrder.supplier_name, PurchaseOrder.supplier_code,
        PurchaseOrder.department, PurchaseOrder.nspt,
        # Dòng hàng
        POItem.product_code, POItem.product_name, POItem.item_group,
        # Lần giao
        PODelivery.progress_note,
    )


def build_warehouse_code_col():
    """Cột Kho của MỘT HÀNG trên bảng — giống hệt luật lùi ở `export.row_values`.

    bao-CR-411: ô Kho hiện kho của lần giao, thiếu thì lùi về kho mặc định của dòng hàng.
    Sắp xếp và lọc điều kiện phải chạy trên CÙNG biểu thức đó; trỏ thẳng vào
    `PODelivery.warehouse_code` thì 78 hàng chưa có lần giao bày ra mã kho nhưng lọc theo
    mã đó lại không ra chúng — lệch âm thầm, không chỗ nào báo lỗi.
    """
    return func.coalesce(func.nullif(PODelivery.warehouse_code, ""), POItem.warehouse_code, "")


def _sort_map():
    """Key cột (FE) -> cột DB thật để sort tại server. Các cột tính toán
    (STT, thành tiền, tên công ty) không có ở đây -> bỏ qua, dùng thứ tự mặc định."""
    return {
        # Đơn mua hàng
        "po_code": PurchaseOrder.code, "misa_code": PurchaseOrder.misa_code,
        "pr_code": PurchaseOrder.pr_code, "company_id": PurchaseOrder.company_id,
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
        # bao-CR-439: hai cột căn cứ quy đổi nay có mặt trên bảng, nên phải sắp xếp và lọc điều
        # kiện được như mọi cột khác — "lọc ra dòng khác VND" là câu hỏi đầu tiên của kế toán.
        "currency": POItem.currency, "exchange_rate": POItem.exchange_rate,
        # bao-CR-409 (ticket prod 51): ngày giao chứng từ cho kế toán — dữ liệu vốn đã trả về
        # trong hàng nhưng không nằm ở đây nên không sắp xếp cũng không lọc điều kiện được
        "document_delivery_date": POItem.document_delivery_date,
        # Lần giao
        "delivery_no": PODelivery.delivery_no,
        # bao-CR-411: KHÔNG phải cột thuần của lần giao nữa — xem `build_warehouse_code_col`
        "warehouse_code": build_warehouse_code_col(),
        "carrier_code": PODelivery.carrier_code, "carrier_name": PODelivery.carrier_name,
        "ship_qty": PODelivery.ship_qty, "received_qty": PODelivery.received_qty,
        "promised_date": PODelivery.promised_date,
        "received_date": PODelivery.received_date, "std_days": PODelivery.std_days,
        "regulated_date": PODelivery.regulated_date, "diff_promise": PODelivery.diff_promise,
        "diff_regulated": PODelivery.diff_regulated, "diff_required": PODelivery.diff_required,
        "delivery_invoice_no": PODelivery.invoice_no,
        "delivery_invoice_date": PODelivery.invoice_date,
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
    """Gate OR: purchase_order.read HOẶC purchase_request.read."""
    if (user_has_permission(db, user, "purchase_order", "read")
            or user_has_permission(db, user, "purchase_request", "read")):
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
    # bao-CR-423: ô Công ty và ô Trạng thái tiến độ CHỌN ĐƯỢC NHIỀU giá trị. Nhận cả
    # `company_id=1,2` lẫn `company_id=1&company_id=2`; một giá trị thì lọc `==` như cũ.
    company_ids = [int(v) for v in read_multi_param(request, "company_id") if v.isdigit()]
    if len(company_ids) == 1:
        q = q.filter(PurchaseOrder.company_id == company_ids[0])
    elif company_ids:
        q = q.filter(PurchaseOrder.company_id.in_(company_ids))
    # CR-088: ô Bộ phận lọc theo ID (`department_id=`), kèm nhánh lùi cho ĐMH chưa điền lùi được id.
    # Vẫn nhận `department=<tên>` cho giao diện cũ và các đường dẫn đã lưu sẵn.
    q = apply_ref_filters(q, PurchaseOrder, request, db)
    department = (request.query_params.get("department") or "").strip()
    if department:
        q = q.filter(PurchaseOrder.department == department)
    month = (request.query_params.get("month") or "").strip()   # YYYY-MM theo ngày đặt hàng
    if month:
        q = q.filter(PurchaseOrder.order_date.like(f"{month}%"))
    statuses = read_multi_param(request, "status")  # theo tiến độ dòng, chọn được nhiều
    if len(statuses) == 1:
        q = q.filter(POItem.progress_status == statuses[0])
    elif statuses:
        q = q.filter(POItem.progress_status.in_(statuses))
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
        q = q.filter(or_(*[c.like(like) for c in _search_columns()]))

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
        # Phòng yêu cầu (chỉ purchase_request.read) → chỉ thấy ĐMH LIÊN KẾT với PYC
        # trong phạm vi của mình (đơn phát sinh từ yêu cầu mua hàng của mình/phòng mình).
        from app.modules.purchase_request.model import PurchaseRequest
        pr_q = apply_scope(db.query(PurchaseRequest.code), PurchaseRequest,
                           "purchase_request", user, prof)
        codes = [c for (c,) in pr_q.all() if c]
        q = q.filter(PurchaseOrder.pr_code.in_(codes)) if codes else q.filter(PurchaseOrder.id == -1)

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
    """Gate OR cho việc XUẤT: `export` trên ĐMH HOẶC trên YCMH — cùng lối gộp quyền của trang."""
    if (user_has_permission(db, user, "purchase_order", "export")
            or user_has_permission(db, user, "purchase_request", "export")):
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
    columns = pick_columns(ex.columns_for(show_supplier), cols, ex.ALWAYS_COLS)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


#  Tiến độ dòng coi là ĐÃ XONG — không còn việc phải hối thúc.
_CLOSED_PROGRESS = ("completed", "cancelled")


def summarize(rows, show_supplier: bool) -> dict:
    """Gom các hàng (đơn × dòng × lần giao) của `_build_query` thành số liệu cho màn BIỂU ĐỒ
    (phân hệ Báo cáo). Tách khỏi route để bài kiểm gọi thẳng được.

    Luật đếm:
    - Mỗi DÒNG hàng đếm một lần dù có nhiều lần giao (hàng của bảng là theo lần giao).
    - Tình trạng nhận so TỔNG đã nhận của mọi lần giao với SL đặt — cùng luật ô `recv_state`;
      dòng SL đặt = 0 không xếp vào nhóm nào.
    - Lần giao TRỄ = trễ so với hẹn NCC HOẶC so với quy định, cùng luật `/api/reports/procurement`;
      chỉ đếm lần giao đã nhận (`received_qty > 0`).
    - Khối NCC rỗng khi người xem không có `supplier.read` — cùng chốt với cột NCC trên bảng.
    """
    items: dict[int, dict] = {}
    delivery_total = delivery_late = 0
    by_month: dict[str, dict] = {}
    by_supplier: dict[str, dict] = {}
    for po, it, dl in rows:
        item = items.setdefault(it.id, {
            "status": it.progress_status or "not_ordered", "qty": float(it.qty_order or 0),
            "received": 0.0, "department": po.department or "(Không rõ)"})
        if dl is None:
            continue
        item["received"] += float(dl.received_qty or 0)
        if float(dl.received_qty or 0) <= 0:
            continue
        late = (dl.diff_promise or 0) < 0 or (dl.diff_regulated or 0) < 0
        delivery_total += 1
        delivery_late += late
        month = (dl.received_date or "")[:7]
        if len(month) == 7:
            m = by_month.setdefault(month, {"month": month, "received": 0, "late": 0})
            m["received"] += 1
            m["late"] += late
        if show_supplier:
            key = po.supplier_name or po.supplier_code or "(Không rõ)"
            s = by_supplier.setdefault(key, {"key": key, "received": 0, "late": 0})
            s["received"] += 1
            s["late"] += late

    by_status: dict[str, int] = {}
    recv = {"unreceived": 0, "under": 0, "full": 0}
    by_dept: dict[str, dict] = {}
    for item in items.values():
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        if item["qty"] > 0:
            if item["received"] <= 0:
                recv["unreceived"] += 1
            elif item["received"] < item["qty"]:
                recv["under"] += 1
            else:
                recv["full"] += 1
        d = by_dept.setdefault(item["department"], {"key": item["department"], "items": 0, "open": 0})
        d["items"] += 1
        d["open"] += item["status"] not in _CLOSED_PROGRESS

    return {
        "total": {"items": len(items), "deliveries": delivery_total, "late": delivery_late,
                  **recv},
        "by_progress_status": [{"code": k, "items": v} for k, v in by_status.items()],
        "by_month": [by_month[k] for k in sorted(by_month)],
        # NCC nhiều lần trễ nhất đứng đầu — đó là người cần hối thúc.
        "by_supplier": sorted(by_supplier.values(), key=lambda x: (-x["late"], -x["received"], x["key"])),
        "by_department": sorted(by_dept.values(), key=lambda x: (-x["open"], -x["items"], x["key"])),
        "show_supplier": show_supplier,
    }


@router.get("/summary")
def progress_summary(request: Request, year: str = "", db: Session = Depends(get_db),
                     user=Depends(_require_progress)):
    """Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi với bảng.

    Có `preset` (P03) -> hợp đồng chuẩn `build_report` (kỳ + so sánh + Xem theo); không có ->
    hành vi CŨ theo `year` (theo NGÀY ĐẶT hàng), bảng gốc vẫn dùng nhánh này."""
    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    qp = request.query_params
    if qp.get("preset"):
        group_by = qp.get("group_by") or None
        if group_by == "supplier" and not show_supplier:
            raise HTTPException(403, "Không có quyền xem báo cáo theo Nhà cung cấp")
        period = parse_period(qp)

        def fetch(d_from, d_to):
            base = _build_query(request, db, user, prof, _po_scope(db, user), show_supplier)
            return prog_summary.fetch_rows(base, d_from, d_to)

        data = build_report(fetch, prog_summary.build_spec(show_supplier), period, group_by=group_by)
        data["notes"] = data.get("notes", []) + [prog_summary.NOTE]
        return success(data)
    q = _build_query(request, db, user, prof, _po_scope(db, user), show_supplier)
    if year.isdigit():
        q = q.filter(PurchaseOrder.order_date.like(f"{year}%"))
    return success(summarize(q.all(), show_supplier))


@router.get("/summary/export")
def progress_summary_export(request: Request, db: Session = Depends(get_db),
                            user=Depends(_require_progress_export)):
    """Xuất Excel bản THEO KỲ của màn Tiến độ mua hàng (P03) — cùng bộ lọc với `/summary`."""
    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    qp = request.query_params
    group_by = qp.get("group_by") or None
    if group_by == "supplier" and not show_supplier:
        raise HTTPException(403, "Không có quyền xem báo cáo theo Nhà cung cấp")
    period = parse_period(qp)

    def fetch(d_from, d_to):
        base = _build_query(request, db, user, prof, _po_scope(db, user), show_supplier)
        return prog_summary.fetch_rows(base, d_from, d_to)

    data = build_report(fetch, prog_summary.build_spec(show_supplier), period, group_by=group_by)
    data["notes"] = data.get("notes", []) + [prog_summary.NOTE]
    return report_xlsx("tien-do-mua-hang", data)
