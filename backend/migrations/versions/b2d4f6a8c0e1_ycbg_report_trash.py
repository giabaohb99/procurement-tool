"""ycbg_report_trash — sọt rác cho khối Báo cáo thực hiện (YCBG), phục vụ HOÀN TÁC
lần «Xóa báo cáo thực hiện».

⚠️ VIẾT TAY, không autogenerate: dev DB lệch model nên autogenerate kéo theo hàng
trăm lệnh drift không liên quan (xem ghi chú migration 7816572fed52). Chỉ tạo đúng
một bảng.

Revision ID: b2d4f6a8c0e1
Revises: a1c2e3d4f5b6
Create Date: 2026-09-12 04:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2d4f6a8c0e1'
down_revision: Union[str, None] = 'a1c2e3d4f5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_survey_request_report_trash',
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('doc_count', sa.SmallInteger(), nullable=False),
        sa.Column('audit_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('restored', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_survey_request_report_trash_survey_request_id'),
                    'tab_survey_request_report_trash', ['survey_request_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_report_trash_audit_id'),
                    'tab_survey_request_report_trash', ['audit_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_survey_request_report_trash_audit_id'),
                  table_name='tab_survey_request_report_trash')
    op.drop_index(op.f('ix_tab_survey_request_report_trash_survey_request_id'),
                  table_name='tab_survey_request_report_trash')
    op.drop_table('tab_survey_request_report_trash')
