from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    role: str  # user | assistant
    content: str


class AskIn(BaseModel):
    message: str = Field(min_length=1)
    # None = nhà mặc định (config). 'claude' | 'gemini'.
    provider: str | None = None
    # None = model mặc định của nhà đó.
    model: str | None = None
    # lookup (loại A) | advice (loại B) | general.
    kind: str = "general"
    # Chèn THÊM vào cuối system (không ghi đè định nghĩa/rào an toàn). Chủ yếu để test.
    system: str | None = None
    # Hội thoại đang tiếp. None = mở hội thoại mới. Nếu truyền `conversation_id` thì
    # `history` bị bỏ qua — lịch sử lấy thẳng từ DB (nguồn chân lý).
    conversation_id: int | None = None
    history: list[HistoryItem] | None = None
