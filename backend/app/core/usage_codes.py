"""Bộ mã HỒ SƠ CÁCH LÀM VIỆC (duoc-CR-641) — số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG.

R2/QĐ-11: cột phân loại là `SMALLINT` + `IntEnum`; tiếng Việt chỉ ở tầng hiển thị.
Dùng bởi `tab_ui_event.event_type/form_key`, `tab_user_usage_snapshot.cohort_kind`,
`tab_user_usage_label.label` và khóa `unmeasured` trong JSON snapshot.

Luật bất biến (cùng `report_keys.py`): số đã cấp giữ nguyên mãi mãi, không gán lại cho
mục khác; mục bỏ thì để trống số; mục mới cấp số TIẾP THEO. `0` không hợp lệ ở bộ nào
trừ `UiForm` (0 = «không phải form», ghi rõ ở schema telemetry).

Thuần stdlib (không import SQLAlchemy) vì `code_sets.py` phải nạp được khi chạy
`scripts/gen_status_ts.py` ở máy không cài SQLAlchemy.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class UiEventType(IntEnum):
    PAGE_VIEW = 1
    PAGE_LEAVE = 2
    FORM_OPEN = 3
    FORM_SUBMIT = 4
    FORM_ABANDON = 5
    SEARCH = 6
    CLIENT_ERROR = 7
    UI_ACTION = 8   # duoc-CR-654: bấm chức năng (mã nút ở `ui_action_codes.UiAction`)


class UiForm(IntEnum):
    """Biểu mẫu có móc đo. Giá trị 0 (không thuộc bộ này) = sự kiện không phải form."""

    PURCHASE_REQUEST = 1   # YCMH
    QUOTE_REQUEST = 2      # YCBG
    PURCHASE_ORDER = 3     # ĐMH
    LEAVE_REQUEST = 4      # Đơn nghỉ phép
    LABOR_CONTRACT = 5     # HĐLĐ
    EMPLOYEE_PROFILE = 6   # Hồ sơ nhân sự
    #  duoc-CR-654 (D0b): 7 biểu mẫu thêm — số tiếp, không chèn giữa
    PAYMENT_REQUEST = 7    # Yêu cầu thanh toán
    GOODS_RECEIPT = 8      # Nhận hàng = dialog dòng ĐMH (không có form nhận hàng riêng)
    DOCUMENT = 9           # Văn bản
    VEHICLE_BOOKING = 10   # Đặt xe
    SEAL_REQUEST = 11      # Duyệt dấu
    ROOM_BOOKING = 12      # Đặt phòng họp
    WORK_TASK = 13         # Việc dự án (tạo nhanh)


class UiApp(IntEnum):
    """Ứng dụng gửi sự kiện (bao-CR-649). Cột `tab_ui_event.app`; lô không khai = ERP v2 (v2 không phải sửa)."""

    ERP_V2 = 1
    THUMUA = 2   # app cũ frontend/ (phòng Thu mua làm chủ yếu ở đây)


class FeatureKind(IntEnum):
    """Loại chức năng ở bảng gom `tab_feature_usage_daily` (duoc-CR-655, D0c)."""

    ACTION = 1        # bấm chức năng (code = UiAction)
    FORM = 2          # biểu mẫu (code = UiForm; uses=mở, completes=gửi, abandons=bỏ dở)
    SCREEN = 3        # màn hình (route; uses=lượt xem, duration_ms=thời gian ở lại)
    SEARCH = 4        # tìm kiếm (route; uses=lượt, fails=lượt không ra kết quả)
    CLIENT_ERROR = 5  # lỗi giao diện (route; uses=số lỗi)


class UsageStyle(IntEnum):
    """Kiểu làm việc (§4 của thiết kế) — nhãn gắn theo tuần, có bằng chứng."""

    BATCH_WORKER = 1       # Làm dồn
    APPROVAL_BOTTLENECK = 2  # Nút thắt duyệt
    EXCEL_PARALLEL = 3     # Dùng Excel song song
    NEWCOMER_STUCK = 4     # Người mới đang vướng
    POWER_USER = 5         # Người thạo
    WANDERER = 6           # Hay đi lạc
    MOBILE_FIRST = 7       # Làm trên điện thoại
    LOW_QUALITY_DOCS = 8   # Phiếu kém chất lượng
    PROXY_DEPENDENT = 9    # Nhờ làm hộ
    LOW_USAGE = 10         # Ít dùng


class CohortKind(IntEnum):
    ROLE = 1
    COMPANY = 2
    ALL = 3


class UnmeasuredReason(IntEnum):
    NOT_COLLECTED = 1      # chưa bật thu sự kiện / trước ngày bật
    BELOW_THRESHOLD = 2    # dưới ngưỡng dữ liệu tối thiểu
    NOT_APPLICABLE = 3     # không áp dụng (vd không có việc duyệt nào)


class PeriodKind(IntEnum):
    WEEK = 1


UI_EVENT_TYPE_LABELS = {
    UiEventType.PAGE_VIEW: "Xem màn hình", UiEventType.PAGE_LEAVE: "Rời màn hình",
    UiEventType.FORM_OPEN: "Mở biểu mẫu", UiEventType.FORM_SUBMIT: "Gửi biểu mẫu",
    UiEventType.FORM_ABANDON: "Bỏ dở biểu mẫu", UiEventType.SEARCH: "Tìm kiếm",
    UiEventType.CLIENT_ERROR: "Lỗi giao diện",
    UiEventType.UI_ACTION: "Bấm chức năng",
}
UI_FORM_LABELS = {
    UiForm.PURCHASE_REQUEST: "Yêu cầu mua hàng", UiForm.QUOTE_REQUEST: "Yêu cầu báo giá",
    UiForm.PURCHASE_ORDER: "Đơn mua hàng", UiForm.LEAVE_REQUEST: "Đơn nghỉ phép",
    UiForm.LABOR_CONTRACT: "Hợp đồng lao động", UiForm.EMPLOYEE_PROFILE: "Hồ sơ nhân sự",
    UiForm.PAYMENT_REQUEST: "Yêu cầu thanh toán", UiForm.GOODS_RECEIPT: "Nhận hàng (dòng ĐMH)",
    UiForm.DOCUMENT: "Văn bản", UiForm.VEHICLE_BOOKING: "Đặt xe", UiForm.SEAL_REQUEST: "Duyệt dấu",
    UiForm.ROOM_BOOKING: "Đặt phòng họp", UiForm.WORK_TASK: "Việc dự án (tạo nhanh)",
}
UI_APP_LABELS = {UiApp.ERP_V2: "ERP v2", UiApp.THUMUA: "Thu mua (app cũ)"}
FEATURE_KIND_LABELS = {
    FeatureKind.ACTION: "Bấm chức năng", FeatureKind.FORM: "Biểu mẫu", FeatureKind.SCREEN: "Màn hình",
    FeatureKind.SEARCH: "Tìm kiếm", FeatureKind.CLIENT_ERROR: "Lỗi giao diện",
}
USAGE_STYLE_LABELS = {
    UsageStyle.BATCH_WORKER: "Làm dồn", UsageStyle.APPROVAL_BOTTLENECK: "Nút thắt duyệt",
    UsageStyle.EXCEL_PARALLEL: "Dùng Excel song song", UsageStyle.NEWCOMER_STUCK: "Người mới đang vướng",
    UsageStyle.POWER_USER: "Người thạo", UsageStyle.WANDERER: "Hay đi lạc",
    UsageStyle.MOBILE_FIRST: "Làm trên điện thoại", UsageStyle.LOW_QUALITY_DOCS: "Phiếu kém chất lượng",
    UsageStyle.PROXY_DEPENDENT: "Nhờ làm hộ", UsageStyle.LOW_USAGE: "Ít dùng",
}
COHORT_KIND_LABELS = {CohortKind.ROLE: "Cùng vai trò", CohortKind.COMPANY: "Cùng pháp nhân",
                      CohortKind.ALL: "Toàn công ty"}
UNMEASURED_REASON_LABELS = {
    UnmeasuredReason.NOT_COLLECTED: "Chưa thu thập", UnmeasuredReason.BELOW_THRESHOLD: "Dưới ngưỡng dữ liệu",
    UnmeasuredReason.NOT_APPLICABLE: "Không áp dụng",
}


def _set(name: str, title: str, labels: dict, keyed: bool = False) -> CodeSet:
    #  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi.
    #  `keyed=True`: kèm tên thành viên IntEnum làm `key` để sinh hằng TS (R2: giao diện không chép tay mã gửi lên).
    return register(CodeSet(name, title, [Code(str(int(k)), v, sort_order=int(k), key=k.name if keyed else "")
                                          for k, v in labels.items()]))


UI_EVENT_TYPE_SET = _set("ui_event_type", "Loại sự kiện giao diện", UI_EVENT_TYPE_LABELS, keyed=True)
UI_FORM_SET = _set("ui_form", "Biểu mẫu có đo", UI_FORM_LABELS, keyed=True)
UI_APP_SET = _set("ui_app", "Ứng dụng gửi sự kiện", UI_APP_LABELS, keyed=True)
FEATURE_KIND_SET = _set("feature_kind", "Loại chức năng đo", FEATURE_KIND_LABELS, keyed=True)
USAGE_STYLE_SET = _set("usage_style", "Kiểu làm việc", USAGE_STYLE_LABELS)
COHORT_KIND_SET = _set("usage_cohort_kind", "Nhóm so sánh", COHORT_KIND_LABELS)
UNMEASURED_REASON_SET = _set("usage_unmeasured_reason", "Lý do chưa đo được", UNMEASURED_REASON_LABELS, keyed=True)
