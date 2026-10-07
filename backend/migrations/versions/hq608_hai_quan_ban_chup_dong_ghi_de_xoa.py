"""bao-CR-608: Tra cứu thị trường — bảng chụp dòng hàng trước khi ghi đè / xóa

Tệp nạp màn «Giá thị trường» nhận thêm hai cột tùy chọn: «ID» (ID có thật → ghi đè đúng dòng đó)
và «Thao tác» (= xóa → xóa dòng có ID đó); màn hình có thêm sửa / xóa từng dòng. Trước khi đụng
một dòng đã có, hệ thống chụp ĐỦ mọi cột của dòng vào bảng mới `tab_customs_line_change`:

- `batch_id` BIGINT — lô nạp đã ghi đè / xóa (0 = sửa / xóa tay trên màn);
- `line_id` BIGINT — id dòng hàng bị đụng;
- `action` SMALLINT — 1 ghi đè · 2 xóa (`CustomsLineChangeAction`, luật R2);
- `source` SMALLINT — 1 nạp tệp · 2 sửa tay (`CustomsLineChangeSource`);
- `snapshot` JSON — mọi cột của dòng trước khi đụng (kèm id, reg_date, batch_id, importer_id,
  partner_id) để hoàn tác lô chèn lại đúng id cũ;
- `created_at`, `created_by`.

Không đổi `tab_customs_line` (bảng chia phân vùng theo năm `reg_date`).

Revision ID: hq608
Revises: lbrct01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "hq608"
down_revision: Union[str, None] = "lbrct01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_customs_line_change",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("line_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("action", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("source", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customs_line_change_batch", "tab_customs_line_change", ["batch_id"])
    op.create_index("ix_customs_line_change_line", "tab_customs_line_change", ["line_id"])


def downgrade() -> None:
    op.drop_index("ix_customs_line_change_line", table_name="tab_customs_line_change")
    op.drop_index("ix_customs_line_change_batch", table_name="tab_customs_line_change")
    op.drop_table("tab_customs_line_change")
