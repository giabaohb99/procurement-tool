"""company type ho kinh doanh

bao-CR-531 (30/09/2026): danh mục Công ty có thêm ô «Loại hình» — 1 Công ty · 2 Hộ kinh
doanh (`app/modules/company/constants.py`, SMALLINT + IntEnum theo R2/QĐ-11). Bản in Phiếu
đề xuất mua hàng của hộ kinh doanh chỉ còn hai ô ký «Chủ hộ» + «Người lập».

Dữ liệu cũ: mọi dòng mặc định `1`; dòng có TÊN bắt đầu bằng «HỘ KINH DOANH» (không phân
biệt hoa thường) đổi sang `2` — prod có đúng một dòng (id 7, «HỘ KINH DOANH DR XANH»). So
khớp làm trong Python chứ không bằng `LIKE`: collation `_ai_ci` của MySQL coi «HO» = «HỘ»,
và câu SQL chứa tiếng Việt là đường dễ dính lỗi mã hóa (CLAUDE.md).

Viết TAY (autogenerate repo này trôi ~650 dòng không liên quan).

Revision ID: c531a7e4d2f9
Revises: c496a1b2d3e4

Thứ tự: đặt NGAY SAU c496a1b2d3e4 (head của prod ngày 30/09) để lên prod trước cụm thuốc
BVTV (5f39bbc564db → a7c3e91d5b20 → b4d81f2c6e37) mà không làm alembic bỏ qua cụm đó sau này.
Create Date: 2026-09-30 10:00:00
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c531a7e4d2f9'
down_revision: Union[str, None] = 'c496a1b2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_HOUSEHOLD = 2
_HOUSEHOLD_PREFIX = unicodedata.normalize("NFC", "HỘ KINH DOANH")


def _is_household_name(name: str | None) -> bool:
    text = unicodedata.normalize("NFC", " ".join((name or "").split())).upper()
    return text.startswith(_HOUSEHOLD_PREFIX)


def upgrade() -> None:
    op.add_column('tab_company',
                  sa.Column('company_type', sa.SmallInteger(), nullable=False, server_default='1'))
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, name FROM tab_company")).fetchall()
    household_ids = [int(r[0]) for r in rows if _is_household_name(r[1])]
    for company_id in household_ids:
        bind.execute(sa.text("UPDATE tab_company SET company_type = :t WHERE id = :i"),
                     {"t": _HOUSEHOLD, "i": company_id})


def downgrade() -> None:
    op.drop_column('tab_company', 'company_type')
