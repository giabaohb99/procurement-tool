"""Biểu thức SẮP XẾP tại server cho màn danh sách Yêu cầu thanh toán (duoc-CR-744).

`apply_sort_from_request(..., allow=...)` chỉ nhận cột thật của bảng nếu không có map này. Các cột
dưới đây ở giao diện hiện chữ KHÁC giá trị lưu trong DB, nên xếp thẳng theo cột là xếp theo thứ gì
người dùng không nhìn thấy. Mỗi khóa xếp theo ĐÚNG thứ ô đang hiện, trên cả tập (đúng qua phân
trang và cả tệp Xuất Excel):

- Nhà cung cấp: ô hiện tên, thiếu tên thì hiện mã NCC.
- Loại nợ, Hình thức TT: DB lưu mã tiếng Anh, ô hiện nhãn tiếng Việt -> xếp theo thứ tự chữ của nhãn.
- Trạng thái: xếp theo vòng đời (Nháp -> Chờ duyệt -> Đã duyệt -> Đã chi -> Đã từ chối).
- Công ty: xếp theo TÊN (`company_id` ra thứ tự số vô nghĩa).
- Người yêu cầu: xếp theo tên nhân sự của tài khoản lập phiếu (cùng luật `resolve_actor`).
- Mã MISA: ô hiện "MS1, MS2" gộp theo thứ tự dòng phiếu nên xếp theo mã MISA ĐẦU TIÊN (dòng phiếu có
  mã, theo thứ tự dòng) - đúng phần đầu của chuỗi đang hiện; phiếu không có mã MISA nào xuống cuối.
- Số tiền, Mã phiếu, Ngày lập, Ngày cập nhật: cột thật, `apply_sort` lo.
"""
from sqlalchemy import case, func, select

from app.core.code_rank_sql import build_value_rank_expression
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.user.model import User

from .model import PaymentRequest, PaymentRequestLine

#  Thứ tự CHỮ của nhãn ở giao diện: Chi phí nhập khẩu < Hàng hóa < Thanh toán nghỉ phép < Vận chuyển.
SOURCE_TYPE_ORDER = ["import_cost", "goods", "leave_encashment", "shipping"]
#  Chuyển khoản < Tiền mặt.
PAYMENT_METHOD_ORDER = ["transfer", "cash"]
#  Vòng đời phiếu; `cancelled` (Đã từ chối) là nhánh phụ nên đứng cuối.
STATUS_ORDER = ["draft", "submitted", "approved", "paid", "cancelled"]


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`."""
    supplier_shown = case((func.trim(PaymentRequest.supplier_name) != "", PaymentRequest.supplier_name),
                          else_=PaymentRequest.supplier_code)
    company_name = (select(Company.name).where(Company.id == PaymentRequest.company_id)
                    .limit(1).scalar_subquery())
    #  Tên người lập: tên nhân sự, không có thì email tài khoản; `created_by = 0` (hệ thống) -> NULL.
    creator_name = (select(func.coalesce(func.nullif(func.trim(Employee.full_name), ""), User.email))
                    .select_from(User)
                    .outerjoin(Employee, Employee.id == User.employee_id)
                    .where(User.id == PaymentRequest.created_by)
                    .limit(1).scalar_subquery())
    #  Mã MISA đầu tiên của phiếu: dòng phiếu chụp mã PO, mã MISA nằm ở ĐMH nên nối theo mã lúc đọc
    #  (cùng luật `service.misa_codes_by_request`: bỏ qua ĐMH chưa có mã MISA).
    first_misa = (select(PurchaseOrder.misa_code)
                  .select_from(PaymentRequestLine)
                  .join(PurchaseOrder, PurchaseOrder.code == func.trim(PaymentRequestLine.po_code))
                  .where(PaymentRequestLine.request_id == PaymentRequest.id,
                         func.trim(PurchaseOrder.misa_code) != "")
                  .order_by(PaymentRequestLine.id)
                  .limit(1).scalar_subquery())
    return {
        "misa_code": first_misa,
        "supplier_name": supplier_shown,
        "company": company_name,
        "created_by_name": creator_name,
        "source_type": build_value_rank_expression(PaymentRequest.source_type, SOURCE_TYPE_ORDER),
        "payment_method": build_value_rank_expression(PaymentRequest.payment_method, PAYMENT_METHOD_ORDER),
        "status": build_value_rank_expression(PaymentRequest.status, STATUS_ORDER),
    }
