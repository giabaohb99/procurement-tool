from pydantic import BaseModel


class CommentIn(BaseModel):
    entity: str
    entity_id: int
    body: str = ""
    # 0 = bình luận gốc. Trỏ vào một phản hồi cũng được — backend tự kéo về gốc (luật 2 cấp).
    parent_id: int = 0
    # Người được nhắc (@). Để 0 thì backend tự suy: trả lời phản hồi của ai thì nhắc người đó.
    reply_to_user_id: int = 0
