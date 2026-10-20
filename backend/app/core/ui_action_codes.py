"""Bộ mã «BẤM CHỨC NĂNG» (duoc-CR-654, D0a) — số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG.

R2/QĐ-11: cột `tab_ui_event.action_key` là `SMALLINT` + `IntEnum`; tiếng Việt chỉ ở tầng hiển thị.
Cấp số theo KHỐI để thêm mã không phải chèn giữa. Khối 300–319 (Duyệt) để trống: cấp khi có duyệt hàng
loạt thật — mã có trong danh mục mà không gắn sẽ làm báo cáo hiện «không ai dùng» sai.

Thuần stdlib (cùng `usage_codes.py`): `code_sets.py` phải nạp được khi chạy `scripts/gen_status_ts.py`.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class UiAction(IntEnum):
    # 1–19 Bảng
    COLUMN_TOGGLE = 1
    COLUMN_PIN = 2
    COLUMN_COLOR = 3
    LAYOUT_RESET = 4
    SORT_CHANGE = 5
    PAGE_CHANGE = 6
    PAGE_SIZE_CHANGE = 7
    REFRESH = 8
    SELECT_ALL_PAGE = 9
    # 20–39 Lọc
    FILTER_APPLY = 20
    FILTER_RESET = 21
    FILTER_ROW_ADD = 22
    QUICK_FILTER = 23
    # 100–119 Xuất / In
    EXPORT_EXCEL = 100
    PRINT = 101
    REPORT_EXPORT = 102
    # 200–219 Phiếu / dòng
    COPY_DOCUMENT = 200
    COPY_LINE = 201
    BULK_DELETE_LINES = 202
    CREATE_NEW = 203


UI_ACTION_LABELS = {
    UiAction.COLUMN_TOGGLE: "Ẩn/hiện cột", UiAction.COLUMN_PIN: "Ghim cột",
    UiAction.COLUMN_COLOR: "Tô màu cột", UiAction.LAYOUT_RESET: "Khôi phục bố cục",
    UiAction.SORT_CHANGE: "Sắp xếp", UiAction.PAGE_CHANGE: "Chuyển trang",
    UiAction.PAGE_SIZE_CHANGE: "Đổi số dòng/trang", UiAction.REFRESH: "Làm mới",
    UiAction.SELECT_ALL_PAGE: "Chọn cả trang",
    UiAction.FILTER_APPLY: "Áp bộ lọc", UiAction.FILTER_RESET: "Xóa bộ lọc",
    UiAction.FILTER_ROW_ADD: "Thêm điều kiện lọc", UiAction.QUICK_FILTER: "Lọc nhanh",
    UiAction.EXPORT_EXCEL: "Xuất Excel", UiAction.PRINT: "In", UiAction.REPORT_EXPORT: "Xuất báo cáo",
    UiAction.COPY_DOCUMENT: "Nhân bản phiếu", UiAction.COPY_LINE: "Sao chép dòng",
    UiAction.BULK_DELETE_LINES: "Xóa nhiều dòng", UiAction.CREATE_NEW: "Tạo mới từ danh sách",
}

UI_ACTION_SET = register(CodeSet(
    "ui_action", "Chức năng được bấm",
    [Code(str(int(k)), v, sort_order=int(k), key=k.name) for k, v in UI_ACTION_LABELS.items()],
))
