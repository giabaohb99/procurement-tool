"""Bộ mã của sổ đồng bộ — SMALLINT kèm IntEnum theo luật R2/QĐ-11.

Mọi thứ trong tệp này CỐ Ý không biết gì về một hệ nguồn cụ thể. Tên nguồn, tên
đối tượng, cờ cảnh báo riêng của từng nguồn thì khai ở `registry.py`, không khai
ở đây. Nhờ vậy sổ dùng lại được cho app đặt xe hôm nay, POS365 và đồng bộ đơn
hàng về sau.

Nhãn tiếng Việt chỉ sống ở tệp này và ở tầng hiển thị; DB chỉ lưu SỐ.
"""
from enum import IntEnum


class SyncGrain(IntEnum):
    """Một dòng sổ đang nói về cái gì.

    MỘT bảng chứa cả hai hạt, cố ý. Trước đây POS365 có bảng riêng
    `tab_pos_sync_run` cho hạt LƯỢT CHẠY, còn app đặt xe định dựng bảng riêng cho
    hạt BẢN GHI — hai bảng, hai màn hình, hai bộ mã trạng thái lệch nhau, và
    không bấm từ một lượt chạy sang những bản ghi nó đã ghi được. Gộp lại thì
    `run_id` nối cha-con ngay trong một bảng.
    """

    RUN = 1     # một LƯỢT CHẠY (con trỏ thời gian, đếm kéo/ghi/bỏ)
    RECORD = 2  # một BẢN GHI đi qua


class SyncDirection(IntEnum):
    """Dữ liệu chạy theo chiều nào so với ERP."""

    INBOUND = 1   # hệ ngoài -> ERP (nhận về)
    OUTBOUND = 2  # ERP -> hệ ngoài (gửi đi)


class SyncAction(IntEnum):
    """Sự kiện xảy ra với bản ghi."""

    CREATE = 1
    UPDATE = 2
    STATUS_CHANGE = 3
    DELETE = 4


class SyncStatus(IntEnum):
    """Vòng đời một dòng sổ.

    PENDING được ghi TRƯỚC khi làm việc (luật §3.2) nên tiến trình chết giữa
    chừng vẫn còn dấu vết; RUNNING/SUCCESS/FAILED/SKIPPED là kết cục.
    """

    PENDING = 1
    RUNNING = 2
    SUCCESS = 3
    FAILED = 4
    SKIPPED = 5


GRAIN_LABELS: dict[int, str] = {
    SyncGrain.RUN: "Lượt chạy",
    SyncGrain.RECORD: "Bản ghi",
}

DIRECTION_LABELS: dict[int, str] = {
    SyncDirection.INBOUND: "Nhận về",
    SyncDirection.OUTBOUND: "Gửi đi",
}

ACTION_LABELS: dict[int, str] = {
    SyncAction.CREATE: "Tạo mới",
    SyncAction.UPDATE: "Cập nhật",
    SyncAction.STATUS_CHANGE: "Đổi trạng thái",
    SyncAction.DELETE: "Xóa",
}

STATUS_LABELS: dict[int, str] = {
    SyncStatus.PENDING: "Chờ xử lý",
    SyncStatus.RUNNING: "Đang chạy",
    SyncStatus.SUCCESS: "Thành công",
    SyncStatus.FAILED: "Lỗi",
    SyncStatus.SKIPPED: "Bỏ qua",
}

#: Trạng thái được phép bấm "Chạy lại".
RETRYABLE_STATUSES = (SyncStatus.FAILED, SyncStatus.PENDING)

#: Trạng thái được phép dọn dẹp định kỳ. Luật §3.2: CHỈ dọn dòng thành công,
#: không bao giờ dọn dòng lỗi.
PURGEABLE_STATUSES = (SyncStatus.SUCCESS,)

#: Số tháng giữ lại dòng thành công trước khi việc chạy nền dọn đi.
PURGE_AFTER_MONTHS = 6


# --- Cờ cảnh báo dùng chung ------------------------------------------------
# Cờ là thứ cho phép LỌC RA mọi bản ghi có dữ liệu bịa sau này. Khai hằng số,
# đừng gõ chuỗi rải rác trong mã. Nguồn nào cần cờ riêng thì khai thêm ở
# `registry.py` (trường `extra_warnings`), đừng nhét vào đây.

WARN_NO_EMPLOYEE = "no_employee"          # không tra ra người theo email
WARN_NO_DEPARTMENT = "no_department"      # không tra ra phòng ban
WARN_COMPANY_BY_DEPT = "company_by_dept"  # pháp nhân lấy ở nấc 2 (theo phòng ban)
WARN_COMPANY_DEFAULT = "company_default"  # pháp nhân lấy ở nấc 3 (GIÁ TRỊ BỊA)
WARN_TRUNCATED = "truncated"              # có chuỗi bị cắt vì vượt trần độ dài
WARN_STATUS_LOSSY = "status_lossy"        # ánh xạ trạng thái không kín

COMMON_WARNINGS: dict[str, str] = {
    WARN_NO_EMPLOYEE: "Không tra ra nhân sự",
    WARN_NO_DEPARTMENT: "Không tra ra phòng ban",
    WARN_COMPANY_BY_DEPT: "Pháp nhân suy từ phòng ban",
    WARN_COMPANY_DEFAULT: "Pháp nhân lấy mặc định (dữ liệu bịa)",
    WARN_TRUNCATED: "Có chuỗi bị cắt ngắn",
    WARN_STATUS_LOSSY: "Trạng thái ánh xạ không kín",
}

#: Ngăn cách các cờ trong cột `warnings`.
WARNING_SEPARATOR = ","

#: Trần độ dài cột `warnings` (String(255)) — cắt bớt còn hơn để MySQL ném 500.
WARNINGS_MAX_LENGTH = 255

#: Cửa sổ lệch giờ tối đa của chữ ký (giây). Quá thì coi như tín hiệu phát lại.
SIGNATURE_MAX_SKEW_SECONDS = 300
