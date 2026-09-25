"""agent hub: cot tab_agent_message.files cho anh chup dai ca gui kem (ai-CR-035)

Danh sach tep da luu cua moi tin Telegram, dang JSON [{"path", "kind", "group"}]. Chi
bang cua bot, khong dung bang ERP.

Revision ID: 9a1f3c5e7b20
Revises: b7c1d2e3f4a5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a1f3c5e7b20'
down_revision: Union[str, None] = 'b7c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_agent_message', sa.Column('files', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_agent_message', 'files')
