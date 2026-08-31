"""Phân hệ Công việc — tên `entity` dùng khi ghi nhật ký (`core/audit.record`).

**Vì sao phải có tệp này.** Trước D-09 cả phân hệ ghi chung một tên `work_task`,
còn `entity_id` thì khi là id task, khi là id list, khi là id nhóm. Ba thứ đó
đánh số độc lập nên `(entity="work_task", entity_id=5)` vừa có thể là task #5,
vừa có thể là danh sách #5 — không lọc ra được dòng hoạt động của MỘT dự án.
Tab «Hoạt động» (D-09, §8 của `05-giao-dien.md`) sống bằng đúng phép lọc đó.

Từ nay mỗi loại đối tượng một tên riêng, và **`entity_id` luôn là id của chính
đối tượng nêu trong tên**:

| entity              | entity_id | ghi ở đâu                              |
|---------------------|-----------|----------------------------------------|
| `work_task`         | id task   | `task_service`, `link_service`         |
| `work_list`         | id list   | `list_service`, `list_config_service`  |
| `work_list_member`  | id list   | `list_service` (mời/gỡ/chuyển chủ)     |
| `work_group`        | id nhóm   | `group_service`                        |
| `work_group_member` | id nhóm   | `group_service` (thêm/gỡ thành viên)   |

⚠️ `work_task` giữ nguyên tên cũ có chủ đích: khối «Lịch sử thao tác» trong panel
chi tiết việc (E-04) đang gọi `/api/audit-logs?entity=work_task&entity_id=…`, đổi
là mất trắng lịch sử của mọi việc. Các dòng CŨ mang tên sai được migration
`work_audit_entity_split` đổi lại theo mẫu câu (xem migration đó).

Đây KHÔNG phải entity phân quyền — bảng đó vẫn là `work_task` duy nhất
(`core/permissions.py`). Chỉ là nhãn phân loại trong nhật ký.
"""
from enum import IntEnum

AUDIT_TASK = "work_task"
AUDIT_LIST = "work_list"
AUDIT_LIST_MEMBER = "work_list_member"
AUDIT_GROUP = "work_group"
AUDIT_GROUP_MEMBER = "work_group_member"


class WorkActivityKind(IntEnum):
    """Loại sự kiện trên tab «Hoạt động» — bộ lọc nhanh của §8 chạy trên nó.

    Suy ra từ `entity` chứ KHÔNG mổ chuỗi `message`: câu ghi log là văn xuôi
    tiếng Việt, ai sửa một chữ là bộ lọc câm mà không ai biết.

    Không lưu xuống bảng nào (`tab_audit_log` chỉ có `entity`/`action`), nên đây
    là bộ số DẪN XUẤT — cùng lối `STATE_*` của `survey_request/line_state.py`.
    """

    TASK = 1
    MEMBER = 2
    LIST = 3


ACTIVITY_KIND_LABEL = {
    WorkActivityKind.TASK: "Công việc",
    WorkActivityKind.MEMBER: "Thành viên",
    WorkActivityKind.LIST: "Dự án & cột",
}

#  entity → loại sự kiện. Chỉ ba entity cấp DANH SÁCH có mặt ở đây: hoạt động
#  của nhóm không thuộc về dòng thời gian của một dự án con nào.
ACTIVITY_KIND_BY_ENTITY = {
    AUDIT_TASK: WorkActivityKind.TASK,
    AUDIT_LIST_MEMBER: WorkActivityKind.MEMBER,
    AUDIT_LIST: WorkActivityKind.LIST,
}


def activity_kind_labels() -> list[dict]:
    """Bộ nhãn `[{value, label}]` cho ô lọc ngoài giao diện."""
    return [{"value": int(k), "label": lb} for k, lb in ACTIVITY_KIND_LABEL.items()]
