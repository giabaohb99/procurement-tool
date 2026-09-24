"""tien_do_ho_so_theo_chung_tu

Bảng `tab_dossier_progress` — tiến độ MỘT tờ hồ sơ TRÊN MỘT chứng từ, thứ tách
«đã có giấy trong kho» khỏi «đã xong cho phiếu này». Xem
`app/modules/dossier/progress_model.py`.

⚠️ Bản autogenerate ra 678 dòng: gần như toàn bộ là **trôi dạt có sẵn** của
repo (NOT NULL trên cột đã có dữ liệu, đổi tên chỉ mục của hai bảng xe…), không
phải thay đổi của lần này. Đã gọt về đúng một bảng mới — chạy nguyên bản kia là
sửa cấu trúc của mười mấy bảng không liên quan trong một migration mang tên hồ sơ.

Revision ID: b92c74d55ee7
Revises: 2ef5534e5ace
Create Date: 2026-09-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b92c74d55ee7'
down_revision: Union[str, None] = '2ef5534e5ace'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_dossier_progress',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('doc_kind', sa.String(length=30), nullable=False),
        sa.Column('doc_id', sa.BigInteger(), nullable=False),
        sa.Column('dossier_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('assignee_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('planned_date', sa.Date(), nullable=True),
        sa.Column('note', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('file_note', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        #  Chốt chống GHI TRÙNG, không phải để tra nhanh: hai lượt bấm gần nhau
        #  mà không có nó thì đẻ hai dòng cho cùng một ô tick, và lần đọc sau
        #  lấy trúng dòng nào là tùy thứ tự MySQL trả về.
        sa.UniqueConstraint('doc_kind', 'doc_id', 'dossier_id', name='uq_dossier_progress'),
    )
    op.create_index(op.f('ix_tab_dossier_progress_doc_kind'), 'tab_dossier_progress',
                    ['doc_kind'], unique=False)
    op.create_index(op.f('ix_tab_dossier_progress_doc_id'), 'tab_dossier_progress',
                    ['doc_id'], unique=False)
    op.create_index(op.f('ix_tab_dossier_progress_dossier_id'), 'tab_dossier_progress',
                    ['dossier_id'], unique=False)
    op.create_index(op.f('ix_tab_dossier_progress_status'), 'tab_dossier_progress',
                    ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_dossier_progress_status'), table_name='tab_dossier_progress')
    op.drop_index(op.f('ix_tab_dossier_progress_dossier_id'), table_name='tab_dossier_progress')
    op.drop_index(op.f('ix_tab_dossier_progress_doc_id'), table_name='tab_dossier_progress')
    op.drop_index(op.f('ix_tab_dossier_progress_doc_kind'), table_name='tab_dossier_progress')
    op.drop_table('tab_dossier_progress')
