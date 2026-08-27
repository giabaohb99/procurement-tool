"""them tab_user_preference luu tuy chon ca nhan

Bang khoa-gia tri cho tuy chon HIEN THI cua tung nguoi dung (hien co: bang mau
giao dien). Xem `app/modules/user_preference/model.py`.

Autogenerate co bat them mot loat alter_column/drop_index cua cac bang khac
(troi mo hinh cu tich luy tu truoc) — da CAT BO het, migration nay chi tao dung
mot bang moi. Dung gop viec don troi vao day.

Revision ID: 3b46d70224ea
Revises: c4d8a2f9e617
Create Date: 2026-08-27 04:47:01.109503
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3b46d70224ea'
down_revision: Union[str, None] = 'c3d9e14a58b7'  # noi tiep sau migration dien dan
# Ban dau tro vao 'c4d8a2f9e617'. Nhanh dien dan (CR-193) cung xuat phat tu do va
# len truoc, nen sau khi gop lai co HAI dau migration - `alembic upgrade head` se
# bao "Multiple head revisions are present" va deploy chet. Doi sang noi tiep sau
# no. Bang tab_user_preference khong dung chung bang nao voi dien dan nen thu tu
# chay khong quan trong.
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_user_preference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('pref_key', sa.String(length=64), nullable=False),
        sa.Column('pref_value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'pref_key', name='uq_user_preference_user_key'),
    )
    op.create_index(
        op.f('ix_tab_user_preference_user_id'),
        'tab_user_preference',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_user_preference_user_id'), table_name='tab_user_preference')
    op.drop_table('tab_user_preference')
