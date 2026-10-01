from pydantic import BaseModel
from app.modules.employee.field_limits import Str20, Str30, Str255, Str500


class TicketCreate(BaseModel):
    subject: Str255 = ""
    department: Str255 = ""
    priority: Str20 = "normal"
    body: str = ""                       # nội dung tin nhắn đầu tiên
    company_id: int = 0
    origin_url: Str500 = ""                  # trang người gửi đang đứng lúc bấm Hỗ trợ (để debug)
    file_ids: list[int] = []             # đính kèm đã upload trước, gắn vào phiếu sau khi tạo


class TicketUpdate(BaseModel):
    subject: Str255 | None = None
    department: Str255 | None = None
    priority: Str20 | None = None


class MessageCreate(BaseModel):
    body: str = ""
    file_ids: list[int] = []


class StatusIn(BaseModel):
    status: Str30                          # in_progress | answered | closed | open
    assignee_id: int | None = None       # tùy chọn: nhóm hỗ trợ nhận việc


class AssignIn(BaseModel):
    assignee_id: int = 0                 # 0 = bỏ nhận (trả phiếu về hàng chờ)
