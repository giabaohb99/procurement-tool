"""bao-CR-494 + bao-CR-495: nhan Thanh pham / Nguyen lieu + tu khoa admin; tu dong nghia tim kiem

- tab_customs_line.product_kind (SMALLINT, 0 = chua gan): nhan tu ten hang theo bo tu khoa.
- tab_customs_kind_keyword: bo tu khoa admin sua duoc, nap san 6 tu mac dinh cua chi Mi.
- tab_customs_search_synonym: tu goc + cac cach viet tuong duong cho o tim ten hang.
Sau khi chay: POST /api/customs/kinds/retag (hoac scripts/load_customs_catalogs.py) de gan nhan
cho dong da nap; migration KHONG tu gan vi bang co the vai chuc nghin dong.

Revision ID: b494c1d2e3f4
Revises: f3b8d1a6c2e9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b494c1d2e3f4'
down_revision: Union[str, None] = 'f3b8d1a6c2e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_KEYWORDS = (
    ("TC", 2, "Thuốc kỹ thuật, vd «ATRAZINE 97% TC»"),
    ("TECH", 2, "Thuốc kỹ thuật, vd «MANCOZEB TECH 86%»"),
    ("TG", 2, "Technical grade"),
    ("TECHNICAL", 2, ""),
    ("KỸ THUẬT", 2, "«Thuốc kỹ thuật …»"),
    ("NGUYÊN LIỆU", 2, "«… nguyên liệu dùng SX thuốc …»"),
)


def _audit_columns():
    return [
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.BigInteger(), server_default='0'),
    ]


def upgrade() -> None:
    op.add_column('tab_customs_line',
                  sa.Column('product_kind', sa.SmallInteger(), nullable=False, server_default='0'))
    op.create_index('ix_tab_customs_line_product_kind', 'tab_customs_line', ['product_kind'])

    keyword = op.create_table(
        'tab_customs_kind_keyword',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('keyword', sa.String(100), nullable=False),
        sa.Column('kind', sa.SmallInteger(), nullable=False, server_default='2'),
        sa.Column('note', sa.String(255), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_columns(),
        sa.UniqueConstraint('keyword', name='uq_customs_kind_keyword'),
    )
    op.bulk_insert(keyword, [{"keyword": k, "kind": kind, "note": note} for k, kind, note in DEFAULT_KEYWORDS])

    op.create_table(
        'tab_customs_search_synonym',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('term', sa.String(100), nullable=False),
        sa.Column('synonyms', sa.String(1000), nullable=False, server_default=''),
        sa.Column('note', sa.String(255), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_columns(),
        sa.UniqueConstraint('term', name='uq_customs_search_synonym'),
    )


def downgrade() -> None:
    op.drop_table('tab_customs_search_synonym')
    op.drop_table('tab_customs_kind_keyword')
    op.drop_index('ix_tab_customs_line_product_kind', table_name='tab_customs_line')
    op.drop_column('tab_customs_line', 'product_kind')
