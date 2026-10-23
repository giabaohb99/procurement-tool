"""CHE CỘT NHẠY CẢM khi XUẤT CSV/Excel nhân sự (duoc-CR-660, HR1-1 / C7).

Một cơ chế cho mọi đường xuất nhân sự (CSV cũ, XLSX, xuất tập trung `export_log`):
cột nào trùng `sensitive.SENSITIVE_FIELDS` mà người xuất thiếu `employee_sensitive.read`
thì ô để RỖNG. Không gõ danh sách thứ hai — thêm trường nhạy cảm mới vào `SENSITIVE_FIELDS`
là mọi bộ xuất tự che theo.

Lý do tách riêng: hôm nay các bộ xuất chưa có cột nhạy cảm nào, nên chưa gì bị lộ; nhưng đúng
ngày ai đó thêm «Ngày sinh» hay «Số TK ngân hàng» vào bộ cột (việc rất tự nhiên với Nhân sự),
nếu không có chốt này thì người chỉ có `employee.export` kéo được cả công ty. Che ở TẦNG DỮ LIỆU
xuất chứ không dựa vào việc người viết bộ cột nhớ lọc.

Ngoại lệ `self` giống mọi cửa khác: dòng hồ sơ của CHÍNH người xuất vẫn đủ.
"""
from types import SimpleNamespace

from . import sensitive


def mask_export_rows(rows: list[dict], employee_ids: list[int], profile) -> list[dict]:
    """Che tại chỗ `rows` (mỗi dòng là dict `khóa cột -> giá trị`), trả lại chính danh sách đó.

    `employee_ids` song song với `rows` (id hồ sơ của từng dòng) để xét ngoại lệ `self`.
    """
    if sensitive.can_read_sensitive(profile):
        return rows
    for row, eid in zip(rows, employee_ids):
        sensitive.mask(row, sensitive.can_read_sensitive(profile, eid))
    return rows


def masked_row_objects(items: list, keys: list[str], profile) -> list[SimpleNamespace]:
    """Dựng các đối tượng `getattr`-được cho `csv_utils.export_csv_response` (nó đọc bằng
    `getattr(item, field)`), đã che cột nhạy cảm. Giữ `is_active` để cột «Trạng thái» đúng."""
    rows = [{k: getattr(it, k, "") for k in keys} for it in items]
    mask_export_rows(rows, [it.id for it in items], profile)
    #  Gộp dict (không truyền `is_active=` riêng): bộ cột nào có sẵn khóa `is_active` thì
    #  hai kwargs trùng tên sẽ ném TypeError -> 500 ngay ở nút Xuất.
    return [SimpleNamespace(**{"is_active": getattr(it, "is_active", True), **r})
            for r, it in zip(rows, items)]
