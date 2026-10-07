"""agent hub: mau bien ban hop dang du lieu — them template_label, template_prompt (ai-CR-112)

Revision ID: meet02
Revises: aibase01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "meet02"
down_revision: Union[str, None] = "aibase01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_agent_meeting", sa.Column("template_label", sa.String(length=80), nullable=False, server_default=""))
    #  MySQL không cho TEXT có giá trị mặc định; thêm cột NOT NULL thì các dòng cũ nhận chuỗi rỗng (như meet01).
    op.add_column("tab_agent_meeting", sa.Column("template_prompt", sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column("tab_agent_meeting", "template_prompt")
    op.drop_column("tab_agent_meeting", "template_label")
