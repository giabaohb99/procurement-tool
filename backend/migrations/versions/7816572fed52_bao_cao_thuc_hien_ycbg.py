"""bao_cao_thuc_hien_ycbg — 3 bảng khối Báo cáo thực hiện trên phiếu YCBG.

⚠️ Bản autogenerate gốc kéo theo hàng trăm lệnh drift không liên quan (drop
`tab_attachment`, đổi nullability hàng loạt…) do dev DB lệch model từ trước —
đã CẮT SẠCH, chỉ giữ đúng 3 bảng mới. Đừng autogenerate lại rồi giữ nguyên.

Revision ID: 7816572fed52
Revises: bee157de2ec8
Create Date: 2026-09-12 01:49:52.398852
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7816572fed52'
down_revision: Union[str, None] = 'bee157de2ec8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_survey_request_report_item',
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_survey_request_report_item_survey_request_id'),
                    'tab_survey_request_report_item', ['survey_request_id'], unique=False)

    op.create_table('tab_survey_request_report_phase',
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_survey_request_report_phase_survey_request_id'),
                    'tab_survey_request_report_phase', ['survey_request_id'], unique=False)

    op.create_table('tab_survey_request_report_doc',
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('phase_id', sa.BigInteger(), nullable=False),
        sa.Column('item_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('file_note', sa.String(length=500), nullable=False),
        sa.Column('depends', sa.JSON(), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_survey_request_report_doc_item_id'),
                    'tab_survey_request_report_doc', ['item_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_report_doc_phase_id'),
                    'tab_survey_request_report_doc', ['phase_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_report_doc_status'),
                    'tab_survey_request_report_doc', ['status'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_report_doc_survey_request_id'),
                    'tab_survey_request_report_doc', ['survey_request_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_survey_request_report_doc_survey_request_id'),
                  table_name='tab_survey_request_report_doc')
    op.drop_index(op.f('ix_tab_survey_request_report_doc_status'),
                  table_name='tab_survey_request_report_doc')
    op.drop_index(op.f('ix_tab_survey_request_report_doc_phase_id'),
                  table_name='tab_survey_request_report_doc')
    op.drop_index(op.f('ix_tab_survey_request_report_doc_item_id'),
                  table_name='tab_survey_request_report_doc')
    op.drop_table('tab_survey_request_report_doc')
    op.drop_index(op.f('ix_tab_survey_request_report_phase_survey_request_id'),
                  table_name='tab_survey_request_report_phase')
    op.drop_table('tab_survey_request_report_phase')
    op.drop_index(op.f('ix_tab_survey_request_report_item_survey_request_id'),
                  table_name='tab_survey_request_report_item')
    op.drop_table('tab_survey_request_report_item')
