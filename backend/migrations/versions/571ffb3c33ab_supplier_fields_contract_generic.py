"""supplier fields + contract generic

Revision ID: 571ffb3c33ab
Revises: 216cddb1081a
Create Date: 2026-07-01 07:23:10.556555

Idempotent: bản autogenerate gốc chạy trên DB dev (tạo bằng create_all) nên sinh ra
lệnh drop 'tab_employee.status' / 'role_name' — 2 cột này KHÔNG tồn tại khi dựng DB
từ đầu theo chain migration, làm `alembic upgrade head` trên DB rỗng chết giữa chừng.
MySQL auto-commit DDL nên migration hỏng còn để lại trạng thái nửa vời → mọi thao tác
đều bọc kiểm tra tồn tại để chạy lại được.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '571ffb3c33ab'
down_revision: Union[str, None] = '216cddb1081a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def _add(table: str, column: sa.Column):
    if column.name not in _columns(table):
        op.add_column(table, column)


def _drop(table: str, column: str):
    if column in _columns(table):
        op.drop_column(table, column)


def upgrade() -> None:
    _add('tab_contract', sa.Column('party_type', sa.String(length=30), nullable=False))
    _add('tab_contract', sa.Column('party_code', sa.String(length=50), nullable=False))
    _add('tab_contract', sa.Column('party_name', sa.String(length=255), nullable=False))
    _add('tab_contract', sa.Column('company_id', sa.BigInteger(), nullable=False))
    _add('tab_contract', sa.Column('signed', sa.Boolean(), nullable=False))

    contract_idx = _indexes('tab_contract')
    if 'ix_tab_contract_supplier_code' in contract_idx:
        op.drop_index('ix_tab_contract_supplier_code', table_name='tab_contract')
    if op.f('ix_tab_contract_party_code') not in contract_idx:
        op.create_index(op.f('ix_tab_contract_party_code'), 'tab_contract', ['party_code'], unique=False)

    for col in ('filename', 'supplier_code', 'supplier_name', 'payment_terms', 'value', 'file_url'):
        _drop('tab_contract', col)

    # Bản autogenerate gốc DROP 2 cột này, nhưng revision kế tiếp (fac1da01ec6e) lại
    # ALTER chúng thành NOT NULL và model Employee vẫn khai báo cả hai → ý định thật là
    # GIỮ. Ở đây chỉ đảm bảo cột tồn tại để chain chạy được trên DB rỗng.
    _add('tab_employee', sa.Column('status', sa.String(length=50), nullable=True, server_default='Chính thức'))
    _add('tab_employee', sa.Column('role_name', sa.String(length=100), nullable=True, server_default=''))

    _add('tab_supplier', sa.Column('legal_type', sa.String(length=30), nullable=False))
    _add('tab_supplier', sa.Column('contact_person', sa.String(length=100), nullable=False))
    _add('tab_supplier', sa.Column('phone', sa.String(length=30), nullable=False))
    _add('tab_supplier', sa.Column('bank_account', sa.String(length=50), nullable=False))
    _add('tab_supplier', sa.Column('bank_name', sa.String(length=255), nullable=False))


def downgrade() -> None:
    for col in ('bank_name', 'bank_account', 'phone', 'contact_person', 'legal_type'):
        _drop('tab_supplier', col)

    _add('tab_employee', sa.Column('role_name', mysql.VARCHAR(length=100), server_default=sa.text("''"), nullable=True))
    _add('tab_employee', sa.Column('status', mysql.VARCHAR(length=50), server_default=sa.text("'Chính thức'"), nullable=True))

    _add('tab_contract', sa.Column('file_url', mysql.VARCHAR(length=1000), nullable=False))
    _add('tab_contract', sa.Column('value', mysql.DECIMAL(precision=18, scale=2), nullable=False))
    _add('tab_contract', sa.Column('payment_terms', mysql.VARCHAR(length=255), nullable=False))
    _add('tab_contract', sa.Column('supplier_name', mysql.VARCHAR(length=255), nullable=False))
    _add('tab_contract', sa.Column('supplier_code', mysql.VARCHAR(length=50), nullable=False))
    _add('tab_contract', sa.Column('filename', mysql.VARCHAR(length=255), nullable=False))

    contract_idx = _indexes('tab_contract')
    if op.f('ix_tab_contract_party_code') in contract_idx:
        op.drop_index(op.f('ix_tab_contract_party_code'), table_name='tab_contract')
    if 'ix_tab_contract_supplier_code' not in contract_idx:
        op.create_index('ix_tab_contract_supplier_code', 'tab_contract', ['supplier_code'], unique=False)

    for col in ('signed', 'company_id', 'party_name', 'party_code', 'party_type'):
        _drop('tab_contract', col)
