"""cr470_hai_quan_nen_du_lieu — lược đồ phân hệ Tra cứu giá hải quan (bao-CR-470, HQ1 → HQ6).

MỘT migration cho cả phân hệ (gộp lúc chưa commit, khỏi đẻ chuỗi migration nối nhau):

- `tab_customs_party`: bảng ĐỐI TƯỢNG — doanh nghiệp trong nước + đối tác nước
  ngoài, phân loại theo bản chất; duy nhất theo `(party_type, dedupe_key)`.
- `tab_customs_line`: mỗi dòng là MỘT DÒNG HÀNG của tờ khai (không phải một tờ
  khai). Trên MySQL: khóa chính `(id, reg_date)` + **chia phân vùng theo năm**.

Lô nạp KHÔNG có bảng riêng — dùng lại `tab_import_batch` (`module = 3`).
Thiết kế: `doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` §3.

Chia phân vùng NGAY LÚC BẢNG CÒN RỖNG: `ALTER TABLE … PARTITION BY` dựng lại toàn
bộ bảng, làm lúc đã có hàng triệu dòng là khóa bảng lâu. Có phân vùng `pmax` hứng
mọi năm chưa khai, nên KHÔNG cần tác vụ mở phân vùng năm mới mới chạy đúng — thêm
phân vùng năm chỉ để cắt tỉa truy vấn cho gọn. (Tác vụ tự mở phân vùng
`system_log/partition.py` của CR-454 hiện chỉ có ở nhánh `erp-v2`; gộp sang thì
đăng ký bảng này vào đó.)

⚠️ VIẾT TAY, không autogenerate. ⚠️ `DROP PRIMARY KEY` và `ADD PRIMARY KEY` phải
nằm CÙNG một câu: `id` là AUTO_INCREMENT, tách riêng thì MySQL từ chối (bài học CR-454).

Revision ID: c4d8e2a6f470
Revises: 05a62d38a47a
Create Date: 2026-09-23 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d8e2a6f470'
down_revision: Union[str, None] = '05a62d38a47a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Năm có phân vùng riêng lúc tạo bảng. Dữ liệu mẫu là năm 2026; mở lùi vài năm
#  cho trường hợp nạp dữ liệu cũ (câu Q4). Năm ngoài dải rơi vào `pmax`, vẫn đúng.
_YEARS = range(2020, 2029)


def _audit_cols():
    return [sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('created_by', sa.BigInteger(), server_default='0'),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_by', sa.BigInteger(), server_default='0')]


def _money(scale_p: int, scale_s: int):
    return sa.Numeric(scale_p, scale_s)


def upgrade() -> None:
    op.create_table(
        'tab_customs_party',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('party_type', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('dedupe_key', sa.String(40), nullable=False, server_default=''),
        sa.Column('tax_code', sa.String(14), nullable=False, server_default=''),
        sa.Column('name', sa.String(255), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.BigInteger(), server_default='0'),
        sa.UniqueConstraint('party_type', 'dedupe_key', name='uq_customs_party_key'),
    )

    op.create_table(
        'tab_customs_line',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('batch_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('source_row', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('date_fixed', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('reg_date', sa.Date(), nullable=False),
        sa.Column('office_code', sa.String(10), nullable=False, server_default=''),
        sa.Column('importer_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('partner_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('hs_code', sa.String(8), nullable=False, server_default=''),
        sa.Column('line_no', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('product_name', sa.String(255), nullable=False, server_default=''),
        sa.Column('price_usd', _money(16, 4), nullable=True),
        sa.Column('price_nt', _money(16, 4), nullable=True),
        sa.Column('adj_price_usd', _money(16, 4), nullable=True),
        sa.Column('adj_price_nt', _money(16, 4), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default=''),
        sa.Column('fx_rate', _money(14, 4), nullable=True),
        sa.Column('usd_rate', _money(14, 4), nullable=True),
        sa.Column('quantity', _money(18, 4), nullable=True),
        sa.Column('unit_code', sa.String(4), nullable=False, server_default=''),
        sa.Column('origin_country', sa.String(2), nullable=False, server_default=''),
        sa.Column('contract_no', sa.String(40), nullable=False, server_default=''),
        sa.Column('contract_date', sa.Date(), nullable=True),
        sa.Column('incoterm', sa.String(3), nullable=False, server_default=''),
        sa.Column('transport_mode', sa.SmallInteger(), nullable=True),
        sa.Column('rate_import', _money(6, 2), nullable=True),
        sa.Column('rate_excise', _money(6, 2), nullable=True),
        sa.Column('rate_vat', _money(6, 2), nullable=True),
        sa.Column('rate_safeguard', _money(6, 2), nullable=True),
        sa.Column('tax_import', _money(18, 3), nullable=True),
        sa.Column('tax_excise', _money(18, 3), nullable=True),
        sa.Column('tax_vat', _money(18, 3), nullable=True),
        sa.Column('tax_environment', _money(18, 3), nullable=True),
        sa.Column('tax_safeguard', _money(18, 3), nullable=True),
        sa.Column('import_country', sa.String(2), nullable=False, server_default=''),
        #  HQ4 — hai cột dẫn xuất từ tên hàng lúc nạp (`customs/ingredient.py`).
        sa.Column('active_ingredient', sa.String(255), nullable=False, server_default=''),
        sa.Column('formulation', sa.String(40), nullable=False, server_default=''),
    )
    op.create_index('ix_tab_customs_line_batch_id', 'tab_customs_line', ['batch_id'])
    op.create_index('ix_customs_line_hs_date', 'tab_customs_line', ['hs_code', 'reg_date'])
    op.create_index('ix_customs_line_importer_date', 'tab_customs_line', ['importer_id', 'reg_date'])
    op.create_index('ix_tab_customs_line_active_ingredient', 'tab_customs_line', ['active_ingredient'])

    #  HQ4 — từ khóa hoạt chất + danh mục thuốc BVTV (dữ liệu tham khảo, nạp bằng kịch bản).
    op.create_table(
        'tab_customs_ingredient_alias',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('keyword', sa.String(100), nullable=False, unique=True),
        sa.Column('canonical', sa.String(255), nullable=False, server_default=''),
        *_audit_cols(),
    )
    op.create_table(
        'tab_customs_pesticide',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('source_id', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trade_name', sa.String(255), nullable=False, server_default=''),
        sa.Column('trade_key', sa.String(255), nullable=False, server_default=''),
        sa.Column('active_ingredient', sa.String(500), nullable=False, server_default=''),
        sa.Column('pest_group', sa.String(100), nullable=False, server_default=''),
        sa.Column('registrant', sa.String(255), nullable=False, server_default=''),
        *_audit_cols(),
    )
    op.create_index('ix_tab_customs_pesticide_trade_key', 'tab_customs_pesticide', ['trade_key'])

    #  HQ6 — danh mục hóa chất theo văn bản (sửa được) + biểu thuế (tham khảo).
    op.create_table(
        'tab_customs_regulation',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('list_code', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('name', sa.String(500), nullable=False, server_default=''),
        sa.Column('name_vi', sa.String(500), nullable=False, server_default=''),
        sa.Column('cas_no', sa.String(40), nullable=False, server_default=''),
        sa.Column('category', sa.String(100), nullable=False, server_default=''),
        sa.Column('threshold_kg', sa.Numeric(14, 3), nullable=True),
        sa.Column('banned_year', sa.SmallInteger(), nullable=True),
        sa.Column('legal_basis', sa.String(255), nullable=False, server_default=''),
        sa.Column('note', sa.String(500), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_cols(),
    )
    op.create_index('ix_tab_customs_regulation_list_code', 'tab_customs_regulation', ['list_code'])
    op.create_index('ix_tab_customs_regulation_cas_no', 'tab_customs_regulation', ['cas_no'])
    op.create_table(
        'tab_customs_tariff',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('hs_code', sa.String(10), nullable=False, server_default=''),
        sa.Column('name_vn', sa.Text(), nullable=True),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(40), nullable=False, server_default=''),
        sa.Column('rate_normal', sa.String(20), nullable=False, server_default=''),
        sa.Column('rate_mfn', sa.String(20), nullable=False, server_default=''),
        sa.Column('rate_vat', sa.String(20), nullable=False, server_default=''),
        sa.Column('fta_json', sa.Text(), nullable=True),
        sa.Column('policy', sa.Text(), nullable=True),
    )
    op.create_index('ix_tab_customs_tariff_hs_code', 'tab_customs_tariff', ['hs_code'])

    bind = op.get_bind()
    if bind.dialect.name != 'mysql':
        return
    #  Khóa chính phải chứa cột phân vùng (luật MySQL) — một câu duy nhất.
    bind.execute(sa.text(
        "ALTER TABLE tab_customs_line DROP PRIMARY KEY, ADD PRIMARY KEY (id, reg_date)"))
    parts = ", ".join(f"PARTITION p{y} VALUES LESS THAN ({y + 1})" for y in _YEARS)
    bind.execute(sa.text(
        f"ALTER TABLE tab_customs_line PARTITION BY RANGE (YEAR(reg_date)) "
        f"({parts}, PARTITION pmax VALUES LESS THAN MAXVALUE)"))


def downgrade() -> None:
    #  Chỉ xóa bảng đang có thật — gỡ được cả DB dựng bằng bản migration cũ hơn của
    #  chính CR này (lúc phát triển, lược đồ gộp dần các phase vào đây).
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    for table in ('tab_customs_tariff', 'tab_customs_regulation', 'tab_customs_pesticide',
                  'tab_customs_ingredient_alias', 'tab_customs_line', 'tab_customs_party'):
        if table in existing:
            op.drop_table(table)
