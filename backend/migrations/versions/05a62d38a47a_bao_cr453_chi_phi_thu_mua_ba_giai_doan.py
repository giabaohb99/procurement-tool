"""bao_cr453_chi_phi_thu_mua_ba_giai_doan

Chi phí thu mua ba giai đoạn (Dự toán → Tạm tính → Quyết toán) + danh mục loại chi phí —
bao-CR-453, thiết kế ở `doc/erp/nhap-khau/02-chi-phi-thu-mua.md`.

1. Đổi tên `tab_po_import_cost` → `tab_po_cost`: chi phí thu mua áp cho MỌI loại đơn, không
   riêng nhập khẩu. Ba chỉ mục cũ đổi tên theo để `alembic --autogenerate` không đòi dựng lại.
2. Mỗi dòng chi phí mang BA bộ số `estimate_ / provisional_ / final_` × `amount / rate / base`
   + `line_stage` (giai đoạn riêng của dòng). Dữ liệu cũ: dòng THỰC TẾ (`cost_status` 2, 0
   hoặc trống) chép sang bộ QUYẾT TOÁN và `line_stage = 3`; dòng DỰ KIẾN sót lại
   (`cost_status = 1`) chép sang bộ DỰ TOÁN. Xong thì bỏ bốn cột cũ
   `amount / exchange_rate / base_amount / cost_status`.
3. `tab_purchase_order.cost_stage` — giai đoạn chi phí của cả đơn. Đơn đã có dòng chi phí, hoặc
   đã Hoàn thành / Hủy / Từ chối, đặt sẵn Quyết toán (số cũ vốn là số thực tế, công nợ đã sinh
   từ đó); đơn còn dòng dự kiến thì đứng ở Dự toán. Đơn còn lại mặc định Dự toán.
4. Bảng danh mục `tab_po_cost_type` + nạp 15 mã gốc (1..14, 99) từ `DEFAULT_COST_TYPES` của
   model — chỉ thêm mã còn thiếu, chạy lại không đè.

Downgrade dựng lại bốn cột cũ từ bộ QUYẾT TOÁN (dòng chưa quyết toán lấy bộ cao nhất đã có
số và `cost_status = 1`), bỏ các cột giai đoạn, đổi tên bảng về như cũ, bỏ `cost_stage` và
bỏ bảng danh mục.

Revision ID: 05a62d38a47a
Revises: f2c5b9d71a48
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '05a62d38a47a'
down_revision: Union[str, None] = 'f2c5b9d71a48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_TABLE = 'tab_po_import_cost'
NEW_TABLE = 'tab_po_cost'
STAGE_PREFIXES = ('estimate', 'provisional', 'final')
# (tên cũ, tên mới) của ba chỉ mục đi theo bảng — MySQL không tự đổi tên chỉ mục khi đổi tên bảng.
RENAMED_INDEXES = (
    ('ix_tab_po_import_cost_po_id', 'ix_tab_po_cost_po_id'),
    ('ix_tab_po_import_cost_cost_type', 'ix_tab_po_cost_cost_type'),
    ('ix_tab_po_import_cost_supplier_code', 'ix_tab_po_cost_supplier_code'),
)


def _is_mysql() -> bool:
    return op.get_bind().dialect.name == 'mysql'


def _rename_indexes(pairs) -> None:
    if not _is_mysql():
        return
    for old, new in pairs:
        op.execute(sa.text(f'ALTER TABLE {NEW_TABLE} RENAME INDEX {old} TO {new}'))


def _seed_cost_types() -> None:
    """Nạp 15 mã gốc, bỏ qua mã đã có (chạy lại được)."""
    from app.modules.purchase_order.model import DEFAULT_COST_TYPES

    bind = op.get_bind()
    existing = {int(code) for (code,) in bind.execute(sa.text('SELECT code FROM tab_po_cost_type'))}
    stmt = sa.text(
        'INSERT INTO tab_po_cost_type (code, name, group_kind, creates_payable, default_supplier_code, '
        'default_allocation_method, default_vat, sort_order, is_active, note, created_by, updated_by) '
        'VALUES (:code, :name, :group_kind, :creates_payable, :default_supplier_code, 1, 0, :sort_order, '
        '1, \'\', 0, 0)')
    for code, name, group_kind, creates_payable, default_supplier_code, sort_order in DEFAULT_COST_TYPES:
        if code in existing:
            continue
        bind.execute(stmt, {'code': code, 'name': name, 'group_kind': group_kind,
                            'creates_payable': 1 if creates_payable else 0,
                            'default_supplier_code': default_supplier_code, 'sort_order': sort_order})


def upgrade() -> None:
    # 1. Đổi tên bảng + chỉ mục
    op.rename_table(OLD_TABLE, NEW_TABLE)
    _rename_indexes(RENAMED_INDEXES)

    # 2. Cột giai đoạn + chép số cũ sang
    op.add_column(NEW_TABLE, sa.Column('line_stage', sa.SmallInteger(), nullable=False, server_default='1'))
    for prefix in STAGE_PREFIXES:
        op.add_column(NEW_TABLE, sa.Column(f'{prefix}_amount', sa.Numeric(18, 2), nullable=True))
        op.add_column(NEW_TABLE, sa.Column(f'{prefix}_rate', sa.Numeric(18, 6), nullable=False, server_default='1'))
        op.add_column(NEW_TABLE, sa.Column(f'{prefix}_base', sa.Numeric(18, 2), nullable=True))
    op.execute(sa.text(
        f'UPDATE {NEW_TABLE} SET final_amount = amount, final_rate = exchange_rate, '
        'final_base = base_amount, line_stage = 3 WHERE cost_status IS NULL OR cost_status <> 1'))
    op.execute(sa.text(
        f'UPDATE {NEW_TABLE} SET estimate_amount = amount, estimate_rate = exchange_rate, '
        'estimate_base = base_amount, line_stage = 1 WHERE cost_status = 1'))
    op.drop_index('ix_tab_po_import_cost_cost_status', table_name=NEW_TABLE)
    for col in ('cost_status', 'base_amount', 'exchange_rate', 'amount'):
        op.drop_column(NEW_TABLE, col)
    op.create_index('ix_po_cost_po_stage', NEW_TABLE, ['po_id', 'line_stage'])

    # 3. Giai đoạn chi phí của đơn
    op.add_column('tab_purchase_order',
                  sa.Column('cost_stage', sa.SmallInteger(), nullable=False, server_default='1'))
    op.create_index(op.f('ix_tab_purchase_order_cost_stage'), 'tab_purchase_order', ['cost_stage'])
    op.execute(sa.text(
        "UPDATE tab_purchase_order SET cost_stage = 3 WHERE status IN ('completed', 'cancelled', 'rejected') "
        f"OR id IN (SELECT po_id FROM {NEW_TABLE})"))
    op.execute(sa.text(
        f"UPDATE tab_purchase_order SET cost_stage = 1 WHERE id IN (SELECT po_id FROM {NEW_TABLE} WHERE line_stage = 1)"))

    # 4. Danh mục loại chi phí
    op.create_table(
        'tab_po_cost_type',
        sa.Column('code', sa.SmallInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('group_kind', sa.SmallInteger(), nullable=False, server_default='2'),
        sa.Column('creates_payable', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('default_supplier_code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('default_allocation_method', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('default_vat', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('note', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_po_cost_type_code'), 'tab_po_cost_type', ['code'], unique=True)
    _seed_cost_types()


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_po_cost_type_code'), table_name='tab_po_cost_type')
    op.drop_table('tab_po_cost_type')

    op.drop_index(op.f('ix_tab_purchase_order_cost_stage'), table_name='tab_purchase_order')
    op.drop_column('tab_purchase_order', 'cost_stage')

    op.drop_index('ix_po_cost_po_stage', table_name=NEW_TABLE)
    op.add_column(NEW_TABLE, sa.Column('amount', sa.Numeric(18, 2), nullable=False, server_default='0'))
    op.add_column(NEW_TABLE, sa.Column('exchange_rate', sa.Numeric(18, 6), nullable=False, server_default='1'))
    op.add_column(NEW_TABLE, sa.Column('base_amount', sa.Numeric(18, 2), nullable=False, server_default='0'))
    op.add_column(NEW_TABLE, sa.Column('cost_status', sa.SmallInteger(), nullable=False, server_default='2'))
    # Dòng đã quyết toán lấy bộ QUYẾT TOÁN; dòng chưa thì lấy bộ cao nhất đã có số và đánh dấu Dự kiến.
    op.execute(sa.text(
        f'UPDATE {NEW_TABLE} SET amount = final_amount, exchange_rate = final_rate, '
        'base_amount = COALESCE(final_base, 0), cost_status = 2 WHERE final_amount IS NOT NULL'))
    op.execute(sa.text(
        f'UPDATE {NEW_TABLE} SET amount = provisional_amount, exchange_rate = provisional_rate, '
        'base_amount = COALESCE(provisional_base, 0), cost_status = 1 '
        'WHERE final_amount IS NULL AND provisional_amount IS NOT NULL'))
    op.execute(sa.text(
        f'UPDATE {NEW_TABLE} SET amount = estimate_amount, exchange_rate = estimate_rate, '
        'base_amount = COALESCE(estimate_base, 0), cost_status = 1 '
        'WHERE final_amount IS NULL AND provisional_amount IS NULL AND estimate_amount IS NOT NULL'))
    op.create_index('ix_tab_po_import_cost_cost_status', NEW_TABLE, ['cost_status'])
    for prefix in STAGE_PREFIXES:
        for suffix in ('base', 'rate', 'amount'):
            op.drop_column(NEW_TABLE, f'{prefix}_{suffix}')
    op.drop_column(NEW_TABLE, 'line_stage')

    _rename_indexes([(new, old) for old, new in RENAMED_INDEXES])
    op.rename_table(NEW_TABLE, OLD_TABLE)
