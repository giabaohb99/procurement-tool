"""Biểu thức SẮP XẾP tại server cho bảng Chi tiết YC mua hàng (`GET /api/reports/pr-lines` + `/export`).

duoc-CR-744. Trước đây `sort_by` / `sort_dir` bị bỏ qua hoàn toàn: bảng luôn ra theo ngày lập phiếu
mới nhất, bấm tiêu đề cột không đổi gì. Nay mỗi cột người dùng thấy đều xếp được trên CẢ TẬP (đúng
qua phân trang, và file Xuất Excel ra cùng thứ tự với bảng), theo đúng thứ MÀ Ô ĐANG HIỆN:

- Cột thật nằm thẳng trong dòng YCMH / phiếu YCMH: xếp theo cột đó.
- Cột hiện TÊN dựng từ id hay mã (NSTM, pháp nhân, trưởng bộ phận, người duyệt, phòng xử lý, gram):
  xếp theo tên, không theo id / mã — xếp theo id ra thứ tự số vô nghĩa với người đọc.
- Trạng thái (tiến độ dòng, trạng thái phiếu) hiện NHÃN tiếng Việt, mà xếp theo chữ cái nhãn thì
  "Chưa đặt hàng" đứng sau "Hủy đơn" — vô nghĩa. Nên xếp theo THỨ TỰ VÒNG ĐỜI nghiệp vụ (xem
  `_LINE_STATUS_ORDER`, `_PR_STATUS_ORDER`); tăng dần = từ đầu vòng đời tới cuối.
- Cột ghép từ ĐMH (mã ĐMH, số đơn, NCC đơn gần nhất, hẹn giao gần nhất, số lần nhận hàng): dựng lại
  bằng truy vấn con tương quan, CÙNG điều kiện ghép với `service._pr_line_po_links` — hai nơi mà lệch
  thì cột hiện một giá trị còn thứ tự theo giá trị khác.

Giá trị rỗng / NULL theo luật của DB (đứng đầu khi tăng dần, cuối khi giảm dần) — như các màn khác.
"""
from sqlalchemy import case, func, literal, select

from app.core.central_purchasing import get_central_dept_id
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.product.model import Product
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

I = PurchaseRequestItem
PR = PurchaseRequest

#  Thứ tự vòng đời của TIẾN ĐỘ DÒNG (khớp `status_codes.PR_LINE_STATUS`): chưa tạo đơn -> chưa đặt ->
#  đã đặt -> đã nhận -> hoàn thành; "Hủy đơn" nằm ngoài chuỗi nên xếp cuối. Bài kiểm canh đủ mã.
_LINE_STATUS_ORDER = ("no_po", "not_ordered", "ordered", "received", "completed", "cancelled")

#  Thứ tự vòng đời của TRẠNG THÁI PHIẾU YCMH: nháp -> chờ duyệt -> đã duyệt -> điều phối -> đang xử lý
#  -> đang mua -> đã mua -> hoàn thành; hai nhánh kết thúc không thành (bị trả lại, đã từ chối) xếp cuối.
_PR_STATUS_ORDER = ("draft", "submitted", "approved", "dispatched", "processing", "purchasing",
                    "purchased", "completed", "rejected", "cancelled")

#  Cột chỉ người có `supplier.read` được xếp: thứ tự dòng theo tên NCC là đủ để mò ra NCC đã bị che.
SUPPLIER_SORT_KEYS = frozenset({"suggested_supplier", "latest_po_supplier"})

#  Cột thật, xếp thẳng.
_DIRECT_COLUMNS = {
    "id": I.id,
    "pr_code": PR.code,
    "created_date": PR.request_date,
    "requester": PR.requester,
    "department": PR.department,
    "product_code": I.product_code,
    "product_name": I.product_name,
    "warehouse": I.warehouse,
    "item_group": I.item_group,
    "qty": I.qty,
    "price": I.price,
    "vat_pct": I.vat_pct,
    "amount": I.amount,
    "expected_date": I.expected_date,
    "qty_ordered": I.qty_ordered,
    "qty_received": I.qty_received,
    "purpose": PR.purpose,
    "is_urgent": PR.is_urgent,
    "need_date": PR.need_date,
    "required_date": I.required_date,
    "unit": I.unit,
    "suggested_supplier": PR.suggested_supplier,
    "progress_note": I.progress_note,
    "line_note": I.note,
}


def _rank(column, order: tuple[str, ...]):
    """CASE xếp hạng theo `order`; mã lạ / rỗng ra hạng sau cùng."""
    return case({code: index for index, code in enumerate(order)}, value=func.coalesce(column, ""),
                else_=len(order))


def _employee_name(match):
    return select(Employee.full_name).where(match).limit(1).scalar_subquery()


def _po_link_conditions():
    """Điều kiện ghép dòng YCMH với dòng ĐMH — PHẢI trùng `service._pr_line_po_links`: ĐMH mang mã phiếu
    và dòng ĐMH cùng mã hàng; bỏ đơn đã xóa / đã hủy và dòng đơn đã hủy; dòng YCMH không mã hàng thì không ghép."""
    return (PurchaseOrder.pr_code == PR.code, PR.code != "",
            POItem.product_code == I.product_code, I.product_code != "",
            PurchaseOrder.is_deleted.is_(False), PurchaseOrder.status != "cancelled",
            POItem.progress_status != "cancelled")


def _po_scalar(column, *extra, order_by=()):
    """Truy vấn con lấy MỘT giá trị của đơn ghép với dòng YCMH đang xét (theo `order_by`, lấy dòng đầu)."""
    return (select(column).select_from(PurchaseOrder).join(POItem, POItem.po_id == PurchaseOrder.id)
            .where(*_po_link_conditions(), *extra).order_by(*order_by).limit(1).scalar_subquery())


def _po_aggregate(expression, *, with_delivery: bool, extra=()):
    """Truy vấn con gom (đếm / lớn nhất) trên các đơn ghép; `with_delivery` nối thêm các lần giao hàng."""
    stmt = select(expression).select_from(PurchaseOrder).join(POItem, POItem.po_id == PurchaseOrder.id)
    if with_delivery:
        stmt = stmt.join(PODelivery, PODelivery.po_item_id == POItem.id)
    return stmt.where(*_po_link_conditions(), *extra).scalar_subquery()


def _computed_expression(db, key: str):
    """Biểu thức SQL cho cột TÍNH / cột hiện tên; None nếu `key` không thuộc nhóm này."""
    if key == "gram":
        #  Gram = "Thông số" của sản phẩm cùng mã hàng (hệ thống không có trường gram riêng).
        return select(Product.specs).where(Product.code == I.product_code).limit(1).scalar_subquery()
    if key == "line_status":
        return _rank(I.line_status, _LINE_STATUS_ORDER)
    if key == "status":
        return _rank(PR.status, _PR_STATUS_ORDER)
    if key == "assignee":
        #  Ô hiện tên NSTM, lùi về mã nếu mã không còn khớp nhân sự.
        name = _employee_name(Employee.code == I.assignee)
        return func.coalesce(func.nullif(name, ""), I.assignee)
    if key == "company_name":
        return select(Company.name).where(Company.id == PR.company_id).limit(1).scalar_subquery()
    if key == "head_of_dept_name":
        #  Ô hiện tên theo id nhân sự, lùi về tên đã chụp trên phiếu.
        name = _employee_name(Employee.id == PR.head_of_dept_id)
        return func.coalesce(func.nullif(name, ""), PR.head_of_dept)
    if key == "approver_name":
        return _employee_name(Employee.id == PR.approver_employee_id)
    if key == "handler_dept_name":
        #  `handler_dept_id = 0` (phiếu cũ) đọc như phòng thu mua mặc định, đúng như ô đang hiện.
        dept_id = case((PR.handler_dept_id != 0, PR.handler_dept_id), else_=literal(get_central_dept_id(db)))
        return select(Department.name).where(Department.id == dept_id).limit(1).scalar_subquery()
    if key == "po_codes":
        #  Ô hiện các mã nối dấu phẩy theo thứ tự đơn tạo trước -> sau: xếp theo mã ĐẦU TIÊN của dãy đó.
        return _po_scalar(PurchaseOrder.code,
                          order_by=(PurchaseOrder.created_at.asc(), PurchaseOrder.id.asc(), POItem.id.asc()))
    if key == "po_count":
        return _po_aggregate(func.count(func.distinct(PurchaseOrder.code)), with_delivery=False)
    if key == "latest_po_supplier":
        #  NCC của đơn tạo SAU CÙNG có ghi tên NCC (như `_pr_line_po_links`).
        return _po_scalar(PurchaseOrder.supplier_name, PurchaseOrder.supplier_name != "",
                          order_by=(PurchaseOrder.created_at.desc(), PurchaseOrder.id.desc(), POItem.id.desc()))
    if key == "latest_delivery_date":
        return _po_aggregate(func.max(func.nullif(PODelivery.promised_date, "")), with_delivery=True)
    if key == "delivery_count":
        return _po_aggregate(func.count(PODelivery.id), with_delivery=True, extra=(PODelivery.received_qty > 0,))
    return None


def get_pr_lines_sort_expression(db, key: str, *, show_supplier: bool):
    """Biểu thức xếp cho cột `key`; None nếu cột không xếp được (controller bỏ qua, giữ thứ tự mặc định).

    Cột NCC chỉ xếp được khi người xem có `supplier.read` (`show_supplier`)."""
    if key in SUPPLIER_SORT_KEYS and not show_supplier:
        return None
    if key in _DIRECT_COLUMNS:
        return _DIRECT_COLUMNS[key]
    return _computed_expression(db, key)


def sortable_keys() -> frozenset[str]:
    """Mọi khóa cột xếp được — để bài kiểm canh đủ cột bảng."""
    computed = {"gram", "line_status", "status", "assignee", "company_name", "head_of_dept_name",
                "approver_name", "handler_dept_name", "po_codes", "po_count", "latest_po_supplier",
                "latest_delivery_date", "delivery_count"}
    return frozenset(_DIRECT_COLUMNS) | computed
