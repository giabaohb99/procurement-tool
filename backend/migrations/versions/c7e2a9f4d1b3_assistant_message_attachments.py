"""assistant_message_attachments (CR-204)

Them cot `attachments` (JSON danh sach tep dinh kem) vao tab_assistant_message —
tin cua nguoi dung co the kem anh/PDF cho tro ly phan tich.

Viet TAY (khong autogenerate — autogenerate keo theo ~20 bang drift ngoai pham vi).

Revision ID: c7e2a9f4d1b3
Revises: b8d4e6f1a2c9
Create Date: 2026-08-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e2a9f4d1b3'
down_revision: Union[str, None] = 'b8d4e6f1a2c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL tu dien '' cho dong cu khi ADD COLUMN TEXT NOT NULL (TEXT khong nhan DEFAULT).
    op.add_column('tab_assistant_message', sa.Column('attachments', sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column('tab_assistant_message', 'attachments')
