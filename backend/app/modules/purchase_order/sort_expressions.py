"""ĐMH — biểu thức SQL cho các cột danh sách KHÔNG phải cột vật lý (duoc-CR-738).

Dùng truy vấn con tương quan (correlated scalar subquery) để chạy được cả MySQL 8 lẫn SQLite của bộ test.
Mỗi biểu thức phải KHỚP số hiển thị do serializer tính, kẻo bấm sắp xếp ra thứ tự lệch với con số trên màn.
"""
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.central_purchasing import get_central_dept_id
from app.core.code_rank_sql import build_code_rank_expression, build_value_rank_expression
from app.core.status_codes import PO_DOCUMENT_STATUS
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from app.modules.user.model import User

from .model import OrderType, POItem, PurchaseOrder

#  Dòng đời của đơn (cột `status`): nhãn đang hiện là tiếng Việt nên xếp theo THỨ TỰ TIẾN TRÌNH,
#  không theo chữ cái của mã tiếng Anh (duoc-CR-744). Nhánh rẽ (bị trả lại, từ chối) đứng sau
#  chuỗi; `processing` là mã cũ không còn nhãn, đặt sau "Đã duyệt".
PO_STATUS_ORDER = ("draft", "submitted", "approved", "processing", "partial", "received",
                   "completed", "rejected", "cancelled", "")


def list_sort_allow(db: Session) -> dict:
    """Map {khóa cột giao diện: biểu thức} cho cột tính toán của danh sách ĐMH.

    - `amount`: tiền hàng = SL đặt x đơn giá x (1 + VAT%) x tỷ giá, cộng mọi dòng
      (cùng luật `order_amount_map`; tỷ giá trống hoặc 0 đọc thành 1).
    - `supplier`: ô bày tên NCC, đơn chỉ có mã thì bày mã -> xếp theo đúng chữ đang hiện.
    - `status` / `document_status`: hạng theo dòng đời / chuỗi chứng từ, không theo chữ cái của mã.
    - `handler_dept_name`: tên phòng xử lý; `handler_dept_id = 0` (đơn cũ) = phòng thu mua mặc định
      (bao-CR-524), giống `list_display_names`.
    - `approver_name`: tên trưởng phòng phê duyệt được chọn (`approver_employee_id`).
    - `order_type`: xếp theo NHÃN đang hiện (Nhập khẩu < Trong nước), không theo mã số 1 / 2.
    - `company_name`, `created_by_name`: hai cột phụ ẩn sẵn (bao-CR-705).
    """
    rate = case((func.coalesce(POItem.exchange_rate, 0) == 0, 1), else_=POItem.exchange_rate)
    amount = (
        select(func.coalesce(
            func.sum(POItem.qty_order * POItem.price * (1 + POItem.vat / 100.0) * rate), 0))
        .where(POItem.po_id == PurchaseOrder.id)
        .correlate(PurchaseOrder)
        .scalar_subquery()
    )
    central = get_central_dept_id(db)
    handler_id = case((func.coalesce(PurchaseOrder.handler_dept_id, 0) == 0, central),
                      else_=PurchaseOrder.handler_dept_id)
    handler_name = (
        select(Department.name).where(Department.id == handler_id)
        .correlate(PurchaseOrder).scalar_subquery()
    )
    approver_name = (
        select(Employee.full_name).where(Employee.id == PurchaseOrder.approver_employee_id)
        .correlate(PurchaseOrder).scalar_subquery()
    )
    company_name = (
        select(Company.name).where(Company.id == PurchaseOrder.company_id)
        .correlate(PurchaseOrder).scalar_subquery()
    )
    #  Người tạo: họ tên nhân sự, thiếu thì email tài khoản (đúng `list_display_names`).
    created_by_name = (
        select(func.coalesce(Employee.full_name, User.email))
        .select_from(User.__table__.outerjoin(Employee.__table__, Employee.id == User.employee_id))
        .where(User.id == PurchaseOrder.created_by)
        .correlate(PurchaseOrder).scalar_subquery()
    )
    return {
        "amount": amount,
        "order_type": case((PurchaseOrder.order_type == int(OrderType.IMPORT), 1),
                           (PurchaseOrder.order_type == int(OrderType.DOMESTIC), 2), else_=3),
        "company_name": company_name,
        "created_by_name": created_by_name,
        "supplier": func.coalesce(func.nullif(PurchaseOrder.supplier_name, ""),
                                  PurchaseOrder.supplier_code),
        "status": build_value_rank_expression(PurchaseOrder.status, PO_STATUS_ORDER),
        "document_status": build_code_rank_expression(PurchaseOrder.document_status,
                                                      PO_DOCUMENT_STATUS),
        "handler_dept_name": handler_name,
        "approver_name": approver_name,
    }
