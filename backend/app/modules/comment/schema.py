from pydantic import BaseModel, Field

# survey_id/survey_code KHÔNG nhận từ FE nữa — server tự suy từ (entity, entity_id) để
# tránh giả mạo thông báo (H1). Field thừa do FE gửi sẽ bị Pydantic bỏ qua (extra='ignore').


class CommentCreate(BaseModel):
    entity: str            # 'survey' | 'survey_line'
    entity_id: int
    body: str = Field(min_length=1, max_length=5000)
    parent_id: int | None = None
    mention_user_ids: list[int] | None = None


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    mention_user_ids: list[int] | None = None
