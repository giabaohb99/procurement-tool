"""Điểm cà phê × POS365 — phase CP1: 5 bảng nền (doc/erp/diem-ca-phe/02-bang-du-lieu.md)

Viết TAY (không autogenerate — DB dev đang lệch một migration của nhánh khác nên
autogenerate không chạy được), đối chiếu từng cột với
`app/modules/coffee_point/model.py`. Điểm đáng soát:
  - `tab_coffee_ledger.uniq_key` UNIQUE + NULLABLE — MySQL cho nhiều NULL trong
    UNIQUE, đó chính là chỗ ADJUST/REVOKE được nhiều dòng còn GRANT/SPEND thì không;
  - sổ cái CHỈ INSERT — không có gì ở tầng DDL diễn tả điều đó, luật nằm ở
    service (`append_ledger` là đường ghi duy nhất).

Revision ID: coffee1cp1a01
Revises: 32e30ac28788
Create Date: 2026-09-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'coffee1cp1a01'
down_revision: Union[str, None] = '32e30ac28788'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols():
    """Bộ cột chuẩn của AuditMixin — mọi bảng trong hệ đều có."""
    return [
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        'tab_coffee_policy',
        *_audit_cols(),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('level_code', sa.SmallInteger(), nullable=False),
        sa.Column('monthly_points', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.String(length=10), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'level_code', 'effective_from',
                            name='uq_coffee_policy_level_from'),
    )
    op.create_index(op.f('ix_tab_coffee_policy_company_id'), 'tab_coffee_policy',
                    ['company_id'])

    op.create_table(
        'tab_coffee_member',
        *_audit_cols(),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('employee_id', sa.BigInteger(), nullable=False),
        sa.Column('level_code', sa.SmallInteger(), nullable=False),
        sa.Column('title_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('pos_partner_id', sa.BigInteger(), nullable=False),
        sa.Column('pos_partner_code', sa.String(length=50), nullable=False),
        sa.Column('matched_by', sa.BigInteger(), nullable=False),
        sa.Column('matched_at', sa.String(length=19), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id'),
    )
    op.create_index(op.f('ix_tab_coffee_member_company_id'), 'tab_coffee_member',
                    ['company_id'])
    op.create_index(op.f('ix_tab_coffee_member_pos_partner_id'), 'tab_coffee_member',
                    ['pos_partner_id'])

    op.create_table(
        'tab_coffee_ledger',
        *_audit_cols(),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('employee_id', sa.BigInteger(), nullable=False),
        sa.Column('period', sa.String(length=6), nullable=False),
        sa.Column('type', sa.SmallInteger(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('pos_order_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('uniq_key', sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uniq_key'),
    )
    op.create_index(op.f('ix_tab_coffee_ledger_company_id'), 'tab_coffee_ledger',
                    ['company_id'])
    op.create_index(op.f('ix_tab_coffee_ledger_employee_id'), 'tab_coffee_ledger',
                    ['employee_id'])
    op.create_index(op.f('ix_tab_coffee_ledger_period'), 'tab_coffee_ledger', ['period'])
    op.create_index('ix_coffee_ledger_emp_period', 'tab_coffee_ledger',
                    ['employee_id', 'period'])

    op.create_table(
        'tab_pos_order',
        *_audit_cols(),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('pos_order_id', sa.BigInteger(), nullable=False),
        sa.Column('pos_code', sa.String(length=50), nullable=False),
        sa.Column('purchase_date', sa.String(length=19), nullable=False),
        sa.Column('pos_partner_id', sa.BigInteger(), nullable=False),
        sa.Column('employee_id', sa.BigInteger(), nullable=False),
        sa.Column('total', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('points_paid', sa.Integer(), nullable=False),
        sa.Column('pos_status', sa.Integer(), nullable=False),
        sa.Column('match_status', sa.SmallInteger(), nullable=False),
        sa.Column('is_voided', sa.SmallInteger(), nullable=False),
        sa.Column('resolve_note', sa.String(length=500), nullable=False),
        sa.Column('raw_json', sa.Text(), nullable=False),
        sa.Column('synced_at', sa.String(length=19), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pos_order_id'),
    )
    op.create_index(op.f('ix_tab_pos_order_company_id'), 'tab_pos_order', ['company_id'])
    op.create_index(op.f('ix_tab_pos_order_purchase_date'), 'tab_pos_order',
                    ['purchase_date'])
    op.create_index(op.f('ix_tab_pos_order_pos_partner_id'), 'tab_pos_order',
                    ['pos_partner_id'])
    op.create_index(op.f('ix_tab_pos_order_employee_id'), 'tab_pos_order',
                    ['employee_id'])

    op.create_table(
        'tab_pos_sync_run',
        *_audit_cols(),
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('started_at', sa.String(length=19), nullable=False),
        sa.Column('finished_at', sa.String(length=19), nullable=False),
        sa.Column('cursor_from', sa.String(length=30), nullable=False),
        sa.Column('cursor_to', sa.String(length=30), nullable=False),
        sa.Column('fetched', sa.Integer(), nullable=False),
        sa.Column('written', sa.Integer(), nullable=False),
        sa.Column('skipped', sa.Integer(), nullable=False),
        sa.Column('error', sa.Text(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_pos_sync_run_kind'), 'tab_pos_sync_run', ['kind'])
    op.create_index(op.f('ix_tab_pos_sync_run_status'), 'tab_pos_sync_run', ['status'])


def downgrade() -> None:
    op.drop_table('tab_pos_sync_run')
    op.drop_table('tab_pos_order')
    op.drop_table('tab_coffee_ledger')
    op.drop_table('tab_coffee_member')
    op.drop_table('tab_coffee_policy')
