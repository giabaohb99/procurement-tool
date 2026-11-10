"""Biểu thức SẮP XẾP tại server cho các cột KHÔNG xếp thẳng theo một cột DB của màn Tiến độ
mua hàng (duoc-CR-744).

`controller._sort_map()` giữ cột thật và cũng là whitelist của bộ lọc điều kiện. Các cột dưới
đây hoặc là cột TÍNH (hai cột thành tiền), hoặc bày ra khác giá trị lưu (Công ty bày TÊN mà cột
lưu id; Tiến độ / Hồ sơ CT bày nhãn mà cột lưu mã) — xếp thẳng theo cột lưu là ra thứ tự
người dùng đọc thấy lộn xộn. Tách riêng để không mở thêm bộ lọc điều kiện theo biểu thức.
"""
from sqlalchemy import case, func, select

from app.core.code_rank_sql import build_code_rank_expression
from app.core.status_codes import PO_DOCUMENT_STATUS, PO_PROGRESS_STATUS
from app.modules.company.model import Company
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder


def _amount_factor():
    """Đơn giá × (1 + VAT%) × tỷ giá — bản SQL của phần chung trong `export.row_values`.

    Tỷ giá rỗng / 0 đọc thành 1, đúng luật `normalize_rate` (dòng VNĐ và dòng cũ để trống).
    """
    rate = func.coalesce(POItem.exchange_rate, 0)
    rate = case((rate == 0, 1), else_=rate)
    vat = func.coalesce(POItem.vat, 0)
    return func.coalesce(POItem.price, 0) * (1 + vat / 100) * rate


def get_computed_sort_expression(key: str):
    """Biểu thức xếp cho cột `key`; None nếu cột này không có cách xếp riêng."""
    if key == "company":
        #  Xếp theo TÊN công ty như chữ đang hiện, không theo `company_id`.
        return (select(Company.name).where(Company.id == PurchaseOrder.company_id)
                .limit(1).scalar_subquery())
    if key == "order_amount":
        return func.coalesce(POItem.qty_order, 0) * _amount_factor()
    if key == "received_qty":
        #  Hàng chưa có lần giao: bảng hiện 0 (`row_values`) nên xếp như số 0, không xuống
        #  cuối như ô trống (A3 soát dev 10/11/2026).
        return func.coalesce(PODelivery.received_qty, 0)
    if key == "amount":
        #  Hàng chưa có lần giao: SL nhận NULL -> 0, khớp ô 0 trên bảng.
        return func.coalesce(PODelivery.received_qty, 0) * _amount_factor()
    if key == "progress_status":
        #  Dòng cũ để trống hiện là "Chưa đặt hàng" (`row_values`) nên xếp cùng chỗ đó.
        return build_code_rank_expression(POItem.progress_status, PO_PROGRESS_STATUS,
                                          blank_value=PO_PROGRESS_STATUS.ordered_values[0])
    if key == "document_status":
        return build_code_rank_expression(PurchaseOrder.document_status, PO_DOCUMENT_STATUS)
    if key == "supplier_name":
        #  Ô bày tên NCC, thiếu tên thì lùi về mã NCC — xếp theo đúng chữ đang hiện.
        return func.coalesce(func.nullif(PurchaseOrder.supplier_name, ""),
                             PurchaseOrder.supplier_code)
    return None
