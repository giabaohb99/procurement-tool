"""thuoc bvtv mo rong danh muc

Mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026): mở rộng `tab_customs_pesticide` cho đủ
dữ liệu của bản cào danhmuc.thuocbvtv.com (số đăng ký, tình trạng, hạn, hàm lượng, lĩnh vực,
nhóm độc, nhóm kháng, url nguồn) và thêm bảng con `tab_customs_pesticide_use` (phạm vi sử dụng:
cây trồng – dịch hại – liều – cách ly – cách dùng).

Viết TAY (autogenerate repo này trôi ~650 dòng không liên quan). `status` là SMALLINT theo luật
R2 (`constants.PesticideStatus`). Nếu bảng đã có dòng nạp từ `bvtv_data.js` cũ, các dòng đó mang
`status = 0` (chưa rõ) và KHÔNG hiện dưới bộ lọc mặc định «Còn hiệu lực» — phải bấm «Nạp danh mục»
một lần sau khi deploy.

Revision ID: a7c3e91d5b20
Revises: e538c6a1f2d9 (01/10: cum thuoc BVTV len prod truoc, chi muc bao cao 5f39 doi ra sau)
Create Date: 2026-09-29 14:10:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a7c3e91d5b20'
down_revision: Union[str, None] = 'e538c6a1f2d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STRINGS = [("sector", 100), ("concentration", 100), ("registration_no", 60),
            ("toxicity", 500), ("source_url", 255)]


def upgrade() -> None:
    for name, size in _STRINGS:
        op.add_column('tab_customs_pesticide',
                      sa.Column(name, sa.String(length=size), nullable=False, server_default=''))
    op.add_column('tab_customs_pesticide',
                  sa.Column('status', sa.SmallInteger(), nullable=False, server_default='0'))
    op.add_column('tab_customs_pesticide', sa.Column('registered_on', sa.Date(), nullable=True))
    op.add_column('tab_customs_pesticide', sa.Column('expires_on', sa.Date(), nullable=True))
    op.add_column('tab_customs_pesticide', sa.Column('resistance', sa.Text(), nullable=True))
    op.create_index(op.f('ix_tab_customs_pesticide_status'), 'tab_customs_pesticide', ['status'])
    op.create_index(op.f('ix_tab_customs_pesticide_registration_no'), 'tab_customs_pesticide',
                    ['registration_no'])

    op.create_table(
        'tab_customs_pesticide_use',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pesticide_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('crop', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('pest', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('dosage', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('pre_harvest_interval', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('usage', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_customs_pesticide_use_pesticide_id'), 'tab_customs_pesticide_use',
                    ['pesticide_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_customs_pesticide_use_pesticide_id'),
                  table_name='tab_customs_pesticide_use')
    op.drop_table('tab_customs_pesticide_use')
    op.drop_index(op.f('ix_tab_customs_pesticide_registration_no'), table_name='tab_customs_pesticide')
    op.drop_index(op.f('ix_tab_customs_pesticide_status'), table_name='tab_customs_pesticide')
    for name in ['resistance', 'expires_on', 'registered_on', 'status'] + [n for n, _ in _STRINGS]:
        op.drop_column('tab_customs_pesticide', name)
