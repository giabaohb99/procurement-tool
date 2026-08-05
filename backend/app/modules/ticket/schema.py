from pydantic import BaseModel


class TicketCreate(BaseModel):
    subject: str = ""
    department: str = ""
    priority: str = "normal"
    body: str = ""                       # nội dung tin nhắn đầu tiên
    company_id: int = 0
    origin_url: str = ""                  # trang người gửi đang đứng lúc bấm Hỗ trợ (để debug)
    file_ids: list[int] = []             # đính kèm đã upload trước, gắn vào phiếu sau khi tạo


class TicketUpdate(BaseModel):
    subject: str | None = None
    department: str | None = None
    priority: str | None = None


class MessageCreate(BaseModel):
    body: str = ""
    file_ids: list[int] = []


class StatusIn(BaseModel):
    status: str                          # in_progress | answered | closed | open
    assignee_id: int | None = None       # tùy chọn: nhóm hỗ trợ nhận việc


class AssignIn(BaseModel):
    assignee_id: int = 0                 # 0 = bỏ nhận (trả phiếu về hàng chờ)
