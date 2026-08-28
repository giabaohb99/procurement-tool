from pydantic import BaseModel, model_validator


class HistoryItem(BaseModel):
    role: str  # user | assistant
    content: str


class AskIn(BaseModel):
    # Được rỗng KHI có tệp đính kèm ("gửi mỗi cái ảnh") — validator dưới cùng giữ luật
    # "phải có chữ hoặc tệp".
    message: str = ""
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
    # Id tệp đã tải qua POST /api/assistant/uploads (CR-204) — gắn vào lượt hỏi này.
    # Quyền sở hữu kiểm ở conversation.chat, không tin id client gửi.
    attachment_ids: list[int] | None = None

    @model_validator(mode="after")
    def _require_text_or_attachment(self):
        if not self.message.strip() and not self.attachment_ids:
            raise ValueError("Cần nhập câu hỏi hoặc đính kèm tệp")
        return self


class ConfirmUpdateIn(BaseModel):
    """Người dùng bấm 'Xác nhận sửa' trên thẻ đề xuất (CR-218) — chỉ cần token của đề xuất;
    mọi dữ liệu sửa nằm TRONG token (Fernet), client không tự chọn được trường/giá trị."""

    token: str
