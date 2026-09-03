"""CR-260: cot offset_amount tren dong YCTT — can tru tien treo khi DUYET

Trước đây dialog ở ĐMH gọi cấn trừ NGAY lúc bấm tạo phiếu (bấm nhầm không lùi được,
người bấm là thu mua). CR-260 chuyển thành: lúc tạo chỉ GHI phần cấn trừ vào dòng
phiếu (cột này), khi phiếu được DUYỆT backend mới thực thi cấn trừ thật.

Revision ID: a1c58f27d3e6
Revises: 79f6f09573b9
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c58f27d3e6'
down_revision: Union[str, None] = '79f6f09573b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_payment_request_line",
                  sa.Column("offset_amount", sa.Numeric(18, 2), nullable=False,
                            server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_payment_request_line", "offset_amount")
