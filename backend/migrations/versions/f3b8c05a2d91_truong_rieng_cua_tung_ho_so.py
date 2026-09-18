"""Trường riêng của TỪNG hồ sơ — `tab_dossier.custom_fields`

Phân hệ Hồ sơ, 17/09/2026. Người lập hồ sơ khai thêm ô ngay tại chỗ (tên · kiểu
· bắt buộc · giá trị) mà không đụng vào khuôn của loại.

Cùng cấu trúc với `tab_dossier_type.field_schema` (xem `dossier/field_schema.py`),
và GIÁ TRỊ của chúng đi chung vào `tab_dossier.extra_fields` với giá trị của bộ
trường thừa kế từ loại — hai nguồn KHAI, một kho GIÁ TRỊ.

⚠️ Vì chung kho nên khóa không được trùng nhau; chốt ở
`dossier/service.apply_extra_fields`, không phải ở tầng DB (`JSON` không ràng
buộc được chuyện đó).

Revision ID: f3b8c05a2d91
Revises: 2e26610521d7
Create Date: 2026-09-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3b8c05a2d91"
down_revision: Union[str, None] = "2e26610521d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "tab_dossier" in tables:
        cols = [c['name'] for c in inspector.get_columns("tab_dossier")]
        if "custom_fields" not in cols:
            op.add_column("tab_dossier", sa.Column("custom_fields", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_dossier", "custom_fields")
