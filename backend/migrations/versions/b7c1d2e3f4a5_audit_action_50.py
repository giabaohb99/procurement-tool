"""audit: noi cot tab_audit_log.action 20 -> 50 (bao-CR-463)

Tro ly AI ghi `tool:<ten tool>` vao cot nay; ten dai nhat hien 27 ky tu nen moi dong
audit tool ten dai bi MySQL tu choi va lop tool rollback ca phien trong im lang.
Noi rong trong lop 1 byte do dai (< 256 byte utf8mb4) nen MySQL 8 doi INSTANT, khong khoa bang.

Revision ID: b7c1d2e3f4a5
Revises: 8023c5f8bee4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7c1d2e3f4a5'
down_revision: Union[str, None] = '8023c5f8bee4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tab_audit_log', 'action', existing_type=sa.String(length=20),
                    type_=sa.String(length=50), existing_nullable=False)


def downgrade() -> None:
    #  Co the mat du lieu neu da co dong dai hon 20 — co y khong cat bot, de MySQL bao loi.
    op.alter_column('tab_audit_log', 'action', existing_type=sa.String(length=50),
                    type_=sa.String(length=20), existing_nullable=False)
