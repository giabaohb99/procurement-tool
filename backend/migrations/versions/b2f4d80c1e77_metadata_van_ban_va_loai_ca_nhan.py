"""CR-159: tab_document.metadata (JSON) + tab_doc_type.is_personal

Hai cột phục vụ loại văn bản **Giấy nghỉ phép**:

* `tab_document.metadata` — thông tin riêng của từng loại (đơn nghỉ phép cần
  người nghỉ, loại nghỉ, từ/đến ngày kèm buổi, số ngày, lý do, người bàn giao,
  số liên lạc). Thêm mỗi loại một cụm cột thì bảng phình ra và 90% cột luôn NULL
  với 90% văn bản. Hình dạng do `document/type_metadata.py` quy định và backend
  kiểm trước khi ghi — đây không phải ô đổ dữ liệu tùy tiện.

* `tab_doc_type.is_personal` — loại bật cờ này thì văn bản của nó **không đi theo
  phạm vi vai trò** nữa. `document.read` phạm vi *công ty* vốn nghĩa là "đọc mọi
  văn bản của pháp nhân"; áp lên đơn nghỉ phép thì thành cả công ty đọc được đơn
  xin nghỉ ốm của từng người. Luật đầy đủ ở `access_service`.

Bật sẵn cho mã `GNP` (Giấy nghỉ phép) — loại này đã có trong danh mục từ trước.

Revision ID: b2f4d80c1e77
Revises: e7c3a91d55b2
"""
from alembic import op
import sqlalchemy as sa

revision = "b2f4d80c1e77"
down_revision = "e7c3a91d55b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tab_document", sa.Column("metadata", sa.JSON(), nullable=True))
    op.add_column(
        "tab_doc_type",
        sa.Column("is_personal", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    #  Bật cho Giấy nghỉ phép. Dùng UPDATE có điều kiện theo MÃ chứ không theo id:
    #  id khác nhau giữa các môi trường, mã thì giữ nguyên.
    #
    #  ⚠️ Không đụng tới bất kỳ loại nào khác — bật nhầm là văn bản đang chạy
    #  biến mất khỏi danh sách của người đang xem được chúng.
    op.get_bind().execute(
        sa.text("UPDATE tab_doc_type SET is_personal = 1 WHERE code = 'GNP'"))


def downgrade() -> None:
    op.drop_column("tab_doc_type", "is_personal")
    op.drop_column("tab_document", "metadata")
