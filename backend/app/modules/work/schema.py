"""Phân hệ Công việc — schema chiều VÀO (W1).

Chiều RA dựng bằng dict ở `serializer.py` (khuôn Diễn đàn / comment): hình dạng
trả về chỉ một chỗ dùng, khai thêm một lớp Pydantic nữa là hai bản phải sửa
song song mỗi lần thêm trường.

Quy ước: trường `None` nghĩa là **KHÔNG ĐỔI** (PATCH thật sự), khác hẳn `""`
hay `0` là "xóa giá trị đi". Service dựa vào đúng quy ước này.
"""
from typing import Any

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


class SectionMove(BaseModel):
    """Kéo cột kanban. Mốc TƯƠNG ĐỐI: chèn NGAY TRƯỚC `before_section_id`,
    `None` = đẩy xuống cuối. Cùng luật với `TaskMove`."""

    before_section_id: int | None = None


class LabelFieldIn(BaseModel):
    """Khai một trường tùy biến. `field_type` theo `WorkLabelFieldType` (B-13);
    mặc định `1 = chọn một` để lời gọi cũ không đổi hành vi."""

    name: str
    sort_order: int = 0
    field_type: int = 1


class LabelOptionIn(BaseModel):
    name: str
    color: str = ""
    sort_order: int = 0


class LabelFieldUpdate(BaseModel):
    """Đổi tên / kiểu / thứ tự một trường tùy biến.

    ⚠️ `field_type` chỉ đổi được khi trường CHƯA có giá trị nào gán cho việc, và
    không phải trường hệ (`system_key`). Đổi kiểu khi đã có dữ liệu là mọi giá
    trị cũ nằm sai cột `value_*` — nhìn như mất sạch. Service chặn, không phải
    giao diện.
    """

    name: str | None = None
    field_type: int | None = None
    sort_order: int | None = None


class LabelOptionUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    sort_order: int | None = None


class TaskCreate(BaseModel):
    """Tạo task, hoặc VIỆC CON khi có `parent_id`.

    Việc con bỏ qua `list_id`/`section_id` — nó luôn theo cha (C-05).
    """

    list_id: int = 0
    section_id: int | None = None
    parent_id: int | None = None
    title: str
    description: str = ""
    start_date: str = ""
    due_date: str = ""
    sort_order: int = 0
    assignee_ids: list[int] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Sửa task. Kéo thẻ sang cột khác = gửi `section_id` + `sort_order` (B-07)."""

    title: str | None = None
    description: str | None = None
    status: int | None = None
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


class LabelIn(BaseModel):
    """Đặt giá trị cho một trường tùy biến. `value = None` là bỏ chọn.

    `value` ĐA HÌNH theo kiểu trường (id giá trị · danh sách id · employee_id ·
    số · chuỗi ngày · chữ) nên để `Any`: khai kiểu chặt ở đây thì mỗi lần thêm
    một kiểu trường lại phải sửa schema, mà Pydantic cũng không biết kiểu nào
    hợp lệ nếu chưa đọc `field_type` dưới CSDL. Phép kiểm thật nằm ở
    `label_value_service.write_value`.
    """

    field_id: int
    value: Any = None
