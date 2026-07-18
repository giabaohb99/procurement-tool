from sqlalchemy import JSON, BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Comment(Base, AuditMixin):
    """Bình luận đa hình: gắn vào (entity, entity_id). Tác giả = created_by (AuditMixin).

    - entity: 'survey' (cấp phiếu) | 'survey_line' (cấp dòng NCC/SP).
    - parent_id: reply 1 cấp (NULL = comment gốc).
    - mention_user_ids: danh sách user_id được @nhắc → nhận thông báo.
    """

    __tablename__ = "tab_comment"

    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    body: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    mention_user_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
