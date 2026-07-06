"""survey_request (Yêu cầu khảo sát - Task 5)

Revision ID: e5b3d9a1c8f0
Revises: d4a2c6e8b1f3
Create Date: 2026-07-06 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5b3d9a1c8f0'
down_revision: Union[str, None] = 'd4a2c6e8b1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit():
    return [
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
    ]


def upgrade() -> None:
    op.create_table(
        'tab_survey_request',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('company_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('requester', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('requester_position', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('department', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('head_of_dept', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('purpose', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('request_date', sa.String(length=10), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('assignee_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('reject_reason', sa.Text(), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_survey_request_code'), 'tab_survey_request', ['code'], unique=True)
    op.create_index('ix_tab_survey_request_department', 'tab_survey_request', ['department'])
    op.create_index('ix_tab_survey_request_status', 'tab_survey_request', ['status'])

    op.create_table(
        'tab_survey_request_line',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('internal_line_code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('received_date', sa.String(length=10), nullable=False, server_default=''),
        sa.Column('result_due_date', sa.String(length=10), nullable=False, server_default=''),
        sa.Column('department_requester', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('item_group', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('requirement_detail', sa.Text(), nullable=True),
        sa.Column('other_requirement', sa.Text(), nullable=True),
        sa.Column('request_qty', sa.Numeric(18, 3), nullable=False, server_default='0'),
        sa.Column('uom', sa.String(length=25), nullable=False, server_default=''),
        sa.Column('proposed_price', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('image_file', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('assignee', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('pr_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('pr_code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'),
        *_audit(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tab_survey_request_line_survey_request_id', 'tab_survey_request_line', ['survey_request_id'])
    op.create_index('ix_tab_survey_request_line_item_group', 'tab_survey_request_line', ['item_group'])

    op.create_table(
        'tab_survey_request_option',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('survey_request_line_id', sa.BigInteger(), nullable=False),
        sa.Column('product_survey_line_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('public_id', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('display_label', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('is_chosen', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('chosen_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('snap_product_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('snap_spec', sa.Text(), nullable=True),
        sa.Column('snap_origin', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('snap_quote_unit', sa.String(length=25), nullable=False, server_default=''),
        sa.Column('snap_moq', sa.Numeric(18, 3), nullable=False, server_default='0'),
        sa.Column('snap_price_by_volume', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('snap_volume_range', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('snap_vat', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('snap_delivery_time', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('snap_delivery_place', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('snap_shipping_cost', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('snap_sample_ready', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('snap_lab_result', sa.String(length=20), nullable=False, server_default=''),
        sa.Column('snap_internal_code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('supplier_code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('supplier_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('supplier_survey_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('nstm_note', sa.Text(), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tab_survey_request_option_line_id', 'tab_survey_request_option', ['survey_request_line_id'])
    op.create_index('ix_tab_survey_request_option_psl', 'tab_survey_request_option', ['product_survey_line_id'])
    op.create_index('ix_tab_survey_request_option_chosen', 'tab_survey_request_option', ['is_chosen'])


def downgrade() -> None:
    op.drop_table('tab_survey_request_option')
    op.drop_table('tab_survey_request_line')
    op.drop_index(op.f('ix_tab_survey_request_code'), table_name='tab_survey_request')
    op.drop_table('tab_survey_request')
