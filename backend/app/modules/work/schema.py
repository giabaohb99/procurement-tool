"""Phân hệ Công việc — schema chiều VÀO (W1).

Chiều RA dựng bằng dict ở `serializer.py` (khuôn Diễn đàn / comment): hình dạng
trả về chỉ một chỗ dùng, khai thêm một lớp Pydantic nữa là hai bản phải sửa
song song mỗi lần thêm trường.

Quy ước: trường `None` nghĩa là **KHÔNG ĐỔI** (PATCH thật sự), khác hẳn `""`
hay `0` là "xóa giá trị đi". Service dựa vào đúng quy ước này.
"""
from pydantic import BaseModel, Field

from app.modules.work.model import WorkMemberRole


class GroupCreate(BaseModel):
    name: str
    description: str = ""
    #  Có `parent_id` = nhóm con. Service chặn cấp 3 (A-08).
    parent_id: int | None = None
    sort_order: int = 0


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_archived: int | None = None


class MemberIn(BaseModel):
    """Mời một người vào nhóm/list. `role` theo `WorkMemberRole` (số nhỏ = quyền to).

    Mặc định MEMBER: mời nhầm thành quản trị nguy hiểm hơn mời thiếu quyền.
    """

    employee_id: int
    role: int = int(WorkMemberRole.MEMBER)


class ListCreate(BaseModel):
    name: str
    description: str = ""
    color: str = ""
    group_id: int | None = None
    sort_order: int = 0


class ListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    #  Gửi `0` để kéo list RA khỏi nhóm (đứng lẻ vẫn hợp lệ — A-08).
    group_id: int | None = None
    sort_order: int | None = None
    is_archived: int | None = None


class TransferIn(BaseModel):
    employee_id: int


class SectionIn(BaseModel):
    name: str = ""
    color: str | None = None
    sort_order: int | None = None


class TagIn(BaseModel):
    name: str
    color: str = ""
    sort_order: int = 0


class LabelFieldIn(BaseModel):
    name: str
    sort_order: int = 0


class LabelOptionIn(BaseModel):
    name: str
    color: str = ""
    sort_order: int = 0


class TaskCreate(BaseModel):
    """Tạo task, hoặc VIỆC CON khi có `parent_id`.

    Việc con bỏ qua `list_id`/`section_id` — nó luôn theo cha (C-05).
    """

    list_id: int = 0
    section_id: int | None = None
    parent_id: int | None = None
    title: str
    description: str = ""
    priority: int = 0
    start_date: str = ""
    due_date: str = ""
    sort_order: int = 0
    assignee_ids: list[int] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Sửa task. Kéo thẻ sang cột khác = gửi `section_id` + `sort_order` (B-07)."""

    title: str | None = None
    description: str | None = None
    status: int | None = None
    priority: int | None = None
    start_date: str | None = None
    due_date: str | None = None
    section_id: int | None = None
    sort_order: int | None = None


class TaskMove(BaseModel):
    """Kéo thả kanban. Mốc TƯƠNG ĐỐI: chèn NGAY TRƯỚC `before_task_id`, `None` =
    xuống cuối cột. Vì sao không nhận `sort_order`: xem `task_service.move_task`."""

    section_id: int
    before_task_id: int | None = None


class AssigneesIn(BaseModel):
    """Đặt LẠI toàn bộ người phụ trách/theo dõi — không phải thêm từng người.

    Nhiều PIC được (Q5). Ai có mặt ở cả hai danh sách thì tính là PIC.
    """

    pic_ids: list[int] = Field(default_factory=list)
    follower_ids: list[int] = Field(default_factory=list)


class TagsIn(BaseModel):
    tag_ids: list[int] = Field(default_factory=list)


class LabelIn(BaseModel):
    """Chọn giá trị cho một trường nhãn. `option_id = None` là bỏ chọn."""

    field_id: int
    option_id: int | None = None
